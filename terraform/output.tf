output "web_public_ip" {
  description = "Public IP of the web server"
  value = aws_eip.web_eip[0].public_ip
  depends_on = [aws_eip.web_eip]
}

output "web_public_dns" {
  description = "The public DNS of the web server"
  value = aws_eip.web_eip[0].public_dns
  depends_on = [ aws_eip.web_eip ]
}

output "database_endpoint" {
  description = "The endpoint of the db"
  value = aws_db_instance.database.address
}

output "database_port" {
  description = "The port of the database"
  value = aws_db_instance.database.port
}