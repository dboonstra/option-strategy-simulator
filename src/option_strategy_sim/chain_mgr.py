import json
import numpy as np
import pandas as pd
from pydantic import BaseModel, field_validator
from datetime import date
from typing import Optional

"""
There are 3 classes here:

1) OptionChains(csv=cvsfile | chains=pd.DataFrame)
    Holds option chain quotes for the market 

    Methods:
        underlying_symbols()
            Returns list of unique underlying symbols 
        purge(open_interest_threshold=10, delta_min=0.03, delta_max=0.97, price_min=10) -> None:
            Filters out uninteresting option chains based on open interest, delta, and underlying price.
        get_symbol_chain(underlying_symbol)
            Returns OptionChainsSym object for given symbol
        
2) OptionChainsSym
    Holds the option chains for a given underlying symbol

    Methods:
        expire_days()
            Returns the unique days to expiration values in the option chains
        expiration_date()
            Returns the unique expiration dates in the option chains
        underlying_price()
            Retrieves the underlying price from the option chains
        get_dte_chain(days_to_expiration: int, exact: bool = False):
            If exact, then returns precise DTE, otherwise finds closest result
            Returns OptionChainsSymDTE object for a given days to expiration
        get_expiration_date_chain(expiration_date: str|date)
            Match the data type to the initial input (df or csv)
            Returns OptionChainsSymDTE object for a given expiration date

3) OptionChainsSymDTE
    Holds the option chains for a given DTE for an underlying symbol
    
    Attribute Methods:
        underlying_price():
            Retrieves the underlying price from the chain
        underlying_symbol():
            Retrieves the underlying symbol from the chain
        underlying_price()
            Retrieves the underlying price from the chain
        days_to_expiration()
            Retrieves the unique strike prices from the call options
        strikes()
            Retrieves the unique strike prices
        calc_iv()
            Calculates the average implied volatility for strikes near the underlying price
        calc_volume_ratio()
            Calculates total volume based Put/Call or -Call/Put ratio for the contracts.
            returns -1 ... 1 where 0 is equal volume b/n puts and calls
            A negative number is put skewed , a positive number is call skewed
        calc_volatility_ratio()
            Calculates total volatility based Put/Call or -Call/Put ratio for the contracts.
            returns -1 ... 1 where 0 is equal volatility b/n puts and calls
            A negative number is put skewed , a positive number is call skewed

    Leg management methods
        clear_legs()
            Removes all contract legs from the object leg dataframe
        contract(quantity, option_type, symbol= | delta= , clear=False)
            Add a contract to dataframe legs by delta or symbol 
            Returns all legs dataframe
        iron_condor(quantity, delta, otm_delta, width, strike_percent, clear=False)
            Returns legs of an iron condor
            Either delta or strike_percent determins the inner legs 
            Either otm_delta or width determine the outer legs
        straddle(quantity, strike_percent, strike, clear=False)
            Returns legs of a straddle centered by strike or strike_percent 
        strangle(quantity, delta, strike_percent, clear=False)
            Returns legs of a strangle centered by delta or strike_percent
        spread(quantity, option_type, delta, otm_delta, width, strike_percent, clear=False)
            Returns legs of a spread 
            Either delta or strike_percent determins the inner leg
            Either otm_delta or width determine the outer leg
    
    If in repo, look at dev/chain_mgr.ipynb for some example use.
    Column names are based on TastyTrade format.
    Perhaps a dictionary module may assist portability between brokerages
"""

def dumps(data):
    """
    Converts data to a JSON formatted string with indentation.
    """
    return json.dumps(data, indent=4)


def get_first_value(df: pd.DataFrame, column_name: str):
    """
    Retrieves the first value from a specified column in a DataFrame.
    Args:
        df (pd.DataFrame): The input DataFrame.
        column_name (str): The name of the column to extract the value from.
    Returns:
        The first value in the specified column.
    """
    return df[column_name].iloc[0]


def filter_by_closest_value(
    df: pd.DataFrame,
    column_name: str,
    target_value: float,
    direction: str = "absolute",
    exact: bool = False,
    ) -> pd.DataFrame:
    """
    Filters a DataFrame to find rows where a column's value is closest to a target value.

    Args:
        df (pd.DataFrame): The input DataFrame.
        column_name (str): The name of the column to compare against.
        target_value (float): The target value to find the closest match to.
        direction (str): Specifies the direction for finding the closest value.
            Options: 'absolute', 'less_than', 'greater_than'.  Defaults to 'absolute'.

    Returns:
        pd.DataFrame: A DataFrame containing the row(s) with the closest value.
                      Returns an empty DataFrame if the input DataFrame is empty
                      or if no suitable values are found based on the specified direction.

    Raises:
        ValueError: If the `direction` argument is not one of the valid options.
    """
    if df.empty:
        return pd.DataFrame()

    if direction == "absolute":
        # Calculate absolute difference from the target value
        difference = (df[column_name] - target_value).abs()
    elif direction == "less_than":
        # Filter values less than or equal to the target value
        filtered_df = df.loc[df[column_name] <= target_value]
        if filtered_df.empty:
            return pd.DataFrame()
        # Calculate absolute difference from the target value
        difference = (target_value - filtered_df[column_name]).abs()
        df = filtered_df  # Update df to the filtered DataFrame
    elif direction == "greater_than":
        # Filter values greater than or equal to the target value
        filtered_df = df.loc[df[column_name] >= target_value]
        if filtered_df.empty:
            return pd.DataFrame()
        # Calculate absolute difference from the target value
        difference = (filtered_df[column_name] - target_value).abs()
        df = filtered_df  # Update df to the filtered DataFrame
    else:
        raise ValueError(
            "Invalid direction. Must be 'absolute', 'less_than', or 'greater_than'."
        )

    # Get the closest value based on the calculated differences
    closest_value = df[column_name].iloc[difference.argsort()].iloc[0]
    if exact and closest_value != target_value:
        return pd.DataFrame()
    # Return a DataFrame containing rows that match the closest value
    return df[df[column_name] == closest_value].copy()


def filter_by_value(df: pd.DataFrame, column_name: str, value=None):
    """
    Filters a DataFrame to return rows where a specified column equals a given value.

    Args:
        df (pd.DataFrame): The input DataFrame.
        column_name (str): The name of the column to filter by.
        value: The value to filter the column for.
               If None, the original DataFrame is returned (NoOp).

    Returns:
        pd.DataFrame: A filtered DataFrame where the specified column equals the given value.
                      Returns an empty DataFrame if no matches are found.
                      Returns a copy of the original DataFrame if value is None.

    Raises:
        TypeError: If the input is not a pandas DataFrame.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")
    if df.empty:
        return pd.DataFrame({})
    # If value is None, return the original DataFrame
    if value is None:
        return df.copy()
    # Filter the DataFrame and return a copy
    return df.loc[df[column_name] == value].copy()


def filter_option_chains(
    chains: pd.DataFrame,
    symbol: str = None,
    days_to_expiration: int = None,
    option_type: str = None,
    exact: bool = False,
    expiration_date: str = None,
    strike_price: float = None,
):
    """
    Filters option chain data based on specified criteria.

    Args:
        chains (pd.DataFrame): The input DataFrame containing option chain data.
        symbol (str, optional): The underlying symbol to filter by (e.g., 'AAPL', 'SPY'). Defaults to None.
        days_to_expiration (int, optional): The number of days to expiration to filter by.
                                            Defaults to None. use exact match with filter_days2exp function.
        option_type (str, optional): The option type to filter by ('C' or 'P'). Defaults to None.
        exact (bool, optional): Match by exact number of days to experation. Defaults to False.
        expiration_date (str, optional): The expiration date to filter by in 'YYYY-MM-DD' or 'YYYYMMDD' format. Defaults to None.
        strike_price (float, optional): The strike price to filter by. Defaults to None.

    Returns:
        pd.DataFrame: A filtered DataFrame with the specified criteria applied.
    """
    filtered_df = chains.copy()
    if symbol is not None:
        filtered_df = filter_by_value(
            filtered_df, "underlying_symbol", value=symbol
        )
    if expiration_date is not None:
        filtered_df = filter_by_value(
            filtered_df, "expiration_date", value=expiration_date
        )
    if option_type is not None:
        filtered_df = filter_by_value(filtered_df, "option_type", value=option_type)
    if strike_price is not None:
        filtered_df = filter_by_closest_value(
            filtered_df, "strike_price", value=strike_price, exact=exact
        )
    if days_to_expiration is not None:
        filtered_df = filter_by_closest_value(
            filtered_df, 'days_to_expiration' , days_to_expiration, exact=exact
        )

    return filtered_df


def get_chains_from_csv(csv_file_path, prune_spx: bool = True) -> pd.DataFrame:
    """
    Loads option chain data from a CSV file.

    Args:
        csv_file_path (str): The path to the CSV file.
        prune_spx (bool, optional): Whether to remove SPX duplicates. Defaults to True.
                                    Keeps SPXW over SPX contracts, and SQQQ over SQQQ1 contracts.

    Returns:
        pd.DataFrame: A DataFrame containing the option chain data.
    """
    chains = pd.read_csv(csv_file_path)
    # prune extra header insertions
    chains = chains.loc[chains["underlying_symbol"] != "underlying_symbol"].copy()
    return chains


def prepare_chains(chains: pd.DataFrame, prune_spx: bool = True) -> pd.DataFrame:
    """
    Prepares the option chain DataFrame by:
    - Pruning SPX duplicates (optional).
    - Ensuring correct data types for columns.
    - Resetting the 'time' column from milliseconds to seconds.
    - Setting derived columns: 'strike_percent' and 'quote_date'.

    Args:
        chains (pd.DataFrame): The input option chain DataFrame.
        prune_spx (bool, optional): Whether to remove SPX duplicates. Defaults to True.

    Returns:
        pd.DataFrame: The prepared option chain DataFrame.
    """
    if prune_spx:
        # remove SPX options... just keep SPXW in there to prune dupes
        # remove SQQQ1 options.... keep the SQQQ
        # remove UVXY2 options keep the SQQQ
        chains = chains[~chains.symbol.str.startswith("SPX ")].copy()
        chains = chains[~chains.symbol.str.startswith("SQQQ1 ")].copy()
        chains = chains[~chains.symbol.str.startswith("UVXY2 ")].copy()

    # Define column data types
    float_fields = [
        "underlying_price",
        "strike_price",
        "strike_percent",
        "bid_price",
        "ask_price",
        "mark",
        "rho",
        "vega",
        "theta",
        "delta",
        "gamma",
        "volatility",
    ]
    int_fields = [
        "time",
        "bid_size",
        "ask_size",
        "open_interest",
        "prev_day_volume",
    ]  # volume ?
    str_fields = ["underlying_symbol", "option_type"]
    date_fields = ["quote_date", "expiration_date"]

    # Calculate strike percent as distance from strike to current price
    chains.loc[:, "strike_percent"] = (
        chains["strike_price"] - chains["underlying_price"]
    ) / chains["underlying_price"]
    # Switch time from ms to sec
    chains["time"] = (chains["time"].copy() / 1000).astype(np.int64)
    # Add quote_day field
    chains["quote_date"] = pd.to_datetime(chains["time"], unit="s").dt.date

    # Set datatypes ( .. or we could use a pydantic model ? )
    for field in float_fields:
        chains[field] = chains[field].astype(float)
    for field in int_fields:
        chains[field] = chains[field].astype(int)
    for field in str_fields:
        chains[field] = chains[field].astype(str)
    for field in date_fields:
        chains[field] = chains[field].astype(str)
    return chains


class OptionChainsSymDTE(BaseModel, arbitrary_types_allowed=True):
    parent: 'Optional[OptionChainsSym]'
    chain: pd.DataFrame

    calls: pd.DataFrame = None
    puts: pd.DataFrame = None

    legs: pd.DataFrame = pd.DataFrame()

    def model_post_init(self, context):
        """
        Post-initialization to filter calls and puts from the chain.
        """
        self.puts = filter_option_chains(self.chain, option_type="P")
        self.calls = filter_option_chains(self.chain, option_type="C")
        return super().model_post_init(context)

    def repr(self):
        """
        Returns a JSON representation of the first row in the chain.
        """
        return dumps(self.chain.iloc[0].to_dict())

    def underlying_price(self) -> float:
        """
        Retrieves the underlying price from the chain.

        Returns:
            float: The underlying price.
        """
        return get_first_value(self.chain, "underlying_price")

    def underlying_symbol(self) -> str:
        """
        Retrieves the underlying symbol from the chain.

        Returns:
            str: The underlying symbol.
        """
        return get_first_value(self.chain, "underlying_symbol")

    def days_to_expiration(self) -> int:
        """
        Retrieves the days to expiration from the chain.

        Returns:
            int: The days to expiration.
        """
        return get_first_value(self.chain, "days_to_expiration")

    def strikes(self) -> list[ str ]:
        """
        Retrieves the unique strike prices from the call options.

        Returns:
            numpy.ndarray: An array of unique strike prices.
        """
        return self.calls["strike_price"].unique()

    def calc_iv(self):
        """
        Calculates the average implied volatility for strikes near the underlying price.

        Returns:
            float: The average implied volatility.

        Raises:
            ValueError: If 'volatility' is not found in the option chain fields.
        """
        if 'volatility' not in self.calls:
            raise ValueError ("volatility not found in option chain fields")
            # TODO , compute iv from bid/ask ?
        # average volatility for strikes within 12% of underlying
        df = self.chain[abs(self.chain['strike_percent']) < 0.12]
        # return df[['volatility']].sum()/len(df)
        if len(df) == 0:
            return 0
        return float(df['volatility'].sum()/len(df))
    
    def calc_volume_ratio(self) -> float:
        """
        Calculates total volume based Put/Call ratio for the contracts.
        returns -1 ... 1 where 0 is equal volume b/n puts and calls
        A negative number is put skewed , a positive number is call skewed
        """
        key: str = None
        if 'prev_day_volume' in self.calls:
            key = 'prev_day_volume'
        elif 'volume' in self.calls:
            key = 'volume'
        elif 'open_interest' in self.calls:
            key = 'open_interest'
        if key is None:
            return 1 
        tput = self.puts[key].sum()
        tcall = self.calls[key].sum()
        if tcall == 0:
            return 1
        if tput < tcall:
            return float(1 - tput / tcall)
        else:
            return float(-1 * ( 1 - tcall/tput))
    
    def calc_volatility_ratio(self) -> float:
        """put|call vol Skew for the DTE
        
        returns -1 ... 1 where 0 is equal volatility b/n puts and calls
        A negative number is put skewed , a positive number is call skewed

        """

        p = self.puts[self.puts['delta'] > -0.4].loc[self.puts['delta'] < -0.1]
        c = self.calls[self.calls['delta'] < 0.4].loc[self.calls['delta'] > 0.1].copy()
        if len(p) == 0 or len(c) == 0:
            return 0
        pv = p['volatility'].sum()/len(p)
        cv = c['volatility'].sum()/len(c)
        if pv < cv:
            return float(1 - pv/cv)
        else:
            return float(-1 * ( 1 - cv/pv))

    def _contract(
            self,
            option_type: str = None,
            symbol: str = None,
            key: str = None,
            val: float = None,
            direction: str = 'absolute' 
        ):
        """Find matching contract in our chain
        `direction` argument is one of 'absolute', 'less_than', or 'greater_than'.
        """
        # TODO match on less than / greater than ?
        if option_type is None and symbol is None:
            raise ValueError("option_type or symbol required")
        if symbol is not None: # there can be only one
            ctct: pd.DataFrame = filter_by_value(self.chain,'symbol', value=symbol)
        else:
            df = self.calls if option_type == 'C' else self.puts
            ctct: pd.DataFrame = filter_by_closest_value(df, key, val, direction=direction) #iloc[0]
        return None if ctct.empty else ctct.head(1)

    def clear_legs(self) -> None:
        # concat DF contract legs to strategy
        self.legs = pd.DataFrame()

    def join_legs(self, *legs, clear: bool = False) -> pd.DataFrame:
        # concat DF contract legs to strategy
        if clear:
            self.clear_legs()
        if len(legs) > 0:
            self.legs = pd.concat([self.legs,*legs], axis=0, ignore_index=True)
        return self.legs
    
    def delta(self, option_type: str, delta: float) -> float:
        # ensure delta is appropo for option_type
        if option_type == 'C' and delta > 0:
            return delta 
        if option_type == 'P' and delta < 0:
            return delta 
        return -delta
    
    ### strategy constructions
    def contract(
            self,
            quantity: int,
            option_type: str = None,
            symbol: str = None,
            delta: float = None,
            clear: bool = False,
        ) -> pd.DataFrame:
        """
        Add a contract to dataframe legs by delta or symbol 
        Returns all legs dataframe
        """
        if symbol is not None:
            c = self._contract(option_type=option_type, symbol=symbol)
        elif delta is not None:
            if option_type is None:
                if delta > 0:
                    option_type = 'C'
                else:
                    option_type = 'P'
            delta = self.delta(option_type, delta)
            c = self._contract(option_type=option_type, key='delta', val=delta)
        else:
            raise ValueError("contract needs delta or symbol")
        c['quantity'] = quantity
        return self.join_legs(c, clear=clear)
    
    def iron_condor(
            self,
            quantity: int,
            delta: float = None,
            otm_delta: float = None,
            width: float = None,
            strike_percent:float = None, 
            clear: bool = False,
        ) -> pd.DataFrame:
        """
            Returns legs of an iron condor
            Either delta or strike_percent determins the inner legs 
            Either otm_delta or width determine the outer legs
        """
        if delta is None and strike_percent is None:
            raise ValueError("IC needs delta or short_delta or strike_percent")
        if otm_delta is None and width is None:
            raise ValueError("IC needs long_delta or width")
        # find inner contracts
        if strike_percent is not None:
            atm_c = self._contract(option_type='C', key='strike_percent', val=strike_percent)
            atm_p = self._contract(option_type='P', key='strike_percent', val=strike_percent)
        else:
            atm_c = self._contract(option_type='C', key ='delta', val=delta)
            atm_p = self._contract(option_type='P', key='delta', val=-delta)
        if atm_c is None or atm_p is None:
            return None
        # find outer contracts
        if width is not None:
            cstrike = get_first_value(atm_c, 'strike_price')
            pstrike = get_first_value(atm_p, 'strike_price')
            otm_c = self._contract(option_type='C', key ='strike_price', val=cstrike+width)
            otm_p = self._contract(option_type='P', key='strike_price', val=pstrike-width)
        else:
            otm_c = self._contract(option_type='C', key ='delta', val=otm_delta)
            otm_p = self._contract(option_type='P', key='delta', val=-otm_delta)
        if otm_c is None or otm_p is None:
            return None
        
        if atm_c.iloc[0]['strike_price'] == otm_c.iloc[0]['strike_price']:
            # these matched, go out one strike
            otm_c = self._step_out_contract(otm_c)
            if otm_c is None:
                return None
        if atm_p.iloc[0]['strike_price'] == otm_p.iloc[0]['strike_price']:
            # these matched, go out one strike
            otm_p = self._step_out_contract(otm_p)
            if otm_p is None:
                return None



        atm_c['quantity'] = quantity
        atm_p['quantity'] = quantity
        otm_c['quantity'] = -quantity
        otm_p['quantity'] = -quantity
        return self.join_legs(otm_c, atm_c, atm_p, otm_p, clear=clear)

    def straddle(
            self,
            quantity: int,
            strike_percent: float, 
            strike: float,
            clear: bool = False,
            ) -> pd.DataFrame:
        """ Returns legs of a straddle centered by strike or strike_percent """
        if strike_percent is not None:  # going for straddle 
            c = self._contract(option_type='C', key='strike_percent', val=strike_percent)
            p = self._contract(option_type='C', key='strike_percent', val=strike_percent)
        else:
            c = self._contract(option_type='C', key ='strike', val=strike)
            p = self._contract(option_type='P', key='strike', val=strike)
        c['quantity'] = quantity
        p['quantity'] = quantity
        return self.join_legs(c, p, clear=clear)

    def strangle(
            self,
            quantity: int,
            delta: float = None,
            strike_percent:float = None, 
            clear: bool = False,
            ) -> pd.DataFrame:
        """ Returns legs of a strangle centered by delta or strike_percent """
        if strike_percent is not None:  
            c = self._contract(option_type='C', key='strike_percent', val=strike_percent)
            p = self._contract(option='C', key='strike_percent', val=-strike_percent)
        else:
            c = self._contract(option_type='C', key ='delta', val=delta)
            p = self._contract(option_type='P', key='delta', val=-delta)
        c['quantity'] = quantity
        p['quantity'] = quantity
        return self.join_legs(c, p, clear=clear)
    
    def spread(
            self,
            quantity: int,
            option_type: str,
            delta: float = None,
            otm_delta: float = None,
            width: float = None,
            strike_percent:float = None,
            clear: bool = False, 
        ) -> pd.DataFrame:
        if delta is None and strike_percent is None:
            raise ValueError("IC needs delta or strike_percent")
        if otm_delta is None and width is None:
            raise ValueError("IC needs otm_delta or width")

        if strike_percent is not None:
            ct_a = self._contract(option_type=option_type, key='strike_percent', val=strike_percent)
        else:
            delta = self.delta(option_type, delta)
            ct_a = self._contract(option_type=option_type, key='delta', val=delta)
        if ct_a is None:
            return None
        if width is not None:
            strike = get_first_value(ct_a, 'strike_price')
            direction = -1 if option_type == 'C' else 1
            target_strike = strike + direction * width
            ct_b = self._contract(option_type=option_type, key='strike_price', val=target_strike)
        else:
            otm_delta = self.delta(option_type, otm_delta)
            ct_b = self._contract(option_type=option_type, key='delta', val=otm_delta)

        if ct_b is None:
            return None

        if ct_b.iloc[0]['strike_price'] == ct_a.iloc[0]['strike_price']:
            # these matched, go out one strike
            ct_b = self._step_out_contract(ct_b)
            if ct_b is None:
                return None

        ct_a['quantity'] = quantity 
        ct_b['quantity'] = -quantity
        return self.join_legs(ct_a, ct_b, clear=clear)


    def _step_out_contract(self,ct):
        # get next contract further OTM
        target_strike = ct.iloc[0]['strike_price']
        option_type = ct.iloc[0]['option_type']
        if option_type == 'P':
            direction = 'less_than'
            target_strike =  target_strike - 0.05
        else:
            direction = 'greater_than'
            target_strike =  target_strike + 0.05
        return self._contract(
            option_type=option_type, 
            key='strike_price', 
            val=target_strike, 
            direction=direction)


class OptionChainsSym(BaseModel, arbitrary_types_allowed=True):
    chains: pd.DataFrame
    # internal \/
    expiration_dates: dict = {}

    def __post_init__(self):
        """
        Post-initialization method.
        """
        pass

    def get_dte_chain(self, days_to_expiration: int, exact: bool = False) -> OptionChainsSymDTE:
        """
        Retrieves or creates an OptionChainsSymDTE object for a given days to expiration.

        Args:
            days_to_expiration (int): The number of days to expiration.
            key (str, optional): A custom key for caching. Defaults to None.
            exact (bool, optional): Whether to match days to expiration exactly. Defaults to False.

        Returns:
            OptionChainsSymDTE: An OptionChainsSymDTE object for the expiration date.
        """
        key = str(days_to_expiration) + "E" if exact else "~"
        if key not in self.expiration_dates:
            expiration_date_chain: pd.DataFrame = filter_option_chains(
                self.chains, days_to_expiration=days_to_expiration, exact=exact
            )
            if expiration_date_chain.empty:
                self.expiration_dates[key] = None
            else:
                self.expiration_dates[key] = OptionChainsSymDTE(
                    parent=self, chain=expiration_date_chain
                )
        return self.expiration_dates[key]

    def get_expiration_date_chain(self, expiration_date: str|date) -> OptionChainsSymDTE:
        """
        Retrieves or creates an OptionChainsSymDTE object for a given expiration date.

        Args:
            days_to_expiration (int): The number of days to expiration.
            key (str, optional): A custom key for caching. Defaults to None.
            exact (bool, optional): Whether to match days to expiration exactly. Defaults to False.

        Returns:
            OptionChainsSymDTE: An OptionChainsSymDTE object for the expiration date.
        """
        key = str(expiration_date) 
        if key not in self.expiration_dates:
            expiration_date_chain: pd.DataFrame = filter_by_value(
                self.chains, 'expiration_date', expiration_date 
            )
            if expiration_date_chain.empty:
                self.expiration_dates[key] = None
            else:
                self.expiration_dates[key] = OptionChainsSymDTE(
                    parent=self, chain=expiration_date_chain
                )
        return self.expiration_dates[key]

    def expire_days(self):
        """
        Returns the unique days to expiration values in the option chains.

        Returns:
            numpy.ndarray: An array of unique days to expiration.
        """
        return self.chains["days_to_expiration"].unique()

    def expire_dates(self):
        """
        Returns the unique expiration dates in the option chains.

        Returns:
            numpy.ndarray: An array of unique expiration dates.
        """
        return self.chains["expiration_date"].unique()

    def underlying_price(self):
        """
        Retrieves the underlying price from the option chains.

        Returns:
            float: The underlying price.
        """
        return get_first_value(self.chains, "underlying_price")


class OptionChains(BaseModel, arbitrary_types_allowed=True):
    csv: str = None
    chains: pd.DataFrame = None

    # internal \/
    symbol_chains: dict = {}

    def model_post_init(self, context):
        """
        Post-initialization to load and prepare option chains.
        """
        if self.chains is None:
            if self.csv is not None:
                self.chains = get_chains_from_csv(self.csv)
        elif not isinstance(self.chains, pd.DataFrame):
            raise ValueError("Unimplemented chain source")
        self.chains = prepare_chains(chains=self.chains, prune_spx=True)
        return super().model_post_init(context)

    def purge(self, open_interest_threshold=10, delta_min=0.03, delta_max=0.97, price_min=10) -> None:
        """
        Filters out uninteresting option chains based on open interest, delta, and underlying price.

        Args:
            open_interest_threshold (int, optional): The minimum open interest. Defaults to 10.
            delta_min (float, optional): The minimum absolute delta value. Defaults to 0.03.
            delta_max (float, optional): The maximum absolute delta value. Defaults to 0.97.
            price_min (int, optional): The minimum underlying price. Defaults to 10.
        """
        self.chains = self.chains.loc[
            (self.chains["open_interest"] > open_interest_threshold)
            & (abs(self.chains["delta"]) > delta_min)
            & (abs(self.chains["delta"]) < delta_max)
            & (self.chains["underlying_price"] > price_min)
        ].copy()


    def underlying_symbols(self):
        """
        Returns the unique underlying symbols in the option chains.

        Returns:
            numpy.ndarray: An array of unique underlying symbols.
        """
        return self.chains["underlying_symbol"].unique()


    def get_symbol_chain(self, symbol: str) -> OptionChainsSym:
        """
        Retrieves or creates an OptionChainsSym object for a given symbol.

        Args:
            symbol (str): The underlying symbol.

        Returns:
            OptionChainsSym: An OptionChainsSym object for the symbol.
        """
        if symbol not in self.symbol_chains:
            symbol_chain = filter_option_chains(self.chains, symbol=symbol)
            self.symbol_chains[symbol] = OptionChainsSym(chains=symbol_chain)
        return self.symbol_chains[symbol]




