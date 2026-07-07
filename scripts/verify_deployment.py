#!/usr/bin/env python3
"""
Deployment Verification Script for Campus AI Assistant

This script verifies all prerequisites and system components are ready
for classroom deployment. It checks:
- System requirements
- Dependencies
- Ollama connectivity
- Search indices
- Configuration
- End-to-end functionality
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")


def print_check(name: str, passed: bool, details: str = ""):
    """Print a check result"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} {name}")
    if details:
        print(f"      {details}")


def check_python_version() -> Tuple[bool, str]:
    """Check Python version is 3.9+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)"


def check_dependencies() -> Tuple[bool, str]:
    """Check if all required packages are installed"""
    required = [
        'streamlit', 'sentence_transformers', 'faiss', 
        'rank_bm25', 'requests', 'PyPDF2', 'numpy'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_').lower())
        except ImportError:
            missing.append(package)
    
    if missing:
        return False, f"Missing packages: {', '.join(missing)}"
    return True, f"All {len(required)} required packages installed"


def check_ollama() -> Tuple[bool, str]:
    """Check if Ollama is running and accessible"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            return True, f"Ollama running with {len(models)} model(s): {', '.join(model_names)}"
        return False, f"Ollama returned status {response.status_code}"
    except Exception as e:
        return False, f"Cannot connect to Ollama: {str(e)}"


def check_config() -> Tuple[bool, str]:
    """Check if config.json exists and is valid"""
    config_path = Path('config.json')
    if not config_path.exists():
        return False, "config.json not found"
    
    try:
        with open(config_path) as f:
            config = json.load(f)
        
        required_keys = ['ollama_url', 'model_name', 'embedding_model']
        missing = [k for k in required_keys if k not in config]
        
        if missing:
            return False, f"Missing config keys: {', '.join(missing)}"
        
        return True, f"Valid configuration with {len(config)} settings"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"


def check_indices() -> Tuple[bool, str]:
    """Check if search indices exist"""
    indices_dir = Path('data/indices')
    required_files = ['faiss.index', 'bm25_index.pkl', 'metadata.json']
    
    if not indices_dir.exists():
        return False, "data/indices/ directory not found"
    
    missing = []
    sizes = []
    for filename in required_files:
        filepath = indices_dir / filename
        if not filepath.exists():
            missing.append(filename)
        else:
            size_mb = filepath.stat().st_size / (1024 * 1024)
            sizes.append(f"{filename} ({size_mb:.1f}MB)")
    
    if missing:
        return False, f"Missing files: {', '.join(missing)}"
    
    return True, f"All indices present: {', '.join(sizes)}"


def check_documents() -> Tuple[bool, str]:
    """Check if documents directory exists and has PDFs"""
    docs_dir = Path('data/documents')
    if not docs_dir.exists():
        return False, "data/documents/ directory not found"
    
    pdfs = list(docs_dir.glob('*.pdf'))
    if not pdfs:
        return False, "No PDF files found in data/documents/"
    
    total_size = sum(p.stat().st_size for p in pdfs) / (1024 * 1024)
    return True, f"{len(pdfs)} PDF file(s), {total_size:.1f}MB total"


def check_faq() -> Tuple[bool, str]:
    """Check if FAQ file exists (optional)"""
    faq_path = Path('data/faq.json')
    if not faq_path.exists():
        return True, "No FAQ file (optional)"
    
    try:
        with open(faq_path) as f:
            faq_data = json.load(f)
        
        faqs = faq_data.get('faqs', [])
        return True, f"FAQ file with {len(faqs)} entries"
    except Exception as e:
        return False, f"Invalid FAQ file: {str(e)}"


def test_search_engine() -> Tuple[bool, str]:
    """Test if search engine can be loaded"""
    try:
        from engines import SearchEngine
        engine = SearchEngine()
        return True, "Search engine loaded successfully"
    except Exception as e:
        return False, f"Failed to load search engine: {str(e)}"


def test_llm_generator() -> Tuple[bool, str]:
    """Test if LLM generator can be initialized"""
    try:
        from llm import LLMGenerator
        generator = LLMGenerator()
        return True, "LLM generator initialized successfully"
    except Exception as e:
        return False, f"Failed to initialize LLM: {str(e)}"


def test_end_to_end() -> Tuple[bool, str]:
    """Test end-to-end query processing"""
    try:
        from engines import SearchEngine
        from llm import LLMGenerator
        
        # Initialize components
        engine = SearchEngine()
        generator = LLMGenerator()
        
        # Test query
        test_query = "What is the syllabus?"
        
        # Search
        results = engine.search(test_query)
        if not results:
            return False, "Search returned no results"
        
        # Generate response (with timeout)
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("LLM generation timeout")
        
        # Set 15 second timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(15)
        
        try:
            response = generator.generate(test_query, results)
            signal.alarm(0)  # Cancel alarm
            
            if not response or not response.get('answer'):
                return False, "LLM returned empty response"
            
            return True, f"End-to-end test successful (response: {len(response['answer'])} chars)"
        except TimeoutError:
            return False, "LLM generation timed out (>15s)"
        
    except Exception as e:
        return False, f"End-to-end test failed: {str(e)}"


def check_disk_space() -> Tuple[bool, str]:
    """Check available disk space"""
    try:
        stat = os.statvfs('.')
        available_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        
        if available_gb < 5:
            return False, f"Only {available_gb:.1f}GB available (need 5GB+)"
        
        return True, f"{available_gb:.1f}GB available"
    except Exception as e:
        return False, f"Cannot check disk space: {str(e)}"


def check_memory() -> Tuple[bool, str]:
    """Check available memory"""
    try:
        # Try to get memory info (Linux/macOS)
        if sys.platform == 'darwin':  # macOS
            result = subprocess.run(['sysctl', 'hw.memsize'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                mem_bytes = int(result.stdout.split(':')[1].strip())
                mem_gb = mem_bytes / (1024**3)
                
                if mem_gb < 8:
                    return False, f"Only {mem_gb:.1f}GB RAM (need 8GB+)"
                
                return True, f"{mem_gb:.1f}GB RAM available"
        
        elif sys.platform.startswith('linux'):
            with open('/proc/meminfo') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        mem_kb = int(line.split()[1])
                        mem_gb = mem_kb / (1024**2)
                        
                        if mem_gb < 8:
                            return False, f"Only {mem_gb:.1f}GB RAM (need 8GB+)"
                        
                        return True, f"{mem_gb:.1f}GB RAM available"
        
        return True, "Memory check not available on this platform"
    except Exception as e:
        return True, f"Cannot check memory: {str(e)} (non-critical)"


def main():
    """Run all deployment verification checks"""
    print_header("CAMPUS AI ASSISTANT - DEPLOYMENT VERIFICATION")
    
    print(f"{YELLOW}This script verifies all prerequisites for classroom deployment{RESET}\n")
    
    # Track results
    checks = []
    
    # System Requirements
    print_header("1. SYSTEM REQUIREMENTS")
    
    passed, details = check_python_version()
    print_check("Python Version", passed, details)
    checks.append(('Python Version', passed, True))
    
    passed, details = check_memory()
    print_check("Memory (RAM)", passed, details)
    checks.append(('Memory', passed, False))  # Non-critical
    
    passed, details = check_disk_space()
    print_check("Disk Space", passed, details)
    checks.append(('Disk Space', passed, True))
    
    # Dependencies
    print_header("2. DEPENDENCIES")
    
    passed, details = check_dependencies()
    print_check("Python Packages", passed, details)
    checks.append(('Dependencies', passed, True))
    
    passed, details = check_ollama()
    print_check("Ollama Service", passed, details)
    checks.append(('Ollama', passed, True))
    
    # Configuration
    print_header("3. CONFIGURATION")
    
    passed, details = check_config()
    print_check("Configuration File", passed, details)
    checks.append(('Config', passed, True))
    
    # Data Files
    print_header("4. DATA FILES")
    
    passed, details = check_documents()
    print_check("PDF Documents", passed, details)
    checks.append(('Documents', passed, True))
    
    passed, details = check_indices()
    print_check("Search Indices", passed, details)
    checks.append(('Indices', passed, True))
    
    passed, details = check_faq()
    print_check("FAQ Database", passed, details)
    checks.append(('FAQ', passed, False))  # Optional
    
    # Component Tests
    print_header("5. COMPONENT TESTS")
    
    passed, details = test_search_engine()
    print_check("Search Engine", passed, details)
    checks.append(('Search Engine', passed, True))
    
    passed, details = test_llm_generator()
    print_check("LLM Generator", passed, details)
    checks.append(('LLM Generator', passed, True))
    
    # End-to-End Test
    print_header("6. END-TO-END TEST")
    
    print(f"{YELLOW}Running end-to-end query test (may take 10-15 seconds)...{RESET}\n")
    passed, details = test_end_to_end()
    print_check("Full Query Pipeline", passed, details)
    checks.append(('End-to-End', passed, True))
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    critical_checks = [c for c in checks if c[2]]  # Only critical checks
    passed_critical = sum(1 for c in critical_checks if c[1])
    total_critical = len(critical_checks)
    
    all_checks = checks
    passed_all = sum(1 for c in all_checks if c[1])
    total_all = len(all_checks)
    
    print(f"Critical Checks: {passed_critical}/{total_critical} passed")
    print(f"All Checks: {passed_all}/{total_all} passed\n")
    
    # Failed checks
    failed = [c[0] for c in checks if not c[1] and c[2]]
    if failed:
        print(f"{RED}Failed Critical Checks:{RESET}")
        for name in failed:
            print(f"  • {name}")
        print()
    
    # Deployment readiness
    if passed_critical == total_critical:
        print(f"{GREEN}{'=' * 70}{RESET}")
        print(f"{GREEN}✓ SYSTEM READY FOR DEPLOYMENT{RESET}".center(80))
        print(f"{GREEN}{'=' * 70}{RESET}\n")
        
        print("Next steps:")
        print("  1. Start the application: streamlit run app.py")
        print("  2. Access at: http://localhost:8501")
        print("  3. Test with sample queries")
        print("  4. Monitor logs in data/logs/")
        print()
        
        return 0
    else:
        print(f"{RED}{'=' * 70}{RESET}")
        print(f"{RED}✗ SYSTEM NOT READY - FIX ISSUES ABOVE{RESET}".center(80))
        print(f"{RED}{'=' * 70}{RESET}\n")
        
        print("Troubleshooting:")
        print("  • Check DEPLOYMENT.md for detailed setup instructions")
        print("  • Ensure all dependencies are installed: pip install -r requirements.txt")
        print("  • Verify Ollama is running: ollama serve")
        print("  • Build indices if missing: python indexer.py")
        print()
        
        return 1


if __name__ == '__main__':
    sys.exit(main())
