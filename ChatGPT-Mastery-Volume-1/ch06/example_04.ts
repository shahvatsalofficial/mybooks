import axios from 'axios';
import { Request, Response, NextFunction } from 'express';

interface TokenCache {
  accessToken: string;
  expiresAt: number;
  refreshToken: string;
}

const tokenStore = new Map<string, TokenCache>();

export async function oauthRefreshInterceptor(req: Request, res: Response, next: NextFunction) {
  const userId = req.headers['x-user-id'] as string;
  const userTokens = tokenStore.get(userId);

  if (!userTokens) {
    return res.status(401).json({ error: 'No active session. Please authenticate via OAuth2.' });
  }

  // If token expires in less than 60 seconds, execute proactive refresh
  if (Date.now() >= userTokens.expiresAt - 60000) {
    try {
      console.log(`[AUTH REFRESH] Refreshing expired access token for user ${userId}...`);
      const refreshRes = await axios.post('https://auth.suhana-enterprises.com/oauth/token', {
        grant_type: 'refresh_token',
        client_id: process.env.OAUTH_CLIENT_ID,
        client_secret: process.env.OAUTH_CLIENT_SECRET,
        refresh_token: userTokens.refreshToken
      });

      userTokens.accessToken = refreshRes.data.access_token;
      userTokens.expiresAt = Date.now() + (refreshRes.data.expires_in * 1000);
      tokenStore.set(userId, userTokens);
      console.log(`[AUTH REFRESH SUCCESS] Token refreshed successfully.`);
    } catch (refreshErr) {
      return res.status(401).json({ error: 'Refresh token expired or revoked. Re-login required.' });
    }
  }

  req.headers['authorization'] = `Bearer ${userTokens.accessToken}`;
  next();
}
