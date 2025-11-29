# provider block
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  profile = "aws-vonarosa"
  region = var.aws_region
}

data "aws_availability_zones" "available" {
  state = "available"
  #name = ["us-west-2a", "us-west-2b"]
}

# VPC
resource "aws_vpc" "vpc" {
  cidr_block = var.vpc_cidr_block
  enable_dns_hostnames = true
  tags = var.tags
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id
  tags = var.tags
}

# Subnets
resource "aws_subnet" "public_subnet" {
  count = var.subnet_count.public
  vpc_id = aws_vpc.vpc.id
  cidr_block = var.public_subnet_cidr_blocks[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags = {
    Name = "public_subnet_${count.index}",
    Project = var.tags.Project
    Customer = var.tags.Customer
  }
}

resource "aws_subnet" "private_subnet" {
  count = var.subnet_count.private
  vpc_id = aws_vpc.vpc.id
  cidr_block = var.private_subnet_cidr_blocks[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags = {
    Name = "private_subnet_${count.index}",
    Project = var.tags.Project
    Customer = var.tags.Customer
  }
}

# Route Tables
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table_association" "public" {
  count = var.subnet_count.public
  route_table_id = aws_route_table.public_rt.id
  subnet_id = aws_subnet.public_subnet[count.index].id
}

resource "aws_route_table" "private_rt" {
  vpc_id = aws_vpc.vpc.id
}

resource "aws_route_table_association" "private" {
  count = var.subnet_count.private
  route_table_id = aws_route_table.private_rt.id
  subnet_id = aws_subnet.private_subnet[count.index].id
}

# Security Groups
resource "aws_security_group" "web_sg" {
  name = "web_sg"
  description = "Security group for web servers"
  vpc_id = aws_vpc.vpc.id
  
  ingress {
    description = "Allow all traffic though HTTP"
    from_port = "80"
    to_port = "80"
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # TODO: broaden this out to allow ssh from anywhere with key
  # TODO: move ssh traffic to different port
  ingress {
    description = "Allow SSH from my computer"
    from_port = "22"
    to_port = "22"
    protocol = "tcp"
    cidr_blocks = ["${var.my_ip}/32"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = [ "0.0.0.0/0" ]
  }
  tags = {
    Name = "web_sg"
    Project = var.tags.Project
    Customer = var.tags.Customer
  }
}

resource "aws_security_group" "db_sg" {
  name = "db_sg"
  description = "Security group for database"
  vpc_id = aws_vpc.vpc.id

  ingress {
    description = "Allow mysql traffic from only the web sg"
    from_port = "3306"
    to_port = "3306"
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "db_sg"
    Project = var.tags.Project
    Customer = var.tags.Customer
  }
}

# database
resource "aws_db_subnet_group" "aws_db_subnet_group" {
  name = "db_subnet_group"
  description = "DB subnet group"
  subnet_ids = [for subnet in aws_subnet.public_subnet : subnet.id]
  tags = var.tags
}

resource "aws_db_instance" "database" {
  allocated_storage = var.config.database.allocated_storage
  engine = var.config.database.engine
  publicly_accessible = true
  #engine_version = var.config.database.engine_version
  instance_class = var.config.database.instance_class
  db_name = var.config.database.db_name
  username = var.db_username
  password = var.db_password
  db_subnet_group_name = aws_db_subnet_group.aws_db_subnet_group.id
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  skip_final_snapshot = var.config.database.skip_final_snapshot

}

# keys
resource "aws_key_pair" "kp" {
  key_name = "tutorial_kp"
  public_key = file("../secrets/tutorial_kp.pub")
}

# EC2
data "aws_ami" "ubuntu" {
  most_recent = "true"
  
  filter {
    name = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }

  filter {
    name = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"]
}

resource "aws_instance" "app" {
  count = var.config.app.count
  ami = data.aws_ami.ubuntu.id
  instance_type = var.config.app.instance_type
  subnet_id = aws_subnet.public_subnet[count.index].id
  key_name = aws_key_pair.kp.key_name
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  tags = {
    Name = "web_${count.index}"
    Project = var.tags.Project
    Customer = var.tags.Customer
  }
}

resource "aws_eip" "web_eip" {
  count = var.config.app.count
  instance = aws_instance.app[count.index].id
  #vpc = true
  tags = {
    Name = "app_eip_${count.index}"
    Project = var.tags.Project
    Customer = var.tags.Customer
  }
}

# files, etc.
resource "null_resource" "setup_vm" {
  depends_on = [ aws_instance.app, aws_db_instance.database ]

  connection {
    type = "ssh"
    user = "ubuntu"
    private_key = file("../secrets/tutorial_kp")
    host = aws_instance.app[0].public_ip
  }

  provisioner "file" {
    source = "../secrets/sb_api_key"
    destination = "sb_api_key"
  }

  provisioner "file" {
    source = "./setup_script.sh"
    destination = "./setup_script.sh"
  }

  provisioner "file" {
    source = "/home/ian/.ssh/manix_key"
    destination = ".ssh/manix_key"
  }


  # setup db credentials
  provisioner "local-exec" {
    command = "echo \"host:${aws_db_instance.database.address}\" > ../secrets/db_login_file_remote"
  }

  provisioner "local-exec" {
    command = "echo \"port:${aws_db_instance.database.port}\" >> ../secrets/db_login_file_remote"
  }
  provisioner "local-exec" {
    command = "echo \"user:${var.db_username}\" >> ../secrets/db_login_file_remote"
  }
  provisioner "local-exec" {
    command = "echo \"pass:${var.db_password}\" >> ../secrets/db_login_file_remote"
  }
    
  provisioner "file" {
    source = "../secrets/db_login_file_remote"
    destination = "./db_login_file"
  }
  
  provisioner "remote-exec" {
    inline = [ 
      "chmod +x ./setup_script.sh",
      "chmod 600 ~/.ssh/manix_key",
      "./setup_script.sh" 
    ]
  }

}