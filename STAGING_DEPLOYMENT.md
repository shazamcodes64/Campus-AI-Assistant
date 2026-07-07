# Staging Deployment Guide - Campus AI Assistant

## Current Status

✅ **Core System**: Fully implemented and functional
✅ **Documentation**: Complete
✅ **Testing Scripts**: Load testing and validation ready
⚠️ **Indices**: Built (need PDFs for full testing)
🔄 **Ready for**: Staging deployment and load testing

---

## Pre-Deployment Checklist

### System Validation
```bash
# Run quick validation
python3 -c "
import os
checks = [
    ('app.py', os.path.exists('app.py')),
    ('engines.py', os.path.exists('engines.py')),
    ('llm.py', os.path.exists('llm.py')),
    ('config.json', os.path.exists('config.json')),
    ('indices', os.path.exists('data/indices/faiss.index'))
]
for name, ok in checks:
    print(f\"{'✅' if ok else '❌'} {name}\")
"
```

### Required Components
- [x] Core application files (app.py, engines.py, llm.py, indexer.py)
- [x] Configuration (config.json)
- [x] Search indices (FAISS + BM25)
- [x] Testing scripts (load_test.py, validate_deployment.py)
- [x] Documentation (5 comprehensive guides)
- [ ] PDF documents (add to data/documents/)
- [ ] Ollama running with llama3:latest

---

## Quick Start - Local Staging

### 1. Verify Ollama is Running

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve

# Verify model is available
ollama list | grep llama3
```

### 2. Add Test Documents (Optional but Recommended)

```bash
# Copy your PDF files
cp /path/to/your/pdfs/*.pdf data/documents/

# Rebuild indices if you added new documents
python3 indexer.py
```

### 3. Start the Application

```bash
# Start Streamlit
streamlit run app.py

# Or with specific settings
streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true
```

### 4. Verify Application is Running

```bash
# Check if accessible
curl http://localhost:8501

# Or open in browser
open http://localhost:8501
```

---

## Load Testing

### Test 1: Single User Baseline

```bash
# Test with 1 user, 5 queries
python3 scripts/load_test.py --users 1 --queries 5
```

**Expected Results:**
- All queries succeed
- Average latency < 5 seconds
- P95 latency < 10 seconds

### Test 2: Small Group (10 Users)

```bash
# Test with 10 concurrent users
python3 scripts/load_test.py --users 10 --queries 5
```

**Expected Results:**
- Success rate > 95%
- Average latency < 8 seconds
- P95 latency < 15 seconds
- No crashes or errors

### Test 3: Classroom Load (70 Users)

```bash
# Test with 70 concurrent users (target load)
python3 scripts/load_test.py --users 70 --queries 3 --output classroom_load_test.json
```

**Expected Results:**
- Success rate > 90%
- P95 latency < 20 seconds
- System remains stable
- Memory usage < 8GB

### Test 4: Stress Test (100 Users)

```bash
# Stress test beyond target
python3 scripts/load_test.py --users 100 --queries 2
```

**Purpose:** Identify breaking point and failure modes

---

## Performance Monitoring During Tests

### Monitor System Resources

```bash
# Terminal 1: Run load test
python3 scripts/load_test.py --users 70 --queries 3

# Terminal 2: Monitor resources
watch -n 1 'echo "=== CPU & Memory ==="; ps aux | grep -E "(streamlit|ollama|python)" | grep -v grep; echo ""; echo "=== Memory ==="; free -h'
```

### Monitor Application Logs

```bash
# Watch Streamlit logs
tail -f ~/.streamlit/logs/streamlit.log

# Watch interaction logs (if configured)
tail -f data/logs/interactions.jsonl
```

### Monitor Ollama

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Monitor Ollama logs (if running as service)
journalctl -u ollama -f
```

---

## Interpreting Load Test Results

### Success Criteria

✅ **Excellent Performance:**
- Success rate: 100%
- Average latency: < 5s
- P95 latency: < 10s
- No errors

✅ **Good Performance (Acceptable for MVP):**
- Success rate: > 95%
- Average latency: < 8s
- P95 latency: < 15s
- Minimal errors (< 5%)

⚠️ **Needs Optimization:**
- Success rate: 90-95%
- Average latency: 8-12s
- P95 latency: 15-20s
- Some errors (5-10%)

❌ **Not Ready for Production:**
- Success rate: < 90%
- Average latency: > 12s
- P95 latency: > 20s
- Frequent errors (> 10%)

### Common Issues and Solutions

**Issue: High latency (>10s average)**
- **Cause**: Model loading, slow embeddings, or LLM generation
- **Solution**: 
  - Use smaller model (llama3:8b instead of 70b)
  - Reduce chunk_size in config.json
  - Enable caching (already implemented)

**Issue: Memory exhaustion**
- **Cause**: Too many concurrent model instances
- **Solution**:
  - Reduce concurrent users
  - Add garbage collection (see optimization section)
  - Increase system RAM

**Issue: Connection errors to Ollama**
- **Cause**: Ollama overloaded or crashed
- **Solution**:
  - Restart Ollama
  - Increase Ollama timeout
  - Use smaller model

**Issue: Low success rate**
- **Cause**: Application crashes or errors
- **Solution**:
  - Check logs for errors
  - Verify indices are valid
  - Test with single user first

---

## Performance Optimization

### If Load Tests Show Issues

#### 1. Optimize Configuration

Edit `config.json`:

```json
{
  "ollama_url": "http://localhost:11434",
  "model_name": "llama3:8b",  // Use smaller model
  "embedding_model": "all-MiniLM-L6-v2",
  "faq_threshold": 0.8,
  "doc_threshold": 0.5,
  "high_similarity_threshold": 0.85,
  "max_tokens": 300,  // Reduced from 500
  "temperature": 0.3,
  "chunk_size": 400,  // Reduced from 512
  "chunk_overlap": 40  // Reduced from 50
}
```

#### 2. Add Memory Management

Add to `engines.py` and `llm.py`:

```python
import gc

# After processing queries
gc.collect()
```

#### 3. Optimize Streamlit Caching

Verify `app.py` has proper caching (already implemented):

```python
@st.cache_resource
def load_search_engine():
    config = load_config()
    return SearchEngine(config)

@st.cache_resource  
def load_llm_generator():
    config = load_config()
    return LLMGenerator(config)
```

#### 4. Use Lighter Model

```bash
# Pull smaller model
ollama pull llama3:8b

# Update config.json
{
  "model_name": "llama3:8b"
}
```

---

## Staging Environment Setup

### Option 1: Local Staging (Development Machine)

**Pros:**
- Quick setup
- Easy debugging
- No additional infrastructure

**Cons:**
- Not representative of production
- Limited concurrent user testing

**Setup:**
```bash
# Already done - just run the app
streamlit run app.py
```

### Option 2: Dedicated Staging Server

**Pros:**
- Production-like environment
- Better load testing
- Isolated from development

**Cons:**
- Requires additional server
- More setup time

**Setup:**
```bash
# On staging server
git clone <repository>
cd campus-ai-assistant

# Follow DEPLOYMENT.md for full setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy data and build indices
cp -r /path/to/pdfs data/documents/
python3 indexer.py

# Start services
ollama serve &
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

---

## Load Testing Scenarios

### Scenario 1: Morning Rush (Peak Load)

Simulates students accessing system before class:

```bash
# 70 users, 3 queries each, over 5 minutes
python3 scripts/load_test.py --users 70 --queries 3
```

### Scenario 2: Sustained Usage

Simulates continuous usage throughout the day:

```bash
# Run multiple rounds
for i in {1..5}; do
  echo "Round $i"
  python3 scripts/load_test.py --users 20 --queries 5
  sleep 60
done
```

### Scenario 3: Exam Period Spike

Simulates high load during exam preparation:

```bash
# 100 users, 5 queries each
python3 scripts/load_test.py --users 100 --queries 5
```

---

## Validation Checklist

### Before Load Testing
- [ ] Ollama running and model loaded
- [ ] Application starts without errors
- [ ] Single query test successful
- [ ] Indices loaded correctly
- [ ] System resources adequate (8GB+ RAM)

### During Load Testing
- [ ] Monitor CPU usage (should stay < 80%)
- [ ] Monitor memory usage (should stay < 8GB)
- [ ] Monitor response times
- [ ] Check for errors in logs
- [ ] Verify no crashes

### After Load Testing
- [ ] Review test results
- [ ] Analyze performance metrics
- [ ] Identify bottlenecks
- [ ] Document issues found
- [ ] Plan optimizations if needed

---

## Next Steps Based on Results

### If Tests Pass (Success Rate > 95%, P95 < 15s)
1. ✅ Mark system as staging-validated
2. ✅ Proceed to user acceptance testing
3. ✅ Plan production deployment
4. ✅ Prepare monitoring and support

### If Tests Show Issues (Success Rate < 95% or P95 > 15s)
1. ⚠️ Analyze failure patterns
2. ⚠️ Implement optimizations
3. ⚠️ Re-run load tests
4. ⚠️ Consider infrastructure upgrades

### If Tests Fail Completely (Success Rate < 80%)
1. ❌ Review system logs for errors
2. ❌ Test with single user to isolate issues
3. ❌ Fix critical bugs
4. ❌ Re-validate before load testing

---

## Troubleshooting Load Test Issues

### Load Test Won't Start

```bash
# Check Python path
python3 -c "import sys; print(sys.path)"

# Verify imports work
python3 -c "from engines import SearchEngine; print('OK')"

# Check if indices exist
ls -lh data/indices/
```

### Load Test Crashes

```bash
# Check memory
free -h

# Check disk space
df -h

# Check for errors
tail -50 ~/.streamlit/logs/streamlit.log
```

### Inconsistent Results

```bash
# Clear caches
rm -rf ~/.streamlit/cache

# Restart Ollama
pkill ollama
ollama serve &

# Restart application
# (Ctrl+C and restart streamlit)
```

---

## Reporting Results

### Create Test Report

After running load tests, document:

1. **Test Configuration**
   - Number of users
   - Queries per user
   - Test duration
   - System specs

2. **Performance Metrics**
   - Success rate
   - Average latency
   - P95/P99 latency
   - Error rate

3. **Resource Usage**
   - Peak CPU usage
   - Peak memory usage
   - Disk I/O

4. **Issues Found**
   - Errors encountered
   - Performance bottlenecks
   - System limitations

5. **Recommendations**
   - Optimizations needed
   - Infrastructure changes
   - Configuration adjustments

### Example Report Template

```markdown
# Load Test Report - Campus AI Assistant

**Date**: YYYY-MM-DD
**Tester**: [Name]
**Environment**: [Local/Staging/Production]

## Test Configuration
- Users: 70 concurrent
- Queries per user: 3
- Total queries: 210
- Duration: 5 minutes

## Results
- Success rate: 98%
- Average latency: 6.2s
- P95 latency: 12.5s
- P99 latency: 18.3s

## Resource Usage
- Peak CPU: 65%
- Peak Memory: 5.2GB
- No crashes or errors

## Assessment
✅ System meets performance targets
✅ Ready for user acceptance testing
⚠️ Consider optimization for P99 latency

## Recommendations
1. Proceed to UAT with 10 test users
2. Monitor performance during UAT
3. Plan Phase 2 optimizations based on real usage
```

---

## Success Criteria Summary

### Staging Validation Complete When:
- [x] Core system functional
- [x] Documentation complete
- [ ] Load test with 10 users passes
- [ ] Load test with 70 users passes (target)
- [ ] No critical bugs found
- [ ] Performance within acceptable range
- [ ] System stable for 1+ hour under load

### Ready for Production When:
- [ ] Staging validation complete
- [ ] User acceptance testing passed
- [ ] Support procedures ready
- [ ] Monitoring configured
- [ ] Backup procedures tested
- [ ] Rollback plan validated

---

## Quick Commands Reference

```bash
# Start application
streamlit run app.py

# Run load test (10 users)
python3 scripts/load_test.py --users 10 --queries 5

# Run load test (70 users - target)
python3 scripts/load_test.py --users 70 --queries 3

# Monitor resources
htop

# Check Ollama
curl http://localhost:11434/api/tags

# View logs
tail -f ~/.streamlit/logs/streamlit.log

# Rebuild indices
python3 indexer.py
```

---

## Contact and Support

For issues during staging:
- Check TROUBLESHOOTING.md
- Review logs for errors
- Run validation script
- Document issues for team review

---

**Status**: Ready for load testing
**Next Step**: Run `python3 scripts/load_test.py --users 10 --queries 5`
