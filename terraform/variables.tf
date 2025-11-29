# EC2
variable "instance_name" {
  description = "Value of the name tag"
  type = string
  default = "NewInstance"
}

variable "ec2_instance_type" {
  description = "AWS EC2 instance type"
  type = string
  default = "t2.micro"
}

# RDS
variable "rds_storage_allocation" {
    description = "Amount of storage allocated to RDS instance in GB"
    type = number
    default = 10
}

variable "instance_rds_name" {
  type = string
  default = "NewDB"
}

variable "rds_instance_class" {
  description = "AWS RDS instance type"
  type = string
  default = "db.t2.micro"
}

# VPC
variable "vpc_cidr_block" {
  description = "CIDR block for VPC"
  type = string
  default = "10.0.0.0/16"
}

variable "subnet_count" {
  description = "Number of public and private subnets"
  type = map(number)
  default = {
    public = 2
    private = 2
  }
}

variable "public_subnet_cidr_blocks" {
  description = "Available CIDR blocks for public subnets"
  type = list(string)
  default = [
    "10.0.1.0/24",
    "10.0.2.0/24",
    "10.0.3.0/24",
    "10.0.4.0/24",
  ]
}

variable "private_subnet_cidr_blocks" {
  description = "Available CIDR blocks for private subnets"  
  type = list(string)
  default = [
    "10.0.101.0/24",
    "10.0.102.0/24",
    "10.0.103.0/24",
    "10.0.104.0/24",
  ]
}

# General
variable "aws_region" {
  description = "AWS region"
  type = string
  default = "us-west-2"
}


variable "tags" {
  description = "Tags for all resources in this project"
  default = {
    Name = "newInstance"
    Project = "Unknown"
    Customer = "Unknown"
  }
}

variable "config" {
  description = "Config settings for EC2 and RDS instances"
  type = map(any)
  default = {
    "database" = {
      allocated_storage = 10
      engine = "mysql"
      engine_version = "8.0.40"
      instance_class = "db.t3.micro"
      db_name = "cigarScraperDB"
      skip_final_snapshot = true
    },
    "app" = {
      count = 1
      instance_type = "t2.micro"
    }
  }
}

# Secrets
variable "my_ip" {
  description = "My IP address"
  type = string
  sensitive = true
}

variable "db_username" {
  description = "Database master user"
  type = string
  sensitive = true
}

variable "db_password" {
  description = "Database master user passwords"
  type = string
  sensitive = true
}