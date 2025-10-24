"""Vehicle Event Generator Package

A Python package for generating simulated vehicle location events
and sending them to Azure Event Hubs for real-time processing demos.
"""

__version__ = "1.0.0"
__author__ = "Azure Dev Summit"
__email__ = "demo@example.com"

from .generator import VehicleEventGenerator
from .models import VehiclePosition, Route, Vehicle

__all__ = ["VehicleEventGenerator", "VehiclePosition", "Route", "Vehicle"]