---
trigger: model_decision
description: 当需要通过需求文档转换为UI时使用
globs: 
---
# 需求文档转UI设计生成规则

## 目的
本规则用于根据用户指定的需求文档，生成对应的UI设计并输出为单个HTML文件。

## 步骤
1. 读取用户指定的需求文档文件
2. 分析需求文档中的功能需求和用户流程
3. 根据需求生成适合的UI设计
4. 将设计转换为单个HTML文件并输出到output目录

## UI设计生成指南

### 基本原则
- 界面应简洁清晰，符合现代设计趋势
- 优先考虑用户体验和易用性
- 布局应响应式，适配不同设备
- 遵循需求文档中描述的用户流程
- 色彩方案应符合产品定位和目标用户群体

### 输出HTML要求
- 单文件HTML，包含所有必要的CSS和JS
- 不依赖外部资源（除非特别指定）
- 注释清晰，代码结构合理
- 实现需求文档中描述的核心功能
- 提供基本交互效果展示

### 设计元素
- 导航结构
- 布局框架
- 色彩方案
- 字体选择
- 按钮和表单样式
- 图标和视觉元素

## 模板结构
生成的HTML应包含以下基本结构：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[项目名称] UI设计</title>
    <style>
        /* 此处包含所有CSS样式 */
    </style>
</head>
<body>
    <!-- 页面结构 -->
    <header>
        <!-- 导航栏 -->
    </header>
    
    <main>
        <!-- 主要内容区域 -->
    </main>
    
    <footer>
        <!-- 页脚 -->
    </footer>
    
    <script>
        // 此处包含所有JavaScript代码
    </script>
</body>
</html>