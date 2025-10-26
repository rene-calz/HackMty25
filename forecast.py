import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX

def get_sales_probability(product_id, target_date, df, passengers=None, model_params=None, forecast_days=30):
    """
    Calculate the probability of a product being sold on a specific date.

    Parameters:
    -----------
    product_id : int
        ID of the product to analyze
    target_date : str or datetime
        Date for which to calculate the probability (format: 'YYYY-MM-DD')
    df : pandas DataFrame or str
        Original dataframe containing sales and passenger data, or path to Excel file
    passengers : int, optional
        Manual passenger count. If provided, overrides automatic estimation.
        If None, will estimate based on historical patterns.
    model_params : dict, optional
        SARIMA model parameters. If None, uses the optimal parameters found in analysis
    forecast_days : int, default=14
        Number of days to forecast ahead

    Returns:
    --------
    dict : Dictionary containing:
        - probability: Sales probability (sales/passengers)
        - forecast_sales: Forecasted sales for the date
        - expected_passengers: Expected number of passengers (manual or estimated)
        - confidence_interval: Confidence interval for sales forecast
        - status: 'historical' or 'forecast'
        - passenger_source: 'manual' or 'estimated' to track where the value came from
    """

    # Load data if path is provided
    if isinstance(df, str):
        df = pd.read_excel(df)
    
    # Prepare time series data for the product
    def prepare_time_series(df, itemcode, freq='D'):
        product_df = df[df['ITEMCODE'] == itemcode].copy()
        ts_df = product_df.groupby('FECHA').agg({
            'SALES': 'sum',
            'PASSENGERS': 'sum',
            'LOSTSALES': 'sum'
        }).reset_index()
        ts_df.columns = ['Periodo', 'Ventas', 'Pasajeros', 'Ventas_Perdidas']
        ts_df['Periodo'] = pd.to_datetime(ts_df['Periodo'])
        ts_df = ts_df.set_index('Periodo')
        ts_df = ts_df.asfreq(freq, fill_value=0)
        return ts_df

    # Convert target_date to datetime
    target_date = pd.to_datetime(target_date)

    # Get product data
    product_data = prepare_time_series(df, product_id, freq='D')

    # Default model parameters (from your optimal model)
    if model_params is None:
        model_params = {
            'order': (1, 1, 2),  # (p, d, q)
            'seasonal_order': (0, 1, 1, 7)  # (P, D, Q, s)
        }

    # Check if target date is in historical data or requires forecasting
    if target_date in product_data.index:
        # Historical data - use actual values
        historical_row = product_data.loc[target_date]
        actual_sales = historical_row['Ventas']
        
        # Use manual passenger count if provided, otherwise use historical
        if passengers is not None:
            expected_passengers = passengers
            passenger_source = 'manual'
        else:
            expected_passengers = historical_row['Pasajeros']
            passenger_source = 'historical'

        probability = actual_sales / expected_passengers if expected_passengers > 0 else 0

        return {
            'product_id': product_id,
            'date': target_date,
            'probability': probability,
            'sales': actual_sales,
            'passengers': expected_passengers,
            'passenger_source': passenger_source,
            'status': 'historical',
            'confidence_interval': None
        }

    else:
        # Future date - need to forecast
        last_historical_date = product_data.index.max()

        if target_date > last_historical_date:
            # Forecast sales
            model = SARIMAX(
                product_data['Ventas'],
                order=model_params['order'],
                seasonal_order=model_params['seasonal_order'],
                enforce_stationarity=False,
                enforce_invertibility=False
            )

            fitted_model = model.fit(disp=False, maxiter=1000, method='lbfgs')

            # Calculate how many steps to forecast
            days_ahead = (target_date - last_historical_date).days

            if days_ahead > forecast_days:
                raise ValueError(f"Target date is too far in the future. "
                               f"Maximum forecast horizon is {forecast_days} days.")

            # Generate forecast
            forecast_obj = fitted_model.get_forecast(steps=days_ahead)
            forecast_mean = forecast_obj.predicted_mean
            forecast_ci = forecast_obj.conf_int(alpha=0.05)

            # Get forecast for target date
            forecast_sales = forecast_mean.iloc[-1]
            ci_lower = forecast_ci.iloc[-1, 0]
            ci_upper = forecast_ci.iloc[-1, 1]

            # Determine expected passengers
            if passengers is not None:
                # Use manually provided passenger count
                expected_passengers = passengers
                passenger_source = 'manual'
            else:
                # Estimate passengers (using historical pattern)
                target_dow = target_date.dayofweek
                historical_same_dow = product_data[product_data.index.dayofweek == target_dow]

                if len(historical_same_dow) > 0:
                    expected_passengers = historical_same_dow['Pasajeros'].mean()
                else:
                    # Fallback: use overall average
                    expected_passengers = product_data['Pasajeros'].mean()
                passenger_source = 'estimated'

            probability = forecast_sales / expected_passengers if expected_passengers > 0 else 0

            return {
                'product_id': product_id,
                'date': target_date,
                'probability': min(probability, 1.0),  # Cap at 1.0
                'sales': forecast_sales,
                'passengers': expected_passengers,
                'passenger_source': passenger_source,
                'status': 'forecast',
                'confidence_interval': (ci_lower, ci_upper),
                'model_used': f"SARIMA{model_params['order']}{model_params['seasonal_order']}"
            }
        else:
            raise ValueError("Target date is before historical data range.")


def batch_sales_probability(product_ids, target_date, df, passengers=None, model_params=None):
    """
    Calculate sales probabilities for multiple products on the same date.

    Parameters:
    -----------
    product_ids : list
        List of product IDs to analyze
    target_date : str or datetime
        Target date for probability calculation
    df : pandas DataFrame
        Original dataframe
    passengers : int, optional
        Manual passenger count for all products. If None, estimates for each product.
    model_params : dict, optional
        SARIMA model parameters

    Returns:
    --------
    pandas DataFrame with probabilities for all products
    """
    results = []

    for product_id in product_ids:
        try:
            result = get_sales_probability(
                product_id, 
                target_date, 
                df, 
                passengers=passengers,  # Pass passengers to individual function
                model_params=model_params
            )
            results.append(result)
        except Exception as e:
            print(f"Error processing product {product_id}: {str(e)}")
            results.append({
                'product_id': product_id,
                'date': target_date,
                'probability': np.nan,
                'sales': np.nan,
                'passengers': passengers if passengers is not None else np.nan,
                'passenger_source': 'manual' if passengers is not None else 'error',
                'status': 'error',
                'error_message': str(e)
            })

    return pd.DataFrame(results)


# Example usage
if __name__ == "__main__":
    """
    USAGE EXAMPLES:
    
    # 1. Using automatic passenger estimation (original behavior)
    result = get_sales_probability(
        product_id=4542,
        target_date='2025-09-01',
        df='result_hack_filtrado_con_peso_precioA.xlsx'
    )
    
    # 2. Using manual passenger count (NEW FEATURE)
    result = get_sales_probability(
        product_id=4542,
        target_date='2025-09-01',
        df='result_hack_filtrado_con_peso_precioA.xlsx',
        passengers=150  # Manually specify 150 passengers
    )
    
    # 3. Batch processing with manual passenger count
    products = [4542, 4561, 4568]
    results_df = batch_sales_probability(
        product_ids=products,
        target_date='2025-09-01',
        df='result_hack_filtrado_con_peso_precioA.xlsx',
        passengers=150  # All products use same passenger count
    )
    
    print(results_df)
    
    # The result dictionary now includes 'passenger_source' field:
    # - 'manual': passengers were manually provided
    # - 'estimated': passengers were estimated from historical data
    # - 'historical': passengers from historical record
    """
    
    print("Sales Probability Function (with manual passenger input) Ready!")
    print("See docstring for usage examples.")


