"""
模块名称: test_docling_parser
功能描述: Docling文档解析器单元测试
创建日期: 2024-12-17
作者: Sniperz
版本: v1.0.0
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from io import BytesIO
import tempfile
import os

# 导入被测试的模块
import sys
sys.path.append(str(Path(__file__).parent.parent))

from parsers.docling_parser import DoclingParser, DoclingParseResult, DOCLING_AVAILABLE


class TestDoclingParser(unittest.TestCase):
    """Docling解析器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_config = {
            'enable_ocr': True,
            'enable_table_structure': True,
            'enable_picture_description': False,
            'generate_picture_images': True,
            'images_scale': 2
        }
        
        # 创建临时测试文件
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = {}
        
        # 创建测试文件
        test_content = {
            'test.pdf': b'%PDF-1.4 fake pdf content',
            'test.docx': b'fake docx content',
            'test.html': b'<html><body>Test HTML</body></html>',
            'test.csv': b'name,age\nJohn,25\nJane,30',
            'test.md': b'# Test Markdown\n\nThis is a test.',
            'test.txt': b'Plain text content',
            'test.png': b'fake png content'
        }
        
        for filename, content in test_content.items():
            file_path = Path(self.temp_dir) / filename
            with open(file_path, 'wb') as f:
                f.write(content)
            self.test_files[filename] = str(file_path)
    
    def tearDown(self):
        """测试后清理"""
        # 清理临时文件
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @unittest.skipIf(not DOCLING_AVAILABLE, "Docling库未安装")
    def test_parser_initialization(self):
        """测试解析器初始化"""
        # 测试默认配置
        parser = DoclingParser()
        self.assertIsNotNone(parser)
        self.assertTrue(parser.enable_ocr)
        self.assertTrue(parser.enable_table_structure)
        
        # 测试自定义配置
        parser = DoclingParser(self.test_config)
        self.assertEqual(parser.enable_ocr, True)
        self.assertEqual(parser.enable_table_structure, True)
        self.assertEqual(parser.images_scale, 2)
    
    def test_parser_initialization_without_docling(self):
        """测试没有Docling库时的初始化"""
        with patch('parsers.docling_parser.DOCLING_AVAILABLE', False):
            with self.assertRaises(ImportError):
                DoclingParser()
    
    @unittest.skipIf(not DOCLING_AVAILABLE, "Docling库未安装")
    def test_supported_formats(self):
        """测试支持的格式"""
        parser = DoclingParser()
        supported_formats = parser.get_supported_formats()
        
        expected_formats = ['.pdf', '.docx', '.doc', '.html', '.htm', '.xlsx', '.xls',
                           '.csv', '.md', '.markdown', '.txt', '.png', '.jpg', '.jpeg',
                           '.gif', '.bmp', '.tiff', '.tif', '.pptx', '.ppt']
        
        for fmt in expected_formats:
            self.assertIn(fmt, supported_formats)
    
    @unittest.skipIf(not DOCLING_AVAILABLE, "Docling库未安装")
    def test_format_support_check(self):
        """测试格式支持检查"""
        parser = DoclingParser()
        
        # 支持的格式
        self.assertTrue(parser.is_format_supported('test.pdf'))
        self.assertTrue(parser.is_format_supported('test.html'))
        self.assertTrue(parser.is_format_supported('test.csv'))
        
        # 不支持的格式
        self.assertFalse(parser.is_format_supported('test.xyz'))
        self.assertFalse(parser.is_format_supported('test.unknown'))
    
    @unittest.skipIf(not DOCLING_AVAILABLE, "Docling库未安装")
    @patch('parsers.docling_parser.DocumentConverter')
    def test_parse_success(self, mock_converter_class):
        """测试成功解析"""
        # 模拟Docling转换器
        mock_converter = Mock()
        mock_converter_class.return_value = mock_converter
        
        # 模拟转换结果
        mock_conversion_result = Mock()
        mock_conversion_result.status.name = "SUCCESS"
        
        mock_document = Mock()
        mock_document.export_to_markdown.return_value = "# Test Document\n\nContent here."
        mock_document.meta = None
        mock_document.pages = []
        mock_document.iterate_items.return_value = []
        
        mock_conversion_result.document = mock_document
        mock_converter.convert.return_value = mock_conversion_result
        
        # 执行测试
        parser = DoclingParser(self.test_config)
        result = parser.parse(self.test_files['test.html'])
        
        # 验证结果
        self.assertIsInstance(result, DoclingParseResult)
        self.assertEqual(result.text_content, "# Test Document\n\nContent here.")
        self.assertEqual(result.original_format, '.html')
        self.assertIsNotNone(result.metadata)
        self.assertIsNotNone(result.structured_data)
    
    @unittest.skipIf(not DOCLING_AVAILABLE, "Docling库未安装")
    def test_parse_file_not_found(self):
        """测试文件不存在的情况"""
        parser = DoclingParser()
        
        with self.assertRaises(FileNotFoundError):
            parser.parse("nonexistent_file.pdf")
    
    @unittest.skipIf(not DOCLING_AVAILABLE, "Docling库未安装")
    def test_parse_unsupported_format(self):
        """测试不支持的格式"""
        parser = DoclingParser()
        
        # 创建不支持格式的文件
        unsupported_file = Path(self.temp_dir) / "test.xyz"
        with open(unsupported_file, 'w') as f:
            f.write("test content")
        
        with self.assertRaises(ValueError):
            parser.parse(str(unsupported_file))
    
    @unittest.skipIf(not DOCLING_AVAILABLE, "Docling库未安装")
    @patch('parsers.docling_parser.DocumentConverter')
    def test_parse_stream(self, mock_converter_class):
        """测试解析数据流"""
        # 模拟Docling转换器
        mock_converter = Mock()
        mock_converter_class.return_value = mock_converter
        
        # 模拟转换结果
        mock_conversion_result = Mock()
        mock_conversion_result.status.name = "SUCCESS"
        
        mock_document = Mock()
        mock_document.export_to_markdown.return_value = "# Stream Document\n\nContent."
        mock_document.meta = None
        mock_document.pages = []
        mock_document.iterate_items.return_value = []
        
        mock_conversion_result.document = mock_document
        mock_converter.convert.return_value = mock_conversion_result
        
        # 执行测试
        parser = DoclingParser()
        stream = BytesIO(b"test content")
        result = parser.parse_stream(stream, "test.html")
        
        # 验证结果
        self.assertIsInstance(result, DoclingParseResult)
        self.assertEqual(result.text_content, "# Stream Document\n\nContent.")
        self.assertEqual(result.original_format, '.html')
    
    @unittest.skipIf(not DOCLING_AVAILABLE, "Docling库未安装")
    @patch('parsers.docling_parser.DocumentConverter')
    def test_extract_text_only(self, mock_converter_class):
        """测试仅提取文本"""
        # 模拟设置
        mock_converter = Mock()
        mock_converter_class.return_value = mock_converter
        
        mock_conversion_result = Mock()
        mock_conversion_result.status.name = "SUCCESS"
        
        mock_document = Mock()
        mock_document.export_to_markdown.return_value = "Extracted text content"
        mock_document.meta = None
        mock_document.pages = []
        mock_document.iterate_items.return_value = []
        
        mock_conversion_result.document = mock_document
        mock_converter.convert.return_value = mock_conversion_result
        
        # 执行测试
        parser = DoclingParser()
        text = parser.extract_text_only(self.test_files['test.html'])
        
        # 验证结果
        self.assertEqual(text, "Extracted text content")
    
    @unittest.skipIf(not DOCLING_AVAILABLE, "Docling库未安装")
    @patch('parsers.docling_parser.DocumentConverter')
    def test_convert_to_markdown(self, mock_converter_class):
        """测试转换为Markdown"""
        # 模拟设置
        mock_converter = Mock()
        mock_converter_class.return_value = mock_converter
        
        mock_conversion_result = Mock()
        mock_conversion_result.status.name = "SUCCESS"
        
        mock_document = Mock()
        mock_document.export_to_markdown.return_value = "# Markdown Content\n\nConverted text."
        mock_document.meta = None
        mock_document.pages = []
        mock_document.iterate_items.return_value = []
        
        mock_conversion_result.document = mock_document
        mock_converter.convert.return_value = mock_conversion_result
        
        # 执行测试
        parser = DoclingParser()
        
        # 测试不保存文件
        markdown = parser.convert_to_markdown(self.test_files['test.html'])
        self.assertEqual(markdown, "# Markdown Content\n\nConverted text.")
        
        # 测试保存文件
        output_file = Path(self.temp_dir) / "output.md"
        markdown = parser.convert_to_markdown(self.test_files['test.html'], str(output_file))
        
        self.assertTrue(output_file.exists())
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        self.assertEqual(saved_content, "# Markdown Content\n\nConverted text.")
    
    def test_check_dependencies(self):
        """测试依赖检查"""
        dependencies = DoclingParser.check_dependencies()
        
        self.assertIn('docling', dependencies)
        self.assertIn('pandas', dependencies)
        self.assertIn('pillow', dependencies)
        
        self.assertIsInstance(dependencies['docling'], bool)
        self.assertIsInstance(dependencies['pandas'], bool)
        self.assertIsInstance(dependencies['pillow'], bool)
    
    @unittest.skipIf(not DOCLING_AVAILABLE, "Docling库未安装")
    @patch('parsers.docling_parser.DocumentConverter')
    def test_batch_convert(self, mock_converter_class):
        """测试批量转换"""
        # 模拟设置
        mock_converter = Mock()
        mock_converter_class.return_value = mock_converter
        
        mock_conversion_result = Mock()
        mock_conversion_result.status.name = "SUCCESS"
        
        mock_document = Mock()
        mock_document.export_to_markdown.return_value = "Batch converted content"
        mock_document.meta = None
        mock_document.pages = []
        mock_document.iterate_items.return_value = []
        
        mock_conversion_result.document = mock_document
        mock_converter.convert.return_value = mock_conversion_result
        
        # 执行测试
        parser = DoclingParser()
        
        test_files = [
            self.test_files['test.html'],
            self.test_files['test.csv']
        ]
        
        results = parser.batch_convert(test_files)
        
        # 验证结果
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIsInstance(result, DoclingParseResult)
            self.assertEqual(result.text_content, "Batch converted content")


class TestDoclingParserIntegration(unittest.TestCase):
    """Docling解析器集成测试"""
    
    @unittest.skipIf(not DOCLING_AVAILABLE, "Docling库未安装")
    def test_real_markdown_parsing(self):
        """测试真实的Markdown解析（如果Docling可用）"""
        # 创建真实的Markdown文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Test Document

This is a test markdown document.

## Section 1

Some content here.

### Subsection

- Item 1
- Item 2
- Item 3

## Section 2

More content.

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
| Value 3  | Value 4  |
""")
            temp_file = f.name
        
        try:
            parser = DoclingParser({'enable_ocr': False})  # 不需要OCR处理Markdown
            result = parser.parse(temp_file)
            
            # 基本验证
            self.assertIsInstance(result, DoclingParseResult)
            self.assertIn("Test Document", result.text_content)
            self.assertEqual(result.original_format, '.md')
            
            # 检查元数据
            self.assertIn('file_name', result.metadata)
            self.assertIn('parser_type', result.metadata)
            self.assertEqual(result.metadata['parser_type'], 'docling')
            
        finally:
            # 清理临时文件
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()
