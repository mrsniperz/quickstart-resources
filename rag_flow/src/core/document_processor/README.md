# 文档预处理模块

## 概述

文档预处理模块是航空RAG系统的核心组件之一，提供多格式文档的解析、内容提取、智能分块等功能。该模块专门针对航空行业文档特点进行优化，支持维修手册、规章制度、技术标准、培训资料等多种文档类型的处理。

## 功能特性

### 🔧 多格式文档解析
- **PDF文档处理**: 基于PyMuPDF的高性能PDF解析，支持文本提取、表格识别、图像提取
- **Word文档处理**: 基于python-docx的Word文档解析，保持格式和结构
- **Excel文档处理**: 基于openpyxl的Excel数据提取，支持多工作表和表格
- **PowerPoint文档处理**: 基于python-pptx的演示文稿内容提取

### 📊 智能内容提取
- **文本内容提取**: 保持文档结构的文本提取
- **表格数据提取**: 智能表格识别和数据结构化
- **图像内容提取**: 图像信息提取和可选OCR文本识别
- **元数据提取**: 文档属性、创建信息、统计数据等

### 🎯 航空文档优化
- **维修手册分块**: 按章节和步骤进行智能分块
- **规章制度分块**: 按条款和规定进行结构化分块
- **技术标准分块**: 按标准项和规范进行分块
- **培训资料分块**: 按知识点和学习单元分块

## 模块结构

```
document_processor/
├── __init__.py                 # 模块初始化
├── README.md                   # 模块文档
├── parsers/                    # 文档解析器
│   ├── __init__.py
│   ├── pdf_parser.py          # PDF解析器
│   ├── word_parser.py         # Word解析器
│   ├── excel_parser.py        # Excel解析器
│   ├── powerpoint_parser.py   # PowerPoint解析器
│   └── document_processor.py  # 统一文档处理器
├── chunking/                   # 智能分块引擎
│   ├── __init__.py
│   ├── chunking_engine.py     # 分块引擎
│   ├── aviation_strategy.py   # 航空文档分块策略
│   ├── semantic_chunker.py    # 语义分块器
│   └── structure_chunker.py   # 结构分块器
├── extractors/                 # 内容提取器
│   ├── __init__.py
│   ├── metadata_extractor.py  # 元数据提取器
│   ├── table_extractor.py     # 表格提取器
│   └── image_extractor.py     # 图像提取器
└── validators/                 # 质量控制器
    ├── __init__.py
    ├── chunk_validator.py     # 分块验证器
    └── quality_controller.py  # 质量控制器
```

## 快速开始

### 基本使用

```python
from rag_flow.src.core.document_processor import DocumentProcessor

# 初始化文档处理器
processor = DocumentProcessor()

# 解析文档
result = processor.parse("path/to/document.pdf")

# 获取文本内容
text_content = result.text_content

# 获取结构化数据
tables = result.structured_data.get('tables', [])
images = result.structured_data.get('images', [])

# 获取元数据
metadata = result.metadata
```

### 配置选项

```python
config = {
    'pdf_config': {
        'extract_images': True,
        'extract_tables': True,
        'ocr_enabled': False
    },
    'word_config': {
        'preserve_formatting': True,
        'extract_tables': True
    },
    'excel_config': {
        'read_only': True,
        'max_rows': 10000
    },
    'powerpoint_config': {
        'extract_notes': True,
        'extract_shapes': True
    }
}

processor = DocumentProcessor(config)
```

### 批量处理

```python
# 批量处理多个文档
file_paths = [
    "manual1.pdf",
    "regulation.docx", 
    "data.xlsx",
    "training.pptx"
]

results = processor.parse_batch(file_paths)

for result in results:
    print(f"文档类型: {result.document_type.value}")
    print(f"文本长度: {len(result.text_content)}")
```

## API接口

### DocumentProcessor

主要的统一文档处理接口。

#### 方法

- `parse(file_path: str) -> UnifiedParseResult`: 解析单个文档
- `parse_batch(file_paths: List[str]) -> List[UnifiedParseResult]`: 批量解析文档
- `detect_document_type(file_path: str) -> DocumentType`: 检测文档类型
- `is_supported_format(file_path: str) -> bool`: 检查格式支持
- `extract_text_only(file_path: str) -> str`: 仅提取文本
- `extract_metadata_only(file_path: str) -> Dict`: 仅提取元数据

### 专用解析器

#### PDFParser

```python
from rag_flow.src.core.document_processor.parsers import PDFParser

parser = PDFParser({
    'extract_images': True,
    'extract_tables': True,
    'ocr_enabled': False
})

result = parser.parse("document.pdf")
```

#### WordParser

```python
from rag_flow.src.core.document_processor.parsers import WordParser

parser = WordParser({
    'preserve_formatting': True,
    'extract_tables': True
})

result = parser.parse("document.docx")
```

#### ExcelParser

```python
from rag_flow.src.core.document_processor.parsers import ExcelParser

parser = ExcelParser({
    'read_only': True,
    'data_only': True,
    'max_rows': 10000
})

result = parser.parse("document.xlsx")
```

#### PowerPointParser

```python
from rag_flow.src.core.document_processor.parsers import PowerPointParser

parser = PowerPointParser({
    'extract_notes': True,
    'extract_shapes': True
})

result = parser.parse("document.pptx")
```

## 数据结构

### UnifiedParseResult

统一解析结果对象：

```python
@dataclass
class UnifiedParseResult:
    document_type: DocumentType          # 文档类型
    text_content: str                    # 文本内容
    metadata: Dict[str, Any]             # 元数据
    structured_data: Dict[str, Any]      # 结构化数据
    structure_info: Dict[str, Any]       # 结构信息
    original_result: Union[...]          # 原始解析结果
```

### 结构化数据格式

不同文档类型的结构化数据：

```python
# PDF文档
structured_data = {
    'tables': [
        {
            'page_number': 1,
            'table_index': 0,
            'data': [['列1', '列2'], ['值1', '值2']],
            'bbox': (x, y, width, height),
            'rows': 2,
            'columns': 2
        }
    ],
    'images': [
        {
            'page_number': 1,
            'bbox': (x, y, width, height),
            'width': 800,
            'height': 600,
            'format': 'png',
            'image_data': b'...'
        }
    ],
    'page_count': 10
}

# Word文档
structured_data = {
    'tables': [...],
    'paragraphs': [
        {
            'index': 0,
            'text': '段落内容',
            'style': 'Heading 1',
            'runs': [...]
        }
    ]
}

# Excel文档
structured_data = {
    'worksheets': [
        {
            'name': 'Sheet1',
            'data': [['A1', 'B1'], ['A2', 'B2']],
            'rows': 2,
            'columns': 2
        }
    ],
    'tables': [...]
}

# PowerPoint文档
structured_data = {
    'slides': [
        {
            'slide_number': 1,
            'title': '幻灯片标题',
            'content': '幻灯片内容',
            'shapes': [...]
        }
    ],
    'notes': [
        {
            'slide_number': 1,
            'notes_text': '备注内容'
        }
    ]
}
```

## 配置参数

### 全局配置

```python
config = {
    'pdf_config': {...},      # PDF解析器配置
    'word_config': {...},     # Word解析器配置  
    'excel_config': {...},    # Excel解析器配置
    'powerpoint_config': {...} # PowerPoint解析器配置
}
```

### PDF配置

```python
pdf_config = {
    'extract_images': True,        # 是否提取图像
    'extract_tables': True,        # 是否提取表格
    'preserve_layout': True,       # 是否保持布局
    'ocr_enabled': False          # 是否启用OCR
}
```

### Word配置

```python
word_config = {
    'preserve_formatting': True,           # 是否保持格式
    'extract_tables': True,               # 是否提取表格
    'extract_headers_footers': False      # 是否提取页眉页脚
}
```

### Excel配置

```python
excel_config = {
    'read_only': True,            # 只读模式
    'data_only': True,           # 只读取数据值
    'extract_formulas': False,   # 是否提取公式
    'max_rows': None,           # 最大读取行数
    'max_cols': None            # 最大读取列数
}
```

### PowerPoint配置

```python
powerpoint_config = {
    'extract_notes': True,                    # 是否提取备注
    'extract_shapes': True,                   # 是否提取形状信息
    'preserve_slide_structure': True          # 是否保持幻灯片结构
}
```

## 错误处理

模块提供完善的错误处理机制：

```python
try:
    result = processor.parse("document.pdf")
except FileNotFoundError:
    print("文件不存在")
except ValueError as e:
    print(f"文件格式不支持: {e}")
except Exception as e:
    print(f"解析失败: {e}")
```

## 性能优化

### 大文件处理

- Excel文档使用只读模式减少内存占用
- PDF文档支持页面级别的处理
- 支持批量处理优化

### 内存管理

- 自动释放文档对象
- 可配置的数据提取选项
- 流式处理支持

## 扩展开发

### 添加新的文档格式

1. 在`parsers/`目录下创建新的解析器
2. 实现标准的解析接口
3. 在`DocumentProcessor`中注册新格式
4. 更新配置和文档

### 自定义分块策略

1. 在`chunking/`目录下实现新策略
2. 继承基础分块接口
3. 配置策略参数
4. 集成到分块引擎

## 依赖库

### 必需依赖

- `pymupdf`: PDF文档处理
- `python-docx`: Word文档处理  
- `openpyxl`: Excel文档处理
- `python-pptx`: PowerPoint文档处理

### 可选依赖

- `PIL/Pillow`: 图像处理
- `pytesseract`: OCR文本识别
- `pandas`: 数据处理增强

## 注意事项

1. **文件格式支持**: 确保文档格式在支持列表中
2. **内存使用**: 大文件处理时注意内存占用
3. **编码问题**: 处理中文文档时注意编码设置
4. **依赖安装**: 确保所需的第三方库已正确安装
5. **权限问题**: 确保对文档文件有读取权限

## 更新日志

### v1.0.0 (2024-01-15)
- 初始版本发布
- 支持PDF、Word、Excel、PowerPoint文档解析
- 实现统一的文档处理接口
- 提供完整的元数据提取功能
- 支持表格和图像内容提取
