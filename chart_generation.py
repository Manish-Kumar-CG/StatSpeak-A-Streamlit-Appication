import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
import re
import sqlparse
from llm_response_generator import LLMResponseGenerator

def should_generate_chart(df: pd.DataFrame) -> bool:
        if len(df) > 1 and df.select_dtypes(include=['number']).shape[1] > 0:
            return True

        return False
def system_message(message: str) -> any:
        return message
def user_message(message: str) -> any:
        return message
def generate_plotly_code(chart_query: str,question: str = None, sql: str = None, 
                            df_metadata: str = None, ) -> str:
        if question is not None:
            system_msg = f"The following is a pandas DataFrame that contains the results of the query that answers the question the user asked: '{question}'"
        else:
            system_msg = "The following is a pandas DataFrame "

        if sql is not None:
            system_msg += f"\n\nThe DataFrame was produced using this query: {sql}\n\n"

        system_msg += f"The following is information about the resulting pandas DataFrame 'df': \n{df_metadata}"

        if chart_query is not None:
            system_msg += f"Requirements of charts:\n{chart_query}"
        prompt = [
            system_message(system_msg),
            user_message(
                "Can you generate the Python plotly code according to requirement, to chart the results of the dataframe? Assume the data is in a pandas dataframe called 'df'. If there is only one value in the dataframe, use an Indicator. Respond with only Python code. Do not answer with any explanations -- just the code."
            ),
        ]

        llm = LLMResponseGenerator()
        plotly_code = llm.submit_prompt(prompt)
        return sanitize_plotly_code(extract_python_code(plotly_code))

def sanitize_plotly_code(raw_plotly_code: str) -> str:
        # Remove the fig.show() statement from the plotly code
        plotly_code = raw_plotly_code.replace("fig.show()", "")

        return plotly_code
def extract_python_code(markdown_string: str) -> str:
        # Regex pattern to match Python code blocks
        pattern = r"```[\w\s]*python\n([\s\S]*?)```|```([\s\S]*?)```"

        # Find all matches in the markdown string
        matches = re.findall(pattern, markdown_string, re.IGNORECASE)

        # Extract the Python code from the matches
        python_code = []
        for match in matches:
            python = match[0] if match[0] else match[1]
            python_code.append(python.strip())

        if len(python_code) == 0:
            return markdown_string

        return python_code[0]

def get_plotly_figure(
        plotly_code: str, df: pd.DataFrame, dark_mode: bool = True
    ) -> plotly.graph_objs.Figure:
        ldict = {"df": df, "px": px, "go": go}
        try:
            exec(plotly_code, globals(), ldict)

            fig = ldict.get("fig", None)
        except Exception as e:
            # Inspect data types
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            categorical_cols = df.select_dtypes(
                include=["object", "category"]
            ).columns.tolist()

            # Decision-making for plot type
            if len(numeric_cols) >= 2:
                # Use the first two numeric columns for a scatter plot
                fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1])
            elif len(numeric_cols) == 1 and len(categorical_cols) >= 1:
                # Use a bar plot if there's one numeric and one categorical column
                fig = px.bar(df, x=categorical_cols[0], y=numeric_cols[0])
            elif len(categorical_cols) >= 1 and df[categorical_cols[0]].nunique() < 10:
                # Use a pie chart for categorical data with fewer unique values
                fig = px.pie(df, names=categorical_cols[0])
            else:
                # Default to a simple line plot if above conditions are not met
                fig = px.line(df)

        if fig is None:
            return None

        if dark_mode:
            fig.update_layout(template="plotly_dark")

        return fig

def generate_summary(question: str, df: pd.DataFrame) -> str:
        message_log = [
            system_message(
                f"You are a helpful data assistant. The user asked the question: '{question}'\n\nThe following is a pandas DataFrame with the results of the query: \n{df.to_markdown()}\n\n"
            ),
            user_message(
                "Briefly summarize the data based on the question that was asked. Do not respond with any additional explanation beyond the summary." +
                "Respond in the English languague."
            ),
        ]
        llm = LLMResponseGenerator()
        summary = llm.submit_prompt(message_log)
        return summary