---
trigger: model_decision
description: 创建和修改fastapi代码时使用的规则
globs: 
---
# FastAPI 代码规范

> 最后更新: 2025-06-02
> 版本: 1.0.3

## 项目文档及迭代要求
- 在项目开始时，首先仔细阅读项目.cursor/docs目录下的文件并理解其内容，包括项目的目标、功能架构、技术栈和开发计划，确保对项目的整体架构和实现方式有清晰的认识；

本文档定义了使用FastAPI开发时的代码规范要求，确保生成的代码风格统一、文档完整。

## 1. 代码结构规范

### 1.1 导入组织

- 按以下顺序分组导入：标准库、第三方库、本地应用/库
- 每组之间用空行分隔
- 每组内按字母顺序排序
- 避免使用通配符导入（from module import *）
- 显式导入所需模块，不要依赖间接导入
- 使用绝对导入，避免相对导入带来的混淆
- 将所有导入放在文件顶部，避免在函数或条件语句中导入


### 1.2 应用初始化
```python
app = FastAPI(
    title="API名称",
    description="API描述",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Tag名称",
            "description": "Tag描述"
        }
    ]
)
```

### 1.3 中间件配置
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

## 2. 注释规范

### 2.1 文件头注释
```python
"""
模块名称: service.py
功能描述: 用户服务模块，处理用户相关业务逻辑
创建日期: 2025-05-24
作者: Sniperz
版本: 1.0.0
"""
```

### 2.2 路由函数注释
```python
"""
功能描述: 创建航空翻译数据集合

Args:
    - importer: AviationTranslationImporter依赖实例

Returns:
    CreateCollectionResponse: 包含操作结果和消息的响应

Raises:
    HTTPException: 500 - 创建集合时出错
"""
```

### 2.3 模型类注释
```python
"""
搜索请求模型

属性:
    - query_text: 要搜索的文本
    - search_type: 搜索类型(text_match/full_text)
    - limit: 返回结果数量限制
"""
```

### 2.4 代码块注释
```python
# 区域: 数据准备
# 目的: 将Excel数据转换为模型所需格式
```

## 3. API文档规范

### 3.1 路由装饰器
```python
@app.post(
    "/path",
    response_model=ResponseModel,
    tags=["Tag名称"],
    summary="简要描述",
    description="详细描述"
)
```

### 3.2 错误响应
- 使用HTTPException统一处理
- 包含详细的错误信息
- 400错误: 客户端错误
- 500错误: 服务器错误

## 4. 模型定义规范

### 4.1 基础要求
- 继承自pydantic.BaseModel
- 明确的类型提示
- 可选字段使用Optional

### 4.2 示例
```python
class SearchRequest(BaseModel):
    query_text: str
    search_type: str = "text_match"
    limit: int = 5
```

## 5. 依赖注入规范

### 5.1 依赖项函数
```python
def get_importer(
    collection_name: str = Query(...),
    uri: str = Query(...)
):
    """依赖项函数说明"""
    return Importer(uri, collection_name)
```

### 5.2 路由使用
```python
async def endpoint(importer: Importer = Depends(get_importer)):
    pass
```

## 6. 最佳实践

1. 每个路由应专注于单一功能
2. 业务逻辑应封装在单独的服务类中
3. 使用try-except捕获并处理异常
4. 为重要操作添加执行时间统计
5. 临时文件使用后应及时清理
