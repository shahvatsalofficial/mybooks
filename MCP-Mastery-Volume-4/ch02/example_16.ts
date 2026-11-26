import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

const command = new GetObjectCommand({ Bucket: bucket, Key: key });
const signedUrl = await getSignedUrl(s3Client, command, { expiresIn: 900 });
return {
  content: [{ type: "text", text: `Download link (valid for 15 minutes): ${signedUrl}` }]
};
