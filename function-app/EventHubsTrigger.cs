using System.Text.Json;
using Azure.Messaging.EventHubs;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace function_app;

public class EventHubsTrigger
{
    private readonly ILogger<EventHubsTrigger> _logger;
    private readonly VehicleAnalyticsService _analyticsService;

    public EventHubsTrigger(ILogger<EventHubsTrigger> logger)
    {
        _logger = logger;
        _analyticsService = new VehicleAnalyticsService(logger);
    }

    [Function(nameof(EventHubsTrigger))]
    public async Task Run([EventHubTrigger("vehicle-events", Connection = "EventHubConnection")] EventData[] input)
    {
        var processedEvents = new List<VehiclePosition>();
        var failedEvents = 0;
        
        foreach (var message in input)
        {
            try
            {
                var messageBody = message.EventBody.ToString();

                // Parse the CloudEvent message
                var vehicleEvent = ParseVehicleEvent(messageBody);

                if (vehicleEvent != null)
                {
                    processedEvents.Add(vehicleEvent);
                }
                else
                {
                    failedEvents++;
                }
            }
            catch (Exception ex)
            {
                failedEvents++;
                _logger.LogWarning($"Error processing message: {ex.Message}");
            }
        }

        // Log summary of this execution
        _logger.LogInformation($"Processed {processedEvents.Count} events, {failedEvents} failed in batch of {input.Length}");

        // Process all events in batch for analytics
        if (processedEvents.Count > 0)
        {
            await _analyticsService.ProcessVehicleEvents(processedEvents);
        }
    }
    
    private VehiclePosition? ParseVehicleEvent(string message)
    {
        try
        {
            // Parse as JSON and extract the data payload
            using var document = JsonDocument.Parse(message);
            var root = document.RootElement;
            
            // The message should contain the vehicle position data directly
            // since we're sending the CloudEvent data payload to Event Hubs
            
            return new VehiclePosition
            {
                Agency = root.GetProperty("agency").GetString() ?? string.Empty,
                RouteTag = root.GetProperty("routeTag").GetString() ?? string.Empty,
                VehicleId = root.GetProperty("vehicleId").GetString() ?? string.Empty,
                Lat = root.GetProperty("lat").GetDouble(),
                Lon = root.GetProperty("lon").GetDouble(),
                Heading = root.GetProperty("heading").GetDouble(),
                SpeedKmHr = root.GetProperty("speedKmHr").GetDouble(),
                Timestamp = DateTime.Parse(root.GetProperty("timestamp").GetString() ?? DateTime.UtcNow.ToString()),
                Predictable = root.TryGetProperty("predictable", out var predictableElement) ? 
                    predictableElement.GetBoolean() : true
            };
        }
        catch (Exception ex)
        {
            _logger.LogError($"Failed to parse vehicle event: {ex.Message}");
            return null;
        }
    }
}

public class VehiclePosition
{
    public string Agency { get; set; } = string.Empty;
    public string RouteTag { get; set; } = string.Empty;
    public string VehicleId { get; set; } = string.Empty;
    public double Lat { get; set; }
    public double Lon { get; set; }
    public double Heading { get; set; }
    public double SpeedKmHr { get; set; }
    public DateTime Timestamp { get; set; }
    public bool Predictable { get; set; }
}