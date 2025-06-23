"""
模块名称: quality_controller
功能描述: 质量控制器，提供文档处理全流程的质量监控和优化
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# 导入统一日志管理器
try:
    from src.utils.logger import SZ_LoggerManager
    logger = SZ_LoggerManager.setup_logger(__name__)
except ImportError:
    # 回退到标准logging
    import logging
    logger = logging.getLogger(__name__)

from .chunk_validator import ChunkValidator, ValidationResult, ValidationLevel
from ..chunking.chunking_engine import TextChunk
from ..parsers.document_processor import UnifiedParseResult


@dataclass
class QualityReport:
    """质量报告数据类"""
    document_path: str
    processing_timestamp: str
    document_quality: Dict[str, Any]
    parsing_quality: Dict[str, Any]
    chunking_quality: ValidationResult
    overall_score: float
    recommendations: List[str]
    issues_summary: Dict[str, int]


class QualityController:
    """
    质量控制器
    
    提供文档处理全流程的质量监控和优化，包括：
    - 文档解析质量评估
    - 分块质量控制
    - 内容提取质量验证
    - 整体质量评分
    - 优化建议生成
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化质量控制器
        
        Args:
            config (dict, optional): 配置参数
                - validation_level (str): 验证级别，默认'normal'
                - enable_auto_fix (bool): 是否启用自动修复，默认False
                - quality_threshold (float): 质量阈值，默认0.7
                - generate_detailed_report (bool): 是否生成详细报告，默认True
        """
        self.config = config or {}
        self.logger = logger
        
        # 配置参数
        self.validation_level = self.config.get('validation_level', 'normal')
        self.enable_auto_fix = self.config.get('enable_auto_fix', False)
        self.quality_threshold = self.config.get('quality_threshold', 0.7)
        self.generate_detailed_report = self.config.get('generate_detailed_report', True)
        
        # 初始化验证器
        self.chunk_validator = ChunkValidator({
            'validation_level': self.validation_level,
            **self.config.get('chunk_validator_config', {})
        })
    
    def assess_document_quality(self, parse_result: UnifiedParseResult, 
                              chunks: Optional[List[TextChunk]] = None) -> QualityReport:
        """
        评估文档处理质量
        
        Args:
            parse_result: 文档解析结果
            chunks: 分块结果（可选）
            
        Returns:
            QualityReport: 质量报告
        """
        try:
            # 评估文档质量
            document_quality = self._assess_document_quality(parse_result)
            
            # 评估解析质量
            parsing_quality = self._assess_parsing_quality(parse_result)
            
            # 评估分块质量
            chunking_quality = None
            if chunks:
                chunking_quality = self.chunk_validator.validate_chunks(chunks)
            
            # 计算整体质量评分
            overall_score = self._calculate_overall_score(
                document_quality, parsing_quality, chunking_quality
            )
            
            # 生成综合建议
            recommendations = self._generate_comprehensive_recommendations(
                document_quality, parsing_quality, chunking_quality, overall_score
            )
            
            # 统计问题
            issues_summary = self._summarize_issues(
                document_quality, parsing_quality, chunking_quality
            )
            
            return QualityReport(
                document_path=parse_result.metadata.get('file_path', ''),
                processing_timestamp=datetime.now().isoformat(),
                document_quality=document_quality,
                parsing_quality=parsing_quality,
                chunking_quality=chunking_quality,
                overall_score=overall_score,
                recommendations=recommendations,
                issues_summary=issues_summary
            )
            
        except Exception as e:
            self.logger.error(f"文档质量评估失败: {e}")
            return self._create_error_report(str(e))
    
    def _assess_document_quality(self, parse_result: UnifiedParseResult) -> Dict[str, Any]:
        """评估文档质量"""
        try:
            quality_metrics = {
                'content_completeness': 0.0,
                'metadata_completeness': 0.0,
                'structure_clarity': 0.0,
                'content_richness': 0.0,
                'overall_document_score': 0.0
            }
            
            # 评估内容完整性
            content_completeness = self._evaluate_content_completeness(parse_result)
            quality_metrics['content_completeness'] = content_completeness
            
            # 评估元数据完整性
            metadata_completeness = self._evaluate_metadata_completeness(parse_result.metadata)
            quality_metrics['metadata_completeness'] = metadata_completeness
            
            # 评估结构清晰度
            structure_clarity = self._evaluate_structure_clarity(parse_result)
            quality_metrics['structure_clarity'] = structure_clarity
            
            # 评估内容丰富度
            content_richness = self._evaluate_content_richness(parse_result)
            quality_metrics['content_richness'] = content_richness
            
            # 计算整体文档评分
            quality_metrics['overall_document_score'] = (
                content_completeness * 0.3 +
                metadata_completeness * 0.2 +
                structure_clarity * 0.25 +
                content_richness * 0.25
            )
            
            return quality_metrics
            
        except Exception as e:
            self.logger.error(f"文档质量评估失败: {e}")
            return {'error': str(e)}
    
    def _evaluate_content_completeness(self, parse_result: UnifiedParseResult) -> float:
        """评估内容完整性"""
        try:
            score = 0.0
            
            # 检查文本内容
            if parse_result.text_content and len(parse_result.text_content.strip()) > 100:
                score += 0.4
            
            # 检查结构化数据
            structured_data = parse_result.structured_data
            if structured_data:
                if structured_data.get('tables'):
                    score += 0.2
                if structured_data.get('images'):
                    score += 0.2
                if structured_data.get('paragraphs') or structured_data.get('slides'):
                    score += 0.2
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.warning(f"内容完整性评估失败: {e}")
            return 0.0
    
    def _evaluate_metadata_completeness(self, metadata: Dict[str, Any]) -> float:
        """评估元数据完整性"""
        try:
            score = 0.0
            total_fields = 0
            filled_fields = 0
            
            # 检查核心元数据字段
            core_fields = ['title', 'author', 'created_date', 'file_size', 'file_extension']
            
            for field in core_fields:
                total_fields += 1
                if metadata.get(field) and str(metadata[field]).strip():
                    filled_fields += 1
            
            # 检查标准化元数据
            if 'standard' in metadata:
                standard_meta = metadata['standard']
                standard_fields = ['title', 'author', 'subject', 'keywords']
                
                for field in standard_fields:
                    total_fields += 1
                    if standard_meta.get(field) and str(standard_meta[field]).strip():
                        filled_fields += 1
            
            # 检查内容统计
            if 'content_statistics' in metadata:
                score += 0.2
            
            # 计算完整性评分
            if total_fields > 0:
                score += (filled_fields / total_fields) * 0.8
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.warning(f"元数据完整性评估失败: {e}")
            return 0.0
    
    def _evaluate_structure_clarity(self, parse_result: UnifiedParseResult) -> float:
        """评估结构清晰度"""
        try:
            score = 0.0
            structure_info = parse_result.structure_info
            
            if not structure_info:
                return 0.0
            
            # 检查标题结构
            if structure_info.get('heading_structure') or structure_info.get('has_toc'):
                score += 0.3
            
            # 检查段落结构
            if structure_info.get('total_paragraphs', 0) > 0:
                score += 0.2
            
            # 检查表格和图片的组织
            if structure_info.get('total_tables', 0) > 0:
                score += 0.2
            
            # 检查页面结构
            if structure_info.get('page_count', 0) > 0 or structure_info.get('total_slides', 0) > 0:
                score += 0.3
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.warning(f"结构清晰度评估失败: {e}")
            return 0.0
    
    def _evaluate_content_richness(self, parse_result: UnifiedParseResult) -> float:
        """评估内容丰富度"""
        try:
            score = 0.0
            
            # 检查文本长度
            text_length = len(parse_result.text_content) if parse_result.text_content else 0
            if text_length > 1000:
                score += 0.3
            elif text_length > 500:
                score += 0.2
            elif text_length > 100:
                score += 0.1
            
            # 检查多媒体内容
            structured_data = parse_result.structured_data
            if structured_data:
                tables_count = len(structured_data.get('tables', []))
                images_count = len(structured_data.get('images', []))
                
                if tables_count > 0:
                    score += min(0.3, tables_count * 0.1)
                
                if images_count > 0:
                    score += min(0.2, images_count * 0.05)
            
            # 检查内容多样性
            if parse_result.metadata.get('content_statistics'):
                stats = parse_result.metadata['content_statistics']
                if stats.get('primary_language') == 'mixed':
                    score += 0.1
                if stats.get('word_count', 0) > 500:
                    score += 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.warning(f"内容丰富度评估失败: {e}")
            return 0.0
    
    def _assess_parsing_quality(self, parse_result: UnifiedParseResult) -> Dict[str, Any]:
        """评估解析质量"""
        try:
            quality_metrics = {
                'extraction_completeness': 0.0,
                'format_preservation': 0.0,
                'error_rate': 0.0,
                'processing_efficiency': 0.0,
                'overall_parsing_score': 0.0
            }
            
            # 评估提取完整性
            extraction_completeness = self._evaluate_extraction_completeness(parse_result)
            quality_metrics['extraction_completeness'] = extraction_completeness
            
            # 评估格式保持
            format_preservation = self._evaluate_format_preservation(parse_result)
            quality_metrics['format_preservation'] = format_preservation
            
            # 评估错误率
            error_rate = self._evaluate_parsing_errors(parse_result)
            quality_metrics['error_rate'] = 1.0 - error_rate  # 转换为质量分数
            
            # 评估处理效率
            processing_efficiency = self._evaluate_processing_efficiency(parse_result)
            quality_metrics['processing_efficiency'] = processing_efficiency
            
            # 计算整体解析评分
            quality_metrics['overall_parsing_score'] = (
                extraction_completeness * 0.4 +
                format_preservation * 0.3 +
                quality_metrics['error_rate'] * 0.2 +
                processing_efficiency * 0.1
            )
            
            return quality_metrics
            
        except Exception as e:
            self.logger.error(f"解析质量评估失败: {e}")
            return {'error': str(e)}
    
    def _evaluate_extraction_completeness(self, parse_result: UnifiedParseResult) -> float:
        """评估提取完整性"""
        try:
            score = 0.0
            
            # 检查文本提取
            if parse_result.text_content:
                score += 0.5
            
            # 检查结构化数据提取
            structured_data = parse_result.structured_data
            if structured_data:
                expected_types = ['tables', 'images', 'paragraphs', 'slides']
                extracted_types = [t for t in expected_types if structured_data.get(t)]
                score += (len(extracted_types) / len(expected_types)) * 0.3
            
            # 检查元数据提取
            if parse_result.metadata:
                score += 0.2
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.warning(f"提取完整性评估失败: {e}")
            return 0.0
    
    def _evaluate_format_preservation(self, parse_result: UnifiedParseResult) -> float:
        """评估格式保持"""
        try:
            score = 0.8  # 基础分数
            
            # 检查是否有格式相关的错误或警告
            # 这里可以根据具体的解析器实现来检查格式保持情况
            
            return score
            
        except Exception as e:
            self.logger.warning(f"格式保持评估失败: {e}")
            return 0.0
    
    def _evaluate_parsing_errors(self, parse_result: UnifiedParseResult) -> float:
        """评估解析错误率"""
        try:
            # 检查元数据中的错误信息
            error_indicators = 0
            total_checks = 1
            
            # 检查是否有错误标记
            if hasattr(parse_result, 'errors') and parse_result.errors:
                error_indicators += len(parse_result.errors)
                total_checks += len(parse_result.errors)
            
            # 检查内容质量指标
            if parse_result.metadata.get('metadata_quality_score', 1.0) < 0.5:
                error_indicators += 1
            total_checks += 1
            
            return error_indicators / total_checks if total_checks > 0 else 0.0
            
        except Exception as e:
            self.logger.warning(f"解析错误率评估失败: {e}")
            return 0.0
    
    def _evaluate_processing_efficiency(self, parse_result: UnifiedParseResult) -> float:
        """评估处理效率"""
        try:
            # 基于文件大小和处理结果评估效率
            file_size = parse_result.metadata.get('file_size', 0)
            content_length = len(parse_result.text_content) if parse_result.text_content else 0
            
            if file_size > 0 and content_length > 0:
                # 简单的效率指标：提取的内容长度与文件大小的比率
                efficiency_ratio = min(1.0, content_length / file_size)
                return efficiency_ratio
            
            return 0.8  # 默认效率分数
            
        except Exception as e:
            self.logger.warning(f"处理效率评估失败: {e}")
            return 0.0
    
    def _calculate_overall_score(self, document_quality: Dict[str, Any], 
                               parsing_quality: Dict[str, Any], 
                               chunking_quality: Optional[ValidationResult]) -> float:
        """计算整体质量评分"""
        try:
            doc_score = document_quality.get('overall_document_score', 0.0)
            parse_score = parsing_quality.get('overall_parsing_score', 0.0)
            
            if chunking_quality:
                # 基于分块验证结果计算分块质量分数
                chunk_score = self._calculate_chunking_score(chunking_quality)
                overall_score = doc_score * 0.4 + parse_score * 0.3 + chunk_score * 0.3
            else:
                overall_score = doc_score * 0.6 + parse_score * 0.4
            
            return round(overall_score, 3)
            
        except Exception as e:
            self.logger.error(f"整体评分计算失败: {e}")
            return 0.0
    
    def _calculate_chunking_score(self, chunking_quality: ValidationResult) -> float:
        """计算分块质量分数"""
        try:
            if chunking_quality.total_chunks == 0:
                return 0.0
            
            # 基于有效分块比例
            valid_ratio = chunking_quality.valid_chunks / chunking_quality.total_chunks
            
            # 基于平均质量评分
            avg_quality = chunking_quality.quality_metrics.get('average_quality_score', 0.5)
            
            # 基于错误率
            error_rate = chunking_quality.quality_metrics.get('error_rate', 0.0)
            
            chunk_score = valid_ratio * 0.4 + avg_quality * 0.4 + (1.0 - error_rate) * 0.2
            
            return round(chunk_score, 3)
            
        except Exception as e:
            self.logger.error(f"分块质量分数计算失败: {e}")
            return 0.0
    
    def _generate_comprehensive_recommendations(self, document_quality: Dict[str, Any], 
                                              parsing_quality: Dict[str, Any], 
                                              chunking_quality: Optional[ValidationResult],
                                              overall_score: float) -> List[str]:
        """生成综合建议"""
        recommendations = []
        
        try:
            # 基于整体评分
            if overall_score < self.quality_threshold:
                recommendations.append(f"整体质量评分({overall_score:.2f})低于阈值({self.quality_threshold})，需要优化")
            
            # 基于文档质量
            if document_quality.get('overall_document_score', 0) < 0.6:
                recommendations.append("文档质量较低，建议检查源文档的完整性和格式")
            
            # 基于解析质量
            if parsing_quality.get('overall_parsing_score', 0) < 0.7:
                recommendations.append("解析质量需要改进，考虑调整解析器配置或预处理步骤")
            
            # 基于分块质量
            if chunking_quality and chunking_quality.quality_metrics.get('error_rate', 0) > 0.1:
                recommendations.append("分块错误率较高，建议优化分块策略或参数")
                recommendations.extend(chunking_quality.recommendations)
            
            if not recommendations:
                recommendations.append("文档处理质量良好，无需特别优化")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"建议生成失败: {e}")
            return ["建议生成过程出现错误"]
    
    def _summarize_issues(self, document_quality: Dict[str, Any], 
                         parsing_quality: Dict[str, Any], 
                         chunking_quality: Optional[ValidationResult]) -> Dict[str, int]:
        """统计问题摘要"""
        try:
            issues_summary = {
                'total_issues': 0,
                'critical_issues': 0,
                'warnings': 0,
                'info_items': 0
            }
            
            # 统计分块质量问题
            if chunking_quality:
                for issue in chunking_quality.issues:
                    issues_summary['total_issues'] += 1
                    if issue.severity == 'error':
                        issues_summary['critical_issues'] += 1
                    elif issue.severity == 'warning':
                        issues_summary['warnings'] += 1
                    else:
                        issues_summary['info_items'] += 1
            
            return issues_summary
            
        except Exception as e:
            self.logger.error(f"问题摘要统计失败: {e}")
            return {}
    
    def _create_error_report(self, error_message: str) -> QualityReport:
        """创建错误报告"""
        return QualityReport(
            document_path="",
            processing_timestamp=datetime.now().isoformat(),
            document_quality={'error': error_message},
            parsing_quality={'error': error_message},
            chunking_quality=None,
            overall_score=0.0,
            recommendations=[f"处理过程出现错误: {error_message}"],
            issues_summary={'total_issues': 1, 'critical_issues': 1, 'warnings': 0, 'info_items': 0}
        )
