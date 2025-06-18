"""
模块名称: docling_api
功能描述: Docling文档处理器Web API服务
创建日期: 2024-12-17
作者: Sniperz
版本: v1.0.0
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import json
import time

try:
    from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# 添加父目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.docling_parser import DoclingParser, DOCLING_AVAILABLE
from parsers.document_processor import DocumentProcessor
from utils.performance_monitor import get_performance_monitor
from config.config_manager import get_config_manager


# 数据模型
class ProcessingRequest(BaseModel):
    """处理请求模型"""
    file_url: Optional[str] = None
    options: Dict[str, Any] = {}


class ProcessingResponse(BaseModel):
    """处理响应模型"""
    success: bool
    task_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None


class StatusResponse(BaseModel):
    """状态响应模型"""
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None


# 全局变量
app = None
document_processor = None
performance_monitor = None
processing_tasks = {}


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI未安装，请运行: pip install fastapi uvicorn")
    
    if not DOCLING_AVAILABLE:
        raise ImportError("Docling未安装，请运行: pip install docling")
    
    app = FastAPI(
        title="Docling文档处理器API",
        description="基于Docling的多格式文档处理服务",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


def initialize_services():
    """初始化服务"""
    global document_processor, performance_monitor
    
    try:
        # 初始化配置管理器
        config_manager = get_config_manager()
        processor_config = config_manager.get_document_processor_config()
        
        # 初始化文档处理器
        document_processor = DocumentProcessor(processor_config)
        
        # 初始化性能监控
        performance_monitor = get_performance_monitor()
        
        logging.info("服务初始化完成")
        
    except Exception as e:
        logging.error(f"服务初始化失败: {e}")
        raise


# 创建应用实例
if FASTAPI_AVAILABLE:
    app = create_app()
    
    @app.on_event("startup")
    async def startup_event():
        """启动事件"""
        initialize_services()
    
    
    @app.get("/", response_model=StatusResponse)
    async def root():
        """根路径"""
        return StatusResponse(
            status="running",
            message="Docling文档处理器API服务正在运行",
            details={
                "version": "1.0.0",
                "docling_available": DOCLING_AVAILABLE,
                "supported_formats": document_processor.get_supported_formats() if document_processor else []
            }
        )
    
    
    @app.get("/health", response_model=StatusResponse)
    async def health_check():
        """健康检查"""
        try:
            # 检查服务状态
            if document_processor is None:
                raise Exception("文档处理器未初始化")
            
            # 检查Docling状态
            docling_info = document_processor.get_docling_info()
            
            return StatusResponse(
                status="healthy",
                message="服务运行正常",
                details={
                    "docling_available": docling_info.get('available', False),
                    "supported_formats_count": len(document_processor.get_supported_formats()),
                    "performance_monitoring": performance_monitor is not None
                }
            )
            
        except Exception as e:
            return StatusResponse(
                status="unhealthy",
                message=f"服务异常: {str(e)}"
            )
    
    
    @app.post("/parse", response_model=ProcessingResponse)
    async def parse_document(file: UploadFile = File(...)):
        """解析上传的文档"""
        start_time = time.time()
        
        try:
            # 检查文件格式
            if not document_processor.is_supported_format(file.filename):
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件格式: {Path(file.filename).suffix}"
                )
            
            # 保存上传的文件到临时目录
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # 解析文档
                result = document_processor.parse(temp_file_path)
                
                # 构建响应
                response_data = {
                    "file_name": file.filename,
                    "file_size": len(content),
                    "document_type": result.document_type.value,
                    "text_content": result.text_content,
                    "metadata": result.metadata,
                    "structured_data": result.structured_data,
                    "structure_info": result.structure_info
                }
                
                processing_time = time.time() - start_time
                
                return ProcessingResponse(
                    success=True,
                    result=response_data,
                    processing_time=processing_time
                )
                
            finally:
                # 清理临时文件
                os.unlink(temp_file_path)
                
        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResponse(
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    
    @app.post("/parse-async", response_model=ProcessingResponse)
    async def parse_document_async(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
        """异步解析文档"""
        import uuid
        
        task_id = str(uuid.uuid4())
        
        # 检查文件格式
        if not document_processor.is_supported_format(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {Path(file.filename).suffix}"
            )
        
        # 保存文件信息
        content = await file.read()
        processing_tasks[task_id] = {
            "status": "pending",
            "file_name": file.filename,
            "file_size": len(content),
            "created_at": time.time()
        }
        
        # 添加后台任务
        background_tasks.add_task(process_document_background, task_id, content, file.filename)
        
        return ProcessingResponse(
            success=True,
            task_id=task_id,
            result={"status": "pending", "message": "文档处理已开始"}
        )
    
    
    @app.get("/task/{task_id}", response_model=ProcessingResponse)
    async def get_task_status(task_id: str):
        """获取任务状态"""
        if task_id not in processing_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task = processing_tasks[task_id]
        
        return ProcessingResponse(
            success=True,
            task_id=task_id,
            result=task
        )
    
    
    @app.get("/stats", response_model=Dict[str, Any])
    async def get_performance_stats():
        """获取性能统计"""
        if performance_monitor:
            return performance_monitor.get_current_stats()
        else:
            return {"error": "性能监控不可用"}
    
    
    @app.get("/formats")
    async def get_supported_formats():
        """获取支持的格式"""
        return {
            "supported_formats": document_processor.get_supported_formats(),
            "docling_info": document_processor.get_docling_info()
        }
    
    
    @app.post("/reset-stats")
    async def reset_performance_stats():
        """重置性能统计"""
        if performance_monitor:
            performance_monitor.reset_stats()
            return {"message": "性能统计已重置"}
        else:
            return {"error": "性能监控不可用"}


async def process_document_background(task_id: str, content: bytes, filename: str):
    """后台处理文档"""
    try:
        # 更新任务状态
        processing_tasks[task_id]["status"] = "processing"
        processing_tasks[task_id]["started_at"] = time.time()
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 解析文档
            result = document_processor.parse(temp_file_path)
            
            # 更新任务结果
            processing_tasks[task_id].update({
                "status": "completed",
                "completed_at": time.time(),
                "result": {
                    "document_type": result.document_type.value,
                    "text_content": result.text_content,
                    "metadata": result.metadata,
                    "structured_data": result.structured_data,
                    "structure_info": result.structure_info
                }
            })
            
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)
            
    except Exception as e:
        # 更新任务错误
        processing_tasks[task_id].update({
            "status": "failed",
            "completed_at": time.time(),
            "error": str(e)
        })


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """运行服务器"""
    if not FASTAPI_AVAILABLE:
        print("错误: FastAPI未安装，请运行: pip install fastapi uvicorn")
        return
    
    if not DOCLING_AVAILABLE:
        print("错误: Docling未安装，请运行: pip install docling")
        return
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    print(f"启动Docling文档处理器API服务...")
    print(f"服务地址: http://{host}:{port}")
    print(f"API文档: http://{host}:{port}/docs")
    
    uvicorn.run(
        "docling_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Docling文档处理器API服务")
    parser.add_argument("--host", default="0.0.0.0", help="服务主机地址")
    parser.add_argument("--port", type=int, default=8000, help="服务端口")
    parser.add_argument("--reload", action="store_true", help="启用自动重载")
    
    args = parser.parse_args()
    
    run_server(args.host, args.port, args.reload)
