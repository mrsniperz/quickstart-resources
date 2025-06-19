#!/usr/bin/env python3
"""
模块名称: test_chunking_complete
功能描述: RAG Flow文档分块功能完整测试脚本，支持所有可用的分块策略
创建日期: 2025-06-19
作者: Sniperz
版本: v1.0.0

使用说明:
    python test_chunking_complete.py --demo                    # 运行演示模式
    python test_chunking_complete.py -i document.txt          # 测试文件
    python test_chunking_complete.py -t "测试文本"             # 测试直接输入的文本
    python test_chunking_complete.py --performance             # 性能测试模式
    python test_chunking_complete.py -s recursive --chunk-size 500  # 自定义参数
    python test_chunking_complete.py --list-strategies         # 列出可用策略

支持的分块策略（根据环境自动检测）:
    - recursive: 递归字符分块器
    - semantic: 语义分块器
    - structure: 结构分块器
    - aviation_maintenance: 航空维修文档分块器
    - aviation_regulation: 航空规章分块器
    - aviation_standard: 航空标准分块器
    - aviation_training: 航空培训分块器
"""

import argparse
import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入基础模块
try:
    from core.document_processor.chunking.chunking_engine import (
        ChunkingEngine, ChunkType, ChunkMetadata, TextChunk, ChunkingStrategy
    )
    CHUNKING_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"导入ChunkingEngine失败: {e}")
    print("将使用简化版本的测试功能")
    CHUNKING_ENGINE_AVAILABLE = False

# 尝试导入日志管理器
try:
    from utils.logger import SZ_LoggerManager
    USE_CUSTOM_LOGGER = True
except ImportError:
    USE_CUSTOM_LOGGER = False


class SafeChunkingEngine:
    """
    安全的分块引擎包装器
    
    能够优雅地处理缺失的依赖，只加载可用的分块策略
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化安全分块引擎
        
        Args:
            config: 分块引擎配置参数
        """
        self.config = config or {}
        
        # 设置日志记录器
        if USE_CUSTOM_LOGGER:
            self.logger = SZ_LoggerManager.setup_logger(
                logger_name="safe_chunking_engine",
                log_file="chunking_test.log",
                level=logging.INFO
            )
        else:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger("safe_chunking_engine")
        
        self.strategies = {}
        self.available_strategies = []
        
        if CHUNKING_ENGINE_AVAILABLE:
            try:
                # 使用完整的ChunkingEngine
                self.engine = ChunkingEngine(self.config)
                self.available_strategies = self.engine.get_available_strategies()
                self.logger.info(f"成功加载ChunkingEngine，可用策略: {self.available_strategies}")
            except Exception as e:
                self.logger.error(f"ChunkingEngine初始化失败: {e}")
                self.engine = None
        else:
            self.engine = None
            self.logger.warning("ChunkingEngine不可用，将使用简化模式")
    
    def chunk_document(self, text_content: str, document_metadata: Dict[str, Any],
                      strategy_name: Optional[str] = None) -> List:
        """
        执行文档分块
        
        Args:
            text_content: 文档文本内容
            document_metadata: 文档元数据
            strategy_name: 指定的分块策略名称
            
        Returns:
            list: 分块结果列表
        """
        if self.engine:
            return self.engine.chunk_document(text_content, document_metadata, strategy_name)
        else:
            # 简化模式：基本的文本分块
            return self._simple_chunk(text_content, document_metadata)
    
    def _simple_chunk(self, text: str, metadata: Dict[str, Any]) -> List:
        """
        简化的文本分块实现，支持RecursiveCharacterChunker的基本功能

        Args:
            text: 待分块的文本
            metadata: 文档元数据

        Returns:
            list: 简化的分块结果
        """
        chunk_size = self.config.get('chunk_size', 1000)
        chunk_overlap = self.config.get('chunk_overlap', 200)
        separators = self.config.get('separators', ['\n\n', '\n', '。', '！', '？', '.', '!', '?', '；', ';', '，', ',', ' '])
        keep_separator = self.config.get('keep_separator', True)
        is_separator_regex = self.config.get('is_separator_regex', False)
        strip_whitespace = self.config.get('strip_whitespace', True)

        # 递归分块函数
        def _split_text_with_separators(text: str, separators: List[str]) -> List[str]:
            """使用分隔符递归分割文本"""
            if not separators or len(text) <= chunk_size:
                return [text] if text.strip() else []

            separator = separators[0]
            remaining_separators = separators[1:]

            # 分割文本
            if is_separator_regex:
                import re
                parts = re.split(separator, text)
            else:
                parts = text.split(separator)

            # 重新组合分块
            chunks = []
            current_chunk = ""

            for i, part in enumerate(parts):
                # 添加分隔符（如果需要保留）
                if keep_separator and i > 0:
                    if is_separator_regex:
                        # 对于正则表达式，我们无法准确恢复原始分隔符，使用第一个字符作为近似
                        current_chunk += separator[0] if separator else ""
                    else:
                        current_chunk += separator

                # 检查添加这部分后是否超过大小限制
                potential_chunk = current_chunk + part

                if len(potential_chunk) <= chunk_size:
                    current_chunk = potential_chunk
                else:
                    # 如果当前块不为空，先保存它
                    if current_chunk.strip():
                        chunks.append(current_chunk)

                    # 如果这部分本身就太大，需要进一步分割
                    if len(part) > chunk_size:
                        sub_chunks = _split_text_with_separators(part, remaining_separators)
                        chunks.extend(sub_chunks)
                        current_chunk = ""
                    else:
                        current_chunk = part

            # 添加最后的块
            if current_chunk.strip():
                chunks.append(current_chunk)

            return chunks

        # 执行分块
        text_chunks = _split_text_with_separators(text, separators)

        # 处理重叠
        final_chunks = []
        for i, chunk_text in enumerate(text_chunks):
            if strip_whitespace:
                chunk_text = chunk_text.strip()

            if not chunk_text:
                continue

            # 计算在原文中的位置
            start_pos = text.find(chunk_text) if i == 0 else None
            end_pos = start_pos + len(chunk_text) if start_pos is not None else None

            # 处理重叠内容
            overlap_content = None
            if i > 0 and chunk_overlap > 0:
                prev_chunk = text_chunks[i-1]
                if len(prev_chunk) > chunk_overlap:
                    overlap_content = prev_chunk[-chunk_overlap:]

            # 创建分块对象
            chunk = {
                'content': chunk_text,
                'character_count': len(chunk_text),
                'word_count': len(chunk_text.split()),
                'quality_score': 0.8,  # 默认质量评分
                'overlap_content': overlap_content,
                'metadata': {
                    'chunk_id': f"simple_{i:04d}",
                    'chunk_type': 'paragraph',
                    'start_position': start_pos,
                    'end_position': end_pos,
                    'source_document': metadata.get('file_name', 'unknown')
                }
            }

            final_chunks.append(chunk)

        return final_chunks
    
    def get_available_strategies(self) -> List[str]:
        """获取可用的分块策略列表"""
        if self.engine:
            return self.engine.get_available_strategies()
        else:
            return ['simple']
    
    def get_strategy_info(self, strategy_name: str) -> Dict[str, Any]:
        """获取策略信息"""
        if self.engine:
            return self.engine.get_strategy_info(strategy_name)
        else:
            if strategy_name == 'simple':
                return {
                    'name': 'simple',
                    'class_name': 'SimpleChunker',
                    'strategy_name': 'simple',
                    'description': '简化的文本分块器，用于测试环境'
                }
            else:
                return {'error': f'策略不存在: {strategy_name}'}
    
    def validate_chunks(self, chunks: List) -> Dict[str, Any]:
        """验证分块结果"""
        if self.engine and hasattr(self.engine, 'validate_chunks'):
            # 如果chunks是简化格式，需要转换
            if chunks and isinstance(chunks[0], dict):
                # 简化格式，直接计算统计信息
                return self._simple_validate(chunks)
            else:
                return self.engine.validate_chunks(chunks)
        else:
            return self._simple_validate(chunks)
    
    def _simple_validate(self, chunks: List) -> Dict[str, Any]:
        """简化的分块验证"""
        if not chunks:
            return {'total_chunks': 0, 'valid_chunks': 0, 'invalid_chunks': 0}
        
        total_chars = 0
        quality_scores = []
        min_size = float('inf')
        max_size = 0
        
        for chunk in chunks:
            if isinstance(chunk, dict):
                char_count = chunk.get('character_count', 0)
                quality = chunk.get('quality_score', 0.5)
            else:
                char_count = getattr(chunk, 'character_count', 0)
                quality = getattr(chunk, 'quality_score', 0.5)
            
            total_chars += char_count
            quality_scores.append(quality)
            min_size = min(min_size, char_count)
            max_size = max(max_size, char_count)
        
        return {
            'total_chunks': len(chunks),
            'valid_chunks': len(chunks),
            'invalid_chunks': 0,
            'quality_scores': quality_scores,
            'avg_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'size_distribution': {
                'min_size': min_size if min_size != float('inf') else 0,
                'max_size': max_size,
                'avg_size': total_chars / len(chunks) if chunks else 0
            },
            'issues': []
        }


class ChunkingTester:
    """
    文档分块测试器
    
    提供全面的文档分块功能测试，包括：
    - 多种分块策略测试
    - 分块效果可视化
    - 性能统计分析
    - 参数调优建议
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化测试器
        
        Args:
            config: 分块引擎配置参数
        """
        self.config = config or {}
        
        # 设置日志记录器
        if USE_CUSTOM_LOGGER:
            self.logger = SZ_LoggerManager.setup_logger(
                logger_name="chunking_tester",
                log_file="chunking_test.log",
                level=logging.INFO
            )
        else:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger("chunking_tester")
        
        try:
            # 创建安全的分块引擎
            self.engine = SafeChunkingEngine(self.config)
            self.logger.info("分块测试器初始化成功")
        except Exception as e:
            self.logger.error(f"分块测试器初始化失败: {e}")
            raise
    
    def test_chunking(self, text: str, metadata: Dict[str, Any], 
                     strategy_name: Optional[str] = None) -> Dict[str, Any]:
        """
        执行分块测试
        
        Args:
            text: 待分块的文本
            metadata: 文档元数据
            strategy_name: 指定的分块策略名称
            
        Returns:
            dict: 测试结果，包含分块结果和统计信息
        """
        try:
            start_time = time.time()
            
            # 执行分块
            chunks = self.engine.chunk_document(text, metadata, strategy_name)
            
            processing_time = time.time() - start_time
            
            # 计算统计信息
            stats = self._calculate_statistics(chunks, processing_time, len(text))
            
            # 验证分块结果
            validation = self.engine.validate_chunks(chunks)
            
            return {
                'chunks': chunks,
                'statistics': stats,
                'validation': validation,
                'processing_time': processing_time,
                'strategy_used': strategy_name or 'auto'
            }
            
        except Exception as e:
            self.logger.error(f"分块测试失败: {e}")
            raise
    
    def _calculate_statistics(self, chunks: List, processing_time: float, 
                            original_length: int) -> Dict[str, Any]:
        """
        计算分块统计信息
        
        Args:
            chunks: 分块结果列表
            processing_time: 处理时间
            original_length: 原文长度
            
        Returns:
            dict: 统计信息
        """
        if not chunks:
            return {
                'chunk_count': 0,
                'total_characters': 0,
                'average_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0,
                'processing_speed': 0,
                'coverage_rate': 0
            }
        
        # 处理不同格式的chunks
        chunk_sizes = []
        total_chars = 0
        
        for chunk in chunks:
            if isinstance(chunk, dict):
                char_count = chunk.get('character_count', 0)
            else:
                char_count = getattr(chunk, 'character_count', 0)
            
            chunk_sizes.append(char_count)
            total_chars += char_count
        
        return {
            'chunk_count': len(chunks),
            'total_characters': total_chars,
            'average_chunk_size': total_chars / len(chunks),
            'min_chunk_size': min(chunk_sizes) if chunk_sizes else 0,
            'max_chunk_size': max(chunk_sizes) if chunk_sizes else 0,
            'processing_speed': original_length / processing_time if processing_time > 0 else 0,
            'coverage_rate': (total_chars / original_length) * 100 if original_length > 0 else 0
        }
    
    def list_available_strategies(self) -> None:
        """列出所有可用的分块策略"""
        print("\n" + "="*80)
        print("📋 可用的分块策略")
        print("="*80)

        strategies = self.engine.get_available_strategies()

        if not strategies:
            print("❌ 没有可用的分块策略")
            return

        for strategy in strategies:
            info = self.engine.get_strategy_info(strategy)
            print(f"\n🔸 {strategy}")
            print(f"   类名: {info.get('class_name', '未知')}")
            print(f"   描述: {info.get('description', '无描述')}")

            if 'error' in info:
                print(f"   ❌ 错误: {info['error']}")

    def show_recursive_separators(self) -> None:
        """显示RecursiveCharacterChunker的默认分隔符列表"""
        print("\n" + "="*80)
        print("📝 RecursiveCharacterChunker 默认分隔符列表")
        print("="*80)

        # 获取默认分隔符列表
        default_separators = [
            # 段落分隔符
            "\\n\\n", "\\n\\n\\n",

            # 中文段落标记
            "\\n第", "\\n章", "\\n节", "\\n条",

            # 英文段落标记
            "\\nChapter", "\\nSection", "\\nArticle",

            # 列表和编号
            "\\n\\n•", "\\n\\n-", "\\n\\n*", "\\n\\n1.", "\\n\\n2.", "\\n\\n3.",

            # 单行分隔符
            "\\n",

            # 句子分隔符
            "。", "！", "？", ".", "!", "?",

            # 子句分隔符
            "；", ";", "，", ",",

            # 词语分隔符
            " ", "\\t",

            # 中文标点
            "、", "：", ":",

            # 零宽字符
            "\\u200b", "\\uff0c", "\\u3001", "\\uff0e", "\\u3002",

            # 最后的回退选项
            '""'
        ]

        print("📌 分隔符按优先级从高到低排序：")
        print("\n🔹 段落级分隔符:")
        for sep in default_separators[:13]:
            print(f"   '{sep}'")

        print("\n🔹 句子级分隔符:")
        for sep in default_separators[13:19]:
            print(f"   '{sep}'")

        print("\n🔹 子句级分隔符:")
        for sep in default_separators[19:23]:
            print(f"   '{sep}'")

        print("\n🔹 词语级分隔符:")
        for sep in default_separators[23:28]:
            print(f"   '{sep}'")

        print("\n🔹 特殊字符:")
        for sep in default_separators[28:]:
            print(f"   '{sep}'")

        print(f"\n💡 使用说明:")
        print(f"   • 分块器会按优先级依次尝试这些分隔符")
        print(f"   • 如果使用某个分隔符分割后的片段仍然太大，会尝试下一个分隔符")
        print(f"   • 可以使用 --separators 参数自定义分隔符列表")
        print(f"   • 使用 --is-separator-regex 启用正则表达式模式")
        print(f"   • 使用 --no-keep-separator 不保留分隔符")
    
    def compare_strategies(self, text: str, metadata: Dict[str, Any]) -> None:
        """
        比较不同策略的分块效果
        
        Args:
            text: 待分块的文本
            metadata: 文档元数据
        """
        print("\n" + "="*80)
        print("🔍 分块策略对比分析")
        print("="*80)
        
        strategies = self.engine.get_available_strategies()
        results = {}
        
        for strategy in strategies:
            print(f"\n测试策略: {strategy}")
            try:
                result = self.test_chunking(text, metadata, strategy)
                results[strategy] = result
                
                stats = result['statistics']
                print(f"  分块数量: {stats['chunk_count']}")
                print(f"  处理时间: {result['processing_time']:.3f}秒")
                print(f"  平均大小: {stats['average_chunk_size']:.1f}字符")
                print(f"  质量评分: {result['validation'].get('avg_quality_score', 0):.3f}")
                
            except Exception as e:
                print(f"  ❌ 测试失败: {e}")
        
        # 输出对比总结
        if len(results) > 1:
            print(f"\n📊 对比总结:")
            print(f"{'策略':>15} {'分块数':>8} {'时间(s)':>10} {'平均大小':>10} {'质量':>8}")
            print("-" * 60)
            
            for strategy, result in results.items():
                stats = result['statistics']
                quality = result['validation'].get('avg_quality_score', 0)
                print(f"{strategy:>15} {stats['chunk_count']:>8} "
                      f"{result['processing_time']:>9.3f} {stats['average_chunk_size']:>9.1f} "
                      f"{quality:>7.3f}")

    def visualize_chunks(self, result: Dict[str, Any], output_format: str = 'detailed') -> None:
        """
        可视化分块结果

        Args:
            result: 测试结果
            output_format: 输出格式 ('detailed', 'simple', 'json')
        """
        chunks = result['chunks']
        stats = result['statistics']
        validation = result['validation']

        if output_format == 'json':
            self._output_json(result)
            return

        # 输出标题
        print("\n" + "="*80)
        print(f"🔍 RAG Flow 文档分块测试结果")
        print(f"📊 策略: {result['strategy_used']}")
        print(f"⏱️  处理时间: {result['processing_time']:.3f}秒")
        print("="*80)

        # 输出统计信息
        self._print_statistics(stats, validation)

        if output_format == 'detailed':
            self._print_detailed_chunks(chunks)
        else:
            self._print_simple_chunks(chunks)

    def _print_statistics(self, stats: Dict[str, Any], validation: Dict[str, Any]) -> None:
        """打印统计信息"""
        print(f"\n📈 统计信息:")
        print(f"   分块数量: {stats['chunk_count']}")
        print(f"   总字符数: {stats['total_characters']}")
        print(f"   平均分块大小: {stats['average_chunk_size']:.1f} 字符")
        print(f"   最小分块: {stats['min_chunk_size']} 字符")
        print(f"   最大分块: {stats['max_chunk_size']} 字符")
        print(f"   处理速度: {stats['processing_speed']:.0f} 字符/秒")
        print(f"   覆盖率: {stats['coverage_rate']:.1f}%")

        # 验证信息
        print(f"\n🔍 质量验证:")
        print(f"   有效分块: {validation['valid_chunks']}")
        print(f"   无效分块: {validation['invalid_chunks']}")
        print(f"   平均质量评分: {validation.get('avg_quality_score', 0):.3f}")

        if validation.get('issues'):
            print(f"   ⚠️  发现问题: {len(validation['issues'])}个")
            for issue in validation['issues'][:3]:  # 只显示前3个问题
                print(f"      - {issue}")
            if len(validation['issues']) > 3:
                print(f"      - ... 还有{len(validation['issues']) - 3}个问题")

    def _print_detailed_chunks(self, chunks: List) -> None:
        """打印详细分块信息"""
        print(f"\n📝 详细分块结果:")

        for i, chunk in enumerate(chunks, 1):
            print(f"\n--- 分块 {i} ---")

            # 处理不同格式的chunk
            if isinstance(chunk, dict):
                char_count = chunk.get('character_count', 0)
                word_count = chunk.get('word_count', 0)
                quality_score = chunk.get('quality_score', 0)
                content = chunk.get('content', '')
                overlap_content = chunk.get('overlap_content')
                metadata = chunk.get('metadata', {})
            else:
                char_count = getattr(chunk, 'character_count', 0)
                word_count = getattr(chunk, 'word_count', 0)
                quality_score = getattr(chunk, 'quality_score', 0)
                content = getattr(chunk, 'content', '')
                overlap_content = getattr(chunk, 'overlap_content', None)
                metadata = getattr(chunk, 'metadata', {})

            print(f"大小: {char_count} 字符 | 词数: {word_count}")
            print(f"质量评分: {quality_score:.3f}")

            # 显示位置信息
            if isinstance(metadata, dict):
                start_pos = metadata.get('start_position')
                end_pos = metadata.get('end_position')
            else:
                start_pos = getattr(metadata, 'start_position', None)
                end_pos = getattr(metadata, 'end_position', None)

            if start_pos is not None and end_pos is not None:
                print(f"位置: {start_pos}-{end_pos}")

            # 显示内容预览
            content_preview = content[:200] + "..." if len(content) > 200 else content
            print(f"内容: {content_preview}")

            # 显示重叠内容
            if overlap_content:
                overlap_preview = overlap_content[:100] + "..." if len(overlap_content) > 100 else overlap_content
                print(f"重叠: {overlap_preview}")

    def _print_simple_chunks(self, chunks: List) -> None:
        """打印简洁分块信息"""
        print(f"\n📋 分块概览:")

        for i, chunk in enumerate(chunks, 1):
            # 处理不同格式的chunk
            if isinstance(chunk, dict):
                char_count = chunk.get('character_count', 0)
                quality_score = chunk.get('quality_score', 0)
                content = chunk.get('content', '')
            else:
                char_count = getattr(chunk, 'character_count', 0)
                quality_score = getattr(chunk, 'quality_score', 0)
                content = getattr(chunk, 'content', '')

            content_preview = content[:50] + "..." if len(content) > 50 else content
            quality_info = f" (质量: {quality_score:.2f})" if quality_score > 0 else ""
            print(f"  {i:2d}. [{char_count:4d}字符] {content_preview}{quality_info}")

    def _output_json(self, result: Dict[str, Any]) -> None:
        """输出JSON格式结果"""
        # 转换chunks为可序列化的格式
        serializable_chunks = []
        for chunk in result['chunks']:
            if isinstance(chunk, dict):
                chunk_data = chunk.copy()
            else:
                chunk_data = {
                    'content': getattr(chunk, 'content', ''),
                    'character_count': getattr(chunk, 'character_count', 0),
                    'word_count': getattr(chunk, 'word_count', 0),
                    'quality_score': getattr(chunk, 'quality_score', 0.0),
                    'overlap_content': getattr(chunk, 'overlap_content', None),
                    'metadata': {}
                }

                # 处理metadata
                metadata = getattr(chunk, 'metadata', None)
                if metadata:
                    if isinstance(metadata, dict):
                        chunk_data['metadata'] = metadata
                    else:
                        chunk_data['metadata'] = {
                            'chunk_id': getattr(metadata, 'chunk_id', ''),
                            'chunk_type': str(getattr(metadata, 'chunk_type', '')),
                            'start_position': getattr(metadata, 'start_position', None),
                            'end_position': getattr(metadata, 'end_position', None)
                        }

            serializable_chunks.append(chunk_data)

        output = {
            'strategy_used': result['strategy_used'],
            'processing_time': result['processing_time'],
            'statistics': result['statistics'],
            'validation': result['validation'],
            'chunks': serializable_chunks
        }

        print(json.dumps(output, ensure_ascii=False, indent=2))

    def run_performance_test(self, text_sizes: List[int] = None) -> None:
        """
        运行性能测试

        Args:
            text_sizes: 测试文本大小列表（字符数）
        """
        if text_sizes is None:
            text_sizes = [1000, 5000, 10000, 50000, 100000]

        print("\n" + "="*80)
        print("🚀 性能测试模式")
        print("="*80)

        # 生成测试文本
        base_text = self._get_sample_text('performance')

        results = []

        for size in text_sizes:
            # 生成指定大小的文本
            test_text = (base_text * (size // len(base_text) + 1))[:size]

            metadata = {
                'file_name': f'performance_test_{size}.txt',
                'document_type': 'performance_test',
                'title': f'性能测试文档 ({size}字符)'
            }

            print(f"\n测试文本大小: {size:,} 字符")

            try:
                result = self.test_chunking(test_text, metadata)
                results.append({
                    'size': size,
                    'time': result['processing_time'],
                    'chunks': result['statistics']['chunk_count'],
                    'speed': result['statistics']['processing_speed']
                })

                print(f"  处理时间: {result['processing_time']:.3f}秒")
                print(f"  分块数量: {result['statistics']['chunk_count']}")
                print(f"  处理速度: {result['statistics']['processing_speed']:.0f} 字符/秒")

            except Exception as e:
                print(f"  测试失败: {e}")

        # 输出性能总结
        if results:
            print(f"\n📊 性能测试总结:")
            print(f"{'文本大小':>10} {'处理时间':>10} {'分块数':>8} {'速度':>12}")
            print("-" * 45)
            for r in results:
                print(f"{r['size']:>10,} {r['time']:>9.3f}s {r['chunks']:>7} {r['speed']:>10.0f}/s")

    def run_demo(self) -> None:
        """运行演示模式"""
        print("\n" + "="*80)
        print("🎯 RAG Flow 文档分块功能演示")
        print("="*80)

        demo_scenarios = [
            ('通用技术文档', 'general'),
            ('航空维修手册', 'aviation'),
            ('代码文档', 'code'),
            ('结构化文档', 'structured')
        ]

        for name, text_type in demo_scenarios:
            print(f"\n🔸 演示场景: {name}")
            print("-" * 40)

            text = self._get_sample_text(text_type)
            metadata = {
                'file_name': f'{text_type}_demo.txt',
                'document_type': text_type,
                'title': name
            }

            try:
                result = self.test_chunking(text, metadata)
                self.visualize_chunks(result, 'simple')
            except Exception as e:
                print(f"演示失败: {e}")

        # 添加RecursiveCharacterChunker高级功能演示
        self._demo_recursive_features()

    def _demo_recursive_features(self) -> None:
        """演示RecursiveCharacterChunker的高级功能"""
        print("\n" + "="*80)
        print("🔧 RecursiveCharacterChunker 高级功能演示")
        print("="*80)

        demo_text = "第一章：系统架构。本章介绍系统的整体架构设计。第二章：技术选型！本章详细说明各种技术的选择理由。第三章：实施方案？本章描述具体的实施步骤和注意事项。"

        demo_configs = [
            {
                'name': '默认配置',
                'config': {'chunk_size': 30, 'chunk_overlap': 5},
                'description': '使用默认分隔符和配置'
            },
            {
                'name': '自定义分隔符',
                'config': {'chunk_size': 30, 'chunk_overlap': 5, 'separators': ['。', '！', '？']},
                'description': '只使用中文句号、感叹号、问号作为分隔符'
            },
            {
                'name': '不保留分隔符',
                'config': {'chunk_size': 30, 'chunk_overlap': 5, 'separators': ['。', '！', '？'], 'keep_separator': False},
                'description': '分块时不保留分隔符'
            },
            {
                'name': '段落级分隔符',
                'config': {'chunk_size': 50, 'chunk_overlap': 10, 'separators': ['第', '章', '：']},
                'description': '使用章节标识符进行分块'
            }
        ]

        for demo in demo_configs:
            print(f"\n🔹 {demo['name']}")
            print(f"   {demo['description']}")
            print("   " + "-" * 50)

            # 临时修改配置
            original_config = self.config.copy()
            self.config.update(demo['config'])

            # 重新创建引擎
            temp_engine = SafeChunkingEngine(self.config)

            try:
                chunks = temp_engine.chunk_document(demo_text, {'file_name': 'demo.txt'})

                print(f"   分块数量: {len(chunks)}")
                for i, chunk in enumerate(chunks, 1):
                    content = chunk['content'] if isinstance(chunk, dict) else chunk.content
                    char_count = chunk['character_count'] if isinstance(chunk, dict) else chunk.character_count
                    print(f"   {i}. [{char_count:2d}字符] {content}")

            except Exception as e:
                print(f"   ❌ 演示失败: {e}")
            finally:
                # 恢复原始配置
                self.config = original_config

    def _get_sample_text(self, text_type: str) -> str:
        """获取示例文本"""
        samples = {
            'general': """
第一章 系统架构设计

1.1 概述
本系统采用微服务架构设计，具有高可用性、可扩展性和可维护性的特点。系统主要由以下几个核心模块组成：用户管理模块、数据处理模块、接口服务模块和监控模块。

1.2 技术选型
在技术选型方面，我们选择了以下技术栈：
- 后端框架：Spring Boot 2.7
- 数据库：MySQL 8.0 + Redis 6.2
- 消息队列：RabbitMQ 3.9
- 容器化：Docker + Kubernetes
- 监控：Prometheus + Grafana

1.3 系统特性
系统具备以下核心特性：
1. 高并发处理能力，支持每秒10万次请求
2. 数据一致性保证，采用分布式事务管理
3. 自动故障恢复，具备完善的容错机制
4. 实时监控告警，确保系统稳定运行
""",

            'aviation': """
任务1：发动机日常检查程序

警告：在进行任何发动机检查前，必须确保发动机完全冷却，并断开所有电源。

步骤1：外观检查
检查发动机外壳是否有裂纹、腐蚀或异常磨损。特别注意以下部位：
- 进气道和排气口
- 燃油管路连接处
- 电气线束固定点
- 冷却系统管路

步骤2：液位检查
检查各种液体的液位是否在正常范围内：
- 发动机机油液位
- 冷却液液位
- 液压油液位

注意：所有液位检查必须在发动机水平状态下进行。

步骤3：功能测试
启动发动机进行功能测试，监控以下参数：
- 发动机转速
- 油压指示
- 温度指示
- 振动水平

任务2：螺旋桨检查程序

警告：螺旋桨检查时必须确保螺旋桨完全静止，并设置安全警示标志。
""",

            'code': """
# 用户认证模块

## 概述
本模块提供完整的用户认证功能，包括登录、注册、密码重置等核心功能。

## 主要类和方法

### UserAuthenticator类
```python
class UserAuthenticator:
    def __init__(self, config):
        self.config = config
        self.session_manager = SessionManager()

    def authenticate(self, username, password):
        \"\"\"
        用户认证方法

        Args:
            username (str): 用户名
            password (str): 密码

        Returns:
            bool: 认证结果
        \"\"\"
        user = self.get_user(username)
        if user and self.verify_password(password, user.password_hash):
            return self.create_session(user)
        return False
```

### 配置说明
系统支持以下配置参数：
- SESSION_TIMEOUT: 会话超时时间（默认30分钟）
- PASSWORD_MIN_LENGTH: 密码最小长度（默认8位）
- MAX_LOGIN_ATTEMPTS: 最大登录尝试次数（默认5次）
""",

            'structured': """
# 项目管理规范文档

## 1. 项目生命周期管理

### 1.1 项目启动阶段
#### 1.1.1 需求分析
- 业务需求收集
- 技术需求分析
- 可行性研究

#### 1.1.2 项目规划
- 项目范围定义
- 时间计划制定
- 资源分配计划

### 1.2 项目执行阶段
#### 1.2.1 开发管理
- 代码开发规范
- 版本控制管理
- 代码审查流程

#### 1.2.2 质量控制
- 单元测试要求
- 集成测试流程
- 性能测试标准

## 2. 团队协作规范

### 2.1 沟通机制
- 日常站会制度
- 周报汇报机制
- 月度总结会议

### 2.2 文档管理
- 技术文档编写规范
- 文档版本控制
- 知识库维护
""",

            'performance': """
系统性能优化是一个持续的过程，需要从多个维度进行考虑和实施。首先，我们需要建立完善的性能监控体系，实时收集系统运行数据，包括CPU使用率、内存占用、磁盘I/O、网络带宽等关键指标。通过这些数据，我们可以及时发现性能瓶颈，并采取相应的优化措施。在数据库层面，我们需要优化查询语句，建立合适的索引，合理设计表结构，并考虑读写分离、分库分表等策略。在应用层面，我们可以通过缓存机制、异步处理、连接池优化等方式提升性能。同时，代码层面的优化也不容忽视，包括算法优化、内存管理、并发控制等。此外，系统架构的合理设计也是性能优化的重要因素，微服务架构、负载均衡、CDN加速等都能有效提升系统性能。最后，我们还需要建立性能测试体系，定期进行压力测试和性能基准测试，确保系统在各种负载条件下都能稳定运行。
"""
        }

        return samples.get(text_type, samples['general'])


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="RAG Flow文档分块功能完整测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --demo                           # 运行演示模式
  %(prog)s --list-strategies                # 列出可用策略
  %(prog)s --show-separators               # 显示递归分块器的默认分隔符
  %(prog)s -i document.txt                  # 测试文件
  %(prog)s -t "测试文本内容"                 # 测试直接输入
  %(prog)s --performance                    # 性能测试
  %(prog)s --compare -t "测试文本"           # 策略对比
  %(prog)s -s recursive --chunk-size 500   # 自定义参数

RecursiveCharacterChunker 高级用法:
  %(prog)s -t "文本" --separators "。" "！" "？"  # 自定义分隔符
  %(prog)s -t "文本" --is-separator-regex        # 启用正则表达式
  %(prog)s -t "文本" --no-keep-separator         # 不保留分隔符
  %(prog)s -t "文本" --add-start-index           # 添加位置索引
        """
    )

    # 输入参数
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument('--input', '-i', help='输入文件路径')
    input_group.add_argument('--text', '-t', help='直接输入文本内容')
    input_group.add_argument('--demo', action='store_true', help='运行演示模式')
    input_group.add_argument('--performance', action='store_true', help='性能测试模式')
    input_group.add_argument('--list-strategies', action='store_true', help='列出可用策略')

    # 分块参数
    parser.add_argument('--strategy', '-s', help='指定分块策略')
    parser.add_argument('--chunk-size', type=int, default=1000, help='分块大小 (默认: 1000)')
    parser.add_argument('--chunk-overlap', type=int, default=200, help='重叠大小 (默认: 200)')
    parser.add_argument('--min-chunk-size', type=int, default=100, help='最小分块大小 (默认: 100)')
    parser.add_argument('--max-chunk-size', type=int, default=2000, help='最大分块大小 (默认: 2000)')

    # RecursiveCharacterChunker 特有参数
    parser.add_argument('--separators', nargs='*', help='自定义分隔符列表（空格分隔）')
    parser.add_argument('--is-separator-regex', action='store_true', help='分隔符是否为正则表达式')
    parser.add_argument('--keep-separator', action='store_true', default=True, help='是否保留分隔符（默认: True）')
    parser.add_argument('--no-keep-separator', action='store_true', help='不保留分隔符')
    parser.add_argument('--add-start-index', action='store_true', help='添加起始索引信息')
    parser.add_argument('--no-strip-whitespace', action='store_true', help='不去除空白字符')
    parser.add_argument('--show-separators', action='store_true', help='显示默认分隔符列表')

    # 功能参数
    parser.add_argument('--compare', action='store_true', help='对比不同策略')
    parser.add_argument('--validate', action='store_true', help='详细验证分块结果')

    # 输出参数
    parser.add_argument('--output-format', choices=['detailed', 'simple', 'json'],
                       default='detailed', help='输出格式 (默认: detailed)')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式，只输出结果')

    args = parser.parse_args()

    # 构建配置
    config = {
        'chunk_size': args.chunk_size,
        'chunk_overlap': args.chunk_overlap,
        'min_chunk_size': args.min_chunk_size,
        'max_chunk_size': args.max_chunk_size,
        'preserve_context': True
    }

    # 添加 RecursiveCharacterChunker 特有配置
    if args.separators:
        config['separators'] = args.separators
    if args.is_separator_regex:
        config['is_separator_regex'] = True
    if args.no_keep_separator:
        config['keep_separator'] = False
    elif args.keep_separator:
        config['keep_separator'] = True
    if args.add_start_index:
        config['add_start_index'] = True
    if args.no_strip_whitespace:
        config['strip_whitespace'] = False

    try:
        # 创建测试器
        tester = ChunkingTester(config)

        if not args.quiet:
            print("🚀 RAG Flow 文档分块完整测试脚本启动")
            print(f"📋 当前配置: 分块大小={args.chunk_size}, 重叠={args.chunk_overlap}")

        # 根据参数执行不同的测试模式
        if args.show_separators:
            tester.show_recursive_separators()
        elif args.list_strategies:
            tester.list_available_strategies()
        elif args.demo:
            tester.run_demo()
        elif args.performance:
            tester.run_performance_test()
        elif args.compare and (args.input or args.text):
            # 策略对比模式
            if args.input:
                if not os.path.exists(args.input):
                    print(f"❌ 文件不存在: {args.input}")
                    sys.exit(1)
                with open(args.input, 'r', encoding='utf-8') as f:
                    text = f.read()
                metadata = {
                    'file_name': os.path.basename(args.input),
                    'file_path': args.input,
                    'document_type': 'user_document',
                    'title': f'用户文档: {os.path.basename(args.input)}'
                }
            else:
                text = args.text
                metadata = {
                    'file_name': 'direct_input.txt',
                    'document_type': 'direct_input',
                    'title': '直接输入文本'
                }

            tester.compare_strategies(text, metadata)

        elif args.input or args.text:
            # 单一测试模式
            if args.input:
                if not os.path.exists(args.input):
                    print(f"❌ 文件不存在: {args.input}")
                    sys.exit(1)
                with open(args.input, 'r', encoding='utf-8') as f:
                    text = f.read()
                metadata = {
                    'file_name': os.path.basename(args.input),
                    'file_path': args.input,
                    'document_type': 'user_document',
                    'title': f'用户文档: {os.path.basename(args.input)}'
                }
            else:
                text = args.text
                metadata = {
                    'file_name': 'direct_input.txt',
                    'document_type': 'direct_input',
                    'title': '直接输入文本'
                }

            result = tester.test_chunking(text, metadata, args.strategy)
            tester.visualize_chunks(result, args.output_format)

            if args.validate:
                print("\n" + "="*80)
                print("🔍 详细验证结果")
                print("="*80)
                validation = result['validation']
                print(json.dumps(validation, ensure_ascii=False, indent=2))
        else:
            # 默认显示帮助信息
            parser.print_help()
            print("\n💡 提示:")
            print("  --demo              运行演示模式")
            print("  --list-strategies   查看可用策略")
            print("  --show-separators   查看递归分块器分隔符")
            print("  --help              查看详细帮助")

    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
