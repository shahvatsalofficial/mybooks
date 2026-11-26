import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm"],
  target: "node18",
  clean: true,
  minify: true,
  sourcemap: true,
  banner: {
    js: "#!/usr/bin/env node" // MANDATORY: Shebang for direct CLI execution
  },
  noExternal: ["@modelcontextprotocol/sdk", "zod"] // Bundle pure JS dependencies
});
