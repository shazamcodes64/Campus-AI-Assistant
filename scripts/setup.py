#!/usr/bin/env python3
"""
Setup script for Campus AI Assistant
Validates environment and dependencies
"""

import subprocess
import sys
import os
import requests
import json

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if all dependencies are installed"""
    try:
        with open("requirements.txt", "r") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        missing = []
        for req in requirements:
            package = req.split("==")[0].split(">=")[0].split("<=")[0]
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing.append(req)
        
        if missing:
            print(f"❌ Missing dependencies: {', '.join(missing)}")
            print("Run: pip install -r requirements.txt")
            return False
        
        print("✅ All dependencies installed")
        return True
    
    except Exception as e:
        print(f"❌ Error checking dependencies: {e}")
        return False

def check_ollama():
    """Check Ollama installation and service"""
    try:
        # Check if ollama command exists
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Ollama not installed")
            print("Install: curl -fsSL https://ollama.ai/install.sh | sh")
            return False
        
        print("✅ Ollama installed")
        
        # Check if service is running
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama service running")
                
                # Check if llama2:7b model is available
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                if any("llama2" in name for name in model_names):
                    print("✅ llama2 model available")
                    return True
                else:
                    print("⚠️  llama2 model not found")
                    print("Run: ollama pull llama2:7b")
                    return False
            else:
                print("❌ Ollama service not responding")
                return False
        
        except requests.exceptions.RequestException:
            print("❌ Ollama service not running")
            print("Run: ollama serve")
            return False
    
    except FileNotFoundError:
        print("❌ Ollama not installed")
        print("Install: curl -fsSL https://ollama.ai/install.sh | sh")
        return False

def check_directories():
    """Check and create necessary directories"""
    dirs = [
        "data",
        "data/documents", 
        "data/indices",
        "data/logs"
    ]
    
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"📁 Created directory: {dir_path}")
        else:
            print(f"✅ Directory exists: {dir_path}")
    
    return True

def check_config():
    """Check configuration file"""
    if not os.path.exists("config.json"):
        print("❌ config.json not found")
        return False
    
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        
        required_keys = [
            "ollama_url", "model_name", "embedding_model",
            "faq_threshold", "doc_threshold", "max_tokens"
        ]
        
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            print(f"❌ Missing config keys: {', '.join(missing_keys)}")
            return False
        
        print("✅ Configuration valid")
        return True
    
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False

def main():
    """Run all checks"""
    print("🔍 Campus AI Assistant - Environment Check\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Ollama Service", check_ollama),
        ("Directories", check_directories),
        ("Configuration", check_config)
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        if not check_func():
            all_passed = False
    
    print("\n" + "="*50)
    
    if all_passed:
        print("🎉 All checks passed! System ready.")
        print("\nNext steps:")
        print("1. Add PDF files to data/documents/")
        print("2. Run: python indexer.py")
        print("3. Run: streamlit run app.py")
    else:
        print("❌ Some checks failed. Fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()