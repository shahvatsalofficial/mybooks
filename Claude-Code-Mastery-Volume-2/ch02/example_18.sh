# Compile standalone executable for Linux x64
bun build --compile --minify --sourcemap ./src/index.ts --outfile mcp-server-linux-x64

# Cross-compile for macOS Apple Silicon
bun build --compile --target=bun-darwin-arm64 ./src/index.ts --outfile mcp-server-darwin-arm64

# Cross-compile for Windows x64
bun build --compile --target=bun-windows-x64 ./src/index.ts --outfile mcp-server-win.exe
