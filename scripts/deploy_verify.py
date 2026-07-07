#!/usr/bin/env python3
"""
Deployment Verification Script for Campus AI Assistant
Checks all prerequisites and system readiness for classroom deployment
"""

import sys
import json
import os
from pathlib import Path

def print_header(text):
    print("\n" + "="*70)
    print(text)
    print("="*70)

def print_step(step_num, text):
    print(f"\n{step_num}. {text}")

def check_file_exists(filepath, description):
    """Check if a file exists and print result"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        size_mb = size / (1024 * 1024)
        print(f"  ✓ {description}: {filepath} ({size_mb:.2f} MB)")
        return True
    else:
        print(f"  ✗ {description} not found: {filepath}")
        return False

def main():
    print_header("CLASSROOM DEPLOYMENT VERIFICATION TEST")
    
    all_checks_passed = True
    
    # 1. Check configuration
    print_step(1, "Checking configuration...")
    if not check_file_exists("config.json", "Configuration file"):
        all_checks_passed = False
    else:
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
            print(f"  ✓ Configuration loaded successfully")
            print(f"    - Ollama URL: {config.get('ollama_url', 'N/A')}")
            print(f"    - Model: {config.get('model_name', 'N/A')}")
            print(f"    - Embedding model: {config.get('embedding_model', 'N/A')}")
        except Exception as e:
            print(f"  ✗ Failed to load configuration: {e}")
            all_checks_passed = False
    
    # 2. Check core application files
    print_step(2, "Checking core application files...")
    required_files = [
        ("app.py", "Main Streamlit application"),
        ("engines.py", "Search engine module"),
        ("llm.py", "LLM generator module"),
        ("indexer.py", "Document indexer module"),
        ("requirements.txt", "Python dependencies")
    ]
    
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
    
    # 3. Check data directories
    print_step(3, "Checking data directories...")
    required_dirs = [
        "data/documents",
        "data/indices",
        "data/logs"
    ]
    
    for dirpath in required_dirs:
        if os.path.exists(dirpath):
            print(f"  ✓ Directory exists: {dirpath}")
        else:
            print(f"  ✗ Directory missing: {dirpath}")
            all_checks_passed = False
    
    # 4. Check search indices
    print_step(4, "Checking search indices...")
    index_files = [
        ("data/indices/faiss.index", "FAISS vector index"),
        ("data/indices/bm25_index.pkl", "BM25 keyword index"),
        ("data/indices/metadata.json", "Chunk metadata")
    ]
    
    for filepath, description in index_files:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
            print(f"    → Run 'python indexer.py' to build indices")
    
    # 5. Check FAQ database
    print_step(5, "Checking FAQ database...")
    if check_file_exists("data/faq.json", "FAQ database"):
        try:
            with open("data/faq.json", "r") as f:
                faq_data = json.load(f)
            num_faqs = len(faq_data.get("faqs", []))
            print(f"    - FAQ entries: {num_faqs}")
        except Exception as e:
            print(f"  ⚠ FAQ file exists but couldn't be parsed: {e}")
    else:
        print(f"  ⚠ FAQ database not found (optional)")
    
    # 6. Check documents
    print_step(6, "Checking documents...")
    doc_dir = Path("data/documents")
    if doc_dir.exists():
        pdf_files = list(doc_dir.glob("*.pdf"))
        print(f"  ✓ Documents directory exists")
        print(f"    - PDF files: {len(pdf_files)}")
        if len(pdf_files) > 0:
            total_size = sum(f.stat().st_size for f in pdf_files)
            print(f"    - Total size: {total_size / (1024*1024):.2f} MB")
    else:
        print(f"  ✗ Documents directory not found")
        all_checks_passed = False
    
    # 7. Test module imports
    print_step(7, "Testing module imports...")
    try:
        sys.path.insert(0, '.')
        import engines
        import llm
        import indexer
        print(f"  ✓ All core modules imported successfully")
    except ImportError as e:
        print(f"  ✗ Module import failed: {e}")
        all_checks_passed = False
    
    # 8. Test Ollama connectivity
    print_step(8, "Testing Ollama connectivity...")
    try:
        import requests
        with open("config.json", "r") as f:
            config = json.load(f)
        
        ollama_url = config.get("ollama_url", "http://localhost:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"  ✓ Ollama service is running")
            print(f"    - Available models: {len(models)}")
            for model in models:
                print(f"      • {model.get('name', 'unknown')}")
        else:
            print(f"  ✗ Ollama returned status {response.status_code}")
            all_checks_passed = False
    except requests.exceptions.ConnectionError:
        print(f"  ✗ Cannot connect to Ollama service")
        print(f"    → Start Ollama: 'ollama serve'")
        all_checks_passed = False
    except Exception as e:
        print(f"  ✗ Ollama connectivity test failed: {e}")
        all_checks_passed = False
    
    # 9. Check deployment documentation
    print_step(9, "Checking deployment documentation...")
    doc_files = [
        ("README.md", "User guide"),
        ("DEPLOYMENT.md", "Deployment guide")
    ]
    
    for filepath, description in doc_files:
        check_file_exists(filepath, description)
    
    # Final summary
    print_header("DEPLOYMENT VERIFICATION SUMMARY")
    
    if all_checks_passed:
        print("\n✅ ALL CHECKS PASSED - System is ready for deployment!")
        print("\nNext steps:")
        print("  1. Start Ollama (if not running): ollama serve")
        print("  2. Start application: streamlit run app.py")
        print("  3. Access at: http://localhost:8501")
        print("  4. Test with sample queries")
        print("  5. Perform user acceptance testing")
        print("\nFor production deployment:")
        print("  - Review DEPLOYMENT.md for detailed instructions")
        print("  - Set up systemd services for Ollama and Streamlit")
        print("  - Configure firewall and security settings")
        print("  - Set up monitoring and log rotation")
        return 0
    else:
        print("\n❌ SOME CHECKS FAILED - Please fix issues before deployment")
        print("\nCommon fixes:")
        print("  - Run 'python indexer.py' to build search indices")
        print("  - Run 'ollama serve' to start LLM service")
        print("  - Check that all dependencies are installed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
