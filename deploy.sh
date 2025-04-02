#!/bin/bash

# This script automates the deployment process for the Advanced Quiz Bot on Koyeb

# Print header
echo "========================================="
echo "Advanced Quiz Bot - Koyeb Deployment Tool"
echo "========================================="
echo ""

# Check for required environment variables
echo "Checking environment variables..."
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  echo "Error: TELEGRAM_BOT_TOKEN is not set."
  echo "Please set it with: export TELEGRAM_BOT_TOKEN=your_token"
  exit 1
fi

if [ -z "$OWNER_ID" ]; then
  echo "Warning: OWNER_ID is not set. Admin features will be disabled."
  echo "You can set it with: export OWNER_ID=your_telegram_id"
fi

if [ -z "$DATABASE_URL" ]; then
  echo "Error: DATABASE_URL is not set."
  echo "Please set it with: export DATABASE_URL=your_database_url"
  exit 1
fi

if [ -z "$SESSION_SECRET" ]; then
  echo "Generating a random SESSION_SECRET..."
  export SESSION_SECRET=$(openssl rand -hex 32)
  echo "SESSION_SECRET has been set to a random value."
fi

echo "Environment variables check passed!"
echo ""

# Check if Koyeb CLI is installed
echo "Checking for Koyeb CLI..."
if ! command -v koyeb &> /dev/null; then
  echo "Koyeb CLI is not installed."
  echo "Would you like to install it? (y/n)"
  read answer
  if [ "$answer" != "${answer#[Yy]}" ]; then
    echo "Installing Koyeb CLI..."
    curl -fsSL https://cli.koyeb.com/install.sh | bash
  else
    echo "Please install the Koyeb CLI manually and run this script again."
    echo "Installation instructions: https://www.koyeb.com/docs/cli/installation"
    exit 1
  fi
fi

echo "Koyeb CLI is installed!"
echo ""

# Check if logged in to Koyeb
echo "Checking Koyeb authentication..."
if ! koyeb auth check &> /dev/null; then
  echo "Not authenticated with Koyeb."
  echo "Please login using the Koyeb CLI:"
  echo "koyeb login"
  exit 1
fi

echo "Authenticated with Koyeb!"
echo ""

# Create app name
APP_NAME="advanced-quiz-bot"
if [ -n "$1" ]; then
  APP_NAME="$1"
fi

echo "Using app name: $APP_NAME"
echo ""

# Deploy the application
echo "Deploying to Koyeb..."
echo "This might take a few minutes..."

koyeb app create $APP_NAME

koyeb service create web \
  --app $APP_NAME \
  --type web \
  --git github.com/yourusername/advanced-quiz-bot \
  --git-branch main \
  --git-build-command "pip install -r requirements-koyeb.txt" \
  --git-run-command "gunicorn --bind 0.0.0.0:\$PORT --timeout 120 main:app" \
  --ports 80:http:\$PORT \
  --routes /:80 \
  --env TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN \
  --env OWNER_ID=$OWNER_ID \
  --env DATABASE_URL=$DATABASE_URL \
  --env SESSION_SECRET=$SESSION_SECRET \
  --env WEB_APP_URL=https://$APP_NAME.koyeb.app \
  --env PORT=\$PORT \
  --health-check /health:80 \
  --min-scale 1 \
  --max-scale 1

echo ""
echo "Deployment initiated!"
echo "You can check the status with: koyeb service get web -a $APP_NAME"
echo ""
echo "Once deployed, your bot will be available at:"
echo "https://$APP_NAME.koyeb.app"
echo ""
echo "Don't forget to update the WEB_APP_URL environment variable if needed."
echo "========================================="
