# --------------
#                     __      
#   ___ ________ ___ / /__ ___
#  / _ `/ __/ -_) -_)  '_/(_-<
#  \_, /_/  \__/\__/_/\_\/___/
# /___/                       
#


import numpy as np
from scipy.stats import norm
from pydantic import BaseModel, field_validator, model_validator


# days in the year for stddev calc, some ppl like 255 or 251 trade days instead of 365
YEAR_DAYS = 365
# our risk free rate
R = 0.05

def expected_move(underlying_price:float, volatility: float, days_to_expiration: float) -> float:
    """Calculate expected move of underlying for given volatility and duration"""
    if days_to_expiration > 0:
        return underlying_price * volatility * np.sqrt(days_to_expiration / 365)
    return 0


def black_scholes(
    underlying_price: float,
    strike_price: float,
    time_days: int,
    option_type: str,
    volatility: float,
    r: float = R,
    theta_days: int = 1,
) -> tuple[float, float, float, float, float]:
    """
    Calculates the price, delta, and theta of a European option using the Black-Scholes model.

    Args:
        S (float): The current price of the underlying asset.
        K (float): The strike price of the option.
        T (float): The time to expiration of the option, expressed in years (e.g., 0.5 for 6 months).
        r (float, optional): The risk-free interest rate. Defaults to 0.05 (5%).
        sigma (float): The volatility of the underlying asset. Must be provided.
        option_type (str, optional): The type of option, 'C' for call or 'P' for put.
        theta_days (float, optional): Time period in years (e.g., 1/365) to calculate theta decay
    Returns:
        tuple[float, float, float]: A tuple containing:
            - mark (float): The calculated Black-Scholes option price.
            - delta (float): The option's delta.
            - theta (float): The option's theta (time decay) over the given period in `theta_days`, or None if theta_days is not provided.
    Notes:
        - If time to expiration (T) is zero or negative, the function returns the intrinsic value of the option and a delta of 0.
        - Theta is calculated as the difference in option price between the current time and a time `theta_days` in the future.
    """
    if underlying_price is None:
        raise ValueError("underlying_price is required")
    if strike_price is None:
        raise ValueError("strike_price is required")
    if time_days is None:
        raise ValueError("time_days is required")
    if option_type is None:
        raise ValueError("option_type is required")
    if volatility is None:
        raise ValueError("volatility is required")

    T: float = time_days / YEAR_DAYS
    T_next: float = (time_days - 1) / YEAR_DAYS
    thetadiff: float = theta_days / YEAR_DAYS

    if T <= 0:
        return (
            max(0, underlying_price - strike_price)
            if option_type == "C"
            else max(0, strike_price - underlying_price),
            0,
            None,
            0,
            0,
        )
    def bs_greeks(tyear:float, justmark: bool = False) -> tuple:
        sigma_T:float = volatility * np.sqrt(tyear)
        if sigma_T == 0:
            sigma_T = np.sqrt(0.1/365)
        d1 = (
            np.log(underlying_price / strike_price)
            + (r + 0.5 * volatility**2) * tyear
        ) / sigma_T
        d2 = d1 - sigma_T
        if option_type == "C":
            mark = (
                underlying_price * norm.cdf(d1) - strike_price * np.exp(-r * T) * norm.cdf(d2)
            )
            delta = norm.cdf(d1)  # Correct delta for a call option
        elif option_type == "P":
            mark = (
                strike_price * np.exp(-r * T) * norm.cdf(-d2)
                - underlying_price * norm.cdf(-d1)
            )
            delta = norm.cdf(d1) - 1  # Correct delta for a put option
        else:
            raise ValueError("Invalid option type. Use 'C' or 'P'.")
        if justmark:
            return mark
        vega: float = underlying_price * norm.pdf(d1) * np.sqrt(T)
        gamma: float = norm.pdf(d1) / (underlying_price * volatility * np.sqrt(T))
        return mark, delta, vega, gamma
    
    thetadiff:float  = time_days / YEAR_DAYS
    mark, delta, vega, gamma = bs_greeks(thetadiff)    
    next_mark = bs_greeks((time_days - 1) / YEAR_DAYS, justmark=True)
    theta = (next_mark - mark) / thetadiff
    return mark, delta, theta, vega, gamma

def black_scholes_vega(
    underlying_price: float,
    strike_price: float,
    time_days: int,
    volatility: float,
    r: float = R,
) -> float:
    """Calculates the Vega of a European option."""
    T = time_days / YEAR_DAYS
    sigma_T = volatility * np.sqrt(T)
    if T <= 0:
        return 0
    d1 = (
        np.log(underlying_price / strike_price)
        + (r + 0.5 * volatility**2) * T
    ) / sigma_T
    return underlying_price * norm.pdf(d1) * np.sqrt(T)

def black_scholes_gamma(underlying_price: float, strike_price: float, time_days: float,  volatility: float, r: float = R):
    """
    Calculates the Gamma of a European option using the Black-Scholes formula.

    Args:
        S (float): Current price of the underlying asset.
        K (float): Strike price of the option.
        T (float): Time to expiration in years.
        r (float): Risk-free interest rate.
        sigma (float): Volatility of the underlying asset.

    Returns:
        float: Gamma of the option.
    """
    T: float = time_days / YEAR_DAYS
    d1: float = (np.log(underlying_price / strike_price) + (r + 0.5 * volatility ** 2) * T) / (volatility * np.sqrt(T))
    return norm.pdf(d1) / (underlying_price * volatility * np.sqrt(T))

def implied_volatility_newton_raphson(
    underlying_price: float,
    strike_price: float,
    time_days: int,
    mark: float,
    option_type: str,
    r: float = R,
    initial_volatility: float = 0.2,
    tolerance: float = 1e-6,
    max_iterations: int = 100,
) -> tuple[float, float, float, float, float] | None:
    """Calculates implied volatility using Newton-Raphson method.
    returns volatility, delta , theta, vega
    """
    volatility = initial_volatility
    for _ in range(max_iterations):
        calculated_price, delta, theta, vega, gamma = black_scholes(
            underlying_price=underlying_price,
            strike_price=strike_price,
            time_days=time_days,
            r=r,
            volatility=volatility,
            option_type=option_type,
        )
        price_diff = calculated_price - mark
        if vega == 0:
            return None
        if abs(price_diff) < tolerance:
            return volatility, delta, theta, vega, gamma
        volatility = volatility - price_diff / vega
        if volatility < 0:
            return None  # volatility should never be negative.

    return None  # Did not converge

def calculate_price_probability(
    underlying_price: float,
    strike_price: float,
    time_days: int,
    volatility: float,
    r: float = R,
) -> float:
    """
    Calculates the probability of a stock price reaching or exceeding a target price within a given time frame,
    based on the Black-Scholes model.
    Args:
        current_price (float): The current price of the underlying asset.
        target_price (float): The target price to reach or exceed.
        time_days (int): The time frame in days within which the target price needs to be reached.
        volatility (float): The volatility of the underlying asset (annualized).
        interest_rate (float): The risk-free interest rate (annualized).
    Returns:
        float: The probability (between 0 and 1) of the stock price reaching or exceeding the target price within the given time.
    """
    time_years = time_days / YEAR_DAYS
    sigma_T = volatility * np.sqrt(time_years)
    r_T = r * time_years
    d2 = (np.log(underlying_price / strike_price) + (r_T - 0.5 * sigma_T**2)) / sigma_T
    probability = norm.cdf(d2)
    return probability




class Greeks(BaseModel):
    """A data class of option Greeks computation"""
    underlying_price: float
    strike_price: float
    option_type: str
    days_to_expiration: float
    # optional \/
    mark: float | None = None
    volatility: float | None = None
    delta: float | None = None
    theta: float | None = None
    vega: float | None = None
    gamma: float | None = None
    quantity: int | None = None # only used for stocks
    r: float = R
    year_days: int = YEAR_DAYS
    
    @field_validator('option_type')
    def validate_option_type(cls, value):
        if value not in ['C', 'P', 'S']:
            raise ValueError('option_type must be "C" or "P" or "S"')
        return value
    @field_validator('strike_price')
    def validate_strike_price(cls, value):
        if value <= 0:
            raise ValueError('strike_price must > 0')
        return value
    @field_validator('underlying_price')
    def validate_underlying_price(cls, value):
        if value <= 0:
            raise ValueError('underlying_price must > 0')
        return value

    @model_validator(mode="after")
    def validate_mark_or_volatility(self):
        if self.volatility is None and self.mark is None:
            raise ValueError("Either 'mark' or 'volatility' must be provided.")
        return self


    def calc_greeks(self) -> object:
        """Add missing greeks to option contract data 
        This will not override existing given values
        """
        if self.option_type == 'S':
            return self.calc_stock_greeks()
        
        # build volatility 
        if self.volatility is None:
            vol, delta, theta, vega, gamma = implied_volatility_newton_raphson(
                underlying_price=self.underlying_price,
                strike_price=self.strike_price, 
                time_days=self.days_to_expiration, 
                mark=self.mark,
                option_type=self.option_type, 
                r=self.r)
            self.volatility = vol
            self.delta = self.delta or delta
            self.theta = self.theta or theta
            self.vega = self.vega or vega 
            self.gamma = self.gamma or gamma 
        else: 
            price, delta, theta, vega, gamma = black_scholes(
                underlying_price=self.underlying_price,
                strike_price=self.strike_price, 
                time_days=self.days_to_expiration, 
                option_type=self.option_type, 
                volatility=self.volatility, 
                r=self.r,
                theta_days=1)
            self.mark = self.mark or price 
            self.delta = self.delta or delta
            self.theta = self.theta and abs(self.theta) or theta
            self.vega = self.vega or vega 
            self.gamma = self.gamma or gamma 
        return self

    def calc_stock_greeks(self) -> object:
        self.delta = self.quantity / 100
        self.gamma = 0
        self.theta = 0
        self.vega = 0
        return self

    def __repr__(self) -> str:
        """Returns a string representation of object."""
        retstr:str =  (
            f"{self.__class__.__name__}("
            f"underlying_price='{self.underlying_price:.2f}', "
            f"option_type='{self.option_type}', "
            f"strike_price={self.strike_price:.2f}, "
        )
        retstr += f"volatility={self.volatility:.3f}, " if self.volatility else "volatility=None, "
        retstr += f"mark={self.mark:.2f}, " if self.mark else "mark=None, "
        retstr += f"delta={self.delta:.3f}, " if self.delta else "delta=None, "
        retstr += f"theta={self.theta:.3f}, " if self.theta else "theta=None, "
        retstr += f"vega={self.vega:.3f})" if self.vega else "vega=None)"
        return retstr


