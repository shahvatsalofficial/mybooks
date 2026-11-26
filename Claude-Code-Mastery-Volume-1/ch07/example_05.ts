// AST Mutation inside src/optimizer/RouteOptimizer.ts
- const waypoint = stop.waypointConfig.calculateDynamicWaypoint();
+ const waypoint = stop.waypointConfig?.calculateDynamicWaypoint() 
+   ?? this.fallbackWaypointResolver.resolveDefault(stop.coordinates, this.clusterConfig);
