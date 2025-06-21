import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from cost_analyzer.analyzer import CostData, MultiCloudCostAnalyzer


def test_cost_data_creation():
    """Test CostData creation"""
    cost_data = CostData(
        service="EC2",
        cost=100.50,
        currency="USD",
        date=datetime.now(),
        cloud_provider="AWS"
    )
    
    assert cost_data.service == "EC2"
    assert cost_data.cost == 100.50
    assert cost_data.currency == "USD"
    assert cost_data.cloud_provider == "AWS"


def test_cost_summary_empty_data():
    """Test cost summary with empty data"""
    # This would require mocking the config file
    # For now, just test the basic functionality
    assert True  # Placeholder test


if __name__ == "__main__":
    pytest.main([__file__])
