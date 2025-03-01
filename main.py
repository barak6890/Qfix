import re
import pulp
import copy
from query_log_parse import parse_query_log, parse_to_query
from add_variables import add_out_in_variables, add_binary_variables, add_continues_variables, add_u_v_variables, add_query_constant_variables

counter = 0
M = 1e10         # Big-M constant for big-M constraints
eps = 0.001       # Small constant to enforce strict inequalities
ghost = M/2    # Ghost value for deleted tuples

def create_R(D_0, Q):
    """
    Process a query log and update a database accordingly.
    Only handles INSERT queries by adding new tuples with -infinity values.

    Args:
        D_0: Initial database (list of dictionaries)
        Q: Query log (list of SQL-like query strings)

    Returns:
        R: Updated database with new tuples and insertion tracking
    """
    # Create a copy of the initial database
    R = [row.copy() for row in D_0]

    # Add insertion tracking to original rows
    for row in R:
        row['_inserted_at'] = -1  # -1 indicates it was in the original database

    # Process each query in the log
    for q_index, query in enumerate(Q):
        query = query.strip()

        if query.startswith("INSERT"):
            # Create new tuple with -infinity for all attributes
            new_tuple = {}

            # Use the keys from the first row as template if available
            if R and len(R) > 0:
                template_keys = [k for k in R[0].keys() if not k.startswith('_')]

                # Set all attribute values to -infinity
                for key in template_keys:
                    new_tuple[key] = 0

            # Add metadata for insertion tracking
            new_tuple['_inserted_at'] = q_index

            # Add the new tuple to the database
            R.append(new_tuple)

    return R


def MILP(R, D_n, parsed_Q, C, problem):
    # Create the MILP binary variables x_{q,t}
    x_vars = add_binary_variables(R, parsed_Q, "x")
    e_vars = add_binary_variables(R, parsed_Q, "e")
    # s for sigma
    s_vars = add_binary_variables(R, parsed_Q, "s")
    # m for mu
    m_vars = add_continues_variables(R, parsed_Q, "m")

    out_attributes, in_attributes = add_out_in_variables(R, parsed_Q, "a")

    # t_i_q_j.A_k = u.A_k + v.A_k
    u_vars, v_vars = add_u_v_variables(out_attributes)

    c_vars_where, u_vars_set = add_query_constant_variables(parsed_Q)


def main():
    # Example database states and queries for testing

    # Initial database state
    D_0 = [
        {'id': 1, 'A': 9500, 'B': 500, 'D': 8550},
        {'id': 2, 'A': 90000, 'B': 22500, 'D': 67500},
        {'id': 3, 'A': 86000, 'B': 21500, 'D': 64500},
        {'id': 4, 'A': 86500, 'B': 21625, 'D': 64875}
    ]

    # Final database state (with errors)
    D_n = [
        {'id': 1, 'A': 9500, 'B': 500, 'D': 9000},
        {'id': 2, 'A': 90000, 'B': 91000, 'D': -1000},
        {'id': 3, 'A': 86000, 'B': 87000, 'D': -1000},
        {'id': 4, 'A': 86500, 'B': 87500, 'D': -1000},
        {'id': 5, 'A': 85800, 'B': 21450, 'D': -1000}
    ]

    # Query log
    Q = [
        "UPDATE Taxes SET B=A+1000 WHERE A>=85700",
        "INSERT INTO Taxes VALUES (5, 85800, 21450, 64350)",
        "DELETE FROM Taxes WHERE A<=20000",
        "UPDATE Taxes SET D=A-B"
    ]

    # Complaints
    C = [
        {
            'wrong': {'id': 3, 'A': 86000, 'B': 87000, 'D': -1000},
            'correct': {'id': 3, 'A': 86000, 'B': 21500, 'D': 64500}
        },
        {
            'wrong': {'id': 4, 'A': 86500, 'B': 87500, 'D': -1000},
            'correct': {'id': 4, 'A': 86500, 'B': 21625, 'D': 64875}
        }
    ]

    R = create_R(D_0, Q)
    problem = pulp.LpProblem("My_Problem", pulp.LpMinimize)
    parsed_log = parse_query_log(Q)




    # # Diagnose and repair
    variables = MILP(R, D_n, parsed_log, C, problem)
    Q_star = parse_to_query(variables, Q)

    print("Original Queries:")
    for q in Q:
        print(f"  {q}")

    print("\nRepaired Queries:")
    for q in Q_star:
        print(f"  {q}")

if __name__ == "__main__":
    main()
