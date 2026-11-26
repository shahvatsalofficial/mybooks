// Production Remediation: Bot Self-Event Suppression Filter
export function shouldProcessSlackMessage(event: any, myBotUserId: string): boolean {
  // Reject messages from any bot or integration
  if (event.bot_id || event.subtype === 'bot_message') {
    return false;
  }
  // Reject messages matching our own application User ID
  if (event.user === myBotUserId) {
    return false;
  }
  // Enforce message deduplication cache
  if (isDuplicateMessage(event.client_msg_id || event.ts)) {
    return false;
  }
  return true;
}
