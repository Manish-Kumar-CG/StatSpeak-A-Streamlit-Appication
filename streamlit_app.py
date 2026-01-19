import time
import streamlit as st
from helper import (
    generate_sql_cached,
    run_sql_cached,
    generate_plotly_code_cached,
    generate_plot_cached,
    should_generate_chart_cached,
    is_sql_valid_cached,
    generate_summary_cached
)
from datetime import datetime

if 'session_id' not in st.session_state:
    st.session_state['session_id'] = datetime.now().timestamp()
    st.cache_data.clear()

USER_AVATAR = "🧑‍💻"
BOT_AVATAR = "🤖"

st.set_page_config(page_title="Conversational BI", page_icon="static/logo.png", layout="wide")

with open('static/style.css') as f:
    css = f.read()

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

st.session_state["show_sql"] = True
st.session_state["show_table"] = True
st.session_state["show_plotly_code"] = False
st.session_state["show_chart"] = True
st.session_state["show_summary"] = True

def set_question(question):
    st.session_state["my_question"] = question

def clear_df():
    if "df" in st.session_state:
        del st.session_state["df"]

st.chat_message(
    "assistant", avatar=BOT_AVATAR
).write("Hi there! I'm your Virtual Assistant. I can assist you with your business inquiries related to Products, Orders, Campaigns, Channels, or Revenue.")

my_question = st.session_state.get("my_question", default=None)

for message in st.session_state.messages:
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        if message["role"] == "assistant":
            if st.session_state["show_sql"] and message["content"].get("sql", False):
                st.code(message["content"]["sql"], language="sql", line_numbers=True)
            if st.session_state["show_table"]:
                df = message["content"].get("df")
                if df is not None:
                    st.dataframe(df)
            if st.session_state["show_chart"]:
                chart_history = message["content"].get("chart")
                if chart_history:
                    st.plotly_chart(chart_history)
            if st.session_state["show_summary"]:
                summary_history = message["content"].get("summary")
                if summary_history:
                    st.text(summary_history)
        else:
            st.markdown(message["content"])

if my_question := st.chat_input(
        "Ask me a question ",
    ):
    set_question(None)
    clear_df()
    st.session_state.messages.append({"role": "user", "content": my_question})
    if my_question:
        st.session_state["my_question"] = my_question
        user_message = st.chat_message("user", avatar=USER_AVATAR)
        user_message.write(f"{my_question}")
        temp = {}
        try:
            sql = generate_sql_cached(question=my_question)
            if sql:
                if is_sql_valid_cached(sql=sql):
                    if st.session_state.get("show_sql", True):
                        assistant_message_sql = st.chat_message(
                            "assistant", avatar=BOT_AVATAR
                        )
                        assistant_message_sql.code(sql, language="sql", line_numbers=True)
                else:
                    assistant_message = st.chat_message(
                        "assistant", avatar=BOT_AVATAR
                    )
                    assistant_message.error('Error in generated sql. Please try again.')
                    st.stop()
                temp["sql"] = sql
                df = run_sql_cached(sql=sql)
                if df is not None:
                    st.session_state["df"] = df
                if st.session_state.get("df") is not None:
                    if st.session_state.get("show_table", True):
                        df = st.session_state.get("df")
                        assistant_message_table = st.chat_message(
                            "assistant",
                            avatar=BOT_AVATAR,
                        )
                        assistant_message_table.dataframe(df)
                        temp["df"] = df
                    build_chart = st.radio("Do you want to build a chart from the data?", ("No", "Yes"))
                    if build_chart == "Yes":
                        chart_query = st.chat_input("Describe the chart you want (e.g., 'generate a pie chart using sales and region')")    
                    if should_generate_chart_cached(question=my_question, sql=sql, df=df):
                        code = generate_plotly_code_cached(question=my_question, sql=sql, df=df)
                        if st.session_state.get("show_plotly_code", False):
                            assistant_message_plotly_code = st.chat_message(
                                "assistant",
                                avatar=BOT_AVATAR,
                            )
                            assistant_message_plotly_code.code(
                                code, language="python", line_numbers=True
                            )
                        if code is not None and code != "":
                            if st.session_state.get("show_chart", True):
                                assistant_message_chart = st.chat_message(
                                    "assistant",
                                    avatar=BOT_AVATAR,
                                )
                                fig = generate_plot_cached(code=code, df=df)
                                if fig is not None:
                                    assistant_message_chart.plotly_chart(fig)
                                    temp["chart"] = fig
                                else:
                                    assistant_message_chart.error("I couldn't generate a chart")
                    if st.session_state.get("show_summary", True):
                        df = st.session_state.get("df")
                        assistant_message_summary = st.chat_message(
                            "assistant",
                            avatar=BOT_AVATAR,
                        )
                        summary = generate_summary_cached(question=my_question, df=df)
                        if summary is not None:
                            assistant_message_summary.text(summary)
                            temp["summary"] = summary
                st.session_state.messages.append({"role":"assistant", "content":temp})
            else:
                assistant_message_error = st.chat_message(
                    "assistant", avatar=BOT_AVATAR
                )
                assistant_message_error.error("Unable to generate response for that question")
        except Exception as ex:
            print(f'An error occurred while processing the request. Error - {ex}')
            st.cache_data.clear()
            st.error("An error occurred while processing the request. Please try again. If the issue persists, contact the support team")
