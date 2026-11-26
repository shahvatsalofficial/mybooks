# central_oam_sink.tf
resource "aws_oam_sink" "central_sink" {
  name = "EnterpriseCentralObservabilitySink"
}

resource "aws_oam_sink_policy" "org_sink_policy" {
  sink_identifier = aws_oam_sink.central_sink.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = "*"
        Action    = ["oam:CreateLink", "oam:UpdateLink"]
        Resource  = "*"
        Condition = {
          "ForAllValues:StringEquals" = {
            "oam:ResourceTypes" = ["AWS::CloudWatch::Metric", "AWS::Logs::LogGroup", "AWS::XRay::Trace"]
          }
          StringEquals = {
            "aws:PrincipalOrgID" = "o-enterprise12345"
          }
        }
      }
    ]
  })
}
