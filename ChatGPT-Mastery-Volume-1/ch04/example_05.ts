const FORBIDDEN_TRADEMARKS = ['nike', 'swoosh', 'adidas', 'apple', 'coca-cola', 'gucci', 'disney'];

function sanitizeBrandPrompt(userPrompt: string): string {
  let cleaned = userPrompt;
  for (const mark of FORBIDDEN_TRADEMARKS) {
    const regex = new RegExp(`\\b${mark}\\b`, 'gi');
    cleaned = cleaned.replace(regex, 'generic high-end artisanal');
  }
  return `${cleaned}. 100% text-free, zero commercial logos, zero trademarked emblems.`;
}
