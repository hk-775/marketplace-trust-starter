"""Command-line entry point for the local demo service."""

from __future__ import annotations

import argparse
import os

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Marketplace Trust Starter")
    parser.add_argument(
        "--host",
        default=os.getenv("MTS_HOST", "127.0.0.1"),
        help="Interface to bind (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        default=int(os.getenv("MTS_PORT", "8101")),
        type=int,
        help="Port to bind (default: 8101)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable development auto-reload",
    )
    args = parser.parse_args()
    uvicorn.run(
        "marketplace_trust_starter.app:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
