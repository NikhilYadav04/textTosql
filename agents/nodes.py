from colorama import Fore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from agents.state import AgentState


def generate_sql_node(state: AgentState, db, llm) -> dict:
    """Generate SQL from natural language"""

    prompt = ChatPromptTemplate.from_template(
        """
    You are a SQL expert. Generate a MySQL query for this request.
    
    Database Schema:
    {schema}
    
    User Request : {query}
    
    Rules:
    1. Use ONLY tables and columns from the schema
    2. Generate valid MySQL syntax
    3. Use JOINs when needed
    4. Return ONLY the SQL query, no explanations
    
    SQL Query :
    """
    )

    chain = prompt | llm | StrOutputParser()

    try:
        sql = chain.invoke({"schema": state["schema"], "query": state["user_query"]})

        # Clean SQL
        sql = sql.strip()
        if sql.startswith("```"):
            sql = sql.split("```")[1].replace("sql", "").strip()

        print(f"{Fore.YELLOW}Generated SQL : {sql}")

        return {"sql_query": sql, "messages": [AIMessage(content=f"SQL generated")]}
    except Exception as e:
        return {
            "error": f"SQL generation failed : {str(e)}",
            "messages": [AIMessage(content=f"Error : {str(e)}")],
        }


def execute_sql_node(state: AgentState, db, llm):
    """Execute SQL with retry node"""

    if not state.get("sql_query"):
        return {"error": "No SQL to execute"}

    sql = state["sql_query"]
    retry_count = state.get("retry_count", 0)

    # Basic SQL injection check
    dangerous = ["DROP", "DELETE", "UPDATE", "INSERT"]

    sql_upper = sql.upper()

    if not sql_upper.startswith("SELECT") and any(d in sql_upper for d in dangerous):
        return {"error": "Unsafe SQL detected"}

    # Execute query
    success, data, columns = db.execute_query(sql)

    if not success and retry_count < 2:
        # If failed, try to fix and retry
        fix_prompt = ChatPromptTemplate.from_template(
            """
         The following SQL query failed with error : {error}
    
         Original SQL : {sql}
    
        Database Schema :
        {schema}
    
         Generate a corrected SQL query that fixes the error. Return ONLY the SQL : 
         """
        )

        chain = fix_prompt | llm | StrOutputParser()

        try:
            fixed_sql = chain.invoke(
                {"error": data, "sql": sql, "schema": state["schema"]}
            )

            # Clean fixed SQL
            fixed_sql = fixed_sql.strip()
            if fixed_sql.startswith("```"):
                fixed_sql = fixed_sql.split("```")[1].replace("sql", "").strip()

            print(f"{Fore.YELLOW}Retrying with fixed SQL : {fixed_sql}")

            success, data, columns = db.execute_query(fixed_sql)

            if success:
                results = {"columns": columns, "rows": data, "row_count": len(data)}
                return {
                    "results": results,
                    "sql_query": fixed_sql,
                    "retry_count": retry_count + 1,
                    "messages": [AIMessage(content="Query executed after retry")],
                }
        except:
            pass

    if success:
        results = {
            "columns": columns if columns else [],
            "rows": data if columns else [],
            "row_count": len(data) if columns else 0,
        }

        print(f"{Fore.GREEN}Query executed : {results['row_count']} rows")

        return {
            "results": results,
            "messages": [AIMessage(content=f"Query executed successfully")],
        }
    else:
        return {
            "error": f"Execution failed : {data}",
            "retry_count": retry_count + 1,
            "messages": [AIMessage(content=f"Error: {data}")],
        }


def format_answer_node(state: AgentState, llm) -> dict:
    """Format results as natural language"""

    if state.get("error"):
        return {
            "answer": f"I encountered an error {state['error']}",
            "messages": [AIMessage],
        }

    if not state.get("results"):
        return {
            "answer": "No results to display",
            "messages": [AIMessage(content="No results")],
        }

    results = state["results"]

    # Prepare data for LLM

    if results["rows"]:
        # Format first 10 rows
        rows_text = f"Columns : {results['columns']}\n"
        for i, row in enumerate(results["rows"][:10]):
            rows_text += f"Row {i+1}: {row}\n"
        if results["row_count"] > 10:
            rows_text += f"... and {results['row_count'] - 10} more rows"
    else:
        rows_text = "No data found"

    prompt = ChatPromptTemplate.from_template(
        """Convert these SQL results into a clear answer for the user.
    
    User Question : {question}
    SQL Query : {sql}
    Results ({count} rows):
    {results}
    
    Provide a concise, informative answer :"""
    )

    chain = prompt | llm | StrOutputParser()

    try:
        answer = chain.invoke(
            {
                "question": state["user_query"],
                "sql": state["sql_query"],
                "results": rows_text,
                "count": results["row_count"],
            }
        )

        return {"answer": answer, "messages": [AIMessage(content="Answer formatted")]}
    except Exception as e:
        return {
            "answer": f"Results {results['row_count']} rows found",
            "messages": [AIMessage(content="Basic answer provided")],
        }


def evaluate_node(state: AgentState, llm) -> dict:
    """Simple RAGAS evaluation"""

    if not state.get("answer") or not state.get("sql_query"):
        return {"messages": [AIMessage(content="Skipping evaluation")]}

    try:
        from ragas.llms import LangchainLLMWrapper
        from ragas.dataset_schema import SingleTurnSample
        from ragas.metrics import AnswerAccuracy

        # Setup RAGAS with Groq
        ragas_llm = LangchainLLMWrapper(llm)

        results_retrieved = str(state.get("results"))

        sample = SingleTurnSample(
            user_input=state["user_query"],
            response=state["answer"],
            reference=(
                f"SQL: {state['sql_query']}\n"
                f"Results Retrieved after execution of Query: {results_retrieved}"
            ),
        )

        scorer = AnswerAccuracy(llm=ragas_llm)
        score = scorer.single_turn_score(sample)
        print(score)

        print(f"{Fore.GREEN}RAGAS Score: {score:.2f}")

        return {
            "evaluation_score": score,
            "messages": [AIMessage(content=f"Evaluation: {score:.2f}")],
        }

    except Exception as e:
        print(f"{Fore.YELLOW}Evaluation skipped: {str(e)}")
        return {"messages": [AIMessage(content="Evaluation skipped")]}
