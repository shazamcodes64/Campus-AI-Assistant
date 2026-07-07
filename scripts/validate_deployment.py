#!/usr/bin/env python3
"""
Deployment validation script
Checks that all components are properly configured and working
"""

import sys
import os
import json
import subprocess
import requests
from pathlib import Path

class DeploymentValidator:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
    
    def check(self, name, condition, error_msg="", warning=False):
        """Run a validation check"""
        if condition:
            print(f"✅ {name}")
            self.checks_passed += 1
            return True
        else:
            if warning:
                print(f"⚠️  {name}")
                self.warnings.append(f"{name}: {error_msg}")
            else:
                print(f"❌ {name}")
                if error_msg:
                    print(f"   {error_msg}")
                self.checks_failed += 1
            return False
    
    def validate_python_environment(self):
        """Validate Python version and virtual environment"""
        print("\n🐍 Python Environment")
        print("-" * 40)
        
        # Check Python version
        version = sys.version_info
        self.check(
            "Python version >= 3.9",
            version.major == 3 and version.minor >= 9,
            f"Found Python {version.major}.{version.minor}, need 3.9+"
        )
        
        # Check if in virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        self.check(
            "Virtual environment active",
            in_venv,
            "Run: source venv/bin/activate"
        )
        
        # Check required packages
        required_packages = [
            "streamlit",
            "sentence_transformers",
            "faiss",
            "rank_bm25",
            "requests",
            "PyPDF2",
            "numpy",
            "tiktoken"
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                self.check(f"Package: {package}", True)
            except ImportError:
                self.check(
                    f"Package: {package}",
                    False,
                    f"Run: pip install {package}"
                )
    
    def validate_configuration(self):
        """Validate configuration files"""
        print("\n⚙️  Configuration")
        print("-" * 40)
        
        # Check config.json exists
        config_exists = os.path.exists("config.json")
        self.check("config.json exists", config_exists)
        
        if config_exists:
            try:
                with open("config.json") as f:
                    config = json.load(f)
                
                self.check("config.json valid JSON", True)
                
                # Check required keys
                required_keys = [
                    "ollama_url",
                    "model_name",
                    "embedding_model",
                    "faq_threshold",
                    "doc_threshold",
                    "chunk_size"
                ]
                
                for key in required_keys:
                    self.check(
                        f"Config key: {key}",
                        key in config,
                        f"Add '{key}' to config.json"
                    )
                
            except json.JSONDecodeError as e:
                self.check("config.json valid JSON", False, str(e))
    
    def validate_data_structure(self):
        """Validate data directories and files"""
        print("\n📁 Data Structure")
        print("-" * 40)
        
        # Check directories
        directories = [
            "data",
            "data/documents",
            "data/indices",
            "data/logs"
        ]
        
        for directory in directories:
            self.check(
                f"Directory: {directory}",
                os.path.isdir(directory),
                f"Run: mkdir -p {directory}"
            )
        
        # Check for PDF documents
        if os.path.isdir("data/documents"):
            pdf_files = list(Path("data/documents").glob("*.pdf"))
            self.check(
                "PDF documents present",
                len(pdf_files) > 0,
                "Add PDF files to data/documents/",
                warning=True
            )
            if pdf_files:
                print(f"   Found {len(pdf_files)} PDF files")
        
        # Check for indices
        index_files = [
            "data/indices/faiss.index",
            "data/indices/bm25_index.pkl",
            "data/indices/metadata.json"
        ]
        
        indices_exist = all(os.path.exists(f) for f in index_files)
        self.check(
            "Search indices built",
            indices_exist,
            "Run: python indexer.py",
            warning=True
        )
        
        # Check FAQ file
        faq_exists = os.path.exists("data/faq.json")
        self.check(
            "FAQ database present",
            faq_exists,
            "Create data/faq.json (optional)",
            warning=True
        )
        
        if faq_exists:
            try:
                with open("data/faq.json") as f:
                    faq_data = json.load(f)
                self.check("FAQ JSON valid", True)
                
                num_faqs = len(faq_data.get("faqs", []))
                print(f"   Found {num_faqs} FAQ entries")
                
            except json.JSONDecodeError:
                self.check("FAQ JSON valid", False, "Fix JSON syntax in data/faq.json")
    
    def validate_ollama(self):
        """Validate Ollama service"""
        print("\n🤖 Ollama Service")
        print("-" * 40)
        
        # Check if Ollama is running
        try:
            with open("config.json") as f:
                config = json.load(f)
            ollama_url = config.get("ollama_url", "http://localhost:11434")
        except:
            ollama_url = "http://localhost:11434"
        
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            self.check("Ollama service running", response.status_code == 200)
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                # Check if required model is available
                try:
                    with open("config.json") as f:
                        config = json.load(f)
                    required_model = config.get("model_name", "llama3:latest")
                except:
                    required_model = "llama3:latest"
                
                model_available = any(required_model in name for name in model_names)
                self.check(
                    f"Model '{required_model}' available",
                    model_available,
                    f"Run: ollama pull {required_model}"
                )
                
                if model_names:
                    print(f"   Available models: {', '.join(model_names)}")
        
        except requests.exceptions.ConnectionError:
            self.check(
                "Ollama service running",
                False,
                "Start Ollama: ollama serve"
            )
        except Exception as e:
            self.check("Ollama service running", False, str(e))
    
    def validate_application_files(self):
        """Validate core application files"""
        print("\n📄 Application Files")
        print("-" * 40)
        
        core_files = [
            "app.py",
            "engines.py",
            "llm.py",
            "indexer.py",
            "requirements.txt"
        ]
        
        for file in core_files:
            self.check(f"File: {file}", os.path.exists(file))
        
        # Check scripts
        script_files = [
            "scripts/test_system.py",
            "scripts/auto_eval.py",
            "scripts/load_test.py"
        ]
        
        for file in script_files:
            self.check(
                f"Script: {file}",
                os.path.exists(file),
                warning=True
            )
    
    def validate_imports(self):
        """Validate that core modules can be imported"""
        print("\n📦 Module Imports")
        print("-" * 40)
        
        modules = [
            ("engines", "SearchEngine"),
            ("llm", "LLMGenerator"),
            ("indexer", "DocumentIndexer")
        ]
        
        for module_name, class_name in modules:
            try:
                module = __import__(module_name)
                has_class = hasattr(module, class_name)
                self.check(
                    f"Import: {module_name}.{class_name}",
                    has_class,
                    f"Check {module_name}.py for errors"
                )
            except Exception as e:
                self.check(
                    f"Import: {module_name}.{class_name}",
                    False,
                    str(e)
                )
    
    def validate_system_resources(self):
        """Check system resources"""
        print("\n💻 System Resources")
        print("-" * 40)
        
        try:
            import psutil
            
            # Check RAM
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024**3)
            available_gb = memory.available / (1024**3)
            
            self.check(
                f"RAM: {total_gb:.1f}GB total",
                total_gb >= 8,
                "Recommended: 8GB+ RAM",
                warning=True
            )
            print(f"   Available: {available_gb:.1f}GB")
            
            # Check disk space
            disk = psutil.disk_usage('.')
            free_gb = disk.free / (1024**3)
            
            self.check(
                f"Disk space: {free_gb:.1f}GB free",
                free_gb >= 10,
                "Recommended: 10GB+ free space",
                warning=True
            )
            
            # Check CPU
            cpu_count = psutil.cpu_count()
            self.check(
                f"CPU cores: {cpu_count}",
                cpu_count >= 4,
                "Recommended: 4+ cores",
                warning=True
            )
            
        except ImportError:
            print("   ⚠️  psutil not installed (optional)")
            print("   Run: pip install psutil")
    
    def run_smoke_test(self):
        """Run a quick smoke test"""
        print("\n🧪 Smoke Test")
        print("-" * 40)
        
        try:
            # Try to initialize components
            sys.path.insert(0, os.getcwd())
            
            from engines import SearchEngine
            from llm import LLMGenerator
            
            with open("config.json") as f:
                config = json.load(f)
            
            # Test search engine
            try:
                engine = SearchEngine(config)
                self.check("SearchEngine initialization", True)
            except Exception as e:
                self.check("SearchEngine initialization", False, str(e))
            
            # Test LLM generator
            try:
                llm = LLMGenerator(config)
                self.check("LLMGenerator initialization", True)
                
                # Test connection
                connection_ok = llm.test_connection()
                self.check("LLM connection test", connection_ok, warning=True)
                
            except Exception as e:
                self.check("LLMGenerator initialization", False, str(e))
            
        except Exception as e:
            self.check("Smoke test", False, str(e))
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        total_checks = self.checks_passed + self.checks_failed
        
        print(f"\n✅ Passed: {self.checks_passed}/{total_checks}")
        print(f"❌ Failed: {self.checks_failed}/{total_checks}")
        
        if self.warnings:
            print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.checks_failed == 0:
            print("\n🎉 All critical checks passed!")
            print("System is ready for deployment.")
            return True
        else:
            print("\n⚠️  Some checks failed.")
            print("Fix the issues above before deploying.")
            return False

def main():
    """Run deployment validation"""
    print("🔍 Campus AI Assistant - Deployment Validation")
    print("="*60)
    
    validator = DeploymentValidator()
    
    # Run all validations
    validator.validate_python_environment()
    validator.validate_configuration()
    validator.validate_data_structure()
    validator.validate_ollama()
    validator.validate_application_files()
    validator.validate_imports()
    validator.validate_system_resources()
    validator.run_smoke_test()
    
    # Print summary
    success = validator.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
