import time
import csv
import json
import gc
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines import SearchEngine
from llm import LLMGenerator

# -----------------
# CONFIG
# -----------------

# Set to True for quick testing (only 10 queries)
QUICK_MODE = len(sys.argv) > 1 and sys.argv[1] == "--quick"
BATCH_SIZE = 5  # Process queries in small batches to avoid memory issues

QUERIES = [
    # Category A (exists)
    "What is the syllabus?",
    "How many credits is this course?",
    "Exam pattern details",
    "Internal marks breakup",
    "Attendance policy",
    "Lab evaluation method",
    "Project submission deadline",
    "Grading system",
    "Placement eligibility rules",
    "Revaluation procedure",

    # Category B (exists – messy)
    "syllabus??",
    "exam pattn",
    "how much attendence needed",
    "when proj submision last date",
    "marks breakup plz",
    "lab viva marks how many",
    "credits of subject",
    "fail criteria?",
    "placement rules explain",
    "grading cgpa calc",

    # Category C (maybe missing)
    "hostel mess timing",
    "canteen menu",
    "library sunday open",
    "wifi password",
    "bus route details",
    "sports day schedule",
    "faculty phone numbers",
    "holiday list",
    "fees payment link",
    "scholarship form",

    # Category D/E/F (junk/out of scope)
    "tell me a joke",
    "who is prime minister",
    "weather today",
    "solve 2+2",
    "write python code",
    "chat with me",
    "movie recommendations",
    "translate hello",
    "sing a song",
    "what is love",

    # Stress long queries
    "Explain in full detail the entire evaluation methodology including labs internals finals and project grading with percentages",
    "I missed two classes what happens will I be detained",
    "How does placement training work from first year to final year step by step",
    "Complete breakdown of marks distribution for theory and practical subjects",
    "Give all rules for attendance shortage and condonation",
    "What documents are required for project submission and viva",
    "Explain semester registration process",
    "What happens if I fail a subject",
    "Is there improvement exam policy",
    "Give complete syllabus for unit 1"
]

# Quick mode: only test first 10 queries
if QUICK_MODE:
    QUERIES = QUERIES[:10]
    print("🚀 QUICK MODE: Testing first 10 queries only\n")

# -----------------
# LOAD ENGINE ONCE
# -----------------

print(f"Running automated torture test on {len(QUERIES)} queries...")
print("Loading models once (this may take a moment)...\n")

with open("config.json") as f:
    config = json.load(f)

# Initialize ONCE and reuse
engine = SearchEngine(config)
llm = LLMGenerator(config)

print("✓ Models loaded\n")

# -----------------
# STREAMING EVAL
# -----------------

# Open CSV file for streaming writes
with open("eval_results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["query", "latency", "confidence", "missing", "has_sources"])
    
    latencies = []
    missing_count = 0
    source_hits = 0
    
    for idx, q in enumerate(QUERIES, 1):
        print(f"[{idx}/{len(QUERIES)}] {q[:60]}{'...' if len(q) > 60 else ''}")
        
        start = time.time()
        
        try:
            search_result = engine.search(q)
            response = llm.generate_response(q, search_result)
            
            latency = round(time.time() - start, 2)
            
            answer = response.get("answer", "")
            confidence = response.get("confidence", 0)
            
            # automatic heuristics
            missing = "only answer questions about course materials" in answer.lower()
            has_sources = bool(response.get("sources"))
            
            # Write immediately to CSV
            writer.writerow([q, latency, confidence, missing, has_sources])
            f.flush()  # Force write to disk
            
            # Track metrics
            latencies.append(latency)
            if missing:
                missing_count += 1
            if has_sources:
                source_hits += 1
            
            status = "✓" if has_sources and not missing else "⚠"
            print(f"  {status} {latency}s | conf={confidence:.2f} | sources={len(response.get('sources', []))}\n")
            
            # Clear response objects
            del search_result, response, answer
            
        except Exception as e:
            print(f"  ✗ ERROR: {str(e)[:80]}\n")
            writer.writerow([q, 0, 0, False, False])
            f.flush()

# -----------------
# METRICS
# -----------------

print("\n==== REPORT ====")
print("Total queries:", len(QUERIES))
print("Missing:", missing_count)
print("Answers with sources:", source_hits)
if latencies:
    print("Avg latency:", round(sum(latencies)/len(latencies), 2))
    print("Max latency:", max(latencies))
    print("p95 latency:", sorted(latencies)[int(len(latencies)*0.95)])
print("\nSaved detailed log → eval_results.csv")
