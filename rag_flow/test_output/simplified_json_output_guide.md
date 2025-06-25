# 简化JSON输出格式说明

## 概述

基于您的反馈，我们已经简化了JSON输出格式，移除了过度设计的静态信息，只保留与本次实际测试相关的动态信息。

## 简化后的metadata字段

### 🎯 只包含实际测试信息

#### 1. quality_assessment - 本次使用的质量评估策略
```json
"quality_assessment": {
  "strategy_name": "basic",           // 实际使用的策略名称
  "enabled": true,                    // 是否启用质量评估
  "config": {                         // 该策略的具体配置参数
    "length_weight": 0.6,
    "completeness_weight": 0.4,
    "min_length": 100,
    "max_length": 2000,
    "optimal_length": 1000
  },
  "preset": "basic",                  // 使用的预设名称
  "score_calculation": {              // 实际的评分计算方式
    "method": "weighted_average",
    "length_weight": 0.6,
    "completeness_weight": 0.4,
    "formula": "length_score * 0.6 + completeness_score * 0.4"
  }
}
```

#### 2. chunking_config - 本次测试的分块配置
```json
"chunking_config": {
  "chunk_size": 1000,                 // 实际使用的分块大小
  "chunk_overlap": 200,               // 实际使用的重叠大小
  "min_chunk_size": 100,              // 最小分块大小
  "max_chunk_size": 2000,             // 最大分块大小
  "preserve_context": true,           // 是否保留上下文
  "enable_quality_assessment": true,  // 是否启用质量评估
  "quality_strategy": "basic"         // 使用的质量策略
}
```

#### 3. validation_info - 本次validation的实际结果
```json
"validation_info": {
  "method": "average_non_null_scores",     // 使用的计算方法
  "total_chunks_evaluated": 5,            // 评估的分块总数
  "chunks_with_scores": 5,                // 有质量评分的分块数
  "avg_calculation": "sum(non_null_scores) / count(non_null_scores)"  // 平均值计算方式
}
```

## 不同策略的对比

### 启用质量检测 (basic策略)
```json
"quality_assessment": {
  "strategy_name": "basic",
  "enabled": true,
  "score_calculation": {
    "method": "weighted_average",
    "length_weight": 0.6,
    "completeness_weight": 0.4,
    "formula": "length_score * 0.6 + completeness_score * 0.4"
  }
},
"validation_info": {
  "chunks_with_scores": 5,
  "avg_calculation": "sum(non_null_scores) / count(non_null_scores)"
}
```

### 禁用质量检测 (disabled策略)
```json
"quality_assessment": {
  "strategy_name": "disabled",
  "enabled": true,
  "config": {
    "description": "禁用质量检查，所有分块都返回满分"
  },
  "preset": "disabled"
  // 注意：没有score_calculation字段，因为不进行评分计算
},
"validation_info": {
  "chunks_with_scores": 0,
  "avg_calculation": "no_scores_available"
}
```

## 简化的价值

### ✅ 移除的静态内容
- 所有策略的完整说明文档
- 固定的评分解释标准
- 通用的参数描述说明
- 测试环境信息
- 固化的检测逻辑说明

### ✅ 保留的动态信息
- 本次实际使用的策略名称和配置
- 实际的评分计算公式和权重
- 当前测试的具体配置参数
- 本次validation的实际结果统计

### 🎯 核心优势

1. **相关性强**: 所有信息都与本次测试直接相关
2. **信息精准**: 反映实际使用的配置和策略
3. **输出简洁**: 避免了冗余的静态文档内容
4. **动态变化**: 根据不同的测试配置产生不同的输出

## 使用示例

### 快速了解本次测试配置
```bash
# 查看使用的质量评估策略
jq '.metadata.quality_assessment.strategy_name' simplified_output.json

# 查看评分计算公式
jq '.metadata.quality_assessment.score_calculation.formula' simplified_output.json

# 查看分块配置
jq '.metadata.chunking_config' simplified_output.json
```

### 对比不同配置的输出
```bash
# 生成不同配置的JSON输出
python test_chunking_presets.py -i doc.md --preset standard --output-format json > standard.json
python test_chunking_presets.py -i doc.md --preset standard --disable-quality-check --output-format json > disabled.json

# 对比质量评估配置
diff <(jq '.metadata.quality_assessment' standard.json) <(jq '.metadata.quality_assessment' disabled.json)
```

## 总结

简化后的JSON输出格式：
- ✅ 只包含与本次测试相关的动态信息
- ✅ 避免了过度设计的静态文档内容
- ✅ 保持了必要的透明度和可解释性
- ✅ 输出简洁且信息精准

这种设计更符合实际使用需求，避免了信息冗余，同时保持了对测试结果的完整描述。

---

**文档版本**: v2.0 (简化版)  
**创建时间**: 2025-06-25  
**适用版本**: test_chunking_presets.py v2.1.0+
