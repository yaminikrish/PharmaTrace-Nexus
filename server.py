"""
Production-grade Local HTTP & REST API Server for PharmaTrace Nexus.
Entrypoint delegating to enterprise module pharmatrace.api.server.
"""

import sys
from pharmatrace.api.server import start_server

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    start_server(port=port)
