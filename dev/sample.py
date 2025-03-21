import sys
sys.path.insert(0,"./src")
sys.path.insert(0,"../src")
print(sys.path)
print(type(sys.path))

from option_strategy_sim import (
    OptionStrategy, 
    calculate_price_probability,
    black_scholes,
    )
import json 


underlying_price = 104.65
dte = 42


print("Black Scholes")
price, delta, theta, vega, gamma = black_scholes(
    underlying_price=underlying_price,
    strike_price=105,
    time_days = dte,
    r=0.05,
    volatility=0.24,
    option_type = 'C',   
)
print(f"Black Scholes XYZ at C105 : price({price}, delta({delta}), theta({theta}))")
print()

print("Price Probability")
probability = calculate_price_probability(
    underlying_price=underlying_price,
    strike_price=105,
    time_days = dte,
    r=0.05,
    volatility=0.24,
)
print(f"Probability of of > 105 move: {probability}")


calls = [
    {'option_type':'C', 'strike_price':105.0, 'mark':5.68, 'volatility':0.41, 'days_to_expiration':dte},
    {'option_type':'C', 'strike_price':108.0, 'mark':4.40, 'volatility':0.41, 'days_to_expiration':dte},
    {'option_type':'C', 'strike_price':111.0, 'mark':3.30, 'volatility':0.41, 'days_to_expiration':dte},
    ]

puts = [
    {'option_type':'P', 'strike_price':104.0, 'mark':5.10, 'volatility':0.37, 'days_to_expiration':dte},
    {'option_type':'P', 'strike_price':101.0, 'mark':3.75, 'volatility':0.37, 'days_to_expiration':dte},
    {'option_type':'P', 'strike_price':98.0, 'mark':2.68, 'volatility':0.37, 'days_to_expiration':dte},
    ]

stocks = [
    {'option_type':'S', 'strike_price':underlying_price, 'mark':underlying_price, 'volatility':0.37},
    ]


sell = { "quantity": -1 }
buy = { "quantity": 1 }
buys = { "quantity": 100 }

xtests: dict = {
    "longCall":     [{**calls[1], **buy } ],
    "longPut":      [{**puts[1],  **buy }],
    "shortPut":     [{**puts[1],  **sell }],
    "longStraddle": [
        {**calls[0], **buy }, 
        { **puts[0], **buy }
        ],
    "condor": [
        {**calls[2], **buy }, 
        {**calls[1], **sell }, 
        { **puts[1], **sell },
        { **puts[2], **buy },
        ],
}
tests: dict = {
    #"longCall":     [{**calls[1], **buy } ],
    #"stocks":     [{**stocks[0], **buys } ],
    #"covered":    [{**stocks[0], **buys } , {**calls[1], **sell }],
    #"spread":    [{**calls[1], **sell },{**calls[2], **buy } ],
    "spread": [
        {**calls[2], **buy }, 
        {**calls[1], **sell }, 
        ],
    "calendar_spread": [
        {**calls[2], **buy, "days_to_expiration":60 }, 
        {**calls[1], **sell }, 
        ],

}


def dump_obj(obj: object):
    print(str(type(obj)))
    print(json.dumps(dict(obj.repr()), indent=4))

for test, legs in tests.items():
    ostrat = OptionStrategy(
        title=test,
        underlying_price=underlying_price, 
        stddev_range = 3,
        num_simulations = 1000,

        )
    for leg in legs:
        # leg["mark"] = bscholes(leg,d,underlying_price)
        # ostrat.add_leg(**{**leg, "mark":None})
        ostrat.add_leg(**leg)

    # Now you can get margin:
    cash , margin = ostrat.margin()
    print("Total Margin:", margin)
    print("Total Cash:", cash)

    print("partition length = ", len(ostrat.pnls))
    ostrat.add_pnl(partitions=3)
    ostrat.add_pnl(dte=1)
    print("partition length = ", len(ostrat.pnls))

    print("OptionStrategy")
    dump_obj(ostrat)
    print("OptionLeg's")
    for leg in ostrat.legs:
        dump_obj(leg)
    print("OptionPnL's")
    for pnl in ostrat.pnls:
        dump_obj(pnl)

    print(f"plot {ostrat.title}")
    ostrat.plot_strategy()

