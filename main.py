"""
PharmaTrace Nexus — Unified Application Entrypoint.
Delegates to the enterprise CLI interface.
"""

import sys
from pharmatrace.cli.main import main

if __name__ == "__main__":
    main()
