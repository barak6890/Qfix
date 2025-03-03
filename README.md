# **Database Query Repair Using MILP**

## **Project Overview**
This project focuses on **identifying and correcting incorrect database queries** by modeling them as a **Mixed Integer Linear Programming (MILP) problem**. Given an **initial database state (D₀)**, a **final incorrect state (Dₙ)**, and a **log of executed queries (Q)**, we construct a MILP model that finds optimal modifications to the queries to ensure consistency with the expected database state.

### **Problem Definition**
We are given:
- **D₀** – The initial correct state of the database.
- **Dₙ** – The final (incorrect) state of the database.
- **Q** – The set of executed queries that transformed D₀ into Dₙ.
- **C** – A set of complaints specifying incorrect values in Dₙ and their expected corrections.

The goal is to **identify and modify incorrect queries** in Q so that the transformed database **matches the expected corrected state**.

---

## **Algorithms Implemented**

### **1. Query Parsing & Variable Initialization**
- `parse_query_log(Q)`: Parses the SQL-like query log (`Q`) into a structured representation that allows us to analyze and modify queries.
- `create_R(D₀, Q)`: Creates an **augmented database** `R` that tracks tuple modifications, handling inserted rows explicitly.

### **2. MILP Modeling**
We define **decision variables** that represent how each query affects each tuple in the database:

#### **Tuple Attribute Values**
- `t_vars[(q, t, attr)]` → Represents the value of `attr` in tuple `t` **after** query `q`.

#### **Binary Indicators for Query Effects**
- `x_vars[(q, t)]` → Whether tuple `t` is affected by query `q`.
- `s_vars[(q, t)]` → Whether tuple `t` satisfies the query’s WHERE condition.

#### **Building Constraints**
We construct MILP **constraints** that capture how queries modify database tuples:
- **INSERT Queries:** Ensure new tuples match expected values when inserted.
- **UPDATE Queries:**  
  - Constraints enforce attribute modifications using a **binary selection mechanism**:
    - `u_vars[(q, t, attr)] = x * μ(q, attr)`
    - `v_vars[(q, t, attr)] = (1 - x) * t_prev`
    - `t_vars[q, t, attr] = u + v`
- **DELETE Queries:** Ensure tuples marked for deletion transition correctly to a "ghost" state.

#### **Ensuring Correctness**
- Constraints enforce that the final state (`t_vars[n, t, attr]`) matches the expected corrections from `C`.

---

### **3. Query Repair via Optimization**
- We **solve the MILP model** to find the **minimal** changes to `Q` that ensure the final database state aligns with the expected corrected state.
- The **solution from the MILP solver is then translated into a corrected query log (`Q*`)** using `parse_to_query(variables, Q)`.
- This produces a **repaired version of Q**, fixing incorrect queries while making minimal modifications.

---

## **Existing Code & Libraries Used**
- **PuLP**: Open-source Python library for linear programming.
- **Custom Query Parsing**: Extracts query structure from raw SQL logs.
- **Big-M Constraints**: Used to model logical conditions for updates and WHERE clauses.

---

## **How to Run the Project**
```bash
pip install pulp
python main.py
