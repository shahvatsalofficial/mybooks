/**
 * Recipe 05.2: Real-Time Dynamic Resource Subscription Provider
 * Author: Vatsal Shah (Opportunity4u Press)
 * License: Apache-2.0
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import * as fs from 'fs';
import * as path from 'path';

export function registerLiveConfigResource(server: McpServer, configFilePath: string) {
  const resourceUri = 'config://system/live-settings';

  // Expose readable resource
  server.resource(
    'live-settings',
    resourceUri,
    async (uri) => {
      const content = fs.readFileSync(configFilePath, 'utf-8');
      return {
        contents: [
          {
            uri: uri.href,
            text: content,
            mimeType: 'application/json',
          },
        ],
      };
    }
  );

  // Watch for filesystem changes and notify clients
  fs.watch(configFilePath, (eventType) => {
    if (eventType === 'change') {
      console.error(`[FS WATCHER] Detected change in ${configFilePath}. Emitting update notification.`);
      server.server.notification({
        method: 'notifications/resources/updated',
        params: { uri: resourceUri },
      });
    }
  });
}
