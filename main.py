# Imports
import functions as func
import pandas as pd


def main(stock: pd.DataFrame, flights: pd.DataFrame):
	for flight in flights:
		flight_date = flight['date']
		flight_passangers = flight['passangers']
		costs, weights, tipo_usable_products, usable_stock = func.filter_1(flight_date, stock)
		probabilities = []
		
		for product in tipo_usable_products:
			probabilities.append(func.probabilities_model(flight_passengers, flight_date, product))

		optimal_combination = func.smart_cart(probabilities, costs, weights, flight_passengers)

		trolley_stock = func.filter_2(optimal, usable_stock, flight_date)

		stock = func.remove_from_stock(stock, trolley_stock)

		not_consumed_stock = func.simulate_flight(flight_passengers, flight_date, trolley_stock, df=stock)

		stock = func.add_to_stock(not_consumed_stock)

	









