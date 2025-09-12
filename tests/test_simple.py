"""
Simple test to verify the testing infrastructure works.
"""

import pytest
import numpy as np
from unittest.mock import Mock


def test_numpy_import():
    """Test that numpy can be imported and used."""
    arr = np.array([1, 2, 3, 4, 5])
    assert len(arr) == 5
    assert arr.sum() == 15


def test_mock_functionality():
    """Test that unittest.mock works."""
    mock_obj = Mock()
    mock_obj.test_method.return_value = "test_value"
    
    result = mock_obj.test_method()
    assert result == "test_value"
    mock_obj.test_method.assert_called_once()


def test_pytest_fixtures():
    """Test that pytest fixtures work."""
    # This test verifies that pytest is working correctly
    assert True


def test_basic_math():
    """Test basic mathematical operations."""
    assert 2 + 2 == 4
    assert 3 * 3 == 9
    assert 10 / 2 == 5


@pytest.mark.unit
def test_unit_marker():
    """Test that unit marker works."""
    assert True


@pytest.mark.integration
def test_integration_marker():
    """Test that integration marker works."""
    assert True


@pytest.mark.api
def test_api_marker():
    """Test that API marker works."""
    assert True
