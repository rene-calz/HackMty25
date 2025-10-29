# HackMTY 2025 - Pick & Pack of the Future

## 🎯 Project Overview

This repository contains solutions for the **HackMTY 2025 Hackathon** focused on optimizing airline catering operations through smart intelligence and data-driven decision making. The project addresses three critical challenges in the Pick & Pack process for gategroup airline catering services.

## 📋 Table of Contents

- [Problem Statement](#problem-statement)
- [Solution Architecture](#solution-architecture)
- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Core Modules](#core-modules)
- [Installation](#installation)
- [Usage](#usage)
- [Datasets](#datasets)
- [Algorithms & Models](#algorithms--models)
- [Contributing](#contributing)
- [License](#license)

## 🎓 Problem Statement

The project tackles three interconnected challenges in airline catering operations:

### 1. **Consumption Prediction**
Predict product consumption patterns on flights to optimize inventory levels and reduce waste. The system forecasts demand based on:
- Flight characteristics (type, duration, service class)
- Historical consumption data
- Passenger counts
- Product specifications

### 2. **Expiration Date Management**
Implement intelligent FIFO (First-In-First-Out) inventory management that prioritizes products near expiration while ensuring quality standards. The solution:
- Tracks product expiration dates across batches
- Optimizes product selection to minimize waste
- Ensures compliance with food safety regulations
- Reduces financial losses from expired inventory

### 3. **Productivity Estimation**
Estimate drawer assembly time in Pick & Pack operations to improve workforce planning and operational efficiency. The system predicts:
- Time required to assemble drawers based on complexity
- Productivity benchmarks across different drawer types
- Resource allocation needs for flight schedules

## 🏗️ Solution Architecture

The solution integrates multiple machine learning models and optimization algorithms:

```
┌─────────────────┐
│   Flight Data   │
│  (Passengers,   │
│   Date, Type)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│        Forecasting Engine               │
│  ┌───────────────────────────────────┐  │
│  │   SARIMA Time Series Models       │  │
│  │   - Historical sales patterns     │  │
│  │   - Seasonal adjustments          │  │
│  │   - Passenger-based forecasting   │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │ Sales Probability│
         │   Calculation    │
         └────────┬─────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Monte Carlo Simulation             │
│  - Demand estimation under uncertainty  │
│  - Risk-adjusted inventory levels       │
│  - Percentile-based planning (95-98%)   │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   Linear Programming Optimizer          │
│  (PuLP - Smart Cart Algorithm)          │
│  ┌───────────────────────────────────┐  │
│  │  Maximize: Expected Revenue       │  │
│  │  Subject to:                      │  │
│  │    - Weight constraints (≤90 kg)  │  │
│  │    - Expiration dates (FIFO)      │  │
│  │    - Stock availability           │  │
│  │    - Time windows (210-420 min)   │  │
│  └───────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  Optimal Cart   │
         │  Configuration  │
         └────────┬─────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│    Productivity Estimation              │
│  ┌───────────────────────────────────┐  │
│  │  Random Forest Regressor          │  │
│  │  - Total items count              │  │
│  │  - Unique product types           │  │
│  │  - Drawer complexity              │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## ✨ Key Features

### 🔮 Predictive Analytics
- **Time Series Forecasting**: SARIMA models predict product demand based on historical patterns
- **Monte Carlo Simulation**: Probabilistic demand estimation with configurable confidence intervals
- **Productivity Modeling**: Random Forest regression for assembly time estimation

### 🎯 Optimization
- **Linear Programming**: PuLP-based optimization for cart configuration
- **Multi-objective**: Balances revenue maximization with operational constraints
- **Dynamic Constraints**: Weight limits, time windows, and stock availability

### 📦 Inventory Management
- **FIFO Implementation**: Automatic prioritization of products near expiration
- **Batch Tracking**: Granular lot-level inventory control
- **Stock Simulation**: Post-flight inventory adjustment based on consumption

### 🔧 Operational Tools
- **Flexible Configuration**: Adjustable parameters for different operational scenarios
- **Batch Processing**: Handles multiple flights in sequence
- **Real-time Updates**: Dynamic stock updates after each flight

## 📁 Project Structure

```
HackMTY2025/
├── main.py                          # Main orchestration script
├── functions.py                     # Core utility functions
├── forecast.py                      # Time series forecasting module
├── RFRegressor.joblib              # Pre-trained productivity model
├── timeseriesAnalysis.ipynb         # Tests evaluated for the correct choosing of forecast model
├── stock.xlsx                      # Current inventory data
├── vuelos.xlsx                     # Flight schedule data
├── result_hack_filtrado_con_peso_precioA.xlsx  # Historical sales data
├── Probabilistic_Machine_Learning_Assisted_Optimizer.pdf  # Mathematical and Statistical Background and Foundations of our Proposal
└── README.md
```

## 🔧 Core Modules

### 1. `main.py` - Orchestration Engine

The main script coordinates the entire workflow:

```python
def main(stock: pd.DataFrame, flights: pd.DataFrame):
    """
    Main execution flow:
    1. Iterate through scheduled flights
    2. Filter usable stock based on expiration dates
    3. Calculate sales probabilities for each product
    4. Optimize cart configuration
    5. Select specific inventory batches (FIFO)
    6. Update stock after flight
    7. Simulate consumption and return unused stock
    """
```

**Process Flow**:
1. Reads flight schedule and current inventory
2. For each flight:
   - Filters products by expiration date
   - Calculates demand probabilities
   - Optimizes cart configuration
   - Selects inventory batches
   - Updates stock levels
   - Simulates consumption

### 2. `functions.py` - Utility Library

#### **MonteCarlo Function**
```python
def MonteCarlo(Pr: float, sim: int = 1000, N: int = 100, percentil: int = 98) -> float
```

**Purpose**: Estimates demand under uncertainty using Monte Carlo simulation.

**Methodology**:
- Simulates binomial distribution (N trials with probability Pr)
- Runs multiple iterations (default: 1000)
- Returns demand at specified percentile (default: 98th)

**Use Case**: Provides conservative demand estimates to prevent stockouts while minimizing excess inventory.

**Parameters**:
- `Pr`: Probability of sale per passenger (0.0-1.0)
- `sim`: Number of simulation iterations
- `N`: Number of passengers (trials)
- `percentil`: Confidence level for demand estimate

**Mathematical Foundation**:
```
Demand ~ Binomial(n=passengers, p=sale_probability)
Estimate = Percentile(simulations, q=0.98)
```

---

#### **filter_1 Function**
```python
def filter_1(flight_date: datetime, stock: pd.DataFrame) -> tuple
```

**Purpose**: Pre-filters inventory based on expiration dates and aggregates product information.

**Process**:
1. Filters out expired products (expiration_date > flight_date)
2. Identifies unique product types
3. Extracts cost and weight per product
4. Calculates available quantity per product type

**Returns**: Tuple containing:
- `costs`: List of unit costs per product
- `weights`: List of unit weights per product
- `tipo_of_useable_products`: Set of available product types
- `usable_stock`: Filtered DataFrame with valid products
- `stock_per_tipo`: Total quantity available per product type

---

#### **filter_2 Function**
```python
def filter_2(optimal: list, usable_stock: pd.DataFrame, flight_date: datetime) -> pd.DataFrame
```

**Purpose**: Selects specific inventory batches following FIFO principle.

**FIFO Implementation**:
1. Groups stock by product type
2. Sorts by expiration date (ascending)
3. Allocates from nearest expiration first
4. Handles partial batch selection
5. Tracks exact quantities from each batch

**Algorithm**:
```
For each product in optimal combination:
    remaining_needed = target_quantity
    For each batch (sorted by expiration):
        If remaining_needed > 0:
            take = min(remaining_needed, batch.quantity)
            Add batch to trolley
            remaining_needed -= take
```

**Returns**: DataFrame with selected batches and quantities

---

#### **probabilities_model Function**
```python
def probabilities_model(passengers: int, flight_date: datetime, product: int, df: pd.DataFrame) -> float
```

**Purpose**: Calculates the probability of product sale on a specific flight.

**Integration**: Wraps the `forecast.get_sales_probability()` function with error handling.

**Inputs**:
- Flight passenger count
- Flight date
- Product ID
- Historical sales data

**Output**: Probability value (0.0 to 1.0)

---

#### **time_model Function**
```python
def time_model(total_products: int, distinct_products: int, amount_drawer: int = 5) -> float
```

**Purpose**: Predicts drawer assembly time using pre-trained Random Forest model.

**Features**:
- Loads trained model from `RFRegressor.joblib`
- Considers total items and unique types
- Scales prediction by number of drawers

**Prediction Formula**:
```
time = amount_drawer × model.predict([total_products, distinct_products])
```

**Model Input Features**:
1. Total number of items in drawer
2. Number of distinct product types (SKU count)

---

#### **smart_cart Function**
```python
def smart_cart(products: list, probabilities: list, costs: list, 
               weights: list, stock: list, PASSENGERS: int,
               MAX_WEIGHTS: int = 90, T_MIN: int = 210, 
               T_MAX: int = 420) -> list
```

**Purpose**: Optimizes cart configuration using linear programming.

**Optimization Model**:

**Objective Function**:
```
Maximize: Σ(V_i × x_i)
where V_i = Pr(sale)_i × Cost_i
```

**Constraints**:
1. **Weight Constraint**: `Σ(weight_i × x_i) ≤ MAX_WEIGHTS` (90 kg)
2. **Demand Constraint**: `x_i ≤ U_i` (Monte Carlo estimate)
3. **Stock Constraint**: `x_i ≤ stock_i`
4. **Time Constraint**: `T_MIN ≤ time(x) ≤ T_MAX` (210-420 minutes)
5. **Non-negativity**: `x_i ≥ 0` for all i

**Algorithm Steps**:
1. Calculate expected value (V_i) for each product
2. Estimate demand upper bounds using Monte Carlo
3. Formulate LP problem with constraints
4. Solve using PuLP optimizer
5. Return optimal product quantities

**Returns**: List of tuples `[(product_id, quantity), ...]`

---

#### **Stock Management Functions**

##### **remove_from_stock**
```python
def remove_from_stock(stock: pd.DataFrame, removal: pd.DataFrame, 
                     key_cols: tuple = ("item_type", "batch"), 
                     qty_col: str = "quantity") -> pd.DataFrame
```

**Purpose**: Removes allocated inventory from stock after cart preparation.

**Process**:
- Matches by key columns (item_type, batch)
- Subtracts quantities
- Removes zero-quantity entries
- Returns updated stock DataFrame

##### **add_to_stock**
```python
def add_to_stock(stock: pd.DataFrame, addition: pd.DataFrame,
                key_cols: tuple = ("item_type", "batch"),
                qty_col: str = "quantity") -> pd.DataFrame
```

**Purpose**: Returns unused inventory to stock after flight.

**Process**:
- Merges returned stock with existing inventory
- Aggregates quantities for matching batches
- Maintains batch-level granularity

---

#### **simulate_flight Function**
```python
def simulate_flight(passengers: int, flight_date: datetime, 
                   trolley_stock: pd.DataFrame) -> pd.DataFrame
```

**Purpose**: Simulates consumption during flight and calculates returns.

**Simulation Logic**:
1. For each product in trolley:
   - Calculate sale probability
   - Simulate actual consumption
   - Determine unused quantity
2. Returns DataFrame with unconsumed stock

### 3. `forecast.py` - Time Series Forecasting Module

#### **get_sales_probability Function**

```python
def get_sales_probability(product_id, target_date, df, passengers=None, 
                         model_params=None, forecast_days=30) -> dict
```

**Purpose**: Forecasts product sales and calculates sale probability using SARIMA models.

**SARIMA Model**:
- **S**easonal **A**uto**R**egressive **I**ntegrated **M**oving **A**verage
- Captures trends, seasonality, and autocorrelation in time series data

**Model Specification**:
```
SARIMA(p, d, q)(P, D, Q)_s
where:
  p, d, q = non-seasonal AR, differencing, MA orders
  P, D, Q = seasonal AR, differencing, MA orders  
  s = seasonal period
```

**Process**:
1. **Data Preparation**:
   - Groups historical sales by date
   - Aggregates sales and passenger counts
   - Creates time series with daily frequency

2. **Passenger Handling**:
   - **Manual Mode**: Uses provided passenger count
   - **Automatic Mode**: Estimates from historical patterns
   - Tracks source for transparency

3. **Forecasting**:
   - Fits SARIMA model to historical sales
   - Generates forecast for target date
   - Calculates confidence intervals

4. **Probability Calculation**:
   ```python
   probability = forecasted_sales / expected_passengers
   ```

**Returns**: Dictionary with:
- `probability`: Sales probability (0.0-1.0)
- `forecast_sales`: Expected sales volume
- `expected_passengers`: Passenger count (manual or estimated)
- `confidence_interval`: Forecast uncertainty bounds
- `status`: 'historical' or 'forecast'
- `passenger_source`: 'manual' or 'estimated'

**Advanced Features**:
- Handles missing dates with interpolation
- Provides confidence intervals for uncertainty quantification
- Supports both historical analysis and future predictions

---

#### **prepare_time_series Function**

```python
def prepare_time_series(df, itemcode, freq='D') -> pd.DataFrame
```

**Purpose**: Preprocesses raw sales data into time series format.

**Transformations**:
1. Filters data for specific product (itemcode)
2. Groups by date
3. Aggregates sales, passengers, and lost sales
4. Converts to datetime index
5. Handles missing dates

---

#### **batch_sales_probability Function**

```python
def batch_sales_probability(product_ids, target_date, df, 
                           passengers=None, model_params=None) -> pd.DataFrame
```

**Purpose**: Efficiently calculates probabilities for multiple products.

**Use Case**: When processing entire cart inventory for a flight.

**Features**:
- Parallel-friendly design
- Error handling per product
- Consolidated DataFrame output
- Consistent passenger count across products

## 📊 Datasets

### Input Data Files

#### 1. **stock.xlsx**
Current inventory snapshot with columns:
- `item_type`: Product identifier
- `batch`: Lot number
- `quantity`: Available units
- `expiration_date`: Product expiry date
- `cost`: Unit cost
- `weight`: Unit weight (kg)

#### 2. **vuelos.xlsx** (flights.xlsx)
Flight schedule with columns:
- `flight_id`: Unique flight identifier
- `flight_date`: Departure date
- `passengers`: Passenger count
- `flight_type`: Short/medium/long haul
- `service_type`: Retail or standard

#### 3. **result_hack_filtrado_con_peso_precioA.xlsx**
Historical sales data:
- `FECHA`: Transaction date
- `ITEMCODE`: Product ID
- `SALES`: Units sold
- `PASSENGERS`: Flight passenger count
- `LOSTSALES`: Unfulfilled demand

### Competition Datasets

1. **HackMTY2025_ConsumptionPrediction_Dataset_v1.xlsx**
   - Flight consumption patterns
   - Standard specifications vs. actual usage
   - Crew feedback on demand

2. **HackMTY2025_ExpirationDateManagement_Dataset_v1.xlsx**
   - Product expiration tracking
   - Lot numbers and batch information
   - Storage locations

3. **HackMTY2025_ProductivityEstimation_Dataset_v1.xlsx**
   - Drawer specifications
   - Item counts and complexity
   - Assembly time records

## 🧮 Algorithms & Models

### 1. **Time Series Forecasting - SARIMA**

**Model Class**: Seasonal AutoRegressive Integrated Moving Average

**Components**:
- **AR (AutoRegressive)**: Uses past values to predict future
- **I (Integrated)**: Differencing to achieve stationarity
- **MA (Moving Average)**: Uses past forecast errors
- **Seasonal Components**: Captures recurring patterns

**Model Selection Process**:
1. Stationarity testing (ADF test)
2. ACF/PACF analysis for parameter estimation
3. Grid search over parameter space
4. AIC/BIC model comparison
5. Residual diagnostics

**Implementation**:
```python
from statsmodels.tsa.statespace.sarimax import SARIMAX

model = SARIMAX(
    data['Sales'],
    order=(p, d, q),
    seasonal_order=(P, D, Q, s),
    enforce_stationarity=False,
    enforce_invertibility=False
)
fitted_model = model.fit(disp=False)
forecast = fitted_model.forecast(steps=forecast_days)
```

---

### 2. **Monte Carlo Simulation**

**Algorithm**: Probabilistic sampling for demand estimation

**Theoretical Basis**:
- Law of Large Numbers
- Central Limit Theorem
- Binomial distribution for independent trials

**Implementation**:
```python
simulations = [np.random.binomial(N, Pr) for _ in range(sim)]
demand_estimate = np.percentile(simulations, percentile)
```

**Why Monte Carlo?**:
- Captures demand uncertainty
- Risk-adjusted inventory planning
- Handles non-normal distributions
- Computationally efficient

---

### 3. **Linear Programming Optimization**

**Framework**: PuLP (Python Linear Programming)

**Problem Type**: Mixed-Integer Linear Programming (MILP)

**Formulation**:
```
Decision Variables: x_i (quantity of product i)

Maximize: 
    Z = Σ(probability_i × cost_i × x_i)

Subject to:
    Σ(weight_i × x_i) ≤ 90                    [Weight constraint]
    x_i ≤ monte_carlo_demand_i  ∀i            [Demand constraints]
    x_i ≤ stock_i               ∀i            [Stock constraints]
    T_MIN ≤ time_model(x) ≤ T_MAX             [Time constraints]
    x_i ≥ 0                     ∀i            [Non-negativity]
```

**Solver**: Default CBC (Coin-or Branch and Cut)

---

### 4. **Random Forest Regression - Productivity**

**Model Type**: Ensemble learning for regression

**Features**:
- `total_products`: Total item count in drawer
- `distinct_products`: Number of unique SKUs

**Target**: Assembly time (minutes)

**Model Characteristics**:
- Non-linear relationships
- Feature importance ranking
- Robust to outliers
- No feature scaling required

**Training Process**:
1. Feature engineering from drawer specifications
2. Train-test split (80-20)
3. Hyperparameter tuning (GridSearchCV)
4. Cross-validation (5-fold)
5. Model persistence (joblib)

**Prediction**:
```python
pipeline = joblib.load('./RFRegressor.joblib')
model = pipeline['model']
time = model.predict([[total_products, distinct_products]])
```

## 🚀 Installation

### Prerequisites

```bash
Python 3.8+
```

### Dependencies

```bash
pip install pandas numpy scipy statsmodels pulp scikit-learn joblib openpyxl
```

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/HackMTY2025.git
cd HackMTY2025

# Install dependencies
pip install -r requirements.txt

# Prepare data files
# Place stock.xlsx and vuelos.xlsx in project root

# Run the main script
python main.py
```

## 💻 Usage

### Basic Execution

```python
import pandas as pd
from main import main

# Load data
stock = pd.read_excel("./stock.xlsx")
flights = pd.read_excel("./vuelos.xlsx")

# Run optimization
main(stock, flights)
```

### Custom Configuration

```python
from functions import smart_cart, MonteCarlo

# Adjust Monte Carlo parameters
demand = MonteCarlo(
    Pr=0.75,           # 75% sale probability
    sim=2000,          # 2000 simulations
    N=150,             # 150 passengers
    percentil=95       # 95th percentile
)

# Customize cart optimization
optimal_cart = smart_cart(
    products=product_list,
    probabilities=prob_list,
    costs=cost_list,
    weights=weight_list,
    stock=stock_list,
    PASSENGERS=180,
    MAX_WEIGHTS=85,    # 85 kg weight limit
    T_MIN=180,         # 3 hours minimum
    T_MAX=360          # 6 hours maximum
)
```

### Forecasting Individual Products

```python
from forecast import get_sales_probability

result = get_sales_probability(
    product_id=4542,
    target_date='2025-11-01',
    df='result_hack_filtrado_con_peso_precioA.xlsx',
    passengers=150     # Manual passenger count
)

print(f"Sale Probability: {result['probability']:.2%}")
print(f"Expected Sales: {result['forecast_sales']:.1f}")
print(f"Confidence Interval: {result['confidence_interval']}")
```

### Batch Probability Calculation

```python
from forecast import batch_sales_probability

products = [4542, 4561, 4568, 4572]
results_df = batch_sales_probability(
    product_ids=products,
    target_date='2025-11-01',
    df='result_hack_filtrado_con_peso_precioA.xlsx',
    passengers=150
)

print(results_df[['product_id', 'probability', 'forecast_sales']])
```

## 📈 Performance Metrics

### Forecasting Accuracy
- **MAPE**: Mean Absolute Percentage Error
- **RMSE**: Root Mean Squared Error
- **MAE**: Mean Absolute Error

### Optimization Efficiency
- **Revenue Maximization**: Expected value per flight
- **Waste Reduction**: Products past expiration
- **Fill Rate**: Demand satisfaction percentage

### Productivity Gains
- **Time Prediction Accuracy**: R² score
- **Planning Efficiency**: Variance reduction
- **Labor Optimization**: Hours saved per shift

## 📝 License

This project was developed for the HackMTY 2025 hackathon. Please check the specific competition rules for usage rights.

## 🏆 Acknowledgments

- **gategroup**: For providing the challenge and datasets
- **HackMTY 2025**: For organizing the hackathon
- All the team involved in this project: Lilian, René, Jorge, Cristóbal.

---

**Built with ❤️ for HackMTY 2025 - Making airline catering smarter, one cart at a time.**
