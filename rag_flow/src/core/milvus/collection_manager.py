"""
模块名称: collection_manager
功能描述: Milvus Collection管理服务，提供Collection创建、分区管理、索引管理等功能
创建日期: 2025-06-14
作者: Sniperz
版本: v1.0.0
"""

import time
import logging
from typing import List, Dict, Optional, Any, Union
from pathlib import Path
from pymilvus import MilvusClient, DataType, Function, FunctionType, CollectionSchema, FieldSchema

# 导入日志管理器
from ...utils.logger import SZ_LoggerManager

# 配置日志
logger = SZ_LoggerManager.setup_logger(__name__, log_file="milvus_collection.log")

# 常量配置
DEFAULT_MILVUS_URI = "http://124.71.148.16:19530"
DEFAULT_TOKEN = "root:Milvus"
DEFAULT_TEMP_DIR = "./milvus_temp"


class MilvusCollectionManager:
    """
    Milvus Collection管理服务类
    
    提供Collection的创建、删除、分区管理、索引管理等核心功能。
    支持动态Schema配置和多种数据类型的Collection创建。
    
    Attributes:
        client_uri (str): Milvus服务的URI
        client (MilvusClient): Milvus客户端实例
        token (str): Milvus服务的认证令牌
        temp_dir (str): 临时文件目录路径
    """
    
    def __init__(
        self,
        uri: str = DEFAULT_MILVUS_URI,
        token: str = DEFAULT_TOKEN,
        temp_dir: str = DEFAULT_TEMP_DIR
    ):
        """
        初始化MilvusCollectionManager实例
        
        Args:
            uri (str): Milvus服务的URI
            token (str): Milvus服务的认证令牌
            temp_dir (str): 临时文件目录
        """
        self.client_uri = uri
        self.token = token
        self.client = MilvusClient(uri=uri, token=token)
        self.temp_dir = temp_dir
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"MilvusCollectionManager初始化完成，连接到: {uri}")
    
    def create_aviation_collection(
        self,
        collection_name: str,
        schema_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        创建航空文档Collection
        
        支持自定义Schema配置，默认创建包含文本、向量、元数据字段的Collection。
        为文本字段启用BM25函数以支持全文搜索。
        
        Args:
            collection_name (str): Collection名称
            schema_config (Optional[Dict[str, Any]]): 自定义Schema配置
                
        Raises:
            Exception: 如果创建Collection过程中发生Milvus客户端错误
        """
        if collection_name in self.client.list_collections():
            logger.info(f"Collection {collection_name} 已存在")
            return
        
        # 使用默认航空文档Schema或自定义Schema
        if schema_config is None:
            schema_config = self._get_default_aviation_schema()
        
        schema = self._build_collection_schema(schema_config)
        index_params = self._build_index_params(schema_config)
        
        self.client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params,
            auto_id=True
        )
        
        logger.info(f"航空文档Collection {collection_name} 创建成功")
    
    def _get_default_aviation_schema(self) -> Dict[str, Any]:
        """
        获取默认的航空文档Schema配置
        
        Returns:
            Dict[str, Any]: 默认Schema配置
        """
        return {
            "auto_id": True,
            "enable_dynamic_field": False,
            "fields": [
                {
                    "name": "id",
                    "datatype": "INT64",
                    "is_primary": True,
                    "description": "主键ID"
                },
                {
                    "name": "document_title",
                    "datatype": "VARCHAR",
                    "max_length": 500,
                    "enable_analyzer": True,
                    "enable_match": True,
                    "analyzer_params": {"type": "english"},
                    "description": "文档标题"
                },
                {
                    "name": "document_content",
                    "datatype": "VARCHAR", 
                    "max_length": 8000,
                    "enable_analyzer": True,
                    "enable_match": True,
                    "analyzer_params": {"type": "english"},
                    "description": "文档内容"
                },
                {
                    "name": "content_vector",
                    "datatype": "SPARSE_FLOAT_VECTOR",
                    "description": "内容向量"
                },
                {
                    "name": "document_type",
                    "datatype": "VARCHAR",
                    "max_length": 100,
                    "description": "文档类型"
                },
                {
                    "name": "compliance_level",
                    "datatype": "VARCHAR",
                    "max_length": 50,
                    "description": "合规等级"
                },
                {
                    "name": "create_time",
                    "datatype": "INT64",
                    "description": "创建时间戳"
                },
                {
                    "name": "update_time",
                    "datatype": "INT64", 
                    "description": "更新时间戳"
                }
            ],
            "functions": [
                {
                    "name": "bm25_title_func",
                    "input_fields": ["document_title"],
                    "output_fields": ["title_vector"],
                    "function_type": "BM25"
                },
                {
                    "name": "bm25_content_func", 
                    "input_fields": ["document_content"],
                    "output_fields": ["content_vector"],
                    "function_type": "BM25"
                }
            ],
            "indexes": [
                {
                    "field_name": "content_vector",
                    "index_type": "SPARSE_INVERTED_INDEX",
                    "metric_type": "BM25",
                    "params": {
                        "inverted_index_algo": "DAAT_WAND",
                        "bm25_k1": 1.8,
                        "bm25_b": 0.75
                    }
                }
            ]
        }
    
    def _build_collection_schema(self, schema_config: Dict[str, Any]) -> CollectionSchema:
        """
        根据配置构建Collection Schema
        
        Args:
            schema_config (Dict[str, Any]): Schema配置
            
        Returns:
            CollectionSchema: 构建的Schema对象
        """
        schema = MilvusClient.create_schema(
            auto_id=schema_config.get("auto_id", True),
            enable_dynamic_field=schema_config.get("enable_dynamic_field", False)
        )
        
        # 添加字段
        for field_config in schema_config.get("fields", []):
            self._add_field_to_schema(schema, field_config)
        
        # 添加函数
        for func_config in schema_config.get("functions", []):
            self._add_function_to_schema(schema, func_config)
        
        return schema
    
    def _add_field_to_schema(self, schema: CollectionSchema, field_config: Dict[str, Any]) -> None:
        """
        向Schema添加字段
        
        Args:
            schema (CollectionSchema): Schema对象
            field_config (Dict[str, Any]): 字段配置
        """
        field_params = {
            "field_name": field_config["name"],
            "datatype": getattr(DataType, field_config["datatype"])
        }
        
        # 添加可选参数
        optional_params = [
            "max_length", "is_primary", "auto_id", "description",
            "enable_analyzer", "enable_match", "analyzer_params"
        ]
        
        for param in optional_params:
            if param in field_config:
                field_params[param] = field_config[param]
        
        schema.add_field(**field_params)

    def _add_function_to_schema(self, schema: CollectionSchema, func_config: Dict[str, Any]) -> None:
        """
        向Schema添加函数

        Args:
            schema (CollectionSchema): Schema对象
            func_config (Dict[str, Any]): 函数配置
        """
        function = Function(
            name=func_config["name"],
            input_field_names=func_config["input_fields"],
            output_field_names=func_config["output_fields"],
            function_type=getattr(FunctionType, func_config["function_type"])
        )
        schema.add_function(function)

    def _build_index_params(self, schema_config: Dict[str, Any]):
        """
        根据配置构建索引参数

        Args:
            schema_config (Dict[str, Any]): Schema配置

        Returns:
            索引参数对象
        """
        index_params = MilvusClient.prepare_index_params()

        for index_config in schema_config.get("indexes", []):
            index_params.add_index(
                field_name=index_config["field_name"],
                index_type=index_config["index_type"],
                metric_type=index_config["metric_type"],
                params=index_config.get("params", {})
            )

        return index_params

    def create_partition(self, collection_name: str, partition_name: str) -> None:
        """
        在Collection中创建分区

        Args:
            collection_name (str): Collection名称
            partition_name (str): 分区名称

        Raises:
            Exception: 如果创建分区过程中发生Milvus客户端错误
        """
        try:
            if not self.client.has_collection(collection_name):
                raise ValueError(f"Collection {collection_name} 不存在")

            if not self.client.has_partition(collection_name, partition_name):
                self.client.create_partition(
                    collection_name=collection_name,
                    partition_name=partition_name
                )
                logger.info(f"分区 {partition_name} 在Collection {collection_name} 中创建成功")
            else:
                logger.info(f"分区 {partition_name} 在Collection {collection_name} 中已存在")

        except Exception as e:
            logger.error(f"创建分区时发生错误: {e}")
            raise

    def drop_partition(self, collection_name: str, partition_name: str, timeout: Optional[float] = None) -> bool:
        """
        删除指定的分区

        Args:
            collection_name (str): Collection名称
            partition_name (str): 分区名称
            timeout (Optional[float]): 操作超时时间

        Returns:
            bool: 删除是否成功
        """
        try:
            if not self.client.has_partition(collection_name, partition_name):
                logger.info(f"分区 {partition_name} 不存在于Collection {collection_name} 中")
                return True

            # 检查分区加载状态并释放
            load_state = self.client.get_load_state(
                collection_name=collection_name,
                partition_name=partition_name
            )

            if load_state.get('state') == 3:  # LoadState.Loaded
                logger.info(f"分区 {partition_name} 处于加载状态，正在释放...")
                self.client.release_partitions(
                    collection_name=collection_name,
                    partition_names=[partition_name]
                )

            # 删除分区
            self.client.drop_partition(
                collection_name=collection_name,
                partition_name=partition_name,
                timeout=timeout
            )

            logger.info(f"分区 {partition_name} 删除成功")
            return True

        except Exception as e:
            logger.error(f"删除分区 {partition_name} 时发生错误: {e}")
            return False

    def load_collection(self, collection_name: str, load_fields: Optional[List[str]] = None) -> None:
        """
        加载Collection到内存

        Args:
            collection_name (str): Collection名称
            load_fields (Optional[List[str]]): 指定要加载的字段

        Raises:
            Exception: 如果加载Collection过程中发生错误
        """
        logger.info(f"开始加载Collection {collection_name}...")

        load_params = {"collection_name": collection_name}
        if load_fields:
            load_params["load_fields"] = load_fields

        self.client.load_collection(**load_params)

        load_state = self.client.get_load_state(collection_name=collection_name)
        logger.info(f"Collection {collection_name} 加载完成，状态: {load_state}")

    def release_collection(self, collection_name: str) -> None:
        """
        从内存中释放Collection

        Args:
            collection_name (str): Collection名称

        Raises:
            Exception: 如果释放Collection过程中发生错误
        """
        logger.info(f"开始释放Collection {collection_name}...")
        self.client.release_collection(collection_name=collection_name)

        load_state = self.client.get_load_state(collection_name=collection_name)
        logger.info(f"Collection {collection_name} 释放完成，状态: {load_state}")

    def delete_collection(self, collection_name: str) -> None:
        """
        删除Collection

        Args:
            collection_name (str): Collection名称

        Raises:
            Exception: 如果删除Collection过程中发生错误
        """
        try:
            if collection_name in self.client.list_collections():
                self.client.drop_collection(collection_name)
                logger.info(f"Collection {collection_name} 删除成功")
            else:
                logger.info(f"Collection {collection_name} 不存在")
        except Exception as e:
            logger.error(f"删除Collection时发生错误: {e}")
            raise

    def describe_collection(self, collection_name: str) -> Dict[str, Any]:
        """
        获取Collection的详细描述信息

        Args:
            collection_name (str): Collection名称

        Returns:
            Dict[str, Any]: Collection详细信息

        Raises:
            Exception: 如果获取Collection描述过程中发生错误
        """
        try:
            logger.info(f"获取Collection {collection_name} 的详细描述")

            collection_info = self.client.describe_collection(collection_name)
            load_status_raw = self.client.get_load_state(collection_name=collection_name)

            if isinstance(load_status_raw, dict) and 'state' in load_status_raw:
                load_status_str = str(load_status_raw.get('state'))
            else:
                load_status_str = str(load_status_raw)

            collection_info["load_status"] = load_status_str

            logger.info(f"成功获取Collection {collection_name} 的详细描述")
            return collection_info

        except Exception as e:
            logger.error(f"获取Collection描述时出错: {e}")
            raise

    def get_health_info(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取Milvus服务和Collection的健康状态信息

        Args:
            collection_name (Optional[str]): 要检查的Collection名称

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            collections = self.client.list_collections()

            if collection_name:
                collection_exists = collection_name in collections
                num_entities = 0
                if collection_exists:
                    stats = self.client.get_collection_stats(collection_name=collection_name)
                    num_entities = stats.get("row_count", 0) if isinstance(stats, dict) else stats

                return {
                    "status": "healthy" if collection_exists else "unhealthy",
                    "milvus_connected": True,
                    "collection_name": collection_name,
                    "collection_exists": collection_exists,
                    "collection_entities": num_entities
                }
            else:
                return {
                    "status": "healthy" if collections else "unhealthy",
                    "milvus_connected": True,
                    "total_collections": len(collections),
                    "collection_list": collections
                }

        except Exception as e:
            logger.error(f"获取健康状态信息时出错: {e}")
            return {
                "status": "unhealthy",
                "milvus_connected": False,
                "error": str(e)
            }
