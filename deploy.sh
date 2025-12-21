#!/bin/bash

# KeLiva Cloudflare Deployment Script
# This script automates the deployment process for KeLiva

set -e  # Exit on any error

echo "🚀 KeLiva Cloudflare Deployment Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo -e "${RED}❌ Wrangler CLI not found. Please install it first:${NC}"
    echo "npm install -g wrangler"
    exit 1
fi

echo -e "${BLUE}📋 Checking wrangler authentication...${NC}"
if ! wrangler whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Cloudflare. Please run:${NC}"
    echo "wrangler login"
    exit 1
fi

echo -e "${GREEN}✅ Wrangler CLI ready${NC}"

# Function to check if database exists
check_database() {
    if wrangler d1 info keliva-db &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Step 1: Create D1 database if it doesn't exist
echo -e "\n${BLUE}📊 Checking D1 database...${NC}"
if check_database; then
    echo -e "${GREEN}✅ Database 'keliva-db' already exists${NC}"
else
    echo -e "${YELLOW}📊 Creating D1 database...${NC}"
    wrangler d1 create keliva-db
    echo -e "${RED}⚠️  IMPORTANT: Please update wrangler.toml with the database_id from above!${NC}"
    echo -e "${YELLOW}Press Enter after updating wrangler.toml...${NC}"
    read -r
fi

# Step 2: Apply database schema
echo -e "\n${BLUE}🗄️  Applying database schema...${NC}"
if [ -f "schema.sql" ]; then
    wrangler d1 execute keliva-db --file=schema.sql
    echo -e "${GREEN}✅ Database schema applied${NC}"
else
    echo -e "${RED}❌ schema.sql not found${NC}"
    exit 1
fi

# Step 3: Check secrets
echo -e "\n${BLUE}🔐 Checking environment secrets...${NC}"
echo "Please ensure you have set the following secrets:"
echo "- GROQ_API_KEY (get from console.groq.com)"
echo "- TELEGRAM_BOT_TOKEN (get from @BotFather)"
echo ""
echo "Set them with:"
echo "wrangler secret put GROQ_API_KEY"
echo "wrangler secret put TELEGRAM_BOT_TOKEN"
echo ""
echo -e "${YELLOW}Have you set both secrets? (y/n):${NC}"
read -r secrets_ready
if [[ ! $secrets_ready =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Please set the secrets and run this script again.${NC}"
    exit 1
fi

# Step 4: Deploy backend
echo -e "\n${BLUE}🔧 Deploying backend to Cloudflare Pages...${NC}"
wrangler pages deploy functions --project-name=keliva
echo -e "${GREEN}✅ Backend deployed to: https://keliva.pages.dev${NC}"

# Step 5: Build and deploy frontend
echo -e "\n${BLUE}🎨 Building and deploying frontend...${NC}"
if [ -d "frontend" ]; then
    cd frontend
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
        npm install
    fi
    
    # Build frontend
    echo -e "${YELLOW}🔨 Building frontend...${NC}"
    npm run build
    
    # Deploy frontend
    echo -e "${YELLOW}🚀 Deploying frontend...${NC}"
    wrangler pages deploy dist --project-name=keliva-app
    
    cd ..
    echo -e "${GREEN}✅ Frontend deployed to: https://keliva-app.pages.dev${NC}"
else
    echo -e "${RED}❌ Frontend directory not found${NC}"
    exit 1
fi

# Step 6: Test deployment
echo -e "\n${BLUE}🧪 Testing deployment...${NC}"
echo "Testing health endpoint..."
if curl -s "https://keliva.pages.dev/api/health" > /dev/null; then
    echo -e "${GREEN}✅ Backend health check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Backend might still be starting up...${NC}"
fi

# Step 7: Telegram webhook setup
echo -e "\n${BLUE}🤖 Telegram webhook setup${NC}"
echo "To complete the setup, run this command with your bot token:"
echo ""
echo -e "${YELLOW}curl -X POST \"https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook\" \\${NC}"
echo -e "${YELLOW}     -H \"Content-Type: application/json\" \\${NC}"
echo -e "${YELLOW}     -d '{\"url\": \"https://keliva.pages.dev/api/telegram/webhook\"}'${NC}"
echo ""

# Summary
echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
echo "======================================"
echo -e "Backend:  ${BLUE}https://keliva.pages.dev${NC}"
echo -e "Frontend: ${BLUE}https://keliva-app.pages.dev${NC}"
echo -e "API Docs: ${BLUE}https://keliva.pages.dev/docs${NC}"
echo ""
echo "Next steps:"
echo "1. Set up Telegram webhook (command shown above)"
echo "2. Test your bot by sending /start"
echo "3. Visit the frontend to test the web interface"
echo ""
echo -e "${GREEN}Your KeLiva app is now running on Cloudflare's global edge network! 🌍${NC}"