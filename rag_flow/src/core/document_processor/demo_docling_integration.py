#!/usr/bin/env python3
"""
模块名称: demo_docling_integration
功能描述: Docling集成演示脚本，展示Docling解析器的功能和集成效果
创建日期: 2024-12-17
作者: Sniperz
版本: v1.0.0
"""

import tempfile
from pathlib import Path
import json

def create_demo_files():
    """创建演示文件"""
    demo_files = {}
    
    # 创建HTML文件
    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>航空维修手册 - 发动机检查</title>
</head>
<body>
    <h1>发动机检查程序</h1>
    
    <h2>1. 检查前准备</h2>
    <p>在进行发动机检查前，请确保以下条件：</p>
    <ul>
        <li>发动机已完全冷却</li>
        <li>燃油系统已关闭</li>
        <li>所有安全设备已就位</li>
    </ul>
    
    <h2>2. 检查项目</h2>
    <table border="1">
        <tr>
            <th>检查项目</th>
            <th>标准值</th>
            <th>检查方法</th>
        </tr>
        <tr>
            <td>机油压力</td>
            <td>25-35 PSI</td>
            <td>压力表读数</td>
        </tr>
        <tr>
            <td>温度</td>
            <td>180-220°F</td>
            <td>温度传感器</td>
        </tr>
        <tr>
            <td>振动</td>
            <td>&lt;0.5 IPS</td>
            <td>振动分析仪</td>
        </tr>
    </table>
    
    <h2>3. 故障排除</h2>
    <p>如发现异常，请参考故障代码表进行处理。</p>
</body>
</html>"""
    
    # 创建CSV文件
    csv_content = """故障代码,故障描述,严重程度,处理方法
E001,机油压力过低,高,立即停机检查
E002,温度过高,高,检查冷却系统
E003,振动异常,中,检查平衡
W001,燃油消耗异常,低,监控燃油系统
W002,噪音异常,低,检查消音器
I001,定期保养提醒,信息,按计划保养"""
    
    # 创建Markdown文件
    markdown_content = """# 航空维修知识库

## 概述

本知识库包含航空器维修的相关技术文档和操作指南。

## 主要内容

### 发动机维修

#### 日常检查
- 机油液位检查
- 冷却液检查
- 燃油系统检查

#### 定期维护
- 更换机油和滤清器
- 检查点火系统
- 清洁空气滤清器

### 故障诊断

#### 常见故障

1. **启动困难**
   - 检查电池电压
   - 检查启动马达
   - 检查燃油供应

2. **运行不稳**
   - 检查点火时机
   - 检查燃油喷射
   - 检查空气流量

#### 诊断工具

| 工具名称 | 用途 | 精度 |
|---------|------|------|
| 万用表 | 电气测量 | ±0.1% |
| 压力表 | 压力测量 | ±1% |
| 示波器 | 信号分析 | 高精度 |

### 安全规程

⚠️ **重要提醒**：所有维修操作必须严格遵守安全规程。

```bash
# 检查系统状态
system_check --all
maintenance_log --update
```

## 联系信息

如有疑问，请联系技术支持部门。
"""
    
    # 保存文件
    temp_dir = tempfile.mkdtemp()
    
    files = {
        'engine_manual.html': html_content,
        'fault_codes.csv': csv_content,
        'maintenance_guide.md': markdown_content
    }
    
    for filename, content in files.items():
        file_path = Path(temp_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        demo_files[filename] = str(file_path)
    
    return demo_files, temp_dir

def simulate_docling_parsing(file_path, file_type):
    """模拟Docling解析过程"""
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 模拟解析结果
    if file_type == 'html':
        # HTML解析结果
        markdown_output = """# 发动机检查程序

## 1. 检查前准备

在进行发动机检查前，请确保以下条件：

- 发动机已完全冷却
- 燃油系统已关闭
- 所有安全设备已就位

## 2. 检查项目

| 检查项目 | 标准值 | 检查方法 |
|---------|--------|----------|
| 机油压力 | 25-35 PSI | 压力表读数 |
| 温度 | 180-220°F | 温度传感器 |
| 振动 | <0.5 IPS | 振动分析仪 |

## 3. 故障排除

如发现异常，请参考故障代码表进行处理。"""
        
        structured_data = {
            'tables': [
                {
                    'type': 'table',
                    'data': [
                        ['检查项目', '标准值', '检查方法'],
                        ['机油压力', '25-35 PSI', '压力表读数'],
                        ['温度', '180-220°F', '温度传感器'],
                        ['振动', '<0.5 IPS', '振动分析仪']
                    ],
                    'rows': 4,
                    'columns': 3
                }
            ],
            'headings': [
                {'text': '发动机检查程序', 'level': 1},
                {'text': '1. 检查前准备', 'level': 2},
                {'text': '2. 检查项目', 'level': 2},
                {'text': '3. 故障排除', 'level': 2}
            ],
            'lists': [
                {
                    'type': 'list',
                    'items': ['发动机已完全冷却', '燃油系统已关闭', '所有安全设备已就位']
                }
            ]
        }
        
    elif file_type == 'csv':
        # CSV解析结果
        markdown_output = """# 故障代码表

| 故障代码 | 故障描述 | 严重程度 | 处理方法 |
|---------|----------|----------|----------|
| E001 | 机油压力过低 | 高 | 立即停机检查 |
| E002 | 温度过高 | 高 | 检查冷却系统 |
| E003 | 振动异常 | 中 | 检查平衡 |
| W001 | 燃油消耗异常 | 低 | 监控燃油系统 |
| W002 | 噪音异常 | 低 | 检查消音器 |
| I001 | 定期保养提醒 | 信息 | 按计划保养 |"""
        
        structured_data = {
            'tables': [
                {
                    'type': 'table',
                    'data': [
                        ['故障代码', '故障描述', '严重程度', '处理方法'],
                        ['E001', '机油压力过低', '高', '立即停机检查'],
                        ['E002', '温度过高', '高', '检查冷却系统'],
                        ['E003', '振动异常', '中', '检查平衡'],
                        ['W001', '燃油消耗异常', '低', '监控燃油系统'],
                        ['W002', '噪音异常', '低', '检查消音器'],
                        ['I001', '定期保养提醒', '信息', '按计划保养']
                    ],
                    'rows': 7,
                    'columns': 4
                }
            ]
        }
        
    elif file_type == 'md':
        # Markdown解析结果（保持原样）
        markdown_output = content
        
        structured_data = {
            'headings': [
                {'text': '航空维修知识库', 'level': 1},
                {'text': '概述', 'level': 2},
                {'text': '主要内容', 'level': 2},
                {'text': '发动机维修', 'level': 3},
                {'text': '故障诊断', 'level': 3},
                {'text': '安全规程', 'level': 3}
            ],
            'tables': [
                {
                    'type': 'table',
                    'data': [
                        ['工具名称', '用途', '精度'],
                        ['万用表', '电气测量', '±0.1%'],
                        ['压力表', '压力测量', '±1%'],
                        ['示波器', '信号分析', '高精度']
                    ],
                    'rows': 4,
                    'columns': 3
                }
            ],
            'code_blocks': [
                {
                    'type': 'code',
                    'language': 'bash',
                    'code': '# 检查系统状态\nsystem_check --all\nmaintenance_log --update'
                }
            ]
        }
    
    # 模拟元数据
    metadata = {
        'file_name': Path(file_path).name,
        'file_path': file_path,
        'file_extension': Path(file_path).suffix.lower(),
        'file_size': Path(file_path).stat().st_size,
        'parser_type': 'docling',
        'total_elements': len(structured_data.get('headings', [])) + len(structured_data.get('tables', [])) + len(structured_data.get('lists', [])),
        'text_elements': len(structured_data.get('headings', [])),
        'table_elements': len(structured_data.get('tables', [])),
        'list_elements': len(structured_data.get('lists', [])),
        'code_elements': len(structured_data.get('code_blocks', []))
    }
    
    return {
        'text_content': markdown_output,
        'metadata': metadata,
        'structured_data': structured_data,
        'original_format': Path(file_path).suffix.lower()
    }

def demonstrate_docling_features():
    """演示Docling功能"""
    print("Docling文档处理器集成演示")
    print("=" * 60)
    
    # 创建演示文件
    print("创建演示文件...")
    demo_files, temp_dir = create_demo_files()
    print(f"✓ 演示文件已创建在: {temp_dir}")
    
    # 演示解析不同格式的文件
    file_types = {
        'engine_manual.html': 'html',
        'fault_codes.csv': 'csv', 
        'maintenance_guide.md': 'md'
    }
    
    results = {}
    
    for filename, file_type in file_types.items():
        print(f"\n处理文件: {filename}")
        print("-" * 40)
        
        file_path = demo_files[filename]
        result = simulate_docling_parsing(file_path, file_type)
        results[filename] = result
        
        # 显示解析结果
        print(f"✓ 文件类型: {result['original_format']}")
        print(f"✓ 文本长度: {len(result['text_content'])} 字符")
        print(f"✓ 表格数量: {len(result['structured_data'].get('tables', []))}")
        print(f"✓ 标题数量: {len(result['structured_data'].get('headings', []))}")
        print(f"✓ 列表数量: {len(result['structured_data'].get('lists', []))}")
        print(f"✓ 代码块数量: {len(result['structured_data'].get('code_blocks', []))}")
        
        # 显示文本预览
        preview = result['text_content'][:200] + "..." if len(result['text_content']) > 200 else result['text_content']
        print(f"✓ 文本预览:\n{preview}")
    
    # 演示批量转换
    print(f"\n批量转换演示")
    print("-" * 40)
    
    output_dir = Path(temp_dir) / "markdown_output"
    output_dir.mkdir(exist_ok=True)
    
    for filename, result in results.items():
        # 保存为Markdown文件
        output_file = output_dir / f"{Path(filename).stem}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result['text_content'])
        print(f"✓ 已保存: {output_file}")
    
    # 演示统一文档处理器集成
    print(f"\n统一文档处理器集成演示")
    print("-" * 40)
    
    print("配置示例:")
    config_example = {
        'use_docling': True,
        'prefer_docling_for_common_formats': False,
        'docling_config': {
            'enable_ocr': True,
            'enable_table_structure': True,
            'enable_picture_description': False,
            'enable_formula_enrichment': True,
            'enable_code_enrichment': True,
            'generate_picture_images': True,
            'images_scale': 2
        }
    }
    
    print(json.dumps(config_example, indent=2, ensure_ascii=False))
    
    # 演示格式路由
    print(f"\n格式路由演示:")
    format_routing = {
        'test.html': 'Docling解析器 (HTML专用)',
        'test.csv': 'Docling解析器 (CSV专用)', 
        'test.md': 'Docling解析器 (Markdown专用)',
        'test.png': 'Docling解析器 (图片OCR)',
        'test.pdf': '传统PDF解析器 (可配置为Docling)',
        'test.docx': '传统Word解析器 (可配置为Docling)'
    }
    
    for file_format, parser_choice in format_routing.items():
        print(f"  {file_format} -> {parser_choice}")
    
    # 显示功能特性
    print(f"\nDocling解析器功能特性:")
    print("-" * 40)
    
    features = [
        "✓ 统一多格式文档处理 (PDF, Word, HTML, Excel, CSV, Markdown, 图片)",
        "✓ 智能OCR文本识别",
        "✓ 高精度表格结构识别", 
        "✓ 公式识别和LaTeX转换",
        "✓ 代码块识别和语言检测",
        "✓ 图片内容描述 (可选)",
        "✓ 统一Markdown输出格式",
        "✓ 完整的元数据提取",
        "✓ 批量处理支持",
        "✓ 错误处理和日志记录"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    # 清理演示文件
    print(f"\n清理演示文件...")
    import shutil
    shutil.rmtree(temp_dir)
    print("✓ 演示文件已清理")
    
    print(f"\n演示完成！")
    print("=" * 60)
    print("要在实际环境中使用Docling解析器，请确保:")
    print("1. Python版本 >= 3.9")
    print("2. 安装Docling库: pip install docling")
    print("3. 配置相应的解析选项")
    print("4. 根据需要下载预训练模型")

if __name__ == "__main__":
    demonstrate_docling_features()
