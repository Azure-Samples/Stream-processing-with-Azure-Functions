"""Vehicle event generator for Azure Event Hubs."""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union

from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData
from azure.identity.aio import DefaultAzureCredential
from cloudevents.http import CloudEvent

from .models import VehiclePosition, Route, Vehicle


logger = logging.getLogger(__name__)


class VehicleEventGenerator:
    """Generates vehicle location events and sends them to Azure Event Hubs."""
    
    def __init__(self, event_hub_namespace: str, event_hub_name: str):
        """Initialize the event generator.
        
        Args:
            event_hub_namespace: Azure Event Hubs namespace (e.g., 'mynamespace.servicebus.windows.net')
            event_hub_name: Name of the Event Hub
        """
        self.event_hub_namespace = event_hub_namespace
        self.event_hub_name = event_hub_name
        self.producer_client: Optional[EventHubProducerClient] = None
        self.vehicles: List[Vehicle] = []
        self.running = False
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
        
    async def start(self) -> None:
        """Start the Event Hub producer client with high-performance optimizations."""
        # Always use DefaultAzureCredential for authentication
        # This will try: Environment variables → Managed Identity → Azure CLI → VS Code → Interactive
        credential = DefaultAzureCredential()
        logger.info("Using DefaultAzureCredential for authentication")
        
        # Configure Event Hub producer for maximum performance
        self.producer_client = EventHubProducerClient(
            fully_qualified_namespace=self.event_hub_namespace,
            eventhub_name=self.event_hub_name,
            credential=credential
            # Note: Removed transport_type parameter as it's not available in current SDK version
        )
        
        logger.info(f"🚀 Started HIGH-PERFORMANCE Event Hub producer for {self.event_hub_name}")
        logger.info(f"   Namespace: {self.event_hub_namespace}")
        logger.info(f"   Optimized for extreme throughput")
        
    async def stop(self) -> None:
        """Stop the Event Hub producer client."""
        if self.producer_client:
            await self.producer_client.close()
            self.producer_client = None
        logger.info("Stopped Event Hub producer")
        
    def create_demo_routes(self) -> List[Route]:
        """Create demo routes for vehicle simulation."""
        # Demo route 1: Manhattan loop
        manhattan_route = Route(
            tag="manhattan-loop",
            title="Manhattan Downtown Loop",
            waypoints=[
                (40.7128, -74.0060),  # New York City
                (40.7505, -73.9934),  # Times Square
                (40.7829, -73.9654),  # Central Park
                (40.7614, -73.9776),  # Columbus Circle
                (40.7282, -73.9942),  # Greenwich Village
                (40.7128, -74.0060),  # Back to start
            ]
        )
        
        # Demo route 2: Brooklyn route
        brooklyn_route = Route(
            tag="brooklyn-express",
            title="Brooklyn Express",
            waypoints=[
                (40.6892, -73.9442),  # Brooklyn Bridge
                (40.6441, -73.9570),  # Park Slope
                (40.6195, -73.9776),  # Sunset Park
                (40.5795, -73.9707),  # Bay Ridge
                (40.6195, -73.9776),  # Back through Sunset Park
                (40.6441, -73.9570),  # Back through Park Slope
                (40.6892, -73.9442),  # Back to start
            ]
        )
        
        # Demo route 3: Queens route
        queens_route = Route(
            tag="queens-connector",
            title="Queens Connector",
            waypoints=[
                (40.7282, -73.7949),  # Long Island City
                (40.7505, -73.8370),  # Astoria
                (40.7682, -73.8370),  # East Elmhurst
                (40.7505, -73.8756),  # Jackson Heights
                (40.7282, -73.8370),  # Woodside
                (40.7282, -73.7949),  # Back to start
            ]
        )
        
        return [manhattan_route, brooklyn_route, queens_route]
        
    def setup_vehicles(self, agency: str, route_tag: Optional[str], num_vehicles: int) -> None:
        """Set up vehicles for simulation.
        
        Args:
            agency: Transit agency identifier
            route_tag: Specific route tag, or None for all routes
            num_vehicles: Number of vehicles to simulate
        """
        routes = self.create_demo_routes()
        
        # Filter routes if specific route requested
        if route_tag and route_tag != "all-routes":
            routes = [r for r in routes if r.tag == route_tag]
            
        if not routes:
            logger.warning(f"No routes found for route_tag: {route_tag}")
            routes = self.create_demo_routes()[:1]  # Use first route as fallback
            
        self.vehicles = []
        
        # Distribute vehicles across available routes
        for i in range(num_vehicles):
            route = routes[i % len(routes)]
            
            # Add some randomness to starting positions and speeds
            import random
            starting_waypoint = random.randint(0, max(0, len(route.waypoints) - 2))
            starting_progress = random.uniform(0.0, 1.0)
            speed = random.uniform(20.0, 40.0)  # 20-40 km/h
            
            vehicle = Vehicle(
                id=f"vehicle-{i+1:03d}",
                route=route,
                current_waypoint_index=starting_waypoint,
                progress_to_next_waypoint=starting_progress,
                speed_km_hr=speed
            )
            vehicle.update_heading()
            self.vehicles.append(vehicle)
            
        logger.info(f"Set up {len(self.vehicles)} vehicles across {len(routes)} routes")
        
    def create_vehicle_position_event(self, vehicle: Vehicle, agency: str, current_time: datetime) -> CloudEvent:
        """Create a CloudEvent for a vehicle position.
        
        Args:
            vehicle: Vehicle object with current position
            agency: Transit agency identifier
            current_time: Pre-calculated current time for consistency
            
        Returns:
            CloudEvent object ready for sending
        """
        lat, lon = vehicle.get_current_position()
        
        position = VehiclePosition(
            agency=agency,
            route_tag=vehicle.route.tag,
            vehicle_id=vehicle.id,
            lat=lat,
            lon=lon,
            heading=vehicle.heading,
            speed_km_hr=vehicle.speed_km_hr,
            timestamp=current_time
        )
        
        # Create CloudEvent
        event = CloudEvent(
            {
                "type": "vehicle.position",
                "source": "vehicle-generator",
                "subject": f"{agency}/{vehicle.id}",
                "id": str(uuid.uuid4()),
                "time": position.timestamp.isoformat(),
                "datacontenttype": "application/json"
            },
            position.to_dict()
        )
        
        return event
        
    async def send_vehicle_events(self, agency: str) -> None:
        """Send events for all vehicles with high-performance optimizations.
        
        Args:
            agency: Transit agency identifier
        """
        if not self.producer_client:
            raise RuntimeError("Producer client not started")

        start_time = asyncio.get_event_loop().time()
        
        # Use a single timestamp for all events in this batch for consistency
        current_time = datetime.now(timezone.utc)
        time_iso = current_time.isoformat()
        
        # Pre-compute common data to avoid repeated work
        agency_vehicles = [(agency, vehicle) for vehicle in self.vehicles]
        
        # Create all events with maximum concurrency
        events_to_send = await self._create_all_events_optimized(agency_vehicles, current_time, time_iso)
        
        # Send events in parallel batches for maximum throughput
        total_events_sent = await self._send_events_parallel_batches(events_to_send)
        
        end_time = asyncio.get_event_loop().time()
        elapsed_ms = (end_time - start_time) * 1000
        events_per_second = total_events_sent / (elapsed_ms / 1000) if elapsed_ms > 0 else 0
        
        # Enhanced logging with performance metrics
        logger.info(f"🚀 HIGH-PERF: {total_events_sent} events | {len(self.vehicles)} vehicles | "
                   f"{elapsed_ms:.1f}ms | {events_per_second:.0f} events/sec")

    async def _create_all_events_optimized(self, agency_vehicles: list, current_time: datetime, time_iso: str) -> list:
        """Create all events with maximum optimization."""
        # Use semaphore to control concurrency and avoid overwhelming the system
        semaphore = asyncio.Semaphore(100)  # Limit concurrent event creation
        
        async def create_event_with_semaphore(agency, vehicle):
            async with semaphore:
                return await self._create_event_data_optimized(vehicle, agency, current_time, time_iso)
        
        # Create all events concurrently with controlled concurrency
        tasks = [create_event_with_semaphore(agency, vehicle) for agency, vehicle in agency_vehicles]
        return await asyncio.gather(*tasks)

    async def _send_events_parallel_batches(self, events_to_send: list) -> int:
        """Send events using parallel batches for maximum throughput."""
        if not events_to_send:
            return 0
            
        # Split events into multiple batches for parallel sending
        batch_size = 100  # Optimal batch size for Event Hubs
        event_batches = [events_to_send[i:i + batch_size] for i in range(0, len(events_to_send), batch_size)]
        
        # Send batches in parallel with limited concurrency
        semaphore = asyncio.Semaphore(10)  # Limit concurrent batch sends
        
        async def send_batch_with_semaphore(events_batch):
            async with semaphore:
                return await self._send_single_batch(events_batch)
        
        # Send all batches concurrently
        batch_results = await asyncio.gather(*[send_batch_with_semaphore(batch) for batch in event_batches])
        
        return sum(batch_results)

    async def _send_single_batch(self, events_batch: list) -> int:
        """Send a single batch of events."""
        try:
            event_data_batch = await self.producer_client.create_batch()
            events_in_batch = 0
            
            for event_data in events_batch:
                try:
                    event_data_batch.add(event_data)
                    events_in_batch += 1
                except ValueError:
                    # Current batch is full, send it and start a new one
                    if events_in_batch > 0:
                        await self.producer_client.send_batch(event_data_batch)
                    
                    # Create new batch and add the current event
                    event_data_batch = await self.producer_client.create_batch()
                    event_data_batch.add(event_data)
                    events_in_batch = 1
            
            # Send the final batch if it has events
            if events_in_batch > 0:
                await self.producer_client.send_batch(event_data_batch)
                
            return len(events_batch)
            
        except Exception as e:
            logger.error(f"Error sending batch: {e}")
            return 0
        
    async def _create_event_data_optimized(self, vehicle: Vehicle, agency: str, current_time: datetime, time_iso: str) -> EventData:
        """Create EventData for a single vehicle with maximum optimization.
        
        Args:
            vehicle: Vehicle object with current position
            agency: Transit agency identifier
            current_time: Pre-calculated current time for consistency
            time_iso: Pre-calculated ISO timestamp string
            
        Returns:
            EventData object ready for sending
        """
        # Get position (this is already optimized in the Vehicle class)
        lat, lon = vehicle.get_current_position()
        
        # Create the data payload directly as dict to avoid object overhead
        event_data_dict = {
            "agency": agency,
            "routeTag": vehicle.route.tag,
            "vehicleId": vehicle.id,
            "lat": lat,
            "lon": lon,
            "heading": vehicle.heading,
            "speedKmHr": vehicle.speed_km_hr,
            "timestamp": time_iso,
            "predictable": True
        }
        
        # Create EventData directly with JSON string (avoid CloudEvent overhead for high throughput)
        event_data = EventData(json.dumps(event_data_dict))
        
        # Add minimal CloudEvent headers for compatibility
        event_id = str(uuid.uuid4())
        event_data.properties = {
            "ce-specversion": "1.0",
            "ce-type": "vehicle.position",
            "ce-source": "vehicle-generator",
            "ce-subject": f"{agency}/{vehicle.id}",
            "ce-id": event_id,
            "ce-time": time_iso,
            "ce-datacontenttype": "application/json"
        }
        
        return event_data
                
    def advance_vehicles(self, time_step_seconds: float) -> None:
        """Advance all vehicles along their routes.
        
        Args:
            time_step_seconds: Time step for vehicle advancement
        """
        for vehicle in self.vehicles:
            vehicle.advance(time_step_seconds)
            
    async def run_feed(self, agency: str, route_tag: Optional[str] = None, 
                      num_vehicles: int = 1000, poll_interval: float = 0.5) -> None:
        """Run the vehicle event feed with extreme performance optimizations.
        
        Args:
            agency: Transit agency identifier
            route_tag: Specific route tag, or None for all routes
            num_vehicles: Number of vehicles to simulate
            poll_interval: Interval between event batches in seconds
        """
        self.setup_vehicles(agency, route_tag, num_vehicles)
        self.running = True
        
        # Calculate expected performance metrics
        expected_events_per_sec = num_vehicles / poll_interval if poll_interval > 0 else 0
        
        logger.info(f"🚀 Starting EXTREME PERFORMANCE vehicle feed:")
        logger.info(f"   Agency: '{agency}' | Route: '{route_tag or 'all'}'")
        logger.info(f"   Vehicles: {num_vehicles:,} | Interval: {poll_interval}s")
        logger.info(f"   Expected Throughput: {expected_events_per_sec:,.0f} events/sec")
        logger.info(f"   Total Event Rate: {expected_events_per_sec*60:,.0f} events/min")
        
        # Performance tracking
        total_events_sent = 0
        batch_count = 0
        start_time = asyncio.get_event_loop().time()
        
        try:
            while self.running:
                batch_start = asyncio.get_event_loop().time()
                
                # Send current vehicle positions
                await self.send_vehicle_events(agency)
                
                # Update performance tracking
                total_events_sent += num_vehicles
                batch_count += 1
                
                # Log performance metrics every 10 batches to reduce logging overhead
                if batch_count % 10 == 0:
                    elapsed_time = asyncio.get_event_loop().time() - start_time
                    if elapsed_time > 0:
                        actual_events_per_sec = total_events_sent / elapsed_time
                        logger.info(f"📊 PERFORMANCE: Batch {batch_count} | "
                                   f"{total_events_sent:,} total events | "
                                   f"{actual_events_per_sec:,.0f} events/sec actual")
                
                # Advance vehicles for next iteration
                self.advance_vehicles(poll_interval)
                
                # Smart sleep calculation to maintain precise timing
                batch_elapsed = asyncio.get_event_loop().time() - batch_start
                sleep_time = max(0, poll_interval - batch_elapsed)
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                elif batch_count % 10 == 0:  # Only warn occasionally
                    logger.warning(f"⚠️  Processing time ({batch_elapsed:.3f}s) exceeds poll interval ({poll_interval}s)")
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping extreme performance feed...")
        except Exception as e:
            logger.error(f"Error in extreme performance feed loop: {e}")
            raise
        finally:
            self.running = False
            
            # Final performance report
            total_elapsed = asyncio.get_event_loop().time() - start_time
            if total_elapsed > 0:
                final_events_per_sec = total_events_sent / total_elapsed
                logger.info(f"🏁 FINAL PERFORMANCE REPORT:")
                logger.info(f"   Total Events: {total_events_sent:,}")
                logger.info(f"   Total Batches: {batch_count}")
                logger.info(f"   Total Time: {total_elapsed:.1f}s")
                logger.info(f"   Average Throughput: {final_events_per_sec:,.0f} events/sec")
                logger.info(f"   Peak Capability: {final_events_per_sec*60:,.0f} events/min")
            
            logger.info("🛑 Extreme performance vehicle feed stopped")