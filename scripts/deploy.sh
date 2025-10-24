#!/bin/bash

# Enterprise CIA - One-Click Deployment Script
# Deploys frontend to Vercel and backend to Railway

set -e  # Exit on error

echo "🚀 Enterprise CIA - Deployment Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required tools are installed
check_dependencies() {
    echo "🔍 Checking dependencies..."

    if ! command -v vercel &> /dev/null; then
        echo -e "${RED}❌ Vercel CLI not found${NC}"
        echo "Install with: npm i -g vercel"
        exit 1
    fi

    if ! command -v railway &> /dev/null; then
        echo -e "${YELLOW}⚠️  Railway CLI not found${NC}"
        echo "Install from: https://docs.railway.app/develop/cli"
        echo "Or deploy manually via Railway dashboard"
    fi

    echo -e "${GREEN}✅ Dependencies OK${NC}"
    echo ""
}

# Deploy frontend to Vercel
deploy_frontend() {
    echo "📦 Deploying frontend to Vercel..."
    echo ""

    # Build frontend
    echo "Building Next.js app..."
    npm run build

    # Deploy with Vercel
    echo "Deploying to Vercel..."
    vercel --prod

    echo -e "${GREEN}✅ Frontend deployed!${NC}"
    echo ""
}

# Instructions for Railway backend deployment
deploy_backend_instructions() {
    echo "🔧 Backend Deployment (Railway)"
    echo "================================"
    echo ""
    echo "Automated Railway deployment coming soon!"
    echo ""
    echo "For now, deploy manually:"
    echo ""
    echo "1. Go to https://railway.app"
    echo "2. Click 'New Project' → 'Deploy from GitHub repo'"
    echo "3. Select your repo and choose 'backend' folder"
    echo "4. Add these environment variables:"
    echo "   - YOU_API_KEY=your-api-key"
    echo "   - DATABASE_URL=postgresql://... (auto-provided)"
    echo "   - REDIS_URL=redis://... (auto-provided)"
    echo "   - SECRET_KEY=your-secret-key"
    echo "   - SMTP_HOST=smtp.gmail.com (optional)"
    echo "   - SMTP_USER=your-email (optional)"
    echo "   - SMTP_PASSWORD=your-password (optional)"
    echo ""
    echo "5. Add PostgreSQL and Redis services"
    echo "6. Deploy!"
    echo ""
    echo "Once deployed, update vercel.json with your Railway URL"
    echo ""
}

# Main deployment flow
main() {
    echo "Choose deployment option:"
    echo "1. Deploy frontend only (Vercel)"
    echo "2. Show backend deployment instructions (Railway)"
    echo "3. Deploy both"
    echo ""
    read -p "Enter choice (1-3): " choice

    case $choice in
        1)
            check_dependencies
            deploy_frontend
            ;;
        2)
            deploy_backend_instructions
            ;;
        3)
            check_dependencies
            deploy_frontend
            deploy_backend_instructions
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac

    echo ""
    echo "🎉 Deployment process complete!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Test your live demo URL"
    echo "2. Update HACKATHON_README.md with live links"
    echo "3. Record demo video using live site"
    echo "4. Submit to hackathon!"
    echo ""
}

# Run main function
main
