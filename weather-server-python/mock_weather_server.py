from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# 初始化FastMCP服务器
mcp = FastMCP("天气服务")

# Mock数据 - 城市列表及其基础天气信息
CITIES = {
    "北京": {"base_temp": 20, "humidity": 45, "wind": 12},
    "上海": {"base_temp": 24, "humidity": 65, "wind": 10},
    "广州": {"base_temp": 28, "humidity": 70, "wind": 8},
    "深圳": {"base_temp": 27, "humidity": 72, "wind": 7},
    "成都": {"base_temp": 22, "humidity": 60, "wind": 5},
    "西安": {"base_temp": 19, "humidity": 40, "wind": 15},
    "杭州": {"base_temp": 23, "humidity": 62, "wind": 9},
    "南京": {"base_temp": 22, "humidity": 58, "wind": 11},
    "武汉": {"base_temp": 23, "humidity": 60, "wind": 10},
    "重庆": {"base_temp": 25, "humidity": 65, "wind": 6},
    "天津": {"base_temp": 21, "humidity": 50, "wind": 13},
    "青岛": {"base_temp": 20, "humidity": 68, "wind": 14},
    "大连": {"base_temp": 19, "humidity": 65, "wind": 16},
    "厦门": {"base_temp": 26, "humidity": 75, "wind": 8},
    "苏州": {"base_temp": 23, "humidity": 65, "wind": 9},
    # 英文名称映射到中文
    "Beijing": {"base_temp": 20, "humidity": 45, "wind": 12, "zh_name": "北京"},
    "Shanghai": {"base_temp": 24, "humidity": 65, "wind": 10, "zh_name": "上海"},
    "Guangzhou": {"base_temp": 28, "humidity": 70, "wind": 8, "zh_name": "广州"},
    "Shenzhen": {"base_temp": 27, "humidity": 72, "wind": 7, "zh_name": "深圳"},
    "Chengdu": {"base_temp": 22, "humidity": 60, "wind": 5, "zh_name": "成都"},
    "Xi'an": {"base_temp": 19, "humidity": 40, "wind": 15, "zh_name": "西安"},
    "Hangzhou": {"base_temp": 23, "humidity": 62, "wind": 9, "zh_name": "杭州"},
    "Nanjing": {"base_temp": 22, "humidity": 58, "wind": 11, "zh_name": "南京"},
    "Wuhan": {"base_temp": 23, "humidity": 60, "wind": 10, "zh_name": "武汉"},
    "Chongqing": {"base_temp": 25, "humidity": 65, "wind": 6, "zh_name": "重庆"},
    "Tianjin": {"base_temp": 21, "humidity": 50, "wind": 13, "zh_name": "天津"},
    "Qingdao": {"base_temp": 20, "humidity": 68, "wind": 14, "zh_name": "青岛"},
    "Dalian": {"base_temp": 19, "humidity": 65, "wind": 16, "zh_name": "大连"},
    "Xiamen": {"base_temp": 26, "humidity": 75, "wind": 8, "zh_name": "厦门"},
    "Suzhou": {"base_temp": 23, "humidity": 65, "wind": 9, "zh_name": "苏州"}
}

# 天气类型
WEATHER_TYPES = [
    "晴朗", "多云", "阴天", "小雨", "中雨", "大雨", "雷阵雨", 
    "小雪", "中雪", "大雪", "雾", "霾", "沙尘暴"
]

# 天气图标映射
WEATHER_ICONS = {
    "晴朗": "[晴]",
    "多云": "[多云]",
    "阴天": "[阴]",
    "小雨": "[小雨]",
    "中雨": "[中雨]",
    "大雨": "[大雨]",
    "雷阵雨": "[雷阵雨]",
    "小雪": "[小雪]",
    "中雪": "[中雪]",
    "大雪": "[大雪]",
    "雾": "[雾]",
    "霾": "[霾]",
    "沙尘暴": "[沙尘]"
}

# 空气质量指数范围
AQI_RANGES = [
    {"range": (0, 50), "level": "优", "color": "绿色"},
    {"range": (51, 100), "level": "良", "color": "黄色"},
    {"range": (101, 150), "level": "轻度污染", "color": "橙色"},
    {"range": (151, 200), "level": "中度污染", "color": "红色"},
    {"range": (201, 300), "level": "重度污染", "color": "紫色"},
    {"range": (301, 500), "level": "严重污染", "color": "褐红色"}
]

# 生成天气预报
def generate_forecast(city: str, days: int = 5) -> List[Dict]:
    if city not in CITIES:
        return []
    
    base_info = CITIES[city]
    forecasts = []
    
    today = datetime.now()
    
    for i in range(days):
        date = today + timedelta(days=i)
        # 随机生成天气类型
        weather_type = random.choice(WEATHER_TYPES)
        
        # 根据基础气温随机浮动生成高低温
        temp_variation = random.randint(-5, 5)
        high_temp = base_info["base_temp"] + temp_variation
        low_temp = high_temp - random.randint(5, 10)
        
        # 随机生成湿度
        humidity = base_info["humidity"] + random.randint(-10, 10)
        humidity = max(0, min(100, humidity))
        
        # 随机生成风速
        wind_speed = base_info["wind"] + random.randint(-3, 3)
        wind_speed = max(0, wind_speed)
        
        # 随机生成空气质量指数
        aqi = random.randint(20, 250)
        aqi_info = next((item for item in AQI_RANGES if aqi >= item["range"][0] and aqi <= item["range"][1]), AQI_RANGES[-1])
        
        forecasts.append({
            "date": date.strftime("%Y-%m-%d"),
            "day_of_week": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()],
            "weather": weather_type,
            "icon": WEATHER_ICONS.get(weather_type, "❓"),
            "high_temp": high_temp,
            "low_temp": low_temp,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "aqi": aqi,
            "aqi_level": aqi_info["level"]
        })
    
    return forecasts


@mcp.tool()
def get_weather(city: str) -> str:
    """获取指定城市的当前天气情况
    
    Args:
        city: 城市名称（如：北京、上海、广州等）
    """
    if city not in CITIES:
        return "城市不存在"
    
    forecast = generate_forecast(city, 1)[0]
    
    return f"{city}天气：{forecast['weather']} {forecast['icon']}，温度{forecast['low_temp']}-{forecast['high_temp']}度，湿度{forecast['humidity']}%，风速{forecast['wind_speed']}km/h，空气{forecast['aqi_level']}"


@mcp.tool()
def get_forecast(city: str, days: int = 5) -> str:
    """获取指定城市的未来几天天气预报
    
    Args:
        city: 城市名称（如：北京、上海、广州等）
        days: 预报天数，默认5天
    """
    if city not in CITIES:
        return f"抱歉，未找到{city}的天气信息。可用城市: {', '.join(CITIES.keys())}"
    
    if days < 1 or days > 7:
        return "预报天数必须在1-7天之间"
    
    forecasts = generate_forecast(city, days)
    
    result = [f"{city}未来{days}天天气预报:"]
    
    for f in forecasts:
        result.append(f"""
日期: {f['date']} {f['day_of_week']}
天气: {f['weather']} {f['icon']}
温度: {f['low_temp']}°C ~ {f['high_temp']}°C
湿度: {f['humidity']}%
风速: {f['wind_speed']} km/h
空气质量指数: {f['aqi']} ({f['aqi_level']})
""")
    
    return "\n---\n".join(result)


@mcp.tool()
def list_cities() -> str:
    """列出所有可查询的城市"""
    return f"可查询的城市列表: {', '.join(CITIES.keys())}"


@mcp.resource("weather://cities")
def cities_resource() -> str:
    """可查询城市列表资源"""
    return ", ".join(CITIES.keys())


@mcp.prompt()
def weather_query_prompt(city: str = "") -> str:
    """创建查询天气的提示模板
    
    Args:
        city: 要查询的城市名称
    """
    if city:
        return f"请查询{city}的当前天气情况"
    else:
        cities = ", ".join(CITIES.keys())
        return f"请查询某个城市的天气情况。可查询的城市有: {cities}"


if __name__ == "__main__":
    # 启动MCP服务器
    mcp.run(transport='stdio')
    # print(get_weather("北京"))