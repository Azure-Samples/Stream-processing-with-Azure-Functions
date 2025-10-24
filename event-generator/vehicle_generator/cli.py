"""Command-line interface for the vehicle event generator."""

import asyncio
import logging
import os
import sys
from typing import Optional

import click
from dotenv import load_dotenv

from .generator import VehicleEventGenerator


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce noise from Azure SDK packages
azure_loggers = [
    'azure.eventhub',
    'azure.eventhub._pyamqp',
    'azure.eventhub._pyamqp.aio',
    'azure.identity',
    'azure.identity.aio',
    'azure.identity.aio._credentials',
    'azure.identity.aio._internal',
    'azure.core',
    'azure.core.pipeline'
]

for azure_logger_name in azure_loggers:
    azure_logger = logging.getLogger(azure_logger_name)
    azure_logger.setLevel(logging.WARNING)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose: bool):
    """Vehicle Event Generator CLI.
    
    Generate simulated vehicle location events and send them to Azure Event Hubs.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        # Enable Azure SDK logging when verbose is requested
        for azure_logger_name in azure_loggers:
            azure_logger = logging.getLogger(azure_logger_name)
            azure_logger.setLevel(logging.DEBUG)

    # Load environment variables
    load_dotenv()

@cli.command()
@click.option('--agency', required=True, help='Transit agency identifier')
@click.option('--route', default='all-routes', help='Route identifier (default: all-routes)')
@click.option('--vehicles', default=1000, type=int, help='Number of vehicles to simulate (default: 1000 for high throughput)')
@click.option('--poll-interval', default=0.5, type=float, help='Interval between event batches in seconds (default: 0.5 for max throughput)')
@click.option('--event-hub-namespace', envvar='EVENT_HUB_NAMESPACE', help='Event Hub namespace (e.g., mynamespace.servicebus.windows.net)')
@click.option('--event-hub-name', envvar='EVENT_HUB_NAME', help='Event Hub name')
@click.option('--high-performance', is_flag=True, help='Enable extreme high-performance mode for thousands of events/sec')
def feed(agency: str, route: str, vehicles: int, poll_interval: float, 
         event_hub_namespace: Optional[str], event_hub_name: Optional[str], high_performance: bool):
    """Generate and send vehicle location events to Event Hubs with extreme performance optimization.
    
    This command polls vehicle locations and submits them to an Azure Event Hub instance.
    Uses DefaultAzureCredential for authentication (Azure CLI locally, managed identity in Azure).
    
    High-performance mode optimizations:
    - Default 1000 vehicles for massive scale testing
    - 0.5 second intervals for 2000+ events/sec throughput  
    - Parallel batch processing with concurrency controls
    - Optimized event creation and JSON serialization
    
    Example for extreme throughput:
        vehicle-generator feed --agency "demo-transit" --high-performance
        
    Example for custom scale:
        vehicle-generator feed --agency "demo-transit" --vehicles 5000 --poll-interval 0.1
    """
    # Get configuration from environment if not provided
    if not event_hub_namespace:
        event_hub_namespace = os.getenv('EVENT_HUB_NAMESPACE')
    if not event_hub_name:
        event_hub_name = os.getenv('EVENT_HUB_NAME', 'vehicle-events')  # Default hub name
    
    # Apply high-performance defaults
    if high_performance:
        if vehicles == 1000:  # Only override if using default
            vehicles = 5000
        if poll_interval == 0.5:  # Only override if using default  
            poll_interval = 0.1
        click.echo("🚀 HIGH-PERFORMANCE MODE ENABLED 🚀")
        click.echo(f"   Optimized for {vehicles} vehicles at {poll_interval}s intervals")
        click.echo(f"   Expected throughput: {vehicles/poll_interval:.0f} events/sec")
        click.echo()
        
    # Validate required parameters
    if not event_hub_namespace:
        click.echo("Error: Event Hub namespace is required. "
                  "Set EVENT_HUB_NAMESPACE environment variable or use --event-hub-namespace option.",
                  err=True)
        sys.exit(1)
        
    if not event_hub_name:
        click.echo("Error: Event Hub name is required. "
                  "Set EVENT_HUB_NAME environment variable or use --event-hub-name option.",
                  err=True)
        sys.exit(1)
        
    # Validate parameters
    if vehicles <= 0:
        click.echo("Error: Number of vehicles must be positive", err=True)
        sys.exit(1)
        
    if poll_interval <= 0:
        click.echo("Error: Poll interval must be positive", err=True)
        sys.exit(1)
        
    # Performance warnings and recommendations
    expected_throughput = vehicles / poll_interval
    if expected_throughput > 10000:
        click.echo(f"⚠️  WARNING: Very high throughput expected ({expected_throughput:.0f} events/sec)")
        click.echo("   Ensure your Event Hub has sufficient throughput units!")
        click.echo()
    elif expected_throughput > 5000:
        click.echo(f"🔥 HIGH THROUGHPUT: {expected_throughput:.0f} events/sec expected")
        click.echo()
        
    click.echo(f"Starting EXTREME PERFORMANCE vehicle event generator:")
    click.echo(f"  Agency: {agency}")
    click.echo(f"  Route: {route}")
    click.echo(f"  Vehicles: {vehicles:,}")
    click.echo(f"  Poll Interval: {poll_interval}s")
    click.echo(f"  Expected Throughput: {expected_throughput:,.0f} events/sec")
    click.echo(f"  Event Hub: {event_hub_name}")
    click.echo(f"  Event Hub Namespace: {event_hub_namespace}")
    click.echo(f"  Authentication: DefaultAzureCredential")
    click.echo(f"  High-Performance Mode: {'✅ ENABLED' if high_performance else '❌ DISABLED'}")
    click.echo()
    click.echo("Press Ctrl+C to stop...")
    
    # Run the feed
    asyncio.run(run_feed_async(
        event_hub_namespace=event_hub_namespace, 
        event_hub_name=event_hub_name,
        agency=agency, 
        route=route, 
        vehicles=vehicles, 
        poll_interval=poll_interval
    ))


async def run_feed_async(event_hub_namespace: str, event_hub_name: str, 
                        agency: str, route: str, vehicles: int, poll_interval: float):
    """Run the vehicle feed asynchronously."""
    try:
        # Create generator with DefaultAzureCredential
        generator = VehicleEventGenerator(
            event_hub_namespace=event_hub_namespace,
            event_hub_name=event_hub_name
        )
        
        async with generator:
            await generator.run_feed(
                agency=agency,
                route_tag=route if route != 'all-routes' else None,
                num_vehicles=vehicles,
                poll_interval=poll_interval
            )
    except KeyboardInterrupt:
        logger.info("Feed stopped by user")
    except Exception as e:
        logger.error(f"Feed failed: {e}")
        sys.exit(1)


@cli.command()
def agencies():
    """List available demo agencies."""
    click.echo("Available demo agencies:")
    click.echo("  demo-transit    Demo Transit Authority")


@cli.command()
@click.option('--agency', required=True, help='Transit agency identifier')
def routes(agency: str):
    """List available routes for an agency."""
    if agency == "demo-transit":
        click.echo("Available routes for demo-transit:")
        click.echo("  manhattan-loop     Manhattan Downtown Loop")
        click.echo("  brooklyn-express   Brooklyn Express")
        click.echo("  queens-connector   Queens Connector")
    else:
        click.echo(f"No routes found for agency: {agency}")


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()