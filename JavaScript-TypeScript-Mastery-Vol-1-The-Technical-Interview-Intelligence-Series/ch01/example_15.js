function BaseTelemetryRecord() {}
// Retain the core baseline list read-only in the shared prototype context
BaseTelemetryRecord.prototype.sharedMetrics = new Array(500000).fill("SYSTEM_OK");

// Resolve lookup metrics by dynamically accessing prototype properties at query time
BaseTelemetryRecord.prototype.getMetricsSummary = function(localId) {
    // Simply delegate reading, avoiding duplicating the base array in memory
    return {
        baseCount: this.sharedMetrics.length,
        nodeIdentifier: localId
    };
};

function ActiveSensorNode(sensorId) {
    this.sensorId = sensorId;
}
Object.setPrototypeOf(ActiveSensorNode.prototype, BaseTelemetryRecord.prototype);

const nodesList = [];
for (let i = 0; i < 1000; i++) {
    nodesList.push(new ActiveSensorNode(`SN_${i}`));
}
// Memory footprint drops from ~4.2GB to <10MB!
