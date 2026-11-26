import sharp from 'sharp';
import * as path from 'path';

interface DensityConfig {
  suffix: string;
  width: number;
  height: number;
}

const VARIANTS: DensityConfig[] = [
  { suffix: '@1x', width: 896, height: 512 },
  { suffix: '@2x', width: 1792, height: 1024 },
  { suffix: '-mobile', width: 640, height: 640 } // Center square crop for mobile
];

async function generateResponsivePictureSet(masterPngPath: string, outputDir: string, baseName: string) {
  for (const config of VARIANTS) {
    const targetFile = path.join(outputDir, `${baseName}${config.suffix}.webp`);
    if (config.suffix === '-mobile') {
      // Extract centered square crop
      await sharp(masterPngPath)
        .resize(config.width, config.height, { fit: 'cover', position: 'center' })
        .webp({ quality: 82 })
        .toFile(targetFile);
    } else {
      await sharp(masterPngPath)
        .resize(config.width, config.height, { fit: 'inside' })
        .webp({ quality: 85, effort: 6 })
        .toFile(targetFile);
    }
    console.log(`Generated responsive WebP: ${targetFile}`);
  }
}
