import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from colorama import Fore


def validate_query(query: str, llm) -> tuple:
    """Validates if query should go through SQL pipeline
    Returns : {
        is_sql_query:bool, response: str
    }
    """

    validation_prompt = ChatPromptTemplate.from_template(
        """
You are a gatekeeper for a SQL database query system. Analyze the user's input.

User Input: {query}

STRICT RULES:
1. If this is a GENUINE DATABASE QUERY (asking to retrieve, count, show, list, find data from database)
   → Return ONLY the word: TRUE
2. If this is ANYTHING ELSE (greeting, gibberish, out-of-context question, general chat)
   → Return a natural language response

Examples of genuine database queries (return "TRUE"):
- Show me all students
- Count the records
- What is the highest CGPA?
- List all tables
- Find students with marks > 80

Examples of non-database queries (return natural response):
- "Hello! I can help you query a database. What data would you like to retrieve?"
- "How are you?"
- "I'm a database assistant. I can help you retrieve data from your database. What would you like to know?"
- "What's 2+2?"
- "I specifically designed for database queries. Please ask about what you'd like to retrieve."
- "asdfgh123"
- "I couldn't understand that. Please ask a clear question about your database."
- "Write Python code" → I only handle database queries. Please ask about retrieving data from your database.

Remember:
Return ONLY "TRUE" (nothing else) for database queries,
or a helpful natural language response for everything else.

Response:
"""
    )
    chain = validation_prompt | llm | StrOutputParser()

    try:
        result = chain.invoke({"query": query})
        result = result.strip()

        true_pattern = re.compile(r"^TRUE$", re.IGNORECASE)

        if true_pattern.match(result):
            return True, None

        elif "TRUE" in result.upper() and len(result) < 10:
            cleaned = re.sub(r"[^A-Z]", "", result.upper())
            if cleaned == "TRUE":
                return True, None

        return False, result

    except Exception as e:
        print(f"{Fore.YELLOW}Validation error: {e}")
        # Default to processing as SQL if validation fails
        return True, None