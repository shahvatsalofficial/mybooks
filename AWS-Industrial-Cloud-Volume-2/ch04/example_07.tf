# eventbridge_pipe.tf
resource "aws_pipes_pipe" "order_enrichment_pipe" {
  name     = "order-stream-to-eventbus"
  role_arn = aws_iam_role.pipe_execution_role.arn
  source   = aws_sqs_queue.raw_orders_queue.arn
  target   = aws_cloudwatch_event_bus.enterprise_bus.arn

  source_parameters {
    sqs_queue_parameters {
      batch_size                         = 10
      maximum_batching_window_in_seconds = 5
    }
    filter_criteria {
      filter {
        pattern = jsonencode({
          body = {
            status = ["ORDER_PLACED"]
          }
        })
      }
    }
  }

  enrichment = aws_lambda_function.enrichment_lambda.arn

  target_parameters {
    eventbridge_event_bus_parameters {
      detail_type = "EnrichedOrderEvent"
      source      = "ecommerce.orders.pipe"
    }
  }
}
