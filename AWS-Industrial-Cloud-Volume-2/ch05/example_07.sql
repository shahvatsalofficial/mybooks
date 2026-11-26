fields @timestamp, @logStream, @message
| filter @message like /(?i)(exception|error|fatal|panic)/
| parse @message /(?i)(?<exception_class>[a-zA-Z0-9_.]+(Exception|Error)): (?<error_msg>[^\n]+)/
| stats count(*) as OccurrenceCount by exception_class, error_msg
| sort OccurrenceCount desc
| limit 15
