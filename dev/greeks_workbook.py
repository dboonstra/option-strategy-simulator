import sys
sys.path.insert(0,"src")
sys.path.insert(0,"../src")

from option_strategy_sim import (
    calculate_price_probability,
    black_scholes,
    expected_move,
    implied_volatility_newton_raphson,
    )

# SETUP
symbol: str = "XYZ"
underlying_price: float = 104.65
dte: float = 42
volatility: float = 0.22
strike: float = 115.0



# Expected Move of underlying
em = expected_move(underlying_price, volatility, dte)
print(f"Expected move from {underlying_price} in {dte} days:\n\t{em}")
print()



# blackscholes greeks of contract
price, delta, theta, vega, gamma = black_scholes(
    underlying_price=underlying_price,
    strike_price=strike,
    time_days = dte,
    volatility=volatility,
    option_type = 'C',   
)

print(f"Black Scholes XYZ of Call @105 with iv({volatility}):")
print(f"\tprice({price}, delta({delta}), theta({theta}), vega({vega}), gamma({gamma})")
print()




iv_nr, delta_nr, theta_nr, vega_nr, gamma_nr = implied_volatility_newton_raphson(    
    underlying_price=underlying_price,
    strike_price=strike,
    time_days = dte,
    mark = 1.00,  # pricing contractt at one dollar
    option_type = 'C'
)
print(f"With XYZ Call @105 price of $1.00:")
print(f"\tvolatility({iv_nr}, delta({delta_nr}), theta({theta_nr}), vega({vega_nr}), gamma({gamma_nr})")
print()


# probability of price action
An expected move provides the range for a 1 standard deviation move.
Given volatility and days to expiration, we can also use the distribution to determine the probability of an underlying breaching a price in the time frame.



# underlying price breach probability, related to probability of profit 
probability = calculate_price_probability(
    underlying_price=underlying_price,
    strike_price=strike,
    time_days = dte,
    volatility=volatility,
)
print(f"Probability of underlying moving from {underlying_price} to > {strike} in {dte} days:\n\t{probability}")
print()


