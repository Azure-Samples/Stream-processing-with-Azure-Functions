# Event Generator

A Python application that simulates real-time vehicle location events for Azure Event Hubs.

## Features

- **Multi-vehicle simulation**: Simulate multiple vehicles moving simultaneously
- **Realistic GPS coordinates**: Vehicles follow predefined routes with realistic coordinates
- **CloudEvents format**: Events conform to the CloudEvents specification
- **Configurable parameters**: Customize vehicle count, frequency, and duration
- **Azure Event Hubs integration**: Send events directly to Azure Event Hubs

## Installation

### From Source

```bash
# Clone and install in development mode
git clone <repository-url>
cd event-generator
pip install -e .
```

### Requirements

- Python 3.9+
- azure-eventhub
- cloudevents

## Usage

### Authentication

The event generator supports two authentication methods:

#### 1. Managed Identity (Recommended)

```bash
# Using system-assigned managed identity
python -m vehicle_generator.cli feed \
  --agency "demo-transit" \
  --use-managed-identity \
  --event-hub-namespace "your-namespace.servicebus.windows.net" \
  --event-hub-name "vehicle-events"

# Using user-assigned managed identity
python -m vehicle_generator.cli feed \
  --agency "demo-transit" \
  --use-managed-identity \
  --event-hub-namespace "your-namespace.servicebus.windows.net" \
  --managed-identity-client-id "your-identity-client-id" \
  --event-hub-name "vehicle-events"
```

#### 2. Connection String (Legacy)

```bash
python -m vehicle_generator.cli feed \
  --agency "demo-transit" \
  --connection-string "Endpoint=sb://your-namespace.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=your-key"
```

### Command Line Interface

```bash
# Basic usage with managed identity
python -m vehicle_generator.cli feed --agency "demo-transit" --use-managed-identity

# Full configuration with managed identity
python -m vehicle_generator.cli feed \
  --agency "demo-transit" \
  --route "manhattan-loop" \
  --vehicles 5 \
  --poll-interval 2 \
  --use-managed-identity \
  --event-hub-namespace "your-namespace.servicebus.windows.net" \
  --event-hub-name "vehicle-events"
```

### Command Line Options

| Option | Description | Default | Environment Variable |
|--------|-------------|---------|---------------------|
| `--agency` | Transit agency identifier (required) | - | - |
| `--route` | Route identifier | "all-routes" | - |
| `--vehicles` | Number of vehicles to simulate | 3 | - |
| `--poll-interval` | Seconds between events per vehicle | 10 | - |
| `--use-managed-identity` | Use managed identity authentication | false | `USE_MANAGED_IDENTITY` |
| `--event-hub-namespace` | Event Hub namespace (for managed identity) | - | `EVENT_HUB_NAMESPACE` |
| `--managed-identity-client-id` | User-assigned identity client ID | - | `MANAGED_IDENTITY_CLIENT_ID` |
| `--connection-string` | Event Hub connection string (legacy) | - | `EVENT_HUB_CONNECTION_STRING` |
| `--event-hub-name` | Event Hub name | "vehicle-events" | `EVENT_HUB_NAME` |

### Programmatic Usage

#### With Managed Identity

```python
from vehicle_generator.generator import VehicleEventGenerator
import asyncio

async def main():
    # Using system-assigned managed identity
    generator = VehicleEventGenerator(
        event_hub_namespace="your-namespace.servicebus.windows.net",
        event_hub_name="vehicle-events",
        use_managed_identity=True
    )
    
    # Using user-assigned managed identity
    generator = VehicleEventGenerator(
        event_hub_namespace="your-namespace.servicebus.windows.net",
        event_hub_name="vehicle-events",
        use_managed_identity=True,
        managed_identity_client_id="your-identity-client-id"
    )
    
    await generator.run_feed(
        agency="demo-transit",
        route_tag="manhattan-loop",
        num_vehicles=5,
        poll_interval=10.0
    )

# Run the simulation
asyncio.run(main())
```

#### With Connection String (Legacy)

```python
from vehicle_generator.generator import VehicleEventGenerator
import asyncio

async def main():
    generator = VehicleEventGenerator(
        event_hub_namespace="your-namespace.servicebus.windows.net",  # Extracted from connection string
        event_hub_name="vehicle-events",
        connection_string="Endpoint=sb://your-namespace.servicebus.windows.net/;SharedAccessKeyName=...",
        use_managed_identity=False
    )
    
    await generator.run_feed(
        agency="demo-transit",
        route_tag="manhattan-loop",
        num_vehicles=5,
        poll_interval=10.0
    )

# Run the simulation
asyncio.run(main())
```

## Event Format

Events are generated in CloudEvents format:

```json
{
  "specversion": "1.0",
  "type": "com.example.vehicle.position",
  "source": "vehicle-simulator",
  "id": "unique-event-id",
  "time": "2024-01-15T10:30:00Z",
  "datacontenttype": "application/json",
  "subject": "vehicle-001",
  "data": {
    "vehicleId": "vehicle-001",
    "timestamp": "2024-01-15T10:30:00Z",
    "location": {
      "latitude": 47.6062,
      "longitude": -122.3321
    },
    "speed": 35.5,
    "heading": 180.0,
    "routeId": "route-001",
    "routeProgress": 0.15
  }
}
```

## Data Models

### VehiclePosition

```python
@dataclass
class Location:
    latitude: float
    longitude: float

@dataclass
class VehiclePosition:
    vehicle_id: str
    timestamp: str
    location: Location
    speed: float
    heading: float
    route_id: str
    route_progress: float
```

## Route Simulation

The generator includes predefined routes with realistic GPS coordinates:

### Route 1: Seattle Downtown Loop
- **Start**: Seattle Waterfront (47.6062, -122.3321)
- **Path**: Through downtown Seattle
- **End**: Capitol Hill (47.6205, -122.3212)
- **Distance**: ~5 km

### Route 2: Eastside Corridor  
- **Start**: Bellevue (47.6101, -122.2015)
- **Path**: Along I-405 corridor
- **End**: Redmond (47.6740, -122.1215)
- **Distance**: ~8 km

### Route 3: Airport Route
- **Start**: SeaTac Airport (47.4502, -122.3088)
- **Path**: Via I-5 North
- **End**: University District (47.6587, -122.3138)
- **Distance**: ~12 km

## Configuration

### Environment Variables

```bash
# Optional: Set default connection string
export EVENT_HUB_CONNECTION_STRING="your-connection-string"

# Optional: Set default Event Hub name
export EVENT_HUB_NAME="vehicle-events"
```

### Logging

The generator uses Python's logging module. Configure logging level:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Development

### Project Structure

```
event-generator/
├── event_generator/
│   ├── __init__.py
│   ├── models.py          # Data models
│   ├── generator.py       # Core generation logic
│   └── cli.py            # Command-line interface
├── pyproject.toml        # Project configuration
├── README.md
└── requirements.txt
```

### Adding New Routes

To add new routes, modify the `ROUTES` dictionary in `generator.py`:

```python
ROUTES = {
    "route-004": [
        (47.7511, -122.1133),  # Bothell
        (47.7210, -122.0790),  # Woodinville
        (47.6890, -122.0851),  # Kirkland
        # Add more waypoints...
    ]
}
```

### Testing

```bash
# Test with managed identity (minimal settings)
python -m vehicle_generator.cli feed \
  --agency "demo-transit" \
  --vehicles 1 \
  --poll-interval 10 \
  --use-managed-identity \
  --event-hub-namespace "your-namespace.servicebus.windows.net"

# Test with connection string (minimal settings)
python -m vehicle_generator.cli feed \
  --agency "demo-transit" \
  --vehicles 1 \
  --poll-interval 10 \
  --connection-string "YOUR_CONNECTION_STRING"
```

## Troubleshooting

### Common Issues

1. **Managed Identity Authentication Errors**
   - Ensure the compute resource (VM, Function App, etc.) has managed identity enabled
   - Verify the managed identity has "Azure Event Hubs Data Sender" role on the Event Hub namespace
   - For user-assigned identity, ensure the client ID is correct
   - Check Azure logs for authentication failures

2. **Connection refused**
   - Verify Event Hub namespace and name are correct
   - Check network connectivity and firewall rules
   - Ensure Event Hub exists in the specified namespace

3. **Permission errors**
   - For managed identity: Verify RBAC roles (Azure Event Hubs Data Sender)
   - For connection string: Validate shared access key and permissions
   - Check Event Hub access policies

4. **Rate limiting**
   - Reduce vehicle count with `--vehicles` parameter
   - Increase interval between events with `--poll-interval`
   - Check Event Hub throughput units and scaling

### Authentication Troubleshooting

#### Managed Identity Issues

```bash
# Test managed identity connectivity
az account get-access-token --resource https://eventhubs.azure.net/

# Check assigned roles
az role assignment list --assignee <managed-identity-principal-id> --scope <event-hub-namespace-resource-id>
```

#### Required Azure RBAC Roles

For managed identity authentication, assign these roles to the managed identity:

- **Azure Event Hubs Data Sender** - Required to send events to Event Hubs
- **Azure Event Hubs Data Owner** - If you need full access (send, receive, manage)

```bash
# Assign role via Azure CLI
az role assignment create \
  --role "Azure Event Hubs Data Sender" \
  --assignee <managed-identity-principal-id> \
  --scope /subscriptions/<subscription-id>/resourceGroups/<rg-name>/providers/Microsoft.EventHub/namespaces/<namespace-name>
```

### Debug Mode

Enable detailed logging:

```bash
# With managed identity
python -m vehicle_generator.cli feed \
  --agency "demo-transit" \
  --vehicles 1 \
  --poll-interval 30 \
  --use-managed-identity \
  --event-hub-namespace "your-namespace.servicebus.windows.net" \
  -v  # Verbose logging

# With connection string
python -m vehicle_generator.cli feed \
  --agency "demo-transit" \
  --vehicles 1 \
  --poll-interval 30 \
  --connection-string "YOUR_CONNECTION_STRING" \
  -v  # Verbose logging
```

## Performance Considerations

- **Throughput**: Each vehicle generates events at the specified interval
- **Memory usage**: Minimal - events are sent immediately
- **Network**: Batch sends for efficiency
- **Scaling**: Can simulate hundreds of vehicles on a single machine

## License

MIT License - see LICENSE file for details.