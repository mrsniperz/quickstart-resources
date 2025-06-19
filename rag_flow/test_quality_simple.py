#!/usr/bin/env python3
"""
简化的分块质量评估测试

功能描述: 直接测试质量评估方法，避免依赖问题
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import sys
import os
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

# 简化的数据结构定义
class ChunkType(Enum):
    """分块类型枚举"""
    PARAGRAPH = "paragraph"
    SECTION = "section"
    CHAPTER = "chapter"
    LIST = "list"
    TABLE = "table"
    CODE = "code"
    MAINTENANCE_MANUAL = "maintenance_manual"
    REGULATION = "regulation"
    TECHNICAL_STANDARD = "technical_standard"
    TRAINING_MATERIAL = "training_material"
    OPERATION_PROCEDURE = "operation_procedure"

@dataclass
class ChunkMetadata:
    """分块元数据"""
    chunk_id: str
    chunk_type: ChunkType
    source_document: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    parent_chunk_id: Optional[str] = None
    child_chunk_ids: List[str] = None
    confidence_score: float = 1.0
    processing_timestamp: Optional[str] = None

@dataclass
class TextChunk:
    """文本分块数据类"""
    content: str
    metadata: ChunkMetadata
    word_count: int = 0
    character_count: int = 0
    overlap_content: Optional[str] = None
    quality_score: float = 0.0

# 简化的质量评估器类
class QualityAssessmentEngine:
    """质量评估引擎"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 配置参数
        self.chunk_size = self.config.get('chunk_size', 1000)
        self.min_chunk_size = self.config.get('min_chunk_size', 100)
        self.max_chunk_size = self.config.get('max_chunk_size', 2000)
    
    def _get_quality_weights(self, metadata: ChunkMetadata) -> Dict[str, float]:
        """根据文档类型获取质量评估权重配置"""
        try:
            doc_type = getattr(metadata, 'chunk_type', None)
            if hasattr(doc_type, 'value'):
                doc_type = doc_type.value
            
            weight_configs = {
                'maintenance_manual': {
                    'aviation_specific': 0.30,
                    'semantic_completeness': 0.25,
                    'information_density': 0.20,
                    'structure_quality': 0.20,
                    'size_appropriateness': 0.05
                },
                'regulation': {
                    'aviation_specific': 0.20,
                    'semantic_completeness': 0.30,
                    'information_density': 0.25,
                    'structure_quality': 0.20,
                    'size_appropriateness': 0.05
                },
                'technical_standard': {
                    'aviation_specific': 0.25,
                    'semantic_completeness': 0.25,
                    'information_density': 0.25,
                    'structure_quality': 0.20,
                    'size_appropriateness': 0.05
                },
                'training_material': {
                    'aviation_specific': 0.20,
                    'semantic_completeness': 0.30,
                    'information_density': 0.20,
                    'structure_quality': 0.25,
                    'size_appropriateness': 0.05
                }
            }
            
            default_weights = {
                'aviation_specific': 0.25,
                'semantic_completeness': 0.25,
                'information_density': 0.25,
                'structure_quality': 0.20,
                'size_appropriateness': 0.05
            }
            
            return weight_configs.get(str(doc_type), default_weights)
            
        except Exception as e:
            self.logger.warning(f"获取权重配置失败: {e}")
            return {
                'aviation_specific': 0.25,
                'semantic_completeness': 0.25,
                'information_density': 0.25,
                'structure_quality': 0.20,
                'size_appropriateness': 0.05
            }
    
    def _calculate_aviation_specific_score(self, chunk: TextChunk) -> float:
        """计算航空领域特定性评分"""
        try:
            score = 0.5  # 从较低的基础分开始
            content = chunk.content.lower()

            # 航空术语密度检查
            aviation_terms = [
                '发动机', '液压系统', '燃油系统', '电气系统', '起落架',
                '飞行控制', '导航系统', '通信系统', '客舱', '货舱',
                'engine', 'hydraulic', 'fuel system', 'electrical', 'landing gear',
                'flight control', 'navigation', 'communication', 'cabin', 'cargo'
            ]

            # 计算航空术语密度
            aviation_term_count = sum(1 for term in aviation_terms if term in content)
            if aviation_term_count > 0:
                score += min(0.3, aviation_term_count * 0.1)  # 每个术语加0.1分，最多0.3分

            # 检查航空术语是否被截断
            for term in aviation_terms:
                if term in content:
                    if content.startswith(term[1:]) or content.endswith(term[:-1]):
                        score -= 0.3  # 术语截断严重扣分
                        break

            # 安全信息完整性检查
            safety_keywords = [
                '警告', '注意', '危险', '禁止', '必须',
                'warning', 'caution', 'danger', 'prohibited', 'must'
            ]

            safety_found = any(keyword in content for keyword in safety_keywords)
            if safety_found:
                score += 0.2  # 包含安全信息加分
                if not self._is_safety_info_complete(chunk.content):
                    score -= 0.4  # 安全信息不完整严重扣分

            # 操作步骤连贯性检查
            import re
            step_patterns = [
                r'步骤\s*\d+', r'第\s*\d+\s*步', r'step\s+\d+',
                r'\d+\.\s', r'\(\d+\)', r'[a-z]\)'
            ]

            has_steps = any(re.search(pattern, content, re.IGNORECASE) for pattern in step_patterns)
            if has_steps:
                score += 0.2  # 包含步骤加分
                if self._has_incomplete_procedures(chunk.content):
                    score -= 0.3  # 步骤不完整扣分

            # 技术参数检查
            param_patterns = [
                r'\d+\s*(rpm|psi|°c|°f|kg|lb|ft|m|v|a|bar|mpa)',
                r'压力[:：]\s*\d+', r'温度[:：]\s*\d+', r'转速[:：]\s*\d+'
            ]

            has_params = any(re.search(pattern, content, re.IGNORECASE) for pattern in param_patterns)
            if has_params:
                score += 0.2  # 包含技术参数加分

            return max(0.0, min(1.0, score))

        except Exception as e:
            self.logger.warning(f"航空特定性评分计算失败: {e}")
            return 0.5
    
    def _is_safety_info_complete(self, content: str) -> bool:
        """检查安全信息是否完整"""
        try:
            safety_start_patterns = ['警告:', '注意:', '危险:', 'WARNING:', 'CAUTION:', 'DANGER:']

            for pattern in safety_start_patterns:
                if pattern in content:
                    start_idx = content.find(pattern)
                    after_warning = content[start_idx + len(pattern):].strip()

                    # 更严格的完整性检查
                    if len(after_warning) < 20:  # 提高最小长度要求
                        return False

                    # 检查是否有完整的句子结构
                    if not any(after_warning.endswith(end) for end in ['.', '。', '!', '！']):
                        return False

                    # 检查是否包含具体的安全措施描述
                    safety_action_keywords = ['必须', '禁止', '应该', '不得', 'must', 'should', 'do not', 'never']
                    if not any(keyword in after_warning for keyword in safety_action_keywords):
                        return False

            return True

        except Exception:
            return True
    
    def _has_incomplete_procedures(self, content: str) -> bool:
        """检查是否有不完整的操作步骤"""
        try:
            import re
            
            step_numbers = re.findall(r'步骤\s*(\d+)|第\s*(\d+)\s*步|step\s+(\d+)|^(\d+)\.', content, re.IGNORECASE | re.MULTILINE)
            
            if not step_numbers:
                return False
            
            numbers = []
            for match in step_numbers:
                for group in match:
                    if group:
                        numbers.append(int(group))
                        break
            
            if not numbers:
                return False
            
            numbers.sort()
            for i in range(len(numbers) - 1):
                if numbers[i + 1] - numbers[i] > 1:
                    return True
            
            if numbers and not content.strip().endswith(('.', '。', '完成', 'complete', 'done')):
                return True
            
            return False
            
        except Exception:
            return False
    
    def _calculate_semantic_completeness_score(self, chunk: TextChunk) -> float:
        """计算语义完整性评分"""
        try:
            score = 0.6  # 从较低的基础分开始
            content = chunk.content.strip()

            # 检查内容结束的完整性
            proper_endings = ['.', '。', '!', '！', '?', '？', '：', ':', '完成', 'complete', '结束', 'end']
            has_proper_ending = any(content.endswith(ending) for ending in proper_endings)

            # 对于列表、参数等特殊格式，不要求句号结尾
            import re
            list_patterns = [
                r'^\s*[-•]\s',
                r'^\s*\d+\.\s',
                r'^\s*[a-zA-Z]\)\s',
                r':\s*$',
                r'\d+\s*(rpm|psi|°c|°f|kg|lb|ft|m|v|a)\s*$'
            ]

            is_special_format = any(re.search(pattern, content, re.IGNORECASE | re.MULTILINE) for pattern in list_patterns)

            if has_proper_ending or is_special_format:
                score += 0.3  # 有适当结尾加分
            else:
                score -= 0.2  # 没有适当结尾扣分

            # 检查句子完整性
            sentences = re.split(r'[.。!！?？]', content)
            complete_sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]

            if len(complete_sentences) > 0:
                score += 0.2  # 有完整句子加分
            elif not is_special_format:
                score -= 0.3  # 没有完整句子且不是特殊格式扣分

            # 检查内容的连贯性
            if len(content) > 50:  # 对较长内容进行连贯性检查
                # 检查是否有突然的主题转换
                topic_keywords = {
                    'maintenance': ['维修', '检查', '更换', '安装'],
                    'operation': ['操作', '启动', '关闭', '运行'],
                    'safety': ['安全', '警告', '注意', '危险'],
                    'technical': ['参数', '规格', '标准', '技术']
                }

                topic_counts = {}
                content_lower = content.lower()

                for topic, keywords in topic_keywords.items():
                    count = sum(1 for keyword in keywords if keyword in content_lower)
                    if count > 0:
                        topic_counts[topic] = count

                # 如果主题过于分散，扣分
                if len(topic_counts) > 2:
                    score -= 0.1
                elif len(topic_counts) == 1:
                    score += 0.1  # 主题集中加分

            return max(0.0, min(1.0, score))

        except Exception as e:
            self.logger.warning(f"语义完整性评分计算失败: {e}")
            return 0.5
    
    def _calculate_information_density_score(self, chunk: TextChunk) -> float:
        """计算信息密度评分"""
        try:
            score = 0.5  # 从中等基础分开始
            content = chunk.content

            total_chars = len(content)
            if total_chars == 0:
                return 0.0

            # 计算有效字符比例
            non_space_chars = len(content.replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', ''))
            content_ratio = non_space_chars / total_chars

            if content_ratio >= 0.8:
                score += 0.3  # 高密度内容加分
            elif content_ratio >= 0.7:
                score += 0.2
            elif content_ratio >= 0.6:
                score += 0.1
            elif content_ratio < 0.5:
                score -= 0.4  # 低密度内容严重扣分
            elif content_ratio < 0.6:
                score -= 0.2

            # 计算信息关键词密度
            info_keywords = [
                '参数', '数值', '规格', '标准', '要求', '步骤', '方法', '程序',
                '检查', '测试', '维修', '更换', '安装', '调整', '校准',
                'parameter', 'value', 'specification', 'standard', 'requirement',
                'step', 'method', 'procedure', 'check', 'test', 'maintenance'
            ]

            content_lower = content.lower()
            keyword_count = sum(1 for keyword in info_keywords if keyword in content_lower)
            keyword_density = keyword_count / max(1, len(content.split()))

            if keyword_density >= 0.2:
                score += 0.3  # 高关键词密度加分
            elif keyword_density >= 0.1:
                score += 0.2
            elif keyword_density >= 0.05:
                score += 0.1
            else:
                score -= 0.2  # 低关键词密度扣分

            # 检查数字和技术数据的密度
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', content)
            units = re.findall(r'\d+\s*(rpm|psi|°c|°f|kg|lb|ft|m|v|a|bar|mpa)', content, re.IGNORECASE)

            if len(numbers) > 0:
                number_density = len(numbers) / max(1, len(content.split()))
                if number_density > 0.2:
                    score += 0.2  # 高数值密度加分
                elif number_density > 0.1:
                    score += 0.1

            if len(units) > 0:
                score += 0.1  # 包含技术单位加分

            # 检查是否包含无意义的重复内容
            words = content.split()
            if len(words) > 5:
                unique_words = set(words)
                repetition_ratio = len(words) / len(unique_words)
                if repetition_ratio > 3:
                    score -= 0.3  # 重复度太高扣分
                elif repetition_ratio < 1.5:
                    score += 0.1  # 词汇丰富度高加分

            return max(0.0, min(1.0, score))

        except Exception as e:
            self.logger.warning(f"信息密度评分计算失败: {e}")
            return 0.5
    
    def _calculate_structure_quality_score(self, chunk: TextChunk) -> float:
        """计算结构质量评分"""
        try:
            score = 0.4  # 从较低的基础分开始
            content = chunk.content

            # 检查标题和章节结构
            import re
            structure_markers = [
                r'^第\s*[一二三四五六七八九十\d]+\s*[章节条]',
                r'^Chapter\s+\d+',
                r'^Section\s+\d+',
                r'^#{1,6}\s',
                r'^\d+\.\d+',
                r'^[A-Z][A-Z\s]+:$'
            ]

            has_structure = any(re.search(pattern, content, re.IGNORECASE | re.MULTILINE) for pattern in structure_markers)

            if has_structure:
                score += 0.4  # 有明确结构标记大幅加分

            # 检查列表结构
            list_patterns = [
                r'^\s*[-•]\s',
                r'^\s*\d+\.\s',
                r'^\s*[a-zA-Z]\)\s',
                r'^\s*\([a-zA-Z0-9]+\)\s'
            ]

            list_items = []
            for pattern in list_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                list_items.extend(matches)

            if len(list_items) > 1:
                score += 0.3  # 有列表结构加分

                # 检查列表的一致性
                if len(set(list_items)) == len(list_items):
                    score += 0.1  # 列表标记一致加分
            elif len(list_items) == 1:
                score += 0.1  # 有单个列表项小幅加分

            # 检查段落结构
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            if len(paragraphs) > 1:
                score += 0.2  # 有多段落结构加分

            # 检查特殊结构（表格、代码块等）
            special_structures = [
                r'\|.*\|',  # 表格
                r'```.*```',  # 代码块
                r'^\s*\w+[:：]\s*\w+',  # 键值对
                r'\d+\s*[x×]\s*\d+',  # 尺寸规格
            ]

            for pattern in special_structures:
                if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                    score += 0.2  # 有特殊结构加分
                    break

            # 检查结构的完整性
            incomplete_patterns = [
                (r'^\s*步骤\s*\d+', r'完成|结束|end|complete'),
                (r'^\s*注意[:：]', r'[.。!！]$'),
                (r'^\s*警告[:：]', r'[.。!！]$'),
            ]

            for start_pattern, end_pattern in incomplete_patterns:
                if re.search(start_pattern, content, re.IGNORECASE | re.MULTILINE):
                    if not re.search(end_pattern, content, re.IGNORECASE | re.MULTILINE):
                        score -= 0.3  # 结构不完整扣分
                        break

            return max(0.0, min(1.0, score))

        except Exception as e:
            self.logger.warning(f"结构质量评分计算失败: {e}")
            return 0.4
    
    def _calculate_size_appropriateness_score(self, chunk: TextChunk) -> float:
        """计算大小适当性评分"""
        try:
            char_count = chunk.character_count

            optimal_min = self.chunk_size * 0.8
            optimal_max = self.chunk_size * 1.2

            if optimal_min <= char_count <= optimal_max:
                return 1.0

            if char_count < optimal_min:
                if char_count < self.min_chunk_size:
                    # 对过小的分块更严格评分
                    ratio = char_count / self.min_chunk_size
                    return max(0.0, ratio * 0.3)  # 降低基础分数
                else:
                    # 小于最优但在可接受范围内
                    ratio = char_count / optimal_min
                    return 0.3 + ratio * 0.4  # 调整评分范围
            else:
                if char_count > self.max_chunk_size:
                    ratio = self.max_chunk_size / char_count
                    return max(0.0, ratio * 0.5)
                else:
                    ratio = optimal_max / char_count
                    return 0.5 + ratio * 0.5

        except Exception as e:
            self.logger.warning(f"大小适当性评分计算失败: {e}")
            return 0.5
    
    def calculate_chunk_quality(self, chunk: TextChunk) -> float:
        """计算分块质量评分（航空RAG系统优化版）"""
        try:
            if not chunk.content.strip():
                return 0.0

            if chunk.character_count < 10:
                return 0.1

            # 根据文档类型获取权重配置
            weights = self._get_quality_weights(chunk.metadata)

            # 计算各维度评分
            aviation_score = self._calculate_aviation_specific_score(chunk)
            semantic_score = self._calculate_semantic_completeness_score(chunk)
            density_score = self._calculate_information_density_score(chunk)
            structure_score = self._calculate_structure_quality_score(chunk)
            size_score = self._calculate_size_appropriateness_score(chunk)

            # 可选的调试输出（注释掉以简化输出）
            # print(f"   [调试] 航空特定性: {aviation_score:.3f}")
            # print(f"   [调试] 语义完整性: {semantic_score:.3f}")
            # print(f"   [调试] 信息密度: {density_score:.3f}")
            # print(f"   [调试] 结构质量: {structure_score:.3f}")
            # print(f"   [调试] 大小适当性: {size_score:.3f}")

            # 加权计算总分
            total_score = (
                aviation_score * weights['aviation_specific'] +
                semantic_score * weights['semantic_completeness'] +
                density_score * weights['information_density'] +
                structure_score * weights['structure_quality'] +
                size_score * weights['size_appropriateness']
            )

            # 对于明显有问题的内容，应用惩罚机制
            penalty = 0.0

            # 内容过短惩罚
            if chunk.character_count < 30:
                penalty += 0.4
            elif chunk.character_count < 50:
                penalty += 0.2

            # 空白字符过多惩罚
            non_space_ratio = len(chunk.content.replace(' ', '').replace('\n', '').replace('\t', '')) / len(chunk.content)
            if non_space_ratio < 0.3:
                penalty += 0.5
            elif non_space_ratio < 0.5:
                penalty += 0.3
            elif non_space_ratio < 0.6:
                penalty += 0.1

            # 应用惩罚，但保留最低分数
            final_score = max(0.1, total_score - penalty)

            return round(min(1.0, final_score), 3)

        except Exception as e:
            self.logger.warning(f"分块质量评分计算失败: {e}")
            return 0.5


def create_test_chunks():
    """创建测试用的分块数据"""
    
    test_cases = [
        {
            'name': '完整的维修步骤',
            'content': '''第3章 发动机维修程序
3.1 日常检查步骤
警告：检查前必须关闭发动机并等待冷却。
步骤1：检查发动机外观，查看是否有泄漏或损坏。
步骤2：检查机油液位，确保在正常范围内（2.5-3.0升）。
步骤3：检查冷却液温度，正常工作温度应为85-95°C。
检查完成后，记录所有参数并签字确认。''',
            'chunk_type': ChunkType.MAINTENANCE_MANUAL,
            'expected_score_range': (0.8, 1.0)
        },
        
        {
            'name': '不完整的安全警告',
            'content': '''警告：在进行液压系统维修时，必须注意
压力释放程序包括：
1. 关闭主电源
2. 释放系统压力''',
            'chunk_type': ChunkType.MAINTENANCE_MANUAL,
            'expected_score_range': (0.4, 0.7)
        },
        
        {
            'name': '技术参数列表',
            'content': '''液压系统技术规格：
工作压力：3000 PSI
最大压力：3500 PSI
工作温度：-40°C 到 +85°C
液压油类型：MIL-H-5606
油箱容量：15升
过滤器规格：25微米''',
            'chunk_type': ChunkType.TECHNICAL_STANDARD,
            'expected_score_range': (0.6, 0.8)  # 调整预期范围，因为内容较短
        },

        {
            'name': '截断的航空术语',
            'content': '''液压系统检查程序
检查液压泵的工作状态，确保压力稳定。如果发现液压
油泄漏，应立即停止操作并进行维修。检查完成后更新维修记录。''',
            'chunk_type': ChunkType.MAINTENANCE_MANUAL,
            'expected_score_range': (0.3, 0.6)
        },

        {
            'name': '完整的航空法规',
            'content': '''第147条 航空器维修人员资质要求
147.1 基本要求
持证维修人员必须具备以下条件：
(a) 年满18周岁；
(b) 具有相应的技术培训经历；
(c) 通过理论和实践考试；
(d) 身体健康，能够胜任维修工作。
本条款自发布之日起生效，所有维修人员必须严格遵守。''',
            'chunk_type': ChunkType.REGULATION,
            'expected_score_range': (0.8, 1.0)
        },

        {
            'name': '空白内容过多',
            'content': '''


检查     项目：     发动机


状态：     正常



''',
            'chunk_type': ChunkType.MAINTENANCE_MANUAL,
            'expected_score_range': (0.1, 0.4)
        }
    ]
    
    chunks = []
    for i, case in enumerate(test_cases):
        metadata = ChunkMetadata(
            chunk_id=f"test_chunk_{i}",
            chunk_type=case['chunk_type'],
            source_document=f"test_doc_{case['name']}"
        )
        
        chunk = TextChunk(
            content=case['content'],
            metadata=metadata,
            word_count=len(case['content'].split()),
            character_count=len(case['content'])
        )
        
        chunks.append({
            'chunk': chunk,
            'name': case['name'],
            'expected_range': case['expected_score_range']
        })
    
    return chunks


def main():
    """主测试函数"""
    print("🚀 航空RAG系统分块质量评估改进效果测试")
    print("=" * 60)
    
    # 创建质量评估引擎
    config = {
        'chunk_size': 1000,
        'min_chunk_size': 100,
        'max_chunk_size': 2000
    }
    
    engine = QualityAssessmentEngine(config)
    
    # 获取测试数据
    test_chunks = create_test_chunks()
    
    print(f"\n📊 测试用例总数: {len(test_chunks)}")
    print("-" * 60)
    
    results = []
    
    for test_case in test_chunks:
        chunk = test_case['chunk']
        name = test_case['name']
        expected_range = test_case['expected_range']
        
        # 计算质量评分
        quality_score = engine.calculate_chunk_quality(chunk)
        
        # 检查是否在预期范围内
        in_range = expected_range[0] <= quality_score <= expected_range[1]
        status = "✅ 通过" if in_range else "❌ 未通过"
        
        print(f"\n📝 测试用例: {name}")
        print(f"   内容长度: {chunk.character_count} 字符")
        print(f"   文档类型: {chunk.metadata.chunk_type}")
        print(f"   质量评分: {quality_score:.3f}")
        print(f"   预期范围: {expected_range[0]:.1f} - {expected_range[1]:.1f}")
        print(f"   测试结果: {status}")
        
        # 显示内容预览
        preview = chunk.content[:100].replace('\n', ' ')
        if len(chunk.content) > 100:
            preview += "..."
        print(f"   内容预览: {preview}")
        
        results.append({
            'name': name,
            'score': quality_score,
            'expected': expected_range,
            'passed': in_range
        })
    
    # 统计结果
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    pass_rate = passed_count / total_count * 100
    
    print("\n" + "=" * 60)
    print("📈 测试结果统计")
    print("-" * 60)
    print(f"通过测试: {passed_count}/{total_count} ({pass_rate:.1f}%)")
    
    if pass_rate >= 80:
        print("🎉 质量评估改进效果良好！")
    elif pass_rate >= 60:
        print("⚠️  质量评估有所改进，但仍需优化")
    else:
        print("❌ 质量评估需要进一步改进")
    
    print("\n✨ 测试完成！")


if __name__ == "__main__":
    main()
