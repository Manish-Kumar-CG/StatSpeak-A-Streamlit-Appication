import streamlit as st
import pandas as pd
from datetime import datetime
from helper import (
    generate_sql_cached,
    run_sql_cached,
    generate_plotly_code_cached,
    generate_plot_cached,
    should_generate_chart_cached,
    generate_summary_cached
)

# --- Session Setup ---
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = datetime.now().timestamp()
    st.cache_data.clear()

# Initialize State Variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_df" not in st.session_state:
    st.session_state.active_df = None  
if "active_sql" not in st.session_state:
    st.session_state.active_sql = None
if "active_question" not in st.session_state:
    st.session_state.active_question = None

# Config Flags
if "show_sql" not in st.session_state: st.session_state["show_sql"] = True
if "show_table" not in st.session_state: st.session_state["show_table"] = True
if "show_plotly_code" not in st.session_state: st.session_state["show_plotly_code"] = False
if "show_chart" not in st.session_state: st.session_state["show_chart"] = True
if "show_summary" not in st.session_state: st.session_state["show_summary"] = True

USER_AVATAR = "🧑‍💻"
BOT_AVATAR = "🤖"

st.set_page_config(page_title="Statspeak", layout="wide")
# CSS loading
try:
    with open('static/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass
st.header("Statspeak")

st.chat_message("assistant", avatar=BOT_AVATAR).write(
    "Hi there! I'm your Virtual Assistant. I can assist you with your business inquiries."
)

# --- 1. DISPLAY HISTORY ---
for message in st.session_state.messages:
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        content = message["content"]
        if message["role"] == "assistant" and isinstance(content, dict):
            # 1. SQL
            if st.session_state["show_sql"] and content.get("sql"):
                st.code(content["sql"], language="sql")
            # 2. Table
            if st.session_state["show_table"]:
                df_hist = content.get("df")
                if df_hist is not None:
                    st.dataframe(df_hist)
            # 3. Chart (Displayed BEFORE Summary)
            if st.session_state["show_chart"]:
                chart_hist = content.get("chart")
                if chart_hist:
                    st.plotly_chart(chart_hist)
            # 4. Summary (Displayed LAST)
            if st.session_state["show_summary"]:
                summary_hist = content.get("summary")
                if summary_hist:
                    st.write(summary_hist)
        elif isinstance(content, str):
             st.markdown(content)

# --- 2. HANDLE INTERACTION (Chart & Summary) ---
# This runs if we have a DataFrame waiting for user input
if st.session_state.active_df is not None:
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        st.write("Data retrieved. Would you like to visualize this?")
        
        col1, col2 = st.columns([1, 4])
        
        # Radio Button
        chart_choice = st.radio(
            "Generate Chart?", 
            ("No", "Yes"), 
            horizontal=True, 
            key="chart_decision_radio"
        )
        
        # --- PATH A: USER WANTS A CHART ---
        if chart_choice == "Yes":

            chart_query = st.text_input(
                "Describe the chart (e.g., 'Pie chart of sales by region')",
                key="chart_query_input"
            )

            if st.button("Generate Chart & Summary"):
                if chart_query:
                    with st.spinner("Generating chart and summary..."):
                        df = st.session_state.active_df
                        sql = st.session_state.active_sql
                        orig_q = st.session_state.active_question

                        code = generate_plotly_code_cached(
                            chart_query=chart_query,
                            question=orig_q,
                            sql=sql,
                            df=df
                        )
                        fig = generate_plot_cached(code=code, df=df)
                        summary = generate_summary_cached(question=orig_q, df=df) if st.session_state["show_summary"] else None

                        # Show chart and summary immediately
                        if fig:
                            st.plotly_chart(fig)
                        if summary:
                            st.write(summary)

                        # Update history for future display
                        last_msg_index = len(st.session_state.messages) - 1
                        if last_msg_index >= 0:
                            st.session_state.messages[last_msg_index]["content"]["chart"] = fig
                            if summary:
                                st.session_state.messages[last_msg_index]["content"]["summary"] = summary

                        # Now clear state and rerun if you want to reset UI
                        st.session_state.active_df = None
                        st.rerun()

        # --- PATH B: USER DOES NOT WANT A CHART ---
        elif chart_choice == "No":
            if st.button("Generate Summary Only"):
                with st.spinner("Generating summary..."):
                    df = st.session_state.active_df
                    orig_q = st.session_state.active_question
                    
                    last_msg_index = len(st.session_state.messages) - 1
                    if last_msg_index >= 0:
                        # Generate Summary (Since they skipped the chart)
                        if st.session_state["show_summary"]:
                            summary = generate_summary_cached(question=orig_q, df=df)
                            if summary:
                                st.session_state.messages[last_msg_index]["content"]["summary"] = summary
                    
                    # Clear State & Refresh
                    st.session_state.active_df = None
                    st.rerun()

# --- 3. HANDLE INITIAL QUESTION ---
if my_question := st.chat_input("Ask me a question"):
    # Clear old active state if user starts over
    st.session_state.active_df = None 
    
    st.session_state.messages.append({"role": "user", "content": my_question})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.write(my_question)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Analyzing..."):
            temp_response = {}
            try:
                # 1. Generate SQL
                sql = generate_sql_cached(question=my_question)
                if sql:
                    temp_response["sql"] = sql
                    if st.session_state["show_sql"]:
                        st.code(sql, language="sql")

                    # 2. Run SQL
                    df = run_sql_cached(sql=sql)
                    if df is not None:
                        temp_response["df"] = df
                        if st.session_state["show_table"]:
                            st.dataframe(df)

                        # NOTE: WE DO NOT GENERATE SUMMARY HERE ANYMORE
                        
                        # Save partial response to history
                        st.session_state.messages.append({"role": "assistant", "content": temp_response})
                        
                        # Set Active State to trigger Interaction Block
                        st.session_state.active_df = df
                        st.session_state.active_sql = sql
                        st.session_state.active_question = my_question
                        
                        st.rerun() 
                    else:
                        st.error("SQL returned no data.")
                else:
                    st.error("Could not generate SQL.")
            except Exception as e:
                st.error(f"Error: {e}")