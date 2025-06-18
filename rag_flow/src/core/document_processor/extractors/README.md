# 内容提取器模块 (extractors)

## 模块概述

内容提取器模块负责从解析后的文档中提取特定类型的内容和元数据。该模块提供专门的提取器来处理不同类型的内容，包括元数据、表格数据和图像信息，为后续的分块和检索提供结构化的数据支持。

## 设计目标

- **专业提取**: 针对不同内容类型提供专门的提取器
- **结构化输出**: 将非结构化内容转换为结构化数据
- **质量保证**: 确保提取内容的准确性和完整性
- **扩展性**: 支持新的内容类型和提取方法
- **性能优化**: 高效的提取算法和内存管理

## 模块结构

```
extractors/
├── __init__.py              # 模块初始化
├── README.md               # 模块文档（本文件）
├── metadata_extractor.py   # 元数据提取器
├── table_extractor.py      # 表格提取器
└── image_extractor.py      # 图像提取器
```

## 核心类和方法

### MetadataExtractor - 元数据提取器

**功能描述**: 从文档中提取各种元数据信息，包括文档属性、统计信息和结构信息。

**主要方法**:
- `extract_metadata(file_path, document_content=None)`: 提取文档元数据
- `extract_file_metadata(file_path)`: 提取文件系统元数据
- `extract_content_metadata(content)`: 提取内容统计元数据
- `extract_structure_metadata(document)`: 提取文档结构元数据

**提取的元数据类型**:
```python
{
    'file_info': {
        'file_name': str,           # 文件名
        'file_path': str,           # 文件路径
        'file_size': int,           # 文件大小
        'file_extension': str,      # 文件扩展名
        'creation_time': datetime,  # 创建时间
        'modification_time': datetime, # 修改时间
    },
    'document_info': {
        'title': str,               # 文档标题
        'author': str,              # 作者
        'subject': str,             # 主题
        'keywords': list,           # 关键词
        'language': str,            # 语言
        'page_count': int,          # 页数
    },
    'content_stats': {
        'character_count': int,     # 字符数
        'word_count': int,          # 词数
        'paragraph_count': int,     # 段落数
        'sentence_count': int,      # 句子数
        'line_count': int,          # 行数
    },
    'structure_info': {
        'has_toc': bool,           # 是否有目录
        'heading_levels': int,      # 标题层级数
        'table_count': int,         # 表格数量
        'image_count': int,         # 图像数量
        'list_count': int,          # 列表数量
    }
}
```

### TableExtractor - 表格提取器

**功能描述**: 专门提取和处理文档中的表格数据，支持多种表格格式和复杂表格结构。

**主要方法**:
- `extract_tables(document)`: 提取所有表格
- `extract_table_data(table_element)`: 提取单个表格数据
- `detect_table_structure(table)`: 检测表格结构
- `convert_to_dataframe(table_data)`: 转换为DataFrame格式

**支持的表格类型**:
- 简单表格（行列结构清晰）
- 复杂表格（合并单元格、嵌套表格）
- 数据表格（数值数据为主）
- 文本表格（文本内容为主）

**表格数据格式**:
```python
{
    'table_id': str,            # 表格ID
    'caption': str,             # 表格标题
    'headers': list,            # 表头
    'data': list,               # 表格数据（二维列表）
    'structure': {
        'rows': int,            # 行数
        'columns': int,         # 列数
        'merged_cells': list,   # 合并单元格信息
    },
    'metadata': {
        'position': dict,       # 位置信息
        'page_number': int,     # 页码
        'table_type': str,      # 表格类型
    }
}
```

### ImageExtractor - 图像提取器

**功能描述**: 提取文档中的图像信息，支持图像元数据提取和可选的OCR文本识别。

**主要方法**:
- `extract_images(document)`: 提取所有图像
- `extract_image_metadata(image)`: 提取图像元数据
- `perform_ocr(image)`: 执行OCR文本识别
- `detect_image_type(image)`: 检测图像类型

**支持的图像类型**:
- 嵌入图像（PDF、Word中的图片）
- 图表和图形
- 截图和扫描图像
- 技术图纸和示意图

**图像数据格式**:
```python
{
    'image_id': str,            # 图像ID
    'caption': str,             # 图像标题
    'description': str,         # 图像描述
    'image_data': bytes,        # 图像二进制数据
    'format': str,              # 图像格式
    'dimensions': {
        'width': int,           # 宽度
        'height': int,          # 高度
    },
    'metadata': {
        'position': dict,       # 位置信息
        'page_number': int,     # 页码
        'image_type': str,      # 图像类型
        'file_size': int,       # 文件大小
    },
    'ocr_text': str,           # OCR识别的文本（可选）
}
```

## 使用示例

### 元数据提取

```python
from rag_flow.src.core.document_processor.extractors import MetadataExtractor

# 初始化元数据提取器
extractor = MetadataExtractor()

# 提取文档元数据
metadata = extractor.extract_metadata("document.pdf")

print("文档信息:")
print(f"  标题: {metadata['document_info']['title']}")
print(f"  作者: {metadata['document_info']['author']}")
print(f"  页数: {metadata['document_info']['page_count']}")

print("内容统计:")
print(f"  字符数: {metadata['content_stats']['character_count']}")
print(f"  词数: {metadata['content_stats']['word_count']}")
print(f"  段落数: {metadata['content_stats']['paragraph_count']}")
```

### 表格提取

```python
from rag_flow.src.core.document_processor.extractors import TableExtractor

# 初始化表格提取器
extractor = TableExtractor()

# 从解析结果中提取表格
tables = extractor.extract_tables(parsed_document)

for i, table in enumerate(tables):
    print(f"表格 {i+1}:")
    print(f"  标题: {table['caption']}")
    print(f"  大小: {table['structure']['rows']}行 x {table['structure']['columns']}列")
    
    # 转换为DataFrame
    df = extractor.convert_to_dataframe(table)
    print(df.head())
```

### 图像提取

```python
from rag_flow.src.core.document_processor.extractors import ImageExtractor

# 初始化图像提取器
config = {
    'enable_ocr': True,
    'ocr_language': 'chi_sim+eng',
    'extract_metadata': True
}
extractor = ImageExtractor(config)

# 提取图像
images = extractor.extract_images(parsed_document)

for i, image in enumerate(images):
    print(f"图像 {i+1}:")
    print(f"  标题: {image['caption']}")
    print(f"  格式: {image['format']}")
    print(f"  尺寸: {image['dimensions']['width']}x{image['dimensions']['height']}")
    
    if image['ocr_text']:
        print(f"  OCR文本: {image['ocr_text'][:100]}...")
```

## 配置参数

### MetadataExtractor 配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `extract_file_info` | bool | True | 是否提取文件信息 |
| `extract_document_info` | bool | True | 是否提取文档信息 |
| `extract_content_stats` | bool | True | 是否提取内容统计 |
| `extract_structure_info` | bool | True | 是否提取结构信息 |
| `language_detection` | bool | False | 是否进行语言检测 |

### TableExtractor 配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `detect_merged_cells` | bool | True | 是否检测合并单元格 |
| `preserve_formatting` | bool | False | 是否保持格式 |
| `min_table_size` | tuple | (2, 2) | 最小表格大小 |
| `max_table_size` | tuple | (100, 50) | 最大表格大小 |
| `auto_header_detection` | bool | True | 是否自动检测表头 |

### ImageExtractor 配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_ocr` | bool | False | 是否启用OCR |
| `ocr_language` | str | 'eng' | OCR语言设置 |
| `min_image_size` | tuple | (50, 50) | 最小图像尺寸 |
| `extract_metadata` | bool | True | 是否提取图像元数据 |
| `save_images` | bool | False | 是否保存图像文件 |
| `image_output_dir` | str | None | 图像输出目录 |

## 独立测试指南

### 测试环境准备

```bash
# 安装测试依赖
pip install pytest pytest-cov pillow pytesseract

# 安装OCR引擎（可选）
# Ubuntu/Debian: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract
# Windows: 下载并安装 Tesseract OCR
```

### 单元测试

```python
# test_extractors.py
import pytest
from extractors.metadata_extractor import MetadataExtractor
from extractors.table_extractor import TableExtractor
from extractors.image_extractor import ImageExtractor

def test_metadata_extractor():
    """测试元数据提取器"""
    extractor = MetadataExtractor()
    
    # 测试文件元数据提取
    metadata = extractor.extract_file_metadata("test_document.pdf")
    assert 'file_name' in metadata
    assert 'file_size' in metadata
    
    # 测试内容元数据提取
    content = "这是一个测试文档。包含多个句子。"
    content_meta = extractor.extract_content_metadata(content)
    assert content_meta['character_count'] > 0
    assert content_meta['word_count'] > 0

def test_table_extractor():
    """测试表格提取器"""
    extractor = TableExtractor()
    
    # 模拟表格数据
    mock_table = {
        'headers': ['列1', '列2', '列3'],
        'data': [
            ['数据1', '数据2', '数据3'],
            ['数据4', '数据5', '数据6']
        ]
    }
    
    # 测试DataFrame转换
    df = extractor.convert_to_dataframe(mock_table)
    assert len(df) == 2
    assert len(df.columns) == 3

def test_image_extractor():
    """测试图像提取器"""
    config = {'enable_ocr': False}
    extractor = ImageExtractor(config)
    
    # 测试图像类型检测
    image_type = extractor.detect_image_type("test_image.png")
    assert image_type in ['photo', 'diagram', 'chart', 'text']

# 运行测试
pytest test_extractors.py -v
```

### 集成测试

```python
def test_full_extraction_pipeline():
    """测试完整提取流程"""
    from parsers.pdf_parser import PDFParser
    
    # 解析文档
    parser = PDFParser()
    parse_result = parser.parse("test_document.pdf")
    
    # 提取元数据
    metadata_extractor = MetadataExtractor()
    metadata = metadata_extractor.extract_metadata("test_document.pdf")
    
    # 提取表格
    table_extractor = TableExtractor()
    tables = table_extractor.extract_tables(parse_result)
    
    # 提取图像
    image_extractor = ImageExtractor({'enable_ocr': True})
    images = image_extractor.extract_images(parse_result)
    
    # 验证结果
    assert metadata is not None
    assert isinstance(tables, list)
    assert isinstance(images, list)
```

### 性能测试

```python
import time

def test_extraction_performance():
    """测试提取性能"""
    extractor = MetadataExtractor()
    
    start_time = time.time()
    metadata = extractor.extract_metadata("large_document.pdf")
    end_time = time.time()
    
    processing_time = end_time - start_time
    print(f"元数据提取时间: {processing_time:.2f}秒")
    
    assert processing_time < 5  # 应在5秒内完成
```

## 与其他模块的接口

### 输入接口

**来源**: `parsers` 模块的解析结果
**数据格式**: 各种解析器的输出结果（PDFParseResult、WordParseResult等）

### 输出接口

**目标**: 合并到 `UnifiedParseResult` 中
**数据格式**: 结构化的元数据、表格数据和图像信息

## 扩展和自定义

### 添加新的提取器

```python
from extractors.base_extractor import BaseExtractor

class CustomExtractor(BaseExtractor):
    def __init__(self, config=None):
        super().__init__(config)
    
    def extract(self, document):
        # 实现自定义提取逻辑
        extracted_data = {}
        # ... 提取处理
        return extracted_data
```

### 自定义OCR引擎

```python
class CustomOCREngine:
    def recognize_text(self, image):
        # 实现自定义OCR逻辑
        return recognized_text

# 在ImageExtractor中使用
config = {
    'ocr_engine': CustomOCREngine(),
    'enable_ocr': True
}
extractor = ImageExtractor(config)
```

## 最佳实践

1. **选择合适的配置**: 根据文档类型和需求选择合适的提取配置
2. **性能优化**: 对于大文档，考虑并行处理或分批处理
3. **质量控制**: 验证提取结果的准确性和完整性
4. **错误处理**: 妥善处理提取过程中的异常情况
5. **资源管理**: 及时释放图像和临时文件资源

## 故障排除

### 常见问题

1. **OCR识别率低**: 检查图像质量、语言设置和OCR引擎配置
2. **表格结构错误**: 调整表格检测参数或使用手动标注
3. **元数据缺失**: 检查文档格式和解析器兼容性
4. **内存占用过高**: 优化图像处理或使用流式处理

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查提取结果
print(f"提取的表格数量: {len(tables)}")
print(f"提取的图像数量: {len(images)}")
print(f"元数据完整性: {len(metadata.keys())}")
```
