#!/usr/bin/env python3
"""
Script to load sample policy documents for development and testing.
Creates a test dataset and verifies the system works with real documents.
"""

import asyncio
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import sys
import tempfile
import shutil

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config.settings import settings


class SampleDataLoader:
    """Class for loading sample policy documents into the system."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the sample data loader.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.loaded_documents = []
        
    def check_api_health(self) -> bool:
        """Check if the API is healthy and ready.
        
        Returns:
            True if API is healthy
        """
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"API Health: {health_data.get('status', 'unknown')}")
                return health_data.get('status') == 'healthy'
            else:
                print(f"API Health Check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"Failed to connect to API: {str(e)}")
            return False
    
    def upload_document(self, file_path: str, filename: str) -> Optional[Dict[str, Any]]:
        """Upload a document to the system.
        
        Args:
            file_path: Path to the document file
            filename: Name of the file
            
        Returns:
            Upload result data or None if failed
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/pdf')}
                response = self.session.post(f"{self.base_url}/api/upload-document", files=files)
            
            if response.status_code == 200:
                upload_data = response.json()
                if upload_data.get('success'):
                    print(f"✓ Uploaded: {filename} (ID: {upload_data.get('document_id')})")
                    self.loaded_documents.append({
                        'document_id': upload_data.get('document_id'),
                        'filename': filename,
                        'file_path': file_path,
                        'status': upload_data.get('status'),
                        'chunks_created': upload_data.get('chunks_created', 0),
                        'processing_time': upload_data.get('processing_time', 0)
                    })
                    return upload_data
                else:
                    print(f"✗ Upload failed: {filename} - {upload_data.get('message', 'Unknown error')}")
                    return None
            else:
                print(f"✗ Upload failed: {filename} - HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ Upload failed: {filename} - {str(e)}")
            return None
    
    def test_query(self, question: str, use_rag: bool = True) -> Optional[Dict[str, Any]]:
        """Test a query against the loaded documents.
        
        Args:
            question: Query question
            use_rag: Whether to use RAG for the query
            
        Returns:
            Query result data or None if failed
        """
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
            
            if response.status_code == 200:
                query_result = response.json()
                if query_result.get('success'):
                    print(f"✓ Query successful: {question[:50]}...")
                    print(f"  Answer: {query_result.get('answer', '')[:100]}...")
                    print(f"  Sources: {len(query_result.get('sources', []))}")
                    print(f"  Tokens: {query_result.get('tokens_used', 0)}")
                    return query_result
                else:
                    print(f"✗ Query failed: {question[:50]}... - {query_result.get('message', 'Unknown error')}")
                    return None
            else:
                print(f"✗ Query failed: {question[:50]}... - HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ Query failed: {question[:50]}... - {str(e)}")
            return None
    
    def get_system_statistics(self) -> Optional[Dict[str, Any]]:
        """Get system statistics.
        
        Returns:
            System statistics or None if failed
        """
        try:
            response = self.session.get(f"{self.base_url}/api/documents/stats")
            
            if response.status_code == 200:
                stats_data = response.json()
                if stats_data.get('success'):
                    statistics = stats_data.get('statistics', {})
                    print("System Statistics:")
                    print(f"  Total Documents: {statistics.get('documents', {}).get('total_documents', 0)}")
                    print(f"  Index Size: {statistics.get('documents', {}).get('index_size_mb', 0):.2f} MB")
                    return statistics
                else:
                    print(f"Failed to get statistics: {stats_data.get('message', 'Unknown error')}")
                    return None
            else:
                print(f"Failed to get statistics: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Failed to get statistics: {str(e)}")
            return None
    
    def create_sample_documents(self, output_dir: Path) -> List[Path]:
        """Create sample policy documents for testing.
        
        Args:
            output_dir: Directory to create documents in
            
        Returns:
            List of paths to created documents
        """
        documents = []
        
        # Sample Policy Document 1: Data Privacy Policy
        privacy_policy = """Data Privacy Policy

1. Introduction
This policy outlines how our organization collects, uses, and protects personal data in accordance with applicable privacy laws and regulations.

2. Data Collection
We collect personal data only when necessary for legitimate business purposes. This includes:
- Contact information (name, email, phone number)
- Professional information (job title, company)
- Usage data (website interactions, service usage)

3. Data Use
Personal data is used for:
- Providing and improving our services
- Communicating with customers
- Complying with legal obligations
- Marketing (with consent)

4. Data Protection
We implement appropriate technical and organizational measures to protect personal data, including:
- Encryption of data in transit and at rest
- Access controls and authentication
- Regular security assessments
- Staff training on data protection

5. Data Retention
Personal data is retained only as long as necessary for the purposes for which it was collected, or as required by law.

6. Individual Rights
Individuals have the right to:
- Access their personal data
- Correct inaccurate data
- Delete their data
- Object to processing
- Data portability

7. Contact Information
For questions about this policy, contact our Data Protection Officer at privacy@company.com.

8. Policy Updates
This policy may be updated periodically. Changes will be communicated to affected individuals.
"""
        
        # Sample Policy Document 2: Remote Work Policy
        remote_work_policy = """Remote Work Policy

1. Purpose
This policy establishes guidelines for remote work arrangements to ensure productivity, security, and employee well-being.

2. Eligibility
Remote work is available to employees whose job functions can be performed effectively from a remote location, subject to manager approval.

3. Work Environment
Remote workers must maintain:
- A dedicated workspace free from distractions
- Reliable internet connection (minimum 25 Mbps)
- Appropriate security measures for company data
- Professional appearance for video calls

4. Work Hours
Remote workers are expected to:
- Maintain regular business hours
- Be available during core collaboration hours (9 AM - 3 PM)
- Log work hours accurately
- Attend all scheduled meetings

5. Security Requirements
Remote workers must:
- Use company-provided devices when possible
- Install and maintain security software
- Use VPN for accessing company systems
- Follow password and authentication policies
- Secure physical documents and devices

6. Communication
Remote workers should:
- Use company-approved communication tools
- Respond to messages within 2 hours during business hours
- Participate in team meetings and check-ins
- Maintain regular contact with supervisors

7. Performance Management
Performance is evaluated based on:
- Quality of work output
- Meeting deadlines and commitments
- Communication and collaboration
- Adherence to policies and procedures

8. Equipment and Expenses
The company may provide:
- Laptop or desktop computer
- Monitor and peripherals
- Software licenses
- Internet reimbursement (up to $50/month)

9. Policy Violations
Violations of this policy may result in:
- Additional training requirements
- Modification of remote work arrangements
- Disciplinary action up to and including termination

10. Review and Updates
This policy will be reviewed annually and updated as needed to reflect changing business needs and best practices.
"""
        
        # Sample Policy Document 3: Information Security Policy
        security_policy = """Information Security Policy

1. Overview
This policy establishes the framework for protecting the confidentiality, integrity, and availability of organizational information and information systems.

2. Scope
This policy applies to all employees, contractors, vendors, and third parties who have access to organizational information systems or data.

3. Information Classification
Information is classified into four categories:
- Public: Information that can be freely shared
- Internal: Information for internal use only
- Confidential: Information requiring protection
- Restricted: Highly sensitive information with strict access controls

4. Access Controls
Access to information systems is granted based on:
- Job responsibilities and business need
- Least privilege principle
- Regular access reviews
- Multi-factor authentication for sensitive systems

5. Data Protection
All data must be protected through:
- Encryption of sensitive data at rest and in transit
- Regular backups with secure storage
- Data loss prevention measures
- Secure disposal of media and devices

6. Network Security
Network security measures include:
- Firewalls and intrusion detection systems
- Network segmentation
- Regular security monitoring
- Secure remote access protocols

7. Incident Response
Security incidents must be:
- Reported immediately to the IT Security team
- Documented with full details
- Investigated thoroughly
- Remediated promptly
- Lessons learned applied

8. Employee Responsibilities
All employees must:
- Use strong, unique passwords
- Keep software and systems updated
- Report suspicious activities
- Follow security procedures
- Complete security training

9. Vendor Management
Third-party vendors must:
- Meet security requirements
- Sign confidentiality agreements
- Undergo security assessments
- Comply with our security policies

10. Compliance
This policy ensures compliance with:
- GDPR and other privacy regulations
- Industry standards (ISO 27001, SOC 2)
- Internal audit requirements
- Legal and regulatory obligations

11. Policy Enforcement
Violations of this policy may result in:
- Additional training
- Access restrictions
- Disciplinary action
- Legal consequences

12. Review and Updates
This policy is reviewed annually and updated as needed to address emerging threats and regulatory changes.
"""
        
        # Sample Policy Document 4: Code of Conduct
        code_of_conduct = """Code of Conduct

1. Our Values
We are committed to:
- Integrity and ethical behavior
- Respect for all individuals
- Excellence in everything we do
- Innovation and continuous improvement
- Social responsibility

2. Professional Standards
All employees must:
- Act with honesty and integrity
- Treat others with respect and dignity
- Maintain confidentiality of sensitive information
- Avoid conflicts of interest
- Comply with all applicable laws and regulations

3. Workplace Behavior
We expect:
- Professional communication and conduct
- Collaboration and teamwork
- Constructive feedback and conflict resolution
- Respect for diversity and inclusion
- Zero tolerance for harassment or discrimination

4. Use of Company Resources
Company resources must be used:
- Primarily for business purposes
- In accordance with company policies
- With appropriate security measures
- Without personal gain or misuse

5. Confidentiality
Employees must:
- Protect confidential information
- Not disclose proprietary data
- Use information only for authorized purposes
- Report unauthorized access or disclosure

6. Conflicts of Interest
Employees must:
- Disclose potential conflicts of interest
- Avoid situations that could compromise judgment
- Not use position for personal gain
- Seek guidance when uncertain

7. Reporting Violations
Employees should:
- Report suspected violations promptly
- Use appropriate reporting channels
- Provide accurate information
- Cooperate with investigations

8. Non-Retaliation
The company prohibits retaliation against employees who:
- Report violations in good faith
- Participate in investigations
- Express concerns about compliance

9. Disciplinary Action
Violations may result in:
- Counseling and training
- Written warnings
- Suspension or termination
- Legal action when appropriate

10. Continuous Improvement
We are committed to:
- Regular policy reviews
- Employee feedback and input
- Training and education
- Updating policies as needed

11. Questions and Concerns
For questions about this code of conduct, contact:
- Human Resources: hr@company.com
- Ethics Hotline: 1-800-ETHICS
- Legal Department: legal@company.com

12. Acknowledgment
All employees must acknowledge receipt and understanding of this code of conduct annually.
"""
        
        # Create documents
        documents_data = [
            ("data_privacy_policy.txt", privacy_policy),
            ("remote_work_policy.txt", remote_work_policy),
            ("information_security_policy.txt", security_policy),
            ("code_of_conduct.txt", code_of_conduct)
        ]
        
        for filename, content in documents_data:
            file_path = output_dir / filename
            file_path.write_text(content)
            documents.append(file_path)
            print(f"Created: {filename}")
        
        return documents
    
    def load_sample_data(self, documents: List[Path], test_queries: List[str] = None) -> Dict[str, Any]:
        """Load sample data and test the system.
        
        Args:
            documents: List of document paths to upload
            test_queries: List of test queries to run
            
        Returns:
            Loading results summary
        """
        print("Loading Sample Data into Policy Pilot RAG System")
        print("=" * 60)
        
        # Check API health
        if not self.check_api_health():
            print("API is not healthy. Aborting data loading.")
            return {"success": False, "error": "API not healthy"}
        
        # Upload documents
        print(f"\nUploading {len(documents)} documents...")
        successful_uploads = 0
        
        for doc_path in documents:
            if doc_path.exists():
                filename = doc_path.name
                result = self.upload_document(str(doc_path), filename)
                if result:
                    successful_uploads += 1
            else:
                print(f"✗ Document not found: {doc_path}")
        
        print(f"\nUpload Summary: {successful_uploads}/{len(documents)} documents uploaded successfully")
        
        # Wait for processing to complete
        if successful_uploads > 0:
            print("\nWaiting for document processing to complete...")
            time.sleep(5)  # Give time for processing
        
        # Get system statistics
        print("\nSystem Statistics:")
        stats = self.get_system_statistics()
        
        # Test queries
        if test_queries:
            print(f"\nTesting {len(test_queries)} queries...")
            successful_queries = 0
            
            for query in test_queries:
                result = self.test_query(query)
                if result:
                    successful_queries += 1
                print()  # Add spacing between queries
            
            print(f"Query Test Summary: {successful_queries}/{len(test_queries)} queries successful")
        else:
            # Default test queries
            default_queries = [
                "What is the purpose of the data privacy policy?",
                "What are the requirements for remote work?",
                "How should security incidents be handled?",
                "What are the key values in the code of conduct?",
                "What are the data retention requirements?"
            ]
            
            print(f"\nTesting {len(default_queries)} default queries...")
            successful_queries = 0
            
            for query in default_queries:
                result = self.test_query(query)
                if result:
                    successful_queries += 1
                print()  # Add spacing between queries
            
            print(f"Query Test Summary: {successful_queries}/{len(default_queries)} queries successful")
        
        # Summary
        summary = {
            "success": successful_uploads > 0,
            "documents_uploaded": successful_uploads,
            "total_documents": len(documents),
            "queries_tested": len(test_queries) if test_queries else 5,
            "successful_queries": successful_queries if test_queries else successful_queries,
            "system_statistics": stats,
            "loaded_documents": self.loaded_documents
        }
        
        print("\n" + "=" * 60)
        print("SAMPLE DATA LOADING SUMMARY")
        print("=" * 60)
        print(f"Documents Uploaded: {successful_uploads}/{len(documents)}")
        print(f"Queries Tested: {summary['queries_tested']}")
        print(f"System Status: {'Ready' if summary['success'] else 'Issues Detected'}")
        
        return summary


def main():
    """Main function for loading sample data."""
    parser = argparse.ArgumentParser(description="Load sample policy documents for Policy Pilot RAG system")
    parser.add_argument("--base-url", default="http://localhost:8000", 
                       help="Base URL of the API server")
    parser.add_argument("--documents", nargs="+", 
                       help="Paths to documents to upload")
    parser.add_argument("--create-sample", action="store_true",
                       help="Create sample documents automatically")
    parser.add_argument("--output-dir", default="./sample_documents",
                       help="Directory to create sample documents in")
    parser.add_argument("--queries", nargs="+",
                       help="Custom test queries to run")
    parser.add_argument("--output", help="Output file for loading results (JSON)")
    
    args = parser.parse_args()
    
    # Create sample documents if requested
    documents = []
    if args.create_sample:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        loader = SampleDataLoader(base_url=args.base_url)
        documents = loader.create_sample_documents(output_dir)
        print(f"Created {len(documents)} sample documents in {output_dir}")
    elif args.documents:
        documents = [Path(doc) for doc in args.documents]
    else:
        print("No documents provided. Use --documents or --create-sample")
        return 1
    
    # Load sample data
    loader = SampleDataLoader(base_url=args.base_url)
    results = loader.load_sample_data(documents, args.queries)
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nLoading results saved to: {args.output}")
    
    # Return exit code based on results
    return 0 if results['success'] else 1


if __name__ == "__main__":
    sys.exit(main())
