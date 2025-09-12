#!/usr/bin/env python3
"""
Comprehensive test runner for Policy Pilot RAG backend.
Runs unit tests, integration tests, and performance benchmarks.
"""

import subprocess
import sys
import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional


class TestRunner:
    """Comprehensive test runner for Policy Pilot RAG backend."""
    
    def __init__(self, project_root: Path = None):
        """Initialize the test runner.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path(__file__).parent.parent
        self.test_results = {}
        
    def run_command(self, command: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
        """Run a command and return the result.
        
        Args:
            command: Command to run as a list
            cwd: Working directory for the command
            
        Returns:
            Command execution result
        """
        cwd = cwd or self.project_root
        
        try:
            print(f"Running: {' '.join(command)}")
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(command)
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out after 5 minutes',
                'command': ' '.join(command)
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'command': ' '.join(command)
            }
    
    def run_unit_tests(self, verbose: bool = False, coverage: bool = True) -> Dict[str, Any]:
        """Run unit tests.
        
        Args:
            verbose: Whether to run tests in verbose mode
            coverage: Whether to generate coverage report
            
        Returns:
            Unit test results
        """
        print("\n" + "=" * 60)
        print("RUNNING UNIT TESTS")
        print("=" * 60)
        
        command = ["python", "-m", "pytest", "tests/"]
        
        if verbose:
            command.append("-v")
        
        if coverage:
            command.extend([
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml"
            ])
        
        # Add markers for unit tests only
        command.extend(["-m", "unit"])
        
        result = self.run_command(command)
        
        self.test_results['unit_tests'] = result
        
        if result['success']:
            print("✓ Unit tests passed")
        else:
            print("✗ Unit tests failed")
            print(f"Error: {result['stderr']}")
        
        return result
    
    def run_integration_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run integration tests.
        
        Args:
            verbose: Whether to run tests in verbose mode
            
        Returns:
            Integration test results
        """
        print("\n" + "=" * 60)
        print("RUNNING INTEGRATION TESTS")
        print("=" * 60)
        
        command = ["python", "-m", "pytest", "tests/"]
        
        if verbose:
            command.append("-v")
        
        # Add markers for integration tests only
        command.extend(["-m", "integration"])
        
        result = self.run_command(command)
        
        self.test_results['integration_tests'] = result
        
        if result['success']:
            print("✓ Integration tests passed")
        else:
            print("✗ Integration tests failed")
            print(f"Error: {result['stderr']}")
        
        return result
    
    def run_api_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run API tests.
        
        Args:
            verbose: Whether to run tests in verbose mode
            
        Returns:
            API test results
        """
        print("\n" + "=" * 60)
        print("RUNNING API TESTS")
        print("=" * 60)
        
        command = ["python", "-m", "pytest", "tests/"]
        
        if verbose:
            command.append("-v")
        
        # Add markers for API tests only
        command.extend(["-m", "api"])
        
        result = self.run_command(command)
        
        self.test_results['api_tests'] = result
        
        if result['success']:
            print("✓ API tests passed")
        else:
            print("✗ API tests failed")
            print(f"Error: {result['stderr']}")
        
        return result
    
    def run_all_tests(self, verbose: bool = False, coverage: bool = True) -> Dict[str, Any]:
        """Run all tests.
        
        Args:
            verbose: Whether to run tests in verbose mode
            coverage: Whether to generate coverage report
            
        Returns:
            All test results
        """
        print("\n" + "=" * 60)
        print("RUNNING ALL TESTS")
        print("=" * 60)
        
        command = ["python", "-m", "pytest", "tests/"]
        
        if verbose:
            command.append("-v")
        
        if coverage:
            command.extend([
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml"
            ])
        
        result = self.run_command(command)
        
        self.test_results['all_tests'] = result
        
        if result['success']:
            print("✓ All tests passed")
        else:
            print("✗ Some tests failed")
            print(f"Error: {result['stderr']}")
        
        return result
    
    def run_linting(self) -> Dict[str, Any]:
        """Run code linting.
        
        Returns:
            Linting results
        """
        print("\n" + "=" * 60)
        print("RUNNING CODE LINTING")
        print("=" * 60)
        
        # Run flake8
        flake8_result = self.run_command(["python", "-m", "flake8", "src/", "tests/"])
        
        # Run black check
        black_result = self.run_command(["python", "-m", "black", "--check", "src/", "tests/"])
        
        # Run isort check
        isort_result = self.run_command(["python", "-m", "isort", "--check-only", "src/", "tests/"])
        
        # Run mypy
        mypy_result = self.run_command(["python", "-m", "mypy", "src/"])
        
        linting_results = {
            'flake8': flake8_result,
            'black': black_result,
            'isort': isort_result,
            'mypy': mypy_result
        }
        
        self.test_results['linting'] = linting_results
        
        # Check if all linting passed
        all_passed = all(result['success'] for result in linting_results.values())
        
        if all_passed:
            print("✓ All linting checks passed")
        else:
            print("✗ Some linting checks failed")
            for tool, result in linting_results.items():
                if not result['success']:
                    print(f"  {tool}: {result['stderr']}")
        
        return linting_results
    
    def run_integration_script(self, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """Run the integration testing script.
        
        Args:
            base_url: Base URL of the API server
            
        Returns:
            Integration script results
        """
        print("\n" + "=" * 60)
        print("RUNNING INTEGRATION SCRIPT")
        print("=" * 60)
        
        command = [
            "python", "scripts/test_integration.py",
            "--base-url", base_url,
            "--create-test-docs",
            "--performance-queries", "5"
        ]
        
        result = self.run_command(command)
        
        self.test_results['integration_script'] = result
        
        if result['success']:
            print("✓ Integration script passed")
        else:
            print("✗ Integration script failed")
            print(f"Error: {result['stderr']}")
        
        return result
    
    def run_sample_data_loading(self, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """Run the sample data loading script.
        
        Args:
            base_url: Base URL of the API server
            
        Returns:
            Sample data loading results
        """
        print("\n" + "=" * 60)
        print("RUNNING SAMPLE DATA LOADING")
        print("=" * 60)
        
        command = [
            "python", "scripts/load_sample_data.py",
            "--base-url", base_url,
            "--create-sample"
        ]
        
        result = self.run_command(command)
        
        self.test_results['sample_data_loading'] = result
        
        if result['success']:
            print("✓ Sample data loading completed")
        else:
            print("✗ Sample data loading failed")
            print(f"Error: {result['stderr']}")
        
        return result
    
    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate a comprehensive test report.
        
        Args:
            output_file: Optional file to save the report to
            
        Returns:
            Test report
        """
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if isinstance(result, dict) and result.get('success', False))
        
        # Calculate overall success rate
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        report = {
            'timestamp': time.time(),
            'total_test_suites': total_tests,
            'passed_test_suites': passed_tests,
            'failed_test_suites': total_tests - passed_tests,
            'success_rate': success_rate,
            'test_results': self.test_results
        }
        
        print("\n" + "=" * 60)
        print("TEST REPORT SUMMARY")
        print("=" * 60)
        print(f"Total Test Suites: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1%}")
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\nReport saved to: {output_file}")
        
        return report
    
    def run_full_test_suite(self, 
                          verbose: bool = False, 
                          coverage: bool = True,
                          linting: bool = True,
                          integration: bool = True,
                          sample_data: bool = True,
                          base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """Run the complete test suite.
        
        Args:
            verbose: Whether to run tests in verbose mode
            coverage: Whether to generate coverage report
            linting: Whether to run linting checks
            integration: Whether to run integration tests
            sample_data: Whether to test sample data loading
            base_url: Base URL of the API server
            
        Returns:
            Complete test results
        """
        print("Policy Pilot RAG Backend - Comprehensive Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run unit tests
        self.run_unit_tests(verbose=verbose, coverage=coverage)
        
        # Run integration tests
        if integration:
            self.run_integration_tests(verbose=verbose)
        
        # Run API tests
        self.run_api_tests(verbose=verbose)
        
        # Run linting
        if linting:
            self.run_linting()
        
        # Run integration script (requires running server)
        if integration:
            print("\nNote: Integration script requires a running server.")
            print("Start the server with: python run_server.py")
            print("Then run: python scripts/test_integration.py")
        
        # Run sample data loading (requires running server)
        if sample_data:
            print("\nNote: Sample data loading requires a running server.")
            print("Start the server with: python run_server.py")
            print("Then run: python scripts/load_sample_data.py")
        
        total_time = time.time() - start_time
        
        print(f"\nTotal test execution time: {total_time:.2f} seconds")
        
        return self.generate_report()


def main():
    """Main function for running tests."""
    parser = argparse.ArgumentParser(description="Policy Pilot RAG Backend Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--api", action="store_true", help="Run API tests only")
    parser.add_argument("--linting", action="store_true", help="Run linting checks only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--no-linting", action="store_true", help="Skip linting checks")
    parser.add_argument("--no-integration", action="store_true", help="Skip integration tests")
    parser.add_argument("--no-sample-data", action="store_true", help="Skip sample data loading")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API server base URL")
    parser.add_argument("--output", help="Output file for test report (JSON)")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Determine what to run
    if args.unit:
        result = runner.run_unit_tests(verbose=args.verbose, coverage=not args.no_coverage)
    elif args.integration:
        result = runner.run_integration_tests(verbose=args.verbose)
    elif args.api:
        result = runner.run_api_tests(verbose=args.verbose)
    elif args.linting:
        result = runner.run_linting()
    elif args.all or not any([args.unit, args.integration, args.api, args.linting]):
        result = runner.run_full_test_suite(
            verbose=args.verbose,
            coverage=not args.no_coverage,
            linting=not args.no_linting,
            integration=not args.no_integration,
            sample_data=not args.no_sample_data,
            base_url=args.base_url
        )
    else:
        print("Please specify what tests to run. Use --help for options.")
        return 1
    
    # Generate report if output file specified
    if args.output:
        runner.generate_report(args.output)
    
    # Return exit code based on results
    if isinstance(result, dict):
        return 0 if result.get('success', False) else 1
    else:
        # For full test suite, check overall success rate
        return 0 if runner.test_results.get('success_rate', 0) > 0.8 else 1


if __name__ == "__main__":
    sys.exit(main())
