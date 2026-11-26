/**
 * Enterprise Autonomous Brand Asset Generation & Optimization Pipeline
 * Target: Node.js 20+ / TypeScript 5.0+ / OpenAI SDK v4.50+ / Sharp 0.33+
 */

import OpenAI from 'openai';
import sharp from 'sharp';
import * as fs from 'fs';
import * as path from 'path';
import axios from 'axios';

export interface BrandAssetRequest {
  assetId: string;
  conceptPrompt: string;
  aspectRatio: '1:1' | '16:9' | '9:16';
  quality: 'standard' | 'hd';
  brandTheme: {
    primaryHex: string;
    secondaryHex: string;
    canvasHex: string;
    masterStyleDirective: string;
  };
  outputDirectory: string;
  watermarkSvgPath?: string;
}

export interface GeneratedAssetMetadata {
  assetId: string;
  originalUrl: string;
  revisedPrompt: string;
  localHighResPngPath: string;
  localWebpOptimizedPath: string;
  width: number;
  height: number;
  fileSizeBytes: number;
  generationTimestamp: string;
}

export class BrandAssetPipeline {
  private openai: OpenAI;

  constructor(apiKey: string) {
    this.openai = new OpenAI({ apiKey });
  }

  /**
   * Compiles user prompt with immutable brand guidelines
   */
  private compileBrandPrompt(request: BrandAssetRequest): string {
    return `[BRAND_VISUAL_STANDARD: ENTERPRISE_PORTFOLIO]
${request.brandTheme.masterStyleDirective}

[COLOR_CONSTRAINTS]
Primary Accent: ${request.brandTheme.primaryHex}
Secondary Accent: ${request.brandTheme.secondaryHex}
Background Canvas: ${request.brandTheme.canvasHex}

[SCENE_SPECIFICATION]
${request.conceptPrompt}

[EXECUTION_RULES]
100% text-free. Strictly zero letters, words, numerals, or watermarks.
High-contrast studio lighting, sharp focus, professional industrial design aesthetic.`;
  }

  /**
   * Translates aspect ratio enum into DALL-E 3 API dimensions
   */
  private resolveDimensions(ratio: '1:1' | '16:9' | '9:16'): '1024x1024' | '1792x1024' | '1024x1792' {
    switch (ratio) {
      case '16:9':
        return '1792x1024';
      case '9:16':
        return '1024x1792';
      case '1:1':
      default:
        return '1024x1024';
    }
  }

  /**
   * Executes end-to-end asset generation, download, watermark overlay, and multi-format export
   */
  public async generateAndProcessAsset(request: BrandAssetRequest): Promise<GeneratedAssetMetadata> {
    if (!fs.existsSync(request.outputDirectory)) {
      fs.mkdirSync(request.outputDirectory, { recursive: true });
    }

    const compiledPrompt = this.compileBrandPrompt(request);
    const size = this.resolveDimensions(request.aspectRatio);

    console.log(`[DALL-E 3 ENGINE] Dispatching request for Asset: ${request.assetId} (${size}, ${request.quality})...`);

    // 1. Dispatch API call to OpenAI
    const response = await this.openai.images.generate({
      model: 'dall-e-3',
      prompt: compiledPrompt,
      n: 1,
      size: size,
      quality: request.quality,
      response_format: 'url'
    });

    const imageData = response.data[0];
    const imageUrl = imageData.url;
    const revisedPrompt = imageData.revised_prompt || compiledPrompt;

    if (!imageUrl) {
      throw new Error(`[FATAL] OpenAI API did not return an image URL for asset: ${request.assetId}`);
    }

    console.log(`[DALL-E 3 ENGINE] Image synthesized. Downloading raw payload...`);

    // 2. Download raw image stream
    const imageResponse = await axios.get(imageUrl, { responseType: 'arraybuffer' });
    const rawBuffer = Buffer.from(imageResponse.data);

    const highResPngPath = path.join(request.outputDirectory, `${request.assetId}_300dpi.png`);
    const webpOptimizedPath = path.join(request.outputDirectory, `${request.assetId}_web.webp`);

    // 3. Process high-res master PNG using Sharp
    let sharpPipeline = sharp(rawBuffer);

    // Optional vector watermark composite
    if (request.watermarkSvgPath && fs.existsSync(request.watermarkSvgPath)) {
      const watermarkBuffer = fs.readFileSync(request.watermarkSvgPath);
      sharpPipeline = sharpPipeline.composite([
        {
          input: watermarkBuffer,
          gravity: 'southeast',
          blend: 'over'
        }
      ]);
    }

    // Save Master PNG with 300 DPI metadata
    await sharpPipeline
      .withMetadata({ density: 300 })
      .png({ compressionLevel: 8 })
      .toFile(highResPngPath);

    // 4. Save WebP variant optimized for web performance
    await sharp(rawBuffer)
      .webp({ quality: 85, effort: 6 })
      .toFile(webpOptimizedPath);

    const stats = fs.statSync(highResPngPath);
    const imageMeta = await sharp(highResPngPath).metadata();

    console.log(`[PIPELINE SUCCESS] Processed ${request.assetId}: Master PNG (${(stats.size / 1024).toFixed(1)} KB) and WebP written.`);

    return {
      assetId: request.assetId,
      originalUrl: imageUrl,
      revisedPrompt: revisedPrompt,
      localHighResPngPath: highResPngPath,
      localWebpOptimizedPath: webpOptimizedPath,
      width: imageMeta.width || 0,
      height: imageMeta.height || 0,
      fileSizeBytes: stats.size,
      generationTimestamp: new Date().toISOString()
    };
  }
}
