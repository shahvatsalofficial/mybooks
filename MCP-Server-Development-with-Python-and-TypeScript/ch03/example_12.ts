export class DebouncedNotificationManager {
  private pendingUris = new Set<string>();
  private timer: NodeJS.Timeout | null = null;

  constructor(private server: any, private delayMs: number = 300) {}

  public scheduleUpdate(uri: string) {
    this.pendingUris.add(uri);

    if (this.timer) clearTimeout(this.timer);

    this.timer = setTimeout(async () => {
      if (this.pendingUris.size > 20) {
        // High-volume batch: emit single catalog refresh
        await this.server.sendResourceListChanged();
      } else {
        // Low-volume batch: emit targeted URI updates
        for (const targetUri of this.pendingUris) {
          await this.server.sendResourceUpdated({ uri: targetUri });
        }
      }
      this.pendingUris.clear();
      this.timer = null;
    }, this.delayMs);
  }
}
