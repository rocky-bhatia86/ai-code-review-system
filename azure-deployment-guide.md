# 🚀 Azure VM Deployment Guide for AI Code Review System

## Phase 1: Create Azure VM

### 1.1 Create VM in Azure Portal
```bash
# VM Specifications (Recommended)
- Size: Standard B2s (2 vCPUs, 4 GB RAM) - Minimum
- Size: Standard D2s_v3 (2 vCPUs, 8 GB RAM) - Recommended
- OS: Ubuntu 22.04 LTS
- Authentication: SSH public key
- Ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 8001 (API)
```

### 1.2 Connect to VM
```bash
# SSH into your VM
ssh azureuser@your-vm-ip-address

# Update system
sudo apt update && sudo apt upgrade -y
```

## Phase 2: Install Dependencies

### 2.1 Install Python and Node.js
```bash
# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Git
sudo apt install -y git curl wget nginx

# Verify installations
python3.11 --version
node --version
npm --version
```

### 2.2 Install Process Manager
```bash
# Install PM2 for process management
sudo npm install -g pm2

# Install Python packages system-wide
sudo apt install -y python3-pip
```

## Phase 3: Deploy Application

### 3.1 Clone Repository
```bash
# Clone your code
cd /home/azureuser
git clone https://github.com/rocky-bhatia86/ai-code-review-system.git
cd ai-code-review-system

# Or upload your local code
# scp -r ./ai_code_review_project azureuser@your-vm-ip:/home/azureuser/
```

### 3.2 Setup Backend
```bash
# Create Python virtual environment
cd backend
sudo apt install python3.8-venv
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Test backend locally
python -c "from main import app; print('✅ Backend imports successful')"
```

### 3.3 Setup Frontend
```bash
# Install frontend dependencies
cd ../frontend
npm install

# Build production version
npm run build

# The build folder contains the static files
ls -la build/
```

## Phase 4: Environment Variables

### 4.1 Create Environment File
```bash
# Create .env file in project root
cd /home/azureuser/ai_code_review_project
cat > .env << 'EOF'
# AI Code Review System - Production Configuration

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# GitHub Integration
GITHUB_TOKEN=your_github_token_here
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# Server Configuration
HOST=0.0.0.0
PORT=8001
ENVIRONMENT=production

# Security
SECRET_KEY=your_secret_key_here
EOF

# Set proper permissions
chmod 600 .env
```

### 4.2 Load Environment Variables
```bash
# Create a script to load environment variables
cat > start_backend.sh << 'EOF'
#!/bin/bash
cd /home/azureuser/ai_code_review_project/backend
source venv/bin/activate
source ../.env
export OPENAI_API_KEY
export GITHUB_TOKEN
export GITHUB_WEBHOOK_SECRET
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2
EOF

chmod +x start_backend.sh
```

