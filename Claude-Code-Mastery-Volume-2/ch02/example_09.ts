server.resource(
  "paginated-audit-log",
  new ResourceTemplate("audit://events{?cursor,limit}", { list: undefined }),
  { description: "Streams historical security audit events with cursor pagination" },
  async (uri, { cursor, limit }) => {
    const pageLimit = Math.min(parseInt(limit as string) || 50, 200);
    const { records, nextCursor } = await fetchAuditPage(cursor as string, pageLimit);

    return {
      contents: [{
        uri: uri.href,
        text: JSON.stringify(records, null, 2),
        mimeType: "application/json"
      }],
      _meta: {
        nextCursor: nextCursor || null
      }
    };
  }
);
