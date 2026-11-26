import { RouteOptimizer } from '../../src/optimizer/RouteOptimizer';
import { DeliveryBatchDTO, FreightType } from '../../src/types/dispatch';

describe('Production Incident RCA: EVT-98412', () => {
  it('should cleanly handle delivery batches with unassigned refrigerated waypoints without throwing TypeError', async () => {
    const optimizer = new RouteOptimizer();
    
    // Exact minimal synthetic reproduction payload reconstructed from Sentry breadcrumbs
    const maliciousPayload: DeliveryBatchDTO = {
      batchId: 'batch_synthetic_98412',
      freightType: FreightType.REFRIGERATED_MULTI_STOP,
      stops: [
        {
          stopId: 'stop_01',
          coordinates: { lat: 37.7749, lng: -122.4194 },
          waypointConfig: undefined // The edge-case trigger: unassigned config under high-concurrency re-routing
        }
      ]
    };

    // Execution must not throw an unhandled TypeError
    await expect(optimizer.processDeliveryBatch(maliciousPayload))
      .resolves
      .toBeDefined();
  });
});
