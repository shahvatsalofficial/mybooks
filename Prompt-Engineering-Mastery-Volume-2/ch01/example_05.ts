import { Transform, TransformCallback } from 'stream';

export interface StreamTelemetryOptions {
  onReasoningChunk?: (chunk: string) => void;
  onReasoningComplete?: (fullTrace: string) => void;
}

export class StreamingScratchpadFilter extends Transform {
  private buffer: string = '';
  private inScratchpad: boolean = false;
  private reasoningAccumulator: string = '';
  private readonly openTag = '<scratchpad>';
  private readonly closeTag = '</scratchpad>';
  private options: StreamTelemetryOptions;

  constructor(options: StreamTelemetryOptions = {}) {
    super({ encoding: 'utf8' });
    this.options = options;
  }

  _transform(chunk: any, encoding: BufferEncoding, callback: TransformCallback): void {
    const text = typeof chunk === 'string' ? chunk : chunk.toString('utf8');
    this.buffer += text;

    let processed = true;
    while (processed) {
      processed = false;

      if (!this.inScratchpad) {
        const openIdx = this.buffer.indexOf(this.openTag);
        if (openIdx !== -1) {
          // Emit content before the opening tag to client
          if (openIdx > 0) {
            this.push(this.buffer.slice(0, openIdx));
          }
          this.inScratchpad = true;
          this.buffer = this.buffer.slice(openIdx + this.openTag.length);
          processed = true;
        } else {
          // Guard against partial open tag split across chunk boundaries
          const partialMatchLength = this.getPartialMatch(this.buffer, this.openTag);
          if (partialMatchLength > 0) {
            const safeToEmit = this.buffer.slice(0, -partialMatchLength);
            if (safeToEmit.length > 0) {
              this.push(safeToEmit);
              this.buffer = this.buffer.slice(-partialMatchLength);
            }
          } else {
            this.push(this.buffer);
            this.buffer = '';
          }
        }
      } else {
        const closeIdx = this.buffer.indexOf(this.closeTag);
        if (closeIdx !== -1) {
          const reasoningPiece = this.buffer.slice(0, closeIdx);
          this.reasoningAccumulator += reasoningPiece;
          if (this.options.onReasoningChunk) {
            this.options.onReasoningChunk(reasoningPiece);
          }
          if (this.options.onReasoningComplete) {
            this.options.onReasoningComplete(this.reasoningAccumulator);
          }

          this.inScratchpad = false;
          this.buffer = this.buffer.slice(closeIdx + this.closeTag.length);
          processed = true;
        } else {
          // Inside scratchpad: buffer for telemetry, do NOT push to client
          const partialMatchLength = this.getPartialMatch(this.buffer, this.closeTag);
          if (partialMatchLength > 0) {
            const safeReasoning = this.buffer.slice(0, -partialMatchLength);
            this.reasoningAccumulator += safeReasoning;
            if (this.options.onReasoningChunk && safeReasoning.length > 0) {
              this.options.onReasoningChunk(safeReasoning);
            }
            this.buffer = this.buffer.slice(-partialMatchLength);
          } else {
            this.reasoningAccumulator += this.buffer;
            if (this.options.onReasoningChunk && this.buffer.length > 0) {
              this.options.onReasoningChunk(this.buffer);
            }
            this.buffer = '';
          }
        }
      }
    }

    callback();
  }

  _flush(callback: TransformCallback): void {
    if (!this.inScratchpad && this.buffer.length > 0) {
      this.push(this.buffer);
    }
    callback();
  }

  private getPartialMatch(str: string, target: string): number {
    for (let i = 1; i < target.length; i++) {
      if (str.endsWith(target.slice(0, i))) {
        return i;
      }
    }
    return 0;
  }
}
