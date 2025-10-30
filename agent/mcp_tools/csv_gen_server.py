from mcp.server.fastmcp import FastMCP
import csv
import os
from datetime import datetime

mcp = FastMCP("CSV Generator")

@mcp.tool()
def generate_csv(filename: str, headers: list[str], rows: list[list]) -> str:
    """
    Generate a CSV file with the given filename, headers, and data rows.
    
    Args:
        filename: Name for the CSV file (without .csv extension)
        headers: List of column headers
        rows: List of rows, where each row is a list of values
    
    Returns:
        str: Path to the generated CSV file
    """
    # check if directory exists, if not create it
    output_dir = "./database/user-database"
    os.makedirs(output_dir, exist_ok=True)
    
    # Add timestamp to filename to avoid overwrites
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{filename}_{timestamp}.csv"
    filepath = os.path.join(output_dir, csv_filename)
    
    # Write CSV
    # Open file  handle it properly for CSV format, support international characters, and auto-close when done
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    
    return filepath

if __name__ == "__main__":
    mcp.run(transport="stdio")