/**
 * Recipe 03.3: Node.js Transform Stream for Progressive Tool Argument Extraction
 * Author: Vatsal Shah (Opportunity4u Press)
 * License: Apache-2.0
 */

import { Transform, TransformCallback } from 'stream';

export class ProgressiveToolJsonExtractor extends Transform {
  private rawAccumulator = '';
  private extractedToolName: string | null = null;
  private extractedPrimaryKey: string | null = null;

  constructor() {
    super({ objectMode: true });
  }

  _transform(chunk: any, encoding: BufferEncoding, callback: TransformCallback): void {
    const line = chunk.toString();
    
    if (line.includes('"type":"content_block_start"')) {
      try {
        const parsed = JSON.parse(line.replace(/^data:\s*/, ''));
        if (parsed.content_block?.type === 'tool_use') {
          this.extractedToolName = parsed.content_block.name;
          this.emit('tool_detected', { name: this.extractedToolName });
        }
      } catch (e) {}
    }

    if (line.includes('"type":"content_block_delta"')) {
      try {
        const parsed = JSON.parse(line.replace(/^data:\s*/, ''));
        if (parsed.delta?.type === 'input_json_delta') {
          const deltaChunk = parsed.delta.partial_json;
          this.rawAccumulator += deltaChunk;

          // Progressive Extraction: Inspect accumulator for primary identifier
          if (!this.extractedPrimaryKey && this.rawAccumulator.includes('"customer_id"')) {
            const match = this.rawAccumulator.match(/"customer_id"\s*:\s*"([^"]+)"/);
            if (match && match[1]) {
              this.extractedPrimaryKey = match[1];
              this.emit('early_key_extracted', { customerId: this.extractedPrimaryKey });
            }
          }
        }
      } catch (e) {}
    }

    // Forward original chunk downstream
    this.push(chunk);
    callback();
  }
}
