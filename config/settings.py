import os
from langchain_groq import ChatGroq

# GROQ API Configuration
GROQ_API_KEY = ""
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# MySQL Configuration
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "",
    "port": 3306,
}

# Initialize GROQ LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.0,
    max_tokens=2048,
    api_key=GROQ_API_KEY,
)

print("Configuration loaded successfully")
