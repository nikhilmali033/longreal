import subprocess
import sys
import os
import time
from datetime import datetime

class PiCameraTester:
    def __init__(self):
        self.test_dir = "camera_test_results"
        self.ensure_test_directory()
        self.log_file = os.path.join(self.test_dir, "camera_test.log")
        
    def ensure_test_directory(self):
        """Create test directory if it doesn't exist"""
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
            
    def log(self, message):
        """Log message to both console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a') as f:
            f.write(log_message + '\n')
            
    def run_command(self, cmd, timeout=10):
        """Run a command and capture output"""
        try:
            self.log(f"Running command: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return {
                    'success': process.returncode == 0,
                    'stdout': stdout,
                    'stderr': stderr,
                    'returncode': process.returncode
                }
            except subprocess.TimeoutExpired:
                process.kill()
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': 'Command timed out',
                    'returncode': -1
                }
                
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
            
    def test_camera_preview(self):
        """Test camera preview with various configurations"""
        self.log("\n=== Testing Camera Preview ===")
        
        # Test 1: Basic libcamera-hello with Qt
        self.log("\nTest 1: Basic libcamera-hello with Qt")
        result = self.run_command([
            "libcamera-hello",
            "--qt",
            "--timeout", "2000"
        ])
        self.log(f"Result: {'Success' if result['success'] else 'Failed'}")
        if result['stderr']:
            self.log(f"Errors: {result['stderr']}")
            
        # Test 2: Preview with specific resolution
        self.log("\nTest 2: Preview with specific resolution")
        result = self.run_command([
            "libcamera-hello",
            "--qt",
            "--width", "1920",
            "--height", "1080",
            "--timeout", "2000"
        ])
        self.log(f"Result: {'Success' if result['success'] else 'Failed'}")
        if result['stderr']:
            self.log(f"Errors: {result['stderr']}")
            
    def test_image_capture(self):
        """Test image capture functionality"""
        self.log("\n=== Testing Image Capture ===")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_image = os.path.join(self.test_dir, f"test_{timestamp}.jpg")
        
        # Test 1: Basic capture
        self.log("\nTest 1: Basic image capture")
        result = self.run_command([
            "libcamera-jpeg",
            "--qt",
            "-o", test_image,
            "--width", "2304",
            "--height", "1296"
        ])
        self.log(f"Result: {'Success' if result['success'] else 'Failed'}")
        if result['stderr']:
            self.log(f"Errors: {result['stderr']}")
        
        if os.path.exists(test_image):
            self.log(f"Image captured successfully: {test_image}")
            # Get file size
            size = os.path.getsize(test_image)
            self.log(f"Image size: {size/1024:.2f} KB")
        else:
            self.log("Failed to capture image")
            
    def check_system_configuration(self):
        """Check system configuration and requirements"""
        self.log("\n=== Checking System Configuration ===")
        
        # Check libcamera installation
        result = self.run_command(["which", "libcamera-hello"])
        self.log(f"libcamera-hello installed: {'Yes' if result['success'] else 'No'}")
        
        # Check Qt installation
        result = self.run_command(["pkg-config", "--exists", "--print-errors", "Qt5Core"])
        self.log(f"Qt5 installed: {'Yes' if result['success'] else 'No'}")
        
        # Check video group membership
        result = self.run_command(["groups"])
        if result['success']:
            groups = result['stdout'].strip().split()
            self.log(f"User in video group: {'video' in groups}")
            
        # Check camera interface
        result = self.run_command(["vcgencmd", "get_camera"])
        if result['success']:
            self.log(f"Camera interface: {result['stdout'].strip()}")
            
    def run_all_tests(self):
        """Run all camera tests"""
        self.log("Starting camera system tests...")
        
        try:
            # System configuration
            self.check_system_configuration()
            
            # Camera preview tests
            self.test_camera_preview()
            
            # Image capture tests
            self.test_image_capture()
            
            self.log("\n=== Tests Complete ===")
            self.log(f"Log file location: {self.log_file}")
            
        except Exception as e:
            self.log(f"\nError during tests: {str(e)}")
            raise

def main():
    tester = PiCameraTester()
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        print(f"\nError running tests: {e}")

if __name__ == "__main__":
    main()