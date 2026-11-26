/**
 * Real-Time DNS Entropy Exfiltration Filter
 * Author: Vatsal Shah, Lead Enterprise AI Architect
 */

export class DnsEntropyFilter {
    private maxLabelEntropy: number = 3.95;
    private maxLabelLength: number = 35;

    public calculateShannonEntropy(label: string): number {
        const len = label.length;
        if (len === 0) return 0;

        const frequencies = new Map<string, number>();
        for (const char of label) {
            frequencies.set(char, (frequencies.get(char) || 0) + 1);
        }

        let entropy = 0;
        for (const count of frequencies.values()) {
            const p = count / len;
            entropy -= p * Math.log2(p);
        }

        return entropy;
    }

    public inspectDnsQuery(hostname: string): { isAllowed: boolean; reason?: string } {
        const labels = hostname.split('.');

        // Exclude top-level domain and domain root
        for (const label of labels.slice(0, -2)) {
            if (label.length > this.maxLabelLength) {
                return {
                    isAllowed: false,
                    reason: `DNS label length (${label.length}) exceeds security threshold (${this.maxLabelLength})`
                };
            }

            const entropy = this.calculateShannonEntropy(label);
            if (entropy > this.maxLabelEntropy) {
                return {
                    isAllowed: false,
                    reason: `High Shannon entropy (${entropy.toFixed(2)} bits/char) indicates DNS tunneling exfiltration`
                };
            }
        }

        return { isAllowed: true };
    }
}
