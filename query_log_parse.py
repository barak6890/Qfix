import re


def parse_to_query(variables, Q):
    pass

def parse_assignment(expr):
    """
    Parse a single assignment expression from the SET clause.
    For example, "A+1000" is parsed into:
      { "left_operand": "A", "operator": "+", "right_operand": "1000" }
    If no binary operator is found, returns the literal expression.
    """
    expr = expr.strip()
    m = re.match(r"^(\w+)\s*([\+\-\*\/])\s*([\w\.]+)$", expr)
    if m:
        return {
            "left_operand": m.group(1),
            "operator": m.group(2),
            "right_operand": m.group(3)
        }
    else:
        return {"expression": expr}

def parse_condition(cond):
    """
    Parse a simple condition from a WHERE clause.
    For example, "A>=85700" is parsed into:
      { "attribute": "A", "operator": ">=", "value": "85700" }
    If the pattern doesn't match, returns the original condition.
    """
    cond = cond.strip()
    m = re.match(r"^(\w+)\s*(<=|>=|=|<|>)\s*([\w\.]+)$", cond)
    if m:
        return {
            "attribute": m.group(1),
            "operator": m.group(2),
            "value": m.group(3)
        }
    else:
        return {"condition": cond}

def parse_where_clause(where_clause):
    """
    Parse a WHERE clause that may contain multiple conditions joined by AND.
    Returns a list of parsed conditions.
    """
    conditions = [c.strip() for c in re.split(r"(?i)\s+AND\s+", where_clause)]
    return [parse_condition(cond) for cond in conditions if cond]

def parse_query_log(query_log):
    """
    Parse a list of SQL queries (for INSERT, UPDATE, DELETE) and extract:
      - For UPDATE: the target table, the SET clause (parsed into operations),
        and the WHERE clause (parsed into conditions).
      - For INSERT: the target table, optional column names, and the values.
      - For DELETE: the target table and the WHERE clause (parsed into conditions).

    Returns a list of dictionaries with the parsed components.
    """
    results = []

    # Define regex patterns for each query type.
    update_pattern = re.compile(
        r"(?i)^UPDATE\s+(\w+)\s+SET\s+(.*?)(?:\s+WHERE\s+(.*))?$"
    )
    insert_pattern = re.compile(
        r"(?i)^INSERT\s+INTO\s+(\w+)(?:\s*\((.*?)\))?\s+VALUES\s*\((.*?)\)\s*$"
    )
    delete_pattern = re.compile(
        r"(?i)^DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+(.*))?$"
    )

    for query in query_log:
        query = query.strip()
        query_info = {}

        # Try UPDATE query.
        update_match = update_pattern.match(query)
        if update_match:
            query_info["type"] = "UPDATE"
            query_info["table"] = update_match.group(1)

            # Parse the SET clause: each assignment is separated by commas.
            set_clause_str = update_match.group(2).strip()
            set_parsed = {}
            for assign in set_clause_str.split(","):
                assign = assign.strip()
                if "=" in assign:
                    left, right = assign.split("=", 1)
                    column = left.strip()
                    expr = right.strip()
                    set_parsed[column] = parse_assignment(expr)
            query_info["set"] = set_parsed

            # Parse the optional WHERE clause.
            where_clause = update_match.group(3)
            if where_clause:
                query_info["where"] = parse_where_clause(where_clause)
            else:
                query_info["where"] = None

        else:
            # Try INSERT query.
            insert_match = insert_pattern.match(query)
            if insert_match:
                query_info["type"] = "INSERT"
                query_info["table"] = insert_match.group(1)
                columns_str = insert_match.group(2)
                if columns_str:
                    columns = [col.strip() for col in columns_str.split(",")]
                else:
                    columns = None
                query_info["columns"] = columns
                values_str = insert_match.group(3)
                values = [val.strip() for val in values_str.split(",")]
                query_info["values"] = values

            else:
                # Try DELETE query.
                delete_match = delete_pattern.match(query)
                if delete_match:
                    query_info["type"] = "DELETE"
                    query_info["table"] = delete_match.group(1)
                    where_clause = delete_match.group(2)
                    if where_clause:
                        query_info["where"] = parse_where_clause(where_clause)
                    else:
                        query_info["where"] = None
                else:
                    query_info["type"] = "UNKNOWN"
                    query_info["raw"] = query

        results.append(query_info)

    return results

def main():

    # Query log example
    Q = [
        "UPDATE Taxes SET B=A+1000 WHERE A>=85700",
        "INSERT INTO Taxes VALUES (5, 85800, 21450, 64350)",
        "DELETE FROM Taxes WHERE A<=20000",
        "UPDATE Taxes SET D=A-B"
    ]

    parsed_log = parse_query_log(Q)
    print(parsed_log)

if __name__ == "__main__":
    main()
