"""
模块名称: translate_vector.py
功能描述: Milvus航空翻译数据导入和管理模块。
           包含与Milvus交互的类 AviationTranslationImporter,
           用于创建集合、管理分区、导入数据、搜索数据和健康检查。
创建日期: 2025-05-24
作者: Sniperz
版本: 1.2.0  # 更新版本号
"""
import pandas as pd
import time
import hashlib
# import json # Not used
import logging
from typing import List, Dict, Optional, Union, Any # Added Any for search results flexibility
from pymilvus import MilvusClient, DataType, Function, FunctionType, CollectionSchema, FieldSchema
# from pymilvus import LoadState # Import LoadState # Removed this line
# from pymilvus.bulk_writer import ( # Bulk import functionality seems commented out / unused
#     LocalBulkWriter,
#     BulkFileType,
#     bulk_import,
#     get_import_progress,
#     list_import_jobs,
# )
# from concurrent.futures import ThreadPoolExecutor, as_completed # Related to bulk import
from pathlib import Path
from rapidfuzz import fuzz, process # 添加 process 导入
from rapidfuzz.utils import default_process # 添加 default_process 导入
# from pymilvus import CollectionSchema, FieldSchema, DataType # Duplicated import
from aviation_translation.src.utils.SZ_LoggerManager import SZ_LoggerManager

# 尝试导入jieba用于中文分词
try:
    import jieba
except ImportError:
    jieba = None
    logging.warning("jieba 库未安装，中文模糊匹配可能效果不佳。请运行 'pip install jieba'")

# 配置日志
logger = SZ_LoggerManager.setup_logger(__name__, log_file="milvus_import.log")

# Constants
DEFAULT_MILVUS_URI = "http://124.71.148.16:19530"
DEFAULT_COLLECTION_NAME = "aviation_translations"
DEFAULT_TOKEN = "root:Milvus"
DEFAULT_TEMP_DIR = "./milvus_temp"
DEFAULT_CHUNK_SIZE = 10000


class AviationTranslationImporter:
    """
    航空翻译数据导入和管理类。

    封装了与Milvus交互的操作，包括集合创建、分区管理、数据导入、
    数据搜索以及健康状态检查。支持英中双向翻译和搜索。

    Attributes:
        client_uri (str): Milvus服务的URI。
        client (MilvusClient): Milvus客户端实例。
        collection_name (str): Milvus中集合的名称。
        chunk_size (int): 数据导入时的批处理大小。
        temp_dir (str): 用于存储临时文件的目录路径。
    """

    def __init__(
        self,
        uri: str = DEFAULT_MILVUS_URI,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        token: str = DEFAULT_TOKEN,
        temp_dir: str = DEFAULT_TEMP_DIR,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        """
        初始化AviationTranslationImporter实例。

        Args:
            uri (str): Milvus服务的URI。
            collection_name (str): 要操作的Milvus集合名称。
            token (str): Milvus服务的认证令牌。
            temp_dir (str): 临时文件目录。
            chunk_size (int): 数据导入时的分块大小。
        """
        self.client_uri = uri
        self.client = MilvusClient(uri=uri, token=token)
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.temp_dir = temp_dir
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)

    def create_collection(self) -> None:
        """
        在Milvus中创建航空翻译数据集合。

        集合包含 'id', 'text' (英文), 'translation' (中文),
        'sparse_text' (英文稀疏向量), 'sparse_translation' (中文稀疏向量),
        'create_time' (创建时间), 'update_time' (更新时间) 字段。
        为 'text' 和 'translation' 字段启用BM25函数以支持全文搜索，
        并为 'sparse_text' 和 'sparse_translation' 字段创建SPARSE_INVERTED_INDEX索引。
        如果集合已存在，则不执行任何操作。

        Raises:
            Exception: 如果创建集合过程中发生Milvus客户端错误。
        """
        if self.collection_name in self.client.list_collections():
            logger.info(f"集合 {self.collection_name} 已存在")
            return

        schema = MilvusClient.create_schema(auto_id=True, enable_dynamic_field=False)
        analyzer_params_en = {"type": "english"}
        # 使用Milvus内置的中文分析器
        analyzer_params_zh = {"type": "chinese"}

        schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
        # 英文原文
        schema.add_field(
            field_name="text", # English text
            datatype=DataType.VARCHAR,
            max_length=2000,
            enable_analyzer=True,
            enable_match=True, # For TEXT_MATCH on English
            analyzer_params=analyzer_params_en,
        )
        # 中文翻译
        schema.add_field(
            field_name="translation", # Chinese translation
            datatype=DataType.VARCHAR,
            max_length=2000,
            enable_analyzer=True, # Enable analyzer for BM25
            enable_match=True,    # For TEXT_MATCH on Chinese
            analyzer_params=analyzer_params_zh, # 使用中文分析器
        )
        # 英文稀疏向量 (原 sparse 字段)
        schema.add_field(field_name="sparse_text", datatype=DataType.SPARSE_FLOAT_VECTOR)
        # 中文稀疏向量
        schema.add_field(field_name="sparse_translation", datatype=DataType.SPARSE_FLOAT_VECTOR)
        # 创建时间
        schema.add_field(
            field_name="create_time",
            datatype=DataType.INT64,
            description="记录创建时间"
        )
        # 更新时间
        schema.add_field(
            field_name="update_time",
            datatype=DataType.INT64,
            description="记录更新时间"
        )

        # BM25函数 for English text -> sparse_text
        schema.add_function(
            Function(
                name="bm25_func_text",
                input_field_names=["text"],
                output_field_names=["sparse_text"], # Output to new field name
                function_type=FunctionType.BM25,
            )
        )
        # BM25函数 for Chinese translation -> sparse_translation
        schema.add_function(
            Function(
                name="bm25_func_translation",
                input_field_names=["translation"],
                output_field_names=["sparse_translation"],
                function_type=FunctionType.BM25,
            )
        )

        index_params = MilvusClient.prepare_index_params()
        # Index for English sparse vectors
        index_params.add_index(
            field_name="sparse_text", # Updated field name
            index_type="SPARSE_INVERTED_INDEX",
            metric_type="BM25",
            params={
                "inverted_index_algo": "DAAT_WAND",
                "bm25_k1": 1.8,
                "bm25_b": 0.75,
            },
        )
        # Index for Chinese sparse vectors
        index_params.add_index(
            field_name="sparse_translation",
            index_type="SPARSE_INVERTED_INDEX",
            metric_type="BM25",
            params={
                "inverted_index_algo": "DAAT_WAND",
                "bm25_k1": 1.8, # 这些参数可能需要针对中文进行调优
                "bm25_b": 0.75,
            },
        )

        self.client.create_collection(
            collection_name=self.collection_name,
            schema=schema,
            index_params=index_params,
            auto_id=True, # Schema already has auto_id=True
            # enable_dynamic_field=False, # Schema already has enable_dynamic_field=False
        )
        logger.info(f"集合 {self.collection_name} 创建成功，支持双向翻译索引和时间字段。")

    def generate_content_based_id(self, text: str, translation: str) -> int:
        """
        基于文本内容生成确定性的ID

        使用文本和翻译的组合生成一个确定性的整数ID，
        这样相同的内容总是会得到相同的ID。

        参数:
            text (str): 英文原文
            translation (str): 中文翻译

        返回:
            int: 基于内容生成的确定性ID
        """
        # 组合文本内容
        content = f"{text.strip()}|{translation.strip()}"
        # 生成MD5哈希
        hash_object = hashlib.md5(content.encode('utf-8'))
        # 转换为整数（取前8字节避免过大）
        hash_int = int(hash_object.hexdigest()[:8], 16)
        # 确保是正整数且在合理范围内
        return abs(hash_int) % (2**31 - 1)

    def create_custom_partition(self, partition_name: str) -> None:
        """
        在当前集合中创建自定义分区。

        如果指定名称的分区已存在，则不执行任何操作。
        如果集合不存在，则会先尝试创建集合（使用默认参数，可能不符合预期）。
        TODO: 考虑集合不存在时的更优处理逻辑。

        Args:
            partition_name (str): 要创建的分区名称。

        Raises:
            Exception: 如果创建分区过程中发生Milvus客户端错误。
        """
        try:
            if not self.client.has_collection(self.collection_name):
                logger.info(f"集合 {self.collection_name} 不存在，正在创建...")
                # 使用新的create_collection方法创建支持双向翻译的集合
                self.create_collection()
                logger.info(f"集合 {self.collection_name} 已创建 (使用新版schema)")
            else:
                logger.info(f"集合 {self.collection_name} 已存在")

            if not self.client.has_partition(self.collection_name, partition_name):
                self.client.create_partition(
                    collection_name=self.collection_name, partition_name=partition_name
                )
                logger.info(f"分区 {partition_name} 在集合 {self.collection_name} 中已创建")
            else:
                logger.info(f"分区 {partition_name} 在集合 {self.collection_name} 中已存在")
        except Exception as e:
            logger.error(f"创建分区时发生错误：{e}")
            raise  # Re-raise the exception to be handled by the caller

    def prepare_data(self, xlsx_path: str) -> List[Dict[str, str]]:
        """
        从XLSX文件加载并预处理航空翻译数据。

        数据包含'en' (英文文本) 和 'cn' (中文翻译) 两列。
        会去除空值行，并对文本进行前后空格清理。

        Args:
            xlsx_path (str): XLSX文件的路径。

        Returns:
            List[Dict[str, str]]: 处理后的数据列表，每个字典包含 "text" 和 "translation" 键。

        Raises:
            pd.errors.EmptyDataError: 如果Excel文件为空或无法解析。
            FileNotFoundError: 如果指定的xlsx_path文件不存在。
            Exception: 其他Pandas读取或处理错误。
        """
        df = pd.read_excel(xlsx_path)
        df = df.dropna(subset=["en", "cn"])
        df["en"] = df["en"].astype(str).str.strip()
        df["cn"] = df["cn"].astype(str).str.strip()
        return [
            {"text": row["en"], "translation": row["cn"]} for _, row in df.iterrows()
        ]

    def insert_data_to_milvus_with_chunk(
        self, data: List[Dict[str, str]], partition_name: Optional[str] = None
    ) -> None:
        """
        将数据分批插入到Milvus集合中。
        
        参数:
            data (List[Dict[str, str]]): 包含text和translation字段的数据列表
            partition_name (Optional[str]): 目标分区名称，如果为None则使用默认分区
        
        Raises:
            Exception: 如果插入过程中发生Milvus客户端错误
        """
        try:
            # 确保集合存在
            if not self.client.has_collection(self.collection_name):
                self.create_collection()
                logger.info(f"集合 {self.collection_name} 不存在，已创建")
            
            # 确保分区存在（如果指定了分区）
            if partition_name and not self.client.has_partition(self.collection_name, partition_name):
                self.create_custom_partition(partition_name)
                logger.info(f"分区 {partition_name} 不存在，已创建")
            
            # 添加时间戳
            current_time = int(time.time())
            for item in data:
                item["create_time"] = current_time
                item["update_time"] = current_time
            
            # 分批插入数据
            total_records = len(data)
            for i in range(0, total_records, self.chunk_size):
                chunk = data[i:i+self.chunk_size]
                
                # 插入数据
                insert_params = {
                    "collection_name": self.collection_name,
                    "data": chunk
                }
                if partition_name:
                    insert_params["partition_name"] = partition_name
                
                self.client.insert(**insert_params)
                
                logger.info(f"已插入 {i+len(chunk)}/{total_records} 条记录")
            
            logger.info(f"成功插入 {total_records} 条记录到集合 {self.collection_name}")
        except Exception as e:
            logger.error(f"插入数据时出错: {e}")
            raise

    def load_specified_partitions(self, partition_names: List[str]) -> None:
        """
        加载指定的一个或多个分区到内存中。

        Args:
            partition_names (List[str]): 需要加载的分区名称列表。

        Raises:
            Exception: 如果加载分区过程中发生Milvus客户端错误。
        """
        logger.info(f"开始加载分区 {partition_names} 到集合 {self.collection_name}...")
        self.client.load_partitions(
            collection_name=self.collection_name, partition_names=partition_names
        )
        logger.info(f"分区 {partition_names} 加载成功。")

    def release_specified_partitions(self, partition_names: List[str]) -> None:
        """
        从内存中释放指定的一个或多个分区。

        Args:
            partition_names (List[str]): 需要释放的分区名称列表。

        Raises:
            Exception: 如果释放分区过程中发生Milvus客户端错误。
        """
        logger.info(f"开始释放分区 {partition_names} 从集合 {self.collection_name}...")
        self.client.release_partitions(
            collection_name=self.collection_name, partition_names=partition_names
        )
        logger.info(f"分区 {partition_names} 释放成功。")
        
    def drop_partition(self, partition_name: str, timeout: Optional[float] = None) -> bool:
        """
        删除指定的分区。

        注意：删除分区前必须先释放该分区。此方法会自动检查分区是否已释放，
        如果未释放则会先尝试释放分区，然后再执行删除操作。

        Args:
            partition_name (str): 要删除的分区名称。
            timeout (Optional[float]): 操作超时时间，单位为秒。
                如果为None，则在收到任何响应或发生任何错误时超时。

        Returns:
            bool: 如果分区成功删除或不存在，则返回True；如果发生错误，则返回False。

        Raises:
            Exception: 如果删除分区过程中发生Milvus客户端错误且未被捕获。
        """
        try:
            # 检查分区是否存在
            if not self.client.has_partition(self.collection_name, partition_name):
                logger.info(f"分区 {partition_name} 不存在于集合 {self.collection_name} 中，无需删除")
                return True
                
            # 尝试获取分区加载状态
            load_state = self.client.get_load_state(
                collection_name=self.collection_name,
                partition_name=partition_name
            )
            
            # 如果分区已加载，则先释放它
            # LoadState.Loaded 的枚举值为 3
            if load_state.get('state') == 3:
                logger.info(f"分区 {partition_name} 仍处于加载状态，正在释放...")
                self.release_specified_partitions([partition_name])
            
            # 删除分区
            logger.info(f"开始删除分区 {partition_name} 从集合 {self.collection_name}...")
            self.client.drop_partition(
                collection_name=self.collection_name,
                partition_name=partition_name,
                timeout=timeout
            )
            logger.info(f"分区 {partition_name} 删除成功")
            return True
            
        except Exception as e:
            logger.error(f"删除分区 {partition_name} 时发生错误: {e}")
            return False
        
    def load_collection(self, load_fields: Optional[List[str]] = None, skip_load_dynamic_field: bool = False) -> None:
        """
        加载整个集合到内存中。
        
        加载集合是执行相似度搜索和查询的前提条件。如果在集合加载后插入了新的实体，
        它们会自动被索引并加载。

        Args:
            load_fields (Optional[List[str]]): 指定要加载的字段列表。如果为None，则加载所有字段。
            skip_load_dynamic_field (bool): 是否跳过加载动态字段，默认为False。

        Raises:
            Exception: 如果加载集合过程中发生Milvus客户端错误。
        """
        logger.info(f"开始加载集合 {self.collection_name}...")
        
        load_params = {
            "collection_name": self.collection_name
        }
        
        if load_fields:
            load_params["load_fields"] = load_fields
            logger.info(f"指定加载字段: {load_fields}")
            
        if skip_load_dynamic_field:
            load_params["skip_load_dynamic_field"] = skip_load_dynamic_field
            logger.info("跳过加载动态字段")
            
        self.client.load_collection(**load_params)
        
        # 获取加载状态
        load_state = self.client.get_load_state(collection_name=self.collection_name)
        logger.info(f"集合 {self.collection_name} 加载状态: {load_state}")
        logger.info(f"集合 {self.collection_name} 加载成功。")
    
    def release_collection(self) -> None:
        """
        从内存中释放整个集合。
        
        搜索和查询是内存密集型操作。释放不再使用的集合可以节省资源成本。

        Raises:
            Exception: 如果释放集合过程中发生Milvus客户端错误。
        """
        logger.info(f"开始释放集合 {self.collection_name}...")
        self.client.release_collection(collection_name=self.collection_name)
        
        # 获取加载状态
        load_state = self.client.get_load_state(collection_name=self.collection_name)
        logger.info(f"集合 {self.collection_name} 释放后状态: {load_state}")
        logger.info(f"集合 {self.collection_name} 释放成功。")

    def search_data(
        self,
        query_text: str,
        search_type: str,
        search_direction: str = "en_to_zh", 
        partition_names: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        在航空翻译数据中执行搜索，支持双向翻译。

        支持 "text_match" (文本精确匹配) 和 "full_text" (基于BM25的全文搜索) 两种模式。
        支持 "en_to_zh" (英译中) 和 "zh_to_en" (中译英) 两种搜索方向。

        Args:
            query_text (str): 用于搜索的查询文本。
            search_type (str): 搜索类型，必须是 "text_match" 或 "full_text"。
            search_direction (str): 搜索方向，"en_to_zh" (英译中) 或 "zh_to_en" (中译英)。
            partition_names (Optional[List[str]]): 要在其中搜索的分区列表。如果为None，则在所有已加载分区中搜索。
            limit (int): 返回的最大结果数量。

        Returns:
            List[Dict[str, Any]]: 搜索结果列表。每个字典包含 "text", "translation" 和 (对于全文搜索) "score"。

        Raises:
            ValueError: 如果 `search_type` 不是 "text_match" 或 "full_text"，或 `search_direction` 不是 "en_to_zh" 或 "zh_to_en"。
            Exception: 如果搜索过程中发生Milvus客户端错误。
        """
        if search_type not in ["text_match", "full_text"]:
            raise ValueError("search_type 必须是 'text_match' 或 'full_text'")
        if search_direction not in ["en_to_zh", "zh_to_en"]:
            raise ValueError("search_direction 必须是 'en_to_zh' 或 'zh_to_en'")

        # 根据搜索方向确定源文本字段和稀疏向量字段
        source_text_field_for_query: str
        sparse_vector_field_for_search: str
        query_language_for_fuzzy: str

        if search_direction == "en_to_zh":
            source_text_field_for_query = "text"         # 查询英文文本
            sparse_vector_field_for_search = "sparse_text" # 使用英文稀疏向量
            query_language_for_fuzzy = "en"
        else:  # zh_to_en
            source_text_field_for_query = "translation"  # 查询中文文本
            sparse_vector_field_for_search = "sparse_translation" # 使用中文稀疏向量
            query_language_for_fuzzy = "zh"

        # 始终获取ID、文本、翻译和时间字段
        output_fields_list = ["id", "text", "translation", "create_time", "update_time"]
        formatted_results: List[Dict[str, Any]] = []

        if search_type == "text_match":
            filter_expr = f"TEXT_MATCH({source_text_field_for_query}, '{query_text}')"
            results = self.client.query(
                collection_name=self.collection_name,
                filter=filter_expr,
                partition_names=partition_names,
                output_fields=output_fields_list,
                limit=limit,
            )
            formatted_results = [
                {
                    "id": item.get("id"),
                    "text": item.get("text"),
                    "translation": item.get("translation"),
                    "score": None, # TEXT_MATCH doesn't provide a score in this client version
                    "create_time": item.get("create_time"),
                    "update_time": item.get("update_time"),
                }
                for item in results
            ]
        else:  # full_text search
            search_params = {
                "params": {"drop_ratio_search": 0.2}, # Standard search param for BM25/sparse
            }
            # 注意：MilvusClient.search 对于稀疏向量，直接传递查询文本，由BM25函数处理
            results = self.client.search(
                collection_name=self.collection_name,
                data=[query_text],  # 直接传递查询文本
                anns_field=sparse_vector_field_for_search,
                search_params=search_params, 
                partition_names=partition_names,
                limit=limit,
                output_fields=output_fields_list,
            )
            if results and results[0]: # Results is a list of lists of hits
                formatted_results = [
                    {
                        "id": hit.entity.get("id"),
                        "text": hit.entity.get("text"),
                        "translation": hit.entity.get("translation"),
                        "score": hit.distance,
                        "create_time": hit.entity.get("create_time"),
                        "update_time": hit.entity.get("update_time"),
                    }
                    for hit in results[0] # Access the first list of hits for the first query
                ]
        
        # 使用通用方法添加模糊匹配分数，传递查询语言参数
        return self._add_fuzzy_scores(
            query_text, 
            formatted_results, 
            source_text_field_for_query, 
            query_language_for_fuzzy
        )

    def _add_fuzzy_scores(
        self, 
        query_text: str, 
        results: List[Dict[str, Any]], 
        text_field_to_compare_against: str = "text",
        query_language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        为搜索结果添加模糊匹配分数，支持中英文。

        Args:
            query_text (str): 原始查询文本。
            results (List[Dict[str, Any]]): 搜索结果列表。
            text_field_to_compare_against (str): 结果中与查询文本同语言的字段名。
            query_language (str): 查询文本的语言 ("en" 或 "zh")。

        Returns:
            List[Dict[str, Any]]: 添加了模糊匹配分数的结果列表。
        """
        final_results_with_fuzzy: List[Dict[str, Any]] = []
        
        # 收集所有检索到的文本，用于模糊匹配
        retrieved_texts_for_fuzzy_comparison = []
        for item in results:
            text_val = item.get(text_field_to_compare_against)
            if text_val and isinstance(text_val, str):
                retrieved_texts_for_fuzzy_comparison.append(text_val)
        
        if retrieved_texts_for_fuzzy_comparison:
            # 根据语言获取处理后的词元
            def get_processed_tokens(text: str, lang: str) -> List[str]:
                if not text: 
                    return []
                # 如果是中文则使用jieba
                if lang == "zh":
                    if jieba:
                        return list(jieba.cut(text, cut_all=False)) 
                    else: 
                        return list(text) # 回退方案：字符级分词
                else: # "en" 或其他就使用default_process，他是英文的默认分词器
                    return default_process(text) 

            # 自定义评分函数，支持中英文
            def custom_scorer_bidirectional(s1: str, s2: str, lang: str) -> float:
                s1_tokens = get_processed_tokens(s1, lang)
                s2_tokens = get_processed_tokens(s2, lang)
                
                if not s1_tokens or not s2_tokens: 
                    return 0.0
                
                # 将分词结果连接为字符串，用于token_set_ratio比较
                s1_processed_str = " ".join(s1_tokens)
                s2_processed_str = " ".join(s2_tokens)

                # 创建词集合，用于计算覆盖率
                s1_token_set = set(s1_tokens)
                s2_token_set = set(s2_tokens)
                
                # 计算词汇覆盖率 (两个方向)
                query_coverage = sum(1 for token in s1_token_set if token in s2_token_set) / len(s1_token_set) if s1_token_set else 0.0
                retrieved_coverage = sum(1 for token in s2_token_set if token in s1_token_set) / len(s2_token_set) if s2_token_set else 0.0
                
                # 计算长度比例惩罚长度差异过大的文本对
                length_ratio = min(len(s1_tokens), len(s2_tokens)) / max(len(s1_tokens), len(s2_tokens)) if max(len(s1_tokens), len(s2_tokens)) > 0 else 0.0
                
                # 使用token_set_ratio (忽略词序，考虑所有词)
                set_ratio = fuzz.token_set_ratio(s1_processed_str, s2_processed_str) / 100.0

                # 覆盖率阈值，中文可能需要较低的阈值
                coverage_threshold = 0.8 if lang == "en" else 0.7
                min_coverage = min(query_coverage, retrieved_coverage)

                # 综合评分如果覆盖率和长度比例都超过阈值（英文0.8，中文0.7），给予较高评分
                # 否则，根据覆盖率和长度比例对基础评分进行调整
                # 如果最小覆盖率低于0.5，进一步降低评分
                if min_coverage >= coverage_threshold and length_ratio >= coverage_threshold:
                    return set_ratio * 100
                else:
                    adjustment_factor = min_coverage * length_ratio
                    if min_coverage < 0.5: 
                        adjustment_factor *= 0.5
                    return set_ratio * adjustment_factor * 100

            # 计算每个检索文本的相似度分数
            text_to_score_map = {
                text_to_compare: custom_scorer_bidirectional(query_text, text_to_compare, query_language)
                for text_to_compare in retrieved_texts_for_fuzzy_comparison
            }
            
            # 将模糊匹配分数添加到结果中
            for item in results:
                text_val = item.get(text_field_to_compare_against)
                if text_val and isinstance(text_val, str) and text_val in text_to_score_map:
                    item["fuzzy_score"] = text_to_score_map[text_val]
                else:
                    item["fuzzy_score"] = None 
                final_results_with_fuzzy.append(item)
        else:
            # 如果没有检索到文本，直接返回原始结果
            for item in results:
                item["fuzzy_score"] = None
                final_results_with_fuzzy.append(item)

        return final_results_with_fuzzy

    def get_health_info(self, partition_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取Milvus服务和指定集合/分区的健康状态信息。

        Args:
            partition_name (Optional[str]): 要检查的特定分区名称。
                如果提供，则返回该分区的详细信息（是否存在、行数、加载状态）。
                如果不提供，则返回集合级别的摘要信息（连接状态、集合总数、集合列表）。

        Returns:
            Dict[str, Any]: 包含健康状态信息的字典。

        Raises:
            Exception: 如果与Milvus通信时发生错误。
        """
        if partition_name:
            has_part = self.client.has_partition(
                collection_name=self.collection_name, partition_name=partition_name
            )
            if has_part:
                part_stats = self.client.get_partition_stats(
                    collection_name=self.collection_name, partition_name=partition_name
                )
                raw_load_state = self.client.get_load_state(
                    collection_name=self.collection_name, partition_name=partition_name # Corrected: was partition_name=partition_name
                )
       
                #  "load_state": "{'state': <LoadState: NotLoad>}"
                load_state_str = 'has loaded' if raw_load_state == 3 else "not loaded"

                return {
                    "status": "healthy" if has_part else "unhealthy", # partition_exists implies healthy for this context
                    "collection_name": self.collection_name,
                    "partition_name": partition_name,
                    "partition_exists": has_part,
                    "row_count": part_stats.get("row_count", 0) if isinstance(part_stats, dict) else part_stats, # get_partition_stats returns stats, not just row_count
                    "load_state": f'{raw_load_state.get("state")}', # Return string representation
                }
            else:
                return {
                    "status": "unhealthy",
                    "collection_name": self.collection_name,
                    "partition_name": partition_name,
                    "partition_exists": False,
                    "message": f"分区 {partition_name} 不存在于集合 {self.collection_name} 中。"
                }
        else:
            # General health check for the collection / Milvus connection
            collections = self.client.list_collections()
            collection_exists = self.collection_name in collections
            num_entities = 0
            if collection_exists:
                stats = self.client.get_collection_stats(collection_name=self.collection_name)
                num_entities = stats.get("row_count",0) if isinstance(stats, dict) else stats


            return {
                "status": "healthy" if collections else "unhealthy_no_collections_listed",
                "milvus_connected": True, # If list_collections didn't raise error
                "monitored_collection_exists": collection_exists,
                "monitored_collection_entities": num_entities,
                "total_collections_in_milvus": len(collections),
                "collection_list": collections,
            }

    def delete_collection(self) -> None:
        """
        删除当前配置的Milvus集合。

        如果集合不存在，则不执行任何操作。

        Raises:
            Exception: 如果删除集合过程中发生Milvus客户端错误。
        """
        try:
            if self.collection_name in self.client.list_collections():
                self.client.drop_collection(self.collection_name)
                logger.info(f"集合 {self.collection_name} 已删除")
            else:
                logger.info(f"集合 {self.collection_name} 不存在")
        except Exception as e:
            logger.error(f"删除集合时发生错误：{e}")
            raise # Re-raise for API to handle

    def insert_single_entry(
        self, text: str, translation: str, partition_name: str = "from_api"
    ) -> bool:
        """
        插入单条翻译数据到指定分区
        
        参数:
            text (str): 原文本
            translation (str): 翻译文本
            partition_name (str): 分区名称，默认为"from_api"
        
        返回:
            bool: 操作是否成功
        
        Raises:
            Exception: 如果插入过程中发生Milvus客户端错误
        """
        try:
            # 确保集合存在
            if not self.client.has_collection(self.collection_name):
                self.create_collection()
                logger.info(f"集合 {self.collection_name} 不存在，已创建")
            
            # 确保分区存在
            if not self.client.has_partition(self.collection_name, partition_name):
                self.create_custom_partition(partition_name)
                logger.info(f"分区 {partition_name} 不存在，已创建")
            
            # 添加时间戳
            current_time = int(time.time())
            
            # 创建数据条目
            data = [{
                "text": text,
                "translation": translation,
                "create_time": current_time,
                "update_time": current_time
            }]
            
            # 插入数据
            self.client.insert(
                collection_name=self.collection_name,
                data=data,
                partition_name=partition_name
            )
            
            logger.info(f"成功插入翻译数据 '{text[:30]}...' -> '{translation[:30]}...' 到分区 {partition_name}")
            return True
        
        except Exception as e:
            logger.error(f"插入单条翻译数据时出错: {e}")
            return False

    def batch_search_data(
        self,
        query_texts: List[str],
        search_type: str,
        search_direction: str = "en_to_zh", 
        text_field_name: str = "text",
        sparse_field_name: str = "sparse_text",
        partition_names: Optional[List[str]] = None,
        limit: int = 5,
        batch_size: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量执行搜索，支持双向翻译和同时搜索多个查询文本。

        Args:
            query_texts (List[str]): 用于搜索的查询文本列表。
            search_type (str): 搜索类型，必须是 "text_match" 或 "full_text"。
            search_direction (str): 搜索方向，"en_to_zh" (英译中) 或 "zh_to_en" (中译英)。
            text_field_name (str): 存储原始文本的字段名称 (默认为"text"，不建议修改)。
            sparse_field_name (str): 存储BM25稀疏向量的字段名称 (默认为"sparse_text"，兼容旧版)。
            partition_names (Optional[List[str]]): 要在其中搜索的分区列表。如果为None，则在所有已加载分区中搜索。
            limit (int): 每个查询返回的最大结果数量。
            batch_size (int): 批处理大小，每次处理的最大查询数量。

        Returns:
            Dict[str, List[Dict[str, Any]]]: 搜索结果字典，键为查询文本，值为对应的搜索结果列表。

        Raises:
            ValueError: 如果 `search_type` 不是 "text_match" 或 "full_text"，或 `search_direction` 不是 "en_to_zh" 或 "zh_to_en"。
            Exception: 如果搜索过程中发生Milvus客户端错误。
        """
        if search_type not in ["text_match", "full_text"]:
            raise ValueError("search_type 必须是 'text_match' 或 'full_text'")
        if search_direction not in ["en_to_zh", "zh_to_en"]:
            raise ValueError("search_direction 必须是 'en_to_zh' 或 'zh_to_en'")

        # 结果字典，键为查询文本，值为搜索结果列表
        results_dict: Dict[str, List[Dict[str, Any]]] = {}
        
        # 根据搜索方向确定源文本字段和稀疏向量字段
        source_text_field_for_query: str
        sparse_vector_field_for_search: str
        query_language_for_fuzzy: str

        if search_direction == "en_to_zh":
            source_text_field_for_query = "text"
            sparse_vector_field_for_search = "sparse_text"
            query_language_for_fuzzy = "en"
        else: 
            source_text_field_for_query = "translation"
            sparse_vector_field_for_search = "sparse_translation"
            query_language_for_fuzzy = "zh"
        
        output_fields_list = ["id", "text", "translation", "create_time", "update_time"]
        
        # 分批处理查询
        for i in range(0, len(query_texts), batch_size):
            batch_queries = query_texts[i:i+batch_size]
            
            if search_type == "text_match":
                # 对于text_match，我们需要逐个处理查询
                for query_text in batch_queries:
                    try:
                        filter_expr = f"TEXT_MATCH({source_text_field_for_query}, '{query_text}')"
                        results = self.client.query(
                            collection_name=self.collection_name,
                            filter=filter_expr,
                            partition_names=partition_names,
                            output_fields=output_fields_list,
                            limit=limit,
                        )
                        
                        formatted_results = [
                            {
                                "id": item.get("id"),
                                "text": item.get("text"),
                                "translation": item.get("translation"),
                                "score": None,
                                "create_time": item.get("create_time"),
                                "update_time": item.get("update_time"),
                            }
                            for item in results
                        ]
                        
                        # 添加模糊匹配分数
                        final_results = self._add_fuzzy_scores(
                            query_text, 
                            formatted_results, 
                            source_text_field_for_query, 
                            query_language_for_fuzzy
                        )
                        results_dict[query_text] = final_results
                    except Exception as e:
                        logger.error(f"批量text_match搜索出错 (查询: {query_text}): {e}")
                        results_dict[query_text] = []
            else:  # full_text search
                try:
                    search_params = {
                        "params": {"drop_ratio_search": 0.2},
                    }
                    
                    # 批量搜索
                    batch_results = self.client.search(
                        collection_name=self.collection_name,
                        data=batch_queries,  # 批量查询
                        anns_field=sparse_vector_field_for_search,
                        search_params=search_params,
                        partition_names=partition_names,
                        limit=limit,
                        output_fields=output_fields_list,
                    )
                    
                    # 处理每个查询的结果
                    for j, query_text in enumerate(batch_queries):
                        if j < len(batch_results) and batch_results[j]:
                            formatted_results = [
                                {
                                    "id": hit.entity.get("id"),
                                    "text": hit.entity.get("text"),
                                    "translation": hit.entity.get("translation"),
                                    "score": hit.distance,
                                    "create_time": hit.entity.get("create_time"),
                                    "update_time": hit.entity.get("update_time"),
                                }
                                for hit in batch_results[j]
                            ]
                            
                            # 添加模糊匹配分数
                            final_results = self._add_fuzzy_scores(
                                query_text, 
                                formatted_results, 
                                source_text_field_for_query, 
                                query_language_for_fuzzy
                            )
                            results_dict[query_text] = final_results
                        else:
                            results_dict[query_text] = []
                except Exception as e:
                    logger.error(f"批量full_text搜索出错 (批次 {i//batch_size + 1}): {e}")
                    # 为批次中的所有查询添加空结果
                    for query_text in batch_queries:
                        results_dict[query_text] = []

    def describe_collection(self) -> Dict[str, Any]:
        """
        获取集合的详细描述信息

        返回:
            Dict[str, Any]: 包含集合详细信息的字典

        Raises:
            Exception: 如果获取集合描述过程中发生Milvus客户端错误
        """
        try:
            logger.info(f"获取集合 {self.collection_name} 的详细描述")

            # 获取集合描述
            collection_info = self.client.describe_collection(self.collection_name)

            # 获取加载状态
            load_status_raw = self.client.get_load_state(collection_name=self.collection_name)

            # 将加载状态转换为字符串格式，以符合API响应模型的要求
            # load_status_raw 格式: {'state': <LoadState: Loaded>}
            if isinstance(load_status_raw, dict) and 'state' in load_status_raw:
                load_status_str = str(load_status_raw.get('state'))
            else:
                load_status_str = str(load_status_raw)

            # 添加加载状态到返回结果
            collection_info["load_status"] = load_status_str

            logger.info(f"成功获取集合 {self.collection_name} 的详细描述，加载状态: {load_status_str}")
            return collection_info
        except Exception as e:
            logger.error(f"获取集合描述时出错: {e}")
            raise

    def alter_collection_field(self, field_name: str, **kwargs) -> None:
        """
        修改集合字段的属性（仅限现有字段的属性修改，不能添加新字段）

        注意：此方法只能修改现有字段的属性，不能添加新字段到集合中。
        Milvus不支持向现有集合添加新字段，集合schema在创建后基本不可变。

        支持修改的字段属性范围：
        - VARCHAR字段: max_length (最大字符长度)
        - ARRAY字段: max_capacity (数组最大容量)
        - 所有字段: mmap_enabled (内存映射启用状态)

        不支持的操作：
        - 添加新字段
        - 删除现有字段
        - 修改字段数据类型
        - 修改主键字段
        - 修改分区键字段

        参数:
            field_name (str): 要修改的字段名称（必须是已存在的字段）
            **kwargs: 要修改的属性，支持的属性包括:
                - max_length (int): VARCHAR字段的最大字符长度 [1, 65535]
                - max_capacity (int): ARRAY字段的最大容量
                - mmap_enabled (bool): 是否启用内存映射

        Raises:
            Exception: 如果修改字段属性过程中发生Milvus客户端错误
        """
        try:
            logger.info(f"修改集合 {self.collection_name} 的字段 {field_name} 属性")

            # 首先检查字段是否存在
            collection_info = self.describe_collection()
            existing_fields = [field["name"] for field in collection_info.get("fields", [])]

            if field_name not in existing_fields:
                raise ValueError(f"字段 '{field_name}' 不存在于集合 {self.collection_name} 中。"
                               f"可用字段: {existing_fields}")

            # 检查并验证参数
            valid_params = {}
            supported_params = ["max_length", "max_capacity", "mmap_enabled"]

            for param, value in kwargs.items():
                if param in supported_params:
                    valid_params[param] = value
                else:
                    logger.warning(f"不支持的参数 '{param}'，支持的参数: {supported_params}")

            if not valid_params:
                logger.warning("没有提供有效的修改参数")
                logger.info(f"支持的参数: {supported_params}")
                return

            # 使用field_params参数格式调用API
            self.client.alter_collection_field(
                collection_name=self.collection_name,
                field_name=field_name,
                field_params=valid_params
            )

            logger.info(f"成功修改集合 {self.collection_name} 的字段 {field_name} 属性: {valid_params}")
        except Exception as e:
            logger.error(f"修改字段属性时出错: {e}")
            raise

    def upsert_data(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        partition_name: Optional[str] = None,
        use_content_based_id: bool = False
    ) -> Dict[str, Any]:
        """
        更新或插入数据到Milvus集合中

        如果数据中的主键已存在，则更新该记录；如果不存在，则插入新记录。

        参数:
            data (Union[Dict[str, Any], List[Dict[str, Any]]]): 要更新或插入的数据
                可以是单个字典或字典列表，每个字典应包含text和translation字段
            partition_name (Optional[str]): 目标分区名称，如果为None则使用默认分区
            use_content_based_id (bool): 是否为没有ID的数据生成基于内容的确定性ID

        返回:
            Dict[str, Any]: 包含操作结果的字典，包含upsert_count字段和可能的inserted_ids

        Raises:
            Exception: 如果upsert过程中发生Milvus客户端错误
        """
        try:
            # 确保集合存在
            if not self.client.has_collection(self.collection_name):
                self.create_collection()
                logger.info(f"集合 {self.collection_name} 不存在，已创建")

            # 确保分区存在（如果指定了分区）
            if partition_name and not self.client.has_partition(self.collection_name, partition_name):
                self.create_custom_partition(partition_name)
                logger.info(f"分区 {partition_name} 不存在，已创建")

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
                # 如果没有create_time，则添加
                if "create_time" not in item:
                    item["create_time"] = current_time
                # 总是更新update_time
                item["update_time"] = current_time

                # 根据是否有ID分类
                if "id" in item and item["id"] is not None:
                    data_with_id.append(item)
                else:
                    # 如果启用基于内容的ID生成，为无ID数据生成ID
                    if use_content_based_id and "text" in item and "translation" in item:
                        content_id = self.generate_content_based_id(item["text"], item["translation"])
                        item["id"] = content_id
                        data_with_id.append(item)
                        logger.info(f"为内容生成ID: {content_id}")
                    else:
                        data_without_id.append(item)

            total_count = 0

            # 处理有ID的数据 - 使用upsert
            if data_with_id:
                upsert_params = {
                    "collection_name": self.collection_name,
                    "data": data_with_id
                }
                if partition_name:
                    upsert_params["partition_name"] = partition_name

                upsert_result = self.client.upsert(**upsert_params)
                upsert_count = upsert_result.get('upsert_count', len(data_with_id))
                total_count += upsert_count
                logger.info(f"成功upsert {upsert_count} 条有ID的记录")

            # 处理无ID的数据 - 使用insert
            inserted_ids = []
            if data_without_id:
                insert_params = {
                    "collection_name": self.collection_name,
                    "data": data_without_id
                }
                if partition_name:
                    insert_params["partition_name"] = partition_name

                insert_result = self.client.insert(**insert_params)
                insert_count = insert_result.get('insert_count', len(data_without_id))
                total_count += insert_count

                # 获取插入的ID列表
                if 'ids' in insert_result:
                    inserted_ids = insert_result['ids']
                    logger.info(f"成功insert {insert_count} 条无ID的记录，生成的ID: {inserted_ids}")
                else:
                    logger.info(f"成功insert {insert_count} 条无ID的记录")

            logger.info(f"总共处理 {total_count} 条记录到集合 {self.collection_name}")

            result = {"upsert_count": total_count}
            if inserted_ids:
                result["inserted_ids"] = inserted_ids
            return result

        except Exception as e:
            logger.error(f"Upsert数据时出错: {e}")
            raise

    def delete_data(
        self,
        ids: Optional[Union[List[Union[str, int]], str, int]] = None,
        filter_expr: Optional[str] = None,
        partition_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从Milvus集合中删除数据

        可以通过主键ID或过滤表达式来删除数据。

        参数:
            ids (Optional[Union[List[Union[str, int]], str, int]]): 要删除的实体ID或ID列表
            filter_expr (Optional[str]): 过滤表达式，用于批量删除满足条件的实体
            partition_name (Optional[str]): 目标分区名称，如果为None则在所有分区中删除

        返回:
            Dict[str, Any]: 包含操作结果的字典，包含delete_count字段

        Raises:
            ValueError: 如果既没有提供ids也没有提供filter_expr
            Exception: 如果删除过程中发生Milvus客户端错误
        """
        try:
            # 检查参数
            if ids is None and filter_expr is None:
                raise ValueError("必须提供ids或filter_expr中的至少一个参数")

            if ids is not None and filter_expr is not None:
                raise ValueError("不能同时提供ids和filter_expr参数")

            # 确保集合存在
            if not self.client.has_collection(self.collection_name):
                raise ValueError(f"集合 {self.collection_name} 不存在")

            # 构建删除参数
            delete_params = {
                "collection_name": self.collection_name
            }

            if partition_name:
                delete_params["partition_name"] = partition_name

            if ids is not None:
                delete_params["ids"] = ids
                logger.info(f"准备删除ID为 {ids} 的记录")
            else:
                delete_params["filter"] = filter_expr
                logger.info(f"准备删除满足条件 '{filter_expr}' 的记录")

            # 执行删除操作
            result = self.client.delete(**delete_params)

            delete_count = result.get('delete_count', 0)
            logger.info(f"成功删除 {delete_count} 条记录从集合 {self.collection_name}")
            return result

        except Exception as e:
            logger.error(f"删除数据时出错: {e}")
            raise


