# --------------
#             __              __
#  ___  ___  / /_  ___  ___  / /
# / _ \/ _ \/ __/ / _ \/ _ \/ /
# \___/ .__/\__/ / .__/_//_/_/
#    /_/        /_/
#

import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
from pydantic import BaseModel, field_validator, ValidationError # type: ignore
from typing import List, Any

from .greeks import black_scholes
from .utils import class_args, model_repr

class OptionPnLRepr(BaseModel, extra='allow'):
    """
    Representation of OptionPnL key stats
    """
    days_to_expiration: float = None
    payoff: bool = False  # True if we are reviewing expiration
    stddev: float = None  # standard deviation at our DTE
    expected_profit: float = None
    pop: float = None

    def __init__(self, **kwargs):
        # Initialize with known fields only
        super().__init__(**class_args(kwargs, self.model_fields))


class OptionPnL(BaseModel, arbitrary_types_allowed=True):
    optionstrategy: 'OptionStrategy'
    days_to_expiration: float = None
    payoff: bool = False  # True if we are reviewing expiration

    # internal
    stddev: float = None  # standard deviation at our DTE
    expected_profit: float = None
    pop: float = None

    price_range: np.ndarray = None        # price range for our stddev
    pnl_values: np.ndarray = None         # PnL array for price_range

    expected_pnl_values: np.ndarray = None # PnL array weighted by probability
    #########################################
    # Parent OptionStrategy data access points
    # optionstrategy.underlying_price
    # optionstrategy.r
    # optionstrategy.num_simulations
    # optionstrategy.days_to_expiration
    # optionstrategy.stddev_range
    # optionstrategy.year_days
    # optionstrategy.legs
    # optionstrategy.volatility()
    #########################################


    def __init__(self, **data):
        super().__init__(**data)
        if self.payoff:
            # self.days_to_expiration = self.optionstrategy.days_to_expiration
            self.days_to_expiration = 0
        # build PnL profile
        self.stddev = self.calc_stddev()
        self.price_range = self.calc_price_range()
        self.pnl_values = self.calc_pnl_values()
        self.pop = self.calc_pop()
        self.expected_pnl_values = self.calc_expected_pnl_values()
        self.expected_profit = self.calc_expected_profit()



    def __repr__(self):
        return model_repr(self)


    def repr(self) -> OptionPnLRepr:
        """Model of key OptionPnL Stat Components"""
        return OptionPnLRepr(**(dict(self)))


    def calc_time_scale(self, at_expire: bool = False) -> float:
        """Calculate time scale for volatility scaling DTE days_to_expiration"""
        if self.payoff or at_expire:
            dte = self.optionstrategy.days_to_expiration
        else:
            dte = max(self.optionstrategy.days_to_expiration - self.days_to_expiration, 0.5)
        return np.sqrt(dte / self.optionstrategy.year_days)
    

    def calc_stddev(self, at_expire: bool = False) -> float:
        """Calculate std deviation  ( expected Move )"""
        return self.optionstrategy.underlying_price * self.optionstrategy.volatility() * self.calc_time_scale(at_expire)


    def calc_price_range(self, at_expire: bool = False) -> np.ndarray:
        """Calculates the range of price for simulation based on volatility and standard deviations.
            Returns:
                np.ndarray: An array of simulated prices within stddev range
        """
        stddev = self.calc_stddev(at_expire) if at_expire else self.stddev
        # our price range simulation is +/- stddev_range deviations from underlying
        return np.linspace(
                self.optionstrategy.underlying_price - self.optionstrategy.stddev_range * stddev,
                self.optionstrategy.underlying_price + self.optionstrategy.stddev_range * stddev,
                self.optionstrategy.num_simulations)


    def calc_pop(self) -> float:
        """Calculates the Probability of Profit (POP) for the option strategy.

        This function estimates the likelihood of the strategy being profitable
        at the specified DTE, based on the provided or pre-calculated P&L values,
        price range, and standard deviation.

        Returns:
            float: The probability of the strategy being profitable,
            expressed as a value between 0 and 1.
        """
        # pdf is our probability distribution
        pdf = norm.pdf(
            self.price_range,
            loc=self.optionstrategy.underlying_price,
            scale=self.stddev)
        # Find the probability of profit based on the PnL results being above zero
        profitable_pnl = self.pnl_values > 0  # sets [T,F,TT, etc
        # prob of profit is
        # sum pdf where price points are profitable / all pdf points
        return np.sum(pdf[profitable_pnl]) / np.sum(pdf)


    def calc_expected_pnl_values(self) -> np.ndarray:
        """Simulates P&L results across a price range.
        Weights PnL of eache price point by probability
        of the price result
        """
        # we use the diff between cdf points for histogramic volume of probability
        cdf_diff = np.diff(
            norm.cdf(
                self.price_range,
                loc=self.optionstrategy.underlying_price,
                scale=self.stddev),
            prepend=0)

        # prepending 0 for diff has goofy result in leftmost, reset to repeat of [1]
        cdf_diff[0] = cdf_diff[1]
        # multiply PnL points by probability of their results
        return self.pnl_values * cdf_diff


    def calc_expected_profit(self) -> float:
        """Average PnL result weighted by probability"""
        # monte_carlo defined boolean om optionstrategy.__init__()
        if self.optionstrategy.monte_carlo:
            return self.monte_carlo_future_result()
        else:
            return np.sum(self.expected_pnl_values)


    def calc_pnl_values(self, at_expire: bool = False) -> np.ndarray:
        """
        find the sum PnL for all opton legs for a given DTE
        This uses black scholes
        """
        price_range = self.calc_price_range(at_expire) if at_expire else self.price_range
        pnl_values = np.zeros(len(price_range))
        for i, at_price in enumerate(price_range):
            pnl_values[i] = self.future_strategy_value(at_price)

        return pnl_values


    def future_strategy_value(self, at_price: float) -> float:
        """Calculate the strategy value at some point in the future.
           Given a possible at_price, DTE will determine the option leg prices if not
           in expiration payoff mode
        """
        # we use the users given price for expire payoff , not bscholes
        if self.payoff:
            return sum(leg.calc_payoff(at_price) for leg in self.optionstrategy.legs)
        qty:float = 0
        future_strategy_value = 0
        for leg in self.optionstrategy.legs:
            if leg.option_type != 'S':
                future_price, _, _, _, _ = black_scholes(
                    underlying_price=at_price,
                    strike_price=leg.strike_price,
                    time_days=self.days_to_expiration,
                    r=self.optionstrategy.r,
                    volatility=leg.volatility,
                    option_type=leg.option_type
                )
                qty = leg.quantity
            else:
                future_price = at_price
                qty = leg.quantity / 100  # stock is of 100 units
            # For long positions, subtract the initial cost from the future value.
            # For short positions, subtract the future value from the initial premium received
            if leg.quantity > 0:
                future_strategy_value +=  (future_price - leg.mark) * qty
            else:
                future_strategy_value +=  (leg.mark - future_price) * abs(qty)
        return future_strategy_value


    def monte_carlo_future_result(self) -> float:
        """
          Calculates expected profit using monte carlo simulation.
          Using a random normal distribution of possible outcomes.
          we return the average result
        """
        # this return has variance without large cycle size
        random_prices = np.random.normal(
            loc=self.optionstrategy.underlying_price,
            scale=self.stddev,
            size=self.optionstrategy.num_simulations)

        pnl_values = np.array(
            [self.future_strategy_value(price)
                for price in random_prices])
        # average our results for expected_profit
        return pnl_values.mean()


    def monte_carlo_future_result_ai(self) -> float:
        """
          Calculates expected profit using monte carlo simulation.
          Using a random normal distribution of possible outcomes.
          we return the average result
        """
        num_simulations = self.optionstrategy.num_simulations # use base sim size
        convergence_tolerance: float = 0.01
        max_monte_carlo_simulations: int = 10000 # avoid infinite loops with high variance

        pnl_values = []

        while True: # loop until convergence
            random_prices = np.random.normal(
                loc=self.optionstrategy.underlying_price,
                scale=self.stddev,
                size=num_simulations)

            pnl_values.extend([self.future_strategy_value(price) for price in random_prices])

            if len(pnl_values) > 1:
                current_mean = np.mean(pnl_values)
                sem = np.std(pnl_values, ddof=1) / np.sqrt(len(pnl_values))

                if sem < convergence_tolerance:
                    return current_mean

            if len(pnl_values) > max_monte_carlo_simulations:
                return np.mean(pnl_values)
            #increment simulation size
            num_simulations =  min(num_simulations * 2 , max_monte_carlo_simulations - len(pnl_values)) if (
                num_simulations < max_monte_carlo_simulations - len(pnl_values)
                ) else 1
