#!/bin/bash

# Docling文档处理器部署脚本
# 用于生产环境部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查部署依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查Python版本
    python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
    if [[ $(echo "$python_version >= 3.9" | bc -l) -eq 0 ]]; then
        log_warning "建议使用Python 3.9或更高版本，当前版本: $python_version"
    fi
    
    log_success "依赖检查完成"
}

# 环境检查
check_environment() {
    log_info "检查部署环境..."
    
    # 检查内存
    total_mem=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [ "$total_mem" -lt 4096 ]; then
        log_warning "建议至少4GB内存，当前: ${total_mem}MB"
    fi
    
    # 检查磁盘空间
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 10 ]; then
        log_warning "建议至少10GB可用磁盘空间，当前: ${available_space}GB"
    fi
    
    # 检查GPU（可选）
    if command -v nvidia-smi &> /dev/null; then
        log_info "检测到NVIDIA GPU，可启用GPU加速"
        export ENABLE_GPU=true
    else
        log_info "未检测到GPU，将使用CPU模式"
        export ENABLE_GPU=false
    fi
    
    log_success "环境检查完成"
}

# 准备配置文件
prepare_config() {
    log_info "准备配置文件..."
    
    # 创建必要的目录
    mkdir -p ./input ./output ./logs ./models
    
    # 复制配置文件模板
    if [ ! -f "./config/docling_config.yaml" ]; then
        log_info "创建默认配置文件..."
        cp "../config/docling_config.yaml" "./config/"
    fi
    
    # 设置权限
    chmod 755 ./input ./output ./logs ./models
    
    log_success "配置文件准备完成"
}

# 构建Docker镜像
build_image() {
    log_info "构建Docker镜像..."
    
    # 构建镜像
    docker-compose -f deploy/docker/docker-compose.yml build --no-cache
    
    if [ $? -eq 0 ]; then
        log_success "Docker镜像构建成功"
    else
        log_error "Docker镜像构建失败"
        exit 1
    fi
}

# 下载模型
download_models() {
    log_info "下载Docling预训练模型..."
    
    # 创建临时容器下载模型
    docker run --rm \
        -v docling_models:/app/models \
        -e DOCLING_ARTIFACTS_PATH=/app/models \
        docling-document-processor:latest \
        python -c "
from docling.document_converter import DocumentConverter
import subprocess
import sys

try:
    # 下载模型
    subprocess.run(['docling-tools', 'models', 'download'], check=True)
    print('Models downloaded successfully')
except subprocess.CalledProcessError as e:
    print(f'Model download failed: {e}')
    print('Models will be downloaded on first use')
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"
    
    log_success "模型下载完成"
}

# 启动服务
start_services() {
    log_info "启动Docling服务..."
    
    # 启动服务
    docker-compose -f deploy/docker/docker-compose.yml up -d
    
    if [ $? -eq 0 ]; then
        log_success "服务启动成功"
        
        # 等待服务就绪
        log_info "等待服务就绪..."
        sleep 30
        
        # 检查服务状态
        if docker-compose -f deploy/docker/docker-compose.yml ps | grep -q "Up"; then
            log_success "所有服务运行正常"
        else
            log_error "部分服务启动失败"
            docker-compose -f deploy/docker/docker-compose.yml logs
            exit 1
        fi
    else
        log_error "服务启动失败"
        exit 1
    fi
}

# 运行健康检查
health_check() {
    log_info "运行健康检查..."
    
    # 检查容器状态
    container_status=$(docker inspect --format='{{.State.Health.Status}}' docling-document-processor 2>/dev/null || echo "unknown")
    
    case $container_status in
        "healthy")
            log_success "服务健康检查通过"
            ;;
        "unhealthy")
            log_error "服务健康检查失败"
            docker logs docling-document-processor --tail 50
            exit 1
            ;;
        "starting")
            log_info "服务正在启动中，请稍候..."
            sleep 10
            health_check
            ;;
        *)
            log_warning "无法获取健康状态，请手动检查"
            ;;
    esac
}

# 显示部署信息
show_deployment_info() {
    log_success "部署完成！"
    echo
    echo "=== 部署信息 ==="
    echo "服务状态: $(docker-compose -f deploy/docker/docker-compose.yml ps --services --filter status=running | wc -l) 个服务运行中"
    echo "Web端口: http://localhost:8000 (如果启用)"
    echo "监控端口: http://localhost:9090 (Prometheus)"
    echo "Redis端口: localhost:6379"
    echo
    echo "=== 常用命令 ==="
    echo "查看日志: docker-compose -f deploy/docker/docker-compose.yml logs -f"
    echo "停止服务: docker-compose -f deploy/docker/docker-compose.yml down"
    echo "重启服务: docker-compose -f deploy/docker/docker-compose.yml restart"
    echo "查看状态: docker-compose -f deploy/docker/docker-compose.yml ps"
    echo
    echo "=== 配置文件 ==="
    echo "主配置: ./config/docling_config.yaml"
    echo "输入目录: ./input"
    echo "输出目录: ./output"
    echo "日志目录: ./logs"
    echo
}

# 主函数
main() {
    echo "Docling文档处理器部署脚本"
    echo "================================"
    
    # 解析命令行参数
    SKIP_BUILD=false
    SKIP_MODELS=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-models)
                SKIP_MODELS=true
                shift
                ;;
            --help|-h)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --skip-build   跳过Docker镜像构建"
                echo "  --skip-models  跳过模型下载"
                echo "  --help, -h     显示帮助信息"
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                exit 1
                ;;
        esac
    done
    
    # 执行部署步骤
    check_dependencies
    check_environment
    prepare_config
    
    if [ "$SKIP_BUILD" = false ]; then
        build_image
    else
        log_info "跳过镜像构建"
    fi
    
    start_services
    
    if [ "$SKIP_MODELS" = false ]; then
        download_models
    else
        log_info "跳过模型下载"
    fi
    
    health_check
    show_deployment_info
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 运行主函数
main "$@"
