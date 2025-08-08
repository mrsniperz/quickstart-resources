"""文本嵌入模型客户端

功能描述:
- 支持智谱AI Embedding-3、BGE-M3、Qwen3-Embedding三种模型
- 区分API调用和本地化安装两种方式
- 本地化模型自动处理下载和路径加载
- 提供统一的文本嵌入接口

创建日期: 2025-08-08
作者: Sniperz
版本: 1.0.0
"""

import os
import numpy as np
from typing import List, Union, Optional, Dict, Any
from pathlib import Path
from abc import ABC, abstractmethod

# 第三方库导入（按需导入，避免启动时的依赖问题）
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from zhipuai import ZhipuAI
    ZHIPUAI_AVAILABLE = True
except ImportError:
    ZHIPUAI_AVAILABLE = False

from src.utils.logger import SZ_LoggerManager

# 配置日志
logger = SZ_LoggerManager.get_logger(__name__)

# 环境变量名称
ENV_ZHIPU_API_KEY = "ZHIPU_API_KEY"
ENV_OPENAI_API_KEY = "OPENAI_API_KEY"

# 模型配置
MODEL_CONFIGS = {
    # 智谱AI Embedding-3
    "embedding-3": {
        "type": "api",
        "provider": "zhipu",
        "model_id": "embedding-3",
        "max_tokens": 8192,
        "default_dimensions": 1024,
        "supported_dimensions": [64, 128, 256, 512, 768, 1024],
        "price_per_million_tokens": 0.5
    },
    
    # BGE-M3 (本地化模型)
    "bge-m3": {
        "type": "local",
        "provider": "baai",
        "model_id": "BAAI/bge-m3",
        "max_tokens": 8192,
        "default_dimensions": 1024,
        "supported_modes": ["dense", "sparse", "colbert"],
        "local_path": None  # 将在运行时设置
    },
    
    # Qwen3-Embedding (本地化模型)
    "qwen3-embedding-0.6b": {
        "type": "local",
        "provider": "qwen",
        "model_id": "Qwen/Qwen3-Embedding-0.6B",
        "max_tokens": 8192,
        "default_dimensions": 1024,
        "model_size": "0.6B",
        "local_path": None  # 将在运行时设置
    }
}


class BaseEmbeddingProvider(ABC):
    """嵌入模型提供者基类"""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        self.model_name = model_name
        self.config = config
        self.is_initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化模型"""
        pass
    
    @abstractmethod
    def embed_texts(self, texts: Union[str, List[str]], **kwargs) -> Union[List[float], List[List[float]]]:
        """文本嵌入"""
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """获取嵌入维度"""
        pass


class ZhipuEmbeddingProvider(BaseEmbeddingProvider):
    """智谱AI Embedding-3 API提供者"""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, config)
        self.client = None
        self.api_key = os.environ.get(ENV_ZHIPU_API_KEY)
    
    def initialize(self) -> bool:
        """初始化智谱AI客户端"""
        if not ZHIPUAI_AVAILABLE:
            logger.error("zhipuai库未安装，请运行: pip install zhipuai")
            return False
        
        if not self.api_key:
            logger.error(f"未找到智谱API密钥({ENV_ZHIPU_API_KEY}环境变量)")
            return False
        
        try:
            self.client = ZhipuAI(api_key=self.api_key)
            self.is_initialized = True
            logger.info("智谱AI Embedding-3客户端初始化成功")
            return True
        except Exception as e:
            logger.error(f"智谱AI客户端初始化失败: {e}")
            return False
    
    def embed_texts(self, texts: Union[str, List[str]], dimensions: Optional[int] = None, **kwargs) -> Union[List[float], List[List[float]]]:
        """使用智谱AI Embedding-3进行文本嵌入"""
        if not self.is_initialized:
            raise RuntimeError("智谱AI客户端未初始化")
        
        # 确保输入是列表格式
        if isinstance(texts, str):
            texts = [texts]
            single_text = True
        else:
            single_text = False
        
        # 设置维度参数
        if dimensions is None:
            dimensions = self.config.get("default_dimensions", 1024)
        
        if dimensions not in self.config.get("supported_dimensions", [1024]):
            logger.warning(f"不支持的维度 {dimensions}，使用默认维度 {self.config['default_dimensions']}")
            dimensions = self.config["default_dimensions"]
        
        try:
            # 调用智谱AI API
            response = self.client.embeddings.create(
                model=self.config["model_id"],
                input=texts,
                dimensions=dimensions
            )
            
            # 提取嵌入向量
            embeddings = []
            for data in response.data:
                embeddings.append(data.embedding)
            
            logger.info(f"成功生成 {len(embeddings)} 个嵌入向量，维度: {dimensions}")
            
            # 如果输入是单个文本，返回单个向量
            if single_text:
                return embeddings[0]
            return embeddings
            
        except Exception as e:
            logger.error(f"智谱AI嵌入生成失败: {e}")
            raise
    
    def get_embedding_dimension(self, dimensions: Optional[int] = None) -> int:
        """获取嵌入维度"""
        if dimensions is None:
            return self.config.get("default_dimensions", 1024)
        return dimensions


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """本地化嵌入模型提供者"""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, config)
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu" if TRANSFORMERS_AVAILABLE else "cpu"
        self.model_cache_dir = Path.home() / ".cache" / "embedding_models"
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def initialize(self) -> bool:
        """初始化本地模型"""
        if not TRANSFORMERS_AVAILABLE and not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("transformers或sentence-transformers库未安装")
            logger.error("请运行: pip install transformers sentence-transformers torch")
            return False
        
        model_id = self.config["model_id"]
        local_path = self._get_local_model_path(model_id)
        
        try:
            # 检查本地是否已有模型
            if self._is_model_downloaded(local_path):
                logger.info(f"从本地加载模型: {local_path}")
                self._load_local_model(local_path)
            else:
                logger.info(f"本地未找到模型，开始下载: {model_id}")
                if self._download_model(model_id, local_path):
                    self._load_local_model(local_path)
                else:
                    return False
            
            self.is_initialized = True
            logger.info(f"本地模型 {model_id} 初始化成功，设备: {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"本地模型初始化失败: {e}")
            return False
    
    def _get_local_model_path(self, model_id: str) -> Path:
        """获取本地模型路径"""
        # 将模型ID转换为安全的文件夹名称
        safe_name = model_id.replace("/", "_").replace("\\", "_")
        return self.model_cache_dir / safe_name
    
    def _is_model_downloaded(self, local_path: Path) -> bool:
        """检查模型是否已下载"""
        if not local_path.exists():
            return False
        
        # 检查必要的模型文件是否存在
        required_files = ["config.json"]
        if self.config["provider"] == "baai":  # BGE-M3
            required_files.extend(["pytorch_model.bin", "tokenizer.json"])
        elif self.config["provider"] == "qwen":  # Qwen3-Embedding
            required_files.extend(["model.safetensors", "tokenizer.json"])
        
        for file_name in required_files:
            if not (local_path / file_name).exists():
                return False
        
        return True
    
    def _download_model(self, model_id: str, local_path: Path) -> bool:
        """下载模型到本地"""
        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE and self.config["provider"] == "baai":
                # 使用sentence-transformers下载BGE-M3
                logger.info("使用sentence-transformers下载BGE-M3模型...")
                model = SentenceTransformer(model_id, cache_folder=str(self.model_cache_dir.parent))
                # 将模型保存到指定路径
                model.save(str(local_path))
                
            elif TRANSFORMERS_AVAILABLE:
                # 使用transformers下载模型
                logger.info(f"使用transformers下载模型: {model_id}")
                from transformers import AutoModel, AutoTokenizer
                
                # 下载tokenizer和model
                tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=str(local_path))
                model = AutoModel.from_pretrained(model_id, cache_dir=str(local_path))
                
                # 保存到本地
                tokenizer.save_pretrained(str(local_path))
                model.save_pretrained(str(local_path))
            
            else:
                logger.error("无可用的模型下载库")
                return False
            
            logger.info(f"模型下载完成: {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"模型下载失败: {e}")
            return False
    
    def _load_local_model(self, local_path: Path):
        """加载本地模型"""
        if self.config["provider"] == "baai" and SENTENCE_TRANSFORMERS_AVAILABLE:
            # 加载BGE-M3模型
            self.model = SentenceTransformer(str(local_path), device=self.device)
            
        elif TRANSFORMERS_AVAILABLE:
            # 加载transformers模型
            self.tokenizer = AutoTokenizer.from_pretrained(str(local_path))
            self.model = AutoModel.from_pretrained(str(local_path)).to(self.device)
            self.model.eval()
        
        else:
            raise RuntimeError("无可用的模型加载库")
    
    def embed_texts(self, texts: Union[str, List[str]], **kwargs) -> Union[List[float], List[List[float]]]:
        """使用本地模型进行文本嵌入"""
        if not self.is_initialized:
            raise RuntimeError("本地模型未初始化")
        
        # 确保输入是列表格式
        if isinstance(texts, str):
            texts = [texts]
            single_text = True
        else:
            single_text = False
        
        try:
            if self.config["provider"] == "baai" and hasattr(self.model, 'encode'):
                # BGE-M3使用sentence-transformers
                embeddings = self.model.encode(texts, normalize_embeddings=True)
                embeddings = embeddings.tolist()
                
            elif TRANSFORMERS_AVAILABLE and self.tokenizer and self.model:
                # 使用transformers进行嵌入
                embeddings = []
                for text in texts:
                    # 分词
                    inputs = self.tokenizer(text, return_tensors="pt", truncation=True, 
                                          max_length=self.config.get("max_tokens", 512))
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                    
                    # 获取嵌入
                    with torch.no_grad():
                        outputs = self.model(**inputs)
                        # 使用[CLS]标记的嵌入或平均池化
                        if hasattr(outputs, 'last_hidden_state'):
                            embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()  # [CLS] token
                        else:
                            embedding = outputs.pooler_output.cpu().numpy()
                        
                        embeddings.append(embedding.flatten().tolist())
            
            else:
                raise RuntimeError("无可用的嵌入生成方法")
            
            logger.info(f"成功生成 {len(embeddings)} 个本地嵌入向量")
            
            # 如果输入是单个文本，返回单个向量
            if single_text:
                return embeddings[0]
            return embeddings
            
        except Exception as e:
            logger.error(f"本地嵌入生成失败: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """获取嵌入维度"""
        if self.is_initialized and hasattr(self.model, 'get_sentence_embedding_dimension'):
            return self.model.get_sentence_embedding_dimension()
        return self.config.get("default_dimensions", 1024)


class EmbeddingClient:
    """统一的嵌入模型客户端"""
    
    def __init__(self):
        """初始化嵌入客户端"""
        self.providers: Dict[str, BaseEmbeddingProvider] = {}
        self.current_model = None
        logger.info("嵌入客户端初始化完成")
    
    def list_available_models(self) -> List[str]:
        """列出可用的嵌入模型"""
        return list(MODEL_CONFIGS.keys())
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """获取模型信息"""
        return MODEL_CONFIGS.get(model_name)
    
    def initialize_model(self, model_name: str) -> bool:
        """初始化指定的嵌入模型"""
        if model_name not in MODEL_CONFIGS:
            logger.error(f"不支持的模型: {model_name}")
            return False
        
        # 如果已经初始化过，直接返回
        if model_name in self.providers and self.providers[model_name].is_initialized:
            self.current_model = model_name
            logger.info(f"模型 {model_name} 已初始化")
            return True
        
        config = MODEL_CONFIGS[model_name]
        
        # 根据模型类型创建对应的提供者
        if config["type"] == "api" and config["provider"] == "zhipu":
            provider = ZhipuEmbeddingProvider(model_name, config)
        elif config["type"] == "local":
            provider = LocalEmbeddingProvider(model_name, config)
        else:
            logger.error(f"不支持的模型类型: {config['type']}")
            return False
        
        # 初始化提供者
        if provider.initialize():
            self.providers[model_name] = provider
            self.current_model = model_name
            logger.info(f"模型 {model_name} 初始化成功")
            return True
        else:
            logger.error(f"模型 {model_name} 初始化失败")
            return False
    
    def embed_text(self, text: str, model_name: Optional[str] = None, **kwargs) -> List[float]:
        """对单个文本进行嵌入"""
        return self.embed_texts([text], model_name, **kwargs)[0]
    
    def embed_texts(self, texts: List[str], model_name: Optional[str] = None, **kwargs) -> List[List[float]]:
        """对多个文本进行嵌入"""
        # 确定使用的模型
        if model_name is None:
            model_name = self.current_model
        
        if model_name is None:
            raise ValueError("未指定模型且无当前模型")
        
        # 确保模型已初始化
        if model_name not in self.providers or not self.providers[model_name].is_initialized:
            if not self.initialize_model(model_name):
                raise RuntimeError(f"模型 {model_name} 初始化失败")
        
        # 执行嵌入
        provider = self.providers[model_name]
        embeddings = provider.embed_texts(texts, **kwargs)
        
        # 确保返回格式一致
        if isinstance(embeddings[0], (int, float)):
            # 单个向量，转换为列表格式
            return [embeddings]
        return embeddings
    
    def get_embedding_dimension(self, model_name: Optional[str] = None, **kwargs) -> int:
        """获取嵌入维度"""
        if model_name is None:
            model_name = self.current_model
        
        if model_name is None:
            raise ValueError("未指定模型且无当前模型")
        
        if model_name not in self.providers:
            if not self.initialize_model(model_name):
                raise RuntimeError(f"模型 {model_name} 初始化失败")
        
        return self.providers[model_name].get_embedding_dimension(**kwargs)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """计算两个嵌入向量的余弦相似度"""
        try:
            # 转换为numpy数组
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # 计算余弦相似度
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"相似度计算失败: {e}")
            return 0.0
    
    def batch_similarity(self, query_embedding: List[float], 
                        candidate_embeddings: List[List[float]]) -> List[float]:
        """批量计算查询向量与候选向量的相似度"""
        similarities = []
        for candidate in candidate_embeddings:
            similarity = self.calculate_similarity(query_embedding, candidate)
            similarities.append(similarity)
        return similarities


# 全局客户端实例
embedding_client = EmbeddingClient()


def embed_text(text: str, model_name: str = "embedding-3", **kwargs) -> List[float]:
    """简化的单文本嵌入接口"""
    return embedding_client.embed_text(text, model_name, **kwargs)


def embed_texts(texts: List[str], model_name: str = "embedding-3", **kwargs) -> List[List[float]]:
    """简化的多文本嵌入接口"""
    return embedding_client.embed_texts(texts, model_name, **kwargs)


def calculate_similarity(text1: str, text2: str, model_name: str = "embedding-3", **kwargs) -> float:
    """计算两个文本的相似度"""
    embeddings = embed_texts([text1, text2], model_name, **kwargs)
    return embedding_client.calculate_similarity(embeddings[0], embeddings[1])


# 设置API密钥的辅助函数
def set_api_keys(zhipu_api_key: Optional[str] = None):
    """手动设置API密钥"""
    if zhipu_api_key:
        os.environ[ENV_ZHIPU_API_KEY] = zhipu_api_key
        logger.info("智谱API密钥已设置")


if __name__ == "__main__":
    # 使用示例
    print("=== 嵌入模型客户端测试 ===")
    
    # 列出可用模型
    print("可用模型:", embedding_client.list_available_models())
    
    # 测试文本
    test_texts = [
        "人工智能是计算机科学的一个分支",
        "机器学习是人工智能的重要组成部分",
        "今天天气很好，适合出门散步"
    ]
    
    # 测试智谱AI Embedding-3 (需要API密钥)
    try:
        print("\n--- 测试智谱AI Embedding-3 ---")
        if embedding_client.initialize_model("embedding-3"):
            embeddings = embedding_client.embed_texts(test_texts, "embedding-3")
            print(f"生成嵌入向量数量: {len(embeddings)}")
            print(f"向量维度: {len(embeddings[0])}")
            
            # 计算相似度
            sim = embedding_client.calculate_similarity(embeddings[0], embeddings[1])
            print(f"前两个文本相似度: {sim:.4f}")
        else:
            print("智谱AI模型初始化失败")
    except Exception as e:
        print(f"智谱AI测试失败: {e}")
    
    # 测试本地BGE-M3模型
    try:
        print("\n--- 测试BGE-M3本地模型 ---")
        if embedding_client.initialize_model("bge-m3"):
            embeddings = embedding_client.embed_texts(test_texts, "bge-m3")
            print(f"生成嵌入向量数量: {len(embeddings)}")
            print(f"向量维度: {len(embeddings[0])}")
            
            # 计算相似度
            sim = embedding_client.calculate_similarity(embeddings[0], embeddings[1])
            print(f"前两个文本相似度: {sim:.4f}")
        else:
            print("BGE-M3模型初始化失败")
    except Exception as e:
        print(f"BGE-M3测试失败: {e}")
