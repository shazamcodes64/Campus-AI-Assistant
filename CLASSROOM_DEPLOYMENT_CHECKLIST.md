# Campus AI Assistant - Classroom Deployment Checklist

**Target Environment**: ~70 concurrent students, single-node deployment  
**Deployment Date**: _____________  
**Deployed By**: _____________

---

## Pre-Deployment Verification

### System Requirements Check
- [ ] Server has 8-16GB RAM (minimum 8GB)
- [ ] Server has 4+ CPU cores (8 cores recommended)
- [ ] Server has 50GB+ available storage (SSD preferred)
- [ ] Server has stable network connection (100 Mbps+)
- [ ] Operating system is Ubuntu 20.04+ or compatible Linux

### Software Prerequisites
- [ ] Python 3.9+ installed (`python3 --version`)
- [ ] pip package manager installed
- [ ] git installed (if cloning from repository)
- [ ] curl installed (for Ollama installation)
- [ ] Sufficient permissions (sudo access for service setup)

### Data Preparation
- [ ] Academic PDF documents collected and ready
- [ ] FAQ data prepared (optional but recommended)
- [ ] Documents reviewed for sensitive information
- [ ] Backup of all source materials created

---

## Installation Steps

### 1. System Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git curl

# Verify installations
python3 --version  # Should be 3.9+
pip3 --version
git --version
```
- [ ] System dependencies installed successfully
- [ ] Python version verified (3.9+)

### 2. Ollama Installation
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull LLM model (this downloads ~4GB)
ollama pull llama3:latest

# Verify installation
ollama list
```
- [ ] Ollama installed successfully
- [ ] llama3:latest model downloaded
- [ ] Ollama service running (`ollama serve` in background)

### 3. Application Setup
```bash
# Create application directory
sudo mkdir -p /opt/campus-ai-assistant
sudo chown $USER:$USER /opt/campus-ai-assistant
cd /opt/campus-ai-assistant

# Copy application files or clone repository
# (Copy your files here)

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```
- [ ] Application directory created
- [ ] Application files copied/cloned
- [ ] Virtual environment created
- [ ] Dependencies installed without errors

### 4. Data Directory Setup
```bash
# Create data directories
mkdir -p data/documents
mkdir -p data/indices
mkdir -p data/logs

# Copy PDF documents
cp /path/to/pdfs/*.pdf data/documents/

# Verify documents
ls -lh data/documents/
```
- [ ] Data directories created
- [ ] PDF documents copied (count: _____)
- [ ] Documents verified and accessible

### 5. FAQ Database Setup (Optional)
```bash
# Create or copy FAQ file
# Edit data/faq.json with your FAQ entries
nano data/faq.json
```
- [ ] FAQ file created/copied
- [ ] FAQ entries validated (JSON format correct)
- [ ] FAQ content reviewed for accuracy

### 6. Configuration Review
```bash
# Review configuration
cat config.json

# Verify settings:
# - ollama_url: http://localhost:11434
# - model_name: llama3:latest
# - embedding_model: all-MiniLM-L6-v2
# - Thresholds appropriate for your use case
```
- [ ] Configuration file reviewed
- [ ] Ollama URL correct
- [ ] Model names correct
- [ ] Thresholds appropriate

### 7. Build Search Indices
```bash
# Activate virtual environment
source venv/bin/activate

# Run indexer
python indexer.py

# Expected: Success message with chunk counts
```
- [ ] Indexer completed successfully
- [ ] FAISS index created (`data/indices/faiss.index`)
- [ ] BM25 index created (`data/indices/bm25_index.pkl`)
- [ ] Metadata file created (`data/indices/metadata.json`)
- [ ] No errors during indexing

**Indexing Time**: _____ minutes (for reference)

---

## Testing and Validation

### 8. System Tests
```bash
# Run system tests
python scripts/test_system.py
```
- [ ] All system tests passed
- [ ] Search engine loaded successfully
- [ ] LLM generator initialized
- [ ] No critical errors in output

### 9. Application Startup Test
```bash
# Start application (development mode)
streamlit run app.py

# Access at: http://localhost:8501
```
- [ ] Application starts without errors
- [ ] Web interface accessible
- [ ] System status shows green checkmarks
- [ ] No error messages in console

### 10. Functional Testing

**Test Query 1: FAQ Query**
- Query: _______________ (from your FAQ)
- [ ] Returns FAQ answer
- [ ] Confidence score ≥ 0.8
- [ ] Response time < 5 seconds

**Test Query 2: Document Query**
- Query: _______________ (from your documents)
- [ ] Returns relevant answer
- [ ] Shows source citations
- [ ] Response time < 10 seconds

**Test Query 3: Out-of-Scope Query**
- Query: "What's the weather today?"
- [ ] Properly rejects query
- [ ] Shows appropriate message
- [ ] No hallucinated response

**Test Query 4: Complex Query**
- Query: _______________ (multi-document query)
- [ ] Returns synthesized answer
- [ ] Multiple sources cited
- [ ] Response coherent and accurate

### 11. Performance Testing
```bash
# Run quick performance test
python scripts/quick_test.py
```
- [ ] Response times acceptable (< 10s for 95%)
- [ ] Memory usage reasonable (< 4GB typical)
- [ ] No memory leaks observed
- [ ] System stable after multiple queries

---

## Production Setup

### 12. Ollama as System Service
```bash
# Create systemd service file
sudo nano /etc/systemd/system/ollama.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama
sudo systemctl status ollama
```
- [ ] Ollama service file created
- [ ] Service enabled for auto-start
- [ ] Service running successfully
- [ ] Service status shows "active (running)"

### 13. Campus AI as System Service
```bash
# Create systemd service file
sudo nano /etc/systemd/system/campus-ai.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable campus-ai
sudo systemctl start campus-ai
sudo systemctl status campus-ai
```
- [ ] Campus AI service file created
- [ ] Service enabled for auto-start
- [ ] Service running successfully
- [ ] Service status shows "active (running)"

### 14. Firewall Configuration
```bash
# Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8501/tcp  # Streamlit
sudo ufw enable
sudo ufw status
```
- [ ] Firewall rules configured
- [ ] Required ports open
- [ ] SSH access maintained
- [ ] Firewall enabled

### 15. Log Rotation Setup
```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/campus-ai

# Test configuration
sudo logrotate -d /etc/logrotate.d/campus-ai
```
- [ ] Log rotation configured
- [ ] Configuration tested
- [ ] 30-day retention set

---

## Deployment Verification

### 16. Remote Access Test
- [ ] Access application from different computer
- [ ] URL: http://[server-ip]:8501
- [ ] Application loads correctly
- [ ] All features functional

### 17. Concurrent User Simulation
```bash
# Run load test (if available)
python scripts/load_test.py
```
- [ ] System handles 10+ concurrent requests
- [ ] No crashes or errors
- [ ] Response times acceptable under load
- [ ] Memory usage stable

### 18. 24-Hour Stability Test
- [ ] Application running for 24+ hours
- [ ] No crashes or restarts needed
- [ ] Memory usage stable (no leaks)
- [ ] Log files reasonable size
- [ ] No critical errors in logs

### 19. Backup Verification
```bash
# Create backup
tar -czf backup-$(date +%Y%m%d).tar.gz data/ config.json

# Verify backup
tar -tzf backup-$(date +%Y%m%d).tar.gz | head
```
- [ ] Backup created successfully
- [ ] Backup includes all data
- [ ] Backup stored in safe location
- [ ] Restore procedure documented

---

## Documentation and Training

### 20. Documentation Review
- [ ] README.md reviewed and accurate
- [ ] DEPLOYMENT.md complete and tested
- [ ] USER_GUIDE.md available for students
- [ ] TROUBLESHOOTING.md available
- [ ] Configuration documented

### 21. User Training Materials
- [ ] Quick start guide created
- [ ] Example queries documented
- [ ] FAQ about the system prepared
- [ ] Support contact information provided

### 22. Administrator Training
- [ ] Admin trained on system monitoring
- [ ] Admin trained on log review
- [ ] Admin trained on FAQ updates
- [ ] Admin trained on troubleshooting
- [ ] Admin trained on restart procedures

---

## Go-Live Checklist

### 23. Pre-Launch Verification
- [ ] All tests passed
- [ ] Services running and stable
- [ ] Monitoring in place
- [ ] Backup system working
- [ ] Support plan ready

### 24. Soft Launch (5-10 Students)
- [ ] Small group invited to test
- [ ] Feedback collected
- [ ] Issues documented
- [ ] Critical issues resolved
- [ ] Performance acceptable

### 25. Full Launch (All Students)
- [ ] Announcement sent to students
- [ ] Access instructions provided
- [ ] Support channels communicated
- [ ] Monitoring active
- [ ] On-call support available

---

## Post-Deployment Monitoring

### First 24 Hours
- [ ] Monitor service status every 2 hours
- [ ] Review logs for errors
- [ ] Track response times
- [ ] Monitor memory usage
- [ ] Collect user feedback

### First Week
- [ ] Daily log review
- [ ] Daily performance check
- [ ] User feedback analysis
- [ ] FAQ updates based on queries
- [ ] Document common issues

### First Month
- [ ] Weekly performance reports
- [ ] Weekly user satisfaction survey
- [ ] Monthly backup verification
- [ ] System optimization based on usage
- [ ] Plan Phase 2 features

---

## Rollback Plan

### If Critical Issues Occur
1. [ ] Stop campus-ai service: `sudo systemctl stop campus-ai`
2. [ ] Review logs: `sudo journalctl -u campus-ai -n 100`
3. [ ] Identify issue and fix
4. [ ] Test fix in development mode
5. [ ] Restart service: `sudo systemctl start campus-ai`
6. [ ] Verify functionality
7. [ ] Communicate status to users

### If Complete Rollback Needed
1. [ ] Stop all services
2. [ ] Restore from backup
3. [ ] Verify restored system
4. [ ] Restart services
5. [ ] Test functionality
6. [ ] Document incident

---

## Success Criteria

Deployment is considered successful when:

- [x] All installation steps completed without errors
- [x] All tests passed
- [x] Services running as systemd services
- [x] Application accessible remotely
- [x] Response time < 10 seconds (95th percentile)
- [x] System stable for 24+ hours
- [x] No critical errors in logs
- [x] Backup system operational
- [x] Documentation complete
- [x] Support plan in place

---

## Sign-Off

**Technical Lead**: _________________ Date: _______  
**System Administrator**: _________________ Date: _______  
**Project Manager**: _________________ Date: _______

---

## Notes and Issues

Document any issues encountered during deployment:

```
Issue 1:
Description:
Resolution:
Time to resolve:

Issue 2:
Description:
Resolution:
Time to resolve:
```

---

## Contact Information

**Technical Support**: _________________  
**System Administrator**: _________________  
**Emergency Contact**: _________________

---

## Appendix: Quick Reference Commands

### Check Service Status
```bash
sudo systemctl status ollama
sudo systemctl status campus-ai
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u campus-ai -f

# Last 100 lines
sudo journalctl -u campus-ai -n 100
```

### Restart Services
```bash
sudo systemctl restart ollama
sudo systemctl restart campus-ai
```

### Monitor Resources
```bash
# CPU and memory
htop

# Disk usage
df -h

# Log sizes
du -sh data/logs/
```

### Update FAQ (Hot Reload)
```bash
# Edit FAQ file
nano data/faq.json

# No restart needed - changes take effect immediately
```

### Rebuild Indices
```bash
cd /opt/campus-ai-assistant
source venv/bin/activate
python indexer.py
sudo systemctl restart campus-ai
```
