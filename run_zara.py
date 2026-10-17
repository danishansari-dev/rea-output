"""
Startup script for Zara Voice AI Platform.
Why this file exists:
Provides a clean, single-command entry point to run Zara's web UI and API server.
"""

import uvicorn

def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """
    Launches the Zara Voice AI Platform server and web interface.
    Why this code exists:
    Provides a standardized programmatic and CLI entrypoint to initialize Uvicorn and bind the FastAPI application.

    Tricky logic:
    Binds host to 0.0.0.0 for containerized and local network access while defaulting reload to True for development agility.

    TODO: Support SSL/TLS termination parameters for production deployments.

    @danishansari-dev host - Host IP string to bind to
    @danishansari-dev port - TCP port number
    @danishansari-dev reload - Boolean indicating whether to watch files for changes
    @returns None
    """
    print("=" * 60)
    print("  Starting Zara Voice AI Platform")
    print(f"  Web UI & Interactive Companion: http://localhost:{port}")
    print(f"  API Docs & OpenAPI Spec:        http://localhost:{port}/docs")
    print("=" * 60)
    uvicorn.run("zara.server:app", host=host, port=port, reload=reload)

if __name__ == "__main__":
    start_server()
