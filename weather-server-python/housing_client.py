import asyncio
import sys
import os
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class HousingPriceClient:
    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self, server_script_path: str):
        """连接到房价MCP服务器
        
        Args:
            server_script_path: 服务器脚本路径
        """
        # 检查文件是否存在
        if not os.path.exists(server_script_path):
            raise FileNotFoundError(f"找不到服务器脚本: {server_script_path}")
            
        # 确保文件扩展名正确
        if not server_script_path.endswith('.py'):
            raise ValueError("服务器脚本必须是.py文件")
            
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
            env=None
        )
        
        print(f"正在连接到服务器: {server_script_path}")
        try:
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
            
            await self.session.initialize()
            
            # 列出可用工具
            response = await self.session.list_tools()
            tools = response.tools
            print("\n已连接到房价服务器，可用工具:", [tool.name for tool in tools])
            return True
        except Exception as e:
            print(f"连接服务器失败: {str(e)}")
            return False

    async def get_city_price(self, city: str):
        """获取指定城市的平均房价
        
        Args:
            city: 城市名称
        """
        try:
            result = await self.session.call_tool("get_average_price", {"city": city})
            return result.content
        except Exception as e:
            return f"查询失败: {str(e)}"

    async def list_available_cities(self):
        """列出所有可用城市"""
        try:
            result = await self.session.call_tool("list_cities", {})
            return result.content
        except Exception as e:
            return f"获取城市列表失败: {str(e)}"

    async def get_neighborhood_price(self, city: str, neighborhood: str):
        """获取指定城市特定社区的房价
        
        Args:
            city: 城市名称
            neighborhood: 社区名称
        """
        try:
            result = await self.session.call_tool("get_price_by_neighborhood", 
                                                {"city": city, "neighborhood": neighborhood})
            return result.content
        except Exception as e:
            return f"查询社区房价失败: {str(e)}"

    async def get_price_range(self, city: str):
        """获取指定城市的房价范围
        
        Args:
            city: 城市名称
        """
        try:
            result = await self.session.call_tool("get_price_range", {"city": city})
            return result.content
        except Exception as e:
            return f"获取价格范围失败: {str(e)}"

    async def interactive_console(self):
        """交互式控制台"""
        print("\n房价查询客户端已启动!")
        print("输入城市名称查询平均房价，输入'list'查看所有城市，输入'quit'退出。")
        
        # 确保输入提示显示
        print("\n请输入命令: ", end="", flush=True)
        
        while True:
            try:
                command = input().strip()
                
                if command.lower() == 'quit':
                    break
                elif command.lower() == 'list':
                    cities = await self.list_available_cities()
                    print("\n可用城市列表:")
                    print(cities)
                elif ":" in command:
                    # 格式: 城市:社区
                    city, neighborhood = command.split(":", 1)
                    result = await self.get_neighborhood_price(city.strip(), neighborhood.strip())
                    print(result)
                elif command.startswith("range "):
                    # 获取价格范围: range 城市
                    city = command[6:].strip()
                    result = await self.get_price_range(city)
                    print(result)
                else:
                    # 假设是城市名称
                    result = await self.get_city_price(command)
                    print(result)
                
                # 每次操作后重新显示提示
                print("\n请输入命令: ", end="", flush=True)
                    
            except Exception as e:
                print(f"\n错误: {str(e)}")
                print("\n请输入命令: ", end="", flush=True)
    
    async def cleanup(self):
        """清理资源"""
        if self.exit_stack:
            await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("用法: python housing_client.py <服务器脚本路径>")
        sys.exit(1)
        
    client = HousingPriceClient()
    try:
        server_script_path = sys.argv[1]
        # 使用绝对路径
        if not os.path.isabs(server_script_path):
            server_script_path = os.path.abspath(server_script_path)
            
        print(f"正在启动客户端，连接到服务器: {server_script_path}")
        connection_success = await client.connect_to_server(server_script_path)
        
        if connection_success:
            await client.interactive_console()
        else:
            print("连接服务器失败，程序退出")
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        await client.cleanup()
        print("客户端已关闭")

if __name__ == "__main__":
    asyncio.run(main()) 