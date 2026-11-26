node d:/MyData/EBooks/MCP_Mastery_Vol1/dist/index.js
   ```
   If the process crashes or emits unhandled stack traces, resolve the underlying code bug before testing inside the host.
3. **Step 3: Run the MCP Inspector**:
   ```bash
   npx @modelcontextprotocol/inspector node d:/MyData/EBooks/MCP_Mastery_Vol1/dist/index.js
   ```
   Verify that all tools appear in the web UI and that clicking "Run Tool" returns valid `{ isError: false }` envelopes.
4. **Step 4: Check for Orphaned Zombie Processes**:
   If you edited your server code but Claude still runs old logic, terminate lingering processes:
   - macOS/Linux: `pkill -f notes-mcp`
   - Windows: `Get-Process | Where-Object { $_.CommandLine -like "*notes-mcp*" } | Stop-Process`
5. **Step 5: Perform a Complete Host Hard Restart**:
   Merely closing the chat window does not restart child subprocesses. Fully quit the application (`Cmd+Q` on macOS, right-click system tray "Quit" on Windows) and relaunch.

#### 6. Cross-Platform Operating System Architectural Nuances

Deploying MCP servers across heterogeneous engineering fleets requires accounting for fundamental differences in operating system process architecture:

1. **Path Separator Normalization**: On Windows, file paths use backslashes (`\`) and drive letters (`C:\`), whereas JSON strings require escaped backslashes (`C:\\...`) or standard forward slashes (`C:/...`). When writing URIs in MCP resources (e.g., `file:///C:/Users/...`), ensure that server code always normalizes paths using Node.js `path.posix.normalize()` or Python `pathlib.Path.as_posix()`.
2. **Executable Extension Resolution**: On Windows, launching command-line tools requires resolving `.cmd`, `.bat`, or `.exe` binaries. While an interactive terminal shell automatically expands `npm` to `npm.cmd`, Node.js `child_process.spawn("npm")` will fail with `ENOENT` unless `shell: true` is configured or `npm.cmd` is explicitly declared.
3. **Signal Emulation on Windows**: POSIX signals like `SIGTERM` and `SIGINT` do not exist natively on the Windows NT kernel. When Claude Desktop or a custom client terminates a server subprocess on Windows, the operating system executes an abrupt `TerminateProcess()` call unless the server process cooperatively monitors `stdin` closure (`process.stdin.on('close')`).

---

## 8.8 Where This Breaks: Common Client Integration Pitfalls

- **Relative Path Assumptions in Configs**: Writing `"args": ["dist/index.js"]` without specifying the absolute path causes child processes to fail when Claude Desktop launches from `/Applications` or `%WINDIR%`.
- **Missing GUI Environment Variables**: Assuming `process.env.PATH` contains Homebrew or npm paths inside GUI desktop apps. Always supply explicit `"env"` blocks.
- **Aggressive Schema Caching**: Editing server code while Claude Desktop is running results in the "Stale Schema Ghost Bug". Always perform a hard restart (`Cmd+Q` / Kill process).
- **Orphaned Background Daemons**: Killing a terminal window without terminating the child process leaves database file locks on SQLite or PostgreSQL databases.
- **JSON Syntax Errors in Config Files**: Missing commas or trailing commas in `claude_desktop_config.json` causes Claude Desktop to fail to boot silently. Validate config files with `jq . claude_desktop_config.json`.
- **Ignoring Tool Execution Timeouts**: Host applications enforce default tool execution timeouts (typically 60 seconds). Long-running batch jobs must yield intermediate progress via `ctx.info()` or run asynchronously.

---

## Chapter Exercises

### Exercise 1: Check (Foundational)
- **Question**: Why does an MCP server that runs perfectly in a macOS zsh terminal window frequently fail with `spawn ENOENT` when launched via Claude Desktop? How do you resolve this permanently?

### Exercise 2: Build (Applied)
- **Task**: Write a Node.js health-check script `mcp-ping.ts` that takes an MCP server command line as arguments (e.g., `npx ts-node mcp-ping.ts node dist/index.js`), launches the server over stdio, performs the `initialize` handshake, asserts that at least one tool is advertised, and prints `HEALTH_CHECK_PASSED` before exiting with code 0.

### Exercise 3: Stretch (Architectural)
- **Task**: Implement a resilient multi-server proxy router in TypeScript that connects to three separate downstream MCP servers over stdio, aggregates their tool catalogs into a single virtual server, prefixes duplicate tool names with their server identifier, and forwards incoming `tools/call` requests to the appropriate child transport.

---

## Exercise Solutions

### Solution to Exercise 1: Check
When a terminal window opens, the operating system launches an interactive login shell that evaluates user configuration scripts (`~/.zshrc`, `~/.bash_profile`), exporting custom directories (such as `/opt/homebrew/bin`, `~/.nvm/.../bin`, or `~/.local/bin`) to the `PATH` environment variable. When Claude Desktop is launched via Spotlight or Finder, it is spawned directly by the operating system window manager (`launchd` on macOS or `explorer.exe` on Windows), which inherits only the bare system default `PATH` (`/usr/bin:/bin:/usr/sbin:/sbin`). If your server command relies on `uvx`, `node`, or `npx` located in a user-level directory, the OS fails to find the binary and throws `spawn ENOENT`. The permanent solution is to specify the fully qualified absolute path to the executable (e.g., `/Users/name/.local/bin/uvx`) and supply an explicit `"PATH"` variable inside the `"env"` configuration block.

### Solution to Exercise 2: Build
