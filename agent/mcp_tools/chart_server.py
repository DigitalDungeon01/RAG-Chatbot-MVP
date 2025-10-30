from mcp.server.fastmcp import FastMCP
from typing import Dict, List, Any
import json
import urllib.parse

mcp = FastMCP("ChartGenerator")

@mcp.tool()
def create_chart(chart_type: str, labels: List[str], datasets: List[Dict[str, Any]], title: str = "Chart") -> str:
    """Generate Chart.js URL"""
    
    clean_datasets = []
    for ds in datasets:
        clean_datasets.append({
            "label": ds.get("label", "Data"),
            "data": ds.get("data", [])
        })
    
    config = {
        "type": chart_type,
        "data": {"labels": labels, "datasets": clean_datasets},
        "options": {"title": {"display": True, "text": title}}
    }
    
    config_str = json.dumps(config)
    encoded = urllib.parse.quote(config_str)
    url = f"https://quickchart.io/chart?c={encoded}"
    
    return url

if __name__ == "__main__":
    mcp.run(transport="stdio")