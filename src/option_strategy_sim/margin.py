"""Module to calculate Cash/Margin requirements for an option strategy


Much of this is an adaptation of "margin-estimator" by Graeme22 / Graeme Holliday 

https://github.com/tastyware/margin-estimator/tree/main



"""


from __future__ import annotations
import numpy as np
# import OptionStrategy
from typing import List
import option_strategy_sim.core # import OptionStrategy
import option_strategy_sim.leg


### ETFS and leverage, not complete, but ok
### update as needed  { SYMBOL: leverageX }
ETFS = {
    'SPY': 1, 'VOO': 1, 'IVV': 1, 'VTI': 1, 'QQQ': 1, 'VEA': 1, 'IEFA': 1, 'IJH': 1,
    'IJR': 1, 'VIG': 1, 'VGT': 1, 'VWO': 1, 'IEMG': 1, 'VXUS': 1, 'IWM': 1, 'VO': 1,
    'XLK': 1, 'RSP': 1, 'SCHD': 1, 'VB': 1, 'ITOT': 1, 'VYM': 1, 'EFA': 1, 'SPLG': 1,
    'SCHX': 1, 'QUAL': 1, 'XLF': 1, 'VT': 1, 'IWR': 1, 'SCHF': 1, 'VV': 1, 'VEU': 1, 
    'IWB': 1, 'XLV': 1, 'XLE': 1, 'IXUS': 1, 'DIA': 1, 'JEPI': 1, 'VNQ': 1, 'QQQM': 1, 
    'DFAC': 1, 'SCHB': 1, 'DGRO': 1, 'COWZ': 1, 'TQQQ': 3, 'MDY': 1, 'USMV': 1, 'XLY': 1,
    'VXF': 1, 'XLI': 1, 'SDY': 1, 'DVY': 1, 'SPDW': 1, 'XLC': 1, 'IYW': 1, 'ACWI': 1, 'SCHA': 1, 
    'JEPQ': 1, 'EEM': 1, 'FNDX': 1, 'VGK': 1, 'XLU': 1, 'VHT': 1, 'XLP': 1, 'EMXC': 1, 'MOAT': 1, 
    'IWV': 1, 'DGRW': 1, 'OEF': 1, 'IDEV': 1, 'ESGU': 1, 'EWJ': 1, 'MTUM': 1, 'GSLC': 1, 'FNDF': 1, 
    'DYNF': 1, 'RDVY': 1, 'SPSM': 1, 'FTEC': 1, 'VTWO': 1, 'NOBL': 1, 'DFUS': 1, 'SPMD': 1, 
    'SPHQ': 1, 'SCHM': 1, 'VFH': 1, 'BBJP': 1, 'HDV': 1, 'INDA': 1, 'SPEM': 1, 'ESGV': 1, 
    'FVD': 1, 'SPTM': 1, 'FNDA': 1, 'DFAS': 1, 'SCHE': 1, 'FTCS': 1, 'CALF': 1, 'VSS': 1, 
    'SCZ': 1, 'VDE': 1, 'QYLD': 1, 'ESGD': 1, 'VYMI': 1, 'FXI': 1, 'AVUS': 1, 'IQLT': 1, 'XLRE': 1, 
    'PRF': 1, 'QLD': 2, 'BBCA': 1, 'SPLV': 1, 'XLG': 1, 'SDVY': 1, 'ONEQ': 1, 'DUHP': 1, 'VDC': 1, 
    'VIGI': 1, 'DFAX': 1, 'DFAI': 1, 'VPL': 1, 'SPYD': 1, 'DFIC': 1, 'AVEM': 1, 'DFAU': 1, 
    'JGLO': 1, 'EZU': 1, 'VPU': 1, 'DBEF': 1, 'MGC': 1, 'BBEU': 1, 'FNDE': 1, 'JIRE': 1, 
    'IOO': 1, 'VCR': 1, 'XMHQ': 1, 'XLB': 1, 'PBUS': 1, 'VIS': 1, 'EFAV': 1, 'BUFR': 1, 
    'MCHI': 1, 'SSO': 2, 'EWT': 1, 'SPXL': 1, 'HEFA': 1, 'VONE': 1, 'OMFL': 1, 'JQUA': 1, 
    'IXN': 1, 'AVDE': 1, 'DSI': 1, 'BBIN': 1, 'DFAE': 1, 'BBAX': 1, 'IYR': 1, 'FDL': 1, 
    'ACWX': 1, 'DLN': 1, 'ESGE': 1, 'VOX': 1, 'ACWV': 1, 'UPRO': 3, 'DFEM': 1, 'SPGP': 1, 
    'BBUS': 1, 'JHMM': 1, 'IEUR': 1, 'EEMV': 1, 'FDVV': 1, 'EWY': 1, 'IDV': 1, 'RWL': 1, 
    'URTH': 1, 'FELC': 1, 'CGUS': 1, 'SCHK': 1, 'SCHC': 1, 'SPMO': 1, 'DON': 1, 'QTEC': 1, 
    'VSGX': 1, 'IXJ': 1, 'FV': 1, 'SUSA': 1, 'DIVO': 1, 'IYF': 1, 'DXJ': 1, 'EWZ': 1, 'EPI': 1, 
    'GSIE': 1, 'KNG': 1, 'SPHD': 1, 'RSPT': 1, 'TECL': 1, 'XT': 1, 'FEZ': 1, 'PTLC': 1, 
    'VNQI': 1, 'IYH': 1, 'BITU': 2, 'USD': 2, 'UYG': 2, 'ROM': 2, 'AGQ': 2, 'DDM': 2, 'UWM': 2, 
    'UCO': 2, 'SDS': 2, 'TBT': 2, 'BOIL': 2, 'UGL': 2, 'KOLD': 2, 'QID': 2, 'SCO': 2, 'ETHT': 2, 
    'MVV': 2, 'UBT': 2, 'DIG': 2, 'RXL': 2, 'URE': 2, 'BIB': 2, 'DXD': 2, 'YCL': 2, 'SBIT': 2, 
    'TWM': 2, 'EUO': 2, 'UYM': 2, 'SAA': 2, 'SRS': 2, 'UXI': 2, 'YCS': 2, 'EPV': 2, 'ZSL': 2, 
    'UCC': 2, 'UST': 2, 'XPP': 2, 'UPW': 2, 'PST': 2, 'GLL': 2, 'EET': 2, 'UJB': 2, 'DUG': 2, 
    'SKF': 2, 'FXP': 2, 'LTL': 2, 'UGE': 2, 'BZQ': 2, 'EFO': 2, 'SSG': 2, 'ETHD': 2, 'ULE': 2, 
    'EZJ': 2, 'EEV': 2, 'EWV': 2, 'UCYB': 2, 'REW': 2, 'UPV': 2, 'BIS': 2, 'SKYU': 2, 'EFU': 2, 
    'SDD': 2, 'UBR': 2, 'RXD': 2, 'SDP': 2, 'MZZ': 2, 'SCC': 2, 'SIJ': 2, 'SMN': 2, 'SZK': 2, 
    'SQQQ': 3, 'UDOW': 3, 'URTY': 3, 'SPXU': 3, 'SDOW': 3, 'SRTY': 3, 'UMDD': 3, 'TTT': 3, 'SMDD': 3
}

STOCK_MARGIN = 0.25 # brokers range from 0.2 - 0.5

    
class MarginCalculator:
    """Calculates margin requirements for an option strategy."""

    def __init__(self, ostrat: option_strategy_sim.core.OptionStrategy):
        """Initializes with the option strategy."""
        self.ostrat: option_strategy_sim.core.OptionStrategy = ostrat


    def calculate_margin(self) -> tuple[float,float]:
        """
        Calculate margin for an arbitrary order according to CBOE's Margin Manual.
        """
        stock_cash, stock_margin = self._calc_stock_margin()
        option_cash, option_margin = self._calc_option_margin()
        cash = stock_cash + option_cash
        margin = stock_margin + option_margin
        if cash < margin:
            cash = margin
        return cash, margin
    
    def _calc_option_margin_assum(self, *legs) -> tuple[float,float]:
        """ Calc as sum of all margins of option legs """
        cash = 0
        margin = 0
        for leg in legs:
            c, m = self._calc_option_margin(leg)
            cash += c
            margin += m
        return cash , margin


    def _calc_option_margin(self, *legs) -> tuple[float,float]:
        if len(legs) == 0: 
            legs = self.ostrat.option_legs()
        if len(legs) == 1:
            if legs[0].quantity > 0:
                return self._calc_margin_long_option(legs[0])
            return self._calc_margin_short_option(legs[0])
        if len(legs) == 2:
            if legs[0].quantity < 0 and legs[1].quantity < 0:
                return self._calc_margin_short_strangle(legs)
            else: # a spread
                if legs[0].option_type == legs[1].option_type:
                    if legs[0].quantity == -legs[1].quantity:
                        return self._calc_margin_spread(legs)

        if len(legs) == 4:
            # iron condor 
            calls = [leg for leg in legs if leg.option_type == 'C']
            puts = [leg for leg in legs if leg.option_type == 'P']
            if len(calls) == len(puts) and len(puts) == 2:
                if calls[0].quantity + calls[1].quantity == 0:
                    if puts[0].quantity + puts[1].quantity == 0:
                        if abs(puts[0].quantity) == abs(calls[0].quantity):
                            return self._calc_margin_ironcondor(calls,puts)
        # from here we will simply sum the legs 
        # can we do more ? if 3 legs, see if there is a spread ? 
        # if not, this sum will over-estimate some cases
        return self._calc_option_margin_assum(*legs)
    

    def _calc_stock_margin(self, *legs) -> tuple[float,float]:
        """Calculates margin for stock legs, typically 50% of value or some other percentage"""
        if len(legs) == 0: 
            legs = self.ostrat.stock_legs()
        margin: float = 0.0
        cash: float = 0.0
        for leg in legs:
            margin += abs(leg.mark * leg.quantity) * STOCK_MARGIN
            cash += abs(leg.mark * leg.quantity)        
        return cash, margin
    
    def _calc_margin_ironcondor(self, calls, puts):
        cash1, margin1 = self._calc_margin_spread(calls)
        cash2, margin2 = self._calc_margin_spread(puts)
        return max(cash1,cash2), max(margin1, margin2)
    

    def _calc_margin_long_option(self, leg: option_strategy_sim.leg.OptionLeg) -> tuple[float,float] :
        """
        Calculate margin for a single long option.
        Source: CBOE Margin Manual
        """
        # Pay for each put or call in full.
        cash = leg.mark * 100 * leg.quantity
        if leg.days_to_expiration < 90: 
            # Pay for each put or call in full.
            margin=leg.mark * 100 * leg.quantity
        else:
            # Listed: 75% of the total cost of the option.
            margin = leg.mark * 3/4 * 100 * leg.quantity
        return cash, margin 
    

    def _calc_margin_short_option(self,leg: option_strategy_sim.leg.OptionLeg) -> tuple[float,float]:
        """
        Calculate margin for a single short option.
        Source: CBOE Margin Manual
        """
        margin:float = 0.0
        cash:float = 0.0
        stprice = self.ostrat.underlying_price
        if leg.option_type == 'P':
            otm_distance = max(0, stprice - leg.strike_price)
        else:
            otm_distance = max(0, leg.strike_price - stprice)

        underlying_symbol = self.ostrat.underlying_symbol or '_'
        # broad-based ETFs/indices
        if underlying_symbol in ETFS: 
            leverage = ETFS[underlying_symbol] or 1
            if leg.option_type == 'P':
                minimum = leg.mark + leg.strike_price / 10 * leverage
                base = leg.strike_price + stprice * 3 / 20 * leverage - otm_distance
                # 100% of option proceeds plus 15% of underlying index value less
                # out-of-the money amount, if any, to a minimum for puts of option
                # proceeds plus 10% of the put’s exercise price.
                margin = max(minimum, base)
                # Deposit cash or cash equivalents equal to aggregate exercise price
                cash = (leg.strike_price - leg.mark) 
            else:  # OptionType.CALL
                minimum = leg.mark + stprice / 10 * leverage
                base = leg.mark + stprice * 3 / 20 * leverage - otm_distance
                # 100% of option proceeds plus 15% of underlying index value less
                # out-of-the money amount, if any, to a minimum for calls of option
                # proceeds plus 10% of the underlying index value.
                margin = max(minimum, base)
                # Deposit cash or cash equivalents equal to aggregate exercise price
                cash = (leg.strike_price - leg.mark)
        # narrow-based ETFs/indices, volatility indices, equities
        else:
            if leg.option_type == 'P':
                minimum = leg.mark + leg.strike_price / 10 
                base = leg.mark + stprice / 5 - otm_distance
                # 100% of option proceeds plus 20% of underlying security / index value
                # less out-of-the-money amount, if any, to a minimum for puts of option
                # proceeds plus 10% of the put’s exercise price.
                margin = max(minimum, base)
                # Deposit cash or cash equivalents equal to aggregate exercise price.
                cash = (leg.strike_price - leg.mark)
            else:  # OptionType.CALL
                minimum = leg.mark + stprice / 10 
                base = leg.mark + stprice / 5 - otm_distance
                # 100% of option proceeds plus 20% of underlying security / index value
                # less out-of-the-money amount, if any, to a minimum for puts of option
                # proceeds plus 10% of the underlying security/index value.
                margin = max(minimum, base)
                # Deposit underlying security.
                cash = (stprice - leg.mark)
        cash *= 100 * abs(leg.quantity)
        margin *= 100 * abs(leg.quantity)
        return cash, margin
    

    def _calc_margin_short_strangle(self, legs: list[option_strategy_sim.leg.OptionLeg]) -> tuple[float,float]:
        """
        Calculate margin for a short strangle.
        Source: CBOE Margin Manual
        """
        # Deposit an escrow agreement for each option.
        cash1, margin1 = self._calc_margin_short_option(legs[0])
        cash2, margin2 = self._calc_margin_short_option(legs[1])
        cash = cash1 + cash2
        # For the same underlying security, short put or short call requirement whichever
        # is greater, plus the option proceeds of the other side.
        if margin1 > margin2:
            margin = margin1 + legs[1].mark * 100 * abs(legs[1].quantity)
        else:
            margin = margin2 + legs[0].mark * 100 * abs(legs[0].quantity)
        return cash, margin

    def _calc_loss_for(self,leg: option_strategy_sim.leg.OptionLeg, price: float) -> float:
        """
        Calculate value at expiration for option at given price.
        """
        if leg.option_type == 'C':
            itm_distance = max(0, price - leg.strike_price)
        else:
            itm_distance = max(0, leg.strike_price - price)
        return itm_distance * leg.quantity * 100


    def _get_net_credit_or_debit(self, legs) -> float:
        """
        Calculate total debit/credit paid/collected for the order.
        """
        total = 0
        for leg in legs:
            total += leg.quantity * leg.mark * 100
        return total


    def _calc_margin_spread(self, legs) -> tuple[float,float]:
        """
        Calculate margin for a credit spread.
        Source: CBOE Margin Manual
        """
        strikes = [leg.strike_price for leg in legs]
        pnl = self._get_net_credit_or_debit(legs)
        losses = []
        for strike in strikes:
            points = [self._calc_loss_for(leg, strike) for leg in legs]
            losses.append(sum(points))  # type: ignore
        require = abs(min(losses)) + pnl
        return require, require
