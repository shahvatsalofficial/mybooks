// merkle_audit.ts — Cryptographic Merkle Tree Audit Ledger for MCP
import crypto from 'crypto';

export interface AuditEvent {
    eventId: string;
    timestamp: string;
    stage: 'INGRESS' | 'POLICY' | 'SECRET_LEASE' | 'EXECUTION';
    data: Record<string, any>;
}

export class MerkleAuditLedger {
    /**
     * Generates an Ed25519 keypair for cryptographic signing
     */
    public static generateKeyPair(): { publicKey: string; privateKey: string } {
        const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519', {
            publicKeyEncoding: { type: 'spki', format: 'pem' },
            privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
        });
        return { publicKey, privateKey };
    }

    public static sha256(content: string | Buffer): Buffer {
        return crypto.createHash('sha256').update(content).digest();
    }

    /**
     * Builds Merkle Root from an array of 4 atomic audit events
     */
    public static computeMerkleRoot(events: AuditEvent[]): {
        rootHashHex: string;
        leafHashesHex: string[];
    } {
        if (events.length === 0) {
            throw new Error('Cannot construct Merkle tree with zero events.');
        }

        // 1. Hash leaves
        const leafHashes = events.map((ev) => this.sha256(JSON.stringify(ev)));

        // 2. Pairwise reduction
        let currentLevel = leafHashes;
        while (currentLevel.length > 1) {
            const nextLevel: Buffer[] = [];
            for (let i = 0; i < currentLevel.length; i += 2) {
                const left = currentLevel[i];
                const right = i + 1 < currentLevel.length ? currentLevel[i + 1] : left; // Duplicate odd node
                const combined = Buffer.concat([left, right]);
                nextLevel.push(this.sha256(combined));
            }
            currentLevel = nextLevel;
        }

        return {
            rootHashHex: currentLevel[0].toString('hex'),
            leafHashesHex: leafHashes.map((h) => h.toString('hex'))
        };
    }

    /**
     * Signs the Merkle Root with the Gateway's Ed25519 Private Key
     */
    public static signRoot(rootHashHex: string, privateKeyPem: string): string {
        const rootBuffer = Buffer.from(rootHashHex, 'hex');
        const signature = crypto.sign(null, rootBuffer, privateKeyPem);
        return signature.toString('hex');
    }

    /**
     * Verifies the Merkle Root signature using the Public Key
     */
    public static verifyRootSignature(rootHashHex: string, signatureHex: string, publicKeyPem: string): boolean {
        const rootBuffer = Buffer.from(rootHashHex, 'hex');
        const signatureBuffer = Buffer.from(signatureHex, 'hex');
        return crypto.verify(null, rootBuffer, publicKeyPem, signatureBuffer);
    }
}
