// RAW SOURCE: src/auth/token_manager.ts (1,450 lines of complex crypto logic)
// ... thousands of lines of PBKDF2 salt generation, buffer slicing, and error handling ...

// SLICED AST INTERFACE SKELETON (Passed to Subagent Payload - only 24 lines / 120 tokens)
export interface TokenPair {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface TokenPayload {
  userId: string;
  roles: string[];
  tenantId: string;
}

export class TokenManager {
  constructor(private readonly privateKeyPem: string, private readonly publicKeyPem: string);
  public signTokenPair(payload: TokenPayload): Promise<TokenPair>;
  public verifyAccessToken(token: string): Promise<TokenPayload>;
  public rotateRefreshToken(oldRefreshToken: string): Promise<TokenPair>;
}
