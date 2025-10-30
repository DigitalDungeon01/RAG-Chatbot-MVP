from langchain_mcp_adapters.client import MultiServerMCPClient
from config import Settings
import os



# Global MCP client
mcp_client = None
_tools_cache = None

async def initialize_mcp():
    """Initialize MCP memory client"""
    
    global mcp_client
    
    if mcp_client is not None:
        return
    
    os.makedirs(Settings.CSV_GEN_OUTPUT_DIR, exist_ok=True) # directory for csv files
    
    # check csv server exists
    csv_server_path = "agent/mcp_tools/csv_gen_server.py"
    if not os.path.exists(csv_server_path):
        print(f"Warning: CSV server not found at {csv_server_path}")
        print("CSV generation will not be available")
        csv_server_path = None
    
    # Create MCP client
    mcp_client = MultiServerMCPClient({
        # "memory": {
        #     "command": "npx",
        #     "args": ["-y", "@modelcontextprotocol/server-memory"],
        #     "env": {"MEMORY_FILE_PATH": "./database/user-database/memory.jsonl"},
        #     "transport": "stdio"
        # }
        "tavily-remote-mcp": {
            "command": "npx",
            "args": ["-y", "mcp-remote", f"https://mcp.tavily.com/mcp/?tavilyApiKey={Settings.TAVILY_API_KEY}"],
            "env": {},
            "transport": "stdio"
        },
        "csv-gen": {
            "command": "uv",
            "args": ["run", f"{csv_server_path}"],
            "env": {},
            "transport": "stdio"
        },
        "chart-generator": {
            "command": "uv",
            "args": ["run", "agent/mcp_tools/chart_server.py"],
            "env": {},
            "transport": "stdio"
        },
    })
    print("MCP client initialized")



async def get_tools():
    """Get all tools from MCP"""
    if mcp_client is None:
        print("MCP client not initialized")
        return [] # return empty list if tools loading failed to avoid errors
    
    try:
        tools = await mcp_client.get_tools()
        print(f" {len(tools)} tools loaded")
        return tools
    except Exception as e:
        print(f"Tool loading failed: {e}")
        print("Available tools will be limited")
        return [] # return empty list if tools loading failed to avoid errors
    
    