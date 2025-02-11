
import sys
sys.path.insert(0,"src")
sys.path.insert(0,"../src")
from option_strategy_sim import OptionStrategy
from tabulate import tabulate

# SETUP
symbol: str = "XYZ"
underlying_price: float = 100.0
dte: float = 42
volatility: float = 0.3


# ---------------------------------------------
# a chain of calls and puts and some stocks
calls = [
    {'option_type':'C', 'strike_price':105.0, 'mark':5.68, 'volatility':0.41, },
    {'option_type':'C', 'strike_price':108.0, 'mark':4.40, 'volatility':0.45, },
    {'option_type':'C', 'strike_price':111.0, 'mark':3.30, 'volatility':0.51, },
    ]

puts = [
    {'option_type':'P', 'strike_price':104.0, 'mark':5.10, 'volatility':0.37, },
    {'option_type':'P', 'strike_price':101.0, 'mark':3.75, 'volatility':0.39, },
    {'option_type':'P', 'strike_price':98.0, 'mark':2.68, 'volatility':0.41, },
    ]

stocks = [
    {'option_type':'S', 'strike_price':underlying_price, 'mark':underlying_price, 'volatility':0.37},
    ]

# ---------------------------------------------

def new_ostrat(title:str) -> OptionStrategy:
    """ A new OptionStrategy object with a title """
    return OptionStrategy(
        title=title, 
        days_to_expiration = dte,
        underlying_price=underlying_price,
        symbol=symbol,
    )

def create_leg(contract:dict, quantity: int) -> dict:
    """ 
    function to define a buy or sell leg order 
    gets a contract dict from option chain and adds a quantity to it 
    """
    mycontract = contract.copy()  
    mycontract["quantity"] = quantity
    return mycontract

# dump stats of our strategy
def print_stats(obj: any, legs: bool = False, pnls: bool = False) -> None:
    """ 
    use tabulate to print the strategy stats via repr()
    and optional leg and pnl stats
    """
    print(tabulate(obj.repr()))
    if isinstance(obj, OptionStrategy):
        if legs:
            print("Legs: _________________________")
            for leg in obj.legs:
                print_stats(leg)
        if pnls:
            print("PNLs: _________________________")
            for pnl in obj.pnls:
                print_stats(pnl)
                print("--")
# create new strategy with a long call 
# buy the 108 strike call
long_call_leg: dict = create_leg(calls[1], 1)
ostrat = new_ostrat("longCall")
ostrat.add_leg(**long_call_leg)
ostrat.plot_strategy()
print_stats(ostrat, legs=True, pnls=True)


# now make a credit spread with the 105 strike call 
ostrat = new_ostrat("call_spread")
# sell the 105 and buy the 108 strikes
short_call_leg: dict = create_leg(calls[0], -1)
long_call_leg: dict = create_leg(calls[1], 1)
ostrat.add_leg(**long_call_leg)
ostrat.add_leg(**short_call_leg)
ostrat.plot_strategy()
print_stats(ostrat, legs=True, pnls=True)

# make an iron condor with puts added  
ostrat = new_ostrat("iron condor")
# sell the 105 and buy the 108 strikes
short_call_leg: dict = create_leg(calls[1], -1)
long_call_leg: dict = create_leg(calls[2], 1)
short_put_leg: dict = create_leg(puts[1], -1)
long_put_leg: dict = create_leg(puts[2], 1)
ostrat.add_leg(**long_call_leg)
ostrat.add_leg(**short_call_leg)
ostrat.add_leg(**long_put_leg)
ostrat.add_leg(**short_put_leg)

# now we will add more pnls for theoretical DTE analysis
ostrat.add_pnl(dte=14)
ostrat.add_pnl(dte=3)
ostrat.plot_strategy()
print_stats(ostrat, legs=False, pnls=True)



