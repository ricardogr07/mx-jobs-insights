"""Allow package to be executed as python -m mexico_linkedin_jobs_portfolio."""

import sys

from mexico_linkedin_jobs_portfolio.interfaces.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
