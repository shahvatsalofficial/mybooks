SELECT
  eventTime,
  userIdentity.principalId,
  eventName,
  json_extract_scalar(requestParameters, '$.bucketName') AS bucket_name,
  sourceIPAddress,
  userAgent
FROM
  eds-sovereign-org-audit-2026
WHERE
  eventSource = 's3.amazonaws.com'
  AND eventName IN ('PutBucketPolicy', 'PutBucketAcl', 'DeleteBucketPublicAccessBlock')
  AND eventTime >= '2026-08-01 00:00:00';
