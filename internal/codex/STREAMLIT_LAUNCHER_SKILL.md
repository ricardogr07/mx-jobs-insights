# Streamlit Launcher Skill

**PURPOSE:** Automatically launch the Mexico LinkedIn Jobs Insights Streamlit app with zero manual intervention.

**USE WHEN:** You want to spin up the local Streamlit dashboard without typing commands or managing setup steps.

**INVOKES:** Python automation script that handles dependencies, validation, and browser launch.

## What This Skill Does

Executes a fully automated workflow that:

1. ✓ Verifies workspace structure and required files
2. ✓ Validates Python 3.11+ availability
3. ✓ Installs Streamlit dependencies (`pip install -e ".[app]"`)
4. ✓ Checks for curated data in `artifacts/curated/`
5. ✓ Checks for report artifacts in `artifacts/reports/`
6. ✓ Launches Streamlit server on `http://localhost:8501`
7. ✓ Opens browser automatically to dashboard

**Total runtime:** 30-60 seconds (mostly pip dependency check)

## How Agents Use This Skill

**Example agent request:**
```
"Run the Streamlit app for me and open it in the browser"
```

**Agent actions:**
1. Recognizes Streamlit launcher skill is needed
2. Runs: `python scripts/run_streamlit_app.py`
3. Script executes all 7 steps automatically
4. Browser opens to dashboard
5. Streamlit server continues running in background

## Manual Usage

If running manually from terminal:

```bash
cd /path/to/mx-jobs-insights
python scripts/run_streamlit_app.py
```

Expected output:
```
======================================================================
MEXICO LINKEDIN JOBS INSIGHTS - STREAMLIT APP LAUNCHER
======================================================================

Current directory: C:\git\mx-jobs-insights

======================================================================
Step 1: Verifying workspace structure...
======================================================================
✓ Repository root verification passed
✓ pyproject.toml found
✓ Streamlit app file found
✓ Workspace structure verified

...

======================================================================
Step 5: Launching Streamlit app...
======================================================================
✓ Streamlit process started
✓ Browser opened to http://localhost:8501

Opening http://localhost:8501 in your browser...

======================================================================
STREAMLIT SERVER RUNNING
======================================================================

You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
```

## Key Features

### Automated Data Detection
- Checks for existing curated data in `artifacts/curated/`
- Reports count if `artifacts/reports/` directory exists
- Starts app immediately if data is present
- Shows warning if no data found (but app still launches)

### Dependency Management
- Installs only required packages (`streamlit`, `duckdb`, etc.)
- Uses `[app]` extras group from `pyproject.toml`
- No API keys, tokens, or secrets needed
- Continues on warning (doesn't fail on minor issues)

### Error Handling
- Validates Python version (3.11+ required)
- Checks all required repository files exist
- Confirms workspace structure before installing
- Provides clear error messages and remediation steps

### Browser Launch
- Automatically opens `http://localhost:8501` after 3 seconds
- Works on Windows, macOS, and Linux
- Falls back to manual URL if browser launch fails
- Never blocks on browser operation

## Troubleshooting

### Script Fails to Start
**Issue:** `ModuleNotFoundError: No module named 'startfile'` or similar

**Solution:** Ensure you're in the repository root directory
```bash
cd /path/to/mx-jobs-insights
python scripts/run_streamlit_app.py
```

### Dependencies Won't Install
**Issue:** Pip installation fails with version conflicts

**Solution:** Upgrade pip first
```bash
python -m pip install --upgrade pip
python scripts/run_streamlit_app.py
```

### Port 8501 Already in Use
**Issue:** "Address already in use" error

**Solution:** Kill existing Streamlit process
```bash
# Find process on port 8501
netstat -ano | findstr :8501

# Kill it (replace PID with actual process ID)
taskkill /PID <PID> /F
```

Or run script with custom port (requires manual edit):
Edit [scripts/run_streamlit_app.py](../../scripts/run_streamlit_app.py) line 93, change:
```python
"--server.port=8502"  # Use 8502 instead
```

### Browser Doesn't Open
**Issue:** Browser doesn't launch automatically

**Solution:** Script will print the URL. Open manually:
- Copy `http://localhost:8501` from terminal
- Paste into browser address bar

Or modify script to add debug output (optional):
Edit line 115 in [scripts/run_streamlit_app.py](../../scripts/run_streamlit_app.py):
```python
webbrowser.open("http://localhost:8501")
print(f"System default browser = {webbrowser.get()}")
```

### No Data Showing in App
**Issue:** App loads but shows "No reports found"

**Solution:** Generate data first
```bash
python -m mexico_linkedin_jobs_portfolio pipeline --curated-only
python scripts/run_streamlit_app.py
```

## Implementation Details

**Script location:** [scripts/run_streamlit_app.py](../../scripts/run_streamlit_app.py)

**Key steps in source:**
1. **Lines 38-52:** Workspace verification
2. **Lines 54-64:** Python version check
3. **Lines 66-77:** Dependency installation
4. **Lines 79-102:** Data availability check
5. **Lines 104-123:** Streamlit launch
6. **Lines 125-132:** Browser opening
7. **Lines 135-142:** Server blocking call

**Dependencies:**
- `subprocess` - Command execution (stdlib)
- `webbrowser` - Browser launch (stdlib)
- `pathlib` - Path handling (stdlib)
- `streamlit>=1.32.0` - Installed by `pip install -e ".[app]"`
- `duckdb>=1.1.3` - Installed by `pip install -e ".[app]"`

## Agent Integration Example

### For Agent Instructions (`.instructions.md`)

Add this to your agent customization file:

```markdown
## When to Run Streamlit

If user asks to:
- "run the streamlit app"
- "launch the dashboard"
- "start streamlit locally"
- "open the visualization app"

Invoke the Streamlit Launcher Skill by running:
python scripts/run_streamlit_app.py

The script handles all setup automatically and opens the browser.
```

### For Prompt Context (`.prompt.md`)

```markdown
You have access to the Streamlit Launcher Skill for automating app startup.

When users ask to run/launch/start the Streamlit dashboard:
1. Run: python scripts/run_streamlit_app.py
2. Script handles setup, installation, data checks, and browser launch
3. Report back when Streamlit is running at http://localhost:8501
```

## Related Documentation

- **Streamlit Workflow Guide:** [STREAMLIT_LOCAL_WORKFLOW.md](../../docs/codex/STREAMLIT_LOCAL_WORKFLOW.md)
- **App Source Code:** [interfaces/streamlit/app.py](../../src/mexico_linkedin_jobs_portfolio/interfaces/streamlit/app.py)
- **Project Setup:** [pyproject.toml](../../pyproject.toml)
- **Streamlit Docs:** https://docs.streamlit.io/

## Next Steps

1. **For Agents:** Reference this skill in agent `.instructions.md` or `.prompt.md`
2. **For Teams:** Move [scripts/run_streamlit_app.py](../../scripts/run_streamlit_app.py) to shared tools location if desired
3. **For CI/CD:** Use script in GitHub Actions workflows to validate app startup

---

**Skill Author:** Auto-generated for mx-jobs-insights  
**Last Updated:** 2026-03-25  
**Compatibility:** Python 3.11+, Cross-platform (Windows/macOS/Linux)
