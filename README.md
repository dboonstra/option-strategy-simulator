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

## Usage Examples

### Example 1: Long Call Strategy

```python
from option_strategy_sim import OptionStrategy

# Initialize the option strategy
strategy = OptionStrategy(underlying_price=100, days_to_expiration=30, title="Long Call")

# Add a long call option leg
strategy.add_leg(option_type='C', strike_price=105, quantity=1, volatility=0.25)

# Print a summary of the strategy
print(strategy.repr())

# Plot the strategy's P&L
strategy.plot_strategy()
```

### Example 2: Short Put Strategy

```python
from option_strategy_sim import OptionStrategy

# Initialize the strategy
strategy = OptionStrategy(underlying_price=50, days_to_expiration=60, title="Short Put")

# Add a short put option leg
strategy.add_leg(option_type='P', strike_price=45, quantity=-1, volatility=0.30)

# Display key statistics
print(strategy.repr())

# Visualize the strategy
strategy.plot_strategy()
```

### Example 3: Iron Condor Strategy

```python
from option_strategy_sim import OptionStrategy

# Define strategy parameters
strategy = OptionStrategy(underlying_price=100, days_to_expiration=45, title="Iron Condor")

# Add the four legs of the Iron Condor
strategy.add_leg(option_type='C', strike_price=110, quantity=1, volatility=0.20) # Short Call
strategy.add_leg(option_type='C', strike_price=115, quantity=-1, volatility=0.15) # Long Call
strategy.add_leg(option_type='P', strike_price=90, quantity=1, volatility=0.20)  # Short Put
strategy.add_leg(option_type='P', strike_price=85, quantity=-1, volatility=0.15)  # Long Put

# Analyze the strategy
print(strategy.repr())

# Plot the payoff
strategy.plot_strategy()
```

### Example 4: Visualizing P&L at Different Expirations

```python
from option_strategy_sim import OptionStrategy

# Create a simple call option strategy
strategy = OptionStrategy(underlying_price=150, days_to_expiration=60, title="Call Option with Time Decay")
strategy.add_leg(option_type='C', strike_price=155, quantity=1, volatility=0.22)

# Add P&L calculations at different days to expiration
strategy.add_pnl(days_forward=15)  # P&L 15 days forward
strategy.add_pnl(days_forward=30)  # P&L 30 days forward

# Plot the strategy's P&L
strategy.plot_strategy()
```

For more advanced usage and customization options, refer to the examples and documentation within the code.

## Contributing

Contributions are welcome! Feel free to submit pull requests, report bugs, or suggest enhancements.

## Disclaimer

This simulator is intended for educational and analytical purposes only. It should not be considered financial advice. Options trading carries inherent risks, and past simulated performance does not guarantee future real-world results.