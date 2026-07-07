# Campus AI Assistant - Post-Deployment Support Plan

**Version**: 1.0  
**Date**: February 3, 2025  
**Target Environment**: Classroom deployment (~70 concurrent students)

---

## 1. Support Overview

### Support Objectives

- Ensure system stability and availability during classroom sessions
- Quickly resolve technical issues that impact user experience
- Collect and analyze usage data for continuous improvement
- Maintain system performance within target metrics
- Build knowledge base from real-world usage patterns

### Support Scope

**In Scope**:
- System availability and uptime
- Performance issues (slow responses, timeouts)
- Search quality and relevance
- LLM service connectivity
- Error handling and recovery
- User-reported bugs and issues
- FAQ updates and content management

**Out of Scope**:
- Content creation (PDF documents)
- Academic policy questions
- Individual student technical support (device issues)
- Network infrastructure issues
- Hardware procurement or upgrades

---

## 2. Support Team Structure

### Roles and Responsibilities

#### System Administrator
**Primary Contact**: [To be assigned]  
**Responsibilities**:
- Monitor system health and performance
- Restart services when needed
- Apply updates and patches
- Manage backups and recovery
- Handle infrastructure issues

**Availability**: During classroom hours + on-call for critical issues

#### Content Manager
**Primary Contact**: [To be assigned]  
**Responsibilities**:
- Update FAQ database based on common queries
- Review and approve FAQ promotions
- Coordinate document updates with faculty
- Maintain content quality and accuracy

**Availability**: Weekly review sessions

#### Technical Support (Tier 1)
**Primary Contact**: [To be assigned]  
**Responsibilities**:
- Respond to user-reported issues
- Perform basic troubleshooting
- Escalate complex issues
- Document common problems and solutions
- Update troubleshooting guides

**Availability**: During classroom hours

---

## 3. Monitoring and Alerting

### System Health Monitoring

#### Automated Checks (Every 5 minutes)

```bash
#!/bin/bash
# health_check.sh - Run via cron

# Check Ollama service
if ! systemctl is-active --quiet ollama; then
    echo "ALERT: Ollama service is down" | mail -s "Campus AI Alert" admin@example.com
    systemctl restart ollama
fi

# Check Campus AI service
if ! systemctl is-active --quiet campus-ai; then
    echo "ALERT: Campus AI service is down" | mail -s "Campus AI Alert" admin@example.com
    systemctl restart campus-ai
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "ALERT: Disk usage is ${DISK_USAGE}%" | mail -s "Campus AI Alert" admin@example.com
fi

# Check memory usage
MEM_USAGE=$(free | awk 'NR==2 {printf "%.0f", $3/$2*100}')
if [ $MEM_USAGE -gt 90 ]; then
    echo "ALERT: Memory usage is ${MEM_USAGE}%" | mail -s "Campus AI Alert" admin@example.com
fi
```

#### Performance Metrics to Track

**Response Time**:
- Target: <10 seconds (95th percentile)
- Warning: >10 seconds
- Critical: >20 seconds

**Memory Usage**:
- Target: <8GB
- Warning: >12GB
- Critical: >15GB

**Query Success Rate**:
- Target: >95%
- Warning: <90%
- Critical: <80%

**Service Uptime**:
- Target: 99.5% during classroom hours
- Warning: Any downtime >5 minutes
- Critical: Downtime >15 minutes

### Log Monitoring

**Daily Log Review**:
```bash
# Check for errors in last 24 hours
grep -i "error\|exception\|failed" data/logs/interactions.jsonl | tail -50

# Check query patterns
jq -r '.query' data/logs/interactions.jsonl | sort | uniq -c | sort -rn | head -20

# Check average response times
jq -r '.processing_time_seconds' data/logs/interactions.jsonl | awk '{sum+=$1; count++} END {print sum/count}'
```

---

## 4. Incident Response Procedures

### Severity Levels

#### P0 - Critical (Response: Immediate)
**Definition**: System completely unavailable or unusable
**Examples**:
- Application won't start
- All queries failing
- Ollama service crashed
- Database corruption

**Response**:
1. Acknowledge incident immediately
2. Notify all stakeholders
3. Begin troubleshooting
4. Implement emergency workaround if possible
5. Restore from backup if needed
6. Document incident and resolution

#### P1 - High (Response: <30 minutes)
**Definition**: Major functionality impaired
**Examples**:
- Slow response times (>20s)
- High error rate (>20%)
- Memory exhaustion
- Search indices corrupted

**Response**:
1. Acknowledge within 15 minutes
2. Assess impact and scope
3. Begin troubleshooting
4. Implement fix or workaround
5. Monitor for recurrence
6. Document issue

#### P2 - Medium (Response: <2 hours)
**Definition**: Partial functionality impaired
**Examples**:
- FAQ search not working
- Some queries returning poor results
- Slow but functional performance
- Non-critical errors in logs

**Response**:
1. Acknowledge within 30 minutes
2. Schedule fix during maintenance window
3. Document workaround for users
4. Implement permanent fix
5. Update documentation

#### P3 - Low (Response: <24 hours)
**Definition**: Minor issues or enhancement requests
**Examples**:
- FAQ content updates needed
- UI improvements
- Documentation updates
- Feature requests

**Response**:
1. Log issue in tracking system
2. Prioritize for next maintenance cycle
3. Implement during scheduled maintenance
4. Update documentation

### Common Issues and Solutions

#### Issue: Application Not Responding

**Symptoms**: Users cannot access http://localhost:8501

**Diagnosis**:
```bash
# Check service status
systemctl status campus-ai

# Check logs
journalctl -u campus-ai -n 50

# Check port
netstat -tulpn | grep 8501
```

**Solution**:
```bash
# Restart service
systemctl restart campus-ai

# If that fails, check dependencies
systemctl restart ollama
systemctl restart campus-ai

# Verify
curl http://localhost:8501
```

#### Issue: Slow Response Times

**Symptoms**: Queries taking >15 seconds

**Diagnosis**:
```bash
# Check memory
free -h

# Check CPU
htop

# Check Ollama
curl http://localhost:11434/api/tags

# Check logs for timeouts
grep "timeout" data/logs/interactions.jsonl
```

**Solution**:
```bash
# Clear memory
systemctl restart campus-ai

# If persistent, check model
ollama list
ollama pull llama3:latest

# Adjust config if needed
# Reduce chunk_size in config.json
```

#### Issue: No Search Results

**Symptoms**: All queries return "no relevant information"

**Diagnosis**:
```bash
# Check indices exist
ls -lh data/indices/

# Check metadata
head data/indices/metadata.json

# Check logs
tail -50 data/logs/interactions.jsonl
```

**Solution**:
```bash
# Rebuild indices
cd /opt/campus-ai-assistant
source venv/bin/activate
python indexer.py

# Restart application
systemctl restart campus-ai
```

#### Issue: Ollama Connection Failed

**Symptoms**: "LLM service not available" warnings

**Diagnosis**:
```bash
# Check Ollama service
systemctl status ollama

# Test connection
curl http://localhost:11434/api/tags

# Check model
ollama list
```

**Solution**:
```bash
# Restart Ollama
systemctl restart ollama

# Pull model if missing
ollama pull llama3:latest

# Restart application
systemctl restart campus-ai
```

---

## 5. Maintenance Schedule

### Daily Maintenance (5 minutes)

**Time**: Before first class session

**Tasks**:
- [ ] Check service status
- [ ] Review error logs from previous day
- [ ] Verify disk space >20% free
- [ ] Test with sample query
- [ ] Check Ollama model availability

**Script**:
```bash
#!/bin/bash
# daily_check.sh

echo "=== Daily Maintenance Check ==="
echo "Date: $(date)"

# Service status
echo -e "\n1. Service Status:"
systemctl is-active campus-ai && echo "  ✓ Campus AI: Running" || echo "  ✗ Campus AI: Down"
systemctl is-active ollama && echo "  ✓ Ollama: Running" || echo "  ✗ Ollama: Down"

# Disk space
echo -e "\n2. Disk Space:"
df -h / | awk 'NR==2 {print "  Used: "$5" of "$2}'

# Memory
echo -e "\n3. Memory:"
free -h | awk 'NR==2 {print "  Used: "$3" of "$2}'

# Recent errors
echo -e "\n4. Recent Errors (last 24h):"
ERROR_COUNT=$(grep -c "error\|exception" data/logs/interactions.jsonl 2>/dev/null || echo "0")
echo "  Error count: $ERROR_COUNT"

# Test query
echo -e "\n5. System Test:"
curl -s http://localhost:8501 > /dev/null && echo "  ✓ Application accessible" || echo "  ✗ Application not accessible"

echo -e "\n=== Check Complete ==="
```

### Weekly Maintenance (30 minutes)

**Time**: Weekend or low-usage period

**Tasks**:
- [ ] Review query logs and patterns
- [ ] Update FAQ based on common questions
- [ ] Check and rotate logs if needed
- [ ] Review performance metrics
- [ ] Update documentation if needed
- [ ] Test backup and restore procedure
- [ ] Check for system updates

**Checklist**:
```markdown
## Weekly Maintenance - [Date]

### System Health
- [ ] Services running normally
- [ ] No critical errors in logs
- [ ] Performance within targets
- [ ] Disk space adequate

### Content Updates
- [ ] Reviewed common queries
- [ ] Updated FAQ (if needed)
- [ ] Verified document accuracy

### Performance Review
- [ ] Average response time: ___s
- [ ] Query success rate: ___%
- [ ] Peak concurrent users: ___
- [ ] Memory usage: ___GB

### Actions Taken
- [ ] [List any updates or fixes]

### Issues Identified
- [ ] [List any concerns for follow-up]
```

### Monthly Maintenance (2 hours)

**Time**: Scheduled maintenance window

**Tasks**:
- [ ] Apply system updates
- [ ] Update Python dependencies
- [ ] Review and optimize indices
- [ ] Analyze usage patterns
- [ ] Update documentation
- [ ] Review and update support procedures
- [ ] Conduct performance testing
- [ ] Review backup strategy

---

## 6. User Communication

### Status Page

Create a simple status page at `/status` endpoint or separate page:

```markdown
# Campus AI Assistant - System Status

**Last Updated**: [Auto-updated timestamp]

## Current Status: 🟢 Operational

### Services
- Application: ✅ Running
- Search Engine: ✅ Running
- LLM Service: ✅ Running

### Performance (Last Hour)
- Average Response Time: 6.2s
- Success Rate: 97%
- Queries Processed: 142

### Scheduled Maintenance
- Next maintenance: Sunday, Feb 10, 2:00 AM - 4:00 AM

### Known Issues
- None

### Recent Updates
- Feb 3: System deployed and verified
```

### Incident Communication Template

**For P0/P1 Incidents**:
```
Subject: [Campus AI] Service Issue - [Brief Description]

We are currently experiencing [description of issue].

Impact: [What users will experience]
Status: [Investigating/Identified/Fixing/Resolved]
ETA: [Expected resolution time]

We will provide updates every [15/30] minutes.

Workaround: [If available]

Thank you for your patience.
```

**For Scheduled Maintenance**:
```
Subject: [Campus AI] Scheduled Maintenance - [Date]

The Campus AI Assistant will undergo scheduled maintenance:

Date: [Date]
Time: [Start] - [End]
Duration: [Expected duration]

During this time, the system will be unavailable.

Work to be performed:
- [List maintenance tasks]

Expected improvements:
- [List benefits]

Thank you for your understanding.
```

---

## 7. Knowledge Base

### FAQ for Support Team

**Q: How do I restart the services?**
```bash
sudo systemctl restart ollama
sudo systemctl restart campus-ai
```

**Q: How do I check if the system is working?**
```bash
python scripts/deploy_verify.py
```

**Q: How do I rebuild the search indices?**
```bash
cd /opt/campus-ai-assistant
source venv/bin/activate
python indexer.py
```

**Q: How do I update the FAQ?**
```bash
# Edit the file
nano data/faq.json

# No restart needed - hot reload enabled
```

**Q: How do I check system logs?**
```bash
# Application logs
tail -f data/logs/interactions.jsonl

# System logs
journalctl -u campus-ai -f
```

**Q: How do I add new documents?**
```bash
# Copy PDFs
cp /path/to/new/*.pdf data/documents/

# Rebuild indices
python indexer.py

# Restart application
systemctl restart campus-ai
```

### Common User Questions

**Q: Why is the system slow?**
- Check if many users are querying simultaneously
- Verify Ollama service is running
- Check system resources

**Q: Why am I getting "no relevant information"?**
- Query may be out of scope
- Try rephrasing with keywords from documents
- Check if documents are indexed

**Q: How do I report an issue?**
- Email: [support email]
- Include: query text, error message, timestamp

---

## 8. Continuous Improvement

### Data Collection

**Metrics to Track**:
- Query volume by hour/day
- Response times (p50, p95, p99)
- Success/failure rates
- Common query patterns
- FAQ hit rate vs document search rate
- User feedback and satisfaction

**Analysis Script**:
```python
# scripts/analyze_usage.py
import json
from collections import Counter
from datetime import datetime

def analyze_logs(log_file):
    queries = []
    response_times = []
    routes = []
    
    with open(log_file, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                queries.append(entry.get('query', ''))
                response_times.append(entry.get('processing_time_seconds', 0))
                routes.append(entry.get('route', 'unknown'))
            except:
                continue
    
    print(f"Total queries: {len(queries)}")
    print(f"Average response time: {sum(response_times)/len(response_times):.2f}s")
    print(f"\nRoute distribution:")
    for route, count in Counter(routes).most_common():
        print(f"  {route}: {count}")
    
    print(f"\nTop 10 queries:")
    for query, count in Counter(queries).most_common(10):
        print(f"  {count}x: {query[:50]}")

if __name__ == "__main__":
    analyze_logs("data/logs/interactions.jsonl")
```

### Feedback Collection

**Weekly Feedback Form**:
```markdown
# Campus AI Assistant - User Feedback

1. How often did you use the system this week?
   - [ ] Daily
   - [ ] 2-3 times
   - [ ] Once
   - [ ] Not at all

2. How would you rate the answer quality?
   - [ ] Excellent
   - [ ] Good
   - [ ] Fair
   - [ ] Poor

3. How would you rate the response speed?
   - [ ] Fast (<5s)
   - [ ] Acceptable (5-10s)
   - [ ] Slow (>10s)

4. Did you find the sources helpful?
   - [ ] Yes, very helpful
   - [ ] Somewhat helpful
   - [ ] Not helpful

5. What improvements would you suggest?
   [Free text]

6. What questions did the system handle well?
   [Free text]

7. What questions did the system struggle with?
   [Free text]
```

### Improvement Cycle

**Monthly Review Process**:
1. Analyze usage data and metrics
2. Review user feedback
3. Identify top 3 pain points
4. Prioritize improvements
5. Implement changes
6. Document and communicate updates
7. Measure impact

---

## 9. Escalation Procedures

### When to Escalate

**Escalate to System Administrator if**:
- Service restart doesn't resolve issue
- System resources exhausted
- Data corruption suspected
- Security incident detected

**Escalate to Content Manager if**:
- Multiple queries on same topic failing
- Document accuracy concerns
- FAQ updates needed urgently

**Escalate to Technical Lead if**:
- Code changes required
- Architecture changes needed
- Performance optimization required
- New features requested

### Escalation Contact List

```markdown
| Role | Name | Email | Phone | Availability |
|------|------|-------|-------|--------------|
| System Admin | [TBD] | [email] | [phone] | 24/7 on-call |
| Content Manager | [TBD] | [email] | [phone] | Business hours |
| Technical Lead | [TBD] | [email] | [phone] | Business hours |
| Backup Contact | [TBD] | [email] | [phone] | Emergency only |
```

---

## 10. Success Metrics

### Key Performance Indicators (KPIs)

**System Availability**:
- Target: 99.5% uptime during classroom hours
- Measurement: Service status checks

**Response Time**:
- Target: <10s for 95% of queries
- Measurement: Log analysis

**User Satisfaction**:
- Target: >80% positive feedback
- Measurement: Weekly surveys

**Query Success Rate**:
- Target: >90% queries return relevant results
- Measurement: Log analysis + user feedback

**Issue Resolution Time**:
- P0: <1 hour
- P1: <4 hours
- P2: <24 hours
- P3: <1 week

### Monthly Report Template

```markdown
# Campus AI Assistant - Monthly Report

**Period**: [Month Year]

## Usage Statistics
- Total queries: [number]
- Unique users: [number]
- Average queries per user: [number]
- Peak concurrent users: [number]

## Performance Metrics
- Average response time: [X]s
- 95th percentile response time: [X]s
- Query success rate: [X]%
- System uptime: [X]%

## Incidents
- P0 incidents: [number] - [brief description]
- P1 incidents: [number] - [brief description]
- P2 incidents: [number]
- P3 incidents: [number]

## User Feedback
- Survey responses: [number]
- Average satisfaction: [X]/5
- Top positive feedback: [summary]
- Top improvement requests: [summary]

## Content Updates
- FAQ entries added: [number]
- Documents updated: [number]
- FAQ promotions: [number]

## Improvements Implemented
- [List of improvements]

## Issues and Concerns
- [List of ongoing issues]

## Next Month Priorities
- [List of planned improvements]
```

---

## 11. Handoff and Training

### New Support Team Member Onboarding

**Day 1: System Overview**
- Review architecture and components
- Understand data flow
- Learn about deployment environment
- Review documentation

**Day 2: Hands-On Training**
- Access system and run health checks
- Practice common troubleshooting procedures
- Review logs and monitoring tools
- Test backup and restore

**Day 3: Shadowing**
- Shadow experienced team member
- Observe incident response
- Practice communication procedures
- Review escalation process

**Day 4: Supervised Practice**
- Handle issues with supervision
- Update documentation
- Perform maintenance tasks
- Collect and analyze metrics

**Day 5: Independent Work**
- Handle issues independently
- Conduct weekly maintenance
- Provide user support
- Document learnings

### Knowledge Transfer Checklist

- [ ] System architecture explained
- [ ] Access credentials provided
- [ ] Documentation reviewed
- [ ] Monitoring tools demonstrated
- [ ] Incident response practiced
- [ ] Escalation procedures understood
- [ ] Communication templates reviewed
- [ ] Maintenance tasks practiced
- [ ] Emergency contacts shared
- [ ] Questions answered

---

## 12. Appendix

### Useful Commands Reference

```bash
# Service Management
systemctl status campus-ai
systemctl restart campus-ai
systemctl stop campus-ai
systemctl start campus-ai
journalctl -u campus-ai -f

# System Monitoring
htop
free -h
df -h
netstat -tulpn

# Application Commands
cd /opt/campus-ai-assistant
source venv/bin/activate
python scripts/deploy_verify.py
python indexer.py
streamlit run app.py

# Log Analysis
tail -f data/logs/interactions.jsonl
grep "error" data/logs/interactions.jsonl
jq -r '.query' data/logs/interactions.jsonl | sort | uniq -c

# Backup
tar -czf backup-$(date +%Y%m%d).tar.gz data/
```

### Configuration Files

**Location**: `/opt/campus-ai-assistant/config.json`

**Key Settings**:
- `ollama_url`: LLM service endpoint
- `model_name`: LLM model to use
- `faq_threshold`: FAQ matching threshold (0.8)
- `doc_threshold`: Document search threshold (0.5)
- `chunk_size`: Text chunk size (512)

### Contact Information

**System Location**: `/opt/campus-ai-assistant`  
**Web Interface**: `http://localhost:8501`  
**Ollama Service**: `http://localhost:11434`  
**Documentation**: `/opt/campus-ai-assistant/DEPLOYMENT.md`

---

## Document Control

**Version**: 1.0  
**Last Updated**: February 3, 2025  
**Next Review**: March 3, 2025  
**Owner**: [To be assigned]  
**Approved By**: [To be assigned]

**Change Log**:
- v1.0 (Feb 3, 2025): Initial version created post-deployment
