
# test_leg.py

import sys
sys.path.append("..")
sys.path.append("src")
sys.path.append("../src")

import unittest
import pytest
from option_strategy_sim.leg import OptionLeg
from option_strategy_sim.core import OptionStrategy
from pydantic import ValidationError

# Mock OptionStrategy for testing purposes
@pytest.fixture
def mock_option_strategy():
    return OptionStrategy(underlying_price=100, days_to_expiration=30)



@pytest.fixture
def mock_option_strategy_sigma():
    return OptionStrategy(underlying_price=100, sigma=0.2, days_to_expiration=30)


# ------ Pytest Tests ------
def test_option_leg_creation(mock_option_strategy):
    """Test basic OptionLeg creation with valid parameters."""
    leg = OptionLeg(
        option_type="C",
        strike_price=105,
        days_to_expiration=30,
        quantity=1,
        volatility=0.2,
        optionstrategy=mock_option_strategy,
    )
    assert leg.option_type == "C"
    assert leg.strike_price == 105
    assert leg.days_to_expiration == 30
    assert leg.quantity == 1
    assert leg.volatility == 0.2

def test_option_leg_default_volatility(mock_option_strategy):
    """Test that OptionLeg defaults to OptionStrategy volatility when not provided."""
    mock_option_strategy.sigma = 0.3  # Set strategy volatility

    leg = OptionLeg(
        option_type="C",
        strike_price=105,
        days_to_expiration=30,
        quantity=1,
        optionstrategy=mock_option_strategy,
    )

    assert leg.volatility == 0.3

def test_option_leg_default_days_to_expiration(mock_option_strategy):
    """Test that OptionLeg defaults to OptionStrategy days_to_expiration when not provided."""

    leg = OptionLeg(
        option_type="C",
        strike_price=105,
        quantity=1,
        volatility=0.2,
        optionstrategy=mock_option_strategy,
    )
    assert leg.days_to_expiration == 30

def test_option_leg_invalid_option_type(mock_option_strategy):
    """Test that OptionLeg raises ValueError for invalid option_type."""
    with pytest.raises(ValueError) as excinfo:
        OptionLeg(
            option_type="X",  # Invalid option type
            strike_price=105,
            days_to_expiration=30,
            quantity=1,
            volatility=0.2,
            optionstrategy=mock_option_strategy,
        )
    assert " must be " in str(excinfo.value)

def test_option_leg_invalid_strike_price(mock_option_strategy):
    """Test that OptionLeg raises ValueError for invalid strike_price."""
    with pytest.raises(ValueError) as excinfo:
        OptionLeg(
            option_type="C",
            strike_price=-105,  # Invalid strike price
            days_to_expiration=30,
            quantity=1,
            volatility=0.2,
            optionstrategy=mock_option_strategy,
        )
    assert "Strike price must be a positive float." in str(excinfo.value)

def test_option_leg_invalid_days_to_expiration(mock_option_strategy):
    """Test that OptionLeg raises ValueError for invalid days_to_expiration."""
    with pytest.raises(ValueError) as excinfo:
        OptionLeg(
            option_type="C",
            strike_price=105,
            days_to_expiration=-30,  # Invalid days to expiration
            quantity=1,
            volatility=0.2,
            optionstrategy=mock_option_strategy,
        )
    assert "Days to expiration must be a non-negative float." in str(excinfo.value)

def test_option_leg_invalid_quantity(mock_option_strategy):
    """Test that OptionLeg raises ValueError for invalid quantity."""
    with pytest.raises(ValueError) as excinfo:
        OptionLeg(
            option_type="C",
            strike_price=105,
            days_to_expiration=30,
            quantity=1.5,  # Invalid quantity
            volatility=0.2,
            optionstrategy=mock_option_strategy,
        )
    assert "Quantity must be an integer." in str(excinfo.value)

def test_option_leg_calc_price_and_delta(mock_option_strategy):
    """Test the calc_price_and_delta method.  Checks to a degree but depends on black scholes"""
    leg = OptionLeg(
        option_type="C",
        strike_price=105,
        days_to_expiration=30,
        quantity=1,
        volatility=0.2,
        optionstrategy=mock_option_strategy,
    )
    price, delta = leg.calc_price_and_delta()
    assert isinstance(price, float)
    assert isinstance(delta, float)
    assert price > 0  # Option price should always be positive
    assert 0 < delta < 1 # call delta shoulld be between 0-1

def test_option_leg_theta(mock_option_strategy):
    """Test the theta property."""
    leg = OptionLeg(
        option_type="C",
        strike_price=105,
        days_to_expiration=30,
        quantity=1,
        volatility=0.2,
        optionstrategy=mock_option_strategy,
    )
    theta = leg.theta
    assert isinstance(theta, float)
    # Theta can be negative or positive, so we don't check the sign here.
    # Just ensure it's a number.

def test_option_leg_vega(mock_option_strategy):
    """Test the vega property."""
    leg = OptionLeg(
        option_type="C",
        strike_price=105,
        days_to_expiration=30,
        quantity=1,
        volatility=0.2,
        optionstrategy=mock_option_strategy,
    )
    vega = leg.vega
    assert isinstance(vega, float)
    assert vega >= 0  # Vega should always be non-negative


# ------ Unittest Tests ------
class TestOptionLeg(unittest.TestCase):
    def setUp(self):
        self.mock_option_strategy = OptionStrategy(underlying_price=100, days_to_expiration=30)
        self.mock_option_strategy_sigma = OptionStrategy(underlying_price=100, sigma=0.3, days_to_expiration=30)

    def test_option_leg_creation(self):
        """Test basic OptionLeg creation with valid parameters."""
        leg = OptionLeg(
            option_type="C",
            strike_price=105,
            days_to_expiration=30,
            quantity=1,
            volatility=0.2,
            optionstrategy=self.mock_option_strategy,
        )
        self.assertEqual(leg.option_type, "C")
        self.assertEqual(leg.strike_price, 105)
        self.assertEqual(leg.days_to_expiration, 30)
        self.assertEqual(leg.quantity, 1)
        self.assertEqual(leg.volatility, 0.2)

    def test_option_leg_default_volatility(self):
        """Test that OptionLeg defaults to OptionStrategy volatility when not provided."""
        self.mock_option_strategy.sigma = 0.3  # Set strategy volatility

        leg = OptionLeg(
            option_type="C",
            strike_price=105,
            days_to_expiration=30,
            quantity=1,
            optionstrategy=self.mock_option_strategy_sigma,
        )
        self.assertEqual(leg.volatility, 0.3)

    def test_option_leg_default_days_to_expiration(self):
        """Test that OptionLeg defaults to OptionStrategy days_to_expiration when not provided."""

        leg = OptionLeg(
            option_type="C",
            strike_price=105,
            quantity=1,
            volatility=0.2,
            optionstrategy=self.mock_option_strategy,
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
