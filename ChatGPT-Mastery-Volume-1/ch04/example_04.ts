import sharp from 'sharp';

async function applyEnterpriseBranding(inputPath: string, logoSvgPath: string, outputPath: string) {
  const logoBuffer = await sharp(logoSvgPath)
    .resize({ width: 180 })
    .png()
    .toBuffer();

  await sharp(inputPath)
    .composite([
      {
        input: logoBuffer,
        gravity: 'southeast',
        blend: 'over'
      }
    ])
    .withMetadata({ density: 300 })
    .png({ compressionLevel: 9 })
    .toFile(outputPath);

  console.log(`Branded master asset exported to: ${outputPath}`);
}
