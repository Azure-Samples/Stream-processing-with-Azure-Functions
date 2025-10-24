"""Data models for vehicle event generation."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple
import uuid


@dataclass
class VehiclePosition:
    """Represents a vehicle's current position and status."""
    
    agency: str
    route_tag: str
    vehicle_id: str
    lat: float
    lon: float
    heading: float  # degrees (0-360)
    speed_km_hr: float
    timestamp: datetime
    predictable: bool = True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "agency": self.agency,
            "routeTag": self.route_tag,
            "vehicleId": self.vehicle_id,
            "lat": self.lat,
            "lon": self.lon,
            "heading": self.heading,
            "speedKmHr": self.speed_km_hr,
            "timestamp": self.timestamp.isoformat(),
            "predictable": self.predictable
        }


@dataclass
class Route:
    """Represents a transit route with waypoints."""
    
    tag: str
    title: str
    waypoints: List[Tuple[float, float]]  # List of (lat, lon) coordinates
    
    def get_distance_between_points(self, point1: Tuple[float, float], 
                                  point2: Tuple[float, float]) -> float:
        """Calculate approximate distance between two GPS coordinates in km."""
        import math
        
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in km
        r = 6371
        
        return c * r


@dataclass
class Vehicle:
    """Represents a vehicle with its current state."""
    
    id: str
    route: Route
    current_waypoint_index: int = 0
    progress_to_next_waypoint: float = 0.0  # 0.0 to 1.0
    speed_km_hr: float = 25.0  # Default speed
    heading: float = 0.0
    
    def get_current_position(self) -> Tuple[float, float]:
        """Get current interpolated position between waypoints."""
        if not self.route.waypoints:
            return (0.0, 0.0)
            
        if self.current_waypoint_index >= len(self.route.waypoints) - 1:
            # At the end of route, return last waypoint
            return self.route.waypoints[-1]
            
        current_waypoint = self.route.waypoints[self.current_waypoint_index]
        next_waypoint = self.route.waypoints[self.current_waypoint_index + 1]
        
        # Interpolate between current and next waypoint
        lat = (current_waypoint[0] + 
               (next_waypoint[0] - current_waypoint[0]) * self.progress_to_next_waypoint)
        lon = (current_waypoint[1] + 
               (next_waypoint[1] - current_waypoint[1]) * self.progress_to_next_waypoint)
        
        return (lat, lon)
    
    def update_heading(self) -> None:
        """Update heading based on direction to next waypoint."""
        import math
        
        if self.current_waypoint_index >= len(self.route.waypoints) - 1:
            return
            
        current_waypoint = self.route.waypoints[self.current_waypoint_index]
        next_waypoint = self.route.waypoints[self.current_waypoint_index + 1]
        
        # Calculate bearing
        lat1, lon1 = current_waypoint
        lat2, lon2 = next_waypoint
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon_rad = math.radians(lon2 - lon1)
        
        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad))
        
        bearing = math.atan2(y, x)
        bearing_degrees = (math.degrees(bearing) + 360) % 360
        
        self.heading = bearing_degrees
    
    def advance(self, time_step_seconds: float) -> None:
        """Advance vehicle along route based on time step."""
        if not self.route.waypoints or self.current_waypoint_index >= len(self.route.waypoints) - 1:
            return
            
        # Calculate distance traveled in this time step
        distance_km = (self.speed_km_hr / 3600) * time_step_seconds
        
        # Get distance to next waypoint
        current_waypoint = self.route.waypoints[self.current_waypoint_index]
        next_waypoint = self.route.waypoints[self.current_waypoint_index + 1]
        segment_distance = self.route.get_distance_between_points(current_waypoint, next_waypoint)
        
        if segment_distance == 0:
            # Move to next waypoint if current and next are the same
            self.current_waypoint_index += 1
            self.progress_to_next_waypoint = 0.0
            return
            
        # Calculate how much progress we make on current segment
        progress_increment = distance_km / segment_distance
        self.progress_to_next_waypoint += progress_increment
        
        # If we've reached or passed the next waypoint
        while self.progress_to_next_waypoint >= 1.0 and self.current_waypoint_index < len(self.route.waypoints) - 1:
            self.progress_to_next_waypoint -= 1.0
            self.current_waypoint_index += 1
            
            # If we're at the end of the route, loop back to start
            if self.current_waypoint_index >= len(self.route.waypoints) - 1:
                self.current_waypoint_index = 0
                self.progress_to_next_waypoint = 0.0
                break
        
        self.update_heading()