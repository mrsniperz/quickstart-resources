"""
模块名称: search_service
功能描述: Milvus检索服务，提供向量检索、混合检索、查询优化等功能
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
logger = SZ_LoggerManager.setup_logger(__name__, log_file="milvus_search.log")


class MilvusSearchService:
    """
    Milvus检索服务类
    
    提供向量检索、混合检索、查询优化等功能。
    支持多种检索策略和结果排序。
    
    Attributes:
        client (MilvusClient): Milvus客户端实例
    """
    
    def __init__(self, client: MilvusClient):
        """
        初始化MilvusSearchService实例
        
        Args:
            client (MilvusClient): Milvus客户端实例
        """
        self.client = client
        logger.info("MilvusSearchService初始化完成")
    
    def vector_search(
        self,
        collection_name: str,
        query_vectors: List[List[float]],
        vector_field: str,
        limit: int = 10,
        search_params: Optional[Dict[str, Any]] = None,
        filter_expr: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
        partition_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        执行向量相似度检索
        
        Args:
            collection_name (str): Collection名称
            query_vectors (List[List[float]]): 查询向量列表
            vector_field (str): 向量字段名
            limit (int): 返回结果数量限制
            search_params (Optional[Dict[str, Any]]): 检索参数
            filter_expr (Optional[str]): 过滤表达式
            output_fields (Optional[List[str]]): 输出字段列表
            partition_names (Optional[List[str]]): 分区名称列表
            
        Returns:
            List[Dict[str, Any]]: 检索结果列表
            
        Raises:
            Exception: 如果检索过程中发生错误
        """
        try:
            start_time = time.time()
            
            # 设置默认检索参数
            if search_params is None:
                search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            
            # 执行检索
            results = self.client.search(
                collection_name=collection_name,
                data=query_vectors,
                anns_field=vector_field,
                search_params=search_params,
                limit=limit,
                expr=filter_expr,
                output_fields=output_fields,
                partition_names=partition_names
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"向量检索完成，耗时: {elapsed_time:.4f}秒")
            
            # 格式化结果
            formatted_results = self._format_search_results(results)
            return formatted_results
            
        except Exception as e:
            logger.error(f"向量检索时出错: {e}")
            raise
    
    def sparse_vector_search(
        self,
        collection_name: str,
        query_texts: List[str],
        sparse_field: str,
        limit: int = 10,
        search_params: Optional[Dict[str, Any]] = None,
        filter_expr: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
        partition_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        执行稀疏向量检索（BM25全文检索）
        
        Args:
            collection_name (str): Collection名称
            query_texts (List[str]): 查询文本列表
            sparse_field (str): 稀疏向量字段名
            limit (int): 返回结果数量限制
            search_params (Optional[Dict[str, Any]]): 检索参数
            filter_expr (Optional[str]): 过滤表达式
            output_fields (Optional[List[str]]): 输出字段列表
            partition_names (Optional[List[str]]): 分区名称列表
            
        Returns:
            List[Dict[str, Any]]: 检索结果列表
            
        Raises:
            Exception: 如果检索过程中发生错误
        """
        try:
            start_time = time.time()
            
            # 设置默认检索参数
            if search_params is None:
                search_params = {"params": {"drop_ratio_search": 0.2}}
            
            # 执行稀疏向量检索
            results = self.client.search(
                collection_name=collection_name,
                data=query_texts,  # 直接传递查询文本
                anns_field=sparse_field,
                search_params=search_params,
                limit=limit,
                expr=filter_expr,
                output_fields=output_fields,
                partition_names=partition_names
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"稀疏向量检索完成，耗时: {elapsed_time:.4f}秒")
            
            # 格式化结果
            formatted_results = self._format_search_results(results)
            return formatted_results
            
        except Exception as e:
            logger.error(f"稀疏向量检索时出错: {e}")
            raise
    
    def text_match_search(
        self,
        collection_name: str,
        query_text: str,
        text_field: str,
        limit: int = 10,
        output_fields: Optional[List[str]] = None,
        partition_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        执行文本精确匹配检索
        
        Args:
            collection_name (str): Collection名称
            query_text (str): 查询文本
            text_field (str): 文本字段名
            limit (int): 返回结果数量限制
            output_fields (Optional[List[str]]): 输出字段列表
            partition_names (Optional[List[str]]): 分区名称列表
            
        Returns:
            List[Dict[str, Any]]: 检索结果列表
            
        Raises:
            Exception: 如果检索过程中发生错误
        """
        try:
            start_time = time.time()
            
            # 构建TEXT_MATCH过滤表达式
            filter_expr = f"TEXT_MATCH({text_field}, '{query_text}')"
            
            # 执行查询
            results = self.client.query(
                collection_name=collection_name,
                filter=filter_expr,
                output_fields=output_fields,
                partition_names=partition_names,
                limit=limit
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"文本匹配检索完成，耗时: {elapsed_time:.4f}秒")
            
            # 格式化查询结果
            formatted_results = [
                {
                    "id": item.get("id"),
                    "score": None,  # TEXT_MATCH不提供相似度分数
                    "entity": item
                }
                for item in results
            ]
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"文本匹配检索时出错: {e}")
            raise
    
    def hybrid_search(
        self,
        collection_name: str,
        query_vectors: List[List[float]],
        query_texts: List[str],
        vector_field: str,
        sparse_field: str,
        limit: int = 10,
        vector_weight: float = 0.7,
        sparse_weight: float = 0.3,
        filter_expr: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
        partition_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        执行混合检索（向量检索 + 稀疏向量检索）
        
        Args:
            collection_name (str): Collection名称
            query_vectors (List[List[float]]): 查询向量列表
            query_texts (List[str]): 查询文本列表
            vector_field (str): 向量字段名
            sparse_field (str): 稀疏向量字段名
            limit (int): 返回结果数量限制
            vector_weight (float): 向量检索权重
            sparse_weight (float): 稀疏向量检索权重
            filter_expr (Optional[str]): 过滤表达式
            output_fields (Optional[List[str]]): 输出字段列表
            partition_names (Optional[List[str]]): 分区名称列表
            
        Returns:
            List[Dict[str, Any]]: 混合检索结果列表
            
        Raises:
            Exception: 如果检索过程中发生错误
        """
        try:
            start_time = time.time()
            
            # 执行向量检索
            vector_results = self.vector_search(
                collection_name=collection_name,
                query_vectors=query_vectors,
                vector_field=vector_field,
                limit=limit * 2,  # 获取更多结果用于融合
                filter_expr=filter_expr,
                output_fields=output_fields,
                partition_names=partition_names
            )
            
            # 执行稀疏向量检索
            sparse_results = self.sparse_vector_search(
                collection_name=collection_name,
                query_texts=query_texts,
                sparse_field=sparse_field,
                limit=limit * 2,  # 获取更多结果用于融合
                filter_expr=filter_expr,
                output_fields=output_fields,
                partition_names=partition_names
            )
            
            # 融合检索结果
            hybrid_results = self._merge_search_results(
                vector_results, sparse_results, 
                vector_weight, sparse_weight, limit
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"混合检索完成，耗时: {elapsed_time:.4f}秒")
            
            return hybrid_results
            
        except Exception as e:
            logger.error(f"混合检索时出错: {e}")
            raise

    def _format_search_results(self, results) -> List[Dict[str, Any]]:
        """
        格式化检索结果

        Args:
            results: Milvus检索结果

        Returns:
            List[Dict[str, Any]]: 格式化后的结果列表
        """
        formatted_results = []

        if results and results[0]:  # 检查结果是否为空
            for hit in results[0]:  # 访问第一个查询的结果
                formatted_results.append({
                    "id": hit.entity.get("id") if hasattr(hit, 'entity') else hit.get("id"),
                    "score": hit.distance if hasattr(hit, 'distance') else None,
                    "entity": hit.entity if hasattr(hit, 'entity') else hit
                })

        return formatted_results

    def _merge_search_results(
        self,
        vector_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        vector_weight: float,
        sparse_weight: float,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        融合向量检索和稀疏向量检索的结果

        Args:
            vector_results (List[Dict[str, Any]]): 向量检索结果
            sparse_results (List[Dict[str, Any]]): 稀疏向量检索结果
            vector_weight (float): 向量检索权重
            sparse_weight (float): 稀疏向量检索权重
            limit (int): 返回结果数量限制

        Returns:
            List[Dict[str, Any]]: 融合后的结果列表
        """
        # 创建结果字典，以ID为键
        merged_results = {}

        # 处理向量检索结果
        for i, result in enumerate(vector_results):
            entity_id = result.get("id")
            if entity_id is not None:
                # 计算归一化分数（排名越靠前分数越高）
                vector_score = (len(vector_results) - i) / len(vector_results)
                merged_results[entity_id] = {
                    "id": entity_id,
                    "entity": result.get("entity"),
                    "vector_score": vector_score,
                    "sparse_score": 0.0,
                    "combined_score": vector_score * vector_weight
                }

        # 处理稀疏向量检索结果
        for i, result in enumerate(sparse_results):
            entity_id = result.get("id")
            if entity_id is not None:
                # 计算归一化分数
                sparse_score = (len(sparse_results) - i) / len(sparse_results)

                if entity_id in merged_results:
                    # 更新已存在的结果
                    merged_results[entity_id]["sparse_score"] = sparse_score
                    merged_results[entity_id]["combined_score"] = (
                        merged_results[entity_id]["vector_score"] * vector_weight +
                        sparse_score * sparse_weight
                    )
                else:
                    # 添加新结果
                    merged_results[entity_id] = {
                        "id": entity_id,
                        "entity": result.get("entity"),
                        "vector_score": 0.0,
                        "sparse_score": sparse_score,
                        "combined_score": sparse_score * sparse_weight
                    }

        # 按组合分数排序并返回前limit个结果
        sorted_results = sorted(
            merged_results.values(),
            key=lambda x: x["combined_score"],
            reverse=True
        )

        return sorted_results[:limit]

    def query_by_filter(
        self,
        collection_name: str,
        filter_expr: str,
        output_fields: Optional[List[str]] = None,
        partition_names: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        根据过滤条件查询数据

        Args:
            collection_name (str): Collection名称
            filter_expr (str): 过滤表达式
            output_fields (Optional[List[str]]): 输出字段列表
            partition_names (Optional[List[str]]): 分区名称列表
            limit (int): 返回结果数量限制

        Returns:
            List[Dict[str, Any]]: 查询结果列表

        Raises:
            Exception: 如果查询过程中发生错误
        """
        try:
            start_time = time.time()

            results = self.client.query(
                collection_name=collection_name,
                filter=filter_expr,
                output_fields=output_fields,
                partition_names=partition_names,
                limit=limit
            )

            elapsed_time = time.time() - start_time
            logger.info(f"条件查询完成，耗时: {elapsed_time:.4f}秒，返回 {len(results)} 条结果")

            return results

        except Exception as e:
            logger.error(f"条件查询时出错: {e}")
            raise

    def get_entity_by_id(
        self,
        collection_name: str,
        entity_ids: Union[List[Union[str, int]], str, int],
        output_fields: Optional[List[str]] = None,
        partition_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        根据ID获取实体数据

        Args:
            collection_name (str): Collection名称
            entity_ids (Union[List[Union[str, int]], str, int]): 实体ID或ID列表
            output_fields (Optional[List[str]]): 输出字段列表
            partition_names (Optional[List[str]]): 分区名称列表

        Returns:
            List[Dict[str, Any]]: 实体数据列表

        Raises:
            Exception: 如果查询过程中发生错误
        """
        try:
            # 标准化ID格式
            if isinstance(entity_ids, (str, int)):
                id_list = [entity_ids]
            else:
                id_list = entity_ids

            # 构建ID过滤表达式
            if len(id_list) == 1:
                filter_expr = f"id == {id_list[0]}"
            else:
                id_str = ", ".join([str(id_val) for id_val in id_list])
                filter_expr = f"id in [{id_str}]"

            results = self.query_by_filter(
                collection_name=collection_name,
                filter_expr=filter_expr,
                output_fields=output_fields,
                partition_names=partition_names,
                limit=len(id_list)
            )

            logger.info(f"根据ID查询完成，查询 {len(id_list)} 个ID，返回 {len(results)} 条结果")
            return results

        except Exception as e:
            logger.error(f"根据ID查询时出错: {e}")
            raise
