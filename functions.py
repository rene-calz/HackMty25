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

def filter_2(optimal: list, usable_stock: pd.DataFrame, flight_date: datetime) -> pd.DataFrame:
    """
    Selecciona del stock las filas (lotes implícitos) necesarios para cumplir la combinación óptima.
    Prioriza los productos con fecha de vencimiento más próxima (FIFO por vencimiento).

    Parámetros
    ----------
    optimal : list of tuples
        Lista de tuplas con formato [(item_type, amount), ...]
    usable_stock : pd.DataFrame
        Stock disponible, donde cada fila representa un lote implícito.
        Debe tener columnas ['item_type', 'expiration_date', 'cost', 'weight', 'quantity'].
    flight_date : datetime
        Fecha del vuelo.
    
    Retorna
    -------
    trolley_stock : pd.DataFrame
        DataFrame con las filas (lotes) que se usarán, incluyendo la cantidad tomada de cada una.
    """

    result_rows = []

    for item_type, required_qty in optimal:
        # Filtrar solo filas válidas (no vencidas)
        available_rows = usable_stock[
            (usable_stock['item_type'] == item_type) &
            (usable_stock['expiration_date'] >= flight_date)
        ].sort_values(by='expiration_date')

        for _, row in available_rows.iterrows():
            if required_qty <= 0:
                break

            available_qty = row['quantity']
            take_qty = min(required_qty, available_qty)

            result_rows.append({
                'item_type': row['item_type'],
                'expiration_date': row['expiration_date'],
                'cost': row['cost'],
                'weight': row['weight'],
                'quantity_used': take_qty
            })

            required_qty -= take_qty

    trolley_stock = pd.DataFrame(result_rows)
    return trolley_stock



def remove_from_stock(stock: pd.DataFrame, trolley_stock: pd.DataFrame) -> pd.DataFrame:
	pass

def add_to_stock(stock: pd.DataFrame, addition: pd.DataFrame) -> pd.DataFrame:
	pass


def probabilties_model(passengers: int, flight_date: datetime, product: str, df: pd.DataFrame = None) -> float:
    """
    Calculate sales probability for a product on a specific flight date.
    
    Parameters:
    -----------
    passengers : int
        Number of passengers (not currently used, but available for future logic)
    flight_date : datetime
        Date of the flight
    product : str
        Product ID
    df : pd.DataFrame, optional
        DataFrame with sales data. If None, uses default from forecast.py
    
    Returns:
    --------
    float : Sales probability (0.0 to 1.0)
    """
    if df is None:
        # Use default dataset from forecast.py
        result = fore.get_sales_probability(product_id=product, target_date=flight_date)
    else:
        result = fore.get_sales_probability(product_id=product, target_date=flight_date, df=df)
    
    # Extract probability from the returned dictionary
    return result['probability']

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


