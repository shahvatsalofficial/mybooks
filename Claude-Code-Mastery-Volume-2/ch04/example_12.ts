import dns from "dns/promises";
import net from "net";

function isPrivateIp(ip: string): boolean {
  if (net.isIPv4(ip)) {
    const parts = ip.split(".").map(Number);
    if (parts[0] === 10) return true; // 10.0.0.0/8
    if (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) return true; // 172.16.0.0/12
    if (parts[0] === 192 && parts[1] === 168) return true; // 192.168.0.0/16
    if (parts[0] === 127) return true; // Loopback
    if (parts[0] === 169 && parts[1] === 254) return true; // Link-local / Cloud Metadata
    if (parts[0] === 0) return true;
  } else if (net.isIPv6(ip)) {
    if (ip === "::1" || ip.startsWith("fc") || ip.startsWith("fd") || ip.startsWith("fe80")) return true;
  }
  return false;
}

export async function validateSafeEgressUrl(targetUrl: string): Promise<string> {
  const parsed = new URL(targetUrl);
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error(`SECURITY_VIOLATION: Prohibited protocol '${parsed.protocol}'. Only HTTP/HTTPS allowed.`);
  }

  const addresses = await dns.resolve(parsed.hostname);
  for (const addr of addresses) {
    if (isPrivateIp(addr)) {
      throw new Error(`SSRF_VIOLATION: Target host '${parsed.hostname}' resolves to private/internal IP: ${addr}`);
    }
  }

  return targetUrl;
}
