import { Transform } from 'stream';

export class SecretSanitizer extends Transform {
  private secretPatterns = [
    /AKIA[0-9A-Z]{16}/g,
    /(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36}/g,
    /Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*/g,
    /postgres:\/\/[^:]+:([^@]+)@/g
  ];

  _transform(chunk: Buffer, encoding: string, callback: () => void) {
    let text = chunk.toString('utf8');
    for (const pattern of this.secretPatterns) {
      text = text.replace(pattern, '[REDACTED_SECRET]');
    }
    this.push(Buffer.from(text, 'utf8'));
    callback();
  }
}
