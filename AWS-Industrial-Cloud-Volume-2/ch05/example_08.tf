# metric_streams.tf
resource "aws_cloudwatch_metric_stream" "enterprise_stream" {
  name          = "enterprise-metric-stream-to-firehose"
  role_arn      = aws_iam_role.metric_stream_role.arn
  firehose_arn  = aws_kinesis_firehose_delivery_stream.metrics_firehose.arn
  output_format = "opentelemetry0.7"

  include_filter {
    namespace = "AWS/ApplicationELB"
  }
  include_filter {
    namespace = "AWS/ECS"
  }
  include_filter {
    namespace = "IndustrialCloud/PaymentService"
  }
}
