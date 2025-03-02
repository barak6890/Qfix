import pulp

def binary_mult(b, u, M):
    """
    Creates a binary variable e and constraints relating it to binary variable b and variable v.

    Parameters:
    - b: A PuLP binary variable (LpVariable with cat=LpBinary)
    - u: A PuLP variable (could be binary or real-valued)
    - M: A large positive constant for big-M constraints

    Returns:
    - (e, constraints): A tuple containing the binary variable e and a list of constraints
    """
    # Create a binary variable e with a unique name based on b and v
    a = pulp.LpVariable(f"a_{b.name}_{u.name}", cat=pulp.LpBinary)

    # Define the constraints
    constraints = [
        a <= u,
        a <= b * M,
        a >= u - (1 - b) * M
    ]

    return (a, constraints)

def is_less_equal(v1, v2, M):
    b = pulp.LpVariable(f"le_{v1.name}_{v2.name}", cat=pulp.LpBinary)
    constraint = [v1 - v2 <= M * (1 - b)]
    return b, constraint

def and_binary(b1, b2):
    b = pulp.LpVariable(f"and_{b1.name}_{b2.name}", cat=pulp.LpBinary)
    constraints = [
        b <= b1,
        b <= b2,
        b >= b1 + b2 - 1
    ]
    return b, constraints

def is_equal(v1, v2, M):
    b1, c1 = is_less_equal(v1, v2, M)
    b2, c2 = is_less_equal(v2, v1, M)
    b, c_and = and_binary(b1, b2)
    return b, c1 + c2 + c_and

def add_products(u, v, problem):
    """
    Adds two MILP variables u and v, returning a new variable w representing their sum.

    Args:
        u (pulp.LpVariable): The first variable (e.g., result of x * mu.A_j).
        v (pulp.LpVariable): The second variable (e.g., result of (1 - x) * t.A_j).
        problem (pulp.LpProblem): The MILP problem to which the constraint is added.

    Returns:
        pulp.LpVariable: A new variable w where w = u + v.
    """
    # Create a new continuous variable to hold the sum
    w = pulp.LpVariable(f"sum_{u.name}_{v.name}", cat="Continuous")
    
    # Add the constraint w = u + v to the problem
    problem += w == u + v
    
    return w

def add_e_constraints(problem, R, C, e_vars, t_vars, ghost, M):
    """
    Enforce:
        e_{q_i,t_j} = 1 - ( [t_j.A == ghost] AND [t_j^{*}.A == ghost] )

    Args:
        problem   : pulp.LpProblem instance
        R         : List of rows (so j indexes into R).
        C         : Complaints, so that C[j]["correct"]["A"] is a known constant for row j.
        e_vars    : dict {(i,j) -> pulp.LpVariable (Binary)} for e_{q_i,t_j}.
        t_vars    : dict {(i,j) -> pulp.LpVariable} for the *unknown* attribute t_j.A in the MILP.
        ghost     : Numeric value that marks a 'deleted' or 'incorrect' record (was M_minus).
        M         : Big-M constant for the is_equal function.
    """
    for (i, j), e_var in e_vars.items():
        # 1) b1 = [t_j.A == ghost]
        #    We have a real PuLP variable (t_vars[i,j]) for the DB state
        t_Aj_var = t_vars[(i, j)]   # The MILP variable for row j's attribute A in query i
        b1, c1 = is_equal(t_Aj_var, ghost, M)  # Reuses your "is_equal" function
        for c in c1:
            problem += c

        # 2) b2 = [t_j^*.A == ghost]
        #    The complaint's "correct" A-value is just a known constant: no big-M needed!
        t_star_Aj_val = C[j]["correct"]["A"]
        b2 = pulp.LpVariable(f"b2_q{i}_t{j}", cat="Binary")
        if t_star_Aj_val == ghost:
            # If the complaint says the correct value IS ghost => fix b2=1
            problem += (b2 == 1), f"fix_b2_eq_1_q{i}_t{j}"
        else:
            # If the complaint says the correct value != ghost => fix b2=0
            problem += (b2 == 0), f"fix_b2_eq_0_q{i}_t{j}"

        # 3) b_and = b1 AND b2
        #    This uses your existing "and_binary(b1, b2)" function
        b_and, c_and = and_binary(b1, b2)
        for c in c_and:
            problem += c

        # 4) e_{q_i,t_j} = 1 - b_and  =>  e_var + b_and == 1
        problem += e_var + b_and == 1, f"enforce_not_and_q{i}_t{j}"
