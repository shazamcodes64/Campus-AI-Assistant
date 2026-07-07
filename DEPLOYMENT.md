# Campus AI Assistant - Deployment Guide

## Single-Node Deployment for Classroom Use

This guide covers deploying the Campus AI Assistant MVP for ~70 concurrent students on a single server.

---

## System Requirements

### Minimum Hardware
- **CPU**: 4 cores (8 cores recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB SSD
- **Network**: 100 Mbps connection

### Operating System
- Ubuntu 20.04+ (recommended)
- macOS 12+ (for development/testing)
- Other Linux distributions (should work but not tested)

### Software Prerequisites
- Python 3.9+
- pip package manager
- Ollama (for local LLM)

---

## Pre-Deployment Checklist

- [ ] Server meets minimum hardware requirements
- [ ] Python 3.9+ installed
- [ ] Network access to server (SSH for remote deployment)
- [ ] Academic PDF documents ready for indexing
- [ ] FAQ data prepared (optional but recommended)

---

## Step-by-Step Deployment

### 1. Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git curl
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11
```

### 2. Install and Configure Ollama

#### Install Ollama
```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Pull LLM Model
```bash
# Pull the model (this will download ~4GB)
ollama pull llama3:latest

# Verify installation
ollama list
```

#### Start Ollama Service
```bash
# Start Ollama (runs on http://localhost:11434)
ollama serve
```

**Note**: For production, set up Ollama as a systemd service (see Ollama Service Setup section below).

### 3. Clone and Setup Application

```bash
# Clone repository (or copy files to server)
cd /opt
sudo mkdir campus-ai-assistant
sudo chown $USER:$USER campus-ai-assistant
cd campus-ai-assistant

# Copy your application files here
# (or git clone if using version control)

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Prepare Data

#### Create Data Directories
```bash
mkdir -p data/documents
mkdir -p data/indices
mkdir -p data/logs
```

#### Add PDF Documents
```bash
# Copy your academic PDFs to data/documents/
cp /path/to/your/pdfs/*.pdf data/documents/

# Verify files
ls -lh data/documents/
```

#### Create FAQ Database (Optional)
```bash
# Create data/faq.json
cat > data/faq.json << 'EOF'
{
  "faqs": [
    {
      "id": "faq_001",
      "question": "What is the placement process?",
      "answer": "The placement process consists of multiple stages: application submission, aptitude tests, technical interviews, HR interviews, and final selection. Students must maintain minimum CGPA requirements."
    },
    {
      "id": "faq_002",
      "question": "What are the course requirements?",
      "answer": "Course requirements vary by program. Generally, students must complete core courses, electives, laboratory work, and a final project. Check your program syllabus for details."
    },
    {
      "id": "faq_003",
      "question": "How do I access the syllabus?",
      "answer": "The syllabus is available through the course portal, academic office, or from your instructor. It contains course objectives, topics, evaluation criteria, and schedules."
    }
  ]
}
EOF
```

### 5. Configure Application

#### Review config.json
```bash
cat config.json
```

#### Adjust Settings (if needed)
```json
{
  "ollama_url": "http://localhost:11434",
  "model_name": "llama3:latest",
  "embedding_model": "all-MiniLM-L6-v2",
  "faq_threshold": 0.8,
  "doc_threshold": 0.5,
  "high_similarity_threshold": 0.85,
  "max_tokens": 500,
  "temperature": 0.3,
  "chunk_size": 512,
  "chunk_overlap": 50
}
```

### 6. Build Search Indices

```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Run indexer
python indexer.py

# Expected output:
# 🔄 Starting document indexing...
# 📄 Found X PDF files
# Processing: file1.pdf
#   → Y chunks extracted
# ...
# ✅ Indexing complete!
```

**This step may take 5-15 minutes depending on document size.**

### 7. Test the System

```bash
# Run system tests
python scripts/test_system.py

# Expected output:
# 🧪 CAMPUS AI ASSISTANT - STRESS TESTING
# 🔍 Testing Search Engine...
# ✅ Search engine loaded
# ...
# 🎉 All tests passed! System is robust.
```

### 8. Start the Application

#### Development/Testing Mode
```bash
# Start Streamlit (development mode)
streamlit run app.py

# Access at: http://localhost:8501
```

#### Production Mode
```bash
# Start Streamlit on specific port with production settings
streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false
```

### 9. Verify Deployment

1. **Open browser**: Navigate to `http://your-server-ip:8501`
2. **Check system status**: Verify green checkmarks in sidebar
3. **Test query**: Try "What is the syllabus?"
4. **Verify response**: Check that answer includes sources
5. **Test FAQ**: Try a question from your FAQ database
6. **Test out-of-scope**: Try "What's the weather?" (should reject)

---

## Production Setup

### Ollama as Systemd Service

Create `/etc/systemd/system/ollama.service`:

```ini
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
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama
sudo systemctl status ollama
```

### Streamlit as Systemd Service

Create `/etc/systemd/system/campus-ai.service`:

```ini
[Unit]
Description=Campus AI Assistant
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=campusai
Group=campusai
WorkingDirectory=/opt/campus-ai-assistant
Environment="PATH=/opt/campus-ai-assistant/venv/bin"
ExecStart=/opt/campus-ai-assistant/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable campus-ai
sudo systemctl start campus-ai
sudo systemctl status campus-ai
```

### Nginx Reverse Proxy (Optional)

Install Nginx:
```bash
sudo apt install nginx
```

Create `/etc/nginx/sites-available/campus-ai`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/campus-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Monitoring and Maintenance

### Check Service Status
```bash
# Check Ollama
sudo systemctl status ollama

# Check Campus AI
sudo systemctl status campus-ai

# View logs
sudo journalctl -u campus-ai -f
```

### Monitor Resource Usage
```bash
# CPU and memory
htop

# Disk usage
df -h

# Check log sizes
du -sh data/logs/
```

### Log Rotation

Create `/etc/logrotate.d/campus-ai`:

```
/opt/campus-ai-assistant/data/logs/*.jsonl {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 campusai campusai
    sharedscripts
    postrotate
        systemctl reload campus-ai > /dev/null 2>&1 || true
    endscript
}
```

### Backup Strategy

```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/backup/campus-ai"
DATE=$(date +%Y%m%d)

# Backup data
tar -czf $BACKUP_DIR/data-$DATE.tar.gz data/

# Backup config
cp config.json $BACKUP_DIR/config-$DATE.json

# Keep last 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

---

## Troubleshooting

### Application Won't Start

**Check Python version:**
```bash
python3 --version  # Should be 3.9+
```

**Check dependencies:**
```bash
source venv/bin/activate
pip list
```

**Check Ollama:**
```bash
curl http://localhost:11434/api/tags
```

### No Search Results

**Verify indices exist:**
```bash
ls -lh data/indices/
# Should see: faiss.index, bm25_index.pkl, metadata.json
```

**Rebuild indices:**
```bash
python indexer.py
```

### Slow Response Times

**Check Ollama model:**
```bash
ollama list
# Ensure llama3:latest is downloaded
```

**Monitor resources:**
```bash
htop
# Check CPU and RAM usage
```

**Reduce chunk size** (in config.json):
```json
{
  "chunk_size": 400,
  "chunk_overlap": 40
}
```

### Memory Issues

**Check memory usage:**
```bash
free -h
```

**Restart services:**
```bash
sudo systemctl restart ollama
sudo systemctl restart campus-ai
```

**Increase swap** (if needed):
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Security Considerations

### Firewall Configuration
```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP (if using Nginx)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow Streamlit (if direct access)
sudo ufw allow 8501/tcp

# Enable firewall
sudo ufw enable
```

### User Permissions
```bash
# Create dedicated user
sudo useradd -r -s /bin/false campusai

# Set ownership
sudo chown -R campusai:campusai /opt/campus-ai-assistant
```

### Data Privacy
- Keep all data local (no external API calls)
- Regularly review logs for sensitive information
- Implement log anonymization if needed

---

## Performance Tuning

### For 70 Concurrent Users

**Increase Streamlit workers** (if needed):
```bash
streamlit run app.py --server.maxUploadSize 200
```

**Optimize Ollama**:
```bash
# Set environment variables
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=1
```

**Monitor and adjust**:
- Watch response times during peak usage
- Monitor memory usage
- Adjust chunk_size if needed
- Consider caching frequently asked questions

---

## Updating the Application

### Update Code
```bash
cd /opt/campus-ai-assistant
source venv/bin/activate

# Pull latest changes (if using git)
git pull

# Or copy updated files

# Restart service
sudo systemctl restart campus-ai
```

### Update Dependencies
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
sudo systemctl restart campus-ai
```

### Update Documents
```bash
# Add new PDFs
cp /path/to/new/*.pdf data/documents/

# Rebuild indices
python indexer.py

# Restart application
sudo systemctl restart campus-ai
```

### Update FAQ
```bash
# Edit FAQ file
nano data/faq.json

# No restart needed (hot-reload enabled)
```

---

## Support and Maintenance

### Regular Maintenance Tasks

**Daily:**
- Monitor service status
- Check error logs

**Weekly:**
- Review query logs for patterns
- Check disk space
- Verify backup completion

**Monthly:**
- Update system packages
- Review and update FAQ based on common queries
- Analyze performance metrics

### Getting Help

**Check logs:**
```bash
# Application logs
tail -f data/logs/interactions.jsonl

# System logs
sudo journalctl -u campus-ai -n 100
```

**Run diagnostics:**
```bash
python scripts/test_system.py
```

---

## Rollback Procedure

If deployment fails:

1. **Stop services:**
   ```bash
   sudo systemctl stop campus-ai
   sudo systemctl stop ollama
   ```

2. **Restore from backup:**
   ```bash
   cd /opt/campus-ai-assistant
   tar -xzf /backup/campus-ai/data-YYYYMMDD.tar.gz
   cp /backup/campus-ai/config-YYYYMMDD.json config.json
   ```

3. **Restart services:**
   ```bash
   sudo systemctl start ollama
   sudo systemctl start campus-ai
   ```

---

## Success Criteria

Deployment is successful when:

- [ ] Application accessible at configured URL
- [ ] System status shows all green checkmarks
- [ ] Test queries return relevant answers with sources
- [ ] FAQ queries return direct answers
- [ ] Out-of-scope queries are properly rejected
- [ ] Response time < 10 seconds for 95% of queries
- [ ] System stable for 24+ hours of continuous operation
- [ ] No critical errors in logs

---

## Next Steps After Deployment

1. **User Acceptance Testing**: Have 5-10 students test the system
2. **Collect Feedback**: Gather initial user feedback
3. **Monitor Performance**: Track response times and error rates
4. **Iterate**: Make adjustments based on real usage patterns
5. **Plan Phase 2**: Prioritize advanced features based on actual needs

---

## Contact and Support

For issues or questions:
- Check troubleshooting section above
- Review logs for error messages
- Run test_system.py for diagnostics
- Document issues for future reference
