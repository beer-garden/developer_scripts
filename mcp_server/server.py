# server.py
import uvicorn
from fastmcp import FastMCP
from brewtils import EasyClient
from brewtils.models import System
from brewtils.schemas import SystemSchema

# Initialize FastMCP 
mcp = FastMCP(name="MCP_Beergarden")

bg_connection_args = {"host":"beer-garden", "ssl_enabled":False}

@mcp.tool()
def find_systems() -> list[System]:
    """Return the catalog of available systems as serialized dictionaries."""
    client = EasyClient(**bg_connection_args)
    systems = client.find_systems()
    try:   
        return [SystemSchema().dump(system) for system in systems]
    except ImportError:
        return [vars(system) for system in systems]

@mcp.tool()
def calculate_area(width: int, height: int) -> int:
    """Calculate the area of a rectangle."""
    return width * height

# Create the ASGI application app for production servers
app = mcp.http_app( stateless_http=True)

if __name__ == "__main__":
    # Fallback for local python execution: transport="http" invokes Streamable HTTP
    # IMPORTANT: Must bind to 0.0.0.0 inside Docker
    uvicorn.run("server:app", host="0.0.0.0", port=8000, log_level="info")