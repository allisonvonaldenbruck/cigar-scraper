#!/bin/bash
sudo apt update -y
sudo apt upgrade -y
sudo apt install git -y
sudo apt install python3 -y
sudo apt install python3.8-venv -y
sudo apt install cron -y
sudo apt install mysql-client -y
sudo systemctl enable cron
echo "apt installs complete" >> setup.log

#git -c http.sslVerify=false clone git@github.com:ManixI/cigar-scraper.git
#mv db_login_file cigar-scraper/secrets
#mv sb_api_key cigar-scraper/secrets
#echo "git setup complete" >> setup.log
#
#cd cigar-scraper
#mkdir env
#python3 -m venv env
#source env/bin/activate
#pip install -r requirements.txt
#echo "python env setup complete" >> setup.log
#
#crontab -l > mycron
#echo "0 0 * * * python3 ~/cigar-scraper/main.py" >> mycron
#crontab mycron
#rm mycron
#echo "cron setup complete" >> setup.log
#
#echo "setup complete" >> setup.log