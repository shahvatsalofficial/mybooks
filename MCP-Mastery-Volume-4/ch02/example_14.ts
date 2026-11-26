// Architectural Guard: Hard Sizing Rejection
const head = await s3Client.send(new HeadObjectCommand({ Bucket: bucket, Key: key }));
if ((head.ContentLength || 0) > 10 * 1024 * 1024) {
  return {
    isError: true,
    content: [{
      type: "text",
      text: `Object too large for direct download (${head.ContentLength} bytes). Use s3_read_object_range to fetch specific byte chunks.`
    }]
  };
}
