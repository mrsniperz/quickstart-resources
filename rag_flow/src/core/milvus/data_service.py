"""
模块名称: data_service
功能描述: Milvus数据操作服务，提供数据插入、更新、删除、批量操作等功能
创建日期: 2025-06-14
作者: Sniperz
版本: v1.0.0
"""

import time
import hashlib
from typing import List, Dict, Optional, Any, Union
from pymilvus import MilvusClient

# 导入日志管理器
from ...utils.logger import SZ_LoggerManager

# 配置日志
logger = SZ_LoggerManager.setup_logger(__name__, log_file="milvus_data.log")


class MilvusDataService:
    """
    Milvus数据操作服务类
    
    提供数据的插入、更新、删除、批量操作等功能。
    支持单条和批量操作，以及基于内容的ID生成。
    
    Attributes:
        client (MilvusClient): Milvus客户端实例
        chunk_size (int): 批量操作的分块大小
    """
    
    def __init__(self, client: MilvusClient, chunk_size: int = 10000):
        """
        初始化MilvusDataService实例
        
        Args:
            client (MilvusClient): Milvus客户端实例
            chunk_size (int): 批量操作的分块大小
        """
        self.client = client
        self.chunk_size = chunk_size
        logger.info("MilvusDataService初始化完成")
    
    def insert_data(
        self,
        collection_name: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        partition_name: Optional[str] = None,
        add_timestamps: bool = True
    ) -> Dict[str, Any]:
        """
        插入数据到Collection
        
        Args:
            collection_name (str): Collection名称
            data (Union[Dict[str, Any], List[Dict[str, Any]]]): 要插入的数据
            partition_name (Optional[str]): 目标分区名称
            add_timestamps (bool): 是否自动添加时间戳
            
        Returns:
            Dict[str, Any]: 插入操作结果
            
        Raises:
            Exception: 如果插入过程中发生错误
        """
        try:
            start_time = time.time()
            
            # 确保Collection存在
            if not self.client.has_collection(collection_name):
                raise ValueError(f"Collection {collection_name} 不存在")
            
            # 标准化数据格式
            if isinstance(data, dict):
                data_list = [data]
            else:
                data_list = data
            
            # 添加时间戳
            if add_timestamps:
                current_time = int(time.time())
                for item in data_list:
                    if "create_time" not in item:
                        item["create_time"] = current_time
                    if "update_time" not in item:
                        item["update_time"] = current_time
            
            # 分批插入数据
            total_records = len(data_list)
            inserted_count = 0
            
            for i in range(0, total_records, self.chunk_size):
                chunk = data_list[i:i+self.chunk_size]
                
                insert_params = {
                    "collection_name": collection_name,
                    "data": chunk
                }
                if partition_name:
                    insert_params["partition_name"] = partition_name
                
                result = self.client.insert(**insert_params)
                chunk_count = result.get('insert_count', len(chunk))
                inserted_count += chunk_count
                
                logger.info(f"已插入 {i+len(chunk)}/{total_records} 条记录")
            
            elapsed_time = time.time() - start_time
            logger.info(f"数据插入完成，总计 {inserted_count} 条记录，耗时: {elapsed_time:.4f}秒")
            
            return {
                "insert_count": inserted_count,
                "total_records": total_records,
                "elapsed_time": elapsed_time
            }
            
        except Exception as e:
            logger.error(f"插入数据时出错: {e}")
            raise
    
    def upsert_data(
        self,
        collection_name: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        partition_name: Optional[str] = None,
        use_content_based_id: bool = False
    ) -> Dict[str, Any]:
        """
        更新或插入数据到Collection
        
        如果数据中的主键已存在，则更新该记录；如果不存在，则插入新记录。
        
        Args:
            collection_name (str): Collection名称
            data (Union[Dict[str, Any], List[Dict[str, Any]]]): 要更新或插入的数据
            partition_name (Optional[str]): 目标分区名称
            use_content_based_id (bool): 是否为没有ID的数据生成基于内容的确定性ID
            
        Returns:
            Dict[str, Any]: 操作结果
            
        Raises:
            Exception: 如果upsert过程中发生错误
        """
        try:
            start_time = time.time()
            
            # 确保Collection存在
            if not self.client.has_collection(collection_name):
                raise ValueError(f"Collection {collection_name} 不存在")
            
            # 标准化数据格式
            if isinstance(data, dict):
                data_list = [data]
            else:
                data_list = data
            
            # 添加时间戳并分离有ID和无ID的数据
            current_time = int(time.time())
            data_with_id = []
            data_without_id = []
            
            for item in data_list:
                # 添加/更新时间戳
                if "create_time" not in item:
                    item["create_time"] = current_time
                item["update_time"] = current_time
                
                # 根据是否有ID分类
                if "id" in item and item["id"] is not None:
                    data_with_id.append(item)
                else:
                    # 如果启用基于内容的ID生成
                    if use_content_based_id and self._can_generate_content_id(item):
                        content_id = self._generate_content_based_id(item)
                        item["id"] = content_id
                        data_with_id.append(item)
                        logger.debug(f"为内容生成ID: {content_id}")
                    else:
                        data_without_id.append(item)
            
            total_count = 0
            inserted_ids = []
            
            # 处理有ID的数据 - 使用upsert
            if data_with_id:
                upsert_params = {
                    "collection_name": collection_name,
                    "data": data_with_id
                }
                if partition_name:
                    upsert_params["partition_name"] = partition_name
                
                upsert_result = self.client.upsert(**upsert_params)
                upsert_count = upsert_result.get('upsert_count', len(data_with_id))
                total_count += upsert_count
                logger.info(f"成功upsert {upsert_count} 条有ID的记录")
            
            # 处理无ID的数据 - 使用insert
            if data_without_id:
                insert_params = {
                    "collection_name": collection_name,
                    "data": data_without_id
                }
                if partition_name:
                    insert_params["partition_name"] = partition_name
                
                insert_result = self.client.insert(**insert_params)
                insert_count = insert_result.get('insert_count', len(data_without_id))
                total_count += insert_count
                
                if 'ids' in insert_result:
                    inserted_ids = insert_result['ids']
                    logger.info(f"成功insert {insert_count} 条无ID的记录，生成的ID: {inserted_ids[:5]}...")
                else:
                    logger.info(f"成功insert {insert_count} 条无ID的记录")
            
            elapsed_time = time.time() - start_time
            logger.info(f"Upsert操作完成，总计处理 {total_count} 条记录，耗时: {elapsed_time:.4f}秒")
            
            result = {
                "upsert_count": total_count,
                "elapsed_time": elapsed_time
            }
            if inserted_ids:
                result["inserted_ids"] = inserted_ids
            
            return result
            
        except Exception as e:
            logger.error(f"Upsert数据时出错: {e}")
            raise
    
    def delete_data(
        self,
        collection_name: str,
        ids: Optional[Union[List[Union[str, int]], str, int]] = None,
        filter_expr: Optional[str] = None,
        partition_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从Collection中删除数据
        
        可以通过主键ID或过滤表达式来删除数据。这是从原始代码中提取的通用化版本。
        
        Args:
            collection_name (str): Collection名称
            ids (Optional[Union[List[Union[str, int]], str, int]]): 要删除的实体ID或ID列表
            filter_expr (Optional[str]): 过滤表达式，用于批量删除满足条件的实体
            partition_name (Optional[str]): 目标分区名称，如果为None则在所有分区中删除
            
        Returns:
            Dict[str, Any]: 包含操作结果的字典，包含delete_count字段
            
        Raises:
            ValueError: 如果既没有提供ids也没有提供filter_expr，或者Collection不存在
            Exception: 如果删除过程中发生Milvus客户端错误
        """
        try:
            start_time = time.time()
            
            # 检查参数
            if ids is None and filter_expr is None:
                raise ValueError("必须提供ids或filter_expr中的至少一个参数")
            
            if ids is not None and filter_expr is not None:
                raise ValueError("不能同时提供ids和filter_expr参数")
            
            # 确保Collection存在
            if not self.client.has_collection(collection_name):
                raise ValueError(f"Collection {collection_name} 不存在")
            
            # 构建删除参数
            delete_params = {
                "collection_name": collection_name
            }
            
            if partition_name:
                delete_params["partition_name"] = partition_name
            
            if ids is not None:
                # 标准化ID格式
                if isinstance(ids, (str, int)):
                    ids = [ids]
                delete_params["ids"] = ids
                logger.info(f"准备删除ID为 {ids} 的记录")
            else:
                delete_params["filter"] = filter_expr
                logger.info(f"准备删除满足条件 '{filter_expr}' 的记录")
            
            # 执行删除操作
            result = self.client.delete(**delete_params)
            
            delete_count = result.get('delete_count', 0)
            elapsed_time = time.time() - start_time
            
            logger.info(f"成功删除 {delete_count} 条记录从Collection {collection_name}，耗时: {elapsed_time:.4f}秒")
            
            # 增强返回结果
            enhanced_result = result.copy()
            enhanced_result.update({
                "collection_name": collection_name,
                "elapsed_time": elapsed_time,
                "operation_type": "delete_by_ids" if ids is not None else "delete_by_filter"
            })
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"删除数据时出错: {e}")
            raise

    def batch_delete_by_conditions(
        self,
        collection_name: str,
        conditions: List[str],
        partition_name: Optional[str] = None,
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """
        批量按条件删除数据

        Args:
            collection_name (str): Collection名称
            conditions (List[str]): 删除条件列表
            partition_name (Optional[str]): 目标分区名称
            batch_size (int): 批处理大小

        Returns:
            Dict[str, Any]: 批量删除结果
        """
        try:
            start_time = time.time()
            total_deleted = 0
            failed_conditions = []

            for i, condition in enumerate(conditions):
                try:
                    result = self.delete_data(
                        collection_name=collection_name,
                        filter_expr=condition,
                        partition_name=partition_name
                    )
                    deleted_count = result.get('delete_count', 0)
                    total_deleted += deleted_count
                    logger.info(f"条件 {i+1}/{len(conditions)} 删除了 {deleted_count} 条记录")

                except Exception as e:
                    logger.error(f"删除条件 '{condition}' 失败: {e}")
                    failed_conditions.append({"condition": condition, "error": str(e)})

            elapsed_time = time.time() - start_time

            return {
                "total_deleted": total_deleted,
                "processed_conditions": len(conditions),
                "failed_conditions": failed_conditions,
                "success_rate": (len(conditions) - len(failed_conditions)) / len(conditions),
                "elapsed_time": elapsed_time
            }

        except Exception as e:
            logger.error(f"批量删除时出错: {e}")
            raise

    def _can_generate_content_id(self, item: Dict[str, Any]) -> bool:
        """
        检查是否可以为数据项生成基于内容的ID

        Args:
            item (Dict[str, Any]): 数据项

        Returns:
            bool: 是否可以生成内容ID
        """
        # 检查是否有足够的内容字段来生成ID
        content_fields = ["text", "translation", "document_title", "document_content", "content"]
        return any(field in item and item[field] for field in content_fields)

    def _generate_content_based_id(self, item: Dict[str, Any]) -> int:
        """
        基于数据内容生成确定性的ID

        Args:
            item (Dict[str, Any]): 数据项

        Returns:
            int: 基于内容生成的确定性ID
        """
        # 提取内容字段
        content_parts = []
        content_fields = ["text", "translation", "document_title", "document_content", "content"]

        for field in content_fields:
            if field in item and item[field]:
                content_parts.append(str(item[field]).strip())

        # 组合内容
        content = "|".join(content_parts)

        # 生成MD5哈希
        hash_object = hashlib.md5(content.encode('utf-8'))
        # 转换为整数（取前8字节避免过大）
        hash_int = int(hash_object.hexdigest()[:8], 16)
        # 确保是正整数且在合理范围内
        return abs(hash_int) % (2**31 - 1)

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        获取Collection的统计信息

        Args:
            collection_name (str): Collection名称

        Returns:
            Dict[str, Any]: Collection统计信息
        """
        try:
            if not self.client.has_collection(collection_name):
                raise ValueError(f"Collection {collection_name} 不存在")

            stats = self.client.get_collection_stats(collection_name=collection_name)
            load_state = self.client.get_load_state(collection_name=collection_name)

            return {
                "collection_name": collection_name,
                "stats": stats,
                "load_state": load_state,
                "is_loaded": load_state.get("state") == 3
            }

        except Exception as e:
            logger.error(f"获取Collection统计信息时出错: {e}")
            raise

    def validate_data_format(
        self,
        collection_name: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        验证数据格式是否符合Collection Schema

        Args:
            collection_name (str): Collection名称
            data (Union[Dict[str, Any], List[Dict[str, Any]]]): 要验证的数据

        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            # 获取Collection描述
            collection_info = self.client.describe_collection(collection_name)
            fields_info = collection_info.get("fields", [])

            # 创建字段映射
            field_map = {field["name"]: field for field in fields_info}

            # 标准化数据格式
            if isinstance(data, dict):
                data_list = [data]
            else:
                data_list = data

            validation_result = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "validated_count": len(data_list)
            }

            for i, item in enumerate(data_list):
                item_errors = []
                item_warnings = []

                # 检查必需字段
                for field_name, field_info in field_map.items():
                    if field_info.get("is_primary") and field_name not in item:
                        if not field_info.get("auto_id", False):
                            item_errors.append(f"缺少主键字段: {field_name}")

                # 检查字段类型和长度
                for field_name, value in item.items():
                    if field_name in field_map:
                        field_info = field_map[field_name]

                        # 检查VARCHAR字段长度
                        if (field_info.get("type") == "VARCHAR" and
                            isinstance(value, str) and
                            "max_length" in field_info):
                            max_length = field_info["max_length"]
                            if len(value) > max_length:
                                item_errors.append(
                                    f"字段 {field_name} 长度 {len(value)} 超过最大限制 {max_length}"
                                )
                    else:
                        item_warnings.append(f"未知字段: {field_name}")

                if item_errors:
                    validation_result["errors"].append({
                        "item_index": i,
                        "errors": item_errors
                    })
                    validation_result["is_valid"] = False

                if item_warnings:
                    validation_result["warnings"].append({
                        "item_index": i,
                        "warnings": item_warnings
                    })

            return validation_result

        except Exception as e:
            logger.error(f"验证数据格式时出错: {e}")
            raise
