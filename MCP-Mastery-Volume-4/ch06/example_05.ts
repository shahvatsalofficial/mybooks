export interface SearchHit {
  title: string;
  url: string;
  snippet: string;
  source: "brave" | "tavily";
}

export class MultiSearchAggregator {
  private braveApiKey: string;
  private tavilyApiKey: string;

  constructor() {
    this.braveApiKey = process.env.BRAVE_SEARCH_API_KEY || "";
    this.tavilyApiKey = process.env.TAVILY_API_KEY || "";
  }

  // Canonicalize URL to eliminate tracking duplicates
  static cleanUrl(rawUrl: string): string {
    try {
      const u = new URL(rawUrl);
      u.searchParams.delete("utm_source");
      u.searchParams.delete("utm_medium");
      u.searchParams.delete("utm_campaign");
      u.searchParams.delete("utm_term");
      u.searchParams.delete("utm_content");
      u.hash = "";
      return u.toString();
    } catch {
      return rawUrl;
    }
  }

  async searchBrave(query: string, count: number = 5): Promise<SearchHit[]> {
    if (!this.braveApiKey) return [];
    const url = `https://api.search.brave.com/res/v1/web/search?q=${encodeURIComponent(query)}&count=${count}`;
    const res = await fetch(url, {
      headers: { "X-Subscription-Token": this.braveApiKey, Accept: "application/json" }
    });
    const data = await res.json();
    return (data.web?.results || []).map((r: any) => ({
      title: r.title,
      url: MultiSearchAggregator.cleanUrl(r.url),
      snippet: r.description,
      source: "brave" as const
    }));
  }

  async searchTavily(query: string, maxResults: number = 5): Promise<SearchHit[]> {
    if (!this.tavilyApiKey) return [];
    const url = "https://api.tavily.com/search";
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: this.tavilyApiKey, query, max_results: maxResults })
    });
    const data = await res.json();
    return (data.results || []).map((r: any) => ({
      title: r.title,
      url: MultiSearchAggregator.cleanUrl(r.url),
      snippet: r.content,
      source: "tavily" as const
    }));
  }

  // Execute Parallel Search with Deduplication
  async aggregateSearch(query: string, maxResults: number = 8): Promise<SearchHit[]> {
    const [braveHits, tavilyHits] = await Promise.all([
      this.searchBrave(query, maxResults).catch(() => []),
      this.searchTavily(query, maxResults).catch(() => [])
    ]);

    const seenUrls = new Set<string>();
    const unified: SearchHit[] = [];

    // Interleave hits to balance sources
    const maxLength = Math.max(braveHits.length, tavilyHits.length);
    for (let i = 0; i < maxLength; i++) {
      if (braveHits[i] && !seenUrls.has(braveHits[i].url)) {
        seenUrls.add(braveHits[i].url);
        unified.push(braveHits[i]);
      }
      if (tavilyHits[i] && !seenUrls.has(tavilyHits[i].url)) {
        seenUrls.add(tavilyHits[i].url);
        unified.push(tavilyHits[i]);
      }
      if (unified.length >= maxResults) break;
    }

    return unified;
  }
}
