# Imports
import pulp
import numpy as np
import pandas as pd
from datetime import datetime, date, time
import forecast as fore
# Import models

# Functions
def MonteCarlo(Pr: float, sim=1000, N=100) -> float:

    points = []

    for _ in range(sim):
        simulated_point = np.random.binomial(N, Pr)
        points.append(simulated_point)
    
   
    return  np.percentile(points, 98)

def filter_1(flight_date: datetime, stock: pd.DataFrame) -> tuple:
	usable_stock = stock[stock['expiration_date'] < flight_date]
	tipo_of_useable_products = set(usable_stock['item_type'])
	costs = []
	weights = []
	for tipo in tipo_of_usable_products:
		costs.append(usable_stock[usable_stock['item_type'] == tipo]['cost'].iloc[0])
		weights.append(usable_stock[usable_stock['item_type'] == tipo]['weight'].iloc[0])
	return (costs, weights, tipo_of_usable_products, usable_stock)


import pandas as pd
from datetime import datetime

def filter_2(optimal: list, usable_stock: pd.DataFrame, flight_date: datetime) -> pd.DataFrame:
    """
    Selecciona del stock los lotes necesarios para cumplir la combinación óptima de productos.
    Prioriza los lotes con fecha de vencimiento más próxima (FIFO por vencimiento).

    Parámetros
    ----------
    optimal : list of tuples
        Lista de tuplas con formato [(item_type, amount), ...]
    usable_stock : pd.DataFrame
        Subconjunto del stock con columnas ['item_type', 'expiration_date', 'cost', 'weight', 'quantity', ...]
    flight_date : datetime
        Fecha del vuelo.
    
    Retorna
    -------
    trolley_stock : pd.DataFrame
        DataFrame con las filas de stock a utilizar, incluyendo la cantidad tomada de cada lote.
    """

    result_rows = []

    for item_type, required_qty in optimal:
        # Lotes válidos del producto, ordenados por fecha de vencimiento
        available_lots = usable_stock[
            (usable_stock['item_type'] == item_type) &
            (usable_stock['expiration_date'] >= flight_date)
        ].sort_values(by='expiration_date')

        for _, lot in available_lots.iterrows():
            if required_qty <= 0:
                break

            available_qty = lot['quantity']
            take_qty = min(required_qty, available_qty)

            result_rows.append({
                'item_type': item_type,
                'expiration_date': lot['expiration_date'],
                'cost': lot['cost'],
                'weight': lot['weight'],
                'quantity_used': take_qty
            })

            required_qty -= take_qty

    trolley_stock = pd.DataFrame(result_rows)
    return trolley_stock


def remove_from_stock(stock: pd.DataFrame, trolley_stock: pd.DataFrame) -> pd.DataFrame:
	pass

def add_to_stock(stock: pd.DataFrame, addition: pd.DataFrame) -> pd.DataFrame:
	pass


def probabilties_model(passangers: int, flight_date: datatime, product: str) -> float:
	return fore.get_sales_probability(product_id = product, target_date = flight_date)	

def time_model(total_products: int, distinct_products: int) -> float:
	pass

def smart_cart(probabilities: list, costs: list, weights: list, PASSENGERS: int, MAX_WEIGHTS = 90) -> list:
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


