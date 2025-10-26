# Imports
import functions as func
import pandas as pd


def main(stock: pd.DataFrame, flights: pd.DataFrame):
	for row_flight in flights.itertuples():
		print(row_flight)
		flight_date = row_flight.flight_date
		flight_passengers = row_flight.passengers
		costs, weights, tipo_usable_products, usable_stock, stock_per_tipo = func.filter_1(flight_date, stock)
		probabilities = []
		print(tipo_usable_products)	
		for product in tipo_usable_products:
			probabilities.append(func.probabilities_model(passengers=flight_passengers, flight_date=flight_date, product=int(product), df = './result_hack_filtrado_con_peso_precioA.xlsx'))
		print(probabilities)

		optimal_combination = func.smart_cart(tipo_usable_products, probabilities, costs, weights, stock=stock_per_tipo, PASSENGERS=flight_passengers)


		trolley_stock = func.filter_2(optimal_combination, usable_stock, flight_date)
		print(trolley_stock)
		stock = func.remove_from_stock(stock, trolley_stock)

		not_consumed_stock = func.simulate_flight(flight_passengers, flight_date, trolley_stock)

		stock = func.add_to_stock(addition=not_consumed_stock, stock=stock)	

stock = pd.read_excel("./stock.xlsx")
vuelos = pd.read_excel("./vuelos.xlsx")
main(stock, vuelos)	









