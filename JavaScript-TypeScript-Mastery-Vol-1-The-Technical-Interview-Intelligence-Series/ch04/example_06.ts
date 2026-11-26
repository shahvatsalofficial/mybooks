import cluster from 'cluster';
import http from 'http';
import { cpus } from 'os';

if (cluster.isPrimary) {
    const numCPUs = cpus().length;
    console.log(`Master process active: ${process.pid}. Initializing ${numCPUs} clusters...`);

    // Fork workers matching the system's physical CPU core count
    for (let i = 0; i < numCPUs; i++) {
        cluster.fork();
    }

    // Monitor for worker crashes and spawn clean replacements
    cluster.on('exit', (worker, code, signal) => {
        console.warn(`Worker crash detected: ${worker.process.pid}. Signal: ${signal || code}. Respawning...`);
        cluster.fork();
    });
    
} else {
    // Workers share the TCP connection pool, listening on port 8080
    http.createServer((req, res) => {
        res.writeHead(200);
        res.end(`Handled by worker process: ${process.pid}`);
    }).listen(8080);

    console.log(`Worker active: ${process.pid}`);
}
