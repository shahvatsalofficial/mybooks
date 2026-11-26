// Architectural Guard: Bot Loop Blocker
if (message.bot_id || message.subtype === "bot_message" || message.user === BOT_USER_ID) {
  return; // Instantly ignore own messages and other bots
}
