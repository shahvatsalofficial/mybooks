export async function executeJqlSearch(jiraHost: string, authHeader: string, jql: string, maxResults: number = 20) {
  const url = `https://${jiraHost}/rest/api/3/search`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: authHeader,
      "Content-Type": "application/json",
      Accept: "application/json"
    },
    body: JSON.stringify({
      jql,
      maxResults,
      fields: ["summary", "status", "assignee", "priority", "description"]
    })
  });

  const data = await response.json();
  const issues = (data.issues || []).map((issue: any) => ({
    key: issue.key,
    summary: issue.fields.summary,
    status: issue.fields.status?.name,
    assignee: issue.fields.assignee?.displayName || "Unassigned",
    priority: issue.fields.priority?.name,
    descriptionMarkdown: convertAdfToMarkdown(issue.fields.description)
  }));

  return { total: data.total, issues };
}
