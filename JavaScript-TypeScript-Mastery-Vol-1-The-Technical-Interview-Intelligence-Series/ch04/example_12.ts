import { createReadStream } from 'fs';
import { Writable, pipeline } from 'stream';
import csvParser from 'csv-parser';

export function processBulkCSVHardened(filePath: string, dbClient: any): Promise<void> {
    return new Promise((resolve, reject) => {
        const readable = createReadStream(filePath);
        
        const dbWritable = new Writable({
            objectMode: true,
            // Restrict backpressure memory buffer limit to 16 records max
            highWaterMark: 16,
            write(record, encoding, callback) {
                // Perform the slow database operation
                dbClient.insert(record)
                    .then(() => {
                        // Notify the pipeline that the write is complete.
                        // If the queue has drained, the read stream will automatically resume.
                        callback();
                    })
                    .catch((err: Error) => {
                        // Propagate the error through the pipeline to close all open file handles
                        callback(err);
                    });
            }
        });

        // pipeline auto-propagates errors and closes open file handles on completion
        pipeline(
            readable,
            csvParser(),
            dbWritable,
            (err) => {
                if (err) {
                    console.error('Pipeline failed cleanly. All resources freed:', err);
                    reject(err);
                } else {
                    console.log('Bulk processing completed successfully with a flat memory footprint.');
                    resolve();
                }
            }
        );
    });
}
