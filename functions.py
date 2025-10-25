# Imports
import pulp
import numpy as np

# Functions
def MonteCarlo(Pr: float, sim=1000, N=100) -> float:

    points = []

    for _ in range(sim):
        simulated_point = np.random.binomial(N, Pr)
        points.append(simulated_point)
    
   
    return  np.percentile(points, 98)
    
def smart_cart(probabilities: list, costs: list, weights: list, MAX_WEIGHT: int, PASSENGERS: int) -> list:
	# --- 1. Definition of data ---
	# Listas para las restricciones
	U = [MonteCarlo(i,N=PASSENGERS) for i in probabilities]

	# --- 2. Calc of V_i ---
	# V_i = Pr(C_i) * Cost_i
	n = len(costs)
	V = [probabilities[i] * costs[i] for i in range(n)]

	# --- 3. Create LP problem ---
	problem = pulp.LpProblem("Optimization_V_with_LowBound", pulp.LpMaximize)

	# --- 4. Define the decision variables (X_i) ---
	# Using lowBound=1 to keep 1 <= X_i
	# Using upBound=U_i to keep X_i <= U_i
	variables_X = {}
	for i in range(n):
			variables_X[i] = pulp.LpVariable(
					name=f"X_{i}",
					lowBound=1,          
					upBound=U[i],     
					cat=pulp.LpInteger
			)

	# PuLP now knows that X_i should be in rango [1, U_i]

	# --- 5. Objective Function ---
	# max \sum (V_i * X_i)
	objective_function = pulp.lpSum([V[i] * variables_X[i] for i in range(n)])
	problem += objective_function, "Objective function total"

	# --- 6. Defining restrictions ---

	# Restriction: Σ(weight_i * X_i) <= MAX_WEIGHT
	weight_restriction = pulp.lpSum([weights[i] * variables_X[i] for i in range(n)])
	problem += weight_restriction <= MAX_WEIGHT, "Weight restrinction"

	# --- 7. Solve the problem ---
	print("\nSolving the problem...")
	problem.solve()

	# --- 8. Show results ---
	print(f"State of the solution: {pulp.LpStatus[problem.status]}")

	if pulp.LpStatus[problem.status] == 'Optimal':
			print(f"Optimal solution: {pulp.value(problem.objective)}")
			print("\nOptimal values for X_i:")
			for i in range(n):
					print(f"  {variables_X[i].name} = {pulp.value(variables_X[i])}")
	else:
			print("Could not find the solution: Problem non-factible.")

