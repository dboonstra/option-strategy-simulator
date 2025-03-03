# --------------
#             __        __           __                    
#  ___  ___  / /_  ___ / /________ _/ /_  _______  _______ 
# / _ \/ _ \/ __/ (_-</ __/ __/ _ `/ __/ / __/ _ \/ __/ -_)
# \___/ .__/\__/ /___/\__/_/  \_,_/\__/  \__/\___/_/  \__/ 
#    /_/                                                   
#

import numpy as np
from scipy.stats import norm
import pandas as pd

from pydantic import BaseModel, field_validator, ValidationError # type: ignore
from typing import List

from .leg import OptionLeg
from .pnl import OptionPnL
from .plot import plot_strategy as _plot_stragey
from .margin import MarginCalculator
from .utils import class_args, model_repr

# use X std deviations for price range sampling
STDDEV_RANGE = 3
# for how granular we devide our price range or multiples of carlos
NUM_SIMULATIONS = 1000
# days in the year for stddev calc, some ppl like 255 or 251 trade days instead of 365
YEAR_DAYS = 365
# our risk free rate
R = 0.05

class OptionStrategyRepr(BaseModel, extra='allow'):
    """ 
    Representation of OptionPnL key stats
    """
    underlying_price: float
    underlying_symbol: str
    days_to_expiration: float
    volatility: float
    expected_move: float
    pop: float
    expected_profit: float
    expected_roi: float
    cost: float
    margin: float
    theta: float
    delta: float
    vega: float
    gamma: float
    title: str 
    stddev_range: float 
    #monte_carlo: bool = False
    #num_simulations: int 
    #r: float 
    #year_days: int

    def __init__(self, **kwargs):
        # Initialize with known fields only
        super().__init__(**class_args(kwargs, self.model_fields))



class OptionStrategy(BaseModel, arbitrary_types_allowed=True):
    """Represents a collection of option legs and provides methods for analysis."""
    underlying_price: float

    # optional
    title: str = "Option Strategy"
    monte_carlo: bool = False
    underlying_symbol: str = "XYZ"

    # GLOBAL OVERRIDES 
    stddev_range: float = STDDEV_RANGE
    num_simulations: int = NUM_SIMULATIONS
    r: float = R
    year_days: int = YEAR_DAYS

    # internal
    legs: List[OptionLeg] = []
    pnls: List[OptionPnL] = []
    days_to_expiration: float = None # will default DTE
    sigma: float = None  # will override vol calc from legs


    def __init__(self, **data):
        # store volatility as sigma for default volatility
        if "volatility" in data:
            data["sigma"] = data["volatility"]
            del data["volatility"]
        #del data["sigma"]
        super().__init__(**data)

    def __repr__(self):
        return model_repr(self)

    def repr(self) -> OptionStrategyRepr:
        """Model of key OptionPnL Stat Components"""
        cost, margin = self.margin()
        data = dict(self)
        data["theta"] = self.theta()
        data["delta"] = self.delta()
        data["vega"] = self.vega()
        data["gamma"] = self.gamma()
        data["cost"] = cost
        data["margin"] = margin
        data["volatility"] = self.volatility()
        data["expected_move"] = self.expected_move()
        data["pop"] = self.pop()
        data["expected_profit"] = self.expected_profit()

        # roll up cost, dte, profit into an roi estimate
        data["expected_roi"] = 100 * (data["expected_profit"] * 365/self.days_to_expiration)/cost
        return OptionStrategyRepr(**data)

    def reset_pnl(self):
        # update strategy days_to_expiration
        self.days_to_expiration = self.calc_current_dte()
        # clear pnls to be recalculated
        self.pnls = []


    # ________________________
    # Leg interactions

    def add_legs(
            self,
            legs: list[dict] | pd.DataFrame,
        ):
        if not isinstance(legs, list):
            # make it a list from pandas
            legs = legs.to_dict('records')
        for leg in legs:
            if leg['option_type'] == 'S':
                if 'mark' in leg:
                    if leg['mark'] is None:
                        leg['mark'] = leg['strike_price']
                else:
                    leg['mark'] = leg['strike_price']
                leg['days_to_expiration'] = 1000
            if 'volatility' in leg:
                if leg['volatility'] is None:
                    leg['volatility'] = self.volatility()
            else:
                leg['volatility'] = self.volatility()
            if 'days_to_expiration' not in leg:
                leg['days_to_expiration'] = self.days_to_expiration
            leg['optionstrategy'] = self
            self.legs.append(OptionLeg(**leg))
            self.reset_pnl()


    def add_leg(
        self,
        option_type: str,
        strike_price: float,
        quantity: int,
        volatility: float = None,
        days_to_expiration: float = None,
        mark: float = None,
        delta: float = None,
    ):
        """Adds an option leg to the strategy."""
        if option_type == 'S':
            if mark is None:
                mark = strike_price
            if days_to_expiration is None:
                days_to_expiration = 1000
        elif days_to_expiration is None:
            days_to_expiration = self.days_to_expiration
        if mark is None and volatility is None:
            volatility = self.volatility()
            
        self.legs.append(
            OptionLeg(
                option_type=option_type,
                strike_price=strike_price,
                days_to_expiration=days_to_expiration,
                quantity=quantity,
                volatility=volatility,
                mark=mark,
                delta=delta,
                optionstrategy=self,
            )
        )
        self.reset_pnl()

    def delta(self) -> float:
        """Calculate sum delta in the legs"""
        return sum(leg.delta * leg.quantity for leg in self.legs)

    def theta(self) -> float:
        """Calculate sum delta in the legs"""
        return sum(leg.theta * leg.quantity for leg in self.option_legs())
    
    def vega(self) -> float:
        """Calculate sum delta in the legs"""
        return sum(leg.vega * leg.quantity for leg in self.option_legs())

    def gamma(self) -> float:
        """Calculate sum delta in the legs"""
        return sum(leg.gamma * leg.quantity for leg in self.option_legs())

    def cost(self) -> float:
        """Calculate sum delta in the legs"""
        # return raw sum outlay for position
        opt_sum = sum(leg.mark * leg.quantity for leg in self.option_legs()) * 100
        stk_sum = sum(leg.mark * leg.quantity for leg in self.stock_legs())
        return opt_sum + stk_sum

    def calc_current_dte(self) -> float:
        """Return average days_to_expire in the legs"""
        option_legs = self.option_legs()
        if len(option_legs) > 0:
            return sum(
                leg.days_to_expiration for leg in self.option_legs()
            )/len(option_legs)
        else:
            return 1.0

    def volatility(self) -> float:
        """Calculate volatitility as average of the volatility in the legs
        or user may override with __init__( volatility = .x )
        """
        option_legs = self.option_legs()
        if len(option_legs) > 0:
            return sum(leg.volatility for leg in option_legs) / len(option_legs)
        if self.sigma is not None and self.sigma > 0:
            return self.sigma
        return 0.22  # if all else none , 22 is fair
    
    def option_legs(self) -> List[OptionLeg]:
        """Returns a list of option legs, excluding underlying stock legs."""
        return [leg for leg in self.legs if leg.option_type != 'S']

    def stock_legs(self) -> List[OptionLeg]:
        """Returns a list of option legs, excluding underlying stock legs."""
        return [leg for leg in self.legs if leg.option_type == 'S']
    # ________________________
    # pnl interactions

    def add_pnl(self, partitions: int = None, days_forward: int = None, dte: int = None):
        """
        Calculates and adds PnL objects to the strategy based on different DTE (Days To Expiration) configurations.

        Args:
            partitions (int, optional): If provided, calculates PnL at multiple DTEs evenly divided
                across the total expiration days. Must be greater than 1.
                For example, if set to 3, it will create PnL objects at 1/3 and 2/3
                of the total expiration time, in addition to the payoff PnL.
            days_forward (int, optional): If provided, calculates PnL at a specific number of days forward
                from the current time. It derives the target `dte` from `self.days_to_expiration`.
                Must be a positive integer.
            dte (int, optional): If provided, calculates PnL at a specific DTE. 
                Must be >= 0 and <= `self.days_to_expiration`.

        This method handles several cases to create a series of PnL objects:
        1. It will always ensure there's a payoff PnL (at max DTE).
        2. It can compute PnL at regular intervals based on the `partitions`.
        3. It can create a PnL for a forward-looking DTE using `days_forward`.
        4. It can generate a PnL for a specific `dte`.

        Note: Only one of the `partitions`, `days_forward`, or `dte` should be provided at a time. If more than one
        is provided, it may lead to duplicate PnL entries or unexpected behavior.
        """
        ostrat_dte = self.days_to_expiration
        # Ensure that a payoff PnL exists (at max DTE)
        if len(self.pnls) == 0:
            self.pnls.append(OptionPnL(optionstrategy=self, payoff=True))
        # Handle PnLs at partitioned intervals if partitions > 1
        if partitions is not None and partitions > 1:
            part_len: int = round(ostrat_dte/partitions)
            for i in range(partitions)[1:]:
                self.pnls.append(OptionPnL(optionstrategy=self, days_to_expiration=int(part_len * i)))
            return
        # Handle PnL at a specific number of days forward
        if days_forward is not None and days_forward > 0:
            dte = ostrat_dte - days_forward
            self.pnls.append(OptionPnL(optionstrategy=self, days_to_expiration=dte))
            return
        # Handle PnL at a specific DTE
        if dte is not None:
            if dte >= 0 and dte <= ostrat_dte:
                self.pnls.append(OptionPnL(optionstrategy=self, days_to_expiration=dte))
            return

    # pnl data accessor 
    def get_pnl_attr(self, key: str, idx: int = 0):
        if len(self.pnls) == 0:
            self.add_pnl()
        if idx >= len(self.pnls):
            raise ValueError(f"Pnl Attr idx:{idx} move must index valid pnl object")
        return dict(self.pnls[idx])[key]

    def expected_move(self, idx: int = 0) -> float:
        # alias to stddev 
        return self.get_pnl_attr("stddev", idx)
    
    def stddev(self, idx: int = 0) -> float:
        return self.get_pnl_attr("stddev", idx)

    def dte(self, idx: int = 0) -> float:
        return self.get_pnl_attr("days_to_expiration", idx)

    def price_range(self, idx: int = 0) -> float:
        return self.get_pnl_attr("price_range", idx)

    def pnl_values(self, idx: int = 0) -> float:
        return self.get_pnl_attr("pnl_values", idx)

    def pop(self, idx: int = 0) -> float:
        return self.get_pnl_attr("pop", idx)

    def expected_profit(self, idx: int = 0) -> float:
        return self.get_pnl_attr("expected_profit", idx)
    
    def expected_pnl_values(self, idx: int = 0) -> float:
        return self.get_pnl_attr("expected_pnl_values", idx)

    # ________________________
    # plot interactions
    def plot_strategy(self, savefig: str = None, show=True):
        """ Plot the strategy, 
        Args:
            savefig: (str)  filename to save plot to 
            show: (bool) set to False if you do not want display (to write file only)
        """
        _plot_stragey(self, savefig=savefig, show=show)
    
    # ________________________
    # margin interactions
    def margin(self) -> tuple[float,float]:
       """Calculate margin requirements for the strategy.
       Returns: tuple( cash_requirement, margin_requirement )
       """
       return MarginCalculator(self).calculate_margin()
    
