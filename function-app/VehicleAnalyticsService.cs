using Microsoft.Extensions.Logging;
using System.Text.Json;

namespace function_app;

public class VehicleAnalyticsService
{
    private readonly ILogger _logger;

    // Define some geofenced zones for demonstration
    private readonly List<GeofenceZone> _geofenceZones = new()
    {
        new GeofenceZone("manhattan-downtown", "Manhattan Downtown", 40.7128, -74.0060, 2.0),
        new GeofenceZone("central-park", "Central Park Area", 40.7829, -73.9654, 1.5),
        new GeofenceZone("brooklyn-heights", "Brooklyn Heights", 40.6962, -73.9442, 1.0),
        new GeofenceZone("queens-plaza", "Queens Plaza", 40.7505, -73.8370, 1.2)
    };

    // In-memory storage for demo purposes (in production, use Redis/Cosmos DB)
    private static readonly Dictionary<string, VehicleState> _vehicleStates = new();
    private static readonly Dictionary<string, List<RouteMetrics>> _routeMetrics = new();

    public VehicleAnalyticsService(ILogger logger)
    {
        _logger = logger;
    }

    public async Task ProcessVehicleEvents(List<VehiclePosition> events)
    {
        var tasks = new List<Task>();

        foreach (var vehicleEvent in events)
        {
            // Process each event concurrently
            tasks.Add(ProcessSingleVehicleEvent(vehicleEvent));
        }

        await Task.WhenAll(tasks);

        // Generate batch analytics
        await GenerateBatchAnalytics(events);
    }

    private async Task ProcessSingleVehicleEvent(VehiclePosition vehicleEvent)
    {
        try
        {
            // 1. Update vehicle state and detect state changes
            await UpdateVehicleState(vehicleEvent);

            // 2. Check geofence violations/entries
            await CheckGeofences(vehicleEvent);

            // 3. Analyze speed and performance
            await AnalyzeVehiclePerformance(vehicleEvent);

            // 4. Generate predictions (simplified)
            await GeneratePredictions(vehicleEvent);

        }
        catch (Exception ex)
        {
            _logger.LogError($"Error processing vehicle event for {vehicleEvent.VehicleId}: {ex.Message}");
        }
    }

    private async Task UpdateVehicleState(VehiclePosition vehicleEvent)
    {
        var vehicleKey = $"{vehicleEvent.Agency}:{vehicleEvent.VehicleId}";
        var previousState = _vehicleStates.TryGetValue(vehicleKey, out var state) ? state : null;

        var newState = new VehicleState
        {
            VehicleId = vehicleEvent.VehicleId,
            Agency = vehicleEvent.Agency,
            RouteTag = vehicleEvent.RouteTag,
            LastPosition = new GeoPosition(vehicleEvent.Lat, vehicleEvent.Lon),
            LastSpeed = vehicleEvent.SpeedKmHr,
            LastHeading = vehicleEvent.Heading,
            LastUpdateTime = vehicleEvent.Timestamp,
            PreviousPosition = previousState?.LastPosition
        };

        _vehicleStates[vehicleKey] = newState;

        // Detect significant state changes
        if (previousState != null)
        {
            await DetectStateChanges(previousState, newState);
        }

        _logger.LogDebug($"Updated state for vehicle {vehicleKey}");
    }

    private async Task DetectStateChanges(VehicleState previous, VehicleState current)
    {
        // Route change detection
        if (previous.RouteTag != current.RouteTag)
        {
            _logger.LogInformation($"🚌 Vehicle {current.VehicleId} changed routes: {previous.RouteTag} → {current.RouteTag}");
        }

        // Stopped vehicle detection (speed < 5 km/h for demo)
        if (previous.LastSpeed > 5 && current.LastSpeed <= 5)
        {
            _logger.LogInformation($"🛑 Vehicle {current.VehicleId} has stopped (speed: {current.LastSpeed:F1} km/h)");
        }

        // Vehicle started moving
        if (previous.LastSpeed <= 5 && current.LastSpeed > 5)
        {
            _logger.LogInformation($"🚀 Vehicle {current.VehicleId} started moving (speed: {current.LastSpeed:F1} km/h)");
        }

        // Speed violation detection (> 50 km/h in urban area)
        if (current.LastSpeed > 50)
        {
            _logger.LogWarning($"⚠️ Speed violation: Vehicle {current.VehicleId} traveling at {current.LastSpeed:F1} km/h");
        }

        await Task.CompletedTask;
    }

    private async Task CheckGeofences(VehiclePosition vehicleEvent)
    {
        var vehiclePosition = new GeoPosition(vehicleEvent.Lat, vehicleEvent.Lon);
        
        foreach (var zone in _geofenceZones)
        {
            var distance = CalculateDistance(vehiclePosition, zone.Center);
            var isInZone = distance <= zone.RadiusKm;
            
            var vehicleKey = $"{vehicleEvent.Agency}:{vehicleEvent.VehicleId}";
            var stateKey = $"{vehicleKey}:geofence:{zone.Id}";
            
            // Check if this is a zone entry/exit event
            var wasInZone = _vehicleStates.TryGetValue(stateKey, out var geoState) && 
                           geoState.LastUpdateTime > DateTime.UtcNow.AddMinutes(-5); // Consider stale after 5 min

            if (isInZone && !wasInZone)
            {
                _logger.LogInformation($"📍 Vehicle {vehicleEvent.VehicleId} entered {zone.Name}");
                
                // Store geofence state
                _vehicleStates[stateKey] = new VehicleState 
                { 
                    VehicleId = vehicleEvent.VehicleId,
                    LastUpdateTime = vehicleEvent.Timestamp 
                };
            }
            else if (!isInZone && wasInZone)
            {
                _logger.LogInformation($"📍 Vehicle {vehicleEvent.VehicleId} exited {zone.Name}");
                _vehicleStates.Remove(stateKey);
            }
        }

        await Task.CompletedTask;
    }

    private async Task AnalyzeVehiclePerformance(VehiclePosition vehicleEvent)
    {
        var routeKey = $"{vehicleEvent.Agency}:{vehicleEvent.RouteTag}";
        
        if (!_routeMetrics.ContainsKey(routeKey))
        {
            _routeMetrics[routeKey] = new List<RouteMetrics>();
        }

        var metrics = new RouteMetrics
        {
            VehicleId = vehicleEvent.VehicleId,
            RouteTag = vehicleEvent.RouteTag,
            Speed = vehicleEvent.SpeedKmHr,
            Position = new GeoPosition(vehicleEvent.Lat, vehicleEvent.Lon),
            Timestamp = vehicleEvent.Timestamp
        };

        _routeMetrics[routeKey].Add(metrics);

        // Keep only recent metrics (last 100 entries per route)
        if (_routeMetrics[routeKey].Count > 100)
        {
            _routeMetrics[routeKey] = _routeMetrics[routeKey]
                .OrderByDescending(m => m.Timestamp)
                .Take(100)
                .ToList();
        }

        await Task.CompletedTask;
    }

    private async Task GeneratePredictions(VehiclePosition vehicleEvent)
    {
        // Simplified ETA calculation based on current speed and distance
        var vehicleKey = $"{vehicleEvent.Agency}:{vehicleEvent.VehicleId}";
        
        if (_vehicleStates.TryGetValue(vehicleKey, out var vehicleState) && 
            vehicleState.PreviousPosition != null)
        {
            var currentPos = new GeoPosition(vehicleEvent.Lat, vehicleEvent.Lon);
            var distance = CalculateDistance(vehicleState.PreviousPosition, currentPos);
            var timeElapsed = (vehicleEvent.Timestamp - vehicleState.LastUpdateTime).TotalHours;
            
            if (timeElapsed > 0 && distance > 0)
            {
                var calculatedSpeed = distance / timeElapsed;
                
                _logger.LogDebug($"🔮 Vehicle {vehicleEvent.VehicleId} calculated speed: {calculatedSpeed:F1} km/h " +
                               $"(reported: {vehicleEvent.SpeedKmHr:F1} km/h)");
                
                // Example: Predict arrival at next major zone
                var nearestZone = _geofenceZones
                    .Select(z => new { Zone = z, Distance = CalculateDistance(currentPos, z.Center) })
                    .OrderBy(x => x.Distance)
                    .FirstOrDefault();

                if (nearestZone != null && vehicleEvent.SpeedKmHr > 5)
                {
                    var etaMinutes = (nearestZone.Distance / vehicleEvent.SpeedKmHr) * 60;
                    
                    // Only log ETAs that are significant (< 10 minutes) to reduce noise
                    if (etaMinutes < 10 && etaMinutes > 1)
                    {
                        _logger.LogInformation($"🕐 Vehicle {vehicleEvent.VehicleId} ETA to {nearestZone.Zone.Name}: {etaMinutes:F0} minutes");
                    }
                }
            }
        }

        await Task.CompletedTask;
    }

    private async Task GenerateBatchAnalytics(List<VehiclePosition> events)
    {
        var routeGroups = events.GroupBy(e => $"{e.Agency}:{e.RouteTag}");
        var totalVehicles = events.Select(e => $"{e.Agency}:{e.VehicleId}").Distinct().Count();
        var totalEvents = events.Count;
        var congestionCount = 0;
        
        foreach (var routeGroup in routeGroups)
        {
            var routeEvents = routeGroup.ToList();
            var avgSpeed = routeEvents.Average(e => e.SpeedKmHr);
            var vehicleCount = routeEvents.Select(e => e.VehicleId).Distinct().Count();
            
            // Only log route details occasionally to reduce noise
            if (vehicleCount > 5) // Only log routes with significant activity
            {
                _logger.LogInformation($"📊 Route {routeGroup.Key}: {vehicleCount} vehicles, avg speed: {avgSpeed:F1} km/h");
            }
            
            // Detect potential traffic issues
            if (avgSpeed < 15)
            {
                congestionCount++;
                _logger.LogWarning($"🚨 Congestion detected on route {routeGroup.Key} (avg speed: {avgSpeed:F1} km/h)");
            }
        }

        // Enhanced system summary with performance metrics
        var avgOverallSpeed = events.Average(e => e.SpeedKmHr);
        var activeRoutes = routeGroups.Count();
        
        _logger.LogInformation(
            $"📈 BATCH SUMMARY: {totalEvents} events | {totalVehicles} vehicles | {activeRoutes} routes | " +
            $"avg speed: {avgOverallSpeed:F1} km/h | {congestionCount} congested routes"
        );

        await Task.CompletedTask;
    }

    private static double CalculateDistance(GeoPosition pos1, GeoPosition pos2)
    {
        // Haversine formula for distance calculation
        const double R = 6371; // Earth's radius in km
        
        var lat1Rad = pos1.Latitude * Math.PI / 180;
        var lat2Rad = pos2.Latitude * Math.PI / 180;
        var deltaLatRad = (pos2.Latitude - pos1.Latitude) * Math.PI / 180;
        var deltaLonRad = (pos2.Longitude - pos1.Longitude) * Math.PI / 180;

        var a = Math.Sin(deltaLatRad / 2) * Math.Sin(deltaLatRad / 2) +
                Math.Cos(lat1Rad) * Math.Cos(lat2Rad) *
                Math.Sin(deltaLonRad / 2) * Math.Sin(deltaLonRad / 2);
        
        var c = 2 * Math.Atan2(Math.Sqrt(a), Math.Sqrt(1 - a));
        
        return R * c;
    }
}

// Supporting data models
public record GeoPosition(double Latitude, double Longitude);

public record GeofenceZone(string Id, string Name, double Latitude, double Longitude, double RadiusKm)
{
    public GeoPosition Center => new(Latitude, Longitude);
}

public class VehicleState
{
    public string VehicleId { get; set; } = string.Empty;
    public string Agency { get; set; } = string.Empty;
    public string RouteTag { get; set; } = string.Empty;
    public GeoPosition? LastPosition { get; set; }
    public GeoPosition? PreviousPosition { get; set; }
    public double LastSpeed { get; set; }
    public double LastHeading { get; set; }
    public DateTime LastUpdateTime { get; set; }
}

public class RouteMetrics
{
    public string VehicleId { get; set; } = string.Empty;
    public string RouteTag { get; set; } = string.Empty;
    public double Speed { get; set; }
    public GeoPosition Position { get; set; } = new(0, 0);
    public DateTime Timestamp { get; set; }
}