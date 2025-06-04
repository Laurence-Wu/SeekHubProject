import os
import subprocess
import sys

current_dir = os.path.dirname(__file__)
script_path = os.path.join(current_dir, 'unprocessesd_json_generator.py')

# Validate script existence
if not os.path.exists(script_path):
    print(f"Script not found: {script_path}")
    sys.exit(1)

# Configure environment to prioritize current directory
env = os.environ.copy()
env["PYTHONPATH"] = current_dir

# Execute with diagnostics
result = subprocess.run(
    [sys.executable, script_path],
    capture_output=True,
    text=True,
    timeout=300,
    cwd=current_dir,
    env=env
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)