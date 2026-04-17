#!/bin/bash
set -e

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

echo "Starting containers..."
cd /home/ubuntu/codelens
docker-compose pull
docker-compose up -d --remove-orphans
echo "Done."