#!/bin/bash
# Campus AI Assistant - Classroom Deployment Script
# 
# This script automates the deployment process for classroom use.
# Run with: bash scripts/deploy_classroom.sh

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/campus-ai-assistant"
SERVICE_USER="campusai"
OLLAMA_MODEL="llama3:latest"

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        print_success "Detected OS: $OS"
    else
        print_error "Cannot detect OS"
        exit 1
    fi
}

install_system_dependencies() {
    print_header "Installing System Dependencies"
    
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y python3 python3-pip python3-venv git curl htop
        print_success "System dependencies installed"
    elif command -v yum &> /dev/null; then
        yum install -y python3 python3-pip git curl htop
        print_success "System dependencies installed"
    else
        print_error "Unsupported package manager"
        exit 1
    fi
}

install_ollama() {
    print_header "Installing Ollama"
    
    if command -v ollama &> /dev/null; then
        print_warning "Ollama already installed"
    else
        curl -fsSL https://ollama.ai/install.sh | sh
        print_success "Ollama installed"
    fi
    
    # Start Ollama service
    systemctl start ollama || true
    
    # Pull model
    print_info "Pulling $OLLAMA_MODEL (this may take several minutes)..."
    ollama pull $OLLAMA_MODEL
    print_success "Model $OLLAMA_MODEL downloaded"
}

create_service_user() {
    print_header "Creating Service User"
    
    if id "$SERVICE_USER" &>/dev/null; then
        print_warning "User $SERVICE_USER already exists"
    else
        useradd -r -s /bin/false $SERVICE_USER
        print_success "User $SERVICE_USER created"
    fi
}

setup_application() {
    print_header "Setting Up Application"
    
    # Create directory if it doesn't exist
    if [ ! -d "$INSTALL_DIR" ]; then
        mkdir -p $INSTALL_DIR
        print_success "Created $INSTALL_DIR"
    fi
    
    # Copy files (assumes script is run from project root)
    print_info "Copying application files..."
    cp -r ./* $INSTALL_DIR/ 2>/dev/null || true
    
    # Create data directories
    mkdir -p $INSTALL_DIR/data/documents
    mkdir -p $INSTALL_DIR/data/indices
    mkdir -p $INSTALL_DIR/data/logs
    print_success "Data directories created"
    
    # Set ownership
    chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
    print_success "Ownership set to $SERVICE_USER"
}

setup_python_environment() {
    print_header "Setting Up Python Environment"
    
    cd $INSTALL_DIR
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        sudo -u $SERVICE_USER python3 -m venv venv
        print_success "Virtual environment created"
    fi
    
    # Install dependencies
    print_info "Installing Python dependencies..."
    sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip install --upgrade pip
    sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip install -r requirements.txt
    print_success "Python dependencies installed"
}

create_ollama_service() {
    print_header "Creating Ollama Systemd Service"
    
    cat > /etc/systemd/system/ollama.service << 'EOF'
[Unit]
Description=Ollama Service
After=network.target

[Service]
Type=simple
User=ollama
Group=ollama
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3
Environment="OLLAMA_HOST=0.0.0.0:11434"

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable ollama
    systemctl start ollama
    
    print_success "Ollama service created and started"
}

create_campus_ai_service() {
    print_header "Creating Campus AI Systemd Service"
    
    cat > /etc/systemd/system/campus-ai.service << EOF
[Unit]
Description=Campus AI Assistant
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable campus-ai
    
    print_success "Campus AI service created"
}

setup_firewall() {
    print_header "Configuring Firewall"
    
    if command -v ufw &> /dev/null; then
        ufw allow 22/tcp comment 'SSH'
        ufw allow 8501/tcp comment 'Campus AI'
        ufw --force enable
        print_success "Firewall configured"
    else
        print_warning "UFW not available, skipping firewall configuration"
    fi
}

setup_log_rotation() {
    print_header "Setting Up Log Rotation"
    
    cat > /etc/logrotate.d/campus-ai << EOF
$INSTALL_DIR/data/logs/*.jsonl {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 $SERVICE_USER $SERVICE_USER
    sharedscripts
    postrotate
        systemctl reload campus-ai > /dev/null 2>&1 || true
    endscript
}
EOF

    print_success "Log rotation configured"
}

run_verification() {
    print_header "Running Deployment Verification"
    
    cd $INSTALL_DIR
    sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/python scripts/deploy_verify.py
}

print_completion() {
    print_header "Deployment Complete!"
    
    echo -e "${GREEN}Campus AI Assistant has been deployed successfully!${NC}\n"
    
    echo "Service Status:"
    systemctl status ollama --no-pager | head -3
    echo ""
    systemctl status campus-ai --no-pager | head -3
    
    echo -e "\n${BLUE}Next Steps:${NC}"
    echo "1. Add PDF documents to: $INSTALL_DIR/data/documents/"
    echo "2. Create FAQ file: $INSTALL_DIR/data/faq.json (optional)"
    echo "3. Build search indices: cd $INSTALL_DIR && sudo -u $SERVICE_USER venv/bin/python indexer.py"
    echo "4. Start the service: sudo systemctl start campus-ai"
    echo "5. Access the application: http://$(hostname -I | awk '{print $1}'):8501"
    
    echo -e "\n${BLUE}Useful Commands:${NC}"
    echo "• Check status: sudo systemctl status campus-ai"
    echo "• View logs: sudo journalctl -u campus-ai -f"
    echo "• Restart service: sudo systemctl restart campus-ai"
    echo "• Stop service: sudo systemctl stop campus-ai"
}

# Main deployment flow
main() {
    print_header "Campus AI Assistant - Classroom Deployment"
    
    print_info "This script will:"
    echo "  • Install system dependencies"
    echo "  • Install and configure Ollama"
    echo "  • Set up the application"
    echo "  • Create systemd services"
    echo "  • Configure firewall"
    echo "  • Set up log rotation"
    echo ""
    
    read -p "Continue with deployment? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelled"
        exit 0
    fi
    
    check_root
    check_os
    install_system_dependencies
    install_ollama
    create_service_user
    setup_application
    setup_python_environment
    create_ollama_service
    create_campus_ai_service
    setup_firewall
    setup_log_rotation
    
    print_completion
}

# Run main function
main
