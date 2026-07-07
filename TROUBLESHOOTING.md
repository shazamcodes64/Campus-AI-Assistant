# Campus AI Assistant - Troubleshooting Guide

## Quick Diagnostic Checklist

Run through this checklist first:

- [ ] Is Ollama running? (`curl http://localhost:11434/api/tags`)
- [ ] Do indices exist? (`ls data/indices/`)
- [ ] Is Python environment activated? (`which python`)
- [ ] Are dependencies installed? (`pip list | grep streamlit`)
- [ ] Is port 8501 available? (`lsof -i :8501`)

---

## Common Issues and Solutions

### 1. Application Won't Start

#### Error: "ModuleNotFoundError"

**Symptom:**
```
ModuleNotFoundError: No module named 'streamlit'
```

**Cause:** Dependencies not installed or wrong Python environment

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Verify you're in the right environment
which python
# Should show: /path/to/campus-ai-assistant/venv/bin/python

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep streamlit
```

#### Error: "Address already in use"

**Symptom:**
```
OSError: [Errno 48] Address already in use
```

**Cause:** Port 8501 is already in use

**Solution:**
```bash
# Find process using port 8501
lsof -i :8501

# Kill the process
kill -9 <PID>

# Or use a different port
streamlit run app.py --server.port 8502
```

#### Error: "Python version too old"

**Symptom:**
```
ERROR: This package requires Python 3.9+
```

**Cause:** Python version is below 3.9

**Solution:**
```bash
# Check Python version
python3 --version

# Install Python 3.9+ (Ubuntu)
sudo apt install python3.11

# Create new venv with correct Python
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 2. Index/Search Issues

#### Error: "FAISS index not found"

**Symptom:**
```
RuntimeError: ❌ FAISS index not found. Run: python indexer.py first
```

**Cause:** Search indices haven't been built

**Solution:**
```bash
# Check if PDFs exist
ls data/documents/
# Should show PDF files

# Build indices
python indexer.py

# Verify indices were created
ls -lh data/indices/
# Should show: faiss.index, bm25_index.pkl, metadata.json
```

#### Error: "No PDF files found"

**Symptom:**
```
❌ No PDF files found in data/documents
```

**Cause:** No PDF files in documents directory

**Solution:**
```bash
# Create directory if it doesn't exist
mkdir -p data/documents

# Copy PDF files
cp /path/to/your/pdfs/*.pdf data/documents/

# Verify files
ls -lh data/documents/

# Run indexer
python indexer.py
```

#### Issue: "No search results for any query"

**Symptom:** All queries return "No relevant information found"

**Possible Causes:**
1. Indices are corrupted
2. PDFs contain no extractable text (scanned images)
3. Embedding model failed to load

**Solution:**
```bash
# 1. Check if metadata has content
cat data/indices/metadata.json | head -20

# 2. Rebuild indices
rm -rf data/indices/*
python indexer.py

# 3. Test with a simple query
python -c "
from engines import SearchEngine
import json
with open('config.json') as f:
    config = json.load(f)
engine = SearchEngine(config)
result = engine.search('test')
print(result)
"

# 4. Check if PDFs have text
python -c "
from PyPDF2 import PdfReader
reader = PdfReader('data/documents/your-file.pdf')
print(reader.pages[0].extract_text()[:200])
"
```

---

### 3. Ollama/LLM Issues

#### Error: "Cannot connect to Ollama service"

**Symptom:**
```
Cannot connect to Ollama service
LLM service unavailable
```

**Cause:** Ollama is not running

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve

# Or if using systemd
sudo systemctl start ollama
sudo systemctl status ollama

# Verify model is downloaded
ollama list
# Should show llama3:latest

# If model missing, pull it
ollama pull llama3:latest
```

#### Issue: "LLM responses are very slow"

**Symptom:** Queries take >30 seconds

**Possible Causes:**
1. Model is too large for available RAM
2. CPU is overloaded
3. Multiple concurrent requests

**Solution:**
```bash
# 1. Check system resources
htop
# Look at CPU and RAM usage

# 2. Use a smaller model
ollama pull llama3:8b  # Instead of 70b

# Update config.json
{
  "model_name": "llama3:8b"
}

# 3. Limit concurrent requests (in production)
# Edit systemd service to limit workers

# 4. Increase timeout in llm.py if needed
# (already set to 30s, but can adjust)
```

#### Error: "Model not found"

**Symptom:**
```
Error: model 'llama3:latest' not found
```

**Cause:** Model hasn't been downloaded

**Solution:**
```bash
# Pull the model
ollama pull llama3:latest

# This will download ~4GB, may take a while

# Verify
ollama list

# Test
ollama run llama3:latest "Hello"
```

---

### 4. Memory Issues

#### Error: "Out of memory" or System Freezes

**Symptom:** System becomes unresponsive, OOM killer activates

**Cause:** Insufficient RAM for models and indices

**Solution:**
```bash
# 1. Check current memory usage
free -h

# 2. Restart services to clear memory
sudo systemctl restart ollama
sudo systemctl restart campus-ai

# 3. Reduce chunk size in config.json
{
  "chunk_size": 400,  # Reduced from 512
  "chunk_overlap": 40  # Reduced from 50
}

# 4. Add swap space (temporary fix)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 5. Consider upgrading RAM or using smaller model
```

#### Issue: "Memory usage keeps growing"

**Symptom:** RAM usage increases over time

**Cause:** Memory leaks or cache not being cleared

**Solution:**
```bash
# 1. Restart application periodically
# Add to crontab for daily restart
0 3 * * * systemctl restart campus-ai

# 2. Monitor memory usage
watch -n 5 free -h

# 3. Check for memory leaks in logs
sudo journalctl -u campus-ai | grep -i memory

# 4. Clear Streamlit cache
# Add to app.py if needed:
# st.cache_data.clear()
# st.cache_resource.clear()
```

---

### 5. Performance Issues

#### Issue: "Slow response times (>10 seconds)"

**Symptom:** Queries consistently take longer than expected

**Diagnosis:**
```bash
# Run performance test
python scripts/test_system.py

# Check which component is slow
python -c "
import time
from engines import SearchEngine
from llm import LLMGenerator
import json

with open('config.json') as f:
    config = json.load(f)

# Test search
start = time.time()
engine = SearchEngine(config)
print(f'Engine load: {time.time()-start:.2f}s')

start = time.time()
result = engine.search('test query')
print(f'Search: {time.time()-start:.2f}s')

# Test LLM
start = time.time()
llm = LLMGenerator(config)
response = llm.generate_response('test', result)
print(f'Generation: {time.time()-start:.2f}s')
"
```

**Solutions:**

**If search is slow:**
```bash
# Reduce index size
# In config.json:
{
  "chunk_size": 400
}

# Rebuild indices
python indexer.py
```

**If LLM is slow:**
```bash
# Use smaller/faster model
ollama pull llama3:8b

# Update config.json
{
  "model_name": "llama3:8b"
}

# Reduce max_tokens
{
  "max_tokens": 300
}
```

**If model loading is slow:**
```bash
# Models are cached after first load
# Ensure @st.cache_resource is used in app.py
# (already implemented)

# Warm up cache on startup
python -c "
from engines import SearchEngine
from llm import LLMGenerator
import json
with open('config.json') as f:
    config = json.load(f)
engine = SearchEngine(config)
llm = LLMGenerator(config)
print('Models loaded and cached')
"
```

---

### 6. FAQ Issues

#### Issue: "FAQ not working"

**Symptom:** FAQ queries don't return direct answers

**Diagnosis:**
```bash
# Check if FAQ file exists
ls -lh data/faq.json

# Validate JSON syntax
python -c "
import json
with open('data/faq.json') as f:
    data = json.load(f)
print(f'FAQs loaded: {len(data.get(\"faqs\", []))}')
"

# Test FAQ search
python -c "
from engines import SearchEngine
import json
with open('config.json') as f:
    config = json.load(f)
engine = SearchEngine(config)
result = engine._search_faq('What is the placement process?')
print(result)
"
```

**Solutions:**

**If FAQ file is missing:**
```bash
# Create basic FAQ file
cat > data/faq.json << 'EOF'
{
  "faqs": [
    {
      "id": "faq_001",
      "question": "What is the placement process?",
      "answer": "The placement process consists of..."
    }
  ]
}
EOF
```

**If FAQ not matching:**
```bash
# Check threshold in config.json
{
  "faq_threshold": 0.8  # Lower to 0.7 if too strict
}

# FAQ questions need to be similar to user queries
# Update FAQ questions to match common phrasings
```

---

### 7. Streamlit-Specific Issues

#### Error: "Streamlit command not found"

**Symptom:**
```
bash: streamlit: command not found
```

**Cause:** Virtual environment not activated or Streamlit not installed

**Solution:**
```bash
# Activate venv
source venv/bin/activate

# Verify streamlit is installed
which streamlit

# If not found, install
pip install streamlit

# Run app
streamlit run app.py
```

#### Issue: "Streamlit keeps reloading"

**Symptom:** App reloads constantly, can't interact

**Cause:** File watcher detecting changes

**Solution:**
```bash
# Disable file watcher
streamlit run app.py --server.fileWatcherType none

# Or add to .streamlit/config.toml
mkdir -p .streamlit
cat > .streamlit/config.toml << 'EOF'
[server]
fileWatcherType = "none"
EOF
```

#### Issue: "Can't access from other machines"

**Symptom:** Works on localhost but not from other computers

**Cause:** Streamlit bound to localhost only

**Solution:**
```bash
# Bind to all interfaces
streamlit run app.py --server.address 0.0.0.0

# Check firewall
sudo ufw status
sudo ufw allow 8501/tcp

# Verify it's listening
netstat -tuln | grep 8501
```

---

### 8. Data/Content Issues

#### Issue: "Answers are incorrect or irrelevant"

**Symptom:** System returns wrong information

**Diagnosis:**
1. Check source documents are correct
2. Verify indexing completed successfully
3. Test with known-good queries

**Solutions:**
```bash
# 1. Verify document content
python -c "
from PyPDF2 import PdfReader
reader = PdfReader('data/documents/your-file.pdf')
for i, page in enumerate(reader.pages[:3]):
    print(f'Page {i+1}:')
    print(page.extract_text()[:200])
    print('---')
"

# 2. Check metadata
cat data/indices/metadata.json | jq '.[0:3]'

# 3. Rebuild indices with fresh documents
rm -rf data/indices/*
python indexer.py

# 4. Test specific query
python -c "
from engines import SearchEngine
import json
with open('config.json') as f:
    config = json.load(f)
engine = SearchEngine(config)
result = engine.search('your test query')
print('Type:', result['type'])
print('Confidence:', result['confidence'])
if result['type'] == 'document':
    for chunk in result['result']['chunks']:
        print('Source:', chunk['source'], 'Page:', chunk['page'])
        print('Text:', chunk['text'][:100])
"
```

#### Issue: "PDFs not being indexed properly"

**Symptom:** Indexer runs but creates empty or small indices

**Possible Causes:**
1. PDFs are scanned images (no text layer)
2. PDFs are password protected
3. PDFs have encoding issues

**Solutions:**
```bash
# 1. Check if PDF has text
pdftotext data/documents/your-file.pdf - | head -20

# If empty, PDF is likely scanned images
# Need OCR: use tools like ocrmypdf

# 2. Check for password protection
python -c "
from PyPDF2 import PdfReader
reader = PdfReader('data/documents/your-file.pdf')
print('Encrypted:', reader.is_encrypted)
print('Pages:', len(reader.pages))
"

# 3. Try alternative PDF library
pip install pdfplumber
python -c "
import pdfplumber
with pdfplumber.open('data/documents/your-file.pdf') as pdf:
    print('Pages:', len(pdf.pages))
    print('First page text:', pdf.pages[0].extract_text()[:200])
"
```

---

### 9. Deployment Issues

#### Issue: "Works locally but not on server"

**Symptom:** Application runs fine on development machine but fails on server

**Common Causes:**
1. Different Python versions
2. Missing system dependencies
3. Firewall blocking ports
4. Insufficient permissions

**Solutions:**
```bash
# 1. Check Python version matches
python3 --version

# 2. Install system dependencies (Ubuntu)
sudo apt install -y python3-dev build-essential

# 3. Check firewall
sudo ufw status
sudo ufw allow 8501/tcp
sudo ufw allow 11434/tcp

# 4. Check permissions
ls -la /opt/campus-ai-assistant
# Should be owned by service user

# 5. Check SELinux (if applicable)
getenforce
# If enforcing, may need to adjust policies
```

#### Issue: "Service won't start on boot"

**Symptom:** Manual start works but systemd service fails

**Diagnosis:**
```bash
# Check service status
sudo systemctl status campus-ai

# View logs
sudo journalctl -u campus-ai -n 50

# Check service file
cat /etc/systemd/system/campus-ai.service
```

**Solutions:**
```bash
# 1. Verify paths in service file
# WorkingDirectory should be absolute
# ExecStart should use full path to streamlit

# 2. Check dependencies
# Ensure ollama.service starts first

# 3. Reload systemd
sudo systemctl daemon-reload

# 4. Enable service
sudo systemctl enable campus-ai

# 5. Test start
sudo systemctl start campus-ai
sudo systemctl status campus-ai
```

---

### 10. Logging and Debugging

#### Enable Debug Logging

**In app.py:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**In engines.py and llm.py:**
```python
# Add print statements for debugging
print(f"DEBUG: Query: {query}")
print(f"DEBUG: Result type: {result['type']}")
```

#### View Logs

```bash
# Application logs (if using systemd)
sudo journalctl -u campus-ai -f

# Streamlit logs
tail -f ~/.streamlit/logs/streamlit.log

# Interaction logs
tail -f data/logs/interactions.jsonl

# System logs
tail -f /var/log/syslog | grep campus
```

#### Test Individual Components

```bash
# Test search engine
python -c "
from engines import SearchEngine
import json
with open('config.json') as f:
    config = json.load(f)
engine = SearchEngine(config)
result = engine.search('test query')
print(result)
"

# Test LLM
python -c "
from llm import LLMGenerator
import json
with open('config.json') as f:
    config = json.load(f)
llm = LLMGenerator(config)
print('Connection:', llm.test_connection())
"

# Test indexer
python indexer.py
```

---

## Emergency Procedures

### Complete System Reset

If everything is broken:

```bash
# 1. Stop all services
sudo systemctl stop campus-ai
sudo systemctl stop ollama

# 2. Backup current state
tar -czf backup-$(date +%Y%m%d).tar.gz data/ config.json

# 3. Clean everything
rm -rf data/indices/*
rm -rf venv/

# 4. Reinstall
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Rebuild indices
python indexer.py

# 6. Restart services
sudo systemctl start ollama
sudo systemctl start campus-ai

# 7. Test
curl http://localhost:8501
```

### Rollback to Previous Version

```bash
# 1. Stop service
sudo systemctl stop campus-ai

# 2. Restore from backup
cd /opt/campus-ai-assistant
tar -xzf /backup/campus-ai/backup-YYYYMMDD.tar.gz

# 3. Restart
sudo systemctl start campus-ai
```

---

## Getting Help

### Information to Collect

When reporting issues, include:

1. **Error messages** (exact text)
2. **System info**:
   ```bash
   uname -a
   python3 --version
   pip list
   ```
3. **Service status**:
   ```bash
   sudo systemctl status campus-ai
   sudo systemctl status ollama
   ```
4. **Recent logs**:
   ```bash
   sudo journalctl -u campus-ai -n 100
   ```
5. **Configuration**:
   ```bash
   cat config.json
   ```

### Diagnostic Script

Run this to collect all diagnostic info:

```bash
#!/bin/bash
echo "=== System Info ===" > diagnostic.txt
uname -a >> diagnostic.txt
python3 --version >> diagnostic.txt
echo "" >> diagnostic.txt

echo "=== Service Status ===" >> diagnostic.txt
systemctl status campus-ai >> diagnostic.txt 2>&1
systemctl status ollama >> diagnostic.txt 2>&1
echo "" >> diagnostic.txt

echo "=== Disk Space ===" >> diagnostic.txt
df -h >> diagnostic.txt
echo "" >> diagnostic.txt

echo "=== Memory ===" >> diagnostic.txt
free -h >> diagnostic.txt
echo "" >> diagnostic.txt

echo "=== Indices ===" >> diagnostic.txt
ls -lh data/indices/ >> diagnostic.txt 2>&1
echo "" >> diagnostic.txt

echo "=== Recent Logs ===" >> diagnostic.txt
journalctl -u campus-ai -n 50 >> diagnostic.txt 2>&1

echo "Diagnostic info saved to diagnostic.txt"
```

---

## Prevention Tips

1. **Regular backups**: Backup data/ directory daily
2. **Monitor resources**: Set up alerts for high CPU/RAM
3. **Update regularly**: Keep dependencies updated
4. **Test before deploying**: Always test in staging first
5. **Document changes**: Keep a changelog of modifications
6. **Monitor logs**: Review logs weekly for patterns
7. **Capacity planning**: Monitor usage trends

---

## Quick Reference

### Essential Commands

```bash
# Start application
streamlit run app.py

# Rebuild indices
python indexer.py

# Test system
python scripts/test_system.py

# Check Ollama
curl http://localhost:11434/api/tags

# View logs
tail -f data/logs/interactions.jsonl

# Restart services
sudo systemctl restart campus-ai ollama
```

### Configuration Files

- `config.json` - Main configuration
- `.streamlit/config.toml` - Streamlit settings
- `/etc/systemd/system/campus-ai.service` - Service definition
- `data/faq.json` - FAQ database

### Important Paths

- Application: `/opt/campus-ai-assistant`
- Documents: `data/documents/`
- Indices: `data/indices/`
- Logs: `data/logs/`
- Virtual env: `venv/`

---

This troubleshooting guide covers the most common issues. For issues not covered here, check the logs and run diagnostic tests to identify the root cause.
