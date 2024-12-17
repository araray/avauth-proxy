import os
import subprocess
import time

def wait_for_services():
    """Wait for services to be healthy before running tests."""
    print("[INFO] Waiting for services to be ready...")
    time.sleep(15)  # Can be improved with healthchecks.

def run_tests():
    """Run the tests with coverage in the test environment."""
    try:
        print("[INFO] Starting test environment...")
        subprocess.run(["docker-compose", "-f", "docker-compose_test.yaml", "up", "--build", "-d"], check=True)

        wait_for_services()

        print("[INFO] Running tests with coverage...")
        # Run tests with coverage
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose_test.yaml", "exec", "app", "pytest", "--cov=avauth_proxy", "--cov-report=term-missing"],
            check=False
        )
        return result.returncode
    finally:
        print("[INFO] Stopping and cleaning up test environment...")
        subprocess.run(["docker-compose", "-f", "docker-compose_test.yaml", "down"], check=True)

if __name__ == "__main__":
    exit_code = run_tests()
    if exit_code == 0:
        print("[SUCCESS] All tests passed!")
    else:
        print("[FAILURE] Some tests failed.")
    exit(exit_code)
