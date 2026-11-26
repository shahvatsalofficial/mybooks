function extractJiraIssueKeys(text: string): string[] {
  const jiraRegex = /\b[A-Z][A-Z0-9]+-\d+\b/g;
  const matches = text.match(jiraRegex);
  return matches ? Array.from(new Set(matches)) : [];
}
