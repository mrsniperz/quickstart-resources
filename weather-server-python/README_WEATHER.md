# MCP 天气服务示例

这是一个使用Model Context Protocol (MCP)构建的简单天气服务示例。该服务提供模拟的天气数据，可以通过MCP客户端查询多个中国城市的天气情况。

## 功能特点

- 支持查询10个主要中国城市的当前天气
- 提供未来1-7天的天气预报
- 包含温度、湿度、风速和空气质量信息
- 支持标准MCP工具、资源和提示模板
- 提供两种服务器运行模式：标准输入/输出(stdio)和HTTP服务器(SSE)

## 安装

1. 确保已安装Python 3.8+
2. 安装所需依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

### 启动天气服务器

#### 标准输入/输出模式

```bash
python mock_weather_server.py
```

#### HTTP服务器模式

```bash
python mock_weather_http_server.py
```

HTTP服务器将在 http://localhost:8000 启动，MCP API端点为 `/mcp`。

### 运行客户端示例

```bash
python weather_client_example.py
```

这将启动一个示例客户端，演示如何与天气服务进行交互，包括列出可用工具、读取资源和调用天气查询等功能。

## MCP 功能

### 工具

- `get_weather(city: str)`: 获取指定城市的当前天气情况
- `get_forecast(city: str, days: int = 5)`: 获取指定城市的未来几天天气预报
- `list_cities()`: 列出所有可查询的城市

### 资源

- `weather://cities`: 提供可查询城市列表的资源

### 提示模板 

- `weather_query_prompt(city: str = "")`: 创建查询天气的提示模板

## 示例城市

服务支持以下城市的天气查询：
- 北京
- 上海
- 广州
- 深圳
- 成都
- 西安
- 杭州
- 南京
- 武汉
- 重庆

## 数据说明

本服务中的天气数据为模拟数据，不代表实际天气情况。数据生成规则如下：

- 温度基于每个城市的基础气温随机生成
- 天气类型从多种可能类型中随机选择
- 湿度、风速和空气质量指数基于城市基础值随机浮动生成

## 与LLM集成

该服务设计用于与大型语言模型(LLM)集成，允许模型通过MCP协议查询天气数据。模型可以：

1. 发现可用工具和资源
2. 调用天气查询工具
3. 读取城市列表资源
4. 使用提示模板生成用户查询

## 许可

MIT 