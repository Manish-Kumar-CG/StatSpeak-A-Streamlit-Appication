import subprocess
import json
import re
import pandas as pd
import numpy as np
from open_search import get_columns
import os
from llm_response_generator import get_multimodal_model
# def get_columns(question,docsearch):
#         response = docsearch.similarity_search(question, k = 5)
#         columns = []

#         for data in response:
#             data = json.loads(data.page_content)
#             columns.append({"column_name":data['column_name'],"description": data['description']})

        # return columns
def add_cols_to_prompt(starting_prompt: str, table: str, cols_list: list[str]) -> str:
    starting_prompt += f"\n===Table \n {table}"
    if len(cols_list) > 0:
        starting_prompt += "\n===Columns \n"
        for col in cols_list:
            starting_prompt += f"{col}\n"
    return starting_prompt

def add_sample_sqls_to_prompt(starting_prompt: str, question_sql_list: list) -> str:
    if len(question_sql_list) > 0:
        starting_prompt += "\n===Sample questions and corresponding sqls\n\n"
        for example in question_sql_list:
            if example is None:
                print("example is None")
            else:
                if "question" in example and "sql" in example:
                    starting_prompt += f"\nQuestion: {example['question']}"
                    starting_prompt += f", Sql: {example['sql']}\n"
    return starting_prompt

def get_sql_prompt(starting_prompt: str, question: str, columns_list: list, question_sql_list: list, table: str) -> str:
    if starting_prompt is None:
        starting_prompt = (
            "You are a Microsoft SQL Server Management Studio expert. "
            "Please help to generate a SQL query that can run on Microsoft SQL Server to answer the question. Your response should ONLY be based on the given context and follow the response guidelines and format instructions. "
        )
    
    # Adding table and columns context
    starting_prompt = add_cols_to_prompt(starting_prompt, table, columns_list)
    starting_prompt = add_sample_sqls_to_prompt(starting_prompt, question_sql_list)
    
    # Including the question in the prompt
    starting_prompt += f"\n\nQuestion: {question}\n"

    starting_prompt += (
        "===Response Guidelines \n"
        "Please generate the SQL query that corresponds to the question above. "
        "Always study the question properly and try to find similar columns in the columns section. "
        "Check for gender, especially in the question."
    )
    
    return starting_prompt

doc_list = ['Always cast the column invoice_date using Date function', 'If Year is not mentioned in the question, then always filter on current year','Column alias should be under backticks ("``")']

def generate_sql(question: str) -> str:
    starting_prompt = None
    columns  = get_columns(question)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'knowledge_base/sample_sql_query.json')
    with open(json_path, 'r') as f:
        question_sql_list = json.load(f)

    multimodal_model = get_multimodal_model()
    table = "customer_shopping_data"
    prompt = get_sql_prompt(
        starting_prompt=starting_prompt,
        question=question,
        columns_list=columns,
        question_sql_list=question_sql_list,
        table=table
    )
    # print("SQL Prompt", prompt)

    # Generate LLM response for initial prompt
    llm_response = multimodal_model.generate_content(prompt)
    llm_response_text = llm_response.text  # Extract the response text
    # print("LLM Response", llm_response_text)

    # Check if 'intermediate_sql' is in the response text
    if 'intermediate_sql' in llm_response_text:
        intermediate_sql = extract_sql(llm_response_text)

        try:
            # print("Running Intermediate SQL", intermediate_sql)
            # Run the intermediate SQL query and get the DataFrame
            df = run_sql(intermediate_sql)

            # Generate final SQL prompt with the intermediate SQL results
            prompt = get_sql_prompt(
                starting_prompt=starting_prompt,
                question=question,
                columns_list=columns,
                question_sql_list=question_sql_list,
                doc_list=doc_list + [f"The following is a pandas DataFrame with the results of the intermediate SQL query {intermediate_sql}:\n" + df.to_markdown()]
            )
            # print("Final SQL Prompt", prompt)
            # print("\nThis is the len of final input prompt:", len(prompt))

            # Generate LLM response for the final prompt
            llm_response = multimodal_model.generate_content(prompt)
            llm_response_text = llm_response.text  # Extract the response text again
            # print("LLM Response", llm_response_text)

        except Exception as e:
            return f"Error running intermediate SQL: {e}"

    # Extract the final SQL query from the LLM response
    final_sql = extract_sql(llm_response_text)

    return final_sql

def extract_sql(llm_response: str) -> str:
        # If the llm_response contains a CTE (with clause), extract the last sql between WITH and ;
        sqls = re.findall(r"\bWITH\b .*?;", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            # print(f"Extracted SQL - {sql}")
            return sql

        # If the llm_response is not markdown formatted, extract last sql by finding select and ; in the response
        sqls = re.findall(r"SELECT.*?;", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            # print(f"Extracted SQL - {sql}")
            return sql

        # If the llm_response contains a markdown code block, with or without the sql tag, extract the last sql from it
        sqls = re.findall(r"```sql\n(.*)```", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            # print(f"Extracted SQL - {sql}")
            return sql

        sqls = re.findall(r"```(.*)```", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            # print(f"Extracted SQL - {sql}")
            return sql

        return llm_response
from utility import create_sql_connection

def run_sql(sql: str):
    conn = create_sql_connection()
    
    # Check if connection was successful
    if conn is None:
        return "Failed to connect to the database."

    try:
        # Use pandas read_sql to fetch data directly into a DataFrame
        df = pd.read_sql(sql, conn)

        # Round numeric columns to one decimal place
        numeric_cols = df.select_dtypes(include=['number']).columns
        if not numeric_cols.empty:
            df[numeric_cols] = df[numeric_cols].astype('float64').round(1)

        # Set the index starting from 1
        df.index = np.arange(1, len(df) + 1)

        return df

    except Exception as e:
        return f"SQL Server error: {e}"
        
    finally:
        # Close the connection safely
        if conn:
            conn.close()