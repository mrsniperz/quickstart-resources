#!/usr/bin/env python3
"""
模块名称: test_chunking_presets
功能描述: 简化分块系统预设配置测试脚本 - 适配新的预设配置架构
创建日期: 2024-01-15
作者: Sniperz
版本: v2.0.0 (简化重构版)

使用说明:
    python test_chunking_presets.py --demo                    # 运行演示模式
    python test_chunking_presets.py -i document.txt          # 测试文件
    python test_chunking_presets.py -t "测试文本"             # 测试直接输入的文本
    python test_chunking_presets.py --performance             # 性能测试模式
    python test_chunking_presets.py -p semantic --chunk-size 500  # 自定义参数
    python test_chunking_presets.py --list-presets            # 列出可用预设

支持的配置预设（基于简化架构）:
    - quick: 快速分块配置
    - standard: 标准分块配置
    - semantic: 语义分块配置（替代原semantic_chunker）
    - structure: 结构分块配置（替代原structure_chunker）
    - aviation_maintenance: 航空维修文档配置
    - aviation_regulation: 航空规章配置
    - aviation_standard: 航空标准配置
    - aviation_training: 航空培训配置
    - high_quality: 高质量分块配置
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

# 导入简化后的分块模块
try:
    from core.document_processor.chunking.chunking_engine import ChunkingEngine
    from core.document_processor.chunking.recursive_chunker import RecursiveCharacterChunker
    CHUNKING_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"导入ChunkingEngine失败: {e}")
    print("将使用简化版本的测试功能")
    CHUNKING_ENGINE_AVAILABLE = False

# 尝试导入日志管理器
try:
    from src.utils.logger import SZ_LoggerManager
    USE_CUSTOM_LOGGER = True
except ImportError:
    try:
        from utils.logger import SZ_LoggerManager
        USE_CUSTOM_LOGGER = True
    except ImportError:
        USE_CUSTOM_LOGGER = False


class SimplifiedChunkingTester:
    """
    简化分块系统测试器
    
    专门为新的预设配置架构设计，提供：
    - 预设配置测试
    - 自动预设选择测试
    - 性能基准测试
    - 配置验证
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
                logger_name="simplified_chunking_tester",
                log_file="chunking_preset_test.log",
                level=logging.INFO
            )
        else:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger("simplified_chunking_tester")
        
        try:
            if CHUNKING_ENGINE_AVAILABLE:
                # 使用简化后的ChunkingEngine
                self.engine = ChunkingEngine(self.config)
                self.logger.info("简化分块引擎初始化成功")
            else:
                self.engine = None
                self.logger.warning("ChunkingEngine不可用，将使用基础模式")
                
        except Exception as e:
            self.logger.error(f"分块测试器初始化失败: {e}")
            raise
    
    def test_preset_chunking(self, text: str, metadata: Dict[str, Any], 
                           preset_name: Optional[str] = None) -> Dict[str, Any]:
        """
        执行预设配置分块测试
        
        Args:
            text: 待分块的文本
            metadata: 文档元数据
            preset_name: 指定的预设配置名称
            
        Returns:
            dict: 测试结果，包含分块结果和统计信息
        """
        try:
            start_time = time.time()
            
            if self.engine:
                # 使用新的预设配置API
                chunks = self.engine.chunk_document(text, metadata, preset_name)
            else:
                # 基础模式：简单分块
                chunks = self._basic_chunk(text, metadata)
            
            processing_time = time.time() - start_time
            
            # 计算统计信息
            stats = self._calculate_statistics(chunks, processing_time, len(text))
            
            # 创建验证结果
            validation = self._create_validation(chunks)
            
            return {
                'chunks': chunks,
                'statistics': stats,
                'validation': validation,
                'processing_time': processing_time,
                'preset_used': preset_name or 'auto'
            }
            
        except Exception as e:
            self.logger.error(f"预设分块测试失败: {e}")
            raise
    
    def _basic_chunk(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基础分块实现（当引擎不可用时）"""
        chunk_size = self.config.get('chunk_size', 1000)
        chunks = []
        
        # 简单按大小分块
        for i in range(0, len(text), chunk_size):
            chunk_text = text[i:i + chunk_size]
            if chunk_text.strip():
                chunks.append({
                    'content': chunk_text,
                    'character_count': len(chunk_text),
                    'word_count': len(chunk_text.split()),
                    'quality_score': 0.8,
                    'metadata': {
                        'chunk_id': f"basic_{i//chunk_size:04d}",
                        'chunk_type': 'paragraph',
                        'source_document': metadata.get('file_name', 'unknown')
                    }
                })
        
        return chunks
    
    def _calculate_statistics(self, chunks: List, processing_time: float, 
                            original_length: int) -> Dict[str, Any]:
        """计算分块统计信息"""
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
    
    def _create_validation(self, chunks: List) -> Dict[str, Any]:
        """创建验证结果"""
        if not chunks:
            return {
                'total_chunks': 0,
                'valid_chunks': 0,
                'invalid_chunks': 0,
                'avg_quality_score': 0.0,
                'issues': []
            }
        
        total_chunks = len(chunks)
        quality_scores = []
        
        for chunk in chunks:
            if isinstance(chunk, dict):
                quality = chunk.get('quality_score')
            else:
                quality = getattr(chunk, 'quality_score', None)

            # 只有当质量评分不为None时才添加到列表中
            if quality is not None:
                quality_scores.append(quality)

        # 如果有质量评分，计算平均值；否则返回None表示未评估
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None
        
        return {
            'total_chunks': total_chunks,
            'valid_chunks': total_chunks,
            'invalid_chunks': 0,
            'avg_quality_score': avg_quality,
            'issues': []
        }
    
    def list_available_presets(self) -> None:
        """列出所有可用的预设配置"""
        print("\n" + "="*80)
        print("📋 可用的预设配置（简化架构）")
        print("="*80)
        
        if self.engine:
            try:
                # 获取预设配置
                config_manager = None
                try:
                    from core.document_processor.config.config_manager import get_config_manager
                    config_manager = get_config_manager()
                except ImportError:
                    try:
                        from src.core.document_processor.config.config_manager import get_config_manager
                        config_manager = get_config_manager()
                    except ImportError:
                        print("❌ 配置管理器导入失败，无法获取预设信息")
                
                if config_manager:
                    # 直接从配置文件获取预设配置
                    chunking_config = config_manager.get_chunking_config()
                    presets = chunking_config.get('presets', {})
                    
                    if not presets:
                        print("❌ 没有可用的预设配置")
                        return
                    
                    for preset_name, preset_config in presets.items():
                        print(f"\n🔸 {preset_name}")
                        print(f"   描述: {preset_config.get('description', '无描述')}")
                        print(f"   分块大小: {preset_config.get('chunk_size', '未知')}")
                        print(f"   重叠大小: {preset_config.get('chunk_overlap', '未知')}")
                        print(f"   分隔符数量: {len(preset_config.get('separators', []))}")
                else:
                    # 使用引擎的API获取预设
                    presets = self.engine.get_available_presets()
                    
                    if not presets:
                        print("❌ 没有可用的预设配置")
                        return
                    
                    for preset in presets:
                        # 跳过非预设配置项
                        if preset in ['default_strategy', 'chunk_size', 'chunk_overlap', 
                                    'min_chunk_size', 'max_chunk_size', 'preserve_context',
                                    'enable_quality_assessment', 'quality_strategy']:
                            continue
                        
                        try:
                            info = self.engine.get_preset_info(preset)
                            print(f"\n🔸 {preset}")
                            print(f"   描述: {info.get('description', '无描述')}")
                            print(f"   分块大小: {info.get('chunk_size', '未知')}")
                            print(f"   重叠大小: {info.get('chunk_overlap', '未知')}")
                            print(f"   分隔符数量: {info.get('separators_count', '未知')}")
                            
                            if 'error' in info:
                                print(f"   ❌ 错误: {info['error']}")
                        except Exception as e:
                            print(f"获取预设信息失败: {e}")
                        
            except Exception as e:
                print(f"❌ 获取预设信息失败: {e}")
        else:
            print("❌ 分块引擎不可用，无法获取预设信息")
            print("📌 基础模式支持的预设: basic")
    
    def compare_presets(self, text: str, metadata: Dict[str, Any]) -> None:
        """
        比较不同预设的分块效果
        
        Args:
            text: 待分块的文本
            metadata: 文档元数据
        """
        print("\n" + "="*80)
        print("🔍 预设配置对比分析")
        print("="*80)
        
        if not self.engine:
            print("❌ 分块引擎不可用，无法进行预设对比")
            return
        
        presets = self.engine.get_available_presets()
        results = {}
        
        # 测试主要预设
        test_presets = ['standard', 'semantic', 'structure', 'aviation_maintenance', 'high_quality']
        test_presets = [p for p in test_presets if p in presets]
        
        for preset in test_presets:
            print(f"\n测试预设: {preset}")
            try:
                result = self.test_preset_chunking(text, metadata, preset)
                results[preset] = result
                
                stats = result['statistics']
                print(f"  分块数量: {stats['chunk_count']}")
                print(f"  处理时间: {result['processing_time']:.3f}秒")
                print(f"  平均大小: {stats['average_chunk_size']:.1f}字符")
                quality_score = result['validation'].get('avg_quality_score')
                if quality_score is not None:
                    print(f"  质量评分: {quality_score:.3f}")
                else:
                    print(f"  质量评分: 未评估")
                
            except Exception as e:
                print(f"  ❌ 测试失败: {e}")
                self.logger.error(f"预设 {preset} 测试失败: {e}")
        
        # 输出对比总结
        if len(results) > 1:
            print(f"\n📊 对比总结:")
            print(f"{'预设':>15} {'分块数':>8} {'时间(s)':>10} {'平均大小':>10} {'质量':>8}")
            print("-" * 60)
            
            for preset, result in results.items():
                stats = result['statistics']
                quality = result['validation'].get('avg_quality_score', 0)
                print(f"{preset:>15} {stats['chunk_count']:>8} "
                      f"{result['processing_time']:>9.3f} {stats['average_chunk_size']:>9.1f} "
                      f"{quality:>7.3f}")

    def test_automatic_preset_selection(self, test_cases: List[Dict[str, Any]]) -> None:
        """
        测试自动预设选择功能

        Args:
            test_cases: 测试用例列表
        """
        print("\n" + "="*80)
        print("🤖 自动预设选择测试")
        print("="*80)

        if not self.engine:
            print("❌ 分块引擎不可用，无法测试自动预设选择")
            return

        for i, case in enumerate(test_cases, 1):
            print(f"\n--- 测试用例 {i} ---")
            print(f"文档元数据: {case['metadata']}")
            print(f"期望预设: {case.get('expected_preset', '未知')}")

            try:
                # 不指定预设，让引擎自动选择
                result = self.test_preset_chunking(
                    case['text'],
                    case['metadata']
                )

                print(f"实际使用预设: {result['preset_used']}")
                print(f"分块数量: {result['statistics']['chunk_count']}")

                # 检查是否符合预期
                expected = case.get('expected_preset')
                if expected and result['preset_used'] == expected:
                    print("✅ 预设选择正确")
                elif expected:
                    print(f"⚠️  预设选择不符合预期，期望: {expected}")
                else:
                    print("ℹ️  无预期预设，仅验证功能")

            except Exception as e:
                print(f"❌ 测试失败: {e}")

    def test_quality_assessment(self, text: str, metadata: Dict[str, Any]) -> None:
        """
        测试质量检测功能

        Args:
            text: 待测试的文本
            metadata: 文档元数据
        """
        print("\n" + "="*80)
        print("🔍 质量检测功能测试")
        print("="*80)

        if not self.engine:
            print("❌ 分块引擎不可用，无法测试质量检测功能")
            return

        # 测试不同质量检测策略
        quality_strategies = ['basic', 'strict', 'disabled']
        results = {}

        for strategy in quality_strategies:
            print(f"\n--- 测试质量检测策略: {strategy} ---")

            try:
                # 临时设置质量检测策略
                if hasattr(self.engine, 'set_quality_assessment_strategy'):
                    success = self.engine.set_quality_assessment_strategy(strategy)
                    if not success:
                        print(f"⚠️  设置质量检测策略失败: {strategy}")
                        continue

                # 执行分块测试
                start_time = time.time()
                result = self.test_preset_chunking(text, metadata, 'standard')
                processing_time = time.time() - start_time

                results[strategy] = result

                # 输出测试结果
                stats = result['statistics']
                validation = result['validation']

                print(f"  分块数量: {stats['chunk_count']}")
                print(f"  处理时间: {processing_time:.3f}秒")
                quality_score = validation.get('avg_quality_score')
                if quality_score is not None:
                    print(f"  平均质量评分: {quality_score:.3f}")
                else:
                    print(f"  平均质量评分: 未评估")
                print(f"  平均分块大小: {stats['average_chunk_size']:.1f}字符")

                # 分析质量检测效果
                if strategy == 'disabled':
                    print("  📝 质量检测已禁用，所有分块质量评分为默认值")
                elif strategy == 'basic':
                    print("  📝 使用基础质量检测，评估长度和完整性")
                elif strategy == 'strict':
                    print("  📝 使用严格质量检测，更高的质量标准")

            except Exception as e:
                print(f"  ❌ 测试失败: {e}")
                self.logger.error(f"质量检测策略 {strategy} 测试失败: {e}")

        # 输出对比总结
        if len(results) > 1:
            print(f"\n📊 质量检测策略对比:")
            print(f"{'策略':>10} {'分块数':>8} {'平均质量':>10} {'处理时间':>10}")
            print("-" * 45)

            for strategy, result in results.items():
                stats = result['statistics']
                validation = result['validation']
                quality_score = validation.get('avg_quality_score')
                quality_str = f"{quality_score:>9.3f}" if quality_score is not None else "    未评估"
                print(f"{strategy:>10} {stats['chunk_count']:>8} "
                      f"{quality_str} {result['processing_time']:>9.3f}s")

        # 详细质量分析
        self._analyze_quality_impact(results)

    def _analyze_quality_impact(self, results: Dict[str, Dict[str, Any]]) -> None:
        """
        分析质量检测对分块结果的影响

        Args:
            results: 不同策略的测试结果
        """
        if len(results) < 2:
            return

        print(f"\n🔬 质量检测影响分析:")

        # 获取基准结果（disabled策略）
        baseline = results.get('disabled')
        if not baseline:
            baseline = list(results.values())[0]

        baseline_stats = baseline['statistics']
        baseline_time = baseline['processing_time']

        for strategy, result in results.items():
            if strategy == 'disabled':
                continue

            stats = result['statistics']
            validation = result['validation']

            # 计算性能影响
            time_overhead = ((result['processing_time'] - baseline_time) / baseline_time) * 100
            chunk_diff = stats['chunk_count'] - baseline_stats['chunk_count']
            quality_score = validation.get('avg_quality_score', 0)

            print(f"\n  📈 {strategy} 策略影响:")
            print(f"     时间开销: {time_overhead:+.1f}%")
            print(f"     分块数量变化: {chunk_diff:+d}")
            if quality_score is not None:
                print(f"     质量评分: {quality_score:.3f}")
            else:
                print(f"     质量评分: 未评估")

            # 给出建议
            if time_overhead < 5:
                print(f"     💡 建议: 性能影响很小，推荐使用")
            elif time_overhead < 20:
                print(f"     💡 建议: 性能影响适中，可根据需要使用")
            else:
                print(f"     💡 建议: 性能影响较大，仅在质量要求高时使用")

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
        print(f"🔍 简化分块系统测试结果")
        print(f"📊 预设: {result['preset_used']}")
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
        quality_score = validation.get('avg_quality_score')
        if quality_score is not None:
            print(f"   平均质量评分: {quality_score:.3f}")
        else:
            print(f"   平均质量评分: 未评估")

        if validation.get('issues'):
            print(f"   ⚠️  发现问题: {len(validation['issues'])}个")
            for issue in validation['issues'][:3]:
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
                metadata = chunk.get('metadata', {})
            else:
                char_count = getattr(chunk, 'character_count', 0)
                word_count = getattr(chunk, 'word_count', 0)
                quality_score = getattr(chunk, 'quality_score', 0)
                content = getattr(chunk, 'content', '')
                metadata = getattr(chunk, 'metadata', {})

            print(f"大小: {char_count} 字符 | 词数: {word_count}")
            if quality_score is not None:
                print(f"质量评分: {quality_score:.3f}")
            else:
                print(f"质量评分: 未评估")

            # 显示内容预览
            content_preview = content[:200] + "..." if len(content) > 200 else content
            print(f"内容: {content_preview}")

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
        """输出增强的JSON格式结果，包含详细的评分标准和检测逻辑信息"""
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
                    'quality_score': getattr(chunk, 'quality_score', None),
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
                            'source_document': getattr(metadata, 'source_document', '')
                        }

            serializable_chunks.append(chunk_data)

        # 获取本次测试的实际配置信息
        test_metadata = self._get_test_specific_metadata(result)

        output = {
            'preset_used': result['preset_used'],
            'processing_time': result['processing_time'],
            'statistics': result['statistics'],
            'validation': result['validation'],
            'chunks': serializable_chunks,
            # 简化的元数据：只包含本次测试的实际信息
            'metadata': test_metadata
        }

        print(json.dumps(output, ensure_ascii=False, indent=2))

    def _get_test_specific_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """获取本次测试的实际配置和策略信息"""
        try:
            metadata = {}

            # 1. 获取实际使用的质量评估策略信息
            if self.engine and hasattr(self.engine, 'get_quality_assessment_info'):
                quality_info = self.engine.get_quality_assessment_info()
                if 'error' not in quality_info:
                    current_strategy = quality_info.get('current_strategy', 'unknown')
                    strategy_info = quality_info.get('strategy_info', {})

                    metadata['quality_assessment'] = {
                        'strategy_name': current_strategy,
                        'enabled': quality_info.get('enabled', False),
                        'config': strategy_info.get('config', {}),
                        'preset': strategy_info.get('preset', 'unknown')
                    }

                    # 只有在启用时才添加评分计算方式
                    if quality_info.get('enabled', False) and current_strategy != 'disabled':
                        config = strategy_info.get('config', {})
                        if current_strategy == 'basic':
                            metadata['quality_assessment']['score_calculation'] = {
                                'method': 'weighted_average',
                                'length_weight': config.get('length_weight', 0.6),
                                'completeness_weight': config.get('completeness_weight', 0.4),
                                'formula': f"length_score * {config.get('length_weight', 0.6)} + completeness_score * {config.get('completeness_weight', 0.4)}"
                            }
                        elif current_strategy == 'strict':
                            metadata['quality_assessment']['score_calculation'] = {
                                'method': 'weighted_average',
                                'length_weight': config.get('length_weight', 0.5),
                                'completeness_weight': config.get('completeness_weight', 0.5),
                                'formula': f"length_score * {config.get('length_weight', 0.5)} + completeness_score * {config.get('completeness_weight', 0.5)}"
                            }
                else:
                    metadata['quality_assessment'] = {'error': quality_info.get('error')}
            else:
                metadata['quality_assessment'] = {'status': 'unavailable'}

            # 2. 获取本次测试的分块配置
            metadata['chunking_config'] = {
                'chunk_size': self.config.get('chunk_size'),
                'chunk_overlap': self.config.get('chunk_overlap'),
                'min_chunk_size': self.config.get('min_chunk_size'),
                'max_chunk_size': self.config.get('max_chunk_size'),
                'preserve_context': self.config.get('preserve_context'),
                'enable_quality_assessment': self.config.get('enable_quality_assessment'),
                'quality_strategy': self.config.get('quality_strategy')
            }

            # 3. 获取validation的实际结果说明
            validation = result.get('validation', {})
            avg_score = validation.get('avg_quality_score')
            metadata['validation_info'] = {
                'method': 'average_non_null_scores',
                'total_chunks_evaluated': validation.get('total_chunks', 0),
                'chunks_with_scores': len([1 for chunk in result.get('chunks', [])
                                         if self._get_chunk_quality_score(chunk) is not None]),
                'avg_calculation': 'sum(non_null_scores) / count(non_null_scores)' if avg_score is not None else 'no_scores_available'
            }

            return metadata

        except Exception as e:
            return {'error': f'获取测试元数据失败: {e}'}

    def _get_chunk_quality_score(self, chunk) -> Optional[float]:
        """获取分块的质量评分"""
        if isinstance(chunk, dict):
            return chunk.get('quality_score')
        else:
            return getattr(chunk, 'quality_score', None)

    def run_performance_test(self, text_sizes: List[int] = None) -> None:
        """
        运行性能测试

        Args:
            text_sizes: 测试文本大小列表（字符数）
        """
        if text_sizes is None:
            text_sizes = [1000, 5000, 10000, 50000, 100000]

        print("\n" + "="*80)
        print("🚀 简化分块系统性能测试")
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
                result = self.test_preset_chunking(test_text, metadata, 'standard')
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
        print("🎯 简化分块系统功能演示")
        print("="*80)

        demo_scenarios = [
            ('通用技术文档', 'general', 'standard'),
            ('航空维修手册', 'aviation', 'aviation_maintenance'),
            ('结构化文档', 'structured', 'structure'),
            ('语义连贯文档', 'semantic', 'semantic')
        ]

        for name, text_type, expected_preset in demo_scenarios:
            print(f"\n🔸 演示场景: {name}")
            print("-" * 40)

            text = self._get_sample_text(text_type)
            metadata = {
                'file_name': f'{text_type}_demo.txt',
                'document_type': text_type,
                'title': name
            }

            try:
                # 测试自动预设选择
                result = self.test_preset_chunking(text, metadata)
                print(f"自动选择预设: {result['preset_used']}")

                # 测试指定预设
                if expected_preset:
                    result_preset = self.test_preset_chunking(text, metadata, expected_preset)
                    print(f"指定预设效果: {expected_preset}")

                    # 简单对比
                    auto_chunks = result['statistics']['chunk_count']
                    preset_chunks = result_preset['statistics']['chunk_count']
                    print(f"  自动选择: {auto_chunks}个分块")
                    print(f"  指定预设: {preset_chunks}个分块")

                self.visualize_chunks(result, 'simple')

            except Exception as e:
                print(f"演示失败: {e}")
                self.logger.error(f"演示场景 {name} 失败: {e}")

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

            'semantic': """
人工智能技术的发展正在深刻改变我们的世界。机器学习作为人工智能的核心技术，通过算法让计算机能够从数据中学习和改进。

深度学习是机器学习的一个重要分支。它模仿人脑神经网络的结构，通过多层神经网络来处理复杂的数据模式。这种方法在图像识别、自然语言处理和语音识别等领域取得了突破性进展。

然而，人工智能的发展也带来了新的挑战。数据隐私、算法偏见和就业影响等问题需要我们认真对待。我们必须在推动技术进步的同时，确保人工智能的发展符合人类的整体利益。

因此，建立完善的人工智能治理框架变得至关重要。这需要政府、企业和学术界的共同努力，制定相应的法律法规和伦理准则。
""",

            'performance': """
系统性能优化是一个持续的过程，需要从多个维度进行考虑和实施。首先，我们需要建立完善的性能监控体系，实时收集系统运行数据，包括CPU使用率、内存占用、磁盘I/O、网络带宽等关键指标。通过这些数据，我们可以及时发现性能瓶颈，并采取相应的优化措施。在数据库层面，我们需要优化查询语句，建立合适的索引，合理设计表结构，并考虑读写分离、分库分表等策略。在应用层面，我们可以通过缓存机制、异步处理、连接池优化等方式提升性能。同时，代码层面的优化也不容忽视，包括算法优化、内存管理、并发控制等。此外，系统架构的合理设计也是性能优化的重要因素，微服务架构、负载均衡、CDN加速等都能有效提升系统性能。最后，我们还需要建立性能测试体系，定期进行压力测试和性能基准测试，确保系统在各种负载条件下都能稳定运行。
"""
        }

        return samples.get(text_type, samples['general'])


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="简化分块系统预设配置测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --demo                           # 运行演示模式
  %(prog)s --list-presets                   # 列出可用预设
  %(prog)s -i document.txt                  # 测试文件
  %(prog)s -t "测试文本内容"                 # 测试直接输入
  %(prog)s --performance                    # 性能测试
  %(prog)s --compare -t "测试文本"           # 预设对比
  %(prog)s -p semantic --chunk-size 500    # 自定义参数

预设配置说明:
  quick              快速分块配置（500字符）
  standard           标准分块配置（1000字符）
  semantic           语义分块配置（替代原semantic_chunker）
  structure          结构分块配置（替代原structure_chunker）
  aviation_maintenance  航空维修文档配置
  aviation_regulation   航空规章配置
  aviation_standard     航空标准配置
  aviation_training     航空培训配置
  high_quality       高质量分块配置
        """
    )

    # 输入参数
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument('--input', '-i', help='输入文件路径')
    input_group.add_argument('--text', '-t', help='直接输入文本内容')
    input_group.add_argument('--demo', action='store_true', help='运行演示模式')
    input_group.add_argument('--performance', action='store_true', help='性能测试模式')
    input_group.add_argument('--list-presets', action='store_true', help='列出可用预设')

    # 分块参数
    parser.add_argument('--preset', '-p', help='指定预设配置名称')
    parser.add_argument('--chunk-size', type=int, default=1000, help='分块大小 (默认: 1000)')
    parser.add_argument('--chunk-overlap', type=int, default=200, help='重叠大小 (默认: 200)')
    parser.add_argument('--min-chunk-size', type=int, default=100, help='最小分块大小 (默认: 100)')
    parser.add_argument('--max-chunk-size', type=int, default=2000, help='最大分块大小 (默认: 2000)')

    # 功能参数
    parser.add_argument('--compare', action='store_true', help='对比不同预设')
    parser.add_argument('--test-auto-selection', action='store_true', help='测试自动预设选择')
    parser.add_argument('--test-quality-assessment', action='store_true', help='测试质量检测功能')

    # 质量检测参数
    parser.add_argument('--quality-strategy', choices=['basic', 'strict', 'disabled'],
                       default='basic', help='质量检测策略 (默认: basic，选择disabled可禁用检测)')

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
    
    # 处理质量检测配置
    config['quality_strategy'] = args.quality_strategy
    config['enable_quality_assessment'] = (args.quality_strategy != 'disabled')
    
    try:
        # 创建测试器
        tester = SimplifiedChunkingTester(config)

        if not args.quiet:
            print("🚀 简化分块系统预设配置测试脚本启动")
            print(f"📋 当前配置: 分块大小={args.chunk_size}, 重叠={args.chunk_overlap}")

        # 根据参数执行不同的测试模式
        if args.list_presets:
            tester.list_available_presets()
        elif args.demo:
            tester.run_demo()
        elif args.performance:
            tester.run_performance_test()
        elif args.test_auto_selection:
            # 测试自动预设选择
            test_cases = [
                {
                    'text': '第一章 发动机维修程序\n\n任务1：检查发动机\n步骤1：关闭发动机\n警告：注意安全',
                    'metadata': {'title': '维修手册', 'document_type': 'manual'},
                    'expected_preset': 'aviation_maintenance'
                },
                {
                    'text': '第一条 安全规定\n第二条 操作规范\n第三条 责任条款',
                    'metadata': {'title': '安全规章', 'document_type': 'regulation'},
                    'expected_preset': 'aviation_regulation'
                },
                {
                    'text': '# 技术标准文档\n\n## 要求1\n规格说明\n\n## 测试方法\n测试程序',
                    'metadata': {'title': '技术标准', 'document_type': 'standard'},
                    'expected_preset': 'aviation_standard'
                },
                {
                    'text': '学习目标：掌握基本概念\n知识点1：理论基础\n练习1：实践操作',
                    'metadata': {'title': '培训教材', 'document_type': 'training'},
                    'expected_preset': 'aviation_training'
                },
                {
                    'text': '这是一个普通的文档内容。包含多个段落和句子。',
                    'metadata': {'file_extension': '.txt'},
                    'expected_preset': 'semantic'
                }
            ]
            tester.test_automatic_preset_selection(test_cases)
        elif args.test_quality_assessment:
            # 测试质量检测功能
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
            elif args.text:
                text = args.text
                metadata = {
                    'file_name': 'direct_input.txt',
                    'document_type': 'direct_input',
                    'title': '直接输入文本'
                }
            else:
                # 使用默认测试文本
                text = tester._get_sample_text('general')
                metadata = {
                    'file_name': 'quality_test.txt',
                    'document_type': 'quality_test',
                    'title': '质量检测测试文档'
                }

            tester.test_quality_assessment(text, metadata)
        elif args.compare and (args.input or args.text):
            # 预设对比模式
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

            tester.compare_presets(text, metadata)
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

            result = tester.test_preset_chunking(text, metadata, args.preset)
            tester.visualize_chunks(result, args.output_format)
        else:
            # 默认显示帮助信息
            parser.print_help()
            print("\n💡 提示:")
            print("  --demo                    运行演示模式")
            print("  --list-presets            查看可用预设")
            print("  --test-auto-selection     测试自动预设选择")
            print("  --test-quality-assessment 测试质量检测功能")
            print("  --help                    查看详细帮助")

    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(0)
    except Exception as e:
        error_msg = f"测试执行失败: {e}"
        print(f"\n❌ {error_msg}")
        if 'tester' in locals():
            tester.logger.error(error_msg)
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
