# Docling文档处理器Docker镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DOCLING_ARTIFACTS_PATH=/app/models

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 基础工具
    curl \
    wget \
    git \
    # 图像处理依赖
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # OCR依赖
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    # 清理缓存
    && rm -rf /var/lib/apt/lists/*

# 创建模型目录
RUN mkdir -p /app/models /app/cache /app/logs

# 复制requirements文件
COPY requirements.txt /app/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . /app/

# 下载Docling模型（可选，也可以在运行时下载）
RUN python -c "
try:
    from docling.document_converter import DocumentConverter
    # 初始化转换器会自动下载必要的模型
    converter = DocumentConverter()
    print('Docling models downloaded successfully')
except Exception as e:
    print(f'Model download failed: {e}')
    print('Models will be downloaded on first use')
"

# 创建非root用户
RUN useradd -m -u 1000 docling && \
    chown -R docling:docling /app
USER docling

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "from parsers.docling_parser import DoclingParser; print('OK')" || exit 1

# 暴露端口（如果需要Web服务）
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "parsers.docling_parser"]
