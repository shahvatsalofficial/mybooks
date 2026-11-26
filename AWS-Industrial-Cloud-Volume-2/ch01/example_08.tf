# Downstream microservice consuming decoupled networking state
data "aws_ssm_parameter" "private_subnets" {
  name = "/enterprise/production/networking/private_subnet_ids"
}

resource "aws_lb_target_group" "microservice" {
  name        = "payment-service-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = data.aws_ssm_parameter.vpc_id.value
  target_type = "ip"
}
