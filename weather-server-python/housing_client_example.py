import asyncio
import sys
from mcp.client.mcpclient import McpClient
from rich.console import Console
from rich.panel import Panel

console = Console()

async def main():
    """Simple test client for the housing price MCP server."""
    # Connect to the housing MCP server
    async with McpClient() as client:
        console.print(Panel("[bold blue]Housing Price MCP Client Demo[/bold blue]", 
                           subtitle="A demonstration of the Housing Price MCP Server"))
        
        # First, list available cities
        console.print("\n[bold]Available Cities:[/bold]")
        response = await client.invoke_tool("housing", "list_cities", [])
        console.print(response)
        
        # Get average price for New York
        console.print("\n[bold]Average Housing Price in New York:[/bold]")
        response = await client.invoke_tool("housing", "get_average_price", ["New York"])
        console.print(Panel(response, title="New York Housing Data"))
        
        # Get average price for San Francisco
        console.print("\n[bold]Average Housing Price in San Francisco:[/bold]")
        response = await client.invoke_tool("housing", "get_average_price", ["San Francisco"])
        console.print(Panel(response, title="San Francisco Housing Data"))
        
        # Get price range for Chicago
        console.print("\n[bold]Housing Price Range in Chicago:[/bold]")
        response = await client.invoke_tool("housing", "get_price_range", ["Chicago"])
        console.print(Panel(response, title="Chicago Price Range"))
        
        # Get neighborhood pricing in Los Angeles
        console.print("\n[bold]Neighborhood Pricing in Los Angeles:[/bold]")
        response = await client.invoke_tool("housing", "get_price_by_neighborhood", ["Los Angeles", "Beverly Hills"])
        console.print(Panel(response, title="Beverly Hills Neighborhood"))
        
        # Try with invalid city
        console.print("\n[bold]Trying an Invalid City:[/bold]")
        response = await client.invoke_tool("housing", "get_average_price", ["Miami"])
        console.print(Panel(response, title="Invalid City Request"))

if __name__ == "__main__":
    asyncio.run(main()) 