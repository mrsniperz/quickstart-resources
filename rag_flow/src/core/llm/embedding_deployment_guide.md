# Embedding模块服务器部署指南

## 部署概述

本指南将帮助您在服务器上部署embedding模块，支持智谱AI Embedding-3、BGE-M3和Qwen3-Embedding三种模型。

## 系统要求

### 硬件要求
- **CPU**: 4核心以上推荐
- **内存**: 8GB以上（本地模型需要4-6GB）
- **存储**: 20GB可用空间（用于模型缓存）
- **GPU**: 可选，NVIDIA GPU with CUDA支持（用于加速本地模型）

### 软件要求
- **操作系统**: Linux (Ubuntu 18.04+, CentOS 7+) 或 macOS
- **Python**: 3.8 - 3.11
- **网络**: 稳定的互联网连接（用于模型下载和API调用）

## 快速部署

### 1. 环境准备

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# 或
sudo yum update -y  # CentOS/RHEL

# 安装Python和pip（如果未安装）
sudo apt install python3 python3-pip python3-venv -y  # Ubuntu/Debian
# 或
sudo yum install python3 python3-pip -y  # CentOS/RHEL
```

### 2. 创建虚拟环境

```bash
# 进入项目目录
cd /path/to/your/rag_flow

# 创建虚拟环境
python3 -m venv embedding_env

# 激活虚拟环境
source embedding_env/bin/activate
```

### 3. 安装依赖

```bash
# 基础依赖
pip install --upgrade pip
pip install numpy requests pathlib

# 智谱AI支持
pip install zhipuai

# 本地模型支持
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
# 如果有GPU，使用CUDA版本：
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

pip install transformers sentence-transformers
pip install accelerate  # 可选，用于加速
```

### 4. 配置环境变量

```bash
# 创建环境配置文件
cat > embedding_env.sh << 'EOF'
#!/bin/bash
# Embedding模块环境配置

# 智谱AI API密钥（必需，如果使用智谱AI模型）
export ZHIPU_API_KEY="your_zhipu_api_key_here"

# 模型缓存目录（可选，默认为~/.cache/embedding_models）
export EMBEDDING_CACHE_DIR="/opt/embedding_models"

# 日志级别（可选，默认为INFO）
export LOG_LEVEL="INFO"

# GPU设备（可选，默认自动检测）
export CUDA_VISIBLE_DEVICES="0"

echo "Embedding环境变量已加载"
EOF

# 设置执行权限
chmod +x embedding_env.sh

# 加载环境变量
source embedding_env.sh
```

### 5. 验证安装

```bash
# 进入项目目录并激活环境
cd /path/to/your/rag_flow
source embedding_env/bin/activate
source embedding_env.sh

# 运行简单测试
python3 -c "
from src.core.llm.embedding_client import embedding_client
print('可用模型:', embedding_client.list_available_models())
print('Embedding模块安装成功！')
"
```

## 详细配置

### 1. 智谱AI API配置

```bash
# 获取智谱AI API密钥
# 1. 访问 https://open.bigmodel.cn/
# 2. 注册并获取API密钥
# 3. 设置环境变量
export ZHIPU_API_KEY="your_actual_api_key"

# 验证API密钥
python3 -c "
from src.core.llm.embedding_client import embedding_client
success = embedding_client.initialize_model('embedding-3')
print('智谱AI配置:', '成功' if success else '失败')
"
```

### 2. 本地模型预下载

```bash
# 创建模型下载脚本
cat > download_models.py << 'EOF'
#!/usr/bin/env python3
"""预下载embedding模型脚本"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.llm.embedding_client import embedding_client

def download_model(model_name):
    print(f"开始下载模型: {model_name}")
    try:
        success = embedding_client.initialize_model(model_name)
        if success:
            print(f"✅ 模型 {model_name} 下载并初始化成功")
            return True
        else:
            print(f"❌ 模型 {model_name} 初始化失败")
            return False
    except Exception as e:
        print(f"❌ 模型 {model_name} 下载失败: {e}")
        return False

if __name__ == "__main__":
    models_to_download = ["bge-m3", "qwen3-embedding-0.6b"]
    
    for model in models_to_download:
        download_model(model)
        print("-" * 50)
    
    print("模型下载完成！")
EOF

# 运行下载脚本
python3 download_models.py
```

### 3. 系统服务配置（可选）

```bash
# 创建systemd服务文件
sudo cat > /etc/systemd/system/embedding-service.service << 'EOF'
[Unit]
Description=Embedding Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/your/rag_flow
Environment=ZHIPU_API_KEY=your_api_key
Environment=PYTHONPATH=/path/to/your/rag_flow
ExecStart=/path/to/your/rag_flow/embedding_env/bin/python -m src.core.llm.embedding_client
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable embedding-service
sudo systemctl start embedding-service

# 检查服务状态
sudo systemctl status embedding-service
```

## 性能优化

### 1. GPU加速配置

```bash
# 检查GPU可用性
python3 -c "
import torch
print('CUDA可用:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('GPU数量:', torch.cuda.device_count())
    print('GPU名称:', torch.cuda.get_device_name(0))
"

# 安装CUDA版本的PyTorch（如果有GPU）
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 2. 内存优化

```bash
# 创建内存优化配置
cat > memory_config.py << 'EOF'
import os
import torch

# 设置PyTorch内存管理
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    torch.cuda.set_per_process_memory_fraction(0.8)  # 限制GPU内存使用

# 设置环境变量
os.environ['TOKENIZERS_PARALLELISM'] = 'false'  # 避免tokenizer并行警告
os.environ['OMP_NUM_THREADS'] = '4'  # 限制OpenMP线程数
EOF
```

### 3. 缓存配置

```bash
# 创建专用缓存目录
sudo mkdir -p /opt/embedding_models
sudo chown $USER:$USER /opt/embedding_models

# 设置缓存环境变量
echo 'export EMBEDDING_CACHE_DIR="/opt/embedding_models"' >> ~/.bashrc
source ~/.bashrc
```

## 监控和维护

### 1. 日志配置

```bash
# 创建日志目录
mkdir -p /var/log/embedding

# 配置日志轮转
sudo cat > /etc/logrotate.d/embedding << 'EOF'
/var/log/embedding/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 your_username your_username
}
EOF
```

### 2. 健康检查脚本

```bash
cat > health_check.py << 'EOF'
#!/usr/bin/env python3
"""Embedding服务健康检查"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.llm.embedding_client import embedding_client

def health_check():
    try:
        # 检查模型可用性
        models = embedding_client.list_available_models()
        print(f"✅ 可用模型: {models}")
        
        # 测试智谱AI（如果配置了API密钥）
        if os.environ.get('ZHIPU_API_KEY'):
            try:
                embedding_client.initialize_model('embedding-3')
                test_embedding = embedding_client.embed_text("健康检查", 'embedding-3')
                print(f"✅ 智谱AI API正常，维度: {len(test_embedding)}")
            except Exception as e:
                print(f"❌ 智谱AI API异常: {e}")
        
        # 测试本地模型
        for model in ['bge-m3', 'qwen3-embedding-0.6b']:
            try:
                if embedding_client.initialize_model(model):
                    test_embedding = embedding_client.embed_text("健康检查", model)
                    print(f"✅ {model}正常，维度: {len(test_embedding)}")
                else:
                    print(f"❌ {model}初始化失败")
            except Exception as e:
                print(f"❌ {model}异常: {e}")
        
        return True
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

if __name__ == "__main__":
    success = health_check()
    sys.exit(0 if success else 1)
EOF

chmod +x health_check.py
```

### 3. 定期维护

```bash
# 创建维护脚本
cat > maintenance.sh << 'EOF'
#!/bin/bash
# Embedding服务维护脚本

echo "开始维护任务..."

# 清理缓存
echo "清理临时缓存..."
find /tmp -name "*embedding*" -type f -mtime +7 -delete

# 检查磁盘空间
echo "检查磁盘空间..."
df -h /opt/embedding_models

# 更新依赖（谨慎使用）
# pip install --upgrade zhipuai transformers sentence-transformers

# 运行健康检查
echo "运行健康检查..."
python3 health_check.py

echo "维护任务完成"
EOF

chmod +x maintenance.sh

# 添加到crontab（每周执行一次）
(crontab -l 2>/dev/null; echo "0 2 * * 0 /path/to/your/rag_flow/maintenance.sh >> /var/log/embedding/maintenance.log 2>&1") | crontab -
```

## 故障排除

### 常见问题解决

1. **模型下载失败**
```bash
# 检查网络连接
curl -I https://huggingface.co

# 手动下载模型
git lfs install
git clone https://huggingface.co/BAAI/bge-m3 /opt/embedding_models/BAAI_bge-m3
```

2. **内存不足**
```bash
# 检查内存使用
free -h
# 增加swap空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

3. **权限问题**
```bash
# 修复文件权限
sudo chown -R $USER:$USER /opt/embedding_models
chmod -R 755 /opt/embedding_models
```

## 安全建议

1. **API密钥安全**
   - 使用环境变量存储API密钥
   - 定期轮换API密钥
   - 限制API密钥权限

2. **网络安全**
   - 配置防火墙规则
   - 使用HTTPS进行API调用
   - 限制外部访问

3. **文件权限**
   - 设置适当的文件权限
   - 使用专用用户运行服务
   - 定期检查文件完整性

## 部署检查清单

- [ ] 系统要求满足
- [ ] Python环境配置完成
- [ ] 依赖包安装完成
- [ ] 环境变量设置正确
- [ ] 智谱AI API密钥配置（如需要）
- [ ] 本地模型下载完成
- [ ] 健康检查通过
- [ ] 日志配置完成
- [ ] 监控脚本部署
- [ ] 安全配置检查

完成以上步骤后，您的embedding模块就可以在服务器上正常运行了！
