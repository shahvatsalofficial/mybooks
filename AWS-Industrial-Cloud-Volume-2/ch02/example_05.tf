# ephemeral_runner_fargate.tf
resource "aws_ecs_task_definition" "github_runner" {
  family                   = "github-actions-ephemeral-runner"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "2048"
  memory                   = "4096"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.runner_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "runner-container"
      image     = "${aws_ecr_repository.runner_repo.repository_url}:latest"
      essential = true
      environment = [
        { name = "EPHEMERAL", value = "true" },
        { name = "RUNNER_SCOPE", value = "org" }
      ]
      secrets = [
        {
          name      = "GITHUB_PAT"
          valueFrom = aws_secretsmanager_secret.github_token.arn
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/github-ephemeral-runners"
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "runner"
        }
      }
    }
  ])
}

resource "aws_sqs_queue" "runner_queue_fifo" {
  name                        = "github-runner-jobs.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  visibility_timeout_seconds  = 900
}
