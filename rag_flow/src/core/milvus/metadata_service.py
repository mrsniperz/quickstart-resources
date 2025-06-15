"""
模块名称: metadata_service
功能描述: Milvus元数据关联服务，提供PostgreSQL集成、元数据缓存等功能
创建日期: 2025-06-14
作者: Sniperz
版本: v1.0.0
"""

import time
from typing import List, Dict, Optional, Any, Union
from pymilvus import MilvusClient

# 导入日志管理器
from ...utils.logger import SZ_LoggerManager

# 配置日志
logger = SZ_LoggerManager.setup_logger(__name__, log_file="milvus_metadata.log")


class MilvusMetadataService:
    """
    Milvus元数据关联服务类
    
    提供向量ID与文档ID映射、元数据补全、复合查询等功能。
    支持PostgreSQL集成和元数据缓存策略。
    
    Attributes:
        client (MilvusClient): Milvus客户端实例
        metadata_cache (Dict[str, Any]): 元数据缓存
    """
    
    def __init__(self, client: MilvusClient):
        """
        初始化MilvusMetadataService实例
        
        Args:
            client (MilvusClient): Milvus客户端实例
        """
        self.client = client
        self.metadata_cache = {}
        logger.info("MilvusMetadataService初始化完成")
    
    def enrich_search_results_with_metadata(
        self,
        collection_name: str,
        search_results: List[Dict[str, Any]],
        metadata_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        为检索结果补全元数据信息
        
        Args:
            collection_name (str): Collection名称
            search_results (List[Dict[str, Any]]): 检索结果列表
            metadata_fields (Optional[List[str]]): 需要补全的元数据字段
            
        Returns:
            List[Dict[str, Any]]: 补全元数据后的结果列表
            
        Raises:
            Exception: 如果元数据补全过程中发生错误
        """
        try:
            if not search_results:
                return search_results
            
            start_time = time.time()
            
            # 提取需要查询元数据的实体ID
            entity_ids = [result.get("id") for result in search_results if result.get("id")]
            
            if not entity_ids:
                logger.warning("检索结果中没有有效的实体ID")
                return search_results
            
            # 查询元数据
            metadata_map = self._get_metadata_by_ids(
                collection_name, entity_ids, metadata_fields
            )
            
            # 为检索结果补全元数据
            enriched_results = []
            for result in search_results:
                entity_id = result.get("id")
                if entity_id and entity_id in metadata_map:
                    # 合并原始结果和元数据
                    enriched_result = result.copy()
                    enriched_result["metadata"] = metadata_map[entity_id]
                    enriched_results.append(enriched_result)
                else:
                    enriched_results.append(result)
            
            elapsed_time = time.time() - start_time
            logger.info(f"元数据补全完成，耗时: {elapsed_time:.4f}秒")
            
            return enriched_results
            
        except Exception as e:
            logger.error(f"元数据补全时出错: {e}")
            raise
    
    def _get_metadata_by_ids(
        self,
        collection_name: str,
        entity_ids: List[Union[str, int]],
        metadata_fields: Optional[List[str]] = None
    ) -> Dict[Union[str, int], Dict[str, Any]]:
        """
        根据实体ID批量获取元数据
        
        Args:
            collection_name (str): Collection名称
            entity_ids (List[Union[str, int]]): 实体ID列表
            metadata_fields (Optional[List[str]]): 需要获取的元数据字段
            
        Returns:
            Dict[Union[str, int], Dict[str, Any]]: ID到元数据的映射
        """
        metadata_map = {}
        
        try:
            # 检查缓存
            cached_ids = []
            uncached_ids = []
            
            for entity_id in entity_ids:
                cache_key = f"{collection_name}:{entity_id}"
                if cache_key in self.metadata_cache:
                    metadata_map[entity_id] = self.metadata_cache[cache_key]
                    cached_ids.append(entity_id)
                else:
                    uncached_ids.append(entity_id)
            
            logger.info(f"元数据缓存命中: {len(cached_ids)}/{len(entity_ids)}")
            
            # 查询未缓存的元数据
            if uncached_ids:
                # 构建查询条件
                if len(uncached_ids) == 1:
                    filter_expr = f"id == {uncached_ids[0]}"
                else:
                    id_str = ", ".join([str(id_val) for id_val in uncached_ids])
                    filter_expr = f"id in [{id_str}]"
                
                # 执行查询
                results = self.client.query(
                    collection_name=collection_name,
                    filter=filter_expr,
                    output_fields=metadata_fields,
                    limit=len(uncached_ids)
                )
                
                # 处理查询结果并更新缓存
                for result in results:
                    entity_id = result.get("id")
                    if entity_id:
                        metadata_map[entity_id] = result
                        cache_key = f"{collection_name}:{entity_id}"
                        self.metadata_cache[cache_key] = result
            
            return metadata_map
            
        except Exception as e:
            logger.error(f"获取元数据时出错: {e}")
            return metadata_map
    
    def complex_query_with_metadata(
        self,
        collection_name: str,
        vector_query: Optional[Dict[str, Any]] = None,
        metadata_filter: Optional[str] = None,
        limit: int = 10,
        output_fields: Optional[List[str]] = None,
        partition_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        执行复合查询（向量检索 + 元数据过滤）
        
        Args:
            collection_name (str): Collection名称
            vector_query (Optional[Dict[str, Any]]): 向量查询参数
            metadata_filter (Optional[str]): 元数据过滤表达式
            limit (int): 返回结果数量限制
            output_fields (Optional[List[str]]): 输出字段列表
            partition_names (Optional[List[str]]): 分区名称列表
            
        Returns:
            List[Dict[str, Any]]: 复合查询结果列表
            
        Raises:
            Exception: 如果查询过程中发生错误
        """
        try:
            start_time = time.time()
            
            if vector_query:
                # 执行向量检索
                results = self.client.search(
                    collection_name=collection_name,
                    data=vector_query.get("vectors", []),
                    anns_field=vector_query.get("field", ""),
                    search_params=vector_query.get("params", {}),
                    limit=limit,
                    expr=metadata_filter,
                    output_fields=output_fields,
                    partition_names=partition_names
                )
                
                # 格式化向量检索结果
                formatted_results = []
                if results and results[0]:
                    for hit in results[0]:
                        formatted_results.append({
                            "id": hit.entity.get("id"),
                            "score": hit.distance,
                            "entity": hit.entity
                        })
            else:
                # 仅执行元数据查询
                if not metadata_filter:
                    raise ValueError("必须提供vector_query或metadata_filter中的至少一个")
                
                results = self.client.query(
                    collection_name=collection_name,
                    filter=metadata_filter,
                    output_fields=output_fields,
                    partition_names=partition_names,
                    limit=limit
                )
                
                # 格式化查询结果
                formatted_results = [
                    {
                        "id": item.get("id"),
                        "score": None,
                        "entity": item
                    }
                    for item in results
                ]
            
            elapsed_time = time.time() - start_time
            logger.info(f"复合查询完成，耗时: {elapsed_time:.4f}秒，返回 {len(formatted_results)} 条结果")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"复合查询时出错: {e}")
            raise
    
    def aggregate_query_results(
        self,
        collection_name: str,
        filter_expr: str,
        group_by_field: str,
        aggregate_fields: Optional[List[str]] = None,
        partition_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        执行聚合查询
        
        Args:
            collection_name (str): Collection名称
            filter_expr (str): 过滤表达式
            group_by_field (str): 分组字段
            aggregate_fields (Optional[List[str]]): 聚合字段列表
            partition_names (Optional[List[str]]): 分区名称列表
            
        Returns:
            Dict[str, Any]: 聚合查询结果
            
        Raises:
            Exception: 如果聚合查询过程中发生错误
        """
        try:
            start_time = time.time()
            
            # 查询原始数据
            output_fields = [group_by_field]
            if aggregate_fields:
                output_fields.extend(aggregate_fields)
            
            results = self.client.query(
                collection_name=collection_name,
                filter=filter_expr,
                output_fields=output_fields,
                partition_names=partition_names,
                limit=10000  # 设置较大的限制以获取所有匹配数据
            )
            
            # 执行聚合计算
            aggregated_data = self._perform_aggregation(results, group_by_field, aggregate_fields)
            
            elapsed_time = time.time() - start_time
            logger.info(f"聚合查询完成，耗时: {elapsed_time:.4f}秒")
            
            return aggregated_data
            
        except Exception as e:
            logger.error(f"聚合查询时出错: {e}")
            raise
    
    def _perform_aggregation(
        self,
        results: List[Dict[str, Any]],
        group_by_field: str,
        aggregate_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        执行聚合计算
        
        Args:
            results (List[Dict[str, Any]]): 查询结果
            group_by_field (str): 分组字段
            aggregate_fields (Optional[List[str]]): 聚合字段列表
            
        Returns:
            Dict[str, Any]: 聚合结果
        """
        groups = {}
        
        for result in results:
            group_value = result.get(group_by_field)
            if group_value not in groups:
                groups[group_value] = {
                    "count": 0,
                    "items": []
                }
            
            groups[group_value]["count"] += 1
            groups[group_value]["items"].append(result)
        
        # 计算聚合统计
        aggregated_result = {
            "total_groups": len(groups),
            "total_items": len(results),
            "groups": {}
        }
        
        for group_value, group_data in groups.items():
            aggregated_result["groups"][group_value] = {
                "count": group_data["count"],
                "percentage": (group_data["count"] / len(results)) * 100
            }
            
            # 如果有聚合字段，计算统计信息
            if aggregate_fields:
                for field in aggregate_fields:
                    field_values = [
                        item.get(field) for item in group_data["items"] 
                        if item.get(field) is not None
                    ]
                    
                    if field_values and all(isinstance(v, (int, float)) for v in field_values):
                        aggregated_result["groups"][group_value][f"{field}_stats"] = {
                            "min": min(field_values),
                            "max": max(field_values),
                            "avg": sum(field_values) / len(field_values),
                            "sum": sum(field_values)
                        }
        
        return aggregated_result
    
    def clear_metadata_cache(self) -> None:
        """
        清空元数据缓存
        """
        self.metadata_cache.clear()
        logger.info("元数据缓存已清空")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        return {
            "cache_size": len(self.metadata_cache),
            "cache_keys": list(self.metadata_cache.keys())[:10]  # 只显示前10个键
        }
