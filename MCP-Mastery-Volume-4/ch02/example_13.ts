// The Flawed Naive Download Tool
const response = await s3Client.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
const stream = response.Body as NodeJS.ReadableStream;
const fileStream = fs.createWriteStream(`/tmp/${key}`);
await pipeline(stream, fileStream); // Wrote 8.4GB to container root disk
