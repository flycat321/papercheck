import os
import cv2
import numpy as np
import logging
from pathlib import Path
import uuid
from datetime import datetime
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
import re
import jieba
import jieba.analyse
from database import (
    add_newspaper, add_newspaper_page, 
    update_newspaper_ocr_status, 
    get_session, Article, Keyword
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OCR_Handler")

# 数据目录
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# 确保目录存在
RAW_DIR.mkdir(exist_ok=True, parents=True)
PROCESSED_DIR.mkdir(exist_ok=True, parents=True)

class OCRHandler:
    """OCR处理类，负责从报纸图片/PDF中提取文字"""
    
    def __init__(self, use_gpu=False, poppler_path=None):
        """
        初始化OCR处理器
        
        Args:
            use_gpu: 是否使用GPU加速
            poppler_path: Poppler的路径，主要用于Windows系统
        """
        # 初始化OCR引擎，针对中文报纸进行优化
        self.ocr = PaddleOCR(
            use_gpu=use_gpu,
            lang="ch",  # 中文
            use_angle_cls=True,  # 使用角度分类器
            show_log=False,
            det_db_box_thresh=0.5,  # 检测框阈值
            rec_model_dir=None,  # 使用默认模型
            det_model_dir=None
        )
        
        # 保存Poppler路径
        self.poppler_path = poppler_path
        
        # 加载结巴分词词典（可以添加古文/民国时期常用词汇）
        # jieba.load_userdict("path/to/dict.txt")
        
        logger.info("OCR引擎初始化完成")
    
    def process_file(self, file_path, newspaper_name=None):
        """
        处理文件（图片或PDF）
        
        Args:
            file_path: 文件路径
            newspaper_name: 报纸名称，如果为None则从文件名推断
            
        Returns:
            newspaper_id: 数据库中的报纸ID
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 如果未提供报纸名称，从文件名中推断
        if newspaper_name is None:
            newspaper_name = file_path.stem
        
        # 确定文件类型
        file_ext = file_path.suffix.lower()
        logger.info(f"处理文件: {file_path}, 文件扩展名: {file_ext}")
        
        # 增强型文件类型检测
        # 1. 通过扩展名检测
        is_pdf_by_ext = file_ext in ['.pdf']
        is_image_by_ext = file_ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp']
        
        # 2. 通过文件头检测
        file_type_by_header = None
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if header.startswith(b'%PDF'):
                    file_type_by_header = 'pdf'
                elif header.startswith(b'\xFF\xD8\xFF'):  # JPEG
                    file_type_by_header = 'jpeg'
                elif header.startswith(b'\x89PNG\r\n\x1A\n'):  # PNG
                    file_type_by_header = 'png'
                # 可以添加更多文件类型的检测
                logger.info(f"文件头检测结果: {file_type_by_header}, 文件头: {header}")
        except Exception as e:
            logger.error(f"读取文件头失败: {e}")
        
        # 根据检测结果处理文件
        if is_pdf_by_ext:
            logger.info(f"基于扩展名，确定为PDF文件: {file_path}")
            # 如果文件头也确认是PDF，那么更有信心
            if file_type_by_header == 'pdf':
                logger.info(f"文件头确认是PDF文件")
            else:
                logger.warning(f"文件头未确认是PDF文件，但仍按PDF处理")
            
            try:
                return self._process_pdf(file_path, newspaper_name)
            except Exception as e:
                logger.exception(f"PDF处理错误: {e}")
                raise RuntimeError(f"PDF处理失败: {str(e)}")
        
        elif is_image_by_ext:
            logger.info(f"基于扩展名，确定为图片文件: {file_path}")
            try:
                return self._process_image(file_path, newspaper_name)
            except Exception as e:
                logger.exception(f"图片处理错误: {e}")
                raise RuntimeError(f"图片处理失败: {str(e)}")
        
        # 如果扩展名不支持，但文件头可能是已知类型
        elif file_type_by_header == 'pdf':
            logger.warning(f"扩展名不支持({file_ext})，但文件头显示这是PDF文件，尝试按PDF处理")
            try:
                return self._process_pdf(file_path, newspaper_name)
            except Exception as e:
                logger.exception(f"PDF处理错误: {e}")
                raise RuntimeError(f"PDF处理失败: {str(e)}")
        
        elif file_type_by_header in ['jpeg', 'png']:
            logger.warning(f"扩展名不支持({file_ext})，但文件头显示这是图片文件，尝试按图片处理")
            try:
                return self._process_image(file_path, newspaper_name)
            except Exception as e:
                logger.exception(f"图片处理错误: {e}")
                raise RuntimeError(f"图片处理失败: {str(e)}")
        
        else:
            logger.error(f"不支持的文件类型: {file_ext}, 文件: {file_path}")
            raise ValueError(f"不支持的文件类型: {file_ext}")
    
    def _process_pdf(self, pdf_path, newspaper_name):
        """处理PDF文件"""
        try:
            logger.info(f"准备将PDF转换为图片: {pdf_path}")
            
            # 处理Poppler路径
            poppler_path = self.poppler_path
            if poppler_path:
                # 确保使用正斜杠而非反斜杠
                poppler_path = str(poppler_path).replace('\\', '/')
                logger.info(f"处理后的Poppler路径: {poppler_path}")
                poppler_dir = Path(poppler_path)
                if not poppler_dir.exists():
                    logger.error(f"Poppler路径不存在: {poppler_path}")
                    raise FileNotFoundError(f"Poppler路径不存在: {poppler_path}")
                
                # 检查pdftoppm是否存在
                pdftoppm_path = poppler_dir / "pdftoppm.exe" if os.name == 'nt' else poppler_dir / "pdftoppm"
                logger.info(f"检查pdftoppm: {pdftoppm_path}")
                if not pdftoppm_path.exists():
                    alternative_path = poppler_dir.parent / "pdftoppm.exe" if os.name == 'nt' else poppler_dir.parent / "pdftoppm"
                    if not alternative_path.exists():
                        logger.error(f"pdftoppm不存在于Poppler路径中: {pdftoppm_path}")
                        logger.error(f"也不存在于备选路径: {alternative_path}")
                        raise FileNotFoundError(f"找不到pdftoppm: {pdftoppm_path}")
                    else:
                        logger.info(f"在备选路径找到pdftoppm: {alternative_path}")
                else:
                    logger.info(f"pdftoppm存在: {pdftoppm_path}")
            else:
                logger.warning("未设置Poppler路径，将尝试使用系统路径")
            
            # 检查是否为有效的PDF文件
            logger.info(f"检查PDF文件头...")
            try:
                with open(pdf_path, 'rb') as f:
                    header = f.read(4)
                    logger.info(f"PDF文件头: {header}")
                    if header != b'%PDF':
                        logger.error(f"文件不是有效的PDF格式: {pdf_path}, 文件头: {header}")
                        raise ValueError(f"文件不是有效的PDF格式: {pdf_path}")
                    else:
                        logger.info("PDF文件头验证通过")
            except Exception as e:
                logger.error(f"读取PDF文件头失败: {e}")
                raise
            
            # 将PDF转换为图片
            try:
                # 记录环境变量
                logger.info(f"系统环境: os.name={os.name}, PATH={os.environ.get('PATH', '')}")
                
                # 尝试将PDF转换为图片
                logger.info("开始PDF到图片的转换...")
                if poppler_path:
                    logger.info(f"使用自定义Poppler路径: {poppler_path}")
                    try:
                        pages = convert_from_path(str(pdf_path), 300, poppler_path=poppler_path)
                        logger.info(f"使用自定义Poppler路径转换成功")
                    except Exception as custom_poppler_err:
                        logger.exception(f"使用自定义Poppler路径失败: {custom_poppler_err}")
                        logger.info("尝试使用系统Poppler路径作为备选...")
                        pages = convert_from_path(str(pdf_path), 300)
                        logger.info(f"使用系统Poppler路径转换成功")
                else:
                    logger.info(f"使用系统Poppler路径")
                    pages = convert_from_path(str(pdf_path), 300)
                
                if not pages:
                    logger.error("PDF转换结果为空，没有页面被转换")
                    raise RuntimeError("PDF转换结果为空，没有页面被转换")
                
                logger.info(f"PDF成功转换为{len(pages)}个页面图片")
            except Exception as pdf_err:
                logger.exception(f"PDF转换错误: {str(pdf_err)}")
                # 通常这是因为缺少Poppler依赖
                if "poppler" in str(pdf_err).lower() or "pdftoppm" in str(pdf_err).lower():
                    error_msg = f"PDF处理需要安装Poppler库，详细错误: {str(pdf_err)}\n"
                    error_msg += "Windows用户：https://github.com/oschwartz10612/poppler-windows/releases/\n"
                    error_msg += "下载后，将bin目录添加到系统PATH环境变量中，或在.env文件中设置POPPLER_PATH参数。"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                else:
                    logger.error(f"PDF转换失败，详细错误: {str(pdf_err)}")
                    raise RuntimeError(f"PDF转换失败: {str(pdf_err)}")
            
            # 创建报纸记录
            logger.info(f"创建报纸记录: {newspaper_name}")
            newspaper_id = add_newspaper(
                name=newspaper_name,
                file_path=str(pdf_path),
                total_pages=len(pages)
            )
            logger.info(f"报纸记录创建成功, ID: {newspaper_id}")
            
            # 创建存储处理后图片的目录
            save_dir = PROCESSED_DIR / f"newspaper_{newspaper_id}"
            save_dir.mkdir(exist_ok=True)
            logger.info(f"创建图片存储目录: {save_dir}")
            
            # 处理每一页
            for i, page in enumerate(pages):
                page_number = i + 1
                logger.info(f"处理第{page_number}页...")
                
                # 保存页面图片
                page_image_path = save_dir / f"page_{page_number}.jpg"
                page.save(str(page_image_path), "JPEG")
                logger.info(f"页面图片已保存: {page_image_path}")
                
                # 处理图片并提取文字
                logger.info(f"从图像中提取文字...")
                ocr_result = self._extract_text_from_image(np.array(page))
                ocr_text = self._convert_ocr_result_to_text(ocr_result)
                logger.info(f"提取了{len(ocr_text.splitlines())}行文本")
                
                # 添加页面记录
                logger.info(f"添加页面记录到数据库...")
                page_id = add_newspaper_page(
                    newspaper_id=newspaper_id,
                    page_number=page_number,
                    page_image_path=str(page_image_path),
                    ocr_text=ocr_text
                )
                logger.info(f"页面记录添加成功, ID: {page_id}")
                
                # 提取文章和关键词
                logger.info(f"提取文章和关键词...")
                self._extract_articles_and_keywords(page_id, ocr_result, ocr_text)
                
                logger.info(f"已处理页面 {page_number}/{len(pages)}")
            
            # 更新处理状态
            logger.info(f"更新报纸处理状态...")
            update_newspaper_ocr_status(newspaper_id, 1)  # 标记为已处理
            logger.info(f"PDF处理完成: {pdf_path}")
            
            return newspaper_id
        
        except Exception as e:
            logger.exception(f"PDF处理过程中出错: {e}")
            if 'newspaper_id' in locals():
                logger.info(f"将报纸状态标记为处理错误: {newspaper_id}")
                update_newspaper_ocr_status(newspaper_id, 2)  # 标记为处理错误
            raise
    
    def _process_image(self, image_path, newspaper_name):
        """处理单个图片文件"""
        try:
            # 读取图片
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"无法读取图片: {image_path}")
            
            # 创建报纸记录
            newspaper_id = add_newspaper(
                name=newspaper_name,
                file_path=str(image_path),
                total_pages=1
            )
            
            # 创建存储处理后图片的目录
            save_dir = PROCESSED_DIR / f"newspaper_{newspaper_id}"
            save_dir.mkdir(exist_ok=True)
            
            # 复制原始图片
            page_image_path = save_dir / f"page_1.jpg"
            cv2.imwrite(str(page_image_path), image)
            
            # 处理图片并提取文字
            ocr_result = self._extract_text_from_image(image)
            ocr_text = self._convert_ocr_result_to_text(ocr_result)
            
            # 添加页面记录
            page_id = add_newspaper_page(
                newspaper_id=newspaper_id,
                page_number=1,
                page_image_path=str(page_image_path),
                ocr_text=ocr_text
            )
            
            # 提取文章和关键词
            self._extract_articles_and_keywords(page_id, ocr_result, ocr_text)
            
            # 更新处理状态
            update_newspaper_ocr_status(newspaper_id, 1)  # 标记为已处理
            logger.info(f"图片处理完成: {image_path}")
            
            return newspaper_id
        
        except Exception as e:
            logger.error(f"图片处理错误: {e}")
            if 'newspaper_id' in locals():
                update_newspaper_ocr_status(newspaper_id, 2)  # 标记为处理错误
            raise
    
    def _extract_text_from_image(self, image):
        """
        从图片中提取文字
        
        Args:
            image: OpenCV图片对象
        
        Returns:
            OCR结果
        """
        # 图像预处理可以在这里添加
        # 例如：调整对比度、二值化等
        
        # 运行OCR
        result = self.ocr.ocr(image, cls=True)
        return result[0] if result else []
    
    def _convert_ocr_result_to_text(self, ocr_result):
        """
        将OCR结果转换为纯文本
        
        Args:
            ocr_result: OCR的原始结果
            
        Returns:
            提取的文本
        """
        text_lines = []
        for line in ocr_result:
            if line:
                # line结构：[[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], [text, confidence]]
                text, confidence = line[1]
                text_lines.append(text)
        
        return "\n".join(text_lines)
    
    def _extract_articles_and_keywords(self, page_id, ocr_result, ocr_text):
        """
        从OCR结果中提取文章和关键词
        
        Args:
            page_id: 页面ID
            ocr_result: OCR的原始结果
            ocr_text: OCR提取的完整文本
        """
        session = get_session()
        try:
            # 简单的文章分割方法（实际项目可能需要更复杂的算法）
            # 这里简单地把整页当作一篇文章处理
            
            # 尝试提取标题（假设页面上第一行文字是标题）
            title = ocr_result[0][1][0] if ocr_result else "未知标题"
            
            # 尝试从文本中提取日期
            date_match = re.search(r'(\d{2,4})[年/-](\d{1,2})[月/-](\d{1,2})[日号]?', ocr_text)
            extracted_date = None
            if date_match:
                try:
                    year, month, day = map(int, date_match.groups())
                    # 处理民国年份或其他特殊年份格式
                    if year < 100:
                        # 假设是民国年份，转换为公元年份
                        year += 1911
                    extracted_date = datetime(year, month, day).date()
                except ValueError:
                    pass
            
            # 提取关键词
            keywords = jieba.analyse.extract_tags(ocr_text, topK=10)
            
            # 创建文章记录
            article = Article(
                page_id=page_id,
                title=title,
                content=ocr_text,
                extracted_date=extracted_date
            )
            session.add(article)
            session.flush()  # 获取article_id
            
            # 添加关键词
            for word in keywords:
                # 检查关键词是否已存在
                keyword = session.query(Keyword).filter_by(word=word).first()
                if not keyword:
                    keyword = Keyword(word=word)
                    session.add(keyword)
                    session.flush()
                
                # 将关键词与文章关联
                article.keywords.append(keyword)
            
            session.commit()
            logger.info(f"已添加文章: {title}, 关键词: {', '.join(keywords)}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"提取文章和关键词时出错: {e}")
            raise
        finally:
            session.close()

# 单独测试
if __name__ == "__main__":
    # 初始化OCR处理器
    handler = OCRHandler(use_gpu=False)
    
    # 测试处理一个图片
    test_image = "data/raw/test.jpg"  # 替换为实际测试图片路径
    if os.path.exists(test_image):
        handler.process_file(test_image) 