
# test_leg.py

import sys
sys.path.insert(0,"src")
sys.path.insert(0,"../src")

import unittest
from option_strategy_sim.leg import OptionLeg
from option_strategy_sim.core import OptionStrategy
from pydantic import ValidationError

# ------ Unittest Tests ------
class TestOptionLeg(unittest.TestCase):
    def setUp(self):
        self.mock_option_strategy_dte = OptionStrategy(underlying_price=100, days_to_expiration=30)
        self.mock_option_strategy_sigma = OptionStrategy(underlying_price=100, volatility=0.3, days_to_expiration=30)
        self.mock_option_strategy = OptionStrategy(underlying_price=100)

    def test_option_leg_creation(self):
        """Test basic OptionLeg creation with valid parameters."""
        leg = OptionLeg(
            option_type="C",
            strike_price=105,
            days_to_expiration=30,
            quantity=1,
            volatility=0.2,
            days_to_epiration=30,
            optionstrategy=self.mock_option_strategy,
        )
        self.assertEqual(leg.option_type, "C")
        self.assertEqual(leg.strike_price, 105)
        self.assertEqual(leg.days_to_expiration, 30)
        self.assertEqual(leg.quantity, 1)
        self.assertEqual(leg.volatility, 0.2)

    def test_option_leg_default_volatility(self):
        """Test that OptionLeg defaults to OptionStrategy volatility when not provided."""
        leg = OptionLeg(
            option_type="C",
            strike_price=105,
            days_to_expiration=30,
            quantity=1,
            optionstrategy=self.mock_option_strategy_sigma,
        )
        self.assertEqual(leg.volatility, 0.3)

        leg = OptionLeg(
            option_type="C",
            strike_price=105,
            days_to_expiration=30,
            quantity=1,
            volatility=0.8,
            optionstrategy=self.mock_option_strategy_sigma,
        )
        self.assertEqual(leg.volatility, 0.8)


    def test_option_leg_default_days_to_expiration(self):
        """Test that OptionLeg defaults to OptionStrategy days_to_expiration when not provided."""

        leg = OptionLeg(
            option_type="C",
            strike_price=105,
            quantity=1,
            volatility=0.2,
            optionstrategy=self.mock_option_strategy_dte,
        )

        self.assertEqual(leg.days_to_expiration, 30)

    def test_option_leg_invalid_option_type(self):
        """Test that OptionLeg raises ValueError for invalid option_type."""
        with self.assertRaises(ValidationError) as context:
            OptionLeg(
                option_type="X",  # Invalid option type
                strike_price=105,
                days_to_expiration=30,
                quantity=1,
                volatility=0.2,
                optionstrategy=self.mock_option_strategy,
            )
        self.assertIn(" must be ", str(context.exception))

    def test_option_leg_invalid_strike_price(self):
        """Test that OptionLeg raises ValueError for invalid strike_price."""
        with self.assertRaises(ValueError) as context:
            OptionLeg(
                option_type="C",
                strike_price=-105,  # Invalid strike price
                days_to_expiration=30,
                quantity=1,
                volatility=0.2,
                optionstrategy=self.mock_option_strategy,
            )
        self.assertIn(" must ", str(context.exception))

    def test_option_leg_invalid_days_to_expiration(self):
        """Test that OptionLeg raises ValueError for invalid days_to_expiration."""
        with self.assertRaises(ValueError) as context:
            OptionLeg(
                option_type="C",
                strike_price=105,
                days_to_expiration=-30,  # Invalid days to expiration
                quantity=1,
                volatility=0.2,
                optionstrategy=self.mock_option_strategy,
            )
        self.assertIn("must be a non-negative", str(context.exception))

    def test_option_leg_invalid_quantity(self):
        """Test that OptionLeg raises ValueError for invalid quantity."""
        with self.assertRaises(ValueError) as context:
            OptionLeg(
                option_type="C",
                strike_price=105,
                days_to_expiration=30,
                quantity=1.5,  # Invalid quantity
                volatility=0.2,
                optionstrategy=self.mock_option_strategy,
            )
        self.assertIn("quantity", str(context.exception))

    def test_option_leg_calc_price_and_delta(self):
        """Test the calc_price_and_delta method.  Checks to a degree but depends on black scholes"""
        leg = OptionLeg(
            option_type="C",
            strike_price=105,
            days_to_expiration=30,
            quantity=1,
            volatility=0.2,
            optionstrategy=self.mock_option_strategy,
        )
        self.assertIsInstance(leg.mark, float)
        self.assertIsInstance(leg.delta, float)
        self.assertGreater(leg.mark, 0)  # Option price should always be positive
        self.assertTrue(0 < leg.delta < 1) # call delta shoulld be between 0-1

    def test_option_leg_theta(self):
        """Test the theta property."""
        leg = OptionLeg(
            option_type="C",
            strike_price=105,
            days_to_expiration=30,
            quantity=1,
            volatility=0.2,
            optionstrategy=self.mock_option_strategy,
        )
        theta = leg.theta
        self.assertIsInstance(theta, float)
        # Theta can be negative or positive, so we don't check the sign here.
        # Just ensure it's a number.

    def test_option_leg_vega(self):
        """Test the vega property."""
        leg = OptionLeg(
            option_type="C",
            strike_price=105,
            days_to_expiration=30,
            quantity=1,
            volatility=0.2,
            optionstrategy=self.mock_option_strategy,
        )
        vega = leg.vega
        self.assertIsInstance(vega, float)
        self.assertGreaterEqual(vega, 0)  # Vega should always be non-negative

if __name__ == "__main__":
    unittest.main()
