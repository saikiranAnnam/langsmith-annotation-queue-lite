"""
Utility functions for working with SQL queries.
"""

import re
from typing import Any


def prepare_query(query: str, **params: Any) -> tuple[str, list[Any]]:
    """
    Convert a query with named parameters to positional parameters.

    Takes a query string with $param_name placeholders and converts them
    to $1, $2, etc. for use with asyncpg, returning the converted query
    and the ordered parameter values.

    Args:
        query: SQL query string with named parameters like $param_name
        **params: Keyword arguments mapping parameter names to values

    Returns:
        Tuple of (converted_query, ordered_params)

    Example:
        >>> query = "SELECT * FROM users WHERE id = $user_id AND name = $name"
        >>> sql, args = prepare_query(query, user_id=123, name="Alice")
        >>> # sql = "SELECT * FROM users WHERE id = $1 AND name = $2"
        >>> # args = [123, "Alice"]
    """
    # Find all named parameters in the query (e.g., $param_name)
    # Match $ followed by word characters (letters, digits, underscores)
    param_pattern = re.compile(r"\$(\w+)")

    # Find all unique parameter names in order of first appearance
    matches = param_pattern.findall(query)
    seen = set()
    ordered_param_names = []
    for match in matches:
        if match not in seen:
            ordered_param_names.append(match)
            seen.add(match)

    # Build the list of parameter values in order
    ordered_params = []
    for param_name in ordered_param_names:
        if param_name not in params:
            raise ValueError(f"Missing parameter: {param_name}")
        ordered_params.append(params[param_name])

    # Replace named parameters with positional ones
    converted_query = query
    for i, param_name in enumerate(ordered_param_names, start=1):
        # Use word boundaries to avoid partial replacements
        converted_query = re.sub(rf"\${param_name}\b", f"${i}", converted_query)

    return converted_query, ordered_params
