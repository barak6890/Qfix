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
