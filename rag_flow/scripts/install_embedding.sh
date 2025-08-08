#!/bin/bash
# Embedding模块安装脚本
# 用于在服务器上快速部署embedding模块

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python版本
check_python() {
    print_info "检查Python版本..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            print_success "Python版本: $PYTHON_VERSION (满足要求)"
            PYTHON_CMD="python3"
        else
            print_error "Python版本过低: $PYTHON_VERSION (需要3.8+)"
            exit 1
        fi
    else
        print_error "未找到Python3，请先安装Python 3.8+"
        exit 1
    fi
}

# 检查pip
check_pip() {
    print_info "检查pip..."
    
    if command -v pip3 &> /dev/null; then
        print_success "pip3已安装"
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        print_success "pip已安装"
        PIP_CMD="pip"
    else
        print_error "未找到pip，请先安装pip"
        exit 1
    fi
}

# 创建虚拟环境
create_venv() {
    print_info "创建虚拟环境..."
    
    VENV_DIR="embedding_env"
    
    if [ -d "$VENV_DIR" ]; then
        print_warning "虚拟环境已存在，跳过创建"
    else
        $PYTHON_CMD -m venv $VENV_DIR
        print_success "虚拟环境创建完成: $VENV_DIR"
    fi
    
    # 激活虚拟环境
    source $VENV_DIR/bin/activate
    print_success "虚拟环境已激活"
}

# 升级pip
upgrade_pip() {
    print_info "升级pip..."
    pip install --upgrade pip
    print_success "pip升级完成"
}

# 安装基础依赖
install_basic_deps() {
    print_info "安装基础依赖..."
    
    pip install numpy
    print_success "基础依赖安装完成"
}

# 安装智谱AI支持
install_zhipu_support() {
    print_info "安装智谱AI支持..."
    
    pip install zhipuai
    print_success "智谱AI支持安装完成"
}

# 检查GPU支持
check_gpu() {
    print_info "检查GPU支持..."
    
    if command -v nvidia-smi &> /dev/null; then
        GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1)
        print_success "检测到GPU: $GPU_INFO"
        return 0
    else
        print_warning "未检测到NVIDIA GPU，将使用CPU版本"
        return 1
    fi
}

# 安装PyTorch
install_pytorch() {
    print_info "安装PyTorch..."
    
    if check_gpu; then
        print_info "安装GPU版本PyTorch..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    else
        print_info "安装CPU版本PyTorch..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    fi
    
    print_success "PyTorch安装完成"
}

# 安装transformers相关
install_transformers() {
    print_info "安装transformers和sentence-transformers..."
    
    pip install transformers sentence-transformers
    pip install accelerate  # 可选加速库
    
    print_success "transformers相关库安装完成"
}

# 验证安装
verify_installation() {
    print_info "验证安装..."
    
    # 检查基础导入
    python3 -c "
import numpy as np
print('✅ numpy:', np.__version__)

try:
    import zhipuai
    print('✅ zhipuai: 已安装')
except ImportError:
    print('❌ zhipuai: 未安装')

try:
    import torch
    print('✅ torch:', torch.__version__)
    print('   CUDA可用:', torch.cuda.is_available())
    if torch.cuda.is_available():
        print('   GPU数量:', torch.cuda.device_count())
except ImportError:
    print('❌ torch: 未安装')

try:
    import transformers
    print('✅ transformers:', transformers.__version__)
except ImportError:
    print('❌ transformers: 未安装')

try:
    from sentence_transformers import SentenceTransformer
    print('✅ sentence-transformers: 已安装')
except ImportError:
    print('❌ sentence-transformers: 未安装')
"
    
    print_success "安装验证完成"
}

# 创建环境配置文件
create_env_config() {
    print_info "创建环境配置文件..."
    
    cat > embedding_env.sh << 'EOF'
#!/bin/bash
# Embedding模块环境配置

# 智谱AI API密钥（请替换为您的实际密钥）
export ZHIPU_API_KEY="your_zhipu_api_key_here"

# 模型缓存目录（可选，默认为~/.cache/embedding_models）
export EMBEDDING_CACHE_DIR="$HOME/.cache/embedding_models"

# 日志级别（可选，默认为INFO）
export LOG_LEVEL="INFO"

# GPU设备（可选，默认自动检测）
# export CUDA_VISIBLE_DEVICES="0"

echo "Embedding环境变量已加载"
EOF
    
    chmod +x embedding_env.sh
    print_success "环境配置文件创建完成: embedding_env.sh"
}

# 创建测试脚本
create_test_script() {
    print_info "创建测试脚本..."
    
    cat > test_embedding.py << 'EOF'
#!/usr/bin/env python3
"""Embedding模块快速测试脚本"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """测试导入"""
    try:
        from src.core.llm.embedding_client import embedding_client
        print("✅ embedding_client导入成功")
        return True
    except ImportError as e:
        print(f"❌ embedding_client导入失败: {e}")
        return False

def test_models():
    """测试模型列表"""
    try:
        from src.core.llm.embedding_client import embedding_client
        models = embedding_client.list_available_models()
        print(f"✅ 可用模型: {models}")
        return True
    except Exception as e:
        print(f"❌ 模型列表获取失败: {e}")
        return False

def test_zhipu_api():
    """测试智谱AI API"""
    api_key = os.environ.get('ZHIPU_API_KEY')
    if not api_key or api_key == 'your_zhipu_api_key_here':
        print("⚠️  未设置ZHIPU_API_KEY，跳过智谱AI测试")
        return True
    
    try:
        from src.core.llm.embedding_client import embedding_client
        success = embedding_client.initialize_model('embedding-3')
        if success:
            embedding = embedding_client.embed_text("测试文本", 'embedding-3')
            print(f"✅ 智谱AI测试成功，向量维度: {len(embedding)}")
            return True
        else:
            print("❌ 智谱AI初始化失败")
            return False
    except Exception as e:
        print(f"❌ 智谱AI测试失败: {e}")
        return False

def main():
    print("=== Embedding模块测试 ===")
    
    tests = [
        ("导入测试", test_import),
        ("模型列表", test_models),
        ("智谱AI API", test_zhipu_api),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        if test_func():
            passed += 1
    
    print(f"\n=== 测试结果: {passed}/{total} 通过 ===")
    
    if passed == total:
        print("🎉 所有测试通过！Embedding模块安装成功！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查安装")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
    
    chmod +x test_embedding.py
    print_success "测试脚本创建完成: test_embedding.py"
}

# 打印使用说明
print_usage() {
    print_info "安装完成！使用说明："
    echo ""
    echo "1. 激活虚拟环境："
    echo "   source embedding_env/bin/activate"
    echo ""
    echo "2. 加载环境变量："
    echo "   source embedding_env.sh"
    echo ""
    echo "3. 设置智谱AI API密钥（如需要）："
    echo "   export ZHIPU_API_KEY='your_actual_api_key'"
    echo ""
    echo "4. 运行测试："
    echo "   python3 test_embedding.py"
    echo ""
    echo "5. 在Python中使用："
    echo "   from src.core.llm.embedding_client import embedding_client"
    echo "   models = embedding_client.list_available_models()"
    echo ""
}

# 主函数
main() {
    print_info "开始安装Embedding模块..."
    echo ""
    
    # 检查系统环境
    check_python
    check_pip
    
    # 创建和激活虚拟环境
    create_venv
    
    # 安装依赖
    upgrade_pip
    install_basic_deps
    install_zhipu_support
    install_pytorch
    install_transformers
    
    # 验证安装
    verify_installation
    
    # 创建配置文件
    create_env_config
    create_test_script
    
    # 打印使用说明
    print_usage
    
    print_success "Embedding模块安装完成！"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
