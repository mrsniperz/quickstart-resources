import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_weather_client():
    """运行天气服务客户端示例"""
    # 创建服务器参数，连接到天气服务
    server_params = StdioServerParameters(
        command="python",
        args=["mock_weather_server.py"]
    )
    
    print("连接到天气服务服务器...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            
            print("\n=== 可用工具 ===")
            tools = await session.list_tools()
            for tool in tools:
                print(f"- {tool.name}: {tool.description}")
            
            print("\n=== 可用资源 ===")
            resources = await session.list_resources()
            for resource in resources:
                print(f"- {resource.name}: {resource.description}")
                
            print("\n=== 可用提示 ===")
            prompts = await session.list_prompts()
            for prompt in prompts:
                print(f"- {prompt.name}: {prompt.description}")
            
            print("\n=== 读取城市资源 ===")
            cities_content, _ = await session.read_resource("weather://cities")
            print(f"可查询的城市: {cities_content}")
            
            # 调用工具示例
            cities = ["北京", "上海", "广州"]
            
            print("\n=== 获取当前天气 ===")
            for city in cities:
                print(f"\n{city}:")
                result = await session.call_tool("get_weather", {"city": city})
                print(result)
            
            print("\n=== 获取天气预报 ===")
            forecast = await session.call_tool("get_forecast", {"city": "成都", "days": 3})
            print(forecast)
            
            print("\n=== 使用提示模板 ===")
            prompt_result = await session.get_prompt("weather_query_prompt", {"city": "杭州"})
            print("提示内容:")
            for msg in prompt_result.messages:
                print(f"[{msg.role}] {msg.content.text}")

if __name__ == "__main__":
    asyncio.run(run_weather_client()) 