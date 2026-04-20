#!/bin/bash
set -e

echo "Pulling latest code..."
cd /home/ubuntu/codelens
git pull

echo "Pulling secrets from SSM..."
aws ssm get-parameters-by-path \
  --path "/codelens/" \
  --with-decryption \
  --query "Parameters[*].[Name,Value]" \
  --output text \
  --region us-east-2 | while read name value; do
    key=$(basename "$name")
    echo "$key=$value"
  done > /home/ubuntu/codelens/.env

echo "Building and starting containers..."
docker-compose build
docker-compose up -d --remove-orphans
echo "Done."