#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试PDF处理功能的脚本
用法: python test_pdf.py [pdf文件路径]
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("PDF_Test")

# 加载环境变量
load_dotenv()

def test_pdf_conversion(pdf_path=None):
    """测试PDF转换功能"""
    try:
        from pdf2image import convert_from_path
        
        # 获取Poppler路径
        poppler_path = os.getenv('POPPLER_PATH')
        logger.info(f"Poppler路径: {poppler_path}")
        
        # 检查Poppler路径是否存在
        if poppler_path:
            poppler_bin = Path(poppler_path)
            if not poppler_bin.exists():
                logger.error(f"Poppler路径不存在: {poppler_bin}")
            else:
                logger.info(f"Poppler路径存在: {poppler_bin}")
                
                # 检查pdftoppm是否存在
                pdftoppm_path = poppler_bin / "pdftoppm.exe"
                if not pdftoppm_path.exists():
                    pdftoppm_path = poppler_bin / "pdftoppm"
                
                if pdftoppm_path.exists():
                    logger.info(f"pdftoppm存在: {pdftoppm_path}")
                else:
                    logger.error(f"pdftoppm不存在: {pdftoppm_path}")
        else:
            logger.warning("未设置Poppler路径，将使用系统路径")
        
        # 测试PDF文件路径
        if pdf_path is None:
            test_pdf = Path("data/raw/test.pdf")
            logger.warning(f"未提供PDF文件路径，使用默认路径: {test_pdf}")
        else:
            test_pdf = Path(pdf_path)
            logger.info(f"使用提供的PDF文件路径: {test_pdf}")
        
        # 检查测试文件是否存在
        if not test_pdf.exists():
            logger.error(f"测试PDF文件不存在: {test_pdf}")
            logger.info("请指定一个有效的PDF文件路径: python test_pdf.py [pdf文件路径]")
            return
        
        # 尝试转换
        logger.info("开始PDF转换测试...")
        
        try:
            if poppler_path:
                logger.info(f"使用指定Poppler路径: {poppler_path}")
                pages = convert_from_path(test_pdf, 300, poppler_path=poppler_path)
            else:
                logger.info("使用系统Poppler路径")
                pages = convert_from_path(test_pdf, 300)
            
            logger.info(f"PDF转换成功！共{len(pages)}页")
            logger.info(f"第一页尺寸: {pages[0].width} x {pages[0].height}")
            
            # 保存第一页作为测试
            save_path = Path("data/test_output.jpg")
            pages[0].save(str(save_path), "JPEG")
            logger.info(f"已保存测试图片: {save_path}")
            
        except Exception as e:
            logger.error(f"PDF转换失败: {e}")
            traceback.print_exc()
    
    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    logger.info("=== 开始PDF处理测试 ===")
    
    # 确保数据目录存在
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True, parents=True)
    
    # 从命令行获取PDF文件路径
    pdf_path = None
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    test_pdf_conversion(pdf_path)
    
    logger.info("=== PDF处理测试完成 ===") 