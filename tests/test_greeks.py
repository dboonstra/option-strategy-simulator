
# test_greeks.py
import sys 
sys.path.append("..")
sys.path.append("src")
sys.path.append("../src")

# test_greeks.py

import unittest
import pytest
from option_strategy_sim.greeks import (
    black_scholes,
    calculate_price_probability,
    black_scholes_vega,
    implied_volatility_newton_raphson,
    Greeks,
)
from pydantic import ValidationError


class TestBlackScholes(unittest.TestCase):
    """Test cases for the black scholes function."""
    def test_valid_call(self):
        price, delta, theta = black_scholes(100, 100, 30, "C", 0.2)
        self.assertIsNotNone(price); self.assertIsNotNone(delta); self.assertIsNotNone(theta)
        assert 0 <= delta <= 1
    
    def test_valid_put(self):
        price, delta, theta = black_scholes(100, 100, 30, "P", 0.2)
        self.assertIsNotNone(price); self.assertIsNotNone(delta); self.assertIsNotNone(theta)
        assert -1 <= delta <= 0
    
    def test_zero_time_to_expiry(self):
        price, delta, theta = black_scholes(100, 100, 0, "C", 0.2)
        self.assertEqual(price, 0); self.assertEqual(delta, 0); self.assertIsNone(theta)
        price, delta, theta = black_scholes(100, 110, 0, "P", 0.2)
        self.assertEqual(price, 10); self.assertEqual(delta, 0); self.assertIsNone(theta)
    
    def test_invalid_option_type(self):
        with self.assertRaises(ValueError): black_scholes(100, 100, 30, "X", 0.2)
    
    def test_missing_params(self):
        with self.assertRaises(ValueError): black_scholes(None, 100, 30, "C", 0.2)
        with self.assertRaises(ValueError): black_scholes(100, None, 30, "C", 0.2)
        with self.assertRaises(ValueError): black_scholes(100, 100, None, "C", 0.2)
        with self.assertRaises(ValueError): black_scholes(100, 100, 30, None, 0.2)
        with self.assertRaises(ValueError): black_scholes(100, 100, 30, "C", None)


class TestPriceProbability(unittest.TestCase):
    """Test cases for the price probability function."""
    def test_valid_probability(self):
        probability = calculate_price_probability(100, 110, 30, 0.2)
        self.assertGreaterEqual(probability, 0); self.assertLessEqual(probability, 1)
    
    def test_edge_cases(self):
        probability = calculate_price_probability(100, 100, 30, 0.2)
        self.assertGreaterEqual(probability, 0); self.assertLessEqual(probability, 1)
        probability = calculate_price_probability(100, 90, 30, 0.2)
        self.assertGreaterEqual(probability, 0); self.assertLessEqual(probability, 1)


class TestBlackScholesVega(unittest.TestCase):
    """Test cases for the Black-Scholes vega function."""
    def test_valid_vega(self):
        vega = black_scholes_vega(100, 100, 30, 0.2)
        self.assertGreaterEqual(vega, 0); self.assertIsInstance(vega, float)

    def test_zero_time_to_expiry(self):
        vega = black_scholes_vega(100, 100, 0, 0.2)
        self.assertEqual(vega, 0)

class TestImpliedVolatility(unittest.TestCase):
    """Test cases for the implied volatility function."""
    def test_valid_iv(self):
        iv, delta, theta, vega = implied_volatility_newton_raphson(100, 100, 30, 5, "C")
        self.assertIsNotNone(iv); self.assertIsNotNone(delta); self.assertIsNotNone(theta); self.assertIsNotNone(vega)
        self.assertGreaterEqual(iv, 0); self.assertIsInstance(iv, float)

    def test_no_convergence(self):
        iv_result = implied_volatility_newton_raphson(100, 100, 30, 1000, "C")
        self.assertIsNone(iv_result)


class TestGreeksClass(unittest.TestCase):
    """Test cases for the Greeks class."""
    def test_valid_greeks_with_vol(self):
       greeks = Greeks(underlying_price=100, strike_price=100, 
                       days_to_expiration=30, option_type="C", volatility=0.2).calc_greeks()
       self.assertIsNotNone(greeks.mark)
       self.assertIsNotNone(greeks.delta)
       self.assertIsNotNone(greeks.theta)
       self.assertIsNotNone(greeks.vega);
       self.assertIsNotNone(greeks.volatility)
    
    def test_valid_greeks_with_mark(self):
        greeks = Greeks(underlying_price=100, strike_price=100, days_to_expiration=30, 
                        option_type="C", mark=5).calc_greeks()
        self.assertIsNotNone(greeks.mark); self.assertIsNotNone(greeks.delta); self.assertIsNotNone(greeks.theta); self.assertIsNotNone(greeks.vega); self.assertIsNotNone(greeks.volatility)

    def test_greeks_validation_error(self):
        with pytest.raises(TypeError):
            Greeks(underlying_price=-100, strike_price=100, 
                   days_to_expiration=30, option_type="C", volatility=0.2).calc_greeks()
        with pytest.raises(TypeError):
            Greeks(underlying_price=100, strike_price=-100, days_to_expiration=30, option_type="C", volatility=0.2)
        with pytest.raises(TypeError):
            Greeks(underlying_price=100, strike_price=100, days_to_expiration=30, option_type="X", volatility=0.2)
    
    def test_greeks_validation_mark_vol_none(self):
        with pytest.raises(ValueError):
            Greeks(underlying_price=100, strike_price=100, days_to_expiration=30, option_type="C")
    
    def test_greeks_repr(self):
        greeks = Greeks(underlying_price=100, strike_price=100, days_to_expiration=30, option_type="C",
                         volatility=0.2)
        actual_repr = repr(greeks)
        print(actual_repr)
        actual_repr = repr(greeks).replace(", mark=None", "")
        actual_repr = actual_repr.replace(", delta=None","").replace(", theta=None", "").replace("vega=None", "")
        actual_repr = actual_repr.replace(", )",")")
        self.assertEqual(
            actual_repr, 
            "Greeks(underlying_price='100.00', option_type='C', strike_price=100.00, volatility=0.200)")


if __name__ == "__main__":
    unittest.main()
