import { XMLParser } from "fast-xml-parser";

const parser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: "@_"
});

export class FeedDeltaDetector {
  private cache = new Map<string, { etag?: string; lastModified?: string; seenUrls: Set<string> }>();

  async pollSitemapForNewUrls(sitemapUrl: string): Promise<string[]> {
    const cached = this.cache.get(sitemapUrl) || { seenUrls: new Set<string>() };
    const headers: Record<string, string> = {};
    if (cached.etag) headers["If-None-Match"] = cached.etag;
    if (cached.lastModified) headers["If-Modified-Since"] = cached.lastModified;

    const res = await fetch(sitemapUrl, { headers });
    if (res.status === 304) {
      // Not Modified: Zero bandwidth consumed
      return [];
    }

    const newEtag = res.headers.get("etag") || undefined;
    const newLastModified = res.headers.get("last-modified") || undefined;
    const xmlText = await res.text();

    const parsed = parser.parse(xmlText);
    const urlEntries = parsed.urlset?.url || [];
    const currentUrls = (Array.isArray(urlEntries) ? urlEntries : [urlEntries]).map((u: any) => String(u.loc).trim());

    const discoveredNewUrls: string[] = [];
    for (const u of currentUrls) {
      if (!cached.seenUrls.has(u)) {
        cached.seenUrls.add(u);
        discoveredNewUrls.push(u);
      }
    }

    this.cache.set(sitemapUrl, {
      etag: newEtag,
      lastModified: newLastModified,
      seenUrls: cached.seenUrls
    });

    return discoveredNewUrls;
  }
}
