import streamlit as st
from sql_generation import generate_sql, run_sql
from chart_generation import should_generate_chart, generate_plotly_code, get_plotly_figure, generate_summary

@st.cache_data(show_spinner="Fetching Results...")
def generate_sql_cached(question:str):
    return generate_sql(question)

@st.cache_data(show_spinner="Generating Response ...")
def run_sql_cached(sql: str):
    return run_sql(sql=sql)

@st.cache_data(show_spinner="Checking if Chart can be generated from given result...")
def should_generate_chart_cached(df):
    return should_generate_chart(df=df)

@st.cache_data(show_spinner="Generating Chart ...")
def generate_plotly_code_cached(chart_query,question, sql, df):
    code = generate_plotly_code(chart_query, question=question, sql=sql,df_metadata=f"Running df.dtypes gives:\n {df.dtypes}")
    return code

@st.cache_data(show_spinner="Generating Chart ...")
def generate_plot_cached(code, df):
    return get_plotly_figure(plotly_code=code, df=df)

@st.cache_data(show_spinner="Generating summary ...")
def generate_summary_cached(question, df):
    return generate_summary(question=question, df=df)