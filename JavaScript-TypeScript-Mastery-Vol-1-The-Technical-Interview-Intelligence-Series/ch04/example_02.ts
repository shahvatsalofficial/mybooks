import { Readable, Writable } from 'stream';

function safelyCopyData(source: Readable, destination: Writable, onComplete: () => void) {
    source.on('data', (chunk) => {
        // Push chunk to destination
        const canContinue = destination.write(chunk);
        
        if (!canContinue) {
            // Highwatermark hit! Pause readable stream to handle backpressure
            source.pause();
        }
    });

    destination.on('drain', () => {
        // Writable buffer has successfully drained. Safe to resume reading!
        source.resume();
    });

    source.on('end', () => {
        destination.end();
    });

    destination.on('finish', () => {
        onComplete();
    });
}
