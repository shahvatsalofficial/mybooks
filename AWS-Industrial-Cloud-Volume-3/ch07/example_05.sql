SELECT
  eventTime,
  userIdentity.arn AS principal_arn,
  eventName,
  json_extract_scalar(requestParameters, '$.keyId') AS kms_key_id,
  errorCode,
  errorMessage,
  sourceIPAddress
FROM
  eds-sovereign-org-audit-2026
WHERE
  eventSource = 'kms.amazonaws.com'
  AND eventName IN ('ScheduleKeyDeletion', 'DisableKey', 'CancelKeyDeletion')
  AND eventTime >= '2026-08-01 00:00:00'
ORDER BY
  eventTime DESC;
