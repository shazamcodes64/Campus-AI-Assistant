# Campus AI Assistant - Deployment Checklist

## Pre-Deployment Checklist

### System Preparation
- [ ] Server meets minimum requirements (4 cores, 8GB RAM, 50GB storage)
- [ ] Ubuntu 20.04+ or compatible OS installed
- [ ] Python 3.9+ installed and verified
- [ ] Network connectivity confirmed
- [ ] SSH access configured (for remote deployment)
- [ ] Firewall rules planned

### Software Installation
- [ ] Python 3.9+ installed (`python3 --version`)
- [ ] pip package manager installed
- [ ] Git installed (if using version control)
- [ ] Ollama installed (`ollama --version`)
- [ ] LLM model downloaded (`ollama list` shows llama3:latest)
- [ ] Ollama service running (`curl http://localhost:11434/api/tags`)

### Data Preparation
- [ ] Academic PDF documents collected and validated
- [ ] PDFs are text-based (not scanned images)
- [ ] FAQ data prepared (optional but recommended)
- [ ] FAQ JSON validated for syntax errors
- [ ] Document naming conventions followed (no special characters)

### Application Setup
- [ ] Application files copied to server
- [ ] Virtual environment created (`python3 -m venv venv`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] config.json reviewed and customized
- [ ] Directory structure created (data/documents, data/indices, data/logs)

---

## Deployment Steps

### Step 1: Environment Setup
- [ ] Virtual environment activated
- [ ] All dependencies installed without errors
- [ ] Python packages verified (`pip list`)
- [ ] No version conflicts reported

### Step 2: Data Loading
- [ ] PDFs copied to `data/documents/`
- [ ] At least 5 PDF files present for testing
- [ ] FAQ file created at `data/faq.json` (if using FAQs)
- [ ] File permissions correct (readable by application user)

### Step 3: Index Building
- [ ] Indexer executed (`python indexer.py`)
- [ ] No errors during PDF processing
- [ ] FAISS index created (`data/indices/faiss.index` exists)
- [ ] BM25 index created (`data/indices/bm25_index.pkl` exists)
- [ ] Metadata created (`data/indices/metadata.json` exists)
- [ ] Metadata contains expected number of chunks

### Step 4: System Testing
- [ ] Test script executed (`python scripts/test_system.py`)
- [ ] Search engine loads without errors
- [ ] LLM generator loads without errors
- [ ] Test queries return results
- [ ] No critical errors in output

### Step 5: Application Start
- [ ] Streamlit starts without errors
- [ ] Application accessible at http://localhost:8501
- [ ] System status shows all green checkmarks
- [ ] No error messages in console

### Step 6: Functional Testing
- [ ] Test query: "What is the syllabus?" returns relevant answer
- [ ] FAQ query returns direct FAQ answer (if FAQs configured)
- [ ] Out-of-scope query properly rejected
- [ ] Sources displayed correctly
- [ ] Confidence scores reasonable (>0.5 for valid queries)
- [ ] Response time acceptable (<10 seconds)

---

## Production Configuration

### Service Setup
- [ ] Ollama systemd service created
- [ ] Ollama service enabled (`systemctl enable ollama`)
- [ ] Ollama service starts on boot
- [ ] Campus AI systemd service created
- [ ] Campus AI service enabled (`systemctl enable campus-ai`)
- [ ] Campus AI service starts on boot
- [ ] Service dependencies configured correctly

### Network Configuration
- [ ] Firewall rules configured
- [ ] Port 8501 accessible (or configured port)
- [ ] Port 11434 accessible for Ollama
- [ ] Nginx reverse proxy configured (if using)
- [ ] SSL/TLS certificates installed (if using HTTPS)
- [ ] Domain name configured (if applicable)

### Security Hardening
- [ ] Dedicated user account created for services
- [ ] File permissions set correctly
- [ ] Unnecessary ports closed
- [ ] SSH key authentication configured
- [ ] Password authentication disabled (if using keys)
- [ ] Fail2ban or similar configured (optional)

### Monitoring Setup
- [ ] Log rotation configured (`/etc/logrotate.d/campus-ai`)
- [ ] Disk space monitoring enabled
- [ ] Memory usage monitoring enabled
- [ ] Service health checks configured
- [ ] Alert thresholds defined

### Backup Configuration
- [ ] Backup script created
- [ ] Backup schedule configured (daily recommended)
- [ ] Backup location configured
- [ ] Backup retention policy set (7-30 days)
- [ ] Restore procedure tested

---

## Post-Deployment Verification

### Immediate Checks (First Hour)
- [ ] Application accessible from target network
- [ ] All services running (`systemctl status campus-ai ollama`)
- [ ] No errors in logs (`journalctl -u campus-ai -n 50`)
- [ ] Test queries work from different devices
- [ ] Response times acceptable
- [ ] Memory usage stable

### Short-term Checks (First Day)
- [ ] Services remain stable for 24 hours
- [ ] No memory leaks observed
- [ ] No unexpected restarts
- [ ] Log files growing at expected rate
- [ ] Disk space sufficient
- [ ] 5-10 test users can access simultaneously

### Medium-term Checks (First Week)
- [ ] System handles peak load (70 concurrent users)
- [ ] Response times remain acceptable under load
- [ ] No performance degradation over time
- [ ] Logs reviewed for patterns
- [ ] User feedback collected
- [ ] Common queries identified

---

## User Acceptance Testing

### Test User Group
- [ ] 5-10 test users identified
- [ ] Test users trained on system usage
- [ ] User guide distributed
- [ ] Feedback mechanism established

### Test Scenarios
- [ ] Users can access the system
- [ ] Users can ask course-related questions
- [ ] Users receive relevant answers
- [ ] Users understand confidence scores
- [ ] Users can view sources
- [ ] Users report issues easily

### Success Criteria
- [ ] 80%+ of test queries return relevant results
- [ ] 90%+ user satisfaction with interface
- [ ] <10 second response time for 95% of queries
- [ ] No critical bugs reported
- [ ] System stable during test period

---

## Documentation Checklist

### User Documentation
- [ ] User guide created and accessible
- [ ] Example queries documented
- [ ] FAQ about the system created
- [ ] Contact information for support provided

### Technical Documentation
- [ ] Deployment guide complete
- [ ] Troubleshooting guide available
- [ ] System architecture documented
- [ ] Configuration options explained
- [ ] Backup/restore procedures documented

### Operational Documentation
- [ ] Service management procedures documented
- [ ] Monitoring procedures documented
- [ ] Update procedures documented
- [ ] Emergency procedures documented
- [ ] Escalation procedures defined

---

## Training Checklist

### Administrator Training
- [ ] System architecture explained
- [ ] Service management trained
- [ ] Monitoring tools demonstrated
- [ ] Troubleshooting procedures reviewed
- [ ] Backup/restore procedures practiced
- [ ] Update procedures demonstrated

### User Training
- [ ] System purpose explained
- [ ] How to ask questions demonstrated
- [ ] How to interpret results explained
- [ ] Limitations communicated
- [ ] Support channels explained

---

## Rollback Plan

### Rollback Triggers
- [ ] Critical bugs affecting >50% of users
- [ ] System instability (frequent crashes)
- [ ] Security vulnerabilities discovered
- [ ] Performance degradation >50%
- [ ] Data corruption detected

### Rollback Procedure
- [ ] Backup of current state taken
- [ ] Services stopped
- [ ] Previous version restored from backup
- [ ] Services restarted
- [ ] Verification tests passed
- [ ] Users notified of rollback

---

## Go-Live Checklist

### Final Pre-Launch
- [ ] All deployment steps completed
- [ ] All tests passed
- [ ] Documentation complete
- [ ] Training completed
- [ ] Backup verified
- [ ] Rollback plan ready
- [ ] Support team briefed
- [ ] Users notified of launch

### Launch Day
- [ ] Services started
- [ ] Initial health check passed
- [ ] Announcement sent to users
- [ ] Support team on standby
- [ ] Monitoring active
- [ ] First queries successful

### Post-Launch (First 24 Hours)
- [ ] Continuous monitoring active
- [ ] No critical issues reported
- [ ] User feedback being collected
- [ ] Performance metrics within targets
- [ ] Support requests handled
- [ ] Daily backup completed

---

## Success Metrics

### Technical Metrics
- [ ] Uptime >99% in first week
- [ ] Response time <10s for 95% of queries
- [ ] Memory usage <8GB peak
- [ ] CPU usage <70% average
- [ ] No critical errors in logs

### User Metrics
- [ ] 70+ concurrent users supported
- [ ] 80%+ query success rate
- [ ] 90%+ user satisfaction
- [ ] <5% support ticket rate
- [ ] Positive user feedback

### Business Metrics
- [ ] Deployment completed on schedule
- [ ] Within budget
- [ ] No major incidents
- [ ] User adoption >50% in first week
- [ ] Reduced support burden on staff

---

## Sign-Off

### Technical Sign-Off
- [ ] System Administrator: _________________ Date: _______
- [ ] IT Manager: _________________ Date: _______

### Business Sign-Off
- [ ] Academic Coordinator: _________________ Date: _______
- [ ] Department Head: _________________ Date: _______

### User Acceptance
- [ ] Test User Representative: _________________ Date: _______

---

## Post-Deployment Tasks

### Week 1
- [ ] Daily monitoring and log review
- [ ] User feedback collection
- [ ] Performance metrics analysis
- [ ] Issue tracking and resolution
- [ ] Documentation updates based on feedback

### Week 2-4
- [ ] Weekly performance review
- [ ] User satisfaction survey
- [ ] Identify common query patterns
- [ ] Plan FAQ updates
- [ ] Evaluate Phase 2 priorities

### Month 2+
- [ ] Monthly system review
- [ ] Capacity planning
- [ ] Feature prioritization for Phase 2
- [ ] Cost analysis
- [ ] ROI assessment

---

## Emergency Contacts

### Technical Support
- System Administrator: _________________ Phone: _______
- IT Support: _________________ Phone: _______
- Vendor Support: _________________ Phone: _______

### Business Contacts
- Project Manager: _________________ Phone: _______
- Academic Coordinator: _________________ Phone: _______
- Department Head: _________________ Phone: _______

---

## Notes and Comments

Use this space to document any deployment-specific notes, issues encountered, or lessons learned:

```
Date: _______
Notes:




```

---

## Deployment Status

**Status**: [ ] Not Started [ ] In Progress [ ] Completed [ ] Rolled Back

**Deployment Date**: _______

**Go-Live Date**: _______

**Deployed By**: _______

**Verified By**: _______

---

This checklist should be completed in order. Do not skip steps unless explicitly approved by project stakeholders.
