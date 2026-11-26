async function batchScrapePool(urls: string[], concurrency: number = 3) {
  const browser = await getBrowserInstance();
  const results: any[] = [];
  const queue = [...urls];

  async function worker() {
    while (queue.length > 0) {
      const url = queue.shift();
      if (!url) break;
      const page = await browser.newPage();
      try {
        await page.goto(url, { waitUntil: "domcontentloaded", timeout: 15000 });
        const title = await page.title();
        results.push({ url, title, status: "SUCCESS" });
      } catch (err: any) {
        results.push({ url, status: "FAILED", error: err.message });
      } finally {
        await page.close(); // Immediate memory reclamation
      }
    }
  }

  const workers = Array.from({ length: concurrency }, () => worker());
  await Promise.all(workers);
  return results;
}
