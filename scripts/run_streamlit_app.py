#!/usr/bin/env python3
"""
Automated Streamlit App Launcher
Handles environment setup, dependency installation, and browser launch
for the Mexico LinkedIn Jobs Insights Streamlit dashboard.
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def run_command(cmd, description="Running command"):
    """Execute a shell command and return success status."""
    print(f"\n{'='*70}")
    print(f"{description}...")
    print(f"{'='*70}")
    print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            check=True,
            capture_output=False
        )
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError as e:
        print(f"✗ Command not found: {e}")
        return False


def check_path_exists(path, description=""):
    """Check if a path exists."""
    path_obj = Path(path)
    exists = path_obj.exists()
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {path_obj.absolute()}")
    return exists


def main():
    """Main workflow for launching Streamlit app."""
    print("\n" + "="*70)
    print("MEXICO LINKEDIN JOBS INSIGHTS - STREAMLIT APP LAUNCHER")
    print("="*70)
    print(f"\nCurrent directory: {Path.cwd()}")
    
    # Step 1: Verify workspace structure
    print("\n" + "="*70)
    print("Step 1: Verifying workspace structure...")
    print("="*70)
    
    repo_root = Path.cwd()
    pyproject = repo_root / "pyproject.toml"
    src_dir = repo_root / "src" / "mexico_linkedin_jobs_portfolio"
    app_file = src_dir / "interfaces" / "streamlit" / "app.py"
    curated_dir = repo_root / "artifacts" / "curated"
    reports_dir = repo_root / "artifacts" / "reports"
    
    print(f"Repository root: {repo_root}")
    check_path_exists(pyproject, "pyproject.toml")
    check_path_exists(src_dir, "Source directory")
    check_path_exists(app_file, "Streamlit app file")
    
    required_paths = [pyproject, src_dir, app_file]
    if not all(p.exists() for p in required_paths):
        print("\n✗ ERROR: Required project files not found!")
        print("Please ensure you're running from the repository root directory.")
        sys.exit(1)
    
    print("\n✓ Workspace structure verified")
    
    # Step 2: Check Python version
    print("\n" + "="*70)
    print("Step 2: Checking Python version...")
    print("="*70)
    
    version_info = sys.version_info
    version_string = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    print(f"Python version: {version_string}")
    
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 11):
        print(f"\n✗ ERROR: Python 3.11+ required, found {version_string}")
        sys.exit(1)
    
    print("✓ Python version is compatible")
    
    # Step 3: Install dependencies
    print("\n" + "="*70)
    print("Step 3: Installing app dependencies...")
    print("="*70)
    
    install_cmd = [sys.executable, "-m", "pip", "install", "-e", ".[app]"]
    if not run_command(install_cmd, "Installing dependencies with pip"):
        print("\n⚠ WARNING: Dependency installation may have issues")
        print("Continuing anyway... (may experience import errors)")
    
    # Step 4: Check data availability
    print("\n" + "="*70)
    print("Step 4: Checking data availability...")
    print("="*70)
    
    curated_exists = check_path_exists(curated_dir, "Curated data directory")
    reports_exists = check_path_exists(reports_dir, "Reports directory")
    
    if curated_exists:
        duckdb_file = curated_dir / "mx_jobs_insights.duckdb"
        if duckdb_file.exists():
            file_size = duckdb_file.stat().st_size / (1024 * 1024)
            print(f"  └─ Database file: {duckdb_file.name} ({file_size:.1f} MB)")
        else:
            parquet_dir = curated_dir / "parquet"
            if parquet_dir.exists():
                parquet_files = list(parquet_dir.glob("*.parquet"))
                print(f"  └─ Parquet format: {len(parquet_files)} files found")
    
    if reports_exists:
        report_count = sum(1 for _ in reports_dir.rglob("run_summary.json"))
        print(f"  └─ Available reports: {report_count} found")
    
    if not curated_exists and not reports_exists:
        print("\n⚠ WARNING: No data directories found in artifacts/")
        print("   The Streamlit app will start but may show empty data.")
        print("   To generate data, run: python -m mexico_linkedin_jobs_portfolio pipeline --curated-only")
    
    # Step 5: Launch Streamlit
    print("\n" + "="*70)
    print("Step 5: Launching Streamlit app...")
    print("="*70)
    
    streamlit_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_file),
        "--logger.level=error"
    ]
    
    print(f"Starting: streamlit run {app_file.relative_to(repo_root)}")
    print(f"\nStreamlit will be available at: http://localhost:8501")
    print("\nNote: The Streamlit process will continue running.")
    print("      Press Ctrl+C in the terminal to stop the server.\n")
    
    # Give browser launch a moment
    print("Opening browser in 3 seconds...")
    time.sleep(3)
    
    # Step 6: Open browser (in background thread)
    print("\n" + "="*70)
    print("Step 6: Opening browser...")
    print("="*70)
    
    try:
        webbrowser.open("http://localhost:8501")
        print("✓ Browser launch initiated")
    except Exception as e:
        print(f"⚠ Could not open browser automatically: {e}")
        print("   Please open http://localhost:8501 manually")
    
    # Step 7: Start Streamlit (blocking call)
    print("\n" + "="*70)
    print("STREAMLIT SERVER STARTING")
    print("="*70 + "\n")
    
    try:
        subprocess.run(streamlit_cmd, check=False)
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("Streamlit server stopped by user")
        print("="*70)
        sys.exit(0)


if __name__ == "__main__":
    main()
