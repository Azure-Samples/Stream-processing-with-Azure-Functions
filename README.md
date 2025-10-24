<!--
---
name: Vehicle Telemetry Stream Processing with Event Hubs and Azure Functions
description: This sample showcases real-time event processing of vehicle telemetry using Azure Event Hubs and Azure Functions with Flex Consumption plan.
page_type: sample
products:
- azure
- azure-functions
- azure-blob-storage
- azure-virtual-network
- entra-id
- azure-event-hubs
urlFragment: stream-processing-with-azure-functions
languages:
- csharp
- bicep
- azdeveloper
---
-->

# Vehicle Telemetry Stream Processing with Event Hubs and Azure Functions

This sample showcases real-time event processing of vehicle telemetry using Azure Event Hubs and Azure Functions with Flex Consumption plan. The solution includes:

- **Event Generator**: A high-performance Python application that simulates vehicle location events with extreme throughput capabilities
- **Function App**: A .NET 8 isolated Azure Function with OpenTelemetry observability that processes events from Event Hubs
- **Infrastructure**: Bicep templates using Azure Verified Modules for deployment

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│  Event Generator│───▶│  Azure Event Hub │───▶│  Azure Function App  │
│    (Python)     │    │                  │    │    (.NET 8)          │
└─────────────────┘    └──────────────────┘    └──────────────────────┘
```

## Features

- **Real-time event processing** with Azure Event Hubs
- **Serverless compute** with Azure Functions Flex Consumption plan (scales to **32 instances**)
- **Extreme performance capabilities** - Generate and process **thousands of events per second**
- **Vehicle tracking simulation** with GPS coordinates and routing
- **OpenTelemetry observability** with Azure Monitor integration for full telemetry
- **Secure authentication** with managed identity support (DefaultAzureCredential)
- **Auto-scaling demonstrations** - Watch real-time scaling from 1 to 32 instances
- **Smart analytics processing** including:
  - 🚌 **Vehicle state tracking** - Monitor route changes, stops, and movement
  - 📍 **Geofencing** - Detect zone entries/exits (Manhattan, Central Park, etc.)
  - ⚠️ **Performance monitoring** - Speed violations and traffic congestion detection
  - 🔮 **Predictive analytics** - ETA calculations and arrival predictions
  - 📊 **Route analytics** - Average speeds and vehicle density per route
- **Infrastructure as Code** using Azure Verified Modules
- **Azure Developer CLI (azd)** integration for easy deployment

## Prerequisites

- Azure CLI
- Azure Developer CLI (azd)
- .NET 8 SDK
- Python 3.9+
- Visual Studio Code (recommended)

## Quick Start

### 1. Deploy Infrastructure

```powershell
# Login to Azure
azd auth login

# Initialize and deploy
azd init
azd up
```

### 2. Run the Event Generator

```powershell
# Navigate to the event generator directory
cd event-generator

# Install dependencies
pip install -e .

# Standard Development Mode
python -m vehicle_generator.cli feed --agency "demo-transit" --vehicles 100 --poll-interval 2

# High-Performance Demo (recommended for scaling demonstrations)
python -m vehicle_generator.cli feed --agency "demo-transit" --high-performance

# High-Performance Testing with 5000+ vehicles for maximum scale
python -m vehicle_generator.cli feed --agency "demo-transit" --vehicles 5000 --poll-interval 0.1 --high-performance

```

### 3. Monitor the Function App and Scaling

- **Application Insights Live Metrics**: Watch real-time scaling to 32 instances
- **Azure Portal**: View logs in Function App > Monitor
- **Performance metrics**: Monitor thousands of events per second processing
- **OpenTelemetry traces**: End-to-end observability in Application Insights

## Project Structure

```
eventhubs-demo/
├── event-generator/           # Python event generator
│   ├── event_generator/
│   │   ├── __init__.py
│   │   ├── models.py         # Vehicle position data models
│   │   ├── generator.py      # Event generation logic
│   │   └── cli.py           # Command-line interface
│   ├── pyproject.toml       # Python package configuration
│   └── README.md
├── function-app/             # .NET Azure Function
│   ├── EventHubsTrigger.cs  # Event processing function
│   ├── VehiclePosition.cs   # Data models
│   ├── host.json           # Function host configuration
│   ├── local.settings.json # Local development settings
│   └── VehicleTracker.csproj
├── infra/                   # Infrastructure as Code
│   ├── main.bicep          # Main deployment template
│   └── modules/
│       ├── eventHub.bicep  # Event Hub resources
│       └── functionApp.bicep # Function App resources
├── azure.yaml              # Azure Developer CLI configuration
└── README.md
```

## Event Generator

The Python event generator simulates vehicle movement with for high-throughput demonstrations:

### Features
- **Extreme Performance Mode**: Generate **thousands of events per second** with parallel processing
- **Multiple vehicle simulation**: Track up to 5,000+ vehicles simultaneously
- **Route-based movement**: Vehicles follow predefined routes with realistic GPS coordinates
- **CloudEvents format**: Events use the CloudEvents specification optimized for performance
- **Parallel batch processing**: Concurrent event creation and transmission
- **Connection optimization**: Persistent connections with connection reuse
- **Real-time performance metrics**: Live throughput monitoring and warnings

### High-Performance Architecture
- **Semaphore-controlled concurrency**: Limits concurrent operations to prevent system overload
- **Parallel batch transmission**: Multiple concurrent batches for maximum throughput
- **Optimized event creation**: Bypasses CloudEvent overhead for raw EventData performance
- **Performance monitoring**: Real-time metrics showing events/sec and processing times

### Usage

```powershell
# High-performance mode with default: 1000 vehicles, 0.5s intervals = 2000 events/sec)
python -m vehicle_generator.cli feed --agency "demo-transit" --high-performance

# High-performance testing with 5000 vehicles, 0.1s intervals = 50,000 events/sec)
python -m vehicle_generator.cli feed --agency "demo-transit" --vehicles 5000 --poll-interval 0.1 --high-performance

# Standard usage 
python -m vehicle_generator.cli feed --agency "demo-transit" --vehicles 100 --poll-interval 2

# Custom performance testing
python -m vehicle_generator.cli feed \
  --agency "demo-transit" \
  --vehicles 2000 \
  --poll-interval 0.3 \
  --high-performance
```

### Command Line Options

- `--agency`: Transit agency identifier (required)
- `--route`: Route identifier (default: all-routes)
- `--vehicles`: Number of vehicles to simulate (default: 1000 for high throughput)
- `--poll-interval`: Interval between event batches in seconds (default: 0.5 for max throughput)
- `--event-hub-namespace`: Event Hub namespace (can use ENV: EVENT_HUB_NAMESPACE)
- `--event-hub-name`: Event Hub name (can use ENV: EVENT_HUB_NAME, default: vehicle-events)
- `--high-performance`: Enable extreme high-performance mode for thousands of events/sec
- `--verbose, -v`: Enable verbose logging for debugging

### Performance Modes

**Standard Mode** (100-500 vehicles):
- Suitable for functional testing and development
- 50-250 events/sec typical throughput
- Minimal resource usage

**High-Performance Mode** (1000+ vehicles):
- Optimized for scaling demonstrations
- 1000-10,000+ events/sec throughput
- Automatic performance warnings and monitoring
- Demonstrates Function App auto-scaling to 32 instances

## Function App

The .NET 8 isolated Azure Function processes events from Event Hubs with **OpenTelemetry observability**:

### Features
- **Event Hubs trigger**: Automatically processes events as they arrive
- **High-throughput batch processing**: Efficiently handles thousands of events per second
- **OpenTelemetry integration**: Full observability with Azure Monitor exporter
- **Managed Identity authentication**: Secure authentication with DefaultAzureCredential
- **JSON deserialization**: Converts CloudEvents to strongly-typed objects
- **Advanced analytics**: Vehicle tracking, geofencing, and performance monitoring
- **Auto-scaling**: Flex Consumption plan scales to **32 instances** under load

### OpenTelemetry Observability
- **Azure Monitor integration**: Automatic telemetry export to Application Insights
- **Distributed tracing**: End-to-end request tracing across services
- **Custom metrics**: Business-specific performance counters
- **Real-time monitoring**: Live metrics showing scaling and throughput
- **Performance insights**: Detailed analysis of processing times and dependencies

### Scaling Capabilities
- **Flex Consumption plan**: Automatically scales from 1 to 32 instances
- **Event-driven scaling**: Scales based on Event Hub partition load
- **Cost-effective**: Pay only for actual usage
- **Real-time monitoring**: Watch scaling events in Application Insights Live Metrics

## Event Processing Capabilities

The Function App implements sophisticated real-time analytics for vehicle tracking:

### 🚌 Vehicle State Management
- **Route change detection**: Automatically detects when vehicles switch routes
- **Stop/start monitoring**: Identifies when vehicles stop or resume movement
- **Speed tracking**: Monitors vehicle speeds and detects violations

### 📍 Geofencing & Location Analytics
- **Predefined zones**: Manhattan Downtown, Central Park, Brooklyn Heights, Queens Plaza
- **Zone entry/exit events**: Real-time notifications when vehicles cross zone boundaries
- **Location-based insights**: Analyze vehicle density and movement patterns

### ⚠️ Performance & Safety Monitoring
- **Speed violations**: Alerts for vehicles exceeding 50 km/h in urban areas
- **Traffic congestion detection**: Identifies routes with average speeds below 15 km/h
- **Vehicle health monitoring**: Tracks unusual patterns or potential issues

### 🔮 Predictive Analytics
- **ETA calculations**: Estimates arrival times based on current speed and distance
- **Route optimization insights**: Analyzes historical data for route efficiency
- **Real-time predictions**: Provides passenger wait time estimates

### 📊 Route Analytics
- **Performance metrics**: Average speeds and travel times per route
- **Vehicle distribution**: Real-time vehicle count and density analysis
- **Batch processing**: Analyzes events in batches for system-wide insights

### Sample Processing Output

```
📊 Route demo-transit:manhattan-loop: 3 vehicles, avg speed: 28.5 km/h
🚌 Vehicle vehicle-001 changed routes: brooklyn-express → manhattan-loop
📍 Vehicle vehicle-002 entered Manhattan Downtown
⚠️ Speed violation: Vehicle vehicle-003 traveling at 52.1 km/h
🕐 Vehicle vehicle-001 ETA to Central Park Area: 8 minutes
🚨 Potential traffic congestion on route demo-transit:brooklyn-express (avg speed: 12.3 km/h)
```

## Infrastructure

The infrastructure uses Azure Verified Modules (AVM) for best practices:

### Components
- **Event Hub Namespace**: Standard tier with auto-inflate enabled
- **Event Hub**: Configured for vehicle events with 2 partitions
- **Function App**: Flex Consumption plan with .NET 8 isolated runtime
- **Storage Account**: Required for Function App operation
- **Application Insights**: Monitoring and telemetry
- **Log Analytics**: Centralized logging

### Deployment

The infrastructure is deployed using Azure Developer CLI:

```powershell
# Deploy everything
azd up

# Deploy only infrastructure
azd provision

# Deploy only code
azd deploy
```

## Monitoring

### Using Application Insights Live Metrics
To observe the Function App scaling in real-time during high-throughput event processing:

1. **Navigate to Application Insights**
   - In the Azure Portal, go to your Function App
   - Click on "Application Insights" in the left menu
   - Select "Live Metrics" from the Application Insights overview

2. **Generate High-Volume Events**
   ```powershell
   # Run the event generator with high throughput settings
   python -m vehicle_generator.cli feed --agency "demo-transit" --vehicles 1000 --poll-interval 0.5 --high-performance
   ```

3. **Monitor Scaling**
   - Watch the **Server count** increase as the Function App scales out
   - Observe **up to 32 instances** being created automatically
   - Monitor **incoming requests/sec** and **outgoing requests/sec**. Note that this is not the number of total events processed per second, just the number of function executions, each execution can handle a batch of events. See below under Performance Analysis Queries to find the total events per second.
   - View **CPU and Memory** usage across all instances

4. **Real-time Metrics to Watch**
   - **Servers online**: Shows current instance count (can scale up to 32 instances)
   - **Incoming Requests**: Events being processed per second
   - **Request Duration**: Processing time per batch
   - **Dependency Duration**: Event Hub interaction times

### Performance Analysis Queries

To find out more about how your application scaled and how many events per second were processed, run these Application Insights queries a few minutes after running a test:

**1. Scaling and Instance Count Analysis**
```kusto
let _startTime = ago(20m); //Adjust start time as needed
let _endTime = now(); //Adjust end time as needed
let bins = 1s;
requests 
| where operation_Name == 'EventHubsTrigger'
| where timestamp between(_startTime .. _endTime)
| make-series dcount(cloud_RoleInstance) default=0 on timestamp from _startTime to _endTime step bins
| render columnchart  
```

**2. Events per Second Performance**
```kusto
let _startTime = ago(20m); //Adjust start time as needed
let _endTime = now(); //Adjust end time as needed 
requests 
| where operation_Name == 'EventHubsTrigger'
| where timestamp between(_startTime .. _endTime)
| extend NumberOfEvents = toint(customDimensions.['messaging.batch.message_count'])
| summarize sum(NumberOfEvents) by bin(timestamp, 1s)
| render timechart 
```

## Best Practices

### Security
- Managed Identity for Azure resource authentication

### Performance
- Flex Consumption plan automatically scales based on demand
- Event Hub partitioning for parallel processing
- Efficient batch processing in functions

### Monitoring
- Comprehensive logging at all levels using OpenTelemetry framework
- Application Insights for performance monitoring
- Custom metrics for business logic tracking

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Resources

- [Azure Event Hubs Documentation](https://docs.microsoft.com/azure/event-hubs/)
- [Azure Functions Documentation](https://docs.microsoft.com/azure/azure-functions/)
- [Azure Developer CLI](https://docs.microsoft.com/azure/developer/azure-developer-cli/)
- [Azure Verified Modules](https://azure.github.io/Azure-Verified-Modules/)
- [CloudEvents Specification](https://cloudevents.io/)
