fields @timestamp, @message
| filter @message like /"httpMethod"/
| parse @message '"route": "*", "durationMs": *, "statusCode": *' as route, duration, status
| stats count(*) as TotalRequests,
        pct(duration, 50) as P50_Latency,
        pct(duration, 90) as P90_Latency,
        pct(duration, 99) as P99_Latency,
        sum(status >= 500) / count(*) * 100 as ErrorRatePct by route
| sort P99_Latency desc
| limit 20
