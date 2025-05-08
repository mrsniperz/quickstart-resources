# 房价查询客户端

这是一个简单的MCP客户端，用于连接房价服务器并查询美国主要城市的房价信息。

## 功能

- 查询城市平均房价
- 查看城市社区房价
- 获取城市房价范围
- 列出所有可用城市

## 使用方法

1. 确保已安装所需依赖:
   ```
   pip install mcp
   ```

2. 运行客户端:
   ```
   python housing_client.py housing_prices.py
   ```

3. 命令说明:
   - 直接输入城市名称查询平均房价，例如: `New York`
   - 输入 `list` 查看所有可用城市
   - 输入 `range 城市名` 查看该城市的房价范围，例如: `range Chicago`
   - 输入 `城市:社区` 查询特定社区房价，例如: `Chicago:Loop`
   - 输入 `quit` 退出程序

## 示例

```
请输入命令: list

可用城市列表:
- New York
- Los Angeles
- Chicago
- Houston
- Phoenix
- Philadelphia
- San Antonio
- San Diego
- Dallas
- San Francisco

请输入命令: New York

City: New York
Average Housing Price: $1,216,924
Annual Price Trend: 5.0% increase

请输入命令: New York:Brooklyn

City: New York
Neighborhood: Brooklyn
Average Housing Price: $1,071,987
Comparison: 11.5% below city average
``` 