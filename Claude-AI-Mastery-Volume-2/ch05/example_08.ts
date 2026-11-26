// Production Hotfix: Redirect stdout to stderr for all third-party libraries
const originalStdoutWrite = process.stdout.write.bind(process.stdout);

// Guard against non-JSON-RPC stdout pollution
export function installStdoutGuard() {
  console.log = (...args: any[]) => {
    // Re-route stray console.log calls to stderr so they do not break JSON-RPC
    console.error('[STDOUT GUARD REDIRECT]', ...args);
  };
}
