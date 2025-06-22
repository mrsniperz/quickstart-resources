"""
模块名称: aviation_quality
功能描述: 航空领域专用质量评估策略，针对航空文档的特殊需求进行优化
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import re
import time
from typing import Dict, List, Optional, Any
from ..base import QualityAssessmentStrategy, QualityMetrics

# 为了避免循环导入，我们在这里处理TextChunk和ChunkMetadata的导入
try:
    from ...chunking_engine import TextChunk, ChunkMetadata
except ImportError:
    # 如果无法导入，使用base中的简化版本
    from ..base import TextChunk

    class ChunkMetadata:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


class AviationQualityAssessment(QualityAssessmentStrategy):
    """
    航空领域质量评估策略
    
    专门针对航空文档的特殊需求设计，包括：
    - 航空术语完整性检查
    - 安全信息完整性验证
    - 操作步骤连贯性评估
    - 技术参数准确性检查
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化航空质量评估策略
        
        Args:
            config: 配置参数
                - weights: 各维度权重配置
                - min_chunk_size: 最小分块大小
                - max_chunk_size: 最大分块大小
                - chunk_size: 目标分块大小
        """
        super().__init__(config)
        
        # 默认权重配置（针对航空文档优化）
        default_weights = {
            'aviation_specific': 0.25,
            'semantic_completeness': 0.25,
            'information_density': 0.25,
            'structure_quality': 0.20,
            'size_appropriateness': 0.05
        }
        
        self.weights = self.config.get('weights', default_weights)
        self.min_chunk_size = self.config.get('min_chunk_size', 100)
        self.max_chunk_size = self.config.get('max_chunk_size', 2000)
        self.chunk_size = self.config.get('chunk_size', 1000)
        
        # 航空术语库
        self.aviation_terms = [
            '发动机', '液压系统', '燃油系统', '电气系统', '起落架',
            '飞行控制', '导航系统', '通信系统', '客舱', '货舱',
            'engine', 'hydraulic', 'fuel system', 'electrical', 'landing gear',
            'flight control', 'navigation', 'communication', 'cabin', 'cargo'
        ]
        
        # 安全关键词
        self.safety_keywords = [
            '警告', '注意', '危险', '禁止', '必须',
            'warning', 'caution', 'danger', 'prohibited', 'must'
        ]
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "aviation"
    
    def get_supported_dimensions(self) -> List[str]:
        """获取支持的评估维度"""
        return [
            'aviation_specific',
            'semantic_completeness',
            'information_density',
            'structure_quality',
            'size_appropriateness'
        ]
    
    def assess_quality(self, chunk: TextChunk, context: Optional[Dict[str, Any]] = None) -> QualityMetrics:
        """
        评估分块质量
        
        Args:
            chunk: 待评估的文本分块
            context: 评估上下文信息
            
        Returns:
            QualityMetrics: 质量评估结果
        """
        try:
            start_time = time.time()
            
            if not self.validate_chunk(chunk):
                return QualityMetrics(
                    overall_score=0.0,
                    dimension_scores={},
                    confidence=0.0,
                    details={'error': 'Invalid chunk'},
                    strategy_name=self.get_strategy_name()
                )
            
            # 特殊情况处理
            if not chunk.content.strip():
                return QualityMetrics(
                    overall_score=0.0,
                    dimension_scores={},
                    confidence=1.0,
                    details={'reason': 'Empty content'},
                    strategy_name=self.get_strategy_name()
                )
            
            if chunk.character_count < 10:
                return QualityMetrics(
                    overall_score=0.1,
                    dimension_scores={'size_appropriateness': 0.1},
                    confidence=1.0,
                    details={'reason': 'Content too short'},
                    strategy_name=self.get_strategy_name()
                )
            
            # 根据文档类型获取权重配置
            weights = self._get_quality_weights(chunk.metadata)
            
            # 计算各维度评分
            dimension_scores = {}
            dimension_scores['aviation_specific'] = self._calculate_aviation_specific_score(chunk)
            dimension_scores['semantic_completeness'] = self._calculate_semantic_completeness_score(chunk)
            dimension_scores['information_density'] = self._calculate_information_density_score(chunk)
            dimension_scores['structure_quality'] = self._calculate_structure_quality_score(chunk)
            dimension_scores['size_appropriateness'] = self._calculate_size_appropriateness_score(chunk)
            
            # 加权计算总分
            total_score = sum(
                score * weights.get(dimension, 0.0)
                for dimension, score in dimension_scores.items()
            )
            
            # 应用惩罚机制
            penalty = self._calculate_penalty(chunk)
            final_score = max(0.1, total_score - penalty)
            
            processing_time = (time.time() - start_time) * 1000
            
            return QualityMetrics(
                overall_score=round(min(1.0, final_score), 3),
                dimension_scores=dimension_scores,
                confidence=0.9,
                details={
                    'weights_used': weights,
                    'penalty_applied': penalty,
                    'chunk_length': chunk.character_count,
                    'word_count': chunk.word_count or len(chunk.content.split())
                },
                strategy_name=self.get_strategy_name(),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"航空质量评估失败: {e}")
            return self.get_fallback_metrics(chunk, e)
    
    def _get_quality_weights(self, metadata: ChunkMetadata) -> Dict[str, float]:
        """
        根据文档类型获取质量评估权重配置
        
        Args:
            metadata: 分块元数据
            
        Returns:
            dict: 权重配置
        """
        try:
            # 获取文档类型
            doc_type = getattr(metadata, 'chunk_type', None)
            if hasattr(doc_type, 'value'):
                doc_type = doc_type.value
            
            # 根据文档类型返回不同权重
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
            
            return weight_configs.get(str(doc_type), self.weights)
            
        except Exception as e:
            self.logger.warning(f"获取权重配置失败: {e}")
            return self.weights
    
    def _calculate_penalty(self, chunk: TextChunk) -> float:
        """
        计算质量惩罚分数
        
        Args:
            chunk: 文本分块
            
        Returns:
            float: 惩罚分数
        """
        try:
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
            
            return penalty
            
        except Exception:
            return 0.0
    
    def _calculate_aviation_specific_score(self, chunk: TextChunk) -> float:
        """
        计算航空领域特定性评分
        
        Args:
            chunk: 文本分块
            
        Returns:
            float: 航空特定性评分（0-1）
        """
        try:
            score = 0.5  # 从较低的基础分开始
            content = chunk.content.lower()
            
            # 航空术语密度检查
            aviation_term_count = sum(1 for term in self.aviation_terms if term in content)
            if aviation_term_count > 0:
                score += min(0.3, aviation_term_count * 0.1)  # 每个术语加0.1分，最多0.3分
            
            # 检查航空术语是否被截断
            for term in self.aviation_terms:
                if term in content:
                    if content.startswith(term[1:]) or content.endswith(term[:-1]):
                        score -= 0.3  # 术语截断严重扣分
                        break
            
            # 安全信息完整性检查
            safety_found = any(keyword in content for keyword in self.safety_keywords)
            if safety_found:
                score += 0.2  # 包含安全信息加分
                if not self._is_safety_info_complete(chunk.content):
                    score -= 0.4  # 安全信息不完整严重扣分
            
            # 操作步骤连贯性检查
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
        """
        检查安全信息是否完整

        Args:
            content: 文本内容

        Returns:
            bool: 是否完整
        """
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
        """
        检查是否有不完整的操作步骤

        Args:
            content: 文本内容

        Returns:
            bool: 是否有不完整步骤
        """
        try:
            # 查找步骤编号
            step_numbers = re.findall(r'步骤\s*(\d+)|第\s*(\d+)\s*步|step\s+(\d+)|^(\d+)\.', content, re.IGNORECASE | re.MULTILINE)

            if not step_numbers:
                return False

            # 提取数字
            numbers = []
            for match in step_numbers:
                for group in match:
                    if group:
                        numbers.append(int(group))
                        break

            if not numbers:
                return False

            # 检查步骤是否连续
            numbers.sort()
            for i in range(len(numbers) - 1):
                if numbers[i + 1] - numbers[i] > 1:
                    return True  # 有跳跃，可能不完整

            # 检查是否以步骤开始但没有结束
            if numbers and not content.strip().endswith(('.', '。', '完成', 'complete', 'done')):
                return True

            return False

        except Exception:
            return False

    def _calculate_semantic_completeness_score(self, chunk: TextChunk) -> float:
        """
        计算语义完整性评分

        Args:
            chunk: 文本分块

        Returns:
            float: 语义完整性评分（0-1）
        """
        try:
            score = 0.6  # 从较低的基础分开始
            content = chunk.content.strip()

            # 检查内容结束的完整性
            proper_endings = ['.', '。', '!', '！', '?', '？', '：', ':', '完成', 'complete', '结束', 'end']
            has_proper_ending = any(content.endswith(ending) for ending in proper_endings)

            # 对于列表、参数等特殊格式，不要求句号结尾
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
        """
        计算信息密度评分

        Args:
            chunk: 文本分块

        Returns:
            float: 信息密度评分（0-1）
        """
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
        """
        计算结构质量评分

        Args:
            chunk: 文本分块

        Returns:
            float: 结构质量评分（0-1）
        """
        try:
            score = 0.4  # 从较低的基础分开始
            content = chunk.content

            # 检查标题和章节结构
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
                    score += 0.1
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
                        score -= 0.2
                        break

            return max(0.0, min(1.0, score))

        except Exception as e:
            self.logger.warning(f"结构质量评分计算失败: {e}")
            return 0.7

    def _calculate_size_appropriateness_score(self, chunk: TextChunk) -> float:
        """
        计算大小适当性评分

        Args:
            chunk: 文本分块

        Returns:
            float: 大小适当性评分（0-1）
        """
        try:
            char_count = chunk.character_count

            # 定义最优大小区间
            optimal_min = self.chunk_size * 0.8
            optimal_max = self.chunk_size * 1.2

            if optimal_min <= char_count <= optimal_max:
                return 1.0

            # 计算偏离最优区间的程度
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
