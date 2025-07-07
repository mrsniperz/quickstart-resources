# 依赖分析报告

## 概述

本报告基于对 `src/core/` 目录下所有Python核心代码文件的全面分析，识别并更新了项目的第三方库依赖。

## 分析范围

### 扫描的目录和文件
- `src/core/__init__.py` - 核心模块入口
- `src/core/milvus/` - Milvus向量数据库服务模块
  - `collection_manager.py` - Collection管理服务
  - `search_service.py` - 检索服务
  - `metadata_service.py` - 元数据关联服务
  - `data_service.py` - 数据操作服务
- `src/core/document_processor/` - 文档处理模块
  - `parsers/` - 文档解析器（PDF、Word、Excel、PowerPoint、Docling）
  - `chunking/` - 智能分块引擎
  - `extractors/` - 内容提取器
  - `utils/` - 工具类
  - `api/` - API接口
  - `cli/` - 命令行工具
  - 各种示例和测试文件

## 依赖变更摘要

### 🆕 新增依赖
1. **docling>=2.0.0,<3.0.0** - 统一文档处理库
   - **用途**: 提供统一的多格式文档解析能力
   - **支持格式**: PDF、Word、HTML、Excel、CSV、Markdown、图片等
   - **选择理由**: 现代化的文档处理解决方案，支持高级功能如OCR、表格识别、图像描述等
   - **Python要求**: >=3.9

### ✅ 启用依赖
1. **pytesseract>=0.3.10,<1.0.0** - OCR文本识别
   - **状态变更**: 从注释状态启用
   - **用途**: 图像中的文本识别，支持扫描文档处理
   - **选择理由**: 代码中已有使用，应该启用以支持完整功能

### 🔄 版本策略优化
- **版本范围**: 为所有依赖添加了上限版本，避免破坏性更新
- **兼容性**: 确保版本范围兼容，避免依赖冲突
- **稳定性**: 核心依赖使用较严格的版本控制

### 📝 文档和注释改进
- 为每个依赖添加了用途说明
- 按功能模块重新分组依赖
- 添加了Python版本要求说明

## 详细依赖分析

### 核心框架依赖
| 依赖库 | 版本要求 | 用途 | 在core模块中的使用 |
|--------|----------|------|-------------------|
| fastapi | >=0.104.0,<1.0.0 | Web API框架 | 间接使用（项目架构需要） |
| pydantic | >=2.5.0,<3.0.0 | 数据验证 | 间接使用（数据模型定义） |
| uvicorn | >=0.24.0,<1.0.0 | ASGI服务器 | 间接使用（服务部署） |

### 向量数据库依赖
| 依赖库 | 版本要求 | 用途 | 在core模块中的使用 |
|--------|----------|------|-------------------|
| pymilvus | >=2.3.0,<3.0.0 | Milvus客户端 | 直接使用（milvus模块） |

### 文档处理依赖
| 依赖库 | 版本要求 | 用途 | 在core模块中的使用 |
|--------|----------|------|-------------------|
| docling | >=2.0.0,<3.0.0 | 统一文档处理 | 直接使用（docling_parser.py） |
| pymupdf | >=1.23.0,<2.0.0 | PDF处理 | 直接使用（pdf_parser.py） |
| python-docx | >=1.1.0,<2.0.0 | Word处理 | 直接使用（word_parser.py） |
| openpyxl | >=3.1.0,<4.0.0 | Excel处理 | 直接使用（excel_parser.py） |
| python-pptx | >=0.6.23,<1.0.0 | PowerPoint处理 | 直接使用（powerpoint_parser.py） |
| Pillow | >=10.0.0,<11.0.0 | 图像处理 | 直接使用（图像提取和处理） |
| pytesseract | >=0.3.10,<1.0.0 | OCR识别 | 直接使用（文本识别功能） |

### 数据处理依赖
| 依赖库 | 版本要求 | 用途 | 在core模块中的使用 |
|--------|----------|------|-------------------|
| pandas | >=2.1.0,<3.0.0 | 数据处理 | 直接使用（表格数据处理） |
| numpy | >=1.24.0,<2.0.0 | 数值计算 | 间接使用（pandas依赖） |

### 机器学习依赖
| 依赖库 | 版本要求 | 用途 | 在core模块中的使用 |
|--------|----------|------|-------------------|
| transformers | >=4.35.0,<5.0.0 | 深度学习模型 | 直接使用（高级文档处理） |
| torch | >=2.1.0,<3.0.0 | PyTorch框架 | 直接使用（模型推理） |
| sentence-transformers | >=2.2.0,<3.0.0 | 向量化模型 | 间接使用（向量生成） |

## 兼容性说明

### Python版本要求
- **最低版本**: Python 3.9
- **推荐版本**: Python 3.10+
- **原因**: docling库要求Python>=3.9

### 依赖冲突检查
- ✅ 所有依赖版本范围经过兼容性验证
- ✅ 没有发现版本冲突
- ✅ 核心依赖使用稳定版本

### 可选依赖说明
- **pytesseract**: 需要系统安装Tesseract OCR引擎
- **torch**: 建议使用GPU版本以获得更好性能
- **transformers**: 首次使用时会下载预训练模型

## 安装建议

### 基础安装
```bash
# 安装所有依赖
pip install -r requirements.txt

# 验证核心功能
python -c "from src.core import get_system_status; print(get_system_status())"
```

### 系统依赖
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim

# macOS
brew install tesseract tesseract-lang

# Windows
# 下载并安装 Tesseract OCR
```

### GPU支持（可选）
```bash
# 安装GPU版本的PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 维护建议

1. **定期更新**: 建议每季度检查依赖更新
2. **安全扫描**: 使用 `pip-audit` 检查安全漏洞
3. **版本锁定**: 生产环境建议使用 `pip freeze` 锁定具体版本
4. **测试验证**: 更新依赖后运行完整测试套件

## 总结

本次依赖分析和更新主要解决了以下问题：
1. 添加了缺失的核心依赖 `docling`
2. 启用了被注释的 `pytesseract` 依赖
3. 优化了版本管理策略，增加了版本上限
4. 改进了依赖分类和文档说明
5. 确保了所有依赖的兼容性

更新后的 `requirements.txt` 文件更加完整、安全和易于维护。
