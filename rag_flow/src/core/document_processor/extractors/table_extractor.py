"""
模块名称: table_extractor
功能描述: 表格提取器，提供表格数据的提取、解析、格式化和质量控制功能
创建日期: 2024-01-15
作者: Sniperz
版本: v1.0.0
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import re
from dataclasses import dataclass


@dataclass
class TableCell:
    """表格单元格数据类"""
    value: str
    row: int
    column: int
    is_header: bool = False
    is_merged: bool = False
    data_type: str = "text"  # text, number, date, formula


@dataclass
class TableStructure:
    """表格结构数据类"""
    rows: int
    columns: int
    has_header: bool
    header_row: Optional[List[str]] = None
    data_rows: List[List[str]] = None
    cells: List[TableCell] = None


@dataclass
class ProcessedTable:
    """处理后的表格数据类"""
    original_data: List[List[str]]
    structure: TableStructure
    metadata: Dict[str, Any]
    quality_score: float
    formatted_text: str


class TableExtractor:
    """
    表格提取器
    
    提供表格数据的提取、解析、格式化和质量控制功能，包括：
    - 表格结构分析
    - 数据类型识别
    - 表头检测
    - 数据清洗和格式化
    - 质量评估
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化表格提取器
        
        Args:
            config (dict, optional): 配置参数
                - auto_detect_header (bool): 自动检测表头，默认True
                - clean_empty_rows (bool): 清理空行，默认True
                - clean_empty_columns (bool): 清理空列，默认True
                - min_table_size (tuple): 最小表格尺寸(rows, cols)，默认(2, 2)
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 配置参数
        self.auto_detect_header = self.config.get('auto_detect_header', True)
        self.clean_empty_rows = self.config.get('clean_empty_rows', True)
        self.clean_empty_columns = self.config.get('clean_empty_columns', True)
        self.min_table_size = self.config.get('min_table_size', (2, 2))
    
    def process_table(self, table_data: List[List[str]], 
                     table_metadata: Optional[Dict[str, Any]] = None) -> ProcessedTable:
        """
        处理表格数据
        
        Args:
            table_data (list): 原始表格数据
            table_metadata (dict, optional): 表格元数据
            
        Returns:
            ProcessedTable: 处理后的表格对象
        """
        try:
            if not table_data:
                raise ValueError("表格数据为空")
            
            # 清洗表格数据
            cleaned_data = self._clean_table_data(table_data)
            
            # 验证表格尺寸
            if not self._validate_table_size(cleaned_data):
                raise ValueError(f"表格尺寸不符合最小要求: {self.min_table_size}")
            
            # 分析表格结构
            structure = self._analyze_table_structure(cleaned_data)
            
            # 生成表格元数据
            metadata = self._generate_table_metadata(cleaned_data, table_metadata or {})
            
            # 计算质量评分
            quality_score = self._calculate_quality_score(cleaned_data, structure)
            
            # 格式化为文本
            formatted_text = self._format_table_as_text(cleaned_data, structure)
            
            return ProcessedTable(
                original_data=table_data,
                structure=structure,
                metadata=metadata,
                quality_score=quality_score,
                formatted_text=formatted_text
            )
            
        except Exception as e:
            self.logger.error(f"表格处理失败: {e}")
            raise
    
    def _clean_table_data(self, table_data: List[List[str]]) -> List[List[str]]:
        """
        清洗表格数据
        
        Args:
            table_data: 原始表格数据
            
        Returns:
            list: 清洗后的表格数据
        """
        try:
            cleaned_data = []
            
            # 标准化行长度
            max_cols = max(len(row) for row in table_data) if table_data else 0
            
            for row in table_data:
                # 补齐行长度
                cleaned_row = row + [''] * (max_cols - len(row))
                
                # 清理单元格内容
                cleaned_row = [self._clean_cell_content(cell) for cell in cleaned_row]
                
                cleaned_data.append(cleaned_row)
            
            # 移除空行
            if self.clean_empty_rows:
                cleaned_data = [row for row in cleaned_data if any(cell.strip() for cell in row)]
            
            # 移除空列
            if self.clean_empty_columns:
                cleaned_data = self._remove_empty_columns(cleaned_data)
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"表格数据清洗失败: {e}")
            return table_data
    
    def _clean_cell_content(self, cell_content: str) -> str:
        """
        清理单元格内容
        
        Args:
            cell_content: 单元格内容
            
        Returns:
            str: 清理后的内容
        """
        try:
            if not isinstance(cell_content, str):
                cell_content = str(cell_content)
            
            # 移除多余的空白字符
            cleaned = re.sub(r'\s+', ' ', cell_content.strip())
            
            # 移除特殊字符（可选）
            # cleaned = re.sub(r'[^\w\s\-.,()%$]', '', cleaned)
            
            return cleaned
            
        except Exception as e:
            self.logger.warning(f"单元格内容清理失败: {e}")
            return str(cell_content)
    
    def _remove_empty_columns(self, table_data: List[List[str]]) -> List[List[str]]:
        """
        移除空列
        
        Args:
            table_data: 表格数据
            
        Returns:
            list: 移除空列后的表格数据
        """
        try:
            if not table_data:
                return table_data
            
            cols_to_keep = []
            max_cols = len(table_data[0])
            
            for col_idx in range(max_cols):
                # 检查该列是否有非空内容
                has_content = any(
                    col_idx < len(row) and row[col_idx].strip() 
                    for row in table_data
                )
                if has_content:
                    cols_to_keep.append(col_idx)
            
            # 重构表格数据
            cleaned_data = []
            for row in table_data:
                cleaned_row = [row[col_idx] if col_idx < len(row) else '' 
                             for col_idx in cols_to_keep]
                cleaned_data.append(cleaned_row)
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"空列移除失败: {e}")
            return table_data
    
    def _validate_table_size(self, table_data: List[List[str]]) -> bool:
        """
        验证表格尺寸
        
        Args:
            table_data: 表格数据
            
        Returns:
            bool: 是否符合最小尺寸要求
        """
        try:
            if not table_data:
                return False
            
            rows = len(table_data)
            cols = len(table_data[0]) if table_data else 0
            
            min_rows, min_cols = self.min_table_size
            
            return rows >= min_rows and cols >= min_cols
            
        except Exception as e:
            self.logger.error(f"表格尺寸验证失败: {e}")
            return False
    
    def _analyze_table_structure(self, table_data: List[List[str]]) -> TableStructure:
        """
        分析表格结构
        
        Args:
            table_data: 表格数据
            
        Returns:
            TableStructure: 表格结构对象
        """
        try:
            rows = len(table_data)
            columns = len(table_data[0]) if table_data else 0
            
            # 检测表头
            has_header = False
            header_row = None
            
            if self.auto_detect_header and rows > 1:
                has_header = self._detect_header_row(table_data)
                if has_header:
                    header_row = table_data[0]
            
            # 分离数据行
            data_rows = table_data[1:] if has_header else table_data
            
            # 创建单元格对象
            cells = []
            for row_idx, row in enumerate(table_data):
                for col_idx, cell_value in enumerate(row):
                    cell = TableCell(
                        value=cell_value,
                        row=row_idx,
                        column=col_idx,
                        is_header=(row_idx == 0 and has_header),
                        data_type=self._detect_data_type(cell_value)
                    )
                    cells.append(cell)
            
            return TableStructure(
                rows=rows,
                columns=columns,
                has_header=has_header,
                header_row=header_row,
                data_rows=data_rows,
                cells=cells
            )
            
        except Exception as e:
            self.logger.error(f"表格结构分析失败: {e}")
            return TableStructure(rows=0, columns=0, has_header=False)
    
    def _detect_header_row(self, table_data: List[List[str]]) -> bool:
        """
        检测是否存在表头行
        
        Args:
            table_data: 表格数据
            
        Returns:
            bool: 是否存在表头
        """
        try:
            if len(table_data) < 2:
                return False
            
            first_row = table_data[0]
            second_row = table_data[1]
            
            # 检查第一行是否主要包含文本，第二行是否包含更多数字
            first_row_text_ratio = sum(1 for cell in first_row 
                                     if self._detect_data_type(cell) == 'text') / len(first_row)
            
            second_row_number_ratio = sum(1 for cell in second_row 
                                        if self._detect_data_type(cell) in ['number', 'date']) / len(second_row)
            
            # 如果第一行文本比例高且第二行数字比例高，可能存在表头
            return first_row_text_ratio > 0.6 and second_row_number_ratio > 0.3
            
        except Exception as e:
            self.logger.warning(f"表头检测失败: {e}")
            return False
    
    def _detect_data_type(self, cell_value: str) -> str:
        """
        检测单元格数据类型
        
        Args:
            cell_value: 单元格值
            
        Returns:
            str: 数据类型
        """
        try:
            if not cell_value or not cell_value.strip():
                return 'empty'
            
            cell_value = cell_value.strip()
            
            # 检测数字
            if re.match(r'^-?\d+\.?\d*$', cell_value):
                return 'number'
            
            # 检测百分比
            if re.match(r'^-?\d+\.?\d*%$', cell_value):
                return 'percentage'
            
            # 检测日期
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',
                r'\d{2}/\d{2}/\d{4}',
                r'\d{2}-\d{2}-\d{4}'
            ]
            for pattern in date_patterns:
                if re.match(pattern, cell_value):
                    return 'date'
            
            # 检测公式（Excel格式）
            if cell_value.startswith('='):
                return 'formula'
            
            return 'text'
            
        except Exception as e:
            self.logger.warning(f"数据类型检测失败: {e}")
            return 'text'
    
    def _generate_table_metadata(self, table_data: List[List[str]], 
                                base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成表格元数据
        
        Args:
            table_data: 表格数据
            base_metadata: 基础元数据
            
        Returns:
            dict: 表格元数据
        """
        try:
            metadata = base_metadata.copy()
            
            # 基本统计
            metadata.update({
                'total_cells': len(table_data) * len(table_data[0]) if table_data else 0,
                'non_empty_cells': sum(1 for row in table_data for cell in row if cell.strip()),
                'data_types': self._analyze_data_types(table_data),
                'column_stats': self._analyze_columns(table_data)
            })
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"表格元数据生成失败: {e}")
            return base_metadata
    
    def _analyze_data_types(self, table_data: List[List[str]]) -> Dict[str, int]:
        """
        分析数据类型分布
        
        Args:
            table_data: 表格数据
            
        Returns:
            dict: 数据类型统计
        """
        try:
            type_counts = {}
            
            for row in table_data:
                for cell in row:
                    data_type = self._detect_data_type(cell)
                    type_counts[data_type] = type_counts.get(data_type, 0) + 1
            
            return type_counts
            
        except Exception as e:
            self.logger.error(f"数据类型分析失败: {e}")
            return {}
    
    def _analyze_columns(self, table_data: List[List[str]]) -> List[Dict[str, Any]]:
        """
        分析列统计信息
        
        Args:
            table_data: 表格数据
            
        Returns:
            list: 列统计信息
        """
        try:
            if not table_data:
                return []
            
            column_stats = []
            num_cols = len(table_data[0])
            
            for col_idx in range(num_cols):
                col_values = [row[col_idx] if col_idx < len(row) else '' 
                            for row in table_data]
                
                non_empty_values = [v for v in col_values if v.strip()]
                
                stats = {
                    'column_index': col_idx,
                    'total_values': len(col_values),
                    'non_empty_values': len(non_empty_values),
                    'empty_ratio': 1 - (len(non_empty_values) / len(col_values)) if col_values else 1,
                    'dominant_type': self._get_dominant_data_type(non_empty_values),
                    'unique_values': len(set(non_empty_values))
                }
                
                column_stats.append(stats)
            
            return column_stats
            
        except Exception as e:
            self.logger.error(f"列分析失败: {e}")
            return []
    
    def _get_dominant_data_type(self, values: List[str]) -> str:
        """
        获取主导数据类型
        
        Args:
            values: 值列表
            
        Returns:
            str: 主导数据类型
        """
        try:
            if not values:
                return 'empty'
            
            type_counts = {}
            for value in values:
                data_type = self._detect_data_type(value)
                type_counts[data_type] = type_counts.get(data_type, 0) + 1
            
            return max(type_counts, key=type_counts.get)
            
        except Exception as e:
            self.logger.warning(f"主导数据类型获取失败: {e}")
            return 'text'
    
    def _calculate_quality_score(self, table_data: List[List[str]], 
                               structure: TableStructure) -> float:
        """
        计算表格质量评分
        
        Args:
            table_data: 表格数据
            structure: 表格结构
            
        Returns:
            float: 质量评分（0-1）
        """
        try:
            score = 0.0
            
            # 完整性评分（30%）
            total_cells = structure.rows * structure.columns
            non_empty_cells = sum(1 for row in table_data for cell in row if cell.strip())
            completeness_score = non_empty_cells / total_cells if total_cells > 0 else 0
            score += completeness_score * 0.3
            
            # 结构性评分（25%）
            structure_score = 1.0 if structure.has_header else 0.5
            score += structure_score * 0.25
            
            # 一致性评分（25%）
            consistency_score = self._calculate_consistency_score(table_data)
            score += consistency_score * 0.25
            
            # 尺寸评分（20%）
            size_score = min(1.0, (structure.rows * structure.columns) / 100)
            score += size_score * 0.2
            
            return round(score, 3)
            
        except Exception as e:
            self.logger.error(f"质量评分计算失败: {e}")
            return 0.0
    
    def _calculate_consistency_score(self, table_data: List[List[str]]) -> float:
        """
        计算数据一致性评分
        
        Args:
            table_data: 表格数据
            
        Returns:
            float: 一致性评分
        """
        try:
            if not table_data or len(table_data) < 2:
                return 1.0
            
            column_consistency_scores = []
            num_cols = len(table_data[0])
            
            for col_idx in range(num_cols):
                col_values = [row[col_idx] if col_idx < len(row) else '' 
                            for row in table_data[1:]]  # 跳过表头
                
                non_empty_values = [v for v in col_values if v.strip()]
                
                if not non_empty_values:
                    column_consistency_scores.append(1.0)
                    continue
                
                # 计算该列的数据类型一致性
                type_counts = {}
                for value in non_empty_values:
                    data_type = self._detect_data_type(value)
                    type_counts[data_type] = type_counts.get(data_type, 0) + 1
                
                dominant_type_count = max(type_counts.values())
                consistency = dominant_type_count / len(non_empty_values)
                column_consistency_scores.append(consistency)
            
            return sum(column_consistency_scores) / len(column_consistency_scores) if column_consistency_scores else 1.0
            
        except Exception as e:
            self.logger.error(f"一致性评分计算失败: {e}")
            return 0.0
    
    def _format_table_as_text(self, table_data: List[List[str]], 
                            structure: TableStructure) -> str:
        """
        将表格格式化为文本
        
        Args:
            table_data: 表格数据
            structure: 表格结构
            
        Returns:
            str: 格式化的文本
        """
        try:
            if not table_data:
                return ""
            
            lines = []
            
            # 添加表头
            if structure.has_header and structure.header_row:
                header_line = " | ".join(structure.header_row)
                lines.append(header_line)
                lines.append("-" * len(header_line))
            
            # 添加数据行
            data_rows = structure.data_rows or table_data
            for row in data_rows:
                row_line = " | ".join(row)
                lines.append(row_line)
            
            return "\n".join(lines)
            
        except Exception as e:
            self.logger.error(f"表格文本格式化失败: {e}")
            return ""
