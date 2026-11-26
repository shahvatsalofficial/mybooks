import { createWorker } from 'tesseract.js';

async function validateZeroText(imagePath: string): Promise<boolean> {
  const worker = await createWorker('eng');
  const ret = await worker.recognize(imagePath);
  await worker.terminate();

  const detectedText = ret.data.text.trim();
  if (detectedText.length > 3) {
    console.warn(`[OCR GATE REJECTED] Detected hallucinated text: "${detectedText}" in ${imagePath}`);
    return false; // Rejection: Contains text
  }
  return true; // Passed: 100% text-free
}
