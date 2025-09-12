#!/usr/bin/env python3
"""
End-to-end integration testing script for Policy Pilot RAG backend.
Tests document upload via API, query processing, OpenSearch indexing, and health checks.
"""

import asyncio
import json
import time
import requests
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config.settings import settings


class IntegrationTester:
    """Integration testing class for Policy Pilot RAG backend."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the integration tester.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.test_results = []
        self.uploaded_documents = []
        
    def log_test(self, test_name: str, success: bool, message: str, 
                 duration: float = 0.0, details: Optional[Dict] = None):
        """Log a test result.
        
        Args:
            test_name: Name of the test
            success: Whether the test passed
            message: Test result message
            duration: Test duration in seconds
            details: Additional test details
        """
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'duration': duration,
            'details': details or {},
            'timestamp': time.time()
        }
        self.test_results.append(result)
        
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}: {message} ({duration:.2f}s)")
        
        if details and not success:
            print(f"  Details: {json.dumps(details, indent=2)}")
    
    def test_health_check(self) -> bool:
        """Test health check endpoint.
        
        Returns:
            True if health check passes
        """
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                self.log_test(
                    "Health Check",
                    True,
                    f"API is healthy - Status: {health_data.get('status', 'unknown')}",
                    duration,
                    health_data
                )
                return True
            else:
                self.log_test(
                    "Health Check",
                    False,
                    f"API returned status {response.status_code}",
                    duration,
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(
                "Health Check",
                False,
                f"Failed to connect to API: {str(e)}",
                duration,
                {"error": str(e)}
            )
            return False
    
    def test_document_upload(self, file_path: str, filename: str) -> Optional[str]:
        """Test document upload via API.
        
        Args:
            file_path: Path to the document file
            filename: Name of the file
            
        Returns:
            Document ID if successful, None otherwise
        """
        start_time = time.time()
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/pdf')}
                response = self.session.post(f"{self.base_url}/api/upload-document", files=files)
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                upload_data = response.json()
                if upload_data.get('success'):
                    document_id = upload_data.get('document_id')
                    self.uploaded_documents.append(document_id)
                    self.log_test(
                        f"Document Upload - {filename}",
                        True,
                        f"Document uploaded successfully - ID: {document_id}",
                        duration,
                        upload_data
                    )
                    return document_id
                else:
                    self.log_test(
                        f"Document Upload - {filename}",
                        False,
                        f"Upload failed: {upload_data.get('message', 'Unknown error')}",
                        duration,
                        upload_data
                    )
                    return None
            else:
                self.log_test(
                    f"Document Upload - {filename}",
                    False,
                    f"Upload failed with status {response.status_code}",
                    duration,
                    {"status_code": response.status_code, "response": response.text}
                )
                return None
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(
                f"Document Upload - {filename}",
                False,
                f"Upload failed with exception: {str(e)}",
                duration,
                {"error": str(e)}
            )
            return None
    
    def test_query_processing(self, question: str, use_rag: bool = True) -> bool:
        """Test query processing via API.
        
        Args:
            question: Query question
            use_rag: Whether to use RAG for the query
            
        Returns:
            True if query processing succeeds
        """
        start_time = time.time()
        
        try:
            query_data = {
                "question": question,
                "use_rag": use_rag,
                "search_type": "semantic",
                "top_k": 5,
                "min_score": 0.7
            }
            
            response = self.session.post(
                f"{self.base_url}/api/query",
                json=query_data,
                headers={"Content-Type": "application/json"}
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                query_result = response.json()
                if query_result.get('success'):
                    self.log_test(
                        f"Query Processing - {'RAG' if use_rag else 'Direct'}",
                        True,
                        f"Query processed successfully - {len(query_result.get('sources', []))} sources found",
                        duration,
                        {
                            "question": question,
                            "answer_length": len(query_result.get('answer', '')),
                            "sources_count": len(query_result.get('sources', [])),
                            "tokens_used": query_result.get('tokens_used', 0),
                            "processing_time": query_result.get('processing_time', 0)
                        }
                    )
                    return True
                else:
                    self.log_test(
                        f"Query Processing - {'RAG' if use_rag else 'Direct'}",
                        False,
                        f"Query processing failed: {query_result.get('message', 'Unknown error')}",
                        duration,
                        query_result
                    )
                    return False
            else:
                self.log_test(
                    f"Query Processing - {'RAG' if use_rag else 'Direct'}",
                    False,
                    f"Query failed with status {response.status_code}",
                    duration,
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(
                f"Query Processing - {'RAG' if use_rag else 'Direct'}",
                False,
                f"Query failed with exception: {str(e)}",
                duration,
                {"error": str(e)}
            )
            return False
    
    def test_document_listing(self) -> bool:
        """Test document listing endpoint.
        
        Returns:
            True if document listing succeeds
        """
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.base_url}/api/documents")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                documents_data = response.json()
                if documents_data.get('success'):
                    doc_count = documents_data.get('total_count', 0)
                    self.log_test(
                        "Document Listing",
                        True,
                        f"Retrieved {doc_count} documents",
                        duration,
                        {
                            "total_documents": doc_count,
                            "page": documents_data.get('page', 1),
                            "page_size": documents_data.get('page_size', 10)
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Document Listing",
                        False,
                        f"Document listing failed: {documents_data.get('message', 'Unknown error')}",
                        duration,
                        documents_data
                    )
                    return False
            else:
                self.log_test(
                    "Document Listing",
                    False,
                    f"Document listing failed with status {response.status_code}",
                    duration,
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(
                "Document Listing",
                False,
                f"Document listing failed with exception: {str(e)}",
                duration,
                {"error": str(e)}
            )
            return False
    
    def test_document_statistics(self) -> bool:
        """Test document statistics endpoint.
        
        Returns:
            True if statistics retrieval succeeds
        """
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.base_url}/api/documents/stats")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                stats_data = response.json()
                if stats_data.get('success'):
                    statistics = stats_data.get('statistics', {})
                    self.log_test(
                        "Document Statistics",
                        True,
                        f"Retrieved document statistics",
                        duration,
                        statistics
                    )
                    return True
                else:
                    self.log_test(
                        "Document Statistics",
                        False,
                        f"Statistics retrieval failed: {stats_data.get('message', 'Unknown error')}",
                        duration,
                        stats_data
                    )
                    return False
            else:
                self.log_test(
                    "Document Statistics",
                    False,
                    f"Statistics retrieval failed with status {response.status_code}",
                    duration,
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(
                "Document Statistics",
                False,
                f"Statistics retrieval failed with exception: {str(e)}",
                duration,
                {"error": str(e)}
            )
            return False
    
    def test_document_deletion(self, document_id: str) -> bool:
        """Test document deletion.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if deletion succeeds
        """
        start_time = time.time()
        
        try:
            response = self.session.delete(f"{self.base_url}/api/documents/{document_id}")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                delete_data = response.json()
                if delete_data.get('success'):
                    self.log_test(
                        f"Document Deletion - {document_id}",
                        True,
                        f"Document deleted successfully",
                        duration,
                        delete_data
                    )
                    return True
                else:
                    self.log_test(
                        f"Document Deletion - {document_id}",
                        False,
                        f"Deletion failed: {delete_data.get('message', 'Unknown error')}",
                        duration,
                        delete_data
                    )
                    return False
            else:
                self.log_test(
                    f"Document Deletion - {document_id}",
                    False,
                    f"Deletion failed with status {response.status_code}",
                    duration,
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test(
                f"Document Deletion - {document_id}",
                False,
                f"Deletion failed with exception: {str(e)}",
                duration,
                {"error": str(e)}
            )
            return False
    
    def test_performance_benchmark(self, num_queries: int = 10) -> Dict[str, Any]:
        """Test performance with multiple queries.
        
        Args:
            num_queries: Number of queries to test
            
        Returns:
            Performance statistics
        """
        start_time = time.time()
        
        test_queries = [
            "What is the main purpose of this policy?",
            "What are the key guidelines mentioned?",
            "How should this policy be implemented?",
            "What are the requirements for compliance?",
            "What are the consequences of non-compliance?",
            "Who is responsible for enforcing this policy?",
            "What are the review procedures?",
            "How often should this policy be updated?",
            "What training is required?",
            "What documentation is needed?"
        ]
        
        successful_queries = 0
        total_processing_time = 0
        total_tokens = 0
        
        for i in range(min(num_queries, len(test_queries))):
            query = test_queries[i]
            query_start = time.time()
            
            try:
                query_data = {
                    "question": query,
                    "use_rag": True,
                    "search_type": "semantic",
                    "top_k": 5,
                    "min_score": 0.7
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/query",
                    json=query_data,
                    headers={"Content-Type": "application/json"}
                )
                
                query_duration = time.time() - query_start
                
                if response.status_code == 200:
                    query_result = response.json()
                    if query_result.get('success'):
                        successful_queries += 1
                        total_processing_time += query_result.get('processing_time', query_duration)
                        total_tokens += query_result.get('tokens_used', 0)
                
            except Exception as e:
                print(f"Query {i+1} failed: {str(e)}")
        
        total_duration = time.time() - start_time
        
        performance_stats = {
            'total_queries': num_queries,
            'successful_queries': successful_queries,
            'success_rate': successful_queries / num_queries if num_queries > 0 else 0,
            'total_duration': total_duration,
            'average_query_time': total_processing_time / successful_queries if successful_queries > 0 else 0,
            'total_tokens': total_tokens,
            'queries_per_second': num_queries / total_duration if total_duration > 0 else 0
        }
        
        self.log_test(
            "Performance Benchmark",
            successful_queries == num_queries,
            f"Completed {successful_queries}/{num_queries} queries successfully",
            total_duration,
            performance_stats
        )
        
        return performance_stats
    
    def run_full_integration_test(self, test_documents: List[str]) -> Dict[str, Any]:
        """Run the complete integration test suite.
        
        Args:
            test_documents: List of paths to test documents
            
        Returns:
            Test results summary
        """
        print("Starting Policy Pilot RAG Backend Integration Tests")
        print("=" * 60)
        
        # Test 1: Health Check
        print("\n1. Testing Health Check...")
        health_ok = self.test_health_check()
        
        if not health_ok:
            print("Health check failed. Aborting integration tests.")
            return self.get_test_summary()
        
        # Test 2: Document Upload
        print("\n2. Testing Document Upload...")
        uploaded_docs = []
        for doc_path in test_documents:
            if Path(doc_path).exists():
                filename = Path(doc_path).name
                doc_id = self.test_document_upload(doc_path, filename)
                if doc_id:
                    uploaded_docs.append(doc_id)
        
        # Test 3: Document Listing
        print("\n3. Testing Document Listing...")
        self.test_document_listing()
        
        # Test 4: Document Statistics
        print("\n4. Testing Document Statistics...")
        self.test_document_statistics()
        
        # Test 5: Query Processing (RAG)
        print("\n5. Testing Query Processing (RAG)...")
        self.test_query_processing("What is the main purpose of this policy?", use_rag=True)
        self.test_query_processing("What are the key guidelines mentioned?", use_rag=True)
        
        # Test 6: Query Processing (Direct)
        print("\n6. Testing Query Processing (Direct)...")
        self.test_query_processing("What is artificial intelligence?", use_rag=False)
        
        # Test 7: Performance Benchmark
        print("\n7. Testing Performance...")
        performance_stats = self.test_performance_benchmark(num_queries=5)
        
        # Test 8: Document Deletion
        print("\n8. Testing Document Deletion...")
        for doc_id in uploaded_docs[:2]:  # Delete first 2 documents
            self.test_document_deletion(doc_id)
        
        # Final Health Check
        print("\n9. Final Health Check...")
        self.test_health_check()
        
        return self.get_test_summary()
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all test results.
        
        Returns:
            Test results summary
        """
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(result['duration'] for result in self.test_results)
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'total_duration': total_duration,
            'average_test_duration': total_duration / total_tests if total_tests > 0 else 0,
            'test_results': self.test_results
        }
        
        print("\n" + "=" * 60)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Total Duration: {total_duration:.2f}s")
        print(f"Average Test Duration: {summary['average_test_duration']:.2f}s")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        return summary


def create_test_documents(temp_dir: Path) -> List[str]:
    """Create test documents for integration testing.
    
    Args:
        temp_dir: Temporary directory to create documents in
        
    Returns:
        List of paths to created test documents
    """
    test_documents = []
    
    # Create sample PDF content (simplified)
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Policy Document) Tj
0 -20 Td
(This is a test policy document for integration testing.) Tj
0 -20 Td
(It contains important policy information and guidelines.) Tj
0 -20 Td
(The document outlines procedures and requirements.) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
453
%%EOF"""
    
    # Create sample text content
    txt_content = """Test Policy Document

This is a test policy document for integration testing purposes.
It contains multiple paragraphs with different information about policies.

Section 1: Introduction
This section introduces the policy and its objectives.
The policy aims to establish clear guidelines for all stakeholders.

Section 2: Guidelines
This section outlines the specific guidelines to follow.
All employees must comply with these guidelines.

Section 3: Implementation
This section describes how to implement the policy.
Implementation should be done in phases.

Section 4: Compliance
This section covers compliance requirements.
Regular audits will be conducted to ensure compliance.

Section 5: Review
This section describes the review process.
The policy will be reviewed annually.
"""
    
    # Create test files
    pdf_file = temp_dir / "test_policy.pdf"
    pdf_file.write_bytes(pdf_content)
    test_documents.append(str(pdf_file))
    
    txt_file = temp_dir / "test_policy.txt"
    txt_file.write_text(txt_content)
    test_documents.append(str(txt_file))
    
    return test_documents


def main():
    """Main function for running integration tests."""
    parser = argparse.ArgumentParser(description="Policy Pilot RAG Backend Integration Tests")
    parser.add_argument("--base-url", default="http://localhost:8000", 
                       help="Base URL of the API server")
    parser.add_argument("--test-docs", nargs="+", 
                       help="Paths to test documents")
    parser.add_argument("--create-test-docs", action="store_true",
                       help="Create test documents automatically")
    parser.add_argument("--performance-queries", type=int, default=5,
                       help="Number of queries for performance testing")
    parser.add_argument("--output", help="Output file for test results (JSON)")
    
    args = parser.parse_args()
    
    # Create test documents if requested
    test_documents = []
    if args.create_test_docs:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_documents = create_test_documents(temp_path)
    elif args.test_docs:
        test_documents = args.test_docs
    else:
        print("No test documents provided. Use --test-docs or --create-test-docs")
        return 1
    
    # Run integration tests
    tester = IntegrationTester(base_url=args.base_url)
    results = tester.run_full_integration_test(test_documents)
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nTest results saved to: {args.output}")
    
    # Return exit code based on test results
    return 0 if results['failed_tests'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
