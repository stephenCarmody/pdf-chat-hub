resource "aws_db_subnet_group" "aurora" {
  name       = "pdf-chat-aurora"
  subnet_ids = aws_subnet.private_subnet[*].id
}

resource "aws_security_group" "aurora" {
  name        = "pdf-chat-aurora"
  description = "Security group for Aurora PostgreSQL"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }
}

resource "aws_rds_cluster" "aurora" {
  cluster_identifier     = "pdf-chat-aurora"
  engine                = "aurora-postgresql"
  engine_version        = "16.3"
  engine_mode           = "provisioned"
  database_name         = "pdf_chat"
  master_username       = "pdf_chat_admin"
  master_password       = "password" # Simple password for development
  storage_encrypted    = true

  
  db_subnet_group_name   = aws_db_subnet_group.aurora.name
  vpc_security_group_ids = [aws_security_group.aurora.id]

  serverlessv2_scaling_configuration {
    max_capacity = 1.0
    min_capacity = 0.0
  }
}

resource "aws_rds_cluster_instance" "aurora_instance" {
  cluster_identifier = aws_rds_cluster.aurora.id
  instance_class    = "db.serverless"
  engine            = aws_rds_cluster.aurora.engine
  engine_version    = aws_rds_cluster.aurora.engine_version
} 