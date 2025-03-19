#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单PDF转换测试脚本
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from pdf2image import convert_from_path

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pdf_test')

def main():
    # 加载环境变量
    load_dotenv()
    poppler_path = os.getenv('POPPLER_PATH')
    logger.info(f"Poppler路径: {poppler_path}")
    
    # 检查Poppler路径
    if poppler_path:
        poppler_dir = Path(poppler_path)
        if not poppler_dir.exists():
            logger.error(f"Poppler路径不存在: {poppler_path}")
            sys.exit(1)
            
        logger.info(f"Poppler路径存在: {poppler_path}")
        
        # 检查pdftoppm是否存在
        if os.name == 'nt':  # Windows
            pdftoppm_path = poppler_dir / "pdftoppm.exe"
        else:
            pdftoppm_path = poppler_dir / "pdftoppm"
            
        if pdftoppm_path.exists():
            logger.info(f"pdftoppm存在: {pdftoppm_path}")
        else:
            logger.warning(f"pdftoppm不存在: {pdftoppm_path}")
    
    # 获取PDF文件路径
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # 寻找任何PDF文件
        pdf_files = list(Path('data/raw').glob('*.pdf'))
        if pdf_files:
            pdf_path = str(pdf_files[0])
            logger.info(f"使用找到的PDF文件: {pdf_path}")
        else:
            logger.error("未找到PDF文件，请指定PDF文件路径作为参数")
            sys.exit(1)
    
    # 检查PDF文件是否存在
    if not Path(pdf_path).exists():
        logger.error(f"PDF文件不存在: {pdf_path}")
        sys.exit(1)
    
    # 尝试转换PDF
    logger.info(f"开始转换PDF文件: {pdf_path}")
    try:
        if poppler_path:
            logger.info(f"使用自定义Poppler路径: {poppler_path}")
            # 使用较低DPI提高速度
            pages = convert_from_path(pdf_path, 150, poppler_path=poppler_path)
        else:
            logger.info("使用系统Poppler路径")
            pages = convert_from_path(pdf_path, 150)
        
        logger.info(f"PDF转换成功，共 {len(pages)} 页")
        
        # 保存第一页作为预览
        if pages:
            output_dir = Path('converted_pages')
            output_dir.mkdir(exist_ok=True)
            
            for i, page in enumerate(pages):
                output_file = output_dir / f"page_{i+1}.jpg"
                page.save(str(output_file), "JPEG")
                logger.info(f"页面 {i+1} 已保存: {output_file}")
                
                # 只保存前3页作为演示
                if i >= 2:
                    logger.info("已保存前3页，停止保存更多页面")
                    break
            
            logger.info(f"PDF已成功转换，预览图片保存在 {output_dir} 目录")
        else:
            logger.warning("PDF转换成功但没有页面内容")
    except Exception as e:
        logger.exception(f"PDF转换失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()