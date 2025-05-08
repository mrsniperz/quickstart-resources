# US Housing Prices MCP Application

This is a simple Model Context Protocol (MCP) application that provides simulated housing price data for major US cities.

## Features

The application provides the following MCP tools:

1. `list_cities` - Lists all available cities in the database
2. `get_average_price` - Gets the average housing price for a specified city
3. `get_price_range` - Gets the price range of housing in a specified city  
4. `get_price_by_neighborhood` - Gets housing prices for specific neighborhoods

## Installation

1. Make sure you have Python 3.10+ installed
2. Install required packages:

```bash
pip install mcp httpx rich
```

## Running the Server

To run the MCP server:

```bash
python housing_prices.py
```

The server will start and listen for incoming MCP requests via standard input/output (STDIO).

## Testing with the Example Client

A sample client is provided to test the functionality:

```bash
python housing_client_example.py
```

This will demonstrate the various tools provided by the MCP server.

## Using with Claude for Desktop

To use this with Claude for Desktop:

1. Make sure you have Claude for Desktop installed (latest version)
2. Open your Claude for Desktop configuration file:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - MacOS/Linux: `~/Library/Application Support/Claude/claude_desktop_config.json`

3. Add the housing server to your config (create the file if it doesn't exist):

```json
{
    "mcpServers": {
        "housing": {
            "command": "python",
            "args": [
                "C:\\ABSOLUTE\\PATH\\TO\\housing_prices.py"
            ]
        }
    }
}
```

Replace `C:\\ABSOLUTE\\PATH\\TO\\` with the actual path to the housing_prices.py file.

4. Restart Claude for Desktop
5. You should now see the available housing tools when clicking on the tools icon (hammer)

## Example Commands

Here are some example prompts you can use in Claude for Desktop:

- "What's the average housing price in New York?"
- "What are the housing prices in different neighborhoods of Los Angeles?"
- "What's the price range for homes in Chicago?"
- "List all the cities you have housing data for."

## Data Disclaimer

All housing data in this application is simulated and should not be used for actual real estate decisions. The prices are generated based on approximations and do not reflect actual market conditions. 