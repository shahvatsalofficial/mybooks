function BaseTelemetryRecord() {}
BaseTelemetryRecord.prototype.sharedMetrics = new Array(500000).fill("SYSTEM_OK");

function ActiveSensorNode(sensorId) {
    this.sensorId = sensorId;
    // Overriding the shared array instance to modify it locally
    this.sharedMetrics = [...BaseTelemetryRecord.prototype.sharedMetrics, sensorId];
}
Object.setPrototypeOf(ActiveSensorNode.prototype, BaseTelemetryRecord.prototype);

const nodesList = [];
for (let i = 0; i < 1000; i++) {
    nodesList.push(new ActiveSensorNode(`SN_${i}`));
}
