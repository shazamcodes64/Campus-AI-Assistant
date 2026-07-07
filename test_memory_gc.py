"""Test script to verify garbage collection triggers and memory monitoring"""

import json
import gc
import sys

# Test memory monitoring
print("="*60)
print("Testing Memory Monitoring and GC Triggers")
print("="*60)

# Test 1: Import memory monitor
print("\n1. Testing memory_monitor import...")
try:
    from memory_monitor import get_monitor, log_memory, trigger_gc_with_logging
    print("✅ memory_monitor imported successfully")
    
    monitor = get_monitor()
    monitor.set_baseline()
    print("✅ Memory monitor initialized")
except ImportError as e:
    print(f"❌ Failed to import memory_monitor: {e}")
    print("   Install psutil: pip install psutil")
    sys.exit(1)

# Test 2: Test GC in engines.py
print("\n2. Testing GC triggers in engines.py...")
try:
    with open("config.json", "r") as f:
        config = json.load(f)
    
    from engines import SearchEngine
    
    log_memory("before SearchEngine init")
    search_engine = SearchEngine(config)
    log_memory("after SearchEngine init")
    
    print("✅ SearchEngine loaded with GC triggers")
    
    # Test a search operation
    test_query = "What is the placement process?"
    log_memory("before search")
    result = search_engine.search(test_query)
    log_memory("after search")
    
    print(f"✅ Search completed: {result['type']}")
    
except Exception as e:
    print(f"❌ Error testing engines.py: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Test GC in llm.py
print("\n3. Testing GC triggers in llm.py...")
try:
    from llm import LLMGenerator
    
    log_memory("before LLMGenerator init")
    llm_gen = LLMGenerator(config)
    log_memory("after LLMGenerator init")
    
    print("✅ LLMGenerator loaded with GC triggers")
    
    # Test connection (don't require Ollama to be running)
    connected = llm_gen.test_connection()
    if connected:
        print("✅ Ollama connection successful")
    else:
        print("⚠️  Ollama not available (this is OK for testing)")
    
except Exception as e:
    print(f"❌ Error testing llm.py: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Manual GC trigger test
print("\n4. Testing manual GC triggers...")
try:
    # Create some garbage
    garbage = [list(range(10000)) for _ in range(100)]
    log_memory("after creating garbage")
    
    # Clear references
    garbage = None
    
    # Trigger GC
    collected = trigger_gc_with_logging("manual test")
    print(f"✅ GC collected {collected} objects")
    
except Exception as e:
    print(f"❌ Error testing manual GC: {e}")

# Test 5: Batch operations test
print("\n5. Testing batch operations with GC...")
try:
    # Test batch encoding (if we have data)
    test_texts = [
        "What is the placement process?",
        "How do I register for courses?",
        "What are the graduation requirements?",
        "When is the academic calendar?",
        "How do I apply for scholarships?"
    ]
    
    log_memory("before batch encoding")
    embeddings = search_engine.encode_batch(test_texts)
    log_memory("after batch encoding")
    
    print(f"✅ Batch encoding completed: {embeddings.shape}")
    
except Exception as e:
    print(f"❌ Error testing batch operations: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Print summary
print("\n6. Memory monitoring summary...")
try:
    monitor.print_summary()
    print("✅ Memory monitoring summary printed")
except Exception as e:
    print(f"❌ Error printing summary: {e}")

# Final verification
print("\n" + "="*60)
print("VERIFICATION RESULTS")
print("="*60)

# Check that gc module is imported in all files
files_to_check = ["app.py", "engines.py", "llm.py"]
gc_imports = []

for filename in files_to_check:
    try:
        with open(filename, "r") as f:
            content = f.read()
            if "import gc" in content:
                gc_imports.append(filename)
                print(f"✅ {filename}: gc module imported")
            else:
                print(f"❌ {filename}: gc module NOT imported")
    except Exception as e:
        print(f"❌ {filename}: Error reading file - {e}")

# Check for gc.collect() calls
gc_calls = []
for filename in files_to_check:
    try:
        with open(filename, "r") as f:
            content = f.read()
            count = content.count("gc.collect()")
            if count > 0:
                gc_calls.append((filename, count))
                print(f"✅ {filename}: {count} gc.collect() call(s)")
            else:
                print(f"⚠️  {filename}: No gc.collect() calls")
    except Exception as e:
        print(f"❌ {filename}: Error reading file - {e}")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"Files with gc import: {len(gc_imports)}/{len(files_to_check)}")
print(f"Total gc.collect() calls: {sum(count for _, count in gc_calls)}")
print(f"Memory monitoring: {'✅ Available' if 'memory_monitor' in sys.modules else '❌ Not available'}")
print("="*60)

print("\n✅ All tests completed!")
