import { spawn } from 'child_process';

// Spawn a system process to run file compression
const child = spawn('tar', ['-czf', 'archive.tar.gz', './massive-directory']);

child.stdout.on('data', (data) => {
    console.log(`System progress: ${data}`);
});

child.stderr.on('data', (data) => {
    console.error(`System error logging: ${data}`);
});

child.on('close', (code) => {
    console.log(`Child process exited with status: ${code}`);
});
