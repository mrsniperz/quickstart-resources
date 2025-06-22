"""
模块名称: utils
功能描述: 质量评估工具函数和配置助手
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import logging
from typing import Dict, List, Any, Optional
from .base import QualityMetrics


class QualityConfigBuilder:
    """
    质量评估配置构建器
    
    帮助构建和管理质量评估的配置参数
    """
    
    def __init__(self):
        """初始化配置构建器"""
        self.config = {
            'default_strategy': 'aviation',
            'enable_caching': True,
            'cache_size': 1000,
            'strategies': {}
        }
    
    def set_default_strategy(self, strategy_name: str) -> 'QualityConfigBuilder':
        """
        设置默认策略
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            QualityConfigBuilder: 配置构建器实例
        """
        self.config['default_strategy'] = strategy_name
        return self
    
    def enable_caching(self, enabled: bool = True, cache_size: int = 1000) -> 'QualityConfigBuilder':
        """
        配置缓存设置
        
        Args:
            enabled: 是否启用缓存
            cache_size: 缓存大小
            
        Returns:
            QualityConfigBuilder: 配置构建器实例
        """
        self.config['enable_caching'] = enabled
        self.config['cache_size'] = cache_size
        return self
    
    def configure_aviation_strategy(self, **kwargs) -> 'QualityConfigBuilder':
        """
        配置航空策略
        
        Args:
            **kwargs: 航空策略配置参数
            
        Returns:
            QualityConfigBuilder: 配置构建器实例
        """
        aviation_config = {
            'weights': {
                'aviation_specific': kwargs.get('aviation_weight', 0.25),
                'semantic_completeness': kwargs.get('semantic_weight', 0.25),
                'information_density': kwargs.get('density_weight', 0.25),
                'structure_quality': kwargs.get('structure_weight', 0.20),
                'size_appropriateness': kwargs.get('size_weight', 0.05)
            },
            'min_chunk_size': kwargs.get('min_chunk_size', 100),
            'max_chunk_size': kwargs.get('max_chunk_size', 2000),
            'chunk_size': kwargs.get('chunk_size', 1000)
        }
        
        self.config['strategies']['aviation'] = aviation_config
        return self
    
    def configure_semantic_strategy(self, **kwargs) -> 'QualityConfigBuilder':
        """
        配置语义策略
        
        Args:
            **kwargs: 语义策略配置参数
            
        Returns:
            QualityConfigBuilder: 配置构建器实例
        """
        semantic_config = {
            'weights': {
                'semantic_boundary': kwargs.get('boundary_weight', 0.30),
                'topic_consistency': kwargs.get('topic_weight', 0.25),
                'context_coherence': kwargs.get('coherence_weight', 0.25),
                'semantic_completeness': kwargs.get('completeness_weight', 0.20)
            },
            'semantic_threshold': kwargs.get('semantic_threshold', 0.7),
            'coherence_window': kwargs.get('coherence_window', 3)
        }
        
        self.config['strategies']['semantic'] = semantic_config
        return self
    
    def configure_length_strategy(self, **kwargs) -> 'QualityConfigBuilder':
        """
        配置长度均匀性策略
        
        Args:
            **kwargs: 长度策略配置参数
            
        Returns:
            QualityConfigBuilder: 配置构建器实例
        """
        length_config = {
            'target_length': kwargs.get('target_length', 1000),
            'min_length': kwargs.get('min_length', 100),
            'max_length': kwargs.get('max_length', 2000),
            'tolerance_ratio': kwargs.get('tolerance_ratio', 0.3),
            'weights': {
                'size_appropriateness': kwargs.get('size_weight', 0.40),
                'length_uniformity': kwargs.get('uniformity_weight', 0.30),
                'relative_consistency': kwargs.get('consistency_weight', 0.20),
                'variation_coefficient': kwargs.get('variation_weight', 0.10)
            }
        }
        
        self.config['strategies']['length_uniformity'] = length_config
        return self
    
    def configure_completeness_strategy(self, **kwargs) -> 'QualityConfigBuilder':
        """
        配置内容完整性策略
        
        Args:
            **kwargs: 完整性策略配置参数
            
        Returns:
            QualityConfigBuilder: 配置构建器实例
        """
        completeness_config = {
            'weights': {
                'information_unit_completeness': kwargs.get('info_unit_weight', 0.30),
                'logical_structure_completeness': kwargs.get('logic_weight', 0.25),
                'reference_completeness': kwargs.get('reference_weight', 0.25),
                'context_dependency_completeness': kwargs.get('context_weight', 0.20)
            },
            'completeness_threshold': kwargs.get('completeness_threshold', 0.7)
        }
        
        self.config['strategies']['content_completeness'] = completeness_config
        return self
    
    def build(self) -> Dict[str, Any]:
        """
        构建配置
        
        Returns:
            dict: 完整的配置字典
        """
        return self.config.copy()


class QualityAnalyzer:
    """
    质量分析工具
    
    提供质量评估结果的分析和统计功能
    """
    
    @staticmethod
    def analyze_quality_distribution(quality_results: List[QualityMetrics]) -> Dict[str, Any]:
        """
        分析质量分布
        
        Args:
            quality_results: 质量评估结果列表
            
        Returns:
            dict: 质量分布分析结果
        """
        try:
            if not quality_results:
                return {'error': '没有质量评估结果'}
            
            scores = [result.overall_score for result in quality_results]
            
            # 基本统计
            analysis = {
                'total_chunks': len(scores),
                'mean_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'score_distribution': {
                    'excellent': len([s for s in scores if s >= 0.8]),
                    'good': len([s for s in scores if 0.6 <= s < 0.8]),
                    'fair': len([s for s in scores if 0.4 <= s < 0.6]),
                    'poor': len([s for s in scores if s < 0.4])
                }
            }
            
            # 计算标准差
            if len(scores) > 1:
                mean = analysis['mean_score']
                variance = sum((s - mean) ** 2 for s in scores) / len(scores)
                analysis['std_deviation'] = variance ** 0.5
            else:
                analysis['std_deviation'] = 0.0
            
            # 维度分析
            dimension_analysis = {}
            for result in quality_results:
                for dimension, score in result.dimension_scores.items():
                    if dimension not in dimension_analysis:
                        dimension_analysis[dimension] = []
                    dimension_analysis[dimension].append(score)
            
            # 计算各维度平均分
            dimension_means = {}
            for dimension, scores_list in dimension_analysis.items():
                if scores_list:
                    dimension_means[dimension] = sum(scores_list) / len(scores_list)
            
            analysis['dimension_means'] = dimension_means
            
            return analysis
            
        except Exception as e:
            return {'error': f'质量分布分析失败: {e}'}
    
    @staticmethod
    def identify_quality_issues(quality_results: List[QualityMetrics], threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        识别质量问题
        
        Args:
            quality_results: 质量评估结果列表
            threshold: 质量阈值
            
        Returns:
            list: 质量问题列表
        """
        try:
            issues = []
            
            for i, result in enumerate(quality_results):
                chunk_issues = {
                    'chunk_index': i,
                    'overall_score': result.overall_score,
                    'issues': []
                }
                
                # 检查总体评分
                if result.overall_score < threshold:
                    chunk_issues['issues'].append(f"总体质量低于阈值 ({result.overall_score:.3f} < {threshold})")
                
                # 检查各维度评分
                for dimension, score in result.dimension_scores.items():
                    if score < threshold:
                        chunk_issues['issues'].append(f"{dimension} 评分过低: {score:.3f}")
                
                # 检查置信度
                if result.confidence < 0.5:
                    chunk_issues['issues'].append(f"评估置信度过低: {result.confidence:.3f}")
                
                # 添加详细问题信息
                if 'completeness_issues' in result.details:
                    chunk_issues['issues'].extend(result.details['completeness_issues'])
                
                if chunk_issues['issues']:
                    issues.append(chunk_issues)
            
            return issues
            
        except Exception as e:
            logging.error(f"质量问题识别失败: {e}")
            return []
    
    @staticmethod
    def generate_quality_report(quality_results: List[QualityMetrics]) -> str:
        """
        生成质量报告
        
        Args:
            quality_results: 质量评估结果列表
            
        Returns:
            str: 质量报告文本
        """
        try:
            if not quality_results:
                return "没有质量评估结果可供分析"
            
            # 分析质量分布
            distribution = QualityAnalyzer.analyze_quality_distribution(quality_results)
            
            # 识别质量问题
            issues = QualityAnalyzer.identify_quality_issues(quality_results)
            
            # 生成报告
            report = []
            report.append("# 分块质量评估报告")
            report.append("")
            
            # 基本统计
            report.append("## 基本统计")
            report.append(f"- 总分块数: {distribution['total_chunks']}")
            report.append(f"- 平均质量评分: {distribution['mean_score']:.3f}")
            report.append(f"- 最高评分: {distribution['max_score']:.3f}")
            report.append(f"- 最低评分: {distribution['min_score']:.3f}")
            report.append(f"- 标准差: {distribution['std_deviation']:.3f}")
            report.append("")
            
            # 质量分布
            report.append("## 质量分布")
            dist = distribution['score_distribution']
            report.append(f"- 优秀 (≥0.8): {dist['excellent']} ({dist['excellent']/distribution['total_chunks']*100:.1f}%)")
            report.append(f"- 良好 (0.6-0.8): {dist['good']} ({dist['good']/distribution['total_chunks']*100:.1f}%)")
            report.append(f"- 一般 (0.4-0.6): {dist['fair']} ({dist['fair']/distribution['total_chunks']*100:.1f}%)")
            report.append(f"- 较差 (<0.4): {dist['poor']} ({dist['poor']/distribution['total_chunks']*100:.1f}%)")
            report.append("")
            
            # 维度分析
            if 'dimension_means' in distribution:
                report.append("## 维度分析")
                for dimension, mean_score in distribution['dimension_means'].items():
                    report.append(f"- {dimension}: {mean_score:.3f}")
                report.append("")
            
            # 质量问题
            if issues:
                report.append("## 质量问题")
                report.append(f"发现 {len(issues)} 个分块存在质量问题:")
                for issue in issues[:10]:  # 只显示前10个问题
                    report.append(f"- 分块 {issue['chunk_index']} (评分: {issue['overall_score']:.3f})")
                    for problem in issue['issues'][:3]:  # 每个分块最多显示3个问题
                        report.append(f"  * {problem}")
                
                if len(issues) > 10:
                    report.append(f"... 还有 {len(issues) - 10} 个分块存在问题")
                report.append("")
            
            # 建议
            report.append("## 改进建议")
            if distribution['mean_score'] < 0.6:
                report.append("- 整体质量偏低，建议检查分块策略和参数配置")
            if dist['poor'] > distribution['total_chunks'] * 0.2:
                report.append("- 低质量分块比例过高，建议优化分块算法")
            if distribution['std_deviation'] > 0.3:
                report.append("- 质量评分差异较大，建议检查内容一致性")
            
            return "\n".join(report)
            
        except Exception as e:
            return f"生成质量报告失败: {e}"


def create_aviation_config() -> Dict[str, Any]:
    """
    创建航空领域的默认质量评估配置
    
    Returns:
        dict: 航空领域配置
    """
    return (QualityConfigBuilder()
            .set_default_strategy('aviation')
            .enable_caching(True, 1000)
            .configure_aviation_strategy(
                aviation_weight=0.30,
                semantic_weight=0.25,
                density_weight=0.20,
                structure_weight=0.20,
                size_weight=0.05
            )
            .build())


def create_general_config() -> Dict[str, Any]:
    """
    创建通用的质量评估配置
    
    Returns:
        dict: 通用配置
    """
    return (QualityConfigBuilder()
            .set_default_strategy('basic')
            .enable_caching(True, 500)
            .build())
