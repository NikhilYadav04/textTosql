import streamlit as st
import os
import time
import pandas as pd
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from agents.graph import create_graph
from database.manager import DatabaseManager
from utils.validator import validate_query

# Page config
st.set_page_config(
    page_title="Text-to-SQL Query Interface",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "db_connected" not in st.session_state:
    st.session_state.db_connected = False

if "llm_initialized" not in st.session_state:
    st.session_state.llm_initialized = False

if "query_history" not in st.session_state:
    st.session_state.query_history = []

if "current_results" not in st.session_state:
    st.session_state.current_results = None

# Sidebar for configuration
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    # Groq API Key
    with st.expander(
        "🔑 Groq API Configuration", expanded=not st.session_state.llm_initialized
    ):
        groq_api_key = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="sk_...",
            help="Enter your Groq API key",
        )

        if st.button("Initialize LLM", disabled=st.session_state.llm_initialized):
            if groq_api_key:
                try:
                    os.environ["GROQ_API_KEY"] = groq_api_key
                    st.session_state.llm = ChatGroq(
                        model="openai/gpt-oss-20b",
                        temperature=0.0,
                        max_tokens=2048,
                        groq_api_key=groq_api_key,
                    )
                    st.session_state.llm_initialized = True
                    st.success("✅ LLM initialized successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to initialize LLM: {e}")
            else:
                st.warning("Please enter Groq API key")

    if st.session_state.llm_initialized:
        st.success("🤖 LLM Ready")

    # Database Configuration
    with st.expander(
        "🗄️ Database Configuration", expanded=not st.session_state.db_connected
    ):
        db_host = st.text_input("Host", value="localhost")
        db_port = st.number_input("Port", value=3306, min_value=1)
        db_user = st.text_input("Username", placeholder="root")
        db_password = st.text_input("Password", type="password")
        db_name = st.text_input("Database Name", placeholder="your_database")

        if st.button("Connect to Database", disabled=st.session_state.db_connected):
            if all([db_host, db_user, db_name]):
                config = {
                    "host": db_host,
                    "user": db_user,
                    "password": db_password,
                    "database": db_name,
                    "port": db_port,
                }

                with st.spinner("Connecting to database..."):
                    db = DatabaseManager(config)
                    if db.connect():
                        st.session_state.db = db
                        st.session_state.db_connected = True
                        st.session_state.schema = db.get_schema()
                        st.success("✅ Database connected successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to connect to database")
            else:
                st.warning("Please fill in all required fields")

    if st.session_state.db_connected:
        st.success("🟢 Database Connected")

        if st.button("Disconnect Database"):
            st.session_state.db_connected = False
            st.session_state.db = None
            st.rerun()

# Show schema if connected
if st.session_state.db_connected:
    with st.expander("📊 Database Schema"):
        st.code(st.session_state.schema, language="sql")

# Query History
if st.session_state.query_history:
    with st.expander("🕘 Query History"):
        for i, item in enumerate(reversed(st.session_state.query_history[-5:])):
            st.markdown(f"**Query {i + 1}:** {item}")

# Main content area
if not st.session_state.llm_initialized or not st.session_state.db_connected:
    st.info(
        "Please configure Groq API and Database connection in the sidebar to get started"
    )
else:
    # Query input section
    col1, col2 = st.columns([4, 1])

    with col1:
        user_query = st.text_area(
            "Enter your question in natural language:",
            placeholder="e.g., Show me all students with CGPA greater than 8.0",
            height=100,
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        execute_button = st.button(
            "🚀 Execute Query", type="primary", use_container_width=True
        )

    # Sample queries
    st.markdown("### 🧪 Sample Queries")
    sample_queries = [
        "Show me all female students",
        "Count the number of students",
        "Show the student with the highest CGPA",
        "List all tables in the database",
    ]

    cols = st.columns(len(sample_queries))
    for i, query in enumerate(sample_queries):
        with cols[i]:
            if st.button(f"📌 {i+1}", help=query, use_container_width=True):
                st.session_state.sample_query = query
                st.rerun()

    # Use sample query if selected
    if "sample_query" in st.session_state:
        user_query = st.session_state.sample_query
        del st.session_state.sample_query
        execute_button = True

    # Execute query
    if execute_button and user_query:
        # Validation first
        with st.spinner("Validating query..."):
            is_sql_query, response_text = validate_query(
                user_query, st.session_state.llm
            )

        if not is_sql_query:
            # Non-SQL query: show response and stop
            st.info("💬 Direct Response")
            st.markdown(
                f"<div class='status-box'>{response_text}</div>", unsafe_allow_html=True
            )

            # Store in history as non-SQL
            st.session_state.query_history.append(
                {
                    "query": user_query,
                    "sql": None,
                    "answer": response_text,
                    "timestamp": datetime.now(),
                    "is_sql": False,
                }
            )

        else:
            # Create the graph
            app = create_graph(db=st.session_state.db)

            # Initialize state
            initial_state = {
                "messages": [HumanMessage(content=user_query)],
                "user_query": user_query,
                "schema": st.session_state.schema,
                "retry_count": 0,
            }

            # Progress tracking
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()

            # Results container
            results_container = st.container()

            with results_container:
                # Execution stages (collapsible)
                execution_expander = st.expander("🧩 Execution Pipeline", expanded=True)

                with execution_expander:
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        sql_gen_status = st.empty()
                        sql_gen_status.info("⚙️ Generating SQL...")

                    with col2:
                        sql_exec_status = st.empty()
                        sql_exec_status.info("⏳ Waiting...")

                    with col3:
                        format_status = st.empty()
                        format_status.info("⏳ Waiting...")

                    with col4:
                        eval_status = st.empty()
                        eval_status.info("⏳ Waiting...")

            # Execute workflow
            config = {
                "configurable": {"thread_id": f"query_{datetime.now().timestamp()}"}
            }

            try:
                step_count = 0
                total_steps = 4

                for step in app.stream(initial_state, config):
                    step_count += 1
                    progress_bar.progress(step_count / total_steps)

                    for key, value in step.items():
                        status_text.text(f"Processing: {key}")

                        if key == "generate_sql":
                            with execution_expander:
                                with col1:
                                    sql_gen_status.success("✅ SQL Generated")
                                    if value.get("sql_query"):
                                        st.code(value["sql_query"], language="sql")

                        elif key == "execute_sql":
                            with execution_expander:
                                with col2:
                                    if value.get("error"):
                                        sql_exec_status.error(
                                            f"❌ {value['error'][:50]}"
                                        )
                                    else:
                                        sql_exec_status.success("✅ Query Executed")
                                        if value.get("results"):
                                            st.metric(
                                                "Rows", value["results"]["row_count"]
                                            )

                        elif key == "format_answer":
                            with execution_expander:
                                with col3:
                                    format_status.success("📝 Answer Formatted")

                        elif key == "evaluate":
                            with execution_expander:
                                with col4:
                                    eval_status.success("📊 Evaluated")

                                    # Score is in the returned value from evaluate_node
                                    if value.get("evaluation_score") is not None:
                                        score_val = value["evaluation_score"]
                                        st.metric("Score", f"{score_val:.2f}")

                    time.sleep(0.5)  # Small delay for visual effect

                # Get final state
                final_state = app.get_state(config).values

                # Collapse execution details
                execution_expander.expanded = False

                # Display results
                st.markdown("---")

                if final_state.get("answer"):
                    st.success("🎉 Query executed successfully!")

                    # Display answer
                    answer_container = st.container()
                    with answer_container:
                        st.markdown("### 📌 Answer")
                        st.markdown(
                            f"<div class='status-box'>{final_state['answer']}</div>",
                            unsafe_allow_html=True,
                        )

                # Display RAGAS Evaluation Score
                if "evaluation_score" in final_state:
                    st.markdown("## 📈 Quality Assessment")

                    score = final_state.get("evaluation_score", 0)

                    # Create columns for score display
                    score_cols = st.columns([2, 1, 2])

                    with score_cols[1]:
                        # Determine score color and emoji
                        if score >= 0.8:
                            score_color = "#4CAF50"  # Green
                            score_emoji = "🏆"
                            score_label = "Excellent"
                        elif score >= 0.6:
                            score_color = "#FFB300"  # Yellow
                            score_emoji = "👍"
                            score_label = "Good"
                        elif score >= 0.4:
                            score_color = "#FF9800"  # Orange
                            score_emoji = "⚠️"
                            score_label = "Fair"
                        else:
                            score_color = "#F44336"  # Red
                            score_emoji = "❌"
                            score_label = "Poor"

                        # Display score in a circular badge style
                        st.markdown(
                            f"""
                            <div style="text-align: center; padding: 1rem;">
                                <div style="
                                    display: inline-block;
                                    width: 150px;
                                    height: 150px;
                                    border-radius: 50%;
                                    background: linear-gradient(135deg, {score_color}22, {score_color}44);
                                    border: 3px solid {score_color};
                                    display: flex;
                                    flex-direction: column;
                                    justify-content: center;
                                    align-items: center;
                                    box-shadow: 0 4px 15px rgba(255, 214, 102, 0.3);
                                ">
                                    <span style="font-size: 2.5rem; font-weight: bold; color: {score_color};">
                                        {score:.1%}
                                    </span>
                                    <span style="font-size: 1rem; color: #ffd666;">
                                        {score_emoji} {score_label}
                                    </span>
                                </div>
                                <p style="color: #ffd666; margin-top: 1rem; font-size: 0.9rem;">
                                    RAGAS Answer Accuracy Score
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # Add score breakdown in expandable section
                    with st.expander("📊 Score Details", expanded=False):
                        st.markdown(
                            f"""
                            **Evaluation Metrics**
                            - **Answer Accuracy**: {score:.2%}
                            - **Query**: {final_state.get('user_query', 'N/A')}
                            - **SQL Generated**: `{final_state.get('sql_query', 'N/A')}`
                            - **Rows Retrieved**: {final_state.get('results', {}).get('row_count', 0)}

                            **Score Interpretation**
                            - 🟢 **80–100%**: Excellent – Highly accurate and relevant
                            - 🟡 **60–79%**: Good – Mostly accurate, minor gaps
                            - 🟠 **40–59%**: Fair – Partial accuracy, needs improvement
                            - 🔴 **0–39%**: Poor – Low accuracy or relevance
                            """
                        )

                    # Mini progress bar
                    st.progress(score)
                    st.caption(
                        "The RAGAS evaluation compares the generated answer against "
                        "the actual query results to measure accuracy and relevance."
                    )

                # Display results table if available
                if final_state.get("results") and final_state["results"].get("rows"):
                    st.markdown("### 📋 Results Table")

                    results = final_state["results"]
                    df = pd.DataFrame(results["rows"], columns=results["columns"])

                    # Display controls
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        show_all = st.checkbox("Show all rows", value=False)

                    if show_all:
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.dataframe(df.head(10), use_container_width=True)
                        if len(df) > 10:
                            st.info(
                                f"Showing 10 of {len(df)} rows. "
                                "Check 'Show all rows' to see more."
                            )

                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download as CSV",
                        data=csv,
                        file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )

                    # Store in history
                    st.session_state.query_history.append(
                        {
                            "query": user_query,
                            "sql": final_state.get("sql_query"),
                            "answer": final_state.get("answer"),
                            "timestamp": datetime.now(),
                        }
                    )

                    # Store current results
                    st.session_state.current_results = final_state

                elif final_state.get("error"):
                    st.error(f"❌ Error: {final_state['error']}")

                # Clean progress indicators
                progress_bar.empty()
                status_text.empty()

            # Error handling
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                progress_bar.empty()
                status_text.empty()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="
        text-align: center;
        color: #ffd666;
        background: rgba(0,0,0,0.8);
        padding: 1rem;
        border-radius: 10px;
    ">
        <p>
            Built with <b>LangGraph</b>, <b>Groq</b>, and <b>Streamlit</b> |
            Text-to-SQL Pipeline with <b>RAGAS Evaluation</b>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
