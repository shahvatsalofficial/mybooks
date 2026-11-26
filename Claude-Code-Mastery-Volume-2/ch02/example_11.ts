import chokidar from "chokidar";

export function initializeReactiveFileSystemWatcher(server: McpServer, watchDir: string) {
  const watcher = chokidar.watch(watchDir, {
    ignored: /(^|[\/\\])\../, // ignore dotfiles
    persistent: true
  });

  watcher.on("change", (filePath) => {
    const relativeUri = `file:///${filePath.replace(/\\/g, "/")}`;
    console.error(`[CHOKIDAR] Detected modification in: ${relativeUri}`);

    // Emit standard MCP resource updated notification
    server.server.notification({
      method: "notifications/resources/updated",
      params: { uri: relativeUri }
    });
  });

  console.error(`[REACTIVE] File system watcher active on: ${watchDir}`);
}
