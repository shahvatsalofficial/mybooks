SELECT
  eventTime,
  userIdentity.arn AS actor_arn,
  eventName,
  requestParameters,
  recipientAccountId,
  sourceIPAddress
FROM
  eds-sovereign-org-audit-2026
WHERE
  eventSource = 'iam.amazonaws.com'
  AND eventName IN ('PutRolePolicy', 'AttachRolePolicy', 'CreatePolicyVersion')
  AND userIdentity.arn NOT LIKE '%/SovereignAdminPipelineRole'
  AND eventTime >= '2026-08-01 00:00:00'
ORDER BY
  eventTime DESC;
