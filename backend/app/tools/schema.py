import re
from typing import List, Dict
from app.tools.sql import get_table_names, get_table_schema


def _extract_enum_annotations(schema: str) -> str:
    """
    Parses CHECK(column IN ('val1','val2',...)) constraints from a CREATE TABLE
    statement and returns readable annotations like:
      -- column valid values: val1, val2, val3
    """
    # Match patterns like: CHECK(column_name IN ('val1','val2','val3'))
    pattern = r"CHECK\s*\(\s*(\w+)\s+IN\s*\(([^)]+)\)\s*\)"
    matches = re.findall(pattern, schema, re.IGNORECASE)
    
    if not matches:
        return ""
    
    lines = ["-- Column valid values:"]
    for col_name, values_str in matches:
        # Clean up: remove quotes and whitespace
        values = [v.strip().strip("'\"") for v in values_str.split(",")]
        lines.append(f"--   {col_name}: {', '.join(values)}")
    
    return "\n".join(lines)


def get_database_schema_string(table_names: List[str] = None) -> str:
    """
    Returns a formatted string containing the schema for the specified tables.
    If no tables are specified, returns schema for all tables.
    Includes enum value annotations extracted from CHECK constraints.
    """
    if not table_names:
        table_names = get_table_names()
    
    schema_parts = []
    for table in table_names:
        schema = get_table_schema(table)
        if schema:
            annotations = _extract_enum_annotations(schema)
            if annotations:
                schema_parts.append(f"{schema}\n{annotations}")
            else:
                schema_parts.append(schema)
            
    return "\n\n".join(schema_parts)

def get_all_table_names_formatted() -> str:
    """Returns a comma-separated string of all table names."""
    return ", ".join(get_table_names())
