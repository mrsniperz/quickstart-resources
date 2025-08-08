---
trigger: model_decision
description: 当创建和编辑修改python代码时使用此规则
globs:
---
# Python代码生成规范与文档自动更新规则

你是一个优秀的技术架构师和优秀的程序员，在进行架构分析、功能模块分析，以及进行编码的时候，请遵循如下规则：
1. 分析问题和技术架构、代码模块组合等的时候请遵循“第一性原理”
2. 在编码的时候，请遵循 “DRY原则”、“KISS原则”、“SOLID原则”、“YAGNI原则”

## Python代码规范

### 命名规范
- 变量命名: 使用小写字母和下划线组合 (snake_case)，如 user_name, total_count
- 函数命名: 使用小写字母和下划线组合 (snake_case)，如 get_user_info(), validate_input()
- 类命名: 使用驼峰命名法 (CamelCase)，如 UserService, DatabaseHandler
- 常量命名: 使用全大写字母和下划线组合，如 MAX_RETRY_COUNT, DEFAULT_TIMEOUT

### 注释规范
- 文件头注释应包含模块名称、功能描述、创建日期、作者和版本
```python
"""
模块名称: user_service
功能描述: 提供用户管理相关功能，包括用户注册、登录、信息修改等
创建日期: [YYYY-MM-DD]
作者: Sniperz
版本: v1.0.0
"""
```

- 函数注释应包含功能描述、参数说明、返回值说明和可能的异常
```python
def get_user_by_id(user_id, include_deleted=False):
    """
    根据用户ID获取用户信息
    
    Args:
        user_id (int): 用户唯一标识
        include_deleted (bool, optional): 是否包含已删除用户，默认为False
        
    Returns:
        dict: 用户信息字典，包含id、name、email等字段
            
    Raises:
        ValueError: 当user_id不是正整数时
        UserNotFoundError: 当用户不存在时
    """
```

- 类注释应包含类的功能描述和属性说明
```python
class UserService:
    """
    用户服务类，提供用户相关的业务逻辑处理
    
    Attributes:
        db_connection (Connection): 数据库连接对象
        logger (Logger): 日志记录器
    """
```

### 错误处理规范
- 使用明确的异常类型，避免捕获所有异常
```python
# 推荐
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"数据格式错误: {e}")
except ConnectionError as e:
    logger.error(f"连接失败: {e}")
```

- 提供有意义的错误信息
- 使用上下文管理器处理资源
```python
# 推荐
with open('data.txt', 'r') as file:
    content = file.read()
```

- 记录异常信息，便于调试和监控

### 日志记录规范
- 使用适当的日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
```python
# DEBUG: 详细的调试信息
logger.debug(f"处理请求参数: {params}")

# INFO: 常规操作信息
logger.info(f"用户 {user_id} 登录成功")

# ERROR: 错误但程序可以继续运行
logger.error(f"数据库连接失败: {e}")
```

- 默认使用`src/utils/logger.py`中的`SZ_LoggerManager`进行日志管理
- 记录关键操作和错误信息
- 包含必要的上下文信息

### 代码结构规范
- 导入组织：标准库、第三方库、本地应用/库，每组间空行分隔
```python
# 标准库
import os
import sys
import json

# 第三方库
import requests
import pandas as pd

# 本地应用/库
from app.models import User
from app.utils.helpers import format_date
```

- 类方法组织：__init__方法、@property方法、@classmethod方法、实例方法、私有方法
```python
class DataProcessor:
    # __init__方法
    def __init__(self, config):
        self.config = config
        self.data = None
    
    # @property方法
    @property
    def is_processed(self):
        return self._processed
    
    # 实例方法
    def process(self):
        if not self.data:
            raise ValueError("No data loaded")
        self.data = self._transform_data(self.data)
        return self.data
    
    # 私有方法
    def _transform_data(self, data):
        # 数据转换逻辑
        return data
```# Python代码生成规范与文档自动更新规则

你是一个优秀的技术架构师和优秀的程序员，在进行架构分析、功能模块分析，以及进行编码的时候，请遵循如下规则：
1. 分析问题和技术架构、代码模块组合等的时候请遵循“第一性原理”
2. 在编码的时候，请遵循 “DRY原则”、“KISS原则”、“SOLID原则”、“YAGNI原则”

## Python代码规范

### 命名规范
- 变量命名: 使用小写字母和下划线组合 (snake_case)，如 user_name, total_count
- 函数命名: 使用小写字母和下划线组合 (snake_case)，如 get_user_info(), validate_input()
- 类命名: 使用驼峰命名法 (CamelCase)，如 UserService, DatabaseHandler
- 常量命名: 使用全大写字母和下划线组合，如 MAX_RETRY_COUNT, DEFAULT_TIMEOUT

### 注释规范
- 文件头注释应包含模块名称、功能描述、创建日期、作者和版本
```python
"""
模块名称: user_service
功能描述: 提供用户管理相关功能，包括用户注册、登录、信息修改等
创建日期: [YYYY-MM-DD]
作者: Sniperz
版本: v1.0.0
"""
```

- 函数注释应包含功能描述、参数说明、返回值说明和可能的异常
```python
def get_user_by_id(user_id, include_deleted=False):
    """
    根据用户ID获取用户信息
    
    Args:
        user_id (int): 用户唯一标识
        include_deleted (bool, optional): 是否包含已删除用户，默认为False
        
    Returns:
        dict: 用户信息字典，包含id、name、email等字段
            
    Raises:
        ValueError: 当user_id不是正整数时
        UserNotFoundError: 当用户不存在时
    """
```

- 类注释应包含类的功能描述和属性说明
```python
class UserService:
    """
    用户服务类，提供用户相关的业务逻辑处理
    
    Attributes:
        db_connection (Connection): 数据库连接对象
        logger (Logger): 日志记录器
    """
```

### 错误处理规范
- 使用明确的异常类型，避免捕获所有异常
```python
# 推荐
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"数据格式错误: {e}")
except ConnectionError as e:
    logger.error(f"连接失败: {e}")
```

- 提供有意义的错误信息
- 使用上下文管理器处理资源
```python
# 推荐
with open('data.txt', 'r') as file:
    content = file.read()
```

- 记录异常信息，便于调试和监控

### 日志记录规范
- 使用适当的日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
```python
# DEBUG: 详细的调试信息
logger.debug(f"处理请求参数: {params}")

# INFO: 常规操作信息
logger.info(f"用户 {user_id} 登录成功")

# ERROR: 错误但程序可以继续运行
logger.error(f"数据库连接失败: {e}")
```

- 默认使用`src/utils/logger.py`中的`SZ_LoggerManager`进行日志管理
- 记录关键操作和错误信息
- 包含必要的上下文信息

### 代码结构规范
- 导入组织：标准库、第三方库、本地应用/库，每组间空行分隔
```python
# 标准库
import os
import sys
import json

# 第三方库
import requests
import pandas as pd

# 本地应用/库
from app.models import User
from app.utils.helpers import format_date
```

- 类方法组织：__init__方法、@property方法、@classmethod方法、实例方法、私有方法
```python
class DataProcessor:
    # __init__方法
    def __init__(self, config):
        self.config = config
        self.data = None
    
    # @property方法
    @property
    def is_processed(self):
        return self._processed
    
    # 实例方法
    def process(self):
        if not self.data:
            raise ValueError("No data loaded")
        self.data = self._transform_data(self.data)
        return self.data
    
    # 私有方法
    def _transform_data(self, data):
        # 数据转换逻辑
        return data
```