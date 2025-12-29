import mysql.connector
from colorama import Fore


class DatabaseManager:
    """Simple database connection and query execution"""

    def __init__(self, config: dict):
        self.config = config
        self.connection = None
        self.schema_text = ""

    def connect(self) -> bool:
        """Connect to MySQL database"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            return True
        except Exception as e:
            print(f"{Fore.RED}Connection Error: {e}")
            return False

    def get_schema(self) -> str:
        """Get simplified database schema for LLM"""
        if not self.connection or not self.connection.is_connected():
            self.connect()

        try:
            cursor = self.connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            schema_text = "DATABASE SCHEMA\n\n"

            for (table_name,) in tables:
                schema_text += f"TABLE: {table_name}\n"

                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()

                schema_text += "Columns:\n"
                for col_name, col_type, nullable, key, default, extra in columns:
                    schema_text += f" - {col_name} ({col_type})"
                    if key == "PRI":
                        schema_text += " PRIMARY KEY"
                    schema_text += "\n"

                cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
                samples = cursor.fetchall()

                if samples:
                    schema_text += "Sample rows:\n"
                    for row in samples:
                        schema_text += f"  {row}\n"

                schema_text += "\n"

            cursor.close()
            self.schema_text = schema_text
            return schema_text

        except Exception as e:
            print(f"{Fore.RED}Schema Error: {e}")
            return ""

    def execute_query(self, query: str, params: tuple = None) -> tuple:
        """Execute SQL query safely with auto-reconnect"""
        if not self.connection or not self.connection.is_connected():
            self.connect()

        query_upper = query.strip().upper()

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)

            if query_upper.startswith(
                ("SELECT", "SHOW", "DESCRIBE", "DESC", "EXPLAIN")
            ):
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                cursor.close()
                return True, results, columns

            self.connection.commit()
            cursor.close()
            return True, "Query executed successfully", None

        except Exception as e:
            if "gone away" in str(e).lower() or "lost connection" in str(e).lower():
                self.connect()
                try:
                    cursor = self.connection.cursor()
                    cursor.execute(query, params)

                    if query_upper.startswith(
                        ("SELECT", "SHOW", "DESCRIBE", "DESC", "EXPLAIN")
                    ):
                        results = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description]
                        cursor.close()
                        return True, results, columns

                    self.connection.commit()
                    cursor.close()
                    return True, "Query executed successfully", None

                except Exception as retry_error:
                    return False, str(retry_error), None

            return False, str(e), None
