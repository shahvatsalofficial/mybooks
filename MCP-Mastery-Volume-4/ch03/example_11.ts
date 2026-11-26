// Production PII Redaction Pipeline for Support Tickets
export function redactPiiFromTicketText(rawText: string): { sanitizedText: string; redactionCount: number } {
  let text = rawText;
  let count = 0;

  // 1. Credit Card Numbers (Visa, MasterCard, Amex, Discover via Luhn pattern)
  const ccRegex = /\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b/g;
  text = text.replace(ccRegex, () => {
    count++;
    return "[REDACTED_CREDIT_CARD]";
  });

  // 2. US Social Security Numbers (XXX-XX-XXXX)
  const ssnRegex = /\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b/g;
  text = text.replace(ssnRegex, () => {
    count++;
    return "[REDACTED_SSN]";
  });

  // 3. International Phone Numbers (E.164 and common formatted patterns)
  const phoneRegex = /(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g;
  text = text.replace(phoneRegex, () => {
    count++;
    return "[REDACTED_PHONE]";
  });

  // 4. API Keys and Password Strings
  const passwordRegex = /(?:password|secret|bearer|token)\s*[:=]\s*['"]?([^\s'"]{6,})['"]?/gi;
  text = text.replace(passwordRegex, (match, captured) => {
    count++;
    return match.replace(captured, "[REDACTED_SECRET]");
  });

  return { sanitizedText: text, redactionCount: count };
}
