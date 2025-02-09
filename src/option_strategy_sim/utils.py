# --------------
#             __         __  _ __  
#  ___  ___  / /_  __ __/ /_(_) /__
# / _ \/ _ \/ __/ / // / __/ / (_-<
# \___/ .__/\__/  \_,_/\__/_/_/___/
#    /_/                           
#
""""Misc functions in need of a home""" 

import numpy as np
from scipy.stats import norm
import json 

def class_args(data:dict, fields: list) -> dict:
    # return slice of dict that matches fieldlist 
    return {key: data.pop(key) for key in fields if key in data}

def model_repr(obj: object) -> str:
    # for __repr__ with object.repr method
    return str(type(obj)) + json.dumps(dict(obj.repr()))


def calculate_ema(prices: np.ndarray, window: int) -> np.ndarray:
    """
    Calculates the Exponential Moving Average (EMA) of a given price series.

    Args:
        prices (np.ndarray): A 1-dimensional numpy array of prices.
        window (int): The time period or window size to use for calculating the EMA.
                      A larger window will result in a smoother EMA.

    Returns:
        np.ndarray: A 1-dimensional numpy array containing the EMA values for each price point.

    Example:
        prices = np.array([10, 12, 13, 14, 15])
        window = 3
        ema = calculate_ema(prices, window) # ema will be approx [10, 11, 12.25, 13.18, 14.09]

    """
    ema = np.zeros(len(prices))
    alpha = 2 / (window + 1)
    ema[0] = prices[0]
    for t in range(1, len(prices)):
        ema[t] = alpha * prices[t] + (1 - alpha) * ema[t - 1]
    return ema

