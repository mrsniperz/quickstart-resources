"""
模块名称: completeness_quality
功能描述: 基于内容完整性的质量评估策略
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import re
import time
from typing import Dict, List, Optional, Any, Tuple
from ..base import QualityAssessmentStrategy, QualityMetrics

# 为了避免循环导入，我们在这里处理TextChunk的导入
try:
    from ...chunking_engine import TextChunk
except ImportError:
    # 如果无法导入，使用base中的简化版本
    from ..base import TextChunk


class ContentCompletenessAssessment(QualityAssessmentStrategy):
    """
    内容完整性质量评估策略
    
    专注于评估分块内容的完整性，包括：
    - 信息单元完整性
    - 逻辑结构完整性
    - 引用和关联完整性
    - 上下文依赖完整性
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化内容完整性评估策略
        
        Args:
            config: 配置参数
                - weights: 各维度权重配置
                - completeness_threshold: 完整性阈值
                - reference_patterns: 引用模式配置
        """
        super().__init__(config)
        
        # 默认权重配置
        default_weights = {
            'information_unit_completeness': 0.30,
            'logical_structure_completeness': 0.25,
            'reference_completeness': 0.25,
            'context_dependency_completeness': 0.20
        }
        
        self.weights = self.config.get('weights', default_weights)
        self.completeness_threshold = self.config.get('completeness_threshold', 0.7)
        
        # 引用和关联模式
        self.reference_patterns = self.config.get('reference_patterns', {
            'figure_ref': [r'图\s*\d+', r'Figure\s+\d+', r'Fig\.\s*\d+'],
            'table_ref': [r'表\s*\d+', r'Table\s+\d+'],
            'section_ref': [r'第\s*\d+\s*[章节条]', r'Section\s+\d+', r'见\s*\d+\.\d+'],
            'page_ref': [r'第\s*\d+\s*页', r'Page\s+\d+', r'p\.\s*\d+'],
            'step_ref': [r'步骤\s*\d+', r'Step\s+\d+'],
            'item_ref': [r'项目\s*\d+', r'Item\s+\d+']
        })
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "content_completeness"
    
    def get_supported_dimensions(self) -> List[str]:
        """获取支持的评估维度"""
        return [
            'information_unit_completeness',
            'logical_structure_completeness',
            'reference_completeness',
            'context_dependency_completeness'
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
            
            # 计算各维度评分
            dimension_scores = {}
            
            dimension_scores['information_unit_completeness'] = self._calculate_information_unit_completeness(chunk)
            dimension_scores['logical_structure_completeness'] = self._calculate_logical_structure_completeness(chunk)
            dimension_scores['reference_completeness'] = self._calculate_reference_completeness(chunk, context)
            dimension_scores['context_dependency_completeness'] = self._calculate_context_dependency_completeness(chunk, context)
            
            # 计算加权总分
            overall_score = sum(
                score * self.weights.get(dimension, 0.0)
                for dimension, score in dimension_scores.items()
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # 分析完整性问题
            completeness_issues = self._analyze_completeness_issues(chunk, dimension_scores)
            
            return QualityMetrics(
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                confidence=0.8,
                details={
                    'completeness_issues': completeness_issues,
                    'chunk_length': len(chunk.content),
                    'weights_used': self.weights,
                    'information_units_found': self._count_information_units(chunk)
                },
                strategy_name=self.get_strategy_name(),
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"内容完整性评估失败: {e}")
            return self.get_fallback_metrics(chunk, e)
    
    def _calculate_information_unit_completeness(self, chunk: TextChunk) -> float:
        """
        计算信息单元完整性评分
        
        Args:
            chunk: 文本分块
            
        Returns:
            float: 信息单元完整性评分（0-1）
        """
        try:
            score = 0.6  # 基础分
            content = chunk.content
            
            # 识别信息单元类型
            info_units = self._identify_information_units(content)
            
            if not info_units:
                return 0.4  # 没有明确的信息单元
            
            complete_units = 0
            total_units = len(info_units)
            
            for unit_type, unit_content in info_units:
                if self._is_information_unit_complete(unit_type, unit_content):
                    complete_units += 1
            
            # 计算完整性比例
            completeness_ratio = complete_units / total_units if total_units > 0 else 0
            
            # 根据完整性比例调整评分
            if completeness_ratio >= 0.9:
                score += 0.4  # 高完整性
            elif completeness_ratio >= 0.7:
                score += 0.3  # 较高完整性
            elif completeness_ratio >= 0.5:
                score += 0.2  # 中等完整性
            elif completeness_ratio >= 0.3:
                score += 0.1  # 较低完整性
            else:
                score -= 0.2  # 低完整性
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            self.logger.warning(f"信息单元完整性评分计算失败: {e}")
            return 0.6
    
    def _calculate_logical_structure_completeness(self, chunk: TextChunk) -> float:
        """
        计算逻辑结构完整性评分
        
        Args:
            chunk: 文本分块
            
        Returns:
            float: 逻辑结构完整性评分（0-1）
        """
        try:
            score = 0.7  # 基础分
            content = chunk.content
            
            # 检查逻辑结构模式
            structure_patterns = {
                'enumeration': [r'第一|第二|第三|首先|其次|最后|1\.|2\.|3\.'],
                'cause_effect': [r'因为|由于|所以|因此|导致|结果|because|therefore|result'],
                'comparison': [r'相比|对比|而|但是|然而|相对|compared|however|while'],
                'procedure': [r'步骤|程序|流程|方法|过程|step|procedure|process'],
                'description': [r'包括|含有|具有|特点|特征|性质|include|feature|characteristic']
            }
            
            found_structures = []
            for structure_type, patterns in structure_patterns.items():
                if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                    found_structures.append(structure_type)
            
            if not found_structures:
                return score  # 没有明确的逻辑结构
            
            # 检查每种结构的完整性
            complete_structures = 0
            for structure_type in found_structures:
                if self._is_logical_structure_complete(structure_type, content):
                    complete_structures += 1
            
            # 根据结构完整性调整评分
            if found_structures:
                structure_completeness = complete_structures / len(found_structures)
                score += (structure_completeness - 0.5) * 0.4
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            self.logger.warning(f"逻辑结构完整性评分计算失败: {e}")
            return 0.7
    
    def _calculate_reference_completeness(self, chunk: TextChunk, context: Optional[Dict[str, Any]]) -> float:
        """
        计算引用完整性评分
        
        Args:
            chunk: 文本分块
            context: 上下文信息
            
        Returns:
            float: 引用完整性评分（0-1）
        """
        try:
            score = 0.8  # 基础分（大多数分块没有引用问题）
            content = chunk.content
            
            # 查找所有引用
            references = self._find_references(content)
            
            if not references:
                return score  # 没有引用，认为完整
            
            # 检查引用的完整性
            complete_references = 0
            for ref_type, ref_content in references:
                if self._is_reference_complete(ref_type, ref_content, context):
                    complete_references += 1
            
            # 计算引用完整性比例
            if references:
                ref_completeness = complete_references / len(references)
                if ref_completeness < 0.5:
                    score -= 0.4  # 引用不完整严重扣分
                elif ref_completeness < 0.8:
                    score -= 0.2  # 部分引用不完整
                # 完整引用不额外加分，保持基础分
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            self.logger.warning(f"引用完整性评分计算失败: {e}")
            return 0.8
    
    def _calculate_context_dependency_completeness(self, chunk: TextChunk, context: Optional[Dict[str, Any]]) -> float:
        """
        计算上下文依赖完整性评分
        
        Args:
            chunk: 文本分块
            context: 上下文信息
            
        Returns:
            float: 上下文依赖完整性评分（0-1）
        """
        try:
            score = 0.7  # 基础分
            content = chunk.content
            
            # 检查上下文依赖指示词
            dependency_indicators = [
                r'如上所述|如前所述|上述|前面提到|如下所示|下面将|接下来',
                r'as mentioned|as shown|above|below|following|previous|next'
            ]
            
            has_dependencies = any(
                re.search(pattern, content, re.IGNORECASE) 
                for pattern in dependency_indicators
            )
            
            if not has_dependencies:
                return score  # 没有明显的上下文依赖
            
            # 如果有上下文依赖，检查是否能在当前分块中找到足够的信息
            if context:
                # 检查前后分块是否提供了必要的上下文
                prev_chunk = context.get('previous_chunk')
                next_chunk = context.get('next_chunk')
                
                if prev_chunk or next_chunk:
                    # 有上下文信息，认为依赖可能得到满足
                    score += 0.2
                else:
                    # 有依赖但缺少上下文，扣分
                    score -= 0.3
            else:
                # 没有上下文信息，无法验证依赖
                score -= 0.2
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            self.logger.warning(f"上下文依赖完整性评分计算失败: {e}")
            return 0.7
    
    def _identify_information_units(self, content: str) -> List[Tuple[str, str]]:
        """
        识别信息单元
        
        Args:
            content: 文本内容
            
        Returns:
            list: 信息单元列表，每个元素为(类型, 内容)
        """
        try:
            units = []
            
            # 定义信息单元模式
            unit_patterns = {
                'definition': r'(.*?[:：].*?[.。!！])',
                'instruction': r'(步骤\s*\d+.*?[.。!！])',
                'warning': r'(警告[:：].*?[.。!！])',
                'note': r'(注意[:：].*?[.。!！])',
                'specification': r'(\w+[:：]\s*\d+.*?[.。!！])',
                'procedure': r'(\d+\.\s*.*?[.。!！])'
            }
            
            for unit_type, pattern in unit_patterns.items():
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    units.append((unit_type, match.strip()))
            
            return units
            
        except Exception:
            return []
    
    def _is_information_unit_complete(self, unit_type: str, unit_content: str) -> bool:
        """
        检查信息单元是否完整
        
        Args:
            unit_type: 信息单元类型
            unit_content: 信息单元内容
            
        Returns:
            bool: 是否完整
        """
        try:
            # 基本完整性检查
            if len(unit_content.strip()) < 10:
                return False
            
            # 根据类型进行特定检查
            if unit_type == 'definition':
                return ':' in unit_content or '：' in unit_content
            elif unit_type == 'instruction':
                return any(unit_content.endswith(end) for end in ['.', '。', '!', '！'])
            elif unit_type in ['warning', 'note']:
                return len(unit_content) > 20 and any(unit_content.endswith(end) for end in ['.', '。', '!', '！'])
            elif unit_type == 'specification':
                return re.search(r'\d+', unit_content) is not None
            elif unit_type == 'procedure':
                return len(unit_content) > 15
            
            return True
            
        except Exception:
            return False
    
    def _is_logical_structure_complete(self, structure_type: str, content: str) -> bool:
        """
        检查逻辑结构是否完整
        
        Args:
            structure_type: 结构类型
            content: 文本内容
            
        Returns:
            bool: 是否完整
        """
        try:
            if structure_type == 'enumeration':
                # 检查枚举是否有开始和结束
                has_start = bool(re.search(r'第一|首先|1\.', content, re.IGNORECASE))
                has_continuation = bool(re.search(r'第二|其次|2\.|第三|最后|3\.', content, re.IGNORECASE))
                return has_start and has_continuation
            
            elif structure_type == 'cause_effect':
                # 检查因果关系是否完整
                has_cause = bool(re.search(r'因为|由于|because', content, re.IGNORECASE))
                has_effect = bool(re.search(r'所以|因此|导致|结果|therefore|result', content, re.IGNORECASE))
                return has_cause and has_effect
            
            elif structure_type == 'procedure':
                # 检查程序是否有多个步骤
                steps = re.findall(r'步骤\s*\d+|step\s+\d+|\d+\.', content, re.IGNORECASE)
                return len(steps) >= 2
            
            return True  # 其他类型默认认为完整
            
        except Exception:
            return False
    
    def _find_references(self, content: str) -> List[Tuple[str, str]]:
        """
        查找文本中的引用
        
        Args:
            content: 文本内容
            
        Returns:
            list: 引用列表，每个元素为(类型, 内容)
        """
        try:
            references = []
            
            for ref_type, patterns in self.reference_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        references.append((ref_type, match))
            
            return references
            
        except Exception:
            return []
    
    def _is_reference_complete(self, ref_type: str, ref_content: str, context: Optional[Dict[str, Any]]) -> bool:
        """
        检查引用是否完整
        
        Args:
            ref_type: 引用类型
            ref_content: 引用内容
            context: 上下文信息
            
        Returns:
            bool: 是否完整
        """
        try:
            # 简单的引用完整性检查
            # 在实际应用中，这里可以检查引用的目标是否存在
            
            if not context:
                return False  # 没有上下文信息，无法验证引用
            
            # 检查是否有相关的引用目标信息
            document_info = context.get('document_info', {})
            
            if ref_type == 'figure_ref':
                return 'figures' in document_info
            elif ref_type == 'table_ref':
                return 'tables' in document_info
            elif ref_type == 'section_ref':
                return 'sections' in document_info
            
            return True  # 其他类型默认认为完整
            
        except Exception:
            return False
    
    def _count_information_units(self, chunk: TextChunk) -> int:
        """
        统计信息单元数量
        
        Args:
            chunk: 文本分块
            
        Returns:
            int: 信息单元数量
        """
        try:
            units = self._identify_information_units(chunk.content)
            return len(units)
        except Exception:
            return 0
    
    def _analyze_completeness_issues(self, chunk: TextChunk, dimension_scores: Dict[str, float]) -> List[str]:
        """
        分析完整性问题
        
        Args:
            chunk: 文本分块
            dimension_scores: 各维度评分
            
        Returns:
            list: 问题列表
        """
        try:
            issues = []
            
            if dimension_scores.get('information_unit_completeness', 1.0) < 0.6:
                issues.append("信息单元不完整")
            
            if dimension_scores.get('logical_structure_completeness', 1.0) < 0.6:
                issues.append("逻辑结构不完整")
            
            if dimension_scores.get('reference_completeness', 1.0) < 0.6:
                issues.append("引用不完整")
            
            if dimension_scores.get('context_dependency_completeness', 1.0) < 0.6:
                issues.append("上下文依赖不完整")
            
            return issues
            
        except Exception:
            return []
