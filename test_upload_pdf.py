#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试PDF文件上传和处理流程
用法: python test_upload_pdf.py <pdf文件路径>
"""

import os
import sys
import logging
import shutil
from pathlib import Path
import datetime
from dotenv import load_dotenv

# 添加app目录到Path，以便能导入应用模块
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 使用DEBUG级别获取最详细的日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("PDF_Upload_Test")

# 加载环境变量
load_dotenv()

def test_file_extension_detection(file_path):
    """测试文件扩展名检测"""
    from app.main import allowed_file
    
    file_path = Path(file_path)
    logger.info(f"测试文件: {file_path}")
    logger.info(f"文件名: {file_path.name}")
    logger.info(f"文件扩展名: {file_path.suffix}")
    logger.info(f"检测结果 (allowed_file): {allowed_file(file_path.name)}")
    
    # 测试手动检测
    suffix = file_path.suffix.lower()
    logger.info(f"手动检测扩展名 (lower): {suffix}")
    logger.info(f"是否为PDF (手动检测): {suffix == '.pdf'}")
    logger.info(f"是否在允许列表中 (手动检测): {suffix.lstrip('.') in ['pdf', 'jpg', 'jpeg', 'png', 'tif', 'tiff']}")

def test_pdf_processing(file_path):
    """测试PDF处理流程"""
    from app.ocr_handler import OCRHandler
    
    # 获取环境变量
    poppler_path = os.getenv('POPPLER_PATH')
    use_gpu = os.getenv('USE_GPU', 'false').lower() == 'true'
    
    logger.info(f"配置信息:")
    logger.info(f"  Poppler路径: {poppler_path}")
    logger.info(f"  使用GPU: {use_gpu}")
    
    # 初始化OCR处理器
    logger.info("初始化OCR处理器...")
    ocr_handler = OCRHandler(use_gpu=use_gpu, poppler_path=poppler_path)
    
    # 准备测试文件副本
    file_path = Path(file_path)
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    test_dir = Path("data/raw")
    test_dir.mkdir(exist_ok=True, parents=True)
    test_file = test_dir / f"{timestamp}_{file_path.name}"
    
    logger.info(f"复制测试文件: {file_path} -> {test_file}")
    shutil.copy2(file_path, test_file)
    
    # 处理文件
    logger.info(f"开始处理文件...")
    try:
        newspaper_name = file_path.stem
        logger.info(f"报纸名称: {newspaper_name}")
        
        # 详细测试文件类型检测
        logger.info(f"文件路径: {test_file}")
        logger.info(f"文件扩展名: {test_file.suffix}")
        logger.info(f"小写扩展名: {test_file.suffix.lower()}")
        logger.info(f"扩展名检测: {test_file.suffix.lower() in ['.pdf']}")
        
        # 检查文件头
        with open(test_file, 'rb') as f:
            header = f.read(8)
            logger.info(f"文件头: {header}")
            logger.info(f"是否为PDF (文件头): {header.startswith(b'%PDF')}")
        
        # 处理文件
        newspaper_id = ocr_handler.process_file(test_file, newspaper_name)
        logger.info(f"处理成功！报纸ID: {newspaper_id}")
        return True
    except Exception as e:
        logger.exception(f"处理失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== 开始PDF上传和处理测试 ===")
    
    if len(sys.argv) < 2:
        logger.error("请提供PDF文件路径")
        print("用法: python test_upload_pdf.py <pdf文件路径>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        logger.error(f"文件不存在: {pdf_path}")
        sys.exit(1)
    
    logger.info("测试文件扩展名检测...")
    test_file_extension_detection(pdf_path)
    
    logger.info("")
    logger.info("测试PDF处理流程...")
    success = test_pdf_processing(pdf_path)
    
    logger.info("")
    if success:
        logger.info("✓ 测试成功！")
    else:
        logger.error("✗ 测试失败！")
    
    logger.info("=== PDF上传和处理测试完成 ===") 