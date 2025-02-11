import sys
sys.path.insert(0,"src")
sys.path.insert(0,"../src")

import pytest
from option_strategy_sim.core import OptionStrategy, OptionLeg, OptionStrategyRepr
from option_strategy_sim.pnl import OptionPnL
import numpy as np
import unittest
class TestOptionStrategy(unittest.TestCase):

    def setUp(self):
        # Create a basic OptionStrategy instance for testing
        self.strategy = OptionStrategy(underlying_price=100.0, days_to_expiration=30.0, volatility=0.2)

    def test_add_leg(self):
        # Test adding an option leg to the strategy
        self.strategy.add_leg(option_type='C', strike_price=105.0, quantity=1, volatility=0.2)
        self.assertEqual(len(self.strategy.legs), 1)
        self.assertEqual(self.strategy.legs[0].strike_price, 105.0)

        # Test adding a stock leg
        self.strategy.add_leg(option_type='S', strike_price=100.0, quantity=10)
        self.assertEqual(len(self.strategy.legs), 2)
        self.assertEqual(self.strategy.legs[1].option_type, 'S')

    def test_delta(self):
        # Test calculating delta of the strategy
        self.strategy.add_leg(option_type='C', strike_price=105.0, quantity=1, delta=0.6)
        self.strategy.add_leg(option_type='P', strike_price=95.0, quantity=-1, delta=-0.4)  # Short put
        expected_delta = 0.6 - (-0.4) # delta is already on the leg, so is multiplied by leg.quantity
        self.assertAlmostEqual(self.strategy.delta(), expected_delta)



    def test_cost(self):
        # Test calculating cost of the strategy
        self.strategy.add_leg(option_type='C', strike_price=105.0, quantity=1, mark=2.0)
        self.strategy.add_leg(option_type='P', strike_price=95.0, quantity=-1, mark=1.0)  # Short put
        self.strategy.add_leg(option_type='S', strike_price=100.0, quantity=2, mark=100.0) #long 2 stocks
        expected_cost = (2.0 * 1 * 100) + (-1.0 * 1 * 100) + (2*100.0)
        self.assertAlmostEqual(self.strategy.cost(), expected_cost)

    def test_calc_current_dte(self):
        # Test calculating average days to expiration
        self.strategy.add_leg(option_type='C', strike_price=105.0, days_to_expiration=30.0, quantity=1)
        self.strategy.add_leg(option_type='P', strike_price=95.0, days_to_expiration=60.0,quantity=-1)
        expected_dte = (30.0 + 60.0) / 2
        self.assertAlmostEqual(self.strategy.calc_current_dte(), expected_dte)

        # Test when no option legs are present
        strategy = OptionStrategy(underlying_price=100.0) #no dte specified either
        self.assertEqual(strategy.calc_current_dte(), 1.0)

    def test_volatility(self):
        # Test calculating volatility (average of legs)
        strategy = OptionStrategy(underlying_price=100.0, days_to_expiration=35)
        strategy.add_leg(option_type='C', strike_price=105.0, volatility=0.2, quantity=1)
        strategy.add_leg(option_type='P', strike_price=95.0, volatility=0.3, quantity=-1)
        expected_volatility = (0.2 + 0.3) / 2
        self.assertAlmostEqual(strategy.volatility(), expected_volatility)

        # Test overriding volatility during OptionStrategy initialization
        strategy = OptionStrategy(underlying_price=100.0, volatility=0.4, days_to_expiration=35)
        strategy.add_leg(option_type='C', strike_price=105.0, quantity=1)
        self.assertAlmostEqual(strategy.volatility(), 0.4)

        # Test when no option legs are present
        strategy = OptionStrategy(underlying_price=100.0)
        self.assertAlmostEqual(strategy.volatility(), 0.22) # Default value

    def test_option_legs(self):
        # Test retrieving only option legs
        self.strategy.add_leg(option_type='C', strike_price=105.0, quantity=1)
        self.strategy.add_leg(option_type='S', strike_price=100.0, quantity=10)
        option_legs = self.strategy.option_legs()
        self.assertEqual(len(option_legs), 1)
        self.assertEqual(option_legs[0].option_type, 'C')

    def test_stock_legs(self):
        # Test retrieving only stock legs
        self.strategy.add_leg(option_type='C', strike_price=105.0, quantity=1)
        self.strategy.add_leg(option_type='S', strike_price=100.0, quantity=10)
        stock_legs = self.strategy.stock_legs()
        self.assertEqual(len(stock_legs), 1)
        self.assertEqual(stock_legs[0].option_type, 'S')

    def test_add_pnl(self):
        # Test adding a PnL object to the strategy
        self.strategy.add_pnl()
        self.assertEqual(len(self.strategy.pnls), 1)
        self.assertTrue(self.strategy.pnls[0].payoff)

        # Test adding PnLs with partitions
        self.strategy.add_pnl(partitions=3)
        self.assertEqual(len(self.strategy.pnls), 3)

        # Test adding PnL with days_forward
        self.strategy.add_pnl(days_forward=10)
        self.assertEqual(len(self.strategy.pnls), 4)

        # Test adding PnL with specific dte
        self.strategy.add_pnl(dte=15)
        self.assertEqual(len(self.strategy.pnls), 5)

    def test_get_pnl_attr(self):
        # Create OptionStrategy and OptionPnL instances
        strategy = OptionStrategy(underlying_price=100, days_to_expiration=30, volatility=0.2)
        strategy.add_leg(option_type='C', strike_price=105.0, quantity=1)

        pnl = OptionPnL(
            optionstrategy=strategy, 
            stddev=10, days_to_expiration=20, price_range=np.array([90,100,110]), pnl_values=np.array([1, 2, 3]), 
            pop=0.5, expected_profit=100, expected_pnl_values=np.array([4, 5, 6])
        )
        strategy.pnls = [pnl]

        # Test retrieving expected move
        self.assertGreater(strategy.expected_move(), 0)

        # Test retrieving stddev
        self.assertGreater(strategy.stddev(), 0)

        # Test retrieving dte
        self.assertEqual(strategy.days_to_expiration, 30)

        # Test retrieving price range
        prange = strategy.price_range(0)
        self.assertAlmostEqual(round(prange[0] - 90), 0)

        # Test retrieving pnl values
        self.assertGreater(0, strategy.pnl_values()[0])

        # Test retrieving pop
        self.assertGreater(0.4, strategy.pop())

        # Test retrieving expected profit
        self.assertGreater(0,strategy.expected_profit())

        # Test retrieving expected pnl values
        self.assertGreater(strategy.expected_pnl_values()[-1], 0)

        # Test invalid index
        strategy = OptionStrategy(underlying_price=100, days_to_expiration=30)
        with self.assertRaises(ValueError):
            strategy.get_pnl_attr("stddev", idx=1)

    def test_repr(self):
        # Test the repr method
        strategy = OptionStrategy(underlying_price=100, days_to_expiration=30)
        strategy.add_leg(option_type='C', strike_price=105.0, quantity=1)

        representation = strategy.repr()
        self.assertIsInstance(representation, OptionStrategyRepr)
        self.assertEqual(representation.underlying_price, 100.0)
        self.assertEqual(representation.volatility, strategy.volatility())


    def test_margin(self):
        # Test the margin calculation (basic test, more detailed tests would be in margin_test.py)
        self.strategy.add_leg(option_type='C', strike_price=105.0, quantity=1)
        margin = self.strategy.margin()
        self.assertIsInstance(margin, tuple)


if __name__ == "__main__":
    unittest.main()
