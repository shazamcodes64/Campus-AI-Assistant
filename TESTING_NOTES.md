# Manual Testing Notes

## Day 2: Real-World Validation

### Step 1: Reality Data ✅
- [ ] Add 15-20 messy PDFs to `data/documents/`:
  - Placement PDFs
  - Policy docs  
  - Syllabus
  - Random circulars
  - Messy scanned text
- [ ] Run: `python indexer.py`

### Step 2: Manual Hammer Testing (1-2 hours)
Test these garbage queries fast. Write down failures:

**Placement queries:**
- how placement
- placement??
- plcement fees refund
- fees refund after drop yr
- cgpa 4 msft
- minimum cgpa google

**Academic queries:**
- who is hod
- who handles internship
- when is lab exam
- midsem marks
- portal not working
- wtf is add drop

**Random garbage:**
- help
- what?
- fees
- marks
- rules
- dates

### Step 3: Fix ONLY These Knobs
When something breaks, adjust ONLY:
- `chunk_size` in config.json
- `faq_threshold` in config.json  
- `doc_threshold` in config.json
- `high_similarity_threshold` in config.json

NO new logic. NO refactor. NO architecture changes.

### Step 4: Repeat
Until 90% of queries feel "good enough" (not perfect).

---

## Failure Log (Manual)

### Query: [write query here]
- **Result**: [wrong/slow/crash/hallucination]
- **Issue**: [what went wrong]
- **Fix tried**: [what you changed]
- **Outcome**: [better/worse/same]

---

### Query: 
- **Result**: 
- **Issue**: 
- **Fix tried**: 
- **Outcome**: 

---

### Query: 
- **Result**: 
- **Issue**: 
- **Fix tried**: 
- **Outcome**: 

---

## Current Config Values
- chunk_size: 512
- faq_threshold: 0.8
- doc_threshold: 0.5
- high_similarity_threshold: 0.85

## Success Criteria
✅ 90% of garbage queries feel "good enough"
✅ Response time <10s for most queries
✅ No crashes on weird input
✅ Students would actually use this