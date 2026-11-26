import { BlobServiceClient, StorageSharedKeyCredential } from "@azure/storage-blob";

export async function appendAuditObservation(blobName: string, observationText: string) {
  const credential = new StorageSharedKeyCredential(
    process.env.AZURE_STORAGE_ACCOUNT!,
    process.env.AZURE_STORAGE_ACCESS_KEY!
  );
  const client = new BlobServiceClient(
    `https://${process.env.AZURE_STORAGE_ACCOUNT}.blob.core.windows.net`,
    credential
  );

  const containerClient = client.getContainerClient("compliance-ledger");
  const appendBlobClient = containerClient.getAppendBlobClient(blobName);

  // Initialize append blob if it does not exist
  await appendBlobClient.createIfNotExists();

  const logEntry = `[${new Date().toISOString()}] ${observationText}\n`;
  await appendBlobClient.appendBlock(logEntry, logEntry.length);
}
