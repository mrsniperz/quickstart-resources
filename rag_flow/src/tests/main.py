from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any, Union
import time
from pathlib import Path
import pandas as pd
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import tempfile
import os

from aviation_translation.src.core.translate_vector import AviationTranslationImporter

# 时间转换工具函数
def parse_datetime_string(datetime_str: str, timezone_offset: Optional[str] = None) -> tuple[datetime, str]:
    """
    解析日期时间字符串

    Returns:
        tuple: (datetime对象, 使用的时区)
    """
    dt_str = datetime_str.strip()

    # 如果只有日期，添加时间部分
    if len(dt_str) == 10 and dt_str.count('-') == 2:
        dt_str += " 00:00:00"

    # 处理ISO格式
    if 'T' in dt_str:
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        elif '+' not in dt_str and '-' not in dt_str[-6:]:
            dt_str += '+00:00'

    try:
        if '+' in dt_str or dt_str.endswith('Z'):
            # 包含时区信息
            parsed_dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            timezone_used = str(parsed_dt.tzinfo)
        else:
            # 使用指定时区或默认UTC
            if timezone_offset:
                dt_str += timezone_offset
                parsed_dt = datetime.fromisoformat(dt_str)
                timezone_used = timezone_offset
            else:
                parsed_dt = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
                timezone_used = "UTC"
    except ValueError as e:
        raise ValueError(f"无法解析日期时间字符串 '{datetime_str}': {e}")

    return parsed_dt, timezone_used


def format_datetime_with_timezone(timestamp: int, timezone_offset: Optional[str] = None) -> tuple[datetime, str, str]:
    """
    格式化时间戳为datetime对象

    Returns:
        tuple: (datetime对象, ISO格式字符串, 使用的时区)
    """
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    timezone_used = "UTC"

    if timezone_offset:
        try:
            # 解析时区偏移
            if timezone_offset.startswith('+') or timezone_offset.startswith('-'):
                sign = 1 if timezone_offset.startswith('+') else -1
                hours, minutes = map(int, timezone_offset[1:].split(':'))
                offset_seconds = sign * (hours * 3600 + minutes * 60)

                target_tz = timezone(timedelta(seconds=offset_seconds))
                dt = dt.astimezone(target_tz)
                timezone_used = timezone_offset
        except Exception:
            # 如果时区解析失败，使用UTC
            pass

    iso_format = dt.isoformat()
    return dt, iso_format, timezone_used


app = FastAPI(
    title="航空翻译数据管理API",
    description="用于管理Milvus中的航空翻译数据的API接口",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Collection Management",
            "description": "集合管理相关操作",
        },
        {
            "name": "Data Import",
            "description": "数据导入相关操作",
        },
        {
            "name": "Search",
            "description": "数据搜索相关操作",
        },
        {
            "name": "Tools",
            "description": "实用工具接口",
        },
    ],
)

origins = ["http://localhost:8080", "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 设置允许的origins来源
    allow_credentials=True,
    allow_methods=["*"],  # 设置允许跨域的http方法，比如 get、post、put等。
    allow_headers=["*"],  # 允许跨域的headers，可以用来鉴别来源等作用。
    expose_headers=["Content-Disposition"],  # 添加需要暴露的头部
)


def get_importer(
    collection_name: str = Query("aviation_translations", description="集合名称"),
    uri: str = Query("http://124.71.148.16:19530", description="Milvus地址"),
    token: str = Query("root:Milvus", description="认证token"),
):
    """依赖项函数，每次请求创建新的importer实例"""
    return AviationTranslationImporter(
        uri=uri, collection_name=collection_name, token=token
    )


# 请求和响应模型
class CreateCollectionResponse(BaseModel):
    success: bool
    message: str
    collection_name: str


class CreatePartitionRequest(BaseModel):
    partition_name: str


class CreatePartitionResponse(BaseModel):
    success: bool
    message: str
    collection_name: str
    partition_name: str


class ImportDataResponse(BaseModel):
    success: bool
    message: str
    data_count: int
    time_elapsed: float


class SearchRequest(BaseModel):
    query_text: str
    search_type: str = "full_text"
    search_direction: str = "en_to_zh"
    partition_names: Optional[list] = None
    limit: int = 5


class LoadPartitionResponse(BaseModel):
    success: bool
    message: str
    collection_name: str
    partition_name: str


class SearchResult(BaseModel):
    id: Optional[int] = None
    text: str
    translation: str
    score: Optional[float] = None
    fuzzy_score: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SearchResponse(BaseModel):
    success: bool
    results: List[SearchResult]
    count: int


class AlterFieldRequest(BaseModel):
    field_name: str
    max_length: Optional[int] = None  # VARCHAR字段的最大字符长度 [1, 65535]
    max_capacity: Optional[int] = None  # ARRAY字段的最大容量
    mmap_enabled: Optional[bool] = None  # 是否启用内存映射


class AlterFieldResponse(BaseModel):
    success: bool
    message: str
    collection_name: str
    field_name: str


class DescribeCollectionResponse(BaseModel):
    success: bool
    collection_name: str
    description: Optional[str] = None
    fields: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    load_status: Optional[str] = None
    aliases: List[str] = []
    properties: Dict[str, Any] = {}


class AddTimeFieldsResponse(BaseModel):
    success: bool
    message: str
    collection_name: str
    has_time_fields: bool  # 是否包含完整的时间字段


class UpsertRequest(BaseModel):
    data: Union[Dict[str, Any], List[Dict[str, Any]]]
    partition_name: Optional[str] = None
    use_content_based_id: Optional[bool] = False


class UpsertResponse(BaseModel):
    success: bool
    message: str
    upsert_count: int
    collection_name: str


class DeleteRequest(BaseModel):
    ids: Optional[List[Union[str, int]]] = None
    filter_expr: Optional[str] = None
    partition_name: Optional[str] = None


class DeleteResponse(BaseModel):
    success: bool
    message: str
    delete_count: int
    collection_name: str


class InsertSingleRequest(BaseModel):
    text: str
    translation: str
    partition_name: str = "from_api"


class InsertSingleResponse(BaseModel):
    success: bool
    message: str
    collection_name: str
    partition_name: str


# 时间转换工具相关模型
class DateTimeToTimestampRequest(BaseModel):
    datetime_str: str
    timezone_offset: Optional[str] = None


class DateTimeToTimestampResponse(BaseModel):
    success: bool
    datetime_str: str
    timestamp: int
    timezone_used: str


class TimestampToDateTimeRequest(BaseModel):
    timestamp: int
    timezone_offset: Optional[str] = None


class TimestampToDateTimeResponse(BaseModel):
    success: bool
    timestamp: int
    datetime_str: str
    iso_format: str
    timezone_used: str


class TimeRangeRequest(BaseModel):
    start_date: str
    end_date: str
    timezone_offset: Optional[str] = None


class TimeRangeResponse(BaseModel):
    success: bool
    start_date: str
    end_date: str
    start_timestamp: int
    end_timestamp: int
    filter_expression: str
    timezone_used: str


class FilterExamplesResponse(BaseModel):
    success: bool
    examples: Dict[str, str]
    common_timestamps: Dict[str, int]
    usage_tips: List[str]


@app.post(
    "/collections/create",
    response_model=CreateCollectionResponse,
    tags=["Collection Management"],
    summary="创建航空翻译集合",
    description="创建一个新的航空翻译集合，包含BM25索引和必要的字段配置。",
)
async def create_collection(
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    创建航空翻译数据集合

    返回:
        CreateCollectionResponse: 包含操作结果和消息的响应
    """
    try:
        start_time = time.time()
        importer.create_collection()
        elapsed = time.time() - start_time

        return CreateCollectionResponse(
            success=True,
            message=f"集合创建成功，耗时 {elapsed:.2f}秒",
            collection_name=importer.collection_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建集合时出错: {str(e)}")


@app.post(
    "/collections/partitions",
    response_model=CreatePartitionResponse,
    tags=["Collection Management"],
    summary="创建分区",
    description="在航空翻译集合中创建一个新的分区。",
)
async def create_partition(
    request: CreatePartitionRequest,
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    在集合中创建新分区

    参数:
        request (CreatePartitionRequest): 包含分区名称的请求体

    返回:
        CreatePartitionResponse: 包含操作结果和消息的响应
    """
    try:
        start_time = time.time()
        importer.create_custom_partition(request.partition_name)
        elapsed = time.time() - start_time

        return CreatePartitionResponse(
            success=True,
            message=f"分区创建成功，耗时 {elapsed:.2f}秒",
            collection_name=importer.collection_name,
            partition_name=request.partition_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建分区时出错: {str(e)}")


@app.post(
    "/data/import",
    response_model=ImportDataResponse,
    tags=["Data Import"],
    summary="导入Excel数据",
    description="从Excel文件导入航空翻译数据到Milvus集合。",
)
async def import_data(
    file: UploadFile = File(..., description="包含翻译数据的Excel文件"),
    partition_name: Optional[str] = Query(None, description="可选的分区名称"),
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    从Excel文件导入数据到Milvus

    参数:
        file (UploadFile): 包含翻译数据的Excel文件
        partition_name (Optional[str]): 目标分区名称

    返回:
        ImportDataResponse: 包含导入结果的响应
    """
    try:
        # 创建临时文件保存上传的Excel
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            start_time = time.time()

            # 准备数据
            data = importer.prepare_data(temp_path)
            data_count = len(data)

            # 插入数据
            importer.insert_data_to_milvus_with_chunk(
                data, partition_name=partition_name if partition_name else None
            )

            elapsed = time.time() - start_time

            return ImportDataResponse(
                success=True,
                message=f"成功导入 {data_count} 条数据",
                data_count=data_count,
                time_elapsed=elapsed,
            )
        finally:
            # 删除临时文件
            os.unlink(temp_path)

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="上传的Excel文件为空或格式不正确")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入数据时出错: {str(e)}")


@app.post(
    "/search",
    response_model=SearchResponse,
    tags=["Search"],
    summary="搜索翻译数据",
    description="在航空翻译数据中执行搜索，支持文本匹配和全文搜索两种模式，以及英中双向翻译。",
)
async def search_translations(
    request: SearchRequest,
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    搜索航空翻译数据

    参数:
        request (SearchRequest): 包含搜索参数和查询文本的请求体

    返回:
        SearchResponse: 包含搜索结果和数量的响应
    """
    try:
        if request.search_type not in ["text_match", "full_text"]:
            raise HTTPException(
                status_code=400, detail="search_type必须是'text_match'或'full_text'"
            )
            
        if request.search_direction not in ["en_to_zh", "zh_to_en"]:
            raise HTTPException(
                status_code=400, detail="search_direction必须是'en_to_zh'或'zh_to_en'"
            )

        results = importer.search_data(
            query_text=request.query_text,
            search_type=request.search_type,
            search_direction=request.search_direction,
            partition_names=request.partition_names,
            limit=request.limit,
        )

        formatted_results = [
            SearchResult(
                id=item.get("id"),
                text=item.get("text", ""),
                translation=item.get("translation", ""),
                score=item.get("score"),
                fuzzy_score=item.get("fuzzy_score"),
                created_at=datetime.fromtimestamp(item.get("create_time")) if item.get("create_time") else None,
                updated_at=datetime.fromtimestamp(item.get("update_time")) if item.get("update_time") else None,
            )
            for item in results
        ]

        return SearchResponse(
            success=True,
            results=formatted_results,
            count=len(formatted_results),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索时出错: {str(e)}")


# 健康检查端点
@app.get("/health", tags=["System"])
async def health_check(
    partition_name: Optional[str] = Query(None, description="可选的分区名称"),
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    服务健康检查

    返回:
        dict: 包含服务状态信息
    """
    try:
        health_info = importer.get_health_info(partition_name=partition_name)
        return health_info
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"服务异常: {str(e)}")


# 加载和释放集合（collection)功能
@app.post(
    "/collections/load",
    response_model=CreateCollectionResponse,
    tags=["Collection Management"],
    summary="加载航空翻译集合",
    description="加载整个航空翻译集合到内存中。",
)
async def load_collection(
    load_fields: Optional[List[str]] = Query(
        None, description="可选的要加载的字段列表"
    ),
    skip_load_dynamic_field: bool = Query(False, description="是否跳过加载动态字段"),
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    加载整个航空翻译数据集合

    参数:
        load_fields (Optional[List[str]]): 可选的要加载的字段列表
        skip_load_dynamic_field (bool): 是否跳过加载动态字段

    返回:
        CreateCollectionResponse: 包含操作结果和消息的响应
    """
    try:
        start_time = time.time()
        importer.load_collection(
            load_fields=load_fields, skip_load_dynamic_field=skip_load_dynamic_field
        )
        elapsed = time.time() - start_time

        return CreateCollectionResponse(
            success=True,
            message=f"集合加载成功，耗时 {elapsed:.2f}秒",
            collection_name=importer.collection_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载集合时出错: {str(e)}")


@app.post(
    "/collections/release",
    response_model=CreateCollectionResponse,
    tags=["Collection Management"],
    summary="释放航空翻译集合",
    description="释放整个航空翻译集合从内存中。",
)
async def release_collection(
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    释放整个航空翻译数据集合

    返回:
        CreateCollectionResponse: 包含操作结果和消息的响应
    """
    try:
        start_time = time.time()
        importer.release_collection()
        elapsed = time.time() - start_time

        return CreateCollectionResponse(
            success=True,
            message=f"集合释放成功，耗时 {elapsed:.2f}秒",
            collection_name=importer.collection_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"释放集合时出错: {str(e)}")


@app.post(
    "/partitions/load",
    response_model=LoadPartitionResponse,
    tags=["Partition Management"],
    summary="加载分区",
    description="加载指定分区到内存中。",
)
async def load_partition(
    partition_name: str = Query(..., description="要加载的分区名称"),
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    加载指定分区

    参数:
        partition_name (str): 要加载的分区名称

    返回:
        LoadPartitionResponse: 包含操作结果和消息的响应
    """
    try:
        start_time = time.time()
        importer.load_specified_partitions(partition_names=[partition_name])
        elapsed = time.time() - start_time

        return LoadPartitionResponse(
            success=True,
            message=f"分区加载成功，耗时 {elapsed:.2f}秒",
            collection_name=importer.collection_name,
            partition_name=partition_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载分区时出错: {str(e)}")


@app.post(
    "/partitions/release",
    response_model=LoadPartitionResponse,
    tags=["Partition Management"],
    summary="释放分区",
    description="释放指定分区从内存中。",
)
async def release_partition(
    partition_name: str = Query(..., description="要释放的分区名称"),
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    释放指定分区
    参数:

    partition_name (str): 要释放的分区名称

    返回:
        LoadPartitionResponse: 包含操作结果和消息的响应
    """
    try:
        start_time = time.time()
        importer.release_specified_partitions(partition_names=[partition_name])
        elapsed = time.time() - start_time

        return LoadPartitionResponse(
            success=True,
            message=f"分区释放成功，耗时 {elapsed:.2f}秒",
            collection_name=importer.collection_name,
            partition_name=partition_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"释放分区时出错: {str(e)}")


@app.delete(
    "/collections/delete",
    response_model=CreateCollectionResponse,
    tags=["Collection Management"],
    summary="删除航空翻译集合",
    description="删除指定的航空翻译集合。",
)
async def delete_collection(
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    删除航空翻译数据集合

    返回:
        CreateCollectionResponse: 包含操作结果和消息的响应
    """
    try:
        start_time = time.time()
        importer.delete_collection()
        elapsed = time.time() - start_time

        return CreateCollectionResponse(
            success=True,
            message=f"集合删除成功，耗时 {elapsed:.2f}秒",
            collection_name=importer.collection_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除集合时出错: {str(e)}")


@app.get(
    "/collections/load_state",
    tags=["Collection Management"],
    summary="获取集合加载状态",
    description="获取航空翻译集合的加载状态。",
)
async def get_collection_load_state(
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    获取航空翻译数据集合的加载状态

    返回:
        dict: 包含集合加载状态的响应
    """
    try:
        load_state = importer.client.get_load_state(
            collection_name=importer.collection_name
        )

        return {
            "success": True,
            "collection_name": importer.collection_name,
            "load_state": load_state,
            "is_loaded": load_state.get("state") == 3,  # LoadState.Loaded 的枚举值为 3
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取集合加载状态时出错: {str(e)}")


@app.get(
    "/collections/describe",
    response_model=DescribeCollectionResponse,
    tags=["Collection Management"],
    summary="获取集合详细描述",
    description="获取指定集合的详细描述信息，包括字段、索引、加载状态等。",
)
async def describe_collection(
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    获取集合详细描述信息

    返回:
        DescribeCollectionResponse: 包含集合详细信息的响应
    """
    try:
        start_time = time.time()
        
        # 获取集合描述
        collection_info = importer.describe_collection()
        elapsed = time.time() - start_time

        # 格式化响应
        return DescribeCollectionResponse(
            success=True,
            collection_name=importer.collection_name,
            description=collection_info.get("description"),
            fields=collection_info.get("fields", []),
            indexes=collection_info.get("indexes", []),
            load_status=collection_info.get("load_status"),
            aliases=collection_info.get("aliases", []),
            properties=collection_info.get("properties", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取集合描述时出错: {str(e)}")


@app.post(
    "/collections/alter_field",
    response_model=AlterFieldResponse,
    tags=["Collection Management"],
    summary="修改集合字段属性",
    description="""修改指定集合中现有字段的属性。

支持修改的属性：
- VARCHAR字段: max_length (最大字符长度)
- ARRAY字段: max_capacity (数组最大容量)
- 所有字段: mmap_enabled (内存映射启用状态)

注意：不能添加新字段、删除字段或修改字段类型。""",
)
async def alter_collection_field(
    request: AlterFieldRequest,
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    修改集合字段属性

    参数:
        request (AlterFieldRequest): 包含字段名称和要修改的属性

    返回:
        AlterFieldResponse: 包含操作结果和消息的响应
    """
    try:
        start_time = time.time()

        # 准备参数
        params = {}
        if request.max_length is not None:
            params["max_length"] = request.max_length
        if request.max_capacity is not None:
            params["max_capacity"] = request.max_capacity
        if request.mmap_enabled is not None:
            params["mmap_enabled"] = request.mmap_enabled

        # 修改字段属性
        importer.alter_collection_field(request.field_name, **params)
        elapsed = time.time() - start_time

        return AlterFieldResponse(
            success=True,
            message=f"字段属性修改成功，耗时 {elapsed:.2f}秒",
            collection_name=importer.collection_name,
            field_name=request.field_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修改字段属性时出错: {str(e)}")


@app.post(
    "/data/insert_single",
    response_model=InsertSingleResponse,
    tags=["Data Import"],
    summary="插入单条翻译数据",
    description="插入单条翻译数据到指定分区。",
)
async def insert_single_translation(
    request: InsertSingleRequest,
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    插入单条翻译数据

    参数:
        request (InsertSingleRequest): 包含翻译数据的请求体

    返回:
        InsertSingleResponse: 包含操作结果和消息的响应
    """
    try:
        success = importer.insert_single_entry(
            text=request.text,
            translation=request.translation,
            partition_name=request.partition_name
        )

        if success:
            return InsertSingleResponse(
                success=True,
                message="单条翻译数据插入成功",
                collection_name=importer.collection_name,
                partition_name=request.partition_name,
            )
        else:
            raise HTTPException(status_code=500, detail="插入单条翻译数据失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"插入单条翻译数据时出错: {str(e)}")


@app.post(
    "/data/upsert",
    response_model=UpsertResponse,
    tags=["Data Import"],
    summary="更新或插入翻译数据",
    description="""更新或插入翻译数据。如果数据中的主键已存在，则更新该记录；如果不存在，则插入新记录。

**请求示例：**

单条数据更新（指定ID）：
```json
{
  "data": {
    "id": 123,
    "text": "aircraft engine",
    "translation": "航空发动机"
  },
  "partition_name": "aviation_engine"
}
```

单条数据插入（不指定ID，自动生成）：
```json
{
  "data": {
    "text": "flight control system",
    "translation": "飞行控制系统"
  }
}
```

单条数据插入（使用基于内容的确定性ID）：
```json
{
  "data": {
    "text": "flight control system",
    "translation": "飞行控制系统"
  },
  "use_content_based_id": true
}
```

批量数据操作（混合更新和插入）：
```json
{
  "data": [
    {
      "id": 123,
      "text": "updated aircraft engine",
      "translation": "更新的航空发动机"
    },
    {
      "text": "new navigation system",
      "translation": "新的导航系统"
    }
  ],
  "partition_name": "aviation_systems"
}
```""",
)
async def upsert_translations(
    request: UpsertRequest,
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    更新或插入翻译数据

    参数:
        request (UpsertRequest): 包含要更新或插入的数据
            - data: 可以是单个字典或字典列表
                单个数据格式: {"id": 可选, "text": "英文", "translation": "中文"}
                批量数据格式: [{"id": 可选, "text": "英文", "translation": "中文"}, ...]
            - partition_name: 可选的分区名称
            - use_content_based_id: 是否为无ID数据生成基于内容的确定性ID

    数据字段说明:
        - id (可选): 记录的主键ID
            * 如果提供且存在，则更新该记录
            * 如果提供但不存在，则插入新记录并使用该ID
            * 如果不提供，则自动生成新ID并插入
        - text (必填): 英文原文
        - translation (必填): 中文翻译
        - create_time (自动): 创建时间戳，插入新记录时自动设置
        - update_time (自动): 更新时间戳，每次upsert操作时自动更新

    使用场景:
        1. 更新现有记录: 提供已存在的ID（使用upsert操作）
        2. 插入新记录: 不提供ID（使用insert操作，自动生成ID）
        3. 插入指定ID: 提供不存在的ID（使用upsert操作）
        4. 批量操作: data传递数组，自动分离有ID和无ID的数据分别处理

    内部处理机制:
        - 有ID的数据使用client.upsert()方法
        - 无ID的数据使用client.insert()方法（避免ID字段缺失错误）
        - 混合数据自动分类处理，确保所有数据都能正确插入或更新

    时间字段自动处理:
        - create_time: 仅在插入新记录时设置，更新现有记录时保持不变
        - update_time: 每次upsert操作都会更新为当前时间戳
        - 时间戳格式: Unix时间戳（秒），可通过搜索API获取datetime格式

    返回:
        UpsertResponse: 包含操作结果和消息的响应
    """
    try:
        start_time = time.time()

        result = importer.upsert_data(
            data=request.data,
            partition_name=request.partition_name,
            use_content_based_id=request.use_content_based_id
        )

        elapsed = time.time() - start_time
        upsert_count = result.get('upsert_count', 0)

        return UpsertResponse(
            success=True,
            message=f"成功upsert {upsert_count} 条记录，耗时 {elapsed:.2f}秒",
            upsert_count=upsert_count,
            collection_name=importer.collection_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upsert数据时出错: {str(e)}")


@app.delete(
    "/data/delete",
    response_model=DeleteResponse,
    tags=["Data Import"],
    summary="删除翻译数据",
    description="""通过主键ID或过滤表达式删除翻译数据。

**请求示例：**

通过ID删除单条记录：
```json
{
  "ids": [123]
}
```

通过ID删除多条记录：
```json
{
  "ids": [123, 456, 789],
  "partition_name": "aviation_engine"
}
```

通过过滤表达式删除：
```json
{
  "filter_expr": "text like 'aircraft%'",
  "partition_name": "aviation_engine"
}
```
```json
{
  "filter_expr": "translation == \"新的导航系统\"",
  "partition_name": "aviation_engine"
}
```

基于时间的过滤条件：
```json
{
  "filter_expr": "create_time > 1640995200",
  "partition_name": "aviation_engine"
}
```

```json
{
  "filter_expr": "update_time >= 1672531200 and update_time <= 1675209600"
}
```

复杂过滤条件（时间+内容）：
```json
{
  "filter_expr": "create_time > 1640995200 and text like 'engine%'"
}
```

```json
{
  "filter_expr": "(update_time > 1672531200 or create_time > 1675209600) and translation like '%系统%'"
}
```""",
)
async def delete_translations(
    request: DeleteRequest,
    importer: AviationTranslationImporter = Depends(get_importer),
):
    """
    删除翻译数据

    参数:
        request (DeleteRequest): 包含删除条件的请求体
            - ids: ID列表，用于删除指定的记录
            - filter_expr: 过滤表达式，用于批量删除满足条件的记录
            - partition_name: 可选的分区名称

    删除方式说明:
        1. 通过ID删除: 提供ids参数，可以是单个ID或ID列表
        2. 通过条件删除: 提供filter_expr参数，支持复杂的过滤条件

    注意事项:
        - ids和filter_expr不能同时提供，必须选择其中一种方式
        - 使用过滤表达式时，集合必须已加载到内存中
        - 支持的过滤操作符: =, !=, >, <, >=, <=, like, in, and, or

    常用过滤表达式示例:
        - "id in [1, 2, 3]" - 删除指定ID的记录
        - "text like 'aircraft%'" - 删除以'aircraft'开头的记录
        - "create_time > 1640995200" - 删除指定时间后创建的记录
        - "update_time >= 1672531200 and update_time <= 1675209600" - 删除指定时间范围内更新的记录
        - "text like 'engine%' and create_time > 1640995200" - 组合条件

    时间筛选说明:
        - 时间字段使用Unix时间戳格式（秒），不支持日期字符串
        - create_time: 记录创建时间，用于筛选创建时间范围
        - update_time: 记录最后更新时间，用于筛选更新时间范围
        - 时间戳转换示例:
            * 2022-01-01 00:00:00 UTC = 1640995200
            * 2023-01-01 00:00:00 UTC = 1672531200
            * 2023-02-01 00:00:00 UTC = 1675209600
        - 支持时间范围查询: 使用 >= 和 <= 组合
        - 可与其他条件组合: 使用 and、or 操作符
        - 在线转换工具: 可使用在线Unix时间戳转换器进行日期转换

    时间筛选说明:
        - 时间字段使用Unix时间戳格式（秒）
        - create_time: 记录创建时间，用于筛选创建时间范围
        - update_time: 记录最后更新时间，用于筛选更新时间范围
        - 时间戳转换: 2022-01-01 00:00:00 UTC = 1640995200
        - 支持时间范围查询: >= 和 <= 组合使用
        - 可与其他条件组合: 使用 and、or 操作符

    返回:
        DeleteResponse: 包含操作结果和消息的响应
    """
    try:
        start_time = time.time()

        result = importer.delete_data(
            ids=request.ids,
            filter_expr=request.filter_expr,
            partition_name=request.partition_name
        )

        elapsed = time.time() - start_time
        delete_count = result.get('delete_count', 0)

        return DeleteResponse(
            success=True,
            message=f"成功删除 {delete_count} 条记录，耗时 {elapsed:.2f}秒",
            delete_count=delete_count,
            collection_name=importer.collection_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除数据时出错: {str(e)}")


# 时间转换工具接口
@app.post(
    "/tools/datetime-to-timestamp",
    response_model=DateTimeToTimestampResponse,
    tags=["Tools"],
    summary="日期时间转时间戳",
    description="""将日期时间字符串转换为Unix时间戳（秒）。

**支持的日期时间格式：**
- "2023-01-01"
- "2023-01-01 12:30:00"
- "2023-01-01T12:30:00"
- "2023-01-01T12:30:00Z"
- "2023-01-01T12:30:00+08:00"

**请求示例：**

基本日期转换：
```json
{
  "datetime_str": "2023-01-01"
}
```

带时区的日期时间转换：
```json
{
  "datetime_str": "2023-01-01 12:30:00",
  "timezone_offset": "+08:00"
}
```

ISO格式转换：
```json
{
  "datetime_str": "2023-01-01T12:30:00Z"
}
```""",
)
async def datetime_to_timestamp(request: DateTimeToTimestampRequest):
    """
    将日期时间字符串转换为Unix时间戳

    参数:
        request (DateTimeToTimestampRequest): 包含日期时间字符串和可选时区偏移的请求体

    返回:
        DateTimeToTimestampResponse: 包含转换结果的响应
    """
    try:
        parsed_dt, timezone_used = parse_datetime_string(
            request.datetime_str,
            request.timezone_offset
        )
        timestamp = int(parsed_dt.timestamp())

        return DateTimeToTimestampResponse(
            success=True,
            datetime_str=request.datetime_str,
            timestamp=timestamp,
            timezone_used=timezone_used
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"日期时间转换失败: {str(e)}")


@app.post(
    "/tools/timestamp-to-datetime",
    response_model=TimestampToDateTimeResponse,
    tags=["Tools"],
    summary="时间戳转日期时间",
    description="""将Unix时间戳（秒）转换为日期时间字符串。

**请求示例：**

基本时间戳转换：
```json
{
  "timestamp": 1672531200
}
```

指定时区的转换：
```json
{
  "timestamp": 1672531200,
  "timezone_offset": "+08:00"
}
```

**响应说明：**
- datetime_str: 人类可读的日期时间字符串
- iso_format: ISO 8601标准格式
- timezone_used: 使用的时区""",
)
async def timestamp_to_datetime(request: TimestampToDateTimeRequest):
    """
    将Unix时间戳转换为日期时间字符串

    参数:
        request (TimestampToDateTimeRequest): 包含时间戳和可选时区偏移的请求体

    返回:
        TimestampToDateTimeResponse: 包含转换结果的响应
    """
    try:
        dt, iso_format, timezone_used = format_datetime_with_timezone(
            request.timestamp,
            request.timezone_offset
        )

        # 生成人类可读的日期时间字符串
        datetime_str = dt.strftime("%Y-%m-%d %H:%M:%S %Z").strip()
        if not datetime_str.endswith('UTC') and not datetime_str.endswith('+') and not datetime_str.endswith('-'):
            datetime_str += f" ({timezone_used})"

        return TimestampToDateTimeResponse(
            success=True,
            timestamp=request.timestamp,
            datetime_str=datetime_str,
            iso_format=iso_format,
            timezone_used=timezone_used
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"时间戳转换失败: {str(e)}")


@app.post(
    "/tools/time-range-to-filter",
    response_model=TimeRangeResponse,
    tags=["Tools"],
    summary="时间范围转过滤表达式",
    description="""将日期范围转换为Milvus过滤表达式。

**请求示例：**

基本日期范围：
```json
{
  "start_date": "2023-01-01",
  "end_date": "2023-01-31"
}
```

带时区的日期范围：
```json
{
  "start_date": "2023-01-01 00:00:00",
  "end_date": "2023-01-31 23:59:59",
  "timezone_offset": "+08:00"
}
```

**用途：**
生成的过滤表达式可直接用于delete API的filter_expr参数。""",
)
async def time_range_to_filter(request: TimeRangeRequest):
    """
    将时间范围转换为Milvus过滤表达式

    参数:
        request (TimeRangeRequest): 包含开始和结束日期的请求体

    返回:
        TimeRangeResponse: 包含时间戳和过滤表达式的响应
    """
    try:
        # 解析开始时间（设为当天开始）
        start_dt_str = request.start_date
        if len(start_dt_str) == 10:  # 只有日期
            start_dt_str += " 00:00:00"
        start_dt, start_tz = parse_datetime_string(start_dt_str, request.timezone_offset)
        start_timestamp = int(start_dt.timestamp())

        # 解析结束时间（设为当天结束）
        end_dt_str = request.end_date
        if len(end_dt_str) == 10:  # 只有日期
            end_dt_str += " 23:59:59"
        end_dt, end_tz = parse_datetime_string(end_dt_str, request.timezone_offset)
        end_timestamp = int(end_dt.timestamp())

        # 生成过滤表达式
        filter_expression = f"create_time >= {start_timestamp} and create_time <= {end_timestamp}"

        return TimeRangeResponse(
            success=True,
            start_date=request.start_date,
            end_date=request.end_date,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            filter_expression=filter_expression,
            timezone_used=start_tz
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"时间范围转换失败: {str(e)}")


@app.get(
    "/tools/filter-examples",
    response_model=FilterExamplesResponse,
    tags=["Tools"],
    summary="获取时间过滤示例",
    description="""获取常用的时间过滤表达式示例和时间戳对照表。

**返回内容：**
- 常用过滤表达式示例
- 重要时间点的时间戳对照表
- 使用技巧和注意事项

**用途：**
帮助用户快速了解和使用时间过滤功能。""",
)
async def get_filter_examples():
    """
    获取时间过滤表达式示例

    返回:
        FilterExamplesResponse: 包含示例和使用技巧的响应
    """
    try:
        current_time = int(time.time())
        one_day_ago = current_time - 86400
        one_week_ago = current_time - 604800
        one_month_ago = current_time - 2592000

        # 常用过滤表达式示例
        examples = {
            "删除最近24小时创建的记录": f"create_time > {one_day_ago}",
            "删除最近7天更新的记录": f"update_time > {one_week_ago}",
            "删除最近30天的记录": f"create_time > {one_month_ago}",
            "删除2023年创建的记录": "create_time >= 1672531200 and create_time < 1704067200",
            "删除指定时间范围的记录": "create_time >= 1672531200 and create_time <= 1675209600",
            "删除创建但从未更新的记录": "create_time = update_time",
            "删除包含特定文本且时间较旧的记录": "text like '%engine%' and create_time < 1672531200",
            "删除更新时间晚于创建时间1年以上的记录": "update_time - create_time > 31536000"
        }

        # 常用时间戳对照表
        common_timestamps = {
            "2022-01-01 00:00:00 UTC": 1640995200,
            "2023-01-01 00:00:00 UTC": 1672531200,
            "2023-06-01 00:00:00 UTC": 1685577600,
            "2024-01-01 00:00:00 UTC": 1704067200,
            "2025-01-01 00:00:00 UTC": 1735689600,
            "当前时间": current_time,
            "24小时前": one_day_ago,
            "7天前": one_week_ago,
            "30天前": one_month_ago
        }

        # 使用技巧
        usage_tips = [
            "时间字段只支持Unix时间戳格式（秒），不支持日期字符串",
            "create_time记录创建时间，update_time记录最后更新时间",
            "使用 >= 和 <= 进行时间范围查询",
            "可以使用 and、or 操作符组合多个条件",
            "时间戳转换可使用本API的转换工具",
            "过滤表达式区分大小写，字段名必须准确",
            "建议先在小数据集上测试过滤表达式",
            "删除操作不可逆，请谨慎使用"
        ]

        return FilterExamplesResponse(
            success=True,
            examples=examples,
            common_timestamps=common_timestamps,
            usage_tips=usage_tips
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取示例失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
