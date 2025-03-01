import pulp


def add_u_v_variables(out_vars):
    """
    For each variable in the out_vars dictionary, create two new MILP continuous variables.
    The new variables are named with the prefixes "u_" and "v_" followed by the original out variable name.

    Args:
        out_vars (dict): A dictionary with keys (q_index, t_index, attribute) mapping to MILP variables (e.g., "out_q0_t0_A").

    Returns:
        tuple: Two dictionaries, u_vars and v_vars, mapping the same keys to the new variables.
    """
    u_vars = {}
    v_vars = {}

    for key, var in out_vars.items():
        # Create new variable names by prepending "u_" and "v_" to the original variable's name
        u_var_name = f"u_{var.name}"
        v_var_name = f"v_{var.name}"

        # Create the new variables as continuous variables (adjust 'cat' if needed)
        u_vars[key] = pulp.LpVariable(u_var_name, cat="Continuous")
        v_vars[key] = pulp.LpVariable(v_var_name, cat="Continuous")

    return u_vars, v_vars

def add_out_in_variables(R, parsed_Q):
    """
    Create MILP continuous variables for each query, each tuple in R, and for each attribute in the tuple.
    The variable name is formatted as "out_q{q_index}_t{t_index}_{attribute}".

    Args:
        R (list): List of tuples (each tuple is a dictionary representing a row in the database).
        parsed_Q (list): List of parsed query dictionaries.

    Returns:
        dict: A dictionary with keys (q_index, t_index, attribute) mapping to the MILP variable.
    """
    out_vars = {}
    in_vars = {}
    for q_index, query in enumerate(parsed_Q):
        for t_index, t in enumerate(R):
            # Only include keys that are not metadata (i.e., not starting with '_')
            for attr in t.keys():
                if not attr.startswith("_"):
                    var_name_in = f"in_q{q_index}_t{t_index}_{attr}"
                    var_name_out = f"out_q{q_index}_t{t_index}_{attr}"

                    # Create a continuous variable (change cat if needed)
                    in_vars[(q_index, t_index, attr)] = pulp.LpVariable(var_name_in, cat="Continuous")
                    out_vars[(q_index, t_index, attr)] = pulp.LpVariable(var_name_out, cat="Continuous")
    return out_vars, in_vars

def add_continues_variables(R, parsed_Q, name):
    """
    Create MILP binary variables for each query in parsed_Q and each tuple in R.

    Args:
        R (list): List of tuples (each tuple is a dictionary representing a row in the database).
        parsed_Q (list): List of parsed query dictionaries.
        name (str): The prefix name for the variable (e.g., "x", "e", "s").

    Returns:
        dict: A dictionary with keys (q_index, t_index) mapping to the MILP binary variable.
    """
    vars = {}
    for q_index, query in enumerate(parsed_Q):
        for t_index, t in enumerate(R):
            # Create a variable name using the query and tuple indices
            var_name = f"{name}_q{q_index}_t{t_index}"
            # Create a binary variable
            vars[(q_index, t_index)] = pulp.LpVariable(var_name, cat="Continuous")
    return vars

def add_binary_variables(R, parsed_Q, name):
    """
    Create MILP binary variables x_{q,t} for each query in parsed_Q and each tuple in R.

    Args:
        R (list): List of tuples (each tuple is a dictionary representing a row in the database).
        parsed_Q (list): List of parsed query dictionaries.
        problem (pulp.LpProblem): The MILP problem.

    Returns:
        dict: A dictionary with keys (q_index, t_index) mapping to the MILP binary variable.
    """
    vars = {}
    for q_index, query in enumerate(parsed_Q):
        for t_index, t in enumerate(R):
            # Create a variable name using the query and tuple indices
            var_name = f"{name}_q{q_index}_t{t_index}"
            # Create a binary variable
            vars[(q_index, t_index)] = pulp.LpVariable(var_name, cat="Binary")
    return vars

def add_query_constant_variables(parsed_Q):
    """
    Create MILP continuous variables for numeric constants found in the queries.

    For example, for an UPDATE query like:
      UPDATE Taxes SET B=A+1000 WHERE A>=85700
    this function creates:
      - A variable for the constant in the SET clause ("1000")
      - A variable for the constant in the WHERE clause ("85700")

    For DELETE queries (which only have a WHERE clause), it creates variables for
    the constants in the WHERE clause.

    Args:
        parsed_Q (list): List of parsed query dictionaries.
            Expected format example:
              {'type': 'UPDATE',
               'table': 'Taxes',
               'set': {'B': {'left_operand': 'A', 'operator': '+', 'right_operand': '1000'}},
               'where': [{'attribute': 'A', 'operator': '>=', 'value': '85700'}]}

    Returns:
        tuple: Two dictionaries:
            - const_vars_set: keys (q_index, attribute) mapping to MILP variable for SET constants.
            - const_vars_where: keys (q_index, attribute, cond_index) mapping to MILP variable for WHERE constants.
    """
    const_vars_set = {}
    const_vars_where = {}

    for q_index, q in enumerate(parsed_Q):
        q_type = q["type"].upper()

        # Process SET clause constants (for UPDATE queries)
        if q_type == "UPDATE" and "set" in q:
            for attr, set_expr in q["set"].items():
                # Look for a right_operand that is a numeric constant.
                if "right_operand" in set_expr:
                    try:
                        # Attempt to convert to float to ensure it's numeric.
                        float(set_expr["right_operand"])
                        var_name = f"const_set_q{q_index}_{attr}"
                        const_vars_set[(q_index, attr)] = pulp.LpVariable(var_name, cat="Continuous")
                    except ValueError:
                        # Not numeric; skip.
                        pass

        # Process WHERE clause constants for UPDATE and DELETE queries.
        if q_type in {"UPDATE", "DELETE"}:
            where_clause = q.get("where")
            if where_clause is not None:
                for cond_index, cond in enumerate(where_clause):
                    if "value" in cond:
                        try:
                            float(cond["value"])
                            var_name = f"const_where_q{q_index}_{cond['attribute']}_{cond_index}"
                            const_vars_where[(q_index, cond["attribute"], cond_index)] = pulp.LpVariable(var_name, cat="Continuous")
                        except ValueError:
                            pass
    return const_vars_set, const_vars_where
