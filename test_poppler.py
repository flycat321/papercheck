#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Poppler安装和PDF转换测试脚本

此脚本用于测试:
1. Poppler是否正确安装
2. 系统是否能成功调用pdftoppm进行PDF转换
3. pdf2image库是否能正常工作

使用方法:
python test_poppler.py [pdf_path]

参数:
    pdf_path: 可选，测试用PDF文件路径，默认为 data/raw/test.pdf
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# 尝试导入pdf2image
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('poppler_test')

def check_poppler_installation():
    """检查Poppler是否安装"""
    logger.info("检查Poppler安装情况...")
    
    # 从环境变量加载Poppler路径
    load_dotenv()
    poppler_path = os.getenv('POPPLER_PATH')
    
    if poppler_path:
        logger.info(f"在环境变量中找到Poppler路径: {poppler_path}")
        poppler_dir = Path(poppler_path)
        
        if not poppler_dir.exists():
            logger.error(f"Poppler路径不存在: {poppler_path}")
            return False, poppler_path
        
        # 检查pdftoppm是否存在
        if os.name == 'nt':  # Windows
            pdftoppm_path = poppler_dir / "pdftoppm.exe"
        else:  # Unix/Linux/Mac
            pdftoppm_path = poppler_dir / "pdftoppm"
            
        if not pdftoppm_path.exists():
            # 尝试查找备选位置
            if os.name == 'nt':  # Windows
                alternative_paths = [
                    poppler_dir.parent / "pdftoppm.exe",
                    Path(poppler_path) / "bin" / "pdftoppm.exe",
                    Path(poppler_path) / "Library" / "bin" / "pdftoppm.exe"
                ]
            else:  # Unix/Linux/Mac
                alternative_paths = [
                    poppler_dir.parent / "pdftoppm",
                    Path(poppler_path) / "bin" / "pdftoppm"
                ]
                
            for alt_path in alternative_paths:
                if alt_path.exists():
                    logger.info(f"在备选位置找到pdftoppm: {alt_path}")
                    return True, str(alt_path.parent)
                    
            logger.error(f"未找到pdftoppm. 已检查的路径: {pdftoppm_path} 和 {alternative_paths}")
            return False, poppler_path
        else:
            logger.info(f"找到pdftoppm: {pdftoppm_path}")
            return True, poppler_path
    else:
        # 尝试在系统PATH中查找
        logger.info("未设置Poppler路径环境变量，尝试在系统PATH中查找...")
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(['where', 'pdftoppm'], 
                                       capture_output=True, text=True, check=False)
            else:  # Unix/Linux/Mac
                result = subprocess.run(['which', 'pdftoppm'], 
                                       capture_output=True, text=True, check=False)
                
            if result.returncode == 0:
                path = result.stdout.strip()
                logger.info(f"在系统PATH中找到pdftoppm: {path}")
                return True, os.path.dirname(path)
            else:
                logger.warning("在系统PATH中未找到pdftoppm")
                return False, None
        except Exception as e:
            logger.error(f"检查系统PATH时出错: {e}")
            return False, None

def test_pdftoppm_command(poppler_path, pdf_path):
    """直接测试pdftoppm命令"""
    logger.info(f"测试pdftoppm命令行...")
    
    if not Path(pdf_path).exists():
        logger.error(f"测试PDF文件不存在: {pdf_path}")
        return False
        
    try:
        # 设置命令和环境
        env = os.environ.copy()
        if poppler_path:
            if os.name == 'nt':  # Windows
                env['PATH'] = f"{poppler_path};{env.get('PATH', '')}"
            else:  # Unix/Linux/Mac
                env['PATH'] = f"{poppler_path}:{env.get('PATH', '')}"
        
        # 构建命令
        output_prefix = str(Path('output_test'))
        if os.name == 'nt':  # Windows
            cmd = ['pdftoppm', '-jpeg', str(pdf_path), output_prefix]
        else:  # Unix/Linux/Mac
            cmd = ['pdftoppm', '-jpeg', str(pdf_path), output_prefix]
            
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            logger.info("pdftoppm命令执行成功!")
            # 检查是否生成了输出文件
            output_files = list(Path('.').glob(f"{output_prefix}*.jpg"))
            if output_files:
                logger.info(f"成功生成了{len(output_files)}个输出文件")
                # 清理测试文件
                for f in output_files:
                    f.unlink()
                return True
            else:
                logger.warning("命令成功执行但未找到输出文件")
                return False
        else:
            logger.error(f"pdftoppm命令执行失败: {result.stderr}")
            return False
    except Exception as e:
        logger.exception(f"执行pdftoppm命令时出错: {e}")
        return False

def test_pdf2image(poppler_path, pdf_path):
    """测试pdf2image库的功能"""
    if not PDF2IMAGE_AVAILABLE:
        logger.error("pdf2image库未安装，请先安装: pip install pdf2image")
        return False
        
    if not Path(pdf_path).exists():
        logger.error(f"测试PDF文件不存在: {pdf_path}")
        return False
        
    logger.info(f"测试pdf2image库转换PDF: {pdf_path}")
    
    try:
        # 尝试转换
        if poppler_path:
            logger.info(f"使用自定义Poppler路径: {poppler_path}")
            pages = convert_from_path(pdf_path, 100, poppler_path=poppler_path)
        else:
            logger.info("使用系统Poppler路径")
            pages = convert_from_path(pdf_path, 100)
            
        if pages:
            logger.info(f"成功转换PDF为{len(pages)}个页面图片")
            # 保存第一页作为测试
            test_output = "test_pdf_output.jpg"
            if pages[0]:
                pages[0].save(test_output, "JPEG")
                logger.info(f"已保存测试输出图片: {test_output}")
                Path(test_output).unlink()  # 清理测试文件
            return True
        else:
            logger.warning("PDF转换成功但没有页面")
            return False
    except Exception as e:
        logger.exception(f"使用pdf2image转换PDF时出错: {e}")
        return False

def main():
    """主函数"""
    logger.info("==== Poppler和PDF转换测试开始 ====")
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "data/raw/test.pdf"
    
    logger.info(f"测试PDF文件: {pdf_path}")
    
    # 1. 检查Poppler安装
    poppler_installed, poppler_path = check_poppler_installation()
    
    if poppler_installed:
        logger.info(f"Poppler安装检查: 通过 ✓")
    else:
        logger.error(f"Poppler安装检查: 失败 ✗")
        logger.info("\n请按照以下说明安装Poppler:")
        logger.info("Windows: 下载 https://github.com/oschwartz10612/poppler-windows/releases/")
        logger.info("         并将bin目录添加到PATH或在.env文件中设置POPPLER_PATH")
        logger.info("Linux:   sudo apt-get install poppler-utils")
        logger.info("macOS:   brew install poppler")
        return
    
    # 2. 测试pdftoppm命令
    if test_pdftoppm_command(poppler_path, pdf_path):
        logger.info("pdftoppm命令测试: 通过 ✓")
    else:
        logger.error("pdftoppm命令测试: 失败 ✗")
    
    # 3. 测试pdf2image库
    if test_pdf2image(poppler_path, pdf_path):
        logger.info("pdf2image库测试: 通过 ✓")
    else:
        logger.error("pdf2image库测试: 失败 ✗")
    
    logger.info("==== 测试完成 ====")
    
    # 提供总结
    logger.info("\n=== 测试结果总结 ===")
    if poppler_installed and test_pdftoppm_command(poppler_path, pdf_path) and test_pdf2image(poppler_path, pdf_path):
        logger.info("所有测试通过! PDF处理应该可以正常工作。")
    else:
        logger.warning("一些测试失败，请检查上面的错误信息。")
        
        # 提供解决方案建议
        logger.info("\n=== 解决方案建议 ===")
        if not poppler_installed:
            logger.info("1. 确保正确安装了Poppler")
            logger.info("   - Windows: 下载 https://github.com/oschwartz10612/poppler-windows/releases/")
            logger.info("   - Linux: sudo apt-get install poppler-utils")
            logger.info("   - macOS: brew install poppler")
        
        if poppler_path:
            logger.info(f"2. 检查Poppler路径配置: {poppler_path}")
            logger.info("   - 确保此路径包含pdftoppm可执行文件")
            logger.info("   - Windows用户: 通常应该指向包含pdftoppm.exe的bin目录")
        
        logger.info("3. 环境变量设置:")
        logger.info("   - 在.env文件中设置: POPPLER_PATH=<poppler_bin_directory>")
        logger.info("   - 或将Poppler的bin目录添加到系统PATH环境变量")
        
        logger.info("4. 尝试使用绝对路径配置Poppler")
        logger.info("5. 确保PDF文件有效且可读")

if __name__ == "__main__":
    main() 