"""
模块名称: example_usage
功能描述: 文档预处理模块使用示例
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import logging
from pathlib import Path
from typing import List

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def example_basic_usage():
    """基本使用示例"""
    print("=== 文档预处理模块基本使用示例 ===\n")
    
    try:
        from .parsers.document_processor import DocumentProcessor
        
        # 初始化文档处理器
        processor = DocumentProcessor()
        
        # 示例文档路径（实际使用时需要提供真实文档）
        sample_files = [
            "sample_manual.pdf",
            "regulation.docx", 
            "data_sheet.xlsx",
            "training.pptx"
        ]
        
        print("支持的文件格式:", processor.get_supported_formats())
        print()
        
        for file_path in sample_files:
            print(f"检查文件格式支持: {file_path}")
            is_supported = processor.is_supported_format(file_path)
            doc_type = processor.detect_document_type(file_path)
            print(f"  - 是否支持: {is_supported}")
            print(f"  - 文档类型: {doc_type.value}")
            print()
            
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所需的依赖库")

def example_pdf_processing():
    """PDF文档处理示例"""
    print("=== PDF文档处理示例 ===\n")
    
    try:
        from .parsers.pdf_parser import PDFParser
        
        # 配置PDF解析器
        config = {
            'extract_images': True,
            'extract_tables': True,
            'preserve_layout': True,
            'ocr_enabled': False
        }
        
        parser = PDFParser(config)
        
        print("PDF解析器配置:")
        print(f"  - 提取图像: {config['extract_images']}")
        print(f"  - 提取表格: {config['extract_tables']}")
        print(f"  - 保持布局: {config['preserve_layout']}")
        print(f"  - OCR功能: {config['ocr_enabled']}")
        print()
        
        print("支持的格式:", parser.get_supported_formats())
        print()
        
        # 示例：如果有真实PDF文件
        # result = parser.parse("sample.pdf")
        # print(f"解析结果:")
        # print(f"  - 页数: {result.page_count}")
        # print(f"  - 文本长度: {len(result.text_content)}")
        # print(f"  - 表格数量: {len(result.tables)}")
        # print(f"  - 图像数量: {len(result.images)}")
        
    except ImportError as e:
        print(f"导入错误: {e}")

def example_chunking_strategies():
    """分块策略示例"""
    print("=== 智能分块策略示例 ===\n")
    
    try:
        from .chunking.chunking_engine import ChunkingEngine
        
        # 配置分块引擎
        config = {
            'chunk_size': 800,
            'chunk_overlap': 200,
            'min_chunk_size': 100,
            'max_chunk_size': 1500,
            'preserve_context': True
        }
        
        engine = ChunkingEngine(config)
        
        print("分块引擎配置:")
        print(f"  - 目标分块大小: {config['chunk_size']}")
        print(f"  - 重叠大小: {config['chunk_overlap']}")
        print(f"  - 最小分块: {config['min_chunk_size']}")
        print(f"  - 最大分块: {config['max_chunk_size']}")
        print()
        
        print("可用的分块策略:", engine.get_available_strategies())
        print()
        
        # 示例文本
        sample_text = """
        第一章 航空安全管理
        
        1.1 安全管理体系
        航空安全管理体系是确保航空运输安全的重要保障。
        
        1.2 风险评估
        定期进行风险评估是安全管理的核心环节。
        
        第二章 维修程序
        
        2.1 日常检查
        每日飞行前必须进行全面的安全检查。
        
        2.2 定期维护
        按照制造商要求进行定期维护。
        """
        
        # 模拟文档元数据
        metadata = {
            'title': '航空维修手册',
            'document_type': 'maintenance_manual',
            'file_path': 'sample_manual.pdf'
        }
        
        # 执行分块（注意：实际使用时需要注册策略）
        # chunks = engine.chunk_document(sample_text, metadata)
        # print(f"分块结果: {len(chunks)}个分块")
        
    except ImportError as e:
        print(f"导入错误: {e}")

def example_quality_control():
    """质量控制示例"""
    print("=== 质量控制示例 ===\n")
    
    try:
        from .validators.chunk_validator import ChunkValidator, ValidationLevel
        from .validators.quality_controller import QualityController
        
        # 配置验证器
        validator_config = {
            'validation_level': 'normal',
            'min_chunk_size': 100,
            'max_chunk_size': 2000,
            'min_quality_score': 0.3
        }
        
        validator = ChunkValidator(validator_config)
        
        print("分块验证器配置:")
        print(f"  - 验证级别: {validator_config['validation_level']}")
        print(f"  - 最小分块大小: {validator_config['min_chunk_size']}")
        print(f"  - 最大分块大小: {validator_config['max_chunk_size']}")
        print(f"  - 最小质量评分: {validator_config['min_quality_score']}")
        print()
        
        # 配置质量控制器
        qc_config = {
            'validation_level': 'normal',
            'quality_threshold': 0.7,
            'generate_detailed_report': True
        }
        
        controller = QualityController(qc_config)
        
        print("质量控制器配置:")
        print(f"  - 验证级别: {qc_config['validation_level']}")
        print(f"  - 质量阈值: {qc_config['quality_threshold']}")
        print(f"  - 详细报告: {qc_config['generate_detailed_report']}")
        print()
        
    except ImportError as e:
        print(f"导入错误: {e}")

def example_aviation_specific():
    """航空行业特定功能示例"""
    print("=== 航空行业特定功能示例 ===\n")
    
    try:
        from .chunking.aviation_strategy import (
            AviationMaintenanceStrategy,
            AviationRegulationStrategy,
            AviationStandardStrategy,
            AviationTrainingStrategy
        )
        
        strategies = {
            '维修手册': AviationMaintenanceStrategy,
            '规章制度': AviationRegulationStrategy,
            '技术标准': AviationStandardStrategy,
            '培训资料': AviationTrainingStrategy
        }
        
        print("航空行业专用分块策略:")
        for name, strategy_class in strategies.items():
            strategy = strategy_class()
            print(f"  - {name}: {strategy.get_strategy_name()}")
        print()
        
        # 示例：维修手册特定模式
        print("维修手册识别模式示例:")
        maintenance_patterns = [
            "任务 1: 发动机检查",
            "警告: 高温部件",
            "所需工具: 扭矩扳手",
            "步骤 1: 关闭发动机"
        ]
        
        for pattern in maintenance_patterns:
            print(f"  - {pattern}")
        print()
        
    except ImportError as e:
        print(f"导入错误: {e}")

def main():
    """主函数 - 运行所有示例"""
    print("航空RAG系统 - 文档预处理模块使用示例")
    print("=" * 50)
    print()
    
    # 运行各个示例
    example_basic_usage()
    print("\n" + "-" * 50 + "\n")
    
    example_pdf_processing()
    print("\n" + "-" * 50 + "\n")
    
    example_chunking_strategies()
    print("\n" + "-" * 50 + "\n")
    
    example_quality_control()
    print("\n" + "-" * 50 + "\n")
    
    example_aviation_specific()
    print("\n" + "-" * 50 + "\n")
    
    print("示例演示完成！")
    print("\n注意事项:")
    print("1. 实际使用前请安装所需的依赖库")
    print("2. 提供真实的文档文件进行测试")
    print("3. 根据具体需求调整配置参数")
    print("4. 查看模块README.md获取详细使用说明")

if __name__ == "__main__":
    main()
