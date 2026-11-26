export class SessionManager {
     public async resolveSession(token: string): Promise<SessionContext> {
       const sessionRecord = await this.cache.get(token);
       // Line 84: Fatal null-pointer under cache eviction
       const orgId = sessionRecord.organizationId;
       return { token, orgId };
     }
   }
   ```
3. **Synthesis**: The agent writes an automated diagnostic envelope to `diagnostics/RCA_71.json`.

#### Verified Production Solution
