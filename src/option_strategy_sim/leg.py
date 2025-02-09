# --------------
#             __    __
#  ___  ___  / /_  / /__ ___ _
# / _ \/ _ \/ __/ / / -_) _ `/
# \___/ .__/\__/ /_/\__/\_, /
#    /_/               /___/
#

import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt

from pydantic import BaseModel, field_validator, ValidationError # type: ignore
from .greeks import Greeks
from .utils import class_args, model_repr
from datetime import date

class OptionLegRepr(BaseModel, extra='allow'):
    """ 
    Representation of OptionLeg
    """
    option_type: str
    strike_price: float
    quantity: int
    days_to_expiration: float 
    volatility: float | None = None
    mark: float | None = None
    delta: float | None = None
    vega: float = None
    theta: float = None
    gamma: float = None
    symbol: str | None = None
    expirey: date | None = None


    def __init__(self, **kwargs):
        # Initialize with known fields only
        super().__init__(**class_args(kwargs, self.model_fields))


class OptionLeg(BaseModel, arbitrary_types_allowed=True):
    """Represents a single option leg (call or put).
        Args:
        option_type (str): 'C' for call or 'P' for put.
        strike_price (float): The strike price of the option.
        quantity (int): The number of contracts.
        volatility (float):  implied vol
        mark (float): The mark paid/received per contract; avg bid|ask
        delta (float): optional contract delta
        vega (float): optional contract vega
        optionstrategy (OptionStrategy): parent strategy object
        theta (float): amount of theta decay for theta_days (1)
    """
    option_type: str
    strike_price: float
    quantity: int
    days_to_expiration: float = None
    optionstrategy: 'OptionStrategy'
    # optional
    volatility: float | None = None
    mark: float | None = None
    delta: float | None = None
    vega: float = None
    theta: float = None
    gamma: float = None
    # metadata without calculation involvement
    symbol: str = None
    expirey: date | None = None

    @field_validator('quantity')
    def validate_quantity(cls, value):
        if value == 0:
            raise ValidationError('quantity must <> 0')
        return value

    def __init__(self, **data):
        super().__init__(**data)
        # REQUIRED : option_type strike_price quantity 
        # REQUIRED in strategy: underlying price days_to_expiration  
        if self.days_to_expiration is None:
            self.days_to_expiration = self.optionstrategy.days_to_expiration
            if self.days_to_expiration is None:
                if self.option_type == 'S':
                    self.days_to_expiration = 1
                else:
                    raise ValueError("days_to_expiration is required")
        if self.days_to_expiration < 0:
            raise ValueError("Days to expiration must be a non-negative float.")
        
        if self.mark is None and self.volatility is None:
            self.volatility = self.optionstrategy.volatility()

        greeks = Greeks(        
            underlying_price=self.optionstrategy.underlying_price,
            strike_price=self.strike_price,
            option_type=self.option_type,
            days_to_expiration=self.days_to_expiration,
            mark=self.mark,
            volatility=self.volatility,
            delta=self.delta,
            theta=self.theta,
            vega=self.vega,
            r=self.optionstrategy.r,
            quantity=self.quantity
            ).calc_greeks()
        
        self.volatility = self.volatility or greeks.volatility
        self.delta = self.delta or greeks.delta
        self.mark = self.mark or greeks.mark
        self.gamma = self.gamma or greeks.gamma
        if self.quantity < 0:
            self.theta = self.theta or -greeks.theta 
            self.vega = self.vega or -greeks.vega
        else:
            self.theta = self.theta or greeks.theta
            self.vega = self.vega or greeks.vega

    def __repr__(self):
        return model_repr(self)

    def repr(self) -> OptionLegRepr:
        """Model of key OptionLeg Stat Components"""
        return OptionLegRepr(**(dict(self)))

    def calc_payoff(self, underlying_price: float) -> float:
        """Calculates the payoff of the option leg at a given underlying price.

        Args:
             underlying_price (float): The price of the underlying asset at expiration.

        Returns:
            float:  The payoff of the leg.
        """
        if self.option_type == 'C':
            return (max(0, underlying_price - self.strike_price) * self.quantity) - (self.mark * self.quantity)
        elif self.option_type == 'P':
            return (max(0, self.strike_price - underlying_price) * self.quantity) - (self.mark * self.quantity)
        elif self.option_type == 'S':
            # stock is of 100 units 
            return (underlying_price -  self.strike_price) * self.quantity/100

