from mock_weather_server import mcp, get_weather, get_forecast, list_cities
import uvicorn

if __name__ == "__main__":
    # 使用HTTP传输层启动MCP服务器
    # 这将创建一个FastAPI应用，可以通过HTTP访问MCP功能
    print("启动天气服务HTTP服务器...")
    print("服务器运行在: http://localhost:8000")
    print("可通过 /mcp 路径访问MCP API")
    
    # 启动服务器，使用SSE传输方式
    mcp.run(transport='sse', host='0.0.0.0', port=8000, mount_path='/mcp') 