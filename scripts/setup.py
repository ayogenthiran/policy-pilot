#!/usr/bin/env python3
"""
Setup script for Policy Pilot RAG Backend.
Initializes OpenSearch index, tests connections, and verifies configuration.
"""

import os
import sys
import time
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings
from src.core.logging import get_logger
from src.config.database import opensearch_connection
from src.services.rag_service import RAGService
from src.services.embedding_service import EmbeddingService

logger = get_logger(__name__)


def print_banner():
    """Print setup banner."""
    print("=" * 60)
    print("Policy Pilot RAG Backend Setup")
    print("=" * 60)
    print()


def check_environment():
    """Check environment configuration."""
    print("🔧 Checking environment configuration...")
    
    required_vars = [
        'OPENAI_API_KEY',
        'OPENSEARCH_URL',
        'OPENSEARCH_INDEX'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment")
        return False
    
    print("✅ Environment variables configured")
    return True


def test_opensearch_connection():
    """Test OpenSearch connection."""
    print("🔍 Testing OpenSearch connection...")
    
    try:
        health = opensearch_connection.health_check()
        if health['status'] == 'healthy':
            print(f"✅ OpenSearch connected: {health.get('cluster_name', 'Unknown')}")
            print(f"   Version: {health.get('opensearch_version', 'Unknown')}")
            print(f"   URL: {settings.opensearch_url}")
            return True
        else:
            print(f"❌ OpenSearch connection failed: {health.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ OpenSearch connection error: {e}")
        return False


def initialize_opensearch_index():
    """Initialize OpenSearch index."""
    print("📊 Initializing OpenSearch index...")
    
    try:
        from src.services.search_service import SearchService
        search_service = SearchService()
        
        # Ensure index exists
        if search_service.ensure_index_exists():
            print(f"✅ OpenSearch index '{settings.opensearch_index}' created/verified")
            return True
        else:
            print(f"❌ Failed to create OpenSearch index")
            return False
    except Exception as e:
        print(f"❌ OpenSearch index initialization error: {e}")
        return False


def test_embedding_service():
    """Test embedding service."""
    print("🧠 Testing embedding service...")
    
    try:
        embedding_service = EmbeddingService()
        
        # Load model
        embedding_service.load_model()
        
        # Test embedding generation
        test_text = "This is a test for embedding generation."
        embedding = embedding_service.get_embedding(test_text)
        
        if embedding is not None and len(embedding) > 0:
            print(f"✅ Embedding service working: {len(embedding)} dimensions")
            print(f"   Model: {settings.embedding_model}")
            return True
        else:
            print("❌ Embedding generation failed")
            return False
    except Exception as e:
        print(f"❌ Embedding service error: {e}")
        return False


def test_gpt_service():
    """Test GPT service."""
    print("🤖 Testing GPT service...")
    
    try:
        from src.services.gpt_service import GPTService
        gpt_service = GPTService()
        
        # Test connection
        health = gpt_service.health_check()
        
        if health['status'] == 'healthy':
            print(f"✅ GPT service connected: {health.get('model', 'Unknown')}")
            print(f"   Model: {settings.openai_model}")
            return True
        else:
            print(f"❌ GPT service connection failed: {health.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ GPT service error: {e}")
        return False


def test_rag_pipeline():
    """Test complete RAG pipeline."""
    print("🔄 Testing RAG pipeline...")
    
    try:
        rag_service = RAGService()
        
        # Test pipeline
        test_result = rag_service.test_rag_pipeline()
        
        if test_result.get('success', False):
            print("✅ RAG pipeline test successful")
            print(f"   Response length: {test_result.get('response_length', 0)} characters")
            print(f"   Sources found: {test_result.get('sources_found', 0)}")
            print(f"   Processing time: {test_result.get('processing_time', 0):.2f}s")
            return True
        else:
            print(f"❌ RAG pipeline test failed: {test_result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ RAG pipeline test error: {e}")
        return False


def create_directories():
    """Create necessary directories."""
    print("📁 Creating necessary directories...")
    
    directories = [
        'uploads',
        'data',
        'logs',
        'models'
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(exist_ok=True)
        print(f"   ✅ Created directory: {directory}")
    
    return True


def download_embedding_model():
    """Download and cache embedding model."""
    print("📥 Downloading embedding model...")
    
    try:
        embedding_service = EmbeddingService()
        embedding_service.load_model()
        
        # Test with a simple embedding to ensure model is cached
        test_embedding = embedding_service.get_embedding("Test model download")
        
        if test_embedding is not None:
            print(f"✅ Embedding model downloaded and cached")
            print(f"   Model: {settings.embedding_model}")
            print(f"   Dimensions: {len(test_embedding)}")
            return True
        else:
            print("❌ Failed to download embedding model")
            return False
    except Exception as e:
        print(f"❌ Embedding model download error: {e}")
        return False


def run_health_check():
    """Run comprehensive health check."""
    print("🏥 Running comprehensive health check...")
    
    try:
        rag_service = RAGService()
        health_status = rag_service.get_system_health()
        
        print(f"   Overall status: {health_status['status']}")
        
        for service, status in health_status['services'].items():
            status_icon = "✅" if status['status'] == 'healthy' else "❌"
            print(f"   {status_icon} {service}: {status['status']}")
        
        if health_status['status'] == 'healthy':
            print("✅ All services are healthy")
            return True
        else:
            print("❌ Some services are not healthy")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def main():
    """Main setup function."""
    print_banner()
    
    # Track setup results
    results = []
    
    # Step 1: Check environment
    results.append(("Environment Check", check_environment()))
    
    # Step 2: Create directories
    results.append(("Directory Creation", create_directories()))
    
    # Step 3: Test OpenSearch connection
    results.append(("OpenSearch Connection", test_opensearch_connection()))
    
    # Step 4: Initialize OpenSearch index
    results.append(("OpenSearch Index", initialize_opensearch_index()))
    
    # Step 5: Test embedding service
    results.append(("Embedding Service", test_embedding_service()))
    
    # Step 6: Download embedding model
    results.append(("Model Download", download_embedding_model()))
    
    # Step 7: Test GPT service
    results.append(("GPT Service", test_gpt_service()))
    
    # Step 8: Test RAG pipeline
    results.append(("RAG Pipeline", test_rag_pipeline()))
    
    # Step 9: Run health check
    results.append(("Health Check", run_health_check()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Setup Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for step, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {step}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} steps passed")
    
    if passed == total:
        print("\n🎉 Setup completed successfully!")
        print("You can now start the Policy Pilot API with:")
        print("   python src/main.py")
        print("   or")
        print("   docker-compose up")
        return True
    else:
        print(f"\n⚠️  Setup completed with {total - passed} errors")
        print("Please check the error messages above and fix any issues")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
