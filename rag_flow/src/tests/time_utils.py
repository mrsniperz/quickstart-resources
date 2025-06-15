#!/usr/bin/env python3
"""
时间转换工具模块

提供时间戳和日期字符串之间的转换功能，用于Milvus过滤表达式中的时间筛选。
"""

import time
from datetime import datetime, timezone
from typing import Union, Optional


def datetime_to_timestamp(dt: Union[str, datetime]) -> int:
    """
    将日期时间转换为Unix时间戳（秒）
    
    Args:
        dt: 日期时间，可以是字符串或datetime对象
            支持的字符串格式:
            - "2023-01-01"
            - "2023-01-01 12:30:00"
            - "2023-01-01T12:30:00"
            - "2023-01-01T12:30:00Z"
            - "2023-01-01T12:30:00+08:00"
    
    Returns:
        int: Unix时间戳（秒）
    
    Examples:
        >>> datetime_to_timestamp("2023-01-01")
        1672531200
        >>> datetime_to_timestamp("2023-01-01 12:30:00")
        1672576200
    """
    if isinstance(dt, str):
        # 处理不同的日期字符串格式
        dt = dt.strip()
        
        # 如果只有日期，添加时间部分
        if len(dt) == 10 and dt.count('-') == 2:
            dt += " 00:00:00"
        
        # 处理ISO格式
        if 'T' in dt:
            if dt.endswith('Z'):
                dt = dt[:-1] + '+00:00'
            elif '+' not in dt and '-' not in dt[-6:]:
                dt += '+00:00'
        
        # 解析日期时间字符串
        try:
            if '+' in dt or dt.endswith('Z'):
                # 包含时区信息
                parsed_dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            else:
                # 假设为UTC时间
                parsed_dt = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
        except ValueError as e:
            raise ValueError(f"无法解析日期时间字符串 '{dt}': {e}")
    
    elif isinstance(dt, datetime):
        parsed_dt = dt
        # 如果没有时区信息，假设为UTC
        if parsed_dt.tzinfo is None:
            parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
    else:
        raise TypeError(f"不支持的类型: {type(dt)}")
    
    return int(parsed_dt.timestamp())


def timestamp_to_datetime(timestamp: int, timezone_offset: Optional[str] = None) -> datetime:
    """
    将Unix时间戳转换为datetime对象
    
    Args:
        timestamp: Unix时间戳（秒）
        timezone_offset: 时区偏移，如 "+08:00"，默认为UTC
    
    Returns:
        datetime: datetime对象
    
    Examples:
        >>> timestamp_to_datetime(1672531200)
        datetime.datetime(2023, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
        >>> timestamp_to_datetime(1672531200, "+08:00")
        datetime.datetime(2023, 1, 1, 8, 0, tzinfo=datetime.timezone(datetime.timedelta(seconds=28800)))
    """
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    
    if timezone_offset:
        # 解析时区偏移
        if timezone_offset.startswith('+') or timezone_offset.startswith('-'):
            sign = 1 if timezone_offset.startswith('+') else -1
            hours, minutes = map(int, timezone_offset[1:].split(':'))
            offset_seconds = sign * (hours * 3600 + minutes * 60)
            target_tz = timezone(timedelta(seconds=offset_seconds))
            dt = dt.astimezone(target_tz)
    
    return dt


def get_time_range_timestamps(start_date: str, end_date: str) -> tuple[int, int]:
    """
    获取日期范围的时间戳
    
    Args:
        start_date: 开始日期，格式如 "2023-01-01"
        end_date: 结束日期，格式如 "2023-01-31"
    
    Returns:
        tuple: (开始时间戳, 结束时间戳)
    
    Examples:
        >>> get_time_range_timestamps("2023-01-01", "2023-01-31")
        (1672531200, 1675123199)
    """
    start_timestamp = datetime_to_timestamp(start_date + " 00:00:00")
    end_timestamp = datetime_to_timestamp(end_date + " 23:59:59")
    return start_timestamp, end_timestamp


def generate_filter_examples():
    """
    生成常用的时间过滤表达式示例
    
    Returns:
        dict: 包含各种时间过滤示例的字典
    """
    now = int(time.time())
    one_day_ago = now - 86400  # 24小时前
    one_week_ago = now - 604800  # 7天前
    one_month_ago = now - 2592000  # 30天前
    
    examples = {
        "最近24小时创建的记录": f"create_time > {one_day_ago}",
        "最近7天更新的记录": f"update_time > {one_week_ago}",
        "最近30天的记录": f"create_time > {one_month_ago}",
        "指定日期范围": f"create_time >= {datetime_to_timestamp('2023-01-01')} and create_time <= {datetime_to_timestamp('2023-01-31 23:59:59')}",
        "今年创建的记录": f"create_time >= {datetime_to_timestamp('2024-01-01')}",
        "昨天更新的记录": f"update_time >= {one_day_ago} and update_time < {now - (now % 86400)}",
    }
    
    return examples


def print_time_conversion_help():
    """
    打印时间转换帮助信息
    """
    print("=== Milvus时间字段过滤帮助 ===")
    print()
    print("1. 时间字段格式:")
    print("   - create_time: INT64类型，Unix时间戳（秒）")
    print("   - update_time: INT64类型，Unix时间戳（秒）")
    print()
    print("2. 常用时间戳:")
    common_dates = [
        ("2022-01-01 00:00:00 UTC", "1640995200"),
        ("2023-01-01 00:00:00 UTC", "1672531200"),
        ("2024-01-01 00:00:00 UTC", "1704067200"),
        ("2025-01-01 00:00:00 UTC", "1735689600"),
    ]
    for date_str, timestamp in common_dates:
        print(f"   {date_str} = {timestamp}")
    print()
    print("3. 过滤表达式示例:")
    examples = generate_filter_examples()
    for desc, expr in examples.items():
        print(f"   {desc}: {expr}")
    print()
    print("4. 转换工具函数:")
    print("   - datetime_to_timestamp('2023-01-01')")
    print("   - timestamp_to_datetime(1672531200)")
    print("   - get_time_range_timestamps('2023-01-01', '2023-01-31')")


if __name__ == "__main__":
    # 示例用法
    print_time_conversion_help()
    
    # 测试转换功能
    print("\n=== 转换测试 ===")
    test_date = "2023-06-15 14:30:00"
    timestamp = datetime_to_timestamp(test_date)
    back_to_datetime = timestamp_to_datetime(timestamp)
    
    print(f"原始日期: {test_date}")
    print(f"转换为时间戳: {timestamp}")
    print(f"转换回日期: {back_to_datetime}")
    
    # 测试日期范围
    start_ts, end_ts = get_time_range_timestamps("2023-01-01", "2023-01-31")
    print(f"\n2023年1月时间戳范围: {start_ts} - {end_ts}")
