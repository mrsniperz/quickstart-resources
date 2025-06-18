# RAG Flow 部署文档

## 部署概述

RAG Flow 支持多种部署方式，从单机开发环境到分布式生产环境。本文档详细介绍各种部署场景的配置和最佳实践。

## 环境要求

### 硬件要求

#### 最小配置（开发环境）
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 50GB 可用空间
- **网络**: 1Gbps

#### 推荐配置（生产环境）
- **CPU**: 16核心
- **内存**: 32GB RAM
- **存储**: 500GB SSD
- **网络**: 10Gbps
- **GPU**: NVIDIA GPU（可选，用于加速）

#### 大规模配置（企业环境）
- **CPU**: 32核心+
- **内存**: 128GB RAM+
- **存储**: 2TB+ NVMe SSD
- **网络**: 25Gbps+
- **GPU**: 多张 NVIDIA A100/V100

### 软件要求

#### 基础环境
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / macOS 12+
- **Python**: 3.8+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

#### 依赖服务
- **Milvus**: 2.4+
- **etcd**: 3.5+
- **MinIO**: RELEASE.2023-01-02+

## 部署方式

### 1. Docker Compose 部署（推荐）

#### 快速启动

```bash
# 克隆项目
git clone <repository-url>
cd rag_flow

# 启动服务
docker-compose up -d
```

#### docker-compose.yml 配置

```yaml
version: '3.8'

services:
  # RAG Flow 应用
  rag-flow:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MILVUS_URI=http://milvus:19530
      - MILVUS_TOKEN=root:Milvus
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - milvus
      - etcd
      - minio

  # Milvus 向量数据库
  milvus:
    image: milvusdb/milvus:v2.4.0
    ports:
      - "19530:19530"
      - "9091:9091"
    environment:
      - ETCD_ENDPOINTS=etcd:2379
      - MINIO_ADDRESS=minio:9000
    volumes:
      - milvus_data:/var/lib/milvus
    depends_on:
      - etcd
      - minio

  # etcd 元数据存储
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    ports:
      - "2379:2379"
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
    volumes:
      - etcd_data:/etcd

  # MinIO 对象存储
  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin
    volumes:
      - minio_data:/data
    command: minio server /data --console-address ":9001"

volumes:
  milvus_data:
  etcd_data:
  minio_data:
```

### 2. Kubernetes 部署

#### 命名空间创建

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: rag-flow
```

#### ConfigMap 配置

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: rag-flow-config
  namespace: rag-flow
data:
  config.yaml: |
    milvus:
      uri: "http://milvus-service:19530"
      token: "root:Milvus"
    
    document_processor:
      use_docling: true
      enable_ocr: true
      chunk_size: 1000
    
    logging:
      level: INFO
      file: "/app/logs/rag-flow.log"
```

#### Deployment 配置

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-flow
  namespace: rag-flow
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-flow
  template:
    metadata:
      labels:
        app: rag-flow
    spec:
      containers:
      - name: rag-flow
        image: rag-flow:latest
        ports:
        - containerPort: 8000
        env:
        - name: MILVUS_URI
          value: "http://milvus-service:19530"
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: data
          mountPath: /app/data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      volumes:
      - name: config
        configMap:
          name: rag-flow-config
      - name: data
        persistentVolumeClaim:
          claimName: rag-flow-data
```

#### Service 配置

```yaml
apiVersion: v1
kind: Service
metadata:
  name: rag-flow-service
  namespace: rag-flow
spec:
  selector:
    app: rag-flow
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. 单机部署

#### 系统准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 3.8+
sudo apt install python3.8 python3.8-pip python3.8-venv

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### 应用部署

```bash
# 创建虚拟环境
python3.8 -m venv rag-flow-env
source rag-flow-env/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动 Milvus
docker run -d --name milvus \
  -p 19530:19530 \
  -p 9091:9091 \
  -v milvus_data:/var/lib/milvus \
  milvusdb/milvus:v2.4.0

# 配置环境变量
export MILVUS_URI="http://localhost:19530"
export MILVUS_TOKEN="root:Milvus"

# 启动应用
python app.py
```

## 配置管理

### 环境变量配置

```bash
# Milvus 配置
export MILVUS_URI="http://localhost:19530"
export MILVUS_TOKEN="root:Milvus"

# 文档处理配置
export USE_DOCLING="true"
export ENABLE_OCR="true"
export CHUNK_SIZE="1000"

# 日志配置
export LOG_LEVEL="INFO"
export LOG_FILE="/app/logs/rag-flow.log"

# 性能配置
export MAX_WORKERS="4"
export BATCH_SIZE="100"
```

### 配置文件

#### config/production.yaml

```yaml
# 生产环境配置
milvus:
  uri: "http://milvus-cluster:19530"
  token: "${MILVUS_TOKEN}"
  connection_pool_size: 10
  timeout: 30

document_processor:
  use_docling: true
  enable_performance_monitoring: true
  docling_config:
    enable_ocr: true
    enable_table_structure: true
    enable_picture_description: true
    table_mode: "accurate"
  chunking_config:
    chunk_size: 1000
    chunk_overlap: 200
    default_strategy: "aviation"

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "/app/logs/rag-flow.log"
  max_size: "100MB"
  backup_count: 5

performance:
  max_workers: 8
  batch_size: 1000
  cache_size: 10000
  timeout: 60
```

## 数据库初始化

### Milvus 集合创建

```python
from rag_flow.src.core.milvus import MilvusCollectionManager

# 初始化管理器
manager = MilvusCollectionManager(
    uri="http://localhost:19530",
    token="root:Milvus"
)

# 创建航空文档集合
manager.create_aviation_collection("aviation_docs")

# 创建分区
manager.create_partition("aviation_docs", "technical_manuals")
manager.create_partition("aviation_docs", "regulations")
manager.create_partition("aviation_docs", "training_materials")

# 加载集合
manager.load_collection("aviation_docs")
```

### 初始化脚本

```bash
#!/bin/bash
# init_database.sh

echo "初始化 RAG Flow 数据库..."

# 等待 Milvus 启动
echo "等待 Milvus 服务启动..."
while ! nc -z localhost 19530; do
  sleep 1
done

# 运行初始化脚本
python scripts/init_collections.py

echo "数据库初始化完成"
```

## 监控和日志

### 日志配置

#### logrotate 配置

```bash
# /etc/logrotate.d/rag-flow
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 app app
    postrotate
        systemctl reload rag-flow
    endscript
}
```

### 监控指标

#### Prometheus 配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'rag-flow'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'milvus'
    static_configs:
      - targets: ['localhost:9091']
```

#### Grafana 仪表板

```json
{
  "dashboard": {
    "title": "RAG Flow 监控",
    "panels": [
      {
        "title": "文档处理速度",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(documents_processed_total[5m])"
          }
        ]
      },
      {
        "title": "检索响应时间",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, search_duration_seconds_bucket)"
          }
        ]
      }
    ]
  }
}
```

## 备份和恢复

### 数据备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# 备份 Milvus 数据
docker exec milvus tar czf - /var/lib/milvus > $BACKUP_DIR/milvus_data.tar.gz

# 备份配置文件
cp -r /app/config $BACKUP_DIR/

# 备份日志
cp -r /app/logs $BACKUP_DIR/

echo "备份完成: $BACKUP_DIR"
```

### 数据恢复

```bash
#!/bin/bash
# restore.sh

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
    echo "请指定备份目录"
    exit 1
fi

# 停止服务
docker-compose down

# 恢复 Milvus 数据
docker run --rm -v milvus_data:/var/lib/milvus -v $BACKUP_DIR:/backup alpine \
    tar xzf /backup/milvus_data.tar.gz -C /

# 恢复配置文件
cp -r $BACKUP_DIR/config /app/

# 启动服务
docker-compose up -d

echo "恢复完成"
```

## 性能调优

### 系统级优化

```bash
# 内核参数优化
echo 'vm.max_map_count=262144' >> /etc/sysctl.conf
echo 'fs.file-max=65536' >> /etc/sysctl.conf
sysctl -p

# 文件描述符限制
echo '* soft nofile 65536' >> /etc/security/limits.conf
echo '* hard nofile 65536' >> /etc/security/limits.conf
```

### 应用级优化

```python
# 性能配置
PERFORMANCE_CONFIG = {
    'milvus': {
        'connection_pool_size': 20,
        'search_timeout': 30,
        'insert_batch_size': 10000
    },
    'document_processor': {
        'max_workers': 8,
        'chunk_size': 5000,
        'enable_parallel': True
    },
    'cache': {
        'metadata_cache_size': 50000,
        'result_cache_ttl': 3600
    }
}
```

## 故障排除

### 常见问题

#### 1. Milvus 连接失败

```bash
# 检查 Milvus 状态
docker ps | grep milvus
docker logs milvus

# 检查网络连接
telnet localhost 19530
```

#### 2. 内存不足

```bash
# 检查内存使用
free -h
docker stats

# 调整配置
# 减少 batch_size 和 max_workers
```

#### 3. 磁盘空间不足

```bash
# 检查磁盘使用
df -h

# 清理日志
find /app/logs -name "*.log" -mtime +7 -delete

# 清理临时文件
rm -rf /tmp/rag_flow_*
```

### 日志分析

```bash
# 查看错误日志
grep ERROR /app/logs/rag-flow.log | tail -100

# 查看性能日志
grep "processing_time" /app/logs/rag-flow.log | tail -50

# 实时监控日志
tail -f /app/logs/rag-flow.log
```

## 安全配置

### 网络安全

```bash
# 防火墙配置
ufw allow 8000/tcp
ufw allow 19530/tcp
ufw enable
```

### 访问控制

```yaml
# nginx.conf
server {
    listen 80;
    server_name rag-flow.example.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # 限制访问
        allow 192.168.1.0/24;
        deny all;
    }
}
```

### SSL 配置

```bash
# 生成 SSL 证书
certbot --nginx -d rag-flow.example.com

# 自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

## 升级指南

### 版本升级

```bash
# 备份数据
./backup.sh

# 停止服务
docker-compose down

# 更新代码
git pull origin main

# 更新镜像
docker-compose pull

# 启动服务
docker-compose up -d

# 验证升级
curl http://localhost:8000/health
```

### 配置迁移

```python
# 配置迁移脚本
def migrate_config(old_config, new_version):
    """配置文件迁移"""
    if new_version == "1.1.0":
        # 添加新配置项
        old_config['new_feature'] = {
            'enabled': True,
            'timeout': 30
        }
    return old_config
```

## 最佳实践

1. **资源规划**: 根据文档量和并发量合理规划硬件资源
2. **监控告警**: 设置完善的监控和告警机制
3. **定期备份**: 建立定期备份和恢复测试流程
4. **性能测试**: 定期进行性能测试和调优
5. **安全更新**: 及时更新系统和依赖库
6. **文档维护**: 保持部署文档的及时更新

---

*部署过程中如有问题，请参考故障排除章节或联系技术支持*
