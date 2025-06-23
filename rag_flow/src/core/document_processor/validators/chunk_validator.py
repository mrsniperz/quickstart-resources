"""
模块名称: chunk_validator
功能描述: 分块验证器，提供分块质量控制、完整性验证和优化建议
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# 导入统一日志管理器
try:
    from src.utils.logger import SZ_LoggerManager
    logger = SZ_LoggerManager.setup_logger(__name__)
except ImportError:
    # 回退到标准logging
    import logging
    logger = logging.getLogger(__name__)

from ..chunking.chunking_engine import TextChunk, ChunkType


class ValidationLevel(Enum):
    """验证级别枚举"""
    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"


@dataclass
class ValidationIssue:
    """验证问题数据类"""
    chunk_id: str
    issue_type: str
    severity: str  # error, warning, info
    message: str
    suggestion: Optional[str] = None
    affected_content: Optional[str] = None


@dataclass
class ValidationResult:
    """验证结果数据类"""
    total_chunks: int
    valid_chunks: int
    invalid_chunks: int
    issues: List[ValidationIssue]
    quality_metrics: Dict[str, Any]
    recommendations: List[str]


class ChunkValidator:
    """
    分块验证器
    
    提供分块质量控制、完整性验证和优化建议，包括：
    - 分块大小验证
    - 内容完整性检查
    - 语义连贯性验证
    - 重叠内容检查
    - 质量评分计算
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化分块验证器
        
        Args:
            config (dict, optional): 配置参数
                - validation_level (str): 验证级别，默认'normal'
                - min_chunk_size (int): 最小分块大小，默认100
                - max_chunk_size (int): 最大分块大小，默认2000
                - optimal_chunk_size (int): 最优分块大小，默认800
                - min_quality_score (float): 最小质量评分，默认0.3
                - check_overlap (bool): 是否检查重叠，默认True
                - check_completeness (bool): 是否检查完整性，默认True
        """
        self.config = config or {}
        self.logger = logger
        
        # 配置参数
        self.validation_level = ValidationLevel(self.config.get('validation_level', 'normal'))
        self.min_chunk_size = self.config.get('min_chunk_size', 100)
        self.max_chunk_size = self.config.get('max_chunk_size', 2000)
        self.optimal_chunk_size = self.config.get('optimal_chunk_size', 800)
        self.min_quality_score = self.config.get('min_quality_score', 0.3)
        self.check_overlap = self.config.get('check_overlap', True)
        self.check_completeness = self.config.get('check_completeness', True)
        
        # 验证规则配置
        self._setup_validation_rules()
    
    def validate_chunks(self, chunks: List[TextChunk]) -> ValidationResult:
        """
        验证分块列表
        
        Args:
            chunks: 分块列表
            
        Returns:
            ValidationResult: 验证结果
        """
        try:
            if not chunks:
                return ValidationResult(
                    total_chunks=0,
                    valid_chunks=0,
                    invalid_chunks=0,
                    issues=[],
                    quality_metrics={},
                    recommendations=["没有分块需要验证"]
                )
            
            issues = []
            valid_count = 0
            
            # 逐个验证分块
            for i, chunk in enumerate(chunks):
                chunk_issues = self._validate_single_chunk(chunk, i)
                issues.extend(chunk_issues)
                
                # 统计有效分块
                if not any(issue.severity == 'error' for issue in chunk_issues):
                    valid_count += 1
            
            # 验证分块间关系
            relationship_issues = self._validate_chunk_relationships(chunks)
            issues.extend(relationship_issues)
            
            # 计算质量指标
            quality_metrics = self._calculate_quality_metrics(chunks, issues)
            
            # 生成建议
            recommendations = self._generate_recommendations(chunks, issues, quality_metrics)
            
            return ValidationResult(
                total_chunks=len(chunks),
                valid_chunks=valid_count,
                invalid_chunks=len(chunks) - valid_count,
                issues=issues,
                quality_metrics=quality_metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"分块验证失败: {e}")
            return ValidationResult(
                total_chunks=len(chunks) if chunks else 0,
                valid_chunks=0,
                invalid_chunks=len(chunks) if chunks else 0,
                issues=[ValidationIssue("", "system_error", "error", f"验证过程失败: {e}")],
                quality_metrics={},
                recommendations=[]
            )
    
    def _validate_single_chunk(self, chunk: TextChunk, index: int) -> List[ValidationIssue]:
        """
        验证单个分块
        
        Args:
            chunk: 文本分块
            index: 分块索引
            
        Returns:
            list: 验证问题列表
        """
        try:
            issues = []
            chunk_id = chunk.metadata.chunk_id or f"chunk_{index}"
            
            # 验证分块大小
            size_issues = self._validate_chunk_size(chunk, chunk_id)
            issues.extend(size_issues)
            
            # 验证内容质量
            content_issues = self._validate_content_quality(chunk, chunk_id)
            issues.extend(content_issues)
            
            # 验证元数据
            metadata_issues = self._validate_metadata(chunk, chunk_id)
            issues.extend(metadata_issues)
            
            # 验证内容完整性
            if self.check_completeness:
                completeness_issues = self._validate_content_completeness(chunk, chunk_id)
                issues.extend(completeness_issues)
            
            return issues
            
        except Exception as e:
            self.logger.error(f"单个分块验证失败: {e}")
            return [ValidationIssue(
                chunk_id=chunk.metadata.chunk_id or f"chunk_{index}",
                issue_type="validation_error",
                severity="error",
                message=f"分块验证过程失败: {e}"
            )]
    
    def _validate_chunk_size(self, chunk: TextChunk, chunk_id: str) -> List[ValidationIssue]:
        """验证分块大小"""
        issues = []
        content_length = len(chunk.content)
        
        # 检查最小大小
        if content_length < self.min_chunk_size:
            severity = "error" if self.validation_level == ValidationLevel.STRICT else "warning"
            issues.append(ValidationIssue(
                chunk_id=chunk_id,
                issue_type="size_too_small",
                severity=severity,
                message=f"分块过小: {content_length}字符 < {self.min_chunk_size}字符",
                suggestion="考虑与相邻分块合并或调整分块策略"
            ))
        
        # 检查最大大小
        if content_length > self.max_chunk_size:
            severity = "error" if self.validation_level == ValidationLevel.STRICT else "warning"
            issues.append(ValidationIssue(
                chunk_id=chunk_id,
                issue_type="size_too_large",
                severity=severity,
                message=f"分块过大: {content_length}字符 > {self.max_chunk_size}字符",
                suggestion="考虑进一步分割或调整分块策略"
            ))
        
        # 检查最优大小
        if abs(content_length - self.optimal_chunk_size) > self.optimal_chunk_size * 0.5:
            if self.validation_level != ValidationLevel.LENIENT:
                issues.append(ValidationIssue(
                    chunk_id=chunk_id,
                    issue_type="size_suboptimal",
                    severity="info",
                    message=f"分块大小偏离最优值: {content_length}字符，最优值: {self.optimal_chunk_size}字符",
                    suggestion="考虑调整分块参数以获得更好的性能"
                ))
        
        return issues
    
    def _validate_content_quality(self, chunk: TextChunk, chunk_id: str) -> List[ValidationIssue]:
        """验证内容质量"""
        issues = []
        content = chunk.content.strip()
        
        # 检查空内容
        if not content:
            issues.append(ValidationIssue(
                chunk_id=chunk_id,
                issue_type="empty_content",
                severity="error",
                message="分块内容为空",
                suggestion="移除空分块或检查分块逻辑"
            ))
            return issues
        
        # 检查质量评分
        if hasattr(chunk, 'quality_score') and chunk.quality_score < self.min_quality_score:
            severity = "warning" if self.validation_level == ValidationLevel.LENIENT else "error"
            issues.append(ValidationIssue(
                chunk_id=chunk_id,
                issue_type="low_quality_score",
                severity=severity,
                message=f"质量评分过低: {chunk.quality_score} < {self.min_quality_score}",
                suggestion="检查分块内容的完整性和连贯性"
            ))
        
        # 检查内容结构
        structure_issues = self._check_content_structure(content, chunk_id)
        issues.extend(structure_issues)
        
        # 检查字符质量
        char_issues = self._check_character_quality(content, chunk_id)
        issues.extend(char_issues)
        
        return issues
    
    def _check_content_structure(self, content: str, chunk_id: str) -> List[ValidationIssue]:
        """检查内容结构"""
        issues = []
        
        # 检查是否只包含空白字符
        if not content.strip():
            issues.append(ValidationIssue(
                chunk_id=chunk_id,
                issue_type="whitespace_only",
                severity="error",
                message="分块只包含空白字符",
                suggestion="移除或合并此分块"
            ))
            return issues
        
        # 检查句子完整性
        if not re.search(r'[.!?。！？]', content):
            if self.validation_level == ValidationLevel.STRICT:
                issues.append(ValidationIssue(
                    chunk_id=chunk_id,
                    issue_type="no_sentence_ending",
                    severity="warning",
                    message="分块不包含完整的句子结束标记",
                    suggestion="检查分块边界是否合理"
                ))
        
        # 检查重复内容
        lines = content.split('\n')
        unique_lines = set(line.strip() for line in lines if line.strip())
        if len(lines) > 1 and len(unique_lines) < len(lines) * 0.8:
            issues.append(ValidationIssue(
                chunk_id=chunk_id,
                issue_type="repetitive_content",
                severity="warning",
                message="分块包含大量重复内容",
                suggestion="检查分块逻辑或内容预处理"
            ))
        
        return issues
    
    def _check_character_quality(self, content: str, chunk_id: str) -> List[ValidationIssue]:
        """检查字符质量"""
        issues = []
        
        # 计算有效字符比例
        total_chars = len(content)
        if total_chars == 0:
            return issues
        
        # 检查空白字符比例
        whitespace_chars = len(re.findall(r'\s', content))
        whitespace_ratio = whitespace_chars / total_chars
        
        if whitespace_ratio > 0.5:
            issues.append(ValidationIssue(
                chunk_id=chunk_id,
                issue_type="excessive_whitespace",
                severity="warning",
                message=f"空白字符比例过高: {whitespace_ratio:.2%}",
                suggestion="检查文本预处理或分块逻辑"
            ))
        
        # 检查特殊字符
        special_chars = len(re.findall(r'[^\w\s\u4e00-\u9fff.,!?;:()"\'-]', content))
        special_ratio = special_chars / total_chars
        
        if special_ratio > 0.1:
            issues.append(ValidationIssue(
                chunk_id=chunk_id,
                issue_type="excessive_special_chars",
                severity="info",
                message=f"特殊字符比例较高: {special_ratio:.2%}",
                suggestion="检查是否包含编码错误或格式问题"
            ))
        
        return issues
    
    def _validate_metadata(self, chunk: TextChunk, chunk_id: str) -> List[ValidationIssue]:
        """验证元数据"""
        issues = []
        metadata = chunk.metadata
        
        # 检查必需字段
        if not metadata.chunk_id:
            issues.append(ValidationIssue(
                chunk_id=chunk_id,
                issue_type="missing_chunk_id",
                severity="error",
                message="缺少分块ID",
                suggestion="确保分块处理过程中正确设置ID"
            ))
        
        if not metadata.source_document:
            issues.append(ValidationIssue(
                chunk_id=chunk_id,
                issue_type="missing_source_document",
                severity="warning",
                message="缺少源文档信息",
                suggestion="设置源文档路径或标识"
            ))
        
        # 检查分块类型
        if metadata.chunk_type == ChunkType.CUSTOM and self.validation_level == ValidationLevel.STRICT:
            issues.append(ValidationIssue(
                chunk_id=chunk_id,
                issue_type="undefined_chunk_type",
                severity="info",
                message="使用了自定义分块类型",
                suggestion="考虑使用标准分块类型"
            ))
        
        return issues
    
    def _validate_content_completeness(self, chunk: TextChunk, chunk_id: str) -> List[ValidationIssue]:
        """验证内容完整性"""
        issues = []
        content = chunk.content
        
        # 检查截断的句子
        if content.endswith(('，', ',', '、', ';', ':')):
            issues.append(ValidationIssue(
                chunk_id=chunk_id,
                issue_type="incomplete_sentence",
                severity="warning",
                message="分块可能以不完整的句子结尾",
                suggestion="调整分块边界以保持句子完整性"
            ))
        
        # 检查开头的连接词
        connecting_words = ['但是', '然而', '因此', '所以', '另外', '此外', 'however', 'therefore', 'moreover']
        first_words = content.split()[:3]
        if any(word.lower() in connecting_words for word in first_words):
            issues.append(ValidationIssue(
                chunk_id=chunk_id,
                issue_type="orphaned_connector",
                severity="info",
                message="分块以连接词开始，可能缺少上下文",
                suggestion="考虑调整分块边界或增加重叠内容"
            ))
        
        return issues
    
    def _validate_chunk_relationships(self, chunks: List[TextChunk]) -> List[ValidationIssue]:
        """验证分块间关系"""
        issues = []
        
        if not self.check_overlap or len(chunks) < 2:
            return issues
        
        # 检查相邻分块的重叠和连贯性
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]
            
            # 检查过度重叠
            overlap_issues = self._check_chunk_overlap(current_chunk, next_chunk, i)
            issues.extend(overlap_issues)
            
            # 检查连贯性
            coherence_issues = self._check_chunk_coherence(current_chunk, next_chunk, i)
            issues.extend(coherence_issues)
        
        return issues
    
    def _check_chunk_overlap(self, chunk1: TextChunk, chunk2: TextChunk, index: int) -> List[ValidationIssue]:
        """检查分块重叠"""
        issues = []
        
        # 简单的重叠检测（可以优化为更复杂的算法）
        content1_words = set(chunk1.content.split())
        content2_words = set(chunk2.content.split())
        
        if content1_words and content2_words:
            overlap_words = content1_words.intersection(content2_words)
            overlap_ratio = len(overlap_words) / min(len(content1_words), len(content2_words))
            
            if overlap_ratio > 0.8:
                issues.append(ValidationIssue(
                    chunk_id=f"chunks_{index}_{index+1}",
                    issue_type="excessive_overlap",
                    severity="warning",
                    message=f"相邻分块重叠过多: {overlap_ratio:.2%}",
                    suggestion="检查分块逻辑或减少重叠设置"
                ))
        
        return issues
    
    def _check_chunk_coherence(self, chunk1: TextChunk, chunk2: TextChunk, index: int) -> List[ValidationIssue]:
        """检查分块连贯性"""
        issues = []
        
        # 简单的连贯性检测
        content1_end = chunk1.content.strip()[-100:] if len(chunk1.content) > 100 else chunk1.content.strip()
        content2_start = chunk2.content.strip()[:100] if len(chunk2.content) > 100 else chunk2.content.strip()
        
        # 检查主题突变（这里使用简单的关键词检测）
        # 在实际应用中可以使用更复杂的语义分析
        
        return issues
    
    def _calculate_quality_metrics(self, chunks: List[TextChunk], issues: List[ValidationIssue]) -> Dict[str, Any]:
        """计算质量指标"""
        try:
            if not chunks:
                return {}
            
            # 基本统计
            total_chunks = len(chunks)
            total_length = sum(len(chunk.content) for chunk in chunks)
            avg_length = total_length / total_chunks
            
            # 大小分布
            lengths = [len(chunk.content) for chunk in chunks]
            min_length = min(lengths)
            max_length = max(lengths)
            
            # 问题统计
            error_count = sum(1 for issue in issues if issue.severity == 'error')
            warning_count = sum(1 for issue in issues if issue.severity == 'warning')
            info_count = sum(1 for issue in issues if issue.severity == 'info')
            
            # 质量评分
            quality_scores = [getattr(chunk, 'quality_score', 0.5) for chunk in chunks]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            return {
                'total_chunks': total_chunks,
                'total_length': total_length,
                'average_length': round(avg_length, 2),
                'min_length': min_length,
                'max_length': max_length,
                'length_std': round(self._calculate_std(lengths), 2),
                'error_count': error_count,
                'warning_count': warning_count,
                'info_count': info_count,
                'error_rate': round(error_count / total_chunks, 3),
                'average_quality_score': round(avg_quality, 3),
                'chunks_below_min_quality': sum(1 for score in quality_scores if score < self.min_quality_score)
            }
            
        except Exception as e:
            self.logger.error(f"质量指标计算失败: {e}")
            return {'error': str(e)}
    
    def _calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _generate_recommendations(self, chunks: List[TextChunk], 
                                issues: List[ValidationIssue], 
                                quality_metrics: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        try:
            # 基于问题类型生成建议
            issue_types = [issue.issue_type for issue in issues]
            
            if 'size_too_small' in issue_types:
                recommendations.append("考虑增加分块大小或合并相邻的小分块")
            
            if 'size_too_large' in issue_types:
                recommendations.append("考虑减少分块大小或使用更细粒度的分块策略")
            
            if 'low_quality_score' in issue_types:
                recommendations.append("检查分块策略的语义连贯性和完整性设置")
            
            if 'excessive_overlap' in issue_types:
                recommendations.append("减少分块重叠设置或优化重叠策略")
            
            # 基于质量指标生成建议
            if quality_metrics.get('error_rate', 0) > 0.1:
                recommendations.append("错误率较高，建议检查分块配置和输入数据质量")
            
            if quality_metrics.get('length_std', 0) > quality_metrics.get('average_length', 0) * 0.5:
                recommendations.append("分块大小变化较大，考虑使用更一致的分块策略")
            
            if not recommendations:
                recommendations.append("分块质量良好，无需特别优化")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"建议生成失败: {e}")
            return ["建议生成过程出现错误，请检查验证配置"]
    
    def _setup_validation_rules(self) -> None:
        """设置验证规则"""
        # 根据验证级别调整规则严格程度
        if self.validation_level == ValidationLevel.STRICT:
            self.min_quality_score = max(self.min_quality_score, 0.5)
        elif self.validation_level == ValidationLevel.LENIENT:
            self.min_quality_score = min(self.min_quality_score, 0.2)
