// FATAL FLAW: Spawning subprocesses without lifecycle management or process reaping
server.tool('run_git_checkout', 'Executes git operations', { repoPath: z.string() }, async ({ repoPath }) => {
  const child = child_process.spawn('git', ['status', '--porcelain'], { cwd: repoPath });
  let output = '';
  child.stdout.on('data', (d) => output += d);
  // Missing: child.on('close'), child.on('error'), and signal termination!
  return { content: [{ type: 'text', text: output }] };
});
