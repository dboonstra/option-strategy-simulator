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
underlying_price=100.0 underlying_symbol='XYZ' days_to_expiration=30.0 volatility=0.3 expected_move=8.600732686214938 pop=0.21848346818853234 expected_profit=-0.2109222338162562 cost=168.65025924292 theta=-0.6249814604296636 delta=0.3168613655540851 vega=10.209907457200684 title='Long Call' stddev_range=3.0

![Image](https://github.com/user-attachments/assets/a9a5d086-9688-45a8-b792-8d6fa12b2be3)

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
underlying_price=50.0 underlying_symbol='XYZ' days_to_expiration=60.0 volatility=0.3 expected_move=6.081636405595374 pop=0.8202121979678375 expected_profit=-0.1392655637013267 cost=-54.15697214414061 theta=-0.07504861280478492 delta=0.15996333839898913 vega=4.9317059900913005 title='Short Put' stddev_range=3.0

![Image](https://github.com/user-attachments/assets/16a82a2f-3087-41da-9c2b-8d38ced42bdb)

### Example 3: Iron Condor Strategy

```python
from option_strategy_sim import OptionStrategy

# Define strategy parameters
ostrat = OptionStrategy(underlying_price=100, days_to_expiration=45, title="Iron Condor")

# Add the four legs of the Iron Condor
# ostrat.add_leg(option_type='C', strike_price=110, quantity=-1, volatility=0.20) # Long Call
# ostrat.add_leg(option_type='C', strike_price=115, quantity=1, volatility=0.15) # Short Call
# ostrat.add_leg(option_type='P', strike_price=90, quantity=-1, volatility=0.20)  # Short Put
# ostrat.add_leg(option_type='P', strike_price=85, quantity=1, volatility=0.15)  # Long Put

# We can add them together as a list group or a pandas dataframe
# using ostrat.add_legs
iron_condor_legs = [
    {"option_type":'C', "strike_price":110, "quantity":-1, "volatility":0.20},
    {"option_type":'C', "strike_price":115, "quantity":1, "volatility":0.15},
    {"option_type":'P', "strike_price":90,  "quantity":-1, "volatility":0.20},
    {"option_type":'P', "strike_price":85,  "quantity":1, "volatility":0.15},
]
ostrat.add_legs( iron_condor_legs )


# Analyze the strategy
print(ostrat.repr())

# Plot the payoff
ostrat.plot_strategy()

```
underlying_price=100.0 underlying_symbol='XYZ' days_to_expiration=45.0 volatility=0.175 expected_move=6.144660227796855 pop=0.9154980278115109 expected_profit=0.2780350407087193 cost=-50.41750700746802 theta=-0.1933800333870672 delta=-0.05085915120209511 vega=10.967046550138337 title='Iron Condor' stddev_range=3.0

![Image](https://github.com/user-attachments/assets/8f14d3dd-a1d4-440c-ad67-72a675565acb)

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
# savefig allows us to save the figure to a PNG file
ostrat.plot_strategy(savefig='ic.png', show=True)
```
![Image](https://github.com/user-attachments/assets/38c680d5-6f42-40a0-9241-ce423c36461c)

For more usage and customization options, refer to the examples in ./dev and documentation within the code.

## Contributing

Contributions are welcome! Feel free to submit pull requests, report bugs, or suggest enhancements.

## Disclaimer

This simulator is intended for educational and analytical purposes only. It should not be considered financial advice. Options trading carries inherent risks, and past simulated performance does not guarantee future real-world results.


