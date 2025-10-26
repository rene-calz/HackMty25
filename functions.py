# Imports
import pulp
import numpy as np
import pandas as pd
from datetime import datetime, date, time
import forecast as fore
from typing import Iterable, Tuple, List
import joblib
# Functions
def MonteCarlo(Pr: float, sim: int = 1000, N: int = 100, percentil: int = 98) -> float:
    """
    Monte Carlo simulation for demand estimation.

    Parameters:
    -----------
    Pr : float
        Probability of sale (0.0 to 1.0)
    sim : int
        Number of simulations (default: 1000)
    N : int
        Number of passengers/trials (default: 100)
    percentil : int
        Percentile to return (default: 95)

    Returns:
    --------
    float : Estimated demand at given percentile
    """
    if not 0 <= Pr <= 1:
        raise ValueError("Probability must be between 0 and 1")

    points = []
    for _ in range(sim):
        simulated_point = np.random.binomial(N, Pr)
        points.append(simulated_point)

    # FIXED: Changed 'int' to 'percentil' (was using type instead of variable)
    return np.percentile(points, percentil)


def filter_1(flight_date: datetime, stock: pd.DataFrame) -> tuple:
	usable_stock = stock[stock['expiration_date'] > flight_date]
	tipo_of_useable_products = set(usable_stock['item_type'])
	costs = []
	weights = []
	stock_per_tipo = []
	for tipo in tipo_of_useable_products:
		costs.append(usable_stock[usable_stock['item_type'] == tipo]['cost'].iloc[0])
		weights.append(usable_stock[usable_stock['item_type'] == tipo]['weight'].iloc[0])
		stock_per_tipo.append(usable_stock.loc[usable_stock['item_type'] == tipo, 'quantity'].sum())  

	return (costs, weights, tipo_of_useable_products, usable_stock, stock_per_tipo)

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
            (usable_stock['expiration_date'] > flight_date)
        ].sort_values(by='expiration_date')

        for _, row in available_rows.iterrows():
            if required_qty <= 0:
                break

            available_qty = row['quantity']
            take_qty = min(required_qty, available_qty)

            result_rows.append({
                'item_type': row['item_type'],
								'batch': row['batch'],
                'expiration_date': row['expiration_date'],
                'cost': row['cost'],
                'weight': row['weight'],
                'quantity': take_qty
            })

            required_qty -= take_qty

    trolley_stock = pd.DataFrame(result_rows)
    return trolley_stock
## ----- Remove and add stock functions -----

def _validate_columns(df: pd.DataFrame, needed: Iterable[str], df_name: str):
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"{df_name} is missing required columns: {missing}")

def _normalize_keys(df: pd.DataFrame, key_cols: Tuple[str, ...], qty_col: str) -> pd.DataFrame:
    """Aggregate by key_cols with summed quantity."""
    return df.groupby(list(key_cols), dropna=False, as_index=False)[qty_col].sum()


def remove_from_stock(
    stock: pd.DataFrame,
    trolley_stock: pd.DataFrame,
    key_cols: Tuple[str, ...] = ("item_type", "batch"),
    qty_col: str = "quantity") -> pd.DataFrame:
    """
    Subtract quantities from general stock using the items assigned to the trolley.

    Behavior:
    - If trolley specifies both 'item_type' and 'batch', subtract per-lot (exact match on keys).
    - If trolley does NOT include 'batch' (e.g., “5 candies”), allocate that quantity across
      available batches in stock for that item_type, depleting in ascending batch order.
    - Negative results are clipped to zero; rows with zero quantity are removed.
    """
    # Stock must have item_type, batch, quantity
    _validate_columns(stock, [*key_cols, qty_col], "stock")
    _validate_columns(trolley_stock, [qty_col, "item_type"], "trolley_stock")

    # Fast path: trolley has item_type & batch -> lot-for-lot subtraction
    has_all_keys_in_trolley = all(k in trolley_stock.columns for k in key_cols)
    if has_all_keys_in_trolley:
        stock_agg   = _normalize_keys(stock, key_cols, qty_col)
        trolley_agg = _normalize_keys(trolley_stock, key_cols, qty_col).rename(columns={qty_col: "trolley_qty"})

        merged = stock_agg.merge(trolley_agg, on=list(key_cols), how="left")
        merged["trolley_qty"] = merged["trolley_qty"].fillna(0)
        merged[qty_col] = (merged[qty_col] - merged["trolley_qty"]).clip(lower=0)

        result = (
            merged.drop(columns=["trolley_qty"])
                  .loc[merged[qty_col] > 0]
                  .reset_index(drop=True)
        )
        return result

    # Allocation path: trolley lacks 'batch' -> distribute per item_type across batches
    # Prepare stock aggregated by (item_type, batch)
    remaining = _normalize_keys(stock, key_cols, qty_col)

    # Sum trolley by item_type only
    trolley_simple = (
        trolley_stock.groupby(["item_type"], dropna=False, as_index=False)[qty_col].sum()
                     .rename(columns={qty_col: "trolley_qty"})
    )

    for _, r in trolley_simple.iterrows():
        itype = r["item_type"]
        need = float(r["trolley_qty"])
        if need <= 0:
            continue

        # All batches for this item_type, deterministic order by 'batch'
        mask = remaining["item_type"] == itype
        pool_idx = remaining.index[mask]
        if len(pool_idx) == 0:
            continue  # nothing to remove for this item_type

        # Sort those rows by batch asc and iterate in that order
        pool_sorted = remaining.loc[pool_idx].sort_values(by=["batch"], ascending=True)
        for idx, prow in pool_sorted.iterrows():
            if need <= 0:
                break
            available = float(prow[qty_col])
            if available <= 0:
                continue

            take = min(available, need)
            remaining.at[idx, qty_col] = available - take
            need -= take
        # move to next item_type

    # Clean up: no negatives; drop zero-quantity rows
    remaining[qty_col] = remaining[qty_col].clip(lower=0)
    final = remaining.loc[remaining[qty_col] > 0].reset_index(drop=True)
    return final


def add_to_stock(
    stock: pd.DataFrame,
    addition: pd.DataFrame,
    key_cols: Tuple[str, ...] = ("item_type", "batch"),
    qty_col: str = "quantity"
) -> pd.DataFrame:
    """
    Adds (returns) remaining trolley items back into general stock.

    Behavior:
    - Treat (item_type, batch) as distinct lots.
    - Quantities are summed when the same lot appears on both sides.
    """
    _validate_columns(stock,   [*key_cols, qty_col], "stock")
    _validate_columns(addition, [*key_cols, qty_col], "addition")

    stock_agg = _normalize_keys(stock, key_cols, qty_col)
    add_agg   = _normalize_keys(addition, key_cols, qty_col).rename(columns={qty_col: "add_qty"})

    merged = stock_agg.merge(add_agg, on=list(key_cols), how="outer")
    merged[qty_col] = merged.get(qty_col, 0).fillna(0) + merged.get("add_qty", 0).fillna(0)

    result = (
        merged.drop(columns=["add_qty"])
              .loc[merged[qty_col] > 0]
              .reset_index(drop=True)
    )
    return result

## ----- Probability models -----
def probabilities_model(passengers: int, flight_date: datetime, product: int, df: pd.DataFrame) -> float:
    """
    Calculate sales probability for a product given specific passenger count.
    
    Parameters:
    -----------
    passengers : int
        Number of passengers on the flight (manual input from flight data)
    flight_date : datetime
        Date of the flight
    product : str
        Product ID (ITEMCODE)
    df : pd.DataFrame
        Historical sales and passenger data for forecasting
        
    Returns:
    --------
    float : Probability of sale (0.0 to 1.0)
    """
    try:
        result = fore.get_sales_probability(
            product_id=product, 
            target_date=flight_date,
            df=df,
            passengers=passengers  # Manual passenger input
        )
        print(result['probability'])
        return result['probability']
    
    except Exception as e:
        print(f"Error calculating probability for product {product}: {str(e)}")
        return 0.0  # Return 0 probability on error

def time_model(total_products: int, distinct_products: int, amount_drawer: int = 5) -> float:
		pipeline = joblib.load('./RFRegressor.joblib')
		model = pipeline['model']
		prediction = model.predict(np.array([total_products, distinct_products]).reshape(1,-1))
		return amount_drawer*prediction[0]
	
def smart_cart(products: list, 
							probabilities: list, 
							costs: list, 
							weights: list, 
							stock: list,
							PASSENGERS: int,
							MAX_WEIGHTS: int= 90,
							T_MIN: int = 210,
							T_MAX: int = 420) -> list:
	# --- 1. Definition of data ---
	# Listas para las restricciones
	U = [MonteCarlo(i,N=PASSENGERS, percentil=98) for i in probabilities]

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
	problem += weight_restriction <= MAX_WEIGHTS, "Weight restrinction"

	# Restriction: Stock: X_i <= STOCK_i for each item
	for i in range(n):
		problem += variables_X[i] <= stock[i], f"Stock_Contraint_X_{i}"

	# --- 7. Solve the problem ---
	print("\nSolving the problem...")
	problem.solve()

	# --- 8. Show results ---
	print(f"State of the solution: {pulp.LpStatus[problem.status]}")

	if pulp.LpStatus[problem.status] == 'Optimal':
			print(f"Optimal solution: {pulp.value(problem.objective)}")
			print("\nOptimal values for X_i:")
			optimal_combination = []
			for i in range(n):
					print(f"  {variables_X[i].name} = {pulp.value(variables_X[i])}")
					optimal_combination.append((list(products)[i], pulp.value(variables_X[i])))
	else:
		print("Could not find the solution: Problem non-factible.")
	
	return optimal_combination


def simulate_flight(passengers: int, flight_date: datetime, trolley_stock: pd.DataFrame) -> pd.DataFrame:
    """
    Simulate consumption during a flight based on probabilities and passenger behavior.
    
    Parameters
    ----------
    passengers : int
        Number of passengers on the flight
    flight_date : datetime
        Date of the flight
    trolley_stock : pd.DataFrame
        Stock loaded onto the trolley for this flight.
        Expected columns: ['item_type', 'expiration_date', 'cost', 'weight', 'quantity_used']
    
    Returns
    -------
    not_consumed_stock : pd.DataFrame
        Items that were NOT consumed during the flight, ready to be added back to main stock.
        Returns DataFrame with columns: ['item_type', 'batch', 'expiration_date', 
                                         'cost', 'weight', 'quantity']
    """
    
    if trolley_stock.empty:
        return pd.DataFrame(columns=['item_type', 'batch', 'expiration_date', 
                                     'cost', 'weight', 'quantity'])
    
    not_consumed_rows = []
    
    for _, row in trolley_stock.iterrows():
        item_type = row['item_type']
        loaded_qty = row['quantity']
        
        # Get consumption probability for this item
        # Using the probabilities_model from your functions.py
        # Note: You'll need to pass the appropriate DataFrame (df) here
        # For simulation, we can use a random consumption based on typical airline sales rates
        
        # Simplified simulation: consume based on binomial distribution
        # Probability of sale per item can be estimated or retrieved from your model
        # For now, using a reasonable consumption rate (you can adjust this)
        
        # Average consumption rate in airline catering is typically 30-70%
        # We'll use a binomial distribution to simulate actual consumption
        base_probability = min(0.6, passengers / 200.0)  # Adjust based on your data
        
        # Simulate actual consumption
        consumed_qty = np.random.binomial(int(loaded_qty), base_probability)
        remaining_qty = loaded_qty - consumed_qty
        
        # If there are items left, add them to not_consumed stock
        if remaining_qty > 0:
            not_consumed_rows.append({
                'item_type': item_type,
                'batch': row.get('batch', f"{item_type}_{flight_date.strftime('%Y%m%d')}"),
                'expiration_date': row['expiration_date'],
                'cost': row['cost'],
                'weight': row['weight'],
                'quantity': remaining_qty
            })
    
    not_consumed_stock = pd.DataFrame(not_consumed_rows)
    return not_consumed_stock
