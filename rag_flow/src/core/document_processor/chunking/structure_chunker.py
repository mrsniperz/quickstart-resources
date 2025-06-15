"""
模块名称: structure_chunker
功能描述: 结构分块器，基于文档结构和格式进行分块处理
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .chunking_engine import ChunkingStrategy, TextChunk, ChunkMetadata, ChunkType


class StructureChunker(ChunkingStrategy):
    """
    结构分块器
    
    基于文档结构和格式进行分块处理，包括：
    - 标题层级识别
    - 段落结构分析
    - 列表项目处理
    - 表格和图片分块
    - 页面边界处理
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化结构分块器
        
        Args:
            config (dict, optional): 配置参数
                - respect_page_breaks (bool): 是否尊重页面分隔，默认True
                - merge_short_sections (bool): 是否合并短节，默认True
                - min_section_size (int): 最小节大小，默认300
                - preserve_tables (bool): 是否保持表格完整，默认True
                - preserve_lists (bool): 是否保持列表完整，默认True
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 配置参数
        self.respect_page_breaks = self.config.get('respect_page_breaks', True)
        self.merge_short_sections = self.config.get('merge_short_sections', True)
        self.min_section_size = self.config.get('min_section_size', 300)
        self.preserve_tables = self.config.get('preserve_tables', True)
        self.preserve_lists = self.config.get('preserve_lists', True)
        
        # 结构模式定义
        self.structure_patterns = {
            'heading1': [
                r'^#\s+(.+)$',                    # Markdown H1
                r'^第[一二三四五六七八九十\d]+章\s*(.*)$',  # 中文章节
                r'^Chapter\s+\d+\s*(.*)$',        # 英文章节
                r'^[A-Z\s]+$'                     # 全大写标题
            ],
            'heading2': [
                r'^##\s+(.+)$',                   # Markdown H2
                r'^第[一二三四五六七八九十\d]+节\s*(.*)$',  # 中文节
                r'^Section\s+\d+\s*(.*)$',        # 英文节
                r'^\d+\.\s+(.+)$'                 # 数字编号
            ],
            'heading3': [
                r'^###\s+(.+)$',                  # Markdown H3
                r'^\d+\.\d+\s+(.+)$',            # 二级数字编号
                r'^[A-Z]\.\s+(.+)$'               # 字母编号
            ],
            'list_item': [
                r'^\s*[-*+]\s+(.+)$',            # 无序列表
                r'^\s*\d+\.\s+(.+)$',            # 有序列表
                r'^\s*[a-z]\)\s+(.+)$',          # 字母列表
                r'^\s*[①②③④⑤⑥⑦⑧⑨⑩]\s*(.+)$'      # 中文数字列表
            ],
            'table_marker': [
                r'表\s*\d+',                      # 中文表格标记
                r'Table\s+\d+',                   # 英文表格标记
                r'\|.*\|',                        # Markdown表格
            ],
            'figure_marker': [
                r'图\s*\d+',                      # 中文图片标记
                r'Figure\s+\d+',                  # 英文图片标记
                r'Fig\.\s*\d+'                    # 简写图片标记
            ],
            'page_break': [
                r'=== 第\d+页 ===',               # 页面分隔标记
                r'--- Page \d+ ---',              # 英文页面分隔
                r'\f'                             # 换页符
            ]
        }
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "structure"
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        基于结构进行文本分块
        
        Args:
            text: 待分块的文本
            metadata: 文档元数据
            
        Returns:
            list: 分块结果列表
        """
        try:
            # 预处理文本
            processed_text = self._preprocess_text(text)
            
            # 分析文档结构
            structure_info = self._analyze_document_structure(processed_text)
            
            # 基于结构进行分块
            chunks = self._structure_based_chunking(processed_text, structure_info, metadata)
            
            # 后处理分块
            processed_chunks = self._post_process_chunks(chunks)
            
            return processed_chunks
            
        except Exception as e:
            self.logger.error(f"结构分块失败: {e}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """
        预处理文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 处理后的文本
        """
        try:
            # 标准化换行符
            text = re.sub(r'\r\n|\r', '\n', text)
            
            # 保留重要的空行（段落分隔）
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
            
            # 标准化空格，但保留行首空格（可能表示缩进）
            lines = text.split('\n')
            processed_lines = []
            
            for line in lines:
                # 保留行首空格，但标准化其他空格
                leading_spaces = len(line) - len(line.lstrip())
                content = re.sub(r'\s+', ' ', line.strip())
                if content:
                    processed_lines.append(' ' * leading_spaces + content)
                else:
                    processed_lines.append('')
            
            return '\n'.join(processed_lines)
            
        except Exception as e:
            self.logger.warning(f"文本预处理失败: {e}")
            return text
    
    def _analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """
        分析文档结构
        
        Args:
            text: 文本内容
            
        Returns:
            dict: 结构分析结果
        """
        try:
            structure_info = {
                'headings': [],
                'lists': [],
                'tables': [],
                'figures': [],
                'page_breaks': [],
                'paragraphs': []
            }
            
            lines = text.split('\n')
            current_list = None
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                
                # 检测标题
                heading_info = self._detect_heading(line_stripped, i)
                if heading_info:
                    structure_info['headings'].append(heading_info)
                    continue
                
                # 检测列表项
                list_info = self._detect_list_item(line_stripped, i)
                if list_info:
                    if current_list is None or current_list['end_line'] < i - 1:
                        # 开始新列表
                        current_list = {
                            'start_line': i,
                            'end_line': i,
                            'items': [list_info]
                        }
                        structure_info['lists'].append(current_list)
                    else:
                        # 继续当前列表
                        current_list['end_line'] = i
                        current_list['items'].append(list_info)
                    continue
                else:
                    current_list = None
                
                # 检测表格标记
                if self._detect_table_marker(line_stripped):
                    structure_info['tables'].append({
                        'line_number': i,
                        'marker': line_stripped
                    })
                    continue
                
                # 检测图片标记
                if self._detect_figure_marker(line_stripped):
                    structure_info['figures'].append({
                        'line_number': i,
                        'marker': line_stripped
                    })
                    continue
                
                # 检测页面分隔
                if self._detect_page_break(line_stripped):
                    structure_info['page_breaks'].append({
                        'line_number': i,
                        'marker': line_stripped
                    })
                    continue
                
                # 普通段落
                structure_info['paragraphs'].append({
                    'line_number': i,
                    'content': line_stripped,
                    'indent_level': len(line) - len(line.lstrip())
                })
            
            return structure_info
            
        except Exception as e:
            self.logger.error(f"文档结构分析失败: {e}")
            return {}
    
    def _detect_heading(self, line: str, line_number: int) -> Optional[Dict[str, Any]]:
        """
        检测标题
        
        Args:
            line: 文本行
            line_number: 行号
            
        Returns:
            dict: 标题信息，如果不是标题返回None
        """
        try:
            for level, patterns in enumerate(['heading1', 'heading2', 'heading3'], 1):
                for pattern in self.structure_patterns[patterns]:
                    match = re.match(pattern, line)
                    if match:
                        return {
                            'line_number': line_number,
                            'level': level,
                            'title': match.group(1) if match.groups() else line,
                            'full_text': line,
                            'pattern': pattern
                        }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"标题检测失败: {e}")
            return None
    
    def _detect_list_item(self, line: str, line_number: int) -> Optional[Dict[str, Any]]:
        """
        检测列表项
        
        Args:
            line: 文本行
            line_number: 行号
            
        Returns:
            dict: 列表项信息，如果不是列表项返回None
        """
        try:
            for pattern in self.structure_patterns['list_item']:
                match = re.match(pattern, line)
                if match:
                    return {
                        'line_number': line_number,
                        'content': match.group(1) if match.groups() else line,
                        'full_text': line,
                        'pattern': pattern
                    }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"列表项检测失败: {e}")
            return None
    
    def _detect_table_marker(self, line: str) -> bool:
        """检测表格标记"""
        try:
            for pattern in self.structure_patterns['table_marker']:
                if re.search(pattern, line):
                    return True
            return False
        except Exception:
            return False
    
    def _detect_figure_marker(self, line: str) -> bool:
        """检测图片标记"""
        try:
            for pattern in self.structure_patterns['figure_marker']:
                if re.search(pattern, line):
                    return True
            return False
        except Exception:
            return False
    
    def _detect_page_break(self, line: str) -> bool:
        """检测页面分隔"""
        try:
            for pattern in self.structure_patterns['page_break']:
                if re.search(pattern, line):
                    return True
            return False
        except Exception:
            return False
    
    def _structure_based_chunking(self, text: str, 
                                structure_info: Dict[str, Any], 
                                metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        基于结构进行分块
        
        Args:
            text: 文本内容
            structure_info: 结构信息
            metadata: 文档元数据
            
        Returns:
            list: 分块结果
        """
        try:
            chunks = []
            lines = text.split('\n')
            
            # 获取所有结构分割点
            split_points = self._get_split_points(structure_info)
            
            # 根据分割点创建分块
            for i, point in enumerate(split_points):
                start_line = point['line_number']
                end_line = split_points[i + 1]['line_number'] if i + 1 < len(split_points) else len(lines)
                
                # 提取分块内容
                chunk_lines = lines[start_line:end_line]
                chunk_content = '\n'.join(chunk_lines).strip()
                
                if chunk_content:
                    chunk = self._create_structure_chunk(
                        content=chunk_content,
                        structure_point=point,
                        metadata=metadata,
                        chunk_index=len(chunks)
                    )
                    chunks.append(chunk)
            
            # 如果没有找到结构分割点，按段落分块
            if not chunks:
                chunks = self._chunk_by_paragraphs(text, metadata)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"结构化分块失败: {e}")
            return []
    
    def _get_split_points(self, structure_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        获取结构分割点
        
        Args:
            structure_info: 结构信息
            
        Returns:
            list: 分割点列表
        """
        try:
            split_points = []
            
            # 添加标题作为分割点
            for heading in structure_info.get('headings', []):
                split_points.append({
                    'line_number': heading['line_number'],
                    'type': 'heading',
                    'level': heading['level'],
                    'title': heading['title'],
                    'data': heading
                })
            
            # 添加页面分隔作为分割点
            if self.respect_page_breaks:
                for page_break in structure_info.get('page_breaks', []):
                    split_points.append({
                        'line_number': page_break['line_number'],
                        'type': 'page_break',
                        'data': page_break
                    })
            
            # 添加表格和图片作为分割点
            if self.preserve_tables:
                for table in structure_info.get('tables', []):
                    split_points.append({
                        'line_number': table['line_number'],
                        'type': 'table',
                        'data': table
                    })
            
            # 按行号排序
            split_points.sort(key=lambda x: x['line_number'])
            
            # 如果没有分割点，添加文档开始作为分割点
            if not split_points:
                split_points.append({
                    'line_number': 0,
                    'type': 'document_start',
                    'data': {}
                })
            
            return split_points
            
        except Exception as e:
            self.logger.error(f"分割点获取失败: {e}")
            return [{'line_number': 0, 'type': 'document_start', 'data': {}}]
    
    def _create_structure_chunk(self, content: str, 
                              structure_point: Dict[str, Any], 
                              metadata: Dict[str, Any], 
                              chunk_index: int) -> TextChunk:
        """
        创建结构分块
        
        Args:
            content: 分块内容
            structure_point: 结构分割点
            metadata: 文档元数据
            chunk_index: 分块索引
            
        Returns:
            TextChunk: 分块对象
        """
        try:
            # 确定分块类型
            chunk_type = ChunkType.PARAGRAPH
            section_title = None
            
            if structure_point['type'] == 'heading':
                if structure_point.get('level') == 1:
                    chunk_type = ChunkType.CHAPTER
                else:
                    chunk_type = ChunkType.SECTION
                section_title = structure_point.get('title')
            elif structure_point['type'] == 'table':
                chunk_type = ChunkType.TABLE
            elif structure_point['type'] == 'page_break':
                chunk_type = ChunkType.PARAGRAPH
            
            # 创建分块元数据
            chunk_metadata = ChunkMetadata(
                chunk_id=f"structure_{chunk_index:04d}",
                chunk_type=chunk_type,
                source_document=metadata.get('file_path', ''),
                section_title=section_title,
                start_position=structure_point['line_number'],
                processing_timestamp=datetime.now().isoformat()
            )
            
            return TextChunk(
                content=content,
                metadata=chunk_metadata
            )
            
        except Exception as e:
            self.logger.error(f"结构分块创建失败: {e}")
            return TextChunk(
                content=content,
                metadata=ChunkMetadata(
                    chunk_id=f"structure_{chunk_index:04d}",
                    chunk_type=ChunkType.PARAGRAPH,
                    source_document=""
                )
            )
    
    def _chunk_by_paragraphs(self, text: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        按段落分块
        
        Args:
            text: 文本内容
            metadata: 文档元数据
            
        Returns:
            list: 分块结果
        """
        try:
            chunks = []
            paragraphs = re.split(r'\n\s*\n', text)
            
            for i, paragraph in enumerate(paragraphs):
                paragraph = paragraph.strip()
                if paragraph:
                    chunk = self._create_structure_chunk(
                        content=paragraph,
                        structure_point={'line_number': i, 'type': 'paragraph', 'data': {}},
                        metadata=metadata,
                        chunk_index=i
                    )
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"段落分块失败: {e}")
            return []
    
    def _post_process_chunks(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """
        后处理分块
        
        Args:
            chunks: 原始分块列表
            
        Returns:
            list: 处理后的分块列表
        """
        try:
            if not self.merge_short_sections:
                return chunks
            
            processed_chunks = []
            current_chunk = None
            
            for chunk in chunks:
                if current_chunk is None:
                    current_chunk = chunk
                    continue
                
                # 检查是否需要合并
                if (len(current_chunk.content) < self.min_section_size and 
                    chunk.metadata.chunk_type == ChunkType.PARAGRAPH):
                    
                    # 合并分块
                    current_chunk.content += '\n\n' + chunk.content
                    current_chunk.metadata.end_position = chunk.metadata.end_position
                else:
                    # 保存当前分块，开始新分块
                    processed_chunks.append(current_chunk)
                    current_chunk = chunk
            
            # 添加最后一个分块
            if current_chunk:
                processed_chunks.append(current_chunk)
            
            return processed_chunks
            
        except Exception as e:
            self.logger.error(f"分块后处理失败: {e}")
            return chunks
