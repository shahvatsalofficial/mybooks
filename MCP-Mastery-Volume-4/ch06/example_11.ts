function stripTrackingParameters(rawUrl: string): string {
  try {
    const url = new URL(rawUrl);
    const trackingParams = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid", "msclkid"];
    trackingParams.forEach((param) => url.searchParams.delete(param));
    return url.toString();
  } catch {
    return rawUrl;
  }
}
