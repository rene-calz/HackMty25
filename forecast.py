import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX

def get_sales_probability(product_id, target_date, df="result_hack_filtrado_con_peso_precioA.xlsx", model_params=None, forecast_days=14):
    """
    Calculate the probability of a product being sold on a specific date.

    Parameters:
    -----------
    product_id : int
        ID of the product to analyze
    target_date : str or datetime
        Date for which to calculate the probability (format: 'YYYY-MM-DD')
    df : pandas DataFrame
        Original dataframe containing sales and passenger data
    model_params : dict, optional
        SARIMA model parameters. If None, uses the optimal parameters found in analysis
    forecast_days : int, default=14
        Number of days to forecast ahead

    Returns:
    --------
    dict : Dictionary containing:
        - probability: Sales probability (sales/passengers)
        - forecast_sales: Forecasted sales for the date
        - expected_passengers: Expected number of passengers
        - confidence_interval: Confidence interval for sales forecast
        - status: 'historical' or 'forecast'
    """

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
        actual_passengers = historical_row['Pasajeros']

        probability = actual_sales / actual_passengers if actual_passengers > 0 else 0

        return {
            'product_id': product_id,
            'date': target_date,
            'probability': probability,
            'sales': actual_sales,
            'passengers': actual_passengers,
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
                raise ValueError(f"Target date is too far in the future. Maximum forecast horizon is {forecast_days} days.")

            # Generate forecast
            forecast_obj = fitted_model.get_forecast(steps=days_ahead)
            forecast_mean = forecast_obj.predicted_mean
            forecast_ci = forecast_obj.conf_int(alpha=0.05)

            # Get forecast for target date
            forecast_sales = forecast_mean.iloc[-1]
            ci_lower = forecast_ci.iloc[-1, 0]
            ci_upper = forecast_ci.iloc[-1, 1]

            # Estimate passengers (using historical pattern)
            # Calculate average passengers for the same day of week in historical data
            target_dow = target_date.dayofweek
            historical_same_dow = product_data[product_data.index.dayofweek == target_dow]

            if len(historical_same_dow) > 0:
                expected_passengers = historical_same_dow['Pasajeros'].mean()
            else:
                # Fallback: use overall average
                expected_passengers = product_data['Pasajeros'].mean()

            probability = forecast_sales / expected_passengers if expected_passengers > 0 else 0

            return {
                'product_id': product_id,
                'date': target_date,
                'probability': min(probability, 1.0),  # Cap at 1.0
                'sales': forecast_sales,
                'passengers': expected_passengers,
                'status': 'forecast',
                'confidence_interval': (ci_lower, ci_upper),
                'model_used': f"SARIMA{model_params['order']}{model_params['seasonal_order']}"
            }
        else:
            raise ValueError("Target date is before historical data range.")

def batch_sales_probability(product_ids, target_date, df, model_params=None):
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
    model_params : dict, optional
        SARIMA model parameters

    Returns:
    --------
    pandas DataFrame with probabilities for all products
    """
    results = []

    for product_id in product_ids:
        try:
            result = get_sales_probability(product_id, target_date, df, model_params)
            results.append(result)
        except Exception as e:
            print(f"Error processing product {product_id}: {str(e)}")
            results.append({
                'product_id': product_id,
                'date': target_date,
                'probability': np.nan,
                'sales': np.nan,
                'passengers': np.nan,
                'status': 'error',
                'error_message': str(e)
            })

    return pd.DataFrame(results)

# Example usage in main file:
if __name__ == "__main__":
    # Example usage
    """
    # In your main file, you would use it like this:

    from sales_probability import get_sales_probability, batch_sales_probability

    # For a single product
    result = get_sales_probability(
        product_id=4542,
        target_date='2025-09-01',
        df=your_dataframe
    )

    print(f"Sales probability: {result['probability']:.3f}")
    print(f"Expected sales: {result['sales']:.1f}")
    print(f"Expected passengers: {result['passengers']:.0f}")

    # For multiple products
    products = [4542, 4561, 4568]
    results_df = batch_sales_probability(
        product_ids=products,
        target_date='2025-09-01',
        df=your_dataframe
    )

    print(results_df)
    """

    # Demo with sample data (you'll need to replace with your actual data)
    print("Sales Probability Function Ready!")
    print("Import this function in your main file and use as shown above.")