// vault_injector.ts — Ephemeral Dynamic Secret Injector for MCP
import http from 'http';

export interface EphemeralDbCredential {
    username: string;
    password: string;
    leaseId: string;
    leaseDurationSeconds: number;
}

export class VaultSecretInjector {
    constructor(
        private readonly vaultBaseUrl: string = 'http://127.0.0.1:8200',
        private readonly vaultToken: string
    ) {}

    /**
     * Issues dynamic read-only credentials from Vault database secrets engine
     */
    public async requestDatabaseCredential(roleName: string = 'analyst_readonly'): Promise<EphemeralDbCredential> {
        return new Promise((resolve, reject) => {
            const url = new URL(`${this.vaultBaseUrl}/v1/database/creds/${roleName}`);
            const req = http.request(
                {
                    hostname: url.hostname,
                    port: url.port,
                    path: url.pathname,
                    method: 'GET',
                    headers: {
                        'X-Vault-Token': this.vaultToken
                    },
                    timeout: 3000
                },
                (res) => {
                    let body = '';
                    res.on('data', (chunk) => (body += chunk));
                    res.on('end', () => {
                        try {
                            const parsed = JSON.parse(body);
                            if (parsed.errors) {
                                reject(new Error(`Vault error: ${parsed.errors.join(', ')}`));
                                return;
                            }

                            resolve({
                                username: parsed.data.username,
                                password: parsed.data.password,
                                leaseId: parsed.lease_id,
                                leaseDurationSeconds: parsed.lease_duration
                            });
                        } catch (err) {
                            reject(new Error(`Failed to parse Vault response: ${err}`));
                        }
                    });
                }
            );

            req.on('error', (err) => reject(new Error(`Vault network failure: ${err.message}`)));
            req.end();
        });
    }

    /**
     * Explicitly revokes a lease immediately upon tool completion
     */
    public async revokeLease(leaseId: string): Promise<void> {
        const payload = JSON.stringify({ lease_id: leaseId });
        return new Promise((resolve) => {
            const url = new URL(`${this.vaultBaseUrl}/v1/sys/leases/revoke`);
            const req = http.request(
                {
                    hostname: url.hostname,
                    port: url.port,
                    path: url.pathname,
                    method: 'PUT',
                    headers: {
                        'X-Vault-Token': this.vaultToken,
                        'Content-Type': 'application/json',
                        'Content-Length': Buffer.byteLength(payload)
                    }
                },
                (res) => {
                    res.resume();
                    resolve();
                }
            );

            req.on('error', (err) => {
                console.warn(`[VAULT] Warning: Failed to revoke lease ${leaseId}: ${err.message}`);
                resolve();
            });

            req.write(payload);
            req.end();
        });
    }
}
