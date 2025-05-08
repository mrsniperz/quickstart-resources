from typing import Any, List, Optional
import random
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("housing")

# Mock housing price data for major US cities
CITIES = {
    "New York": {
        "avg_price": 1200000,
        "price_range": (800000, 2000000),
        "trend": 0.05,  # 5% annual increase
        "neighborhoods": ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
    },
    "Los Angeles": {
        "avg_price": 950000,
        "price_range": (650000, 1500000),
        "trend": 0.04,  # 4% annual increase
        "neighborhoods": ["Hollywood", "Beverly Hills", "Santa Monica", "Downtown", "Venice"]
    },
    "Chicago": {
        "avg_price": 450000,
        "price_range": (300000, 800000),
        "trend": 0.03,  # 3% annual increase
        "neighborhoods": ["Loop", "Lincoln Park", "Wicker Park", "River North", "Hyde Park"]
    },
    "Houston": {
        "avg_price": 350000,
        "price_range": (250000, 650000),
        "trend": 0.07,  # 7% annual increase
        "neighborhoods": ["Downtown", "Montrose", "The Heights", "River Oaks", "Midtown"]
    },
    "Phoenix": {
        "avg_price": 420000,
        "price_range": (280000, 700000),
        "trend": 0.08,  # 8% annual increase
        "neighborhoods": ["Downtown", "Arcadia", "Desert Ridge", "Biltmore", "Ahwatukee"]
    },
    "Philadelphia": {
        "avg_price": 380000,
        "price_range": (250000, 650000),
        "trend": 0.04,  # 4% annual increase
        "neighborhoods": ["Center City", "Fishtown", "University City", "Rittenhouse", "Old City"]
    },
    "San Antonio": {
        "avg_price": 320000,
        "price_range": (220000, 550000),
        "trend": 0.06,  # 6% annual increase
        "neighborhoods": ["Downtown", "Alamo Heights", "King William", "Stone Oak", "Pearl District"]
    },
    "San Diego": {
        "avg_price": 850000,
        "price_range": (600000, 1400000),
        "trend": 0.05,  # 5% annual increase
        "neighborhoods": ["La Jolla", "Gaslamp Quarter", "Pacific Beach", "North Park", "Coronado"]
    },
    "Dallas": {
        "avg_price": 410000,
        "price_range": (280000, 700000),
        "trend": 0.07,  # 7% annual increase
        "neighborhoods": ["Downtown", "Uptown", "Bishop Arts", "Deep Ellum", "Highland Park"]
    },
    "San Francisco": {
        "avg_price": 1500000,
        "price_range": (900000, 2500000),
        "trend": 0.03,  # 3% annual increase
        "neighborhoods": ["SOMA", "Mission District", "North Beach", "Pacific Heights", "Nob Hill"]
    }
}

def get_simulated_price(city: str, neighborhood: Optional[str] = None) -> int:
    """Generate a simulated housing price for a city or neighborhood."""
    if city not in CITIES:
        return 0
    
    city_data = CITIES[city]
    base_price = city_data["avg_price"]
    
    if neighborhood:
        if neighborhood in city_data["neighborhoods"]:
            # Add variation based on neighborhood
            neighborhood_index = city_data["neighborhoods"].index(neighborhood)
            # More expensive neighborhoods are earlier in the list
            modifier = 1.0 - (neighborhood_index * 0.1)
            base_price = int(base_price * modifier)
    
    # Add some randomness to the price
    variation = random.uniform(-0.1, 0.1)  # ±10% variation
    price = int(base_price * (1 + variation))
    
    return price

@mcp.tool()
async def get_average_price(city: str) -> str:
    """Get the average housing price for a major US city.

    Args:
        city: Name of the US city (e.g., New York, Los Angeles)
    """
    if city not in CITIES:
        return f"Sorry, we don't have housing data for {city}. Available cities include: {', '.join(CITIES.keys())}"
    
    price = get_simulated_price(city)
    trend = CITIES[city]["trend"] * 100
    trend_direction = "increase" if trend > 0 else "decrease"
    
    return f"""
City: {city}
Average Housing Price: ${price:,}
Annual Price Trend: {trend:.1f}% {trend_direction}
"""

@mcp.tool()
async def get_price_by_neighborhood(city: str, neighborhood: str) -> str:
    """Get the average housing price for a specific neighborhood in a US city.

    Args:
        city: Name of the US city (e.g., New York, Los Angeles)
        neighborhood: Name of the neighborhood in the city
    """
    if city not in CITIES:
        return f"Sorry, we don't have housing data for {city}. Available cities include: {', '.join(CITIES.keys())}"
    
    if neighborhood not in CITIES[city]["neighborhoods"]:
        available_neighborhoods = ", ".join(CITIES[city]["neighborhoods"])
        return f"Sorry, we don't have data for {neighborhood} in {city}. Available neighborhoods include: {available_neighborhoods}"
    
    price = get_simulated_price(city, neighborhood)
    city_avg_price = CITIES[city]["avg_price"]
    
    comparison = (price / city_avg_price - 1) * 100
    comparison_text = f"{abs(comparison):.1f}% {'above' if comparison > 0 else 'below'} city average"
    
    return f"""
City: {city}
Neighborhood: {neighborhood}
Average Housing Price: ${price:,}
Comparison: {comparison_text}
"""

@mcp.tool()
async def list_cities() -> str:
    """List all available cities in the housing price database."""
    city_list = list(CITIES.keys())
    return "\n".join([f"- {city}" for city in city_list])

@mcp.tool()
async def get_price_range(city: str) -> str:
    """Get the housing price range for a major US city.

    Args:
        city: Name of the US city (e.g., New York, Los Angeles)
    """
    if city not in CITIES:
        return f"Sorry, we don't have housing data for {city}. Available cities include: {', '.join(CITIES.keys())}"
    
    min_price, max_price = CITIES[city]["price_range"]
    avg_price = CITIES[city]["avg_price"]
    
    return f"""
City: {city}
Average Housing Price: ${avg_price:,}
Price Range: ${min_price:,} - ${max_price:,}
"""

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 