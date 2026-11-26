export function convertAdfToMarkdown(node: any): string {
  if (!node) return "";
  if (node.type === "text") {
    let txt = node.text || "";
    if (node.marks) {
      for (const mark of node.marks) {
        if (mark.type === "code") txt = `\`${txt}\``;
        if (mark.type === "strong") txt = `**${txt}**`;
        if (mark.type === "em") txt = `*${txt}*`;
        if (mark.type === "link") txt = `[${txt}](${mark.attrs?.href})`;
      }
    }
    return txt;
  }

  const childText = Array.isArray(node.content)
    ? node.content.map(convertAdfToMarkdown).join("")
    : "";

  switch (node.type) {
    case "doc":
      return childText;
    case "paragraph":
      return `${childText}\n\n`;
    case "heading":
      const level = node.attrs?.level || 2;
      return `${"#".repeat(level)} ${childText}\n\n`;
    case "bulletList":
      return Array.isArray(node.content)
        ? node.content.map((item: any) => `* ${convertAdfToMarkdown(item).trim()}\n`).join("") + "\n"
        : "";
    case "orderedList":
      return Array.isArray(node.content)
        ? node.content.map((item: any, i: number) => `${i + 1}. ${convertAdfToMarkdown(item).trim()}\n`).join("") + "\n"
        : "";
    case "listItem":
      return childText;
    case "codeBlock":
      const lang = node.attrs?.language || "";
      return `\`\`\`${lang}\n${childText}\n\`\`\`\n\n`;
    case "blockquote":
      return `> ${childText.trim()}\n\n`;
    default:
      return childText;
  }
}
