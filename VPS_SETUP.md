# VPS Setup Guide

## Connect to VPS
ssh root@37.187.159.65 -p 20022

## Install Python
apt update && apt upgrade -y
apt install python3 python3-pip -y

## Upload project files
(use scp or git clone)
git clone <your-repo-url>
cd phantom-seats-vps

## Install dependencies
pip3 install -r requirements.txt

## Update .env
nano .env
(set your PIN)

## Run the app
python3 main.py

## Run permanently (keeps running after SSH disconnect)
apt install screen -y
screen -S phantom
python3 main.py
(Press Ctrl+A then D to detach)

## Access kill switch
Open on phone:
http://37.187.159.65:5000

## Open VPS firewall port
ufw allow 5000
ufw enable
