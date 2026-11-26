async function getDeduplicatedEvents(namespace: string) {
  const res = await coreApi.listNamespacedEvent({ namespace });
  const counts: Record<string, { count: number; sampleMessage: string; lastSeen: string }> = {};

  for (const e of res.items) {
    const key = `${e.involvedObject.name}:${e.reason}`;
    if (!counts[key]) {
      counts[key] = { count: e.count || 1, sampleMessage: e.message || "", lastSeen: e.lastTimestamp?.toISOString() || "" };
    } else {
      counts[key].count += e.count || 1;
    }
  }
  return counts;
}
