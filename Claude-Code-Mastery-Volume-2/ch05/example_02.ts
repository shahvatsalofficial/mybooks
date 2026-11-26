export class LoopDetector {
  private history: string[] = [];

  public recordState(fileSnapshotHash: string): void {
    if (this.history.includes(fileSnapshotHash)) {
      throw new Error(
        "CIRCUIT_BREAKER_TRIPPED: Oscillation detected. The agent is repeating previously failed state changes."
      );
    }
    this.history.push(fileSnapshotHash);
    if (this.history.length > 10) this.history.shift();
  }
}
