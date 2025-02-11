# Option Strategy Simulator: Analysis for Options Trading, Fortune Telling 🔮


This Python package provides tools for constructing, analyzing, and visualizing option strategies. It enables users to evaluate potential profitability, risk exposure, and the impact of time decay on various option positions.

## Features

*   **Strategy Construction:** Create custom option strategies by combining calls, puts, and underlying stock positions.
*   **Black-Scholes Pricing:** Utilizes the Black-Scholes model for option price calculation, Greek estimation, and probability analysis.
*   **Multi-Leg Support:** Manage complex strategies with multiple option legs.
*   **Volatility Modeling:** Allows for volatility input at the leg level or a global override for strategy-level volatility.
*   **Risk Analysis (Greeks):** Provides key risk metrics, including Delta, Theta, and Vega.
*   **Profit & Loss (P&L) Visualization:** Visualize strategy P&L across a range of underlying prices.
*   **Probability of Profit (POP) Calculation:** Estimate the likelihood of achieving a profitable outcome.
*   **Expected Outcome (P&L Curve) Calculation:** Project potential P&L scenarios.
*   **Time Decay Simulation:** Model P&L changes over time with varying Days To Expiration (DTE).
*   **Margin Calculation:** Estimate margin requirements for a given strategy.
*   **Plotting Tools:** Generate P&L charts and strategy visualizations using Matplotlib.

## Installation

1.  Ensure you have Python 3.7+ installed.
2.  Clone the repository:

    ```bash
    git clone git@github.com:dboonstra/option-strategy-simulator.git
    cd option-strategy-simulator
    ```

3.  Install wheel and dependencies using pip

    ```bash
    pip install .
    ```


If you are using *uv* and have issue with plot viewing, https://github.com/astral-sh/uv/issues/6893 may have some hints for matplotlib backend setup of tkaag/pyqt.
Otherwise, you may have more success with miniconda.

## Usage 

* init 
* add legs
* add option pnl time points 
* retrieve data , plot

### OptionStrategy() initialization 
Rquired:
* underlying_price (float) underlying etf/equity price 

Optional:
* title (str) name of strategy
* underlying_symbol (str) symbol of etf/equity
* days_to_expriation (float) default contracts to this DTE
* volatility (float, .25) default contracts to this volatility
* stddev_range (float, 3.0) how many standards of deviation to use for plot and estimations
* monte_carl (bool,False) whether to use monte carlo sims for profit estimation
* num_simulations (int, 1000) number of plot points and monte_carlo simulations

### Add legs with ostrat.add_leg()
Required:
* option_type (str) P,C,S
* strike_price (float) strike of contract, if not stock leg ('S')
* quantity (int) quantity bought (+) or sold (-)

Required if not using ostrat defaults:

* mark (float) market price 

if not provided, mark will be calculated with black scholes using volatility

* volatility (float) 

If not provided volatility will be calculated by the market price.

If the market price is not provided, volatility will default to ostrat default 

* days_to_expiration (float) if not provided, the `ostrat.days_to_expiration` will be used.

### Add pnls with ostrat.add_pnl() 
All parameters are optional 

Required: 
* partitions (int)

If provided, calculates PnL at multiple DTEs evenly divided
    across the total expiration days. Must be greater than 1.
    
For example, if set to 3, it will create PnL objects at 1/3 and 2/3
    of the total expiration time, in addition to the payoff PnL.

* days_forward (int): 

If provided, calculates PnL at a specific number of days forward
    from the current time. It derives the target `dte` from `ostrat.days_to_expiration`. Must be a positive integer.

* dte (int): 

If provided, calculates PnL at a specific DTE. 
    Must be >= 0 and <= `ostrat.days_to_expiration`.


## Examples

### Example 1: Long Call Strategy

```python
from option_strategy_sim import OptionStrategy

# Initialize the option strategy
ostrat = OptionStrategy(underlying_price=100, days_to_expiration=30, volatility=0.3, title="Long Call")

# Add a long call option leg
ostrat.add_leg(option_type='C', strike_price=105, quantity=1)

# Print a summary of the strategy
print(ostrat.repr())

# Plot the strategy's P&L
ostrat.plot_strategy()
```
![Image](https://github.com/user-attachments/assets/c60e5500-7c4c-4768-859d-1a8da3324b02)

### Example 2: Short Put Strategy

```python
from option_strategy_sim import OptionStrategy

# Initialize the strategy
ostrat = OptionStrategy(underlying_price=50, days_to_expiration=60, title="Short Put")

# Add a short put option leg
ostrat.add_leg(option_type='P', strike_price=45, quantity=-1, volatility=0.30)

# Display key statistics
print(ostrat.repr())

# Visualize the strategy
ostrat.plot_strategy()
```
![Image](https://github.com/user-attachments/assets/60c0f1e8-2a40-4b9f-9ece-45804ffbbc2c)

### Example 3: Iron Condor Strategy

```python
from option_strategy_sim import OptionStrategy

# Define strategy parameters
ostrat = OptionStrategy(underlying_price=100, days_to_expiration=45, title="Iron Condor")

# Add the four legs of the Iron Condor
ostrat.add_leg(option_type='C', strike_price=110, quantity=-1, volatility=0.20) # Long Call
ostrat.add_leg(option_type='C', strike_price=115, quantity=1, volatility=0.15) # Short Call
ostrat.add_leg(option_type='P', strike_price=90, quantity=-1, volatility=0.20)  # Short Put
ostrat.add_leg(option_type='P', strike_price=85, quantity=1, volatility=0.15)  # Long Put


# Analyze the strategy
print(ostrat.repr())

# Plot the payoff
ostrat.plot_strategy()

```
![Image](https://github.com/user-attachments/assets/6e613649-b7cc-48b3-b5a0-d27b9c3d5bdf)

underlying_price=100.0 underlying_symbol='XYZ' days_to_expiration=45.0 volatility=0.175 expected_move=6.144660227796855 pop=0.9154980278115109 expected_profit=0.2780350407087193 cost=-50.41750700746802 theta=-0.1933800333870672 delta=-0.05085915120209511 vega=10.967046550138337 title='Iron Condor' monte_carlo=False stddev_range=3.0 num_simulations=1000 r=0.05 year_days=365

### Example 4: Visualizing P&L at Different Expirations

```python
from option_strategy_sim import OptionStrategy

# Create a simple call option strategy
ostrat = OptionStrategy(underlying_price=150, days_to_expiration=60, title="Call Option with Time Decay")
ostrat.add_leg(option_type='C', strike_price=155, quantity=1, volatility=0.22)

# Add P&L calculations at different days to expiration
ostrat.add_pnl(days_forward=15)  # P&L 15 days forward
ostrat.add_pnl(days_forward=30)  # P&L 30 days forward

# Plot the strategy's P&L
ostrat.plot_strategy()
```
![Image](https://github.com/user-attachments/assets/83c08b01-79fd-4a53-8626-a488061bd2f3)

For more usage and customization options, refer to the examples in ./dev and documentation within the code.

## Contributing

Contributions are welcome! Feel free to submit pull requests, report bugs, or suggest enhancements.

## Disclaimer

This simulator is intended for educational and analytical purposes only. It should not be considered financial advice. Options trading carries inherent risks, and past simulated performance does not guarantee future real-world results.


