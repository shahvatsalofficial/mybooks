import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm"],
  target: "node18",
  outDir: "dist",
  clean: true,
  minify: true,
  sourcemap: false,
  splitting: false,
  shims: true,
  banner: {
    js: "#!/usr/bin/env node"
  },
  noExternal: [
    "@modelcontextprotocol/sdk",
    "axios",
    "turndown"
  ]
});
