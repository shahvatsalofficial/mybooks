import { pipeline } from 'stream';
import { createReadStream, createWriteStream } from 'fs';
import { createGzip } from 'zlib';

pipeline(
    createReadStream('input.log'),
    createGzip(),
    createWriteStream('output.log.gz'),
    (err) => {
        if (err) {
            console.error('Pipeline failed and auto-closed all descriptors:', err);
        } else {
            console.log('Pipeline executed successfully and freed all buffers.');
        }
    }
);
