# Option Strategy Simulation Core Module

This module provides the core functionality for simulating and analyzing option strategies. 

It defines the `OptionStrategy` class, which allows users to define a collection of option legs and analyze their combined performance.

## Key Classes

### `OptionStrategyRepr`

A data representation class that holds key statistics related to an `OptionStrategy`.  It's used for summarizing and presenting the analysis results.

This is accessed as `OptionStrategy.repr()`

E.g. `mydict = ostrat.repr()`

**Fields:**

*   `underlying_price` (float): The current price of the underlying asset.
*   `underlying_symbol` (str): The ticker symbol of the underlying asset.
*   `days_to_expiration` (float): The number of days until the option contracts expire.
*   `volatility` (float): The implied volatility of the options.
*   `expected_move` (float): The expected price movement of the underlying asset based on volatility and time to expiration.  Calculated as one standard deviation.
*   `pop` (float): Probability of Profit - the likelihood of the strategy being profitable.
*   `expected_profit` (float): The expected profit of the strategy, taking into account probabilities.
*   `cost` (float): The initial cost (debit) or credit received for entering the strategy.
*   `theta` (float): The rate of decay of the option's value with respect to time.
*   `delta` (float): The sensitivity of the option's price to changes in the underlying asset's price.
*   `vega` (float): The sensitivity of the option's price to changes in volatility.
*   `title` (str): A descriptive title for the option strategy.
*   `stddev_range` (float): Multiplier of standard deviation for price range sampling.

### `OptionStrategy`

The core class for defining and analyzing option strategies. It holds a list of `OptionLeg` objects and provides methods for calculating PnL, Greeks, and other relevant metrics.

**Fields:**

*   `underlying_price` (float): The current price of the underlying asset.
*   `title` (str, optional): A descriptive title for the option strategy (default: `"Option Strategy"`).
*   `underlying_symbol` (str, optional): The ticker symbol of the underlying asset (default: `"XYZ"`).
*   `stddev_range` (float, optional): Multiplier of standard deviation for price range sampling (default: `STDDEV_RANGE`).
*   `legs` (List[OptionLeg], optional): A list of `OptionLeg` objects representing the individual option contracts in the strategy (default: `[]`).
*   `pnls` (List[OptionPnL], optional): A list of `OptionPnL` objects representing the profit and loss at various expirations (default: `[]`). This list is automatically populated and cleared.
*   `days_to_expiration` (float, optional): The number of days until the option contracts expire. Defaults to average DTE if legs exist.
*   `volatility` (float, optional): The volatility of the underlying asset. Overrides the calculated average volatility from legs, if provided during initialization (e.g., `OptionStrategy(volatility=0.25)`).
*   `monte_carlo` (bool, optional):  Flag indicating whether Monte Carlo simulation should be used (default: `False`).  *Currently Not Implemented*.
*   `num_simulations` (int, optional): Number of price points used to calc PnL curve (default: `NUM_SIMULATIONS`).
*   `r` (float, optional): Risk-free interest rate used in option pricing models (default: `R`).
*   `year_days` (int, optional): Number of days in a year used for volatility calculations (default: `YEAR_DAYS`).

**Methods:**
*   `repr(self) -> OptionStrategyRepr`: Returns an `OptionStrategyRepr` object containing key statistics about the strategy.

*   `add_leg(self, option_type: str, strike_price: float, quantity: int, volatility: float = None, days_to_expiration: float = None, mark: float = None, delta: float = None)`: Adds an `OptionLeg` to the strategy.
    *   `option_type` (str): Type of option ('C' for call, 'P' for put, 'S' for stock).
    *   `strike_price` (float): Strike price of the option.
    *   `quantity` (int): Number of contracts.  Positive for long, negative for short.
    *   `volatility` (float, optional): Volatility of the option. If None, defaults to the strategy's volatility.
    *   `days_to_expiration` (float, optional): Days to expiration. If None, defaults to the strategy's DTE.
    *   `mark` (float, optional): The current market price of the option.  If None, calculated from Black-Scholes
    *   `delta` (float, optional): The delta of the option.  If None, calculated from Black-Scholes

*   `add_pnl(self, partitions: int = None, days_forward: int = None, dte: int = None)`: Calculates and adds `OptionPnL` objects to the strategy. Only one of `partitions`, `days_forward`, or `dte` should be provided at a time.
    *   `partitions` (int, optional):  Calculates PnL at multiple DTEs evenly divided across the total expiration days.
    *   `days_forward` (int, optional): Calculates PnL at a specific number of days forward.
    *   `dte` (int, optional): Calculates PnL at a specific DTE.

*   `option_legs(self) -> List[OptionLeg]`: Returns a list of option legs (excluding stock).
*   `stock_legs(self) -> List[OptionLeg]`: Returns a list of stock legs.

*   `margin(self) -> tuple[float,float]`: returns cash,margin estimated requirements for the position

*   `plot_strategy(self, savefig: str = None, show=True)`: Plots the PnL of the strategy.
    *   `savefig` (str, optional): Filename to save the plot to.
    *   `show` (bool, optional): Whether to display the plot (default: `True`).

### OptionLegRepr

This is accessed as `OptionLeg.repr()`

Each OptionLeg is access through list `OptionStrategy.legs`

E.g. `mydict = ostrat.legs[0].repr()` 

**Fields:**

*   `option_type` (str) : option type of leg  `C`: call, `P`: put, `S`: stock 
*   `strike_price` (float) : strike price of leg
*   `quantity` (int) : quantity of stock or contracts
*   `days_to_expiration` (float) : days to expiration of contract
*   `volatility` (float) : volatility of contract
*   `mark` (float) : market price of stock or contract
*   `delta` (float) : Greeks delta
*   `vega` (float) : Greeks vega
*   `theta` (float) : Greeks theta
*   `gamma` (float) : Greeks gamma

### OptionPnLRepr

This is accessed as `OptionPnl.repr()`

Each OptionPnl is access through list `OptionStrategy.pnls`

E.g. `mydict = ostrat.pnls[0].repr()` 

**Fields:**

*   `days_to_expiration` (float) : days to expire for this PNL estimation
*   `stddev` (float) : underlying price standard deviation at our DTE
*   `expected_profit` (float) : sum profit accross probability distribution
*   `pop` (float) : probability of profit

## Usage Examples

```python
from option_strategy_sim.core import OptionStrategy

from tabulate import tabulate 

# Create an OptionStrategy object
ostrat = OptionStrategy(underlying_price=100, days_to_expiration=30)

# Add option legs
ostrat.add_leg(option_type='C', strike_price=105, quantity=1)  # Long 1 call
ostrat.add_leg(option_type='P', strike_price=95, quantity=-1)  # Short 1 put
ostrat.add_leg(option_type='S', strike_price=100, quantity=100)  # Buy 100 shares of stock

# Calculate PnL at expiration
ostrat.add_pnl()

# Plot the strategy's PnL
# ostrat.plot_strategy()

# Calculate margin requirements
cash_req, margin_req = ostrat.margin()
print(f"Cash Requirement: {cash_req}, Margin Requirement: {margin_req}")


# Adding PnLs at different points in time
ostrat.add_pnl(partitions=5) # adds 4 pnls for points in time before payoff 


# Print a details of the strategy
print(tabulate(ostrat.repr()))
print("--- LEGS ---")
for leg in ostrat.legs:
    print(tabulate(leg.repr()))
print("--- PNLS ---")
for pnl in ostrat.pnls:
    print(tabulate(pnl.repr()))

```

### output 

```
Cash Requirement: 19526.751992378213, Margin Requirement: 4154.893138118537
------------------  -------------------
underlying_price    100.0
underlying_symbol   XYZ
days_to_expiration  30.0
volatility          0.22
expected_move       6.3072039698909546
pop                 0.48318762249837954
expected_profit     -0.2407434982008798
cost                10026.751992378211
theta               -0.7454608802004816
delta               100.43067084654685
vega                16.655831838586465
title               Option Strategy
stddev_range        3.0
r                   0.05
year_days           365
------------------  -------------------
--- LEGS ---
------------------  --------------------
option_type         C
strike_price        105.0
quantity            1
days_to_expiration  30.0
volatility          0.22
mark                0.9082256524837398
delta               0.2492444084617758
vega                9.095734529230747
theta               -0.40752074257807835
gamma               0.050302168229836706
symbol
expirey
------------------  --------------------
------------------  --------------------
option_type         P
strike_price        95.0
quantity            -1
days_to_expiration  30.0
volatility          0.22
mark                0.6407057287016222
delta               -0.18142643808507608
vega                -7.5600973093557196
theta               0.33794013762240327
gamma               0.04180962905931573
symbol
expirey
------------------  --------------------
------------------  ------
option_type         S
strike_price        100.0
quantity            100
days_to_expiration  1000.0
volatility
mark                100.0
delta               1.0
vega                0.0
theta               0.0
gamma               0.0
symbol
expirey
------------------  ------
--- PNLS ---
------------------  ---------
days_to_expiration   0
stddev               6.3072
expected_profit     -0.240743
pop                  0.483188
------------------  ---------
------------------  ---------
days_to_expiration   6
stddev               5.64133
expected_profit     -0.175464
pop                  0.483188
------------------  ---------
------------------  ---------
days_to_expiration  12
stddev               4.88554
expected_profit     -0.117937
pop                  0.485588
------------------  ---------
------------------  ----------
days_to_expiration  18
stddev               3.98903
expected_profit     -0.0684201
pop                  0.490391
------------------  ----------
------------------  ----------
days_to_expiration  24
stddev               2.82067
expected_profit     -0.0273608
pop                  0.492793
------------------  ----------
```

## Notes

*   The module uses the Black-Scholes model for option pricing and Greeks calculation when a mark price is not explicitly given.
*   The number of simulations (`num_simulations`) impacts the granularity of the PnL curve.  Larger values lead to smoother curves but increase computation time.
*   The `monte_carlo` parameter will computed expected profit via monte_carlo methods instead of normal distribution
*   Consider using `add_pnl` judiciously, as each call adds a new `OptionPnl` object and associated calculations, which can impact performance.
* When using `add_leg`, providing both `mark` and `volatility` can lead to inconsistent results unless these are real market values.  It is recommended to provide `volatility` for theoretical analysis. Omitting both will result in volatility defaulting to the OptionStrategy's volatility (or 0.22 if not otherwise defined).