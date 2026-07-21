import re
from typing import Tuple

FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT", "ALTER", "GRANT", "REVOKE"
]

def validate_sql_safety(query: str) -> Tuple[bool, str]:
    """
    Validates that the SQL query is read-only and safe to execute.
    Returns (is_safe, error_message).
    """
    # Normalize query
    normalized = query.upper()
    
    # Check for forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:
        # Check for keyword as a whole word
        if re.search(r'\b' + keyword + r'\b', normalized):
            return False, f"SQL query contains forbidden keyword: {keyword}. Only read-only queries are allowed."
            
    # Check for cartesian products
    is_safe_join, join_error = check_cartesian_product(query)
    if not is_safe_join:
        return False, join_error
        
    return True, ""


def check_cartesian_product(query: str) -> Tuple[bool, str]:
    """
    Detects cartesian product risk when multiple JOINs are used with aggregation
    but without subqueries to pre-aggregate each source.
    """
    normalized = query.upper()
    
    # Only applies to queries with SUM or COUNT
    if "SUM(" not in normalized and "COUNT(" not in normalized:
        return True, ""
    
    # Count JOINs — need 2+ for cartesian risk
    join_count = len(re.findall(r'\bJOIN\b', normalized))
    if join_count < 2:
        return True, ""
    
    # If subqueries exist (multiple SELECTs), the model is already handling it
    select_count = len(re.findall(r'\bSELECT\b', normalized))
    if select_count > 1:
        return True, ""
    
    # 2+ JOINs + aggregation + no subqueries = cartesian risk
    return False, (
        "Cartesian product risk: Query joins multiple tables and aggregates "
        "(SUM/COUNT) without using subqueries. Pre-aggregate each source in "
        "a subquery first, then JOIN the subquery results."
    )
