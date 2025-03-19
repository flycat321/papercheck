import os
import sys
from pathlib import Path

# 将app目录添加到Python路径，以便能正确导入模块
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import logging
import datetime
from database import init_db, get_newspapers, search_articles_by_content, search_articles_by_keyword
from ocr_handler import OCRHandler
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BaozhiApp")

# 初始化Flask应用
app = Flask(__name__, template_folder='ui/templates', static_folder='ui/static')
app.secret_key = 'baozhi_yuedu_secret_key'  # 用于flash消息

# 配置上传文件存储路径
UPLOAD_FOLDER = Path("data/raw")
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'tif', 'tiff'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 限制上传文件大小为100MB

# 确保上传目录存在
UPLOAD_FOLDER.mkdir(exist_ok=True, parents=True)

# 初始化数据库
init_db()

# 初始化OCR处理器
use_gpu = os.getenv('USE_GPU', 'false').lower() == 'true'
poppler_path = os.getenv('POPPLER_PATH')

# 确保Poppler路径使用正斜杠
if poppler_path:
    poppler_path = poppler_path.replace('\\', '/')
    logger.info(f"设置Poppler路径: {poppler_path}")
    # 检查路径是否存在
    if os.path.exists(poppler_path):
        logger.info(f"Poppler路径存在: {poppler_path}")
    else:
        logger.warning(f"Poppler路径不存在: {poppler_path}")

ocr_handler = OCRHandler(use_gpu=use_gpu, poppler_path=poppler_path)

def allowed_file(filename):
    """检查文件扩展名是否被允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """首页"""
    # 获取最近的报纸列表
    newspapers = get_newspapers(limit=10)
    return render_template('index.html', newspapers=newspapers)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """处理文件上传请求"""
    if request.method == 'POST':
        logger.info(f"接收到上传POST请求")
        logger.info(f"表单数据: {request.form}")
        logger.info(f"Content-Type: {request.content_type}")
        
        # 检查是否有文件被上传
        if 'file' not in request.files:
            logger.warning("请求中没有文件部分")
            flash('没有选择文件')
            return redirect(request.url)
        
        file = request.files['file']
        logger.info(f"接收到上传请求: {file.filename if file else 'None'}")
        logger.info(f"文件类型: {file.content_type if file else 'None'}")
        
        # 如果用户未选择文件，浏览器也会提交一个空文件
        if file.filename == '':
            logger.warning("文件名为空")
            flash('没有选择文件')
            return redirect(request.url)
        
        newspaper_name = request.form.get('newspaper_name', '').strip()
        if not newspaper_name:
            newspaper_name = Path(file.filename).stem
            logger.info(f"未提供报纸名称，使用文件名: {newspaper_name}")
        else:
            logger.info(f"使用提供的报纸名称: {newspaper_name}")
        
        logger.info(f"文件上传: {file.filename}, 报纸名称: {newspaper_name}")
        
        # 详细检查文件类型
        original_filename = file.filename
        file_ext = Path(original_filename).suffix.lower()
        logger.info(f"原始文件名: {original_filename}")
        logger.info(f"文件扩展名: {file_ext}")
        
        # 检查文件是否为允许的类型
        is_allowed = allowed_file(original_filename)
        logger.info(f"是否允许的文件类型: {is_allowed}")
        
        if not is_allowed:
            logger.warning(f"不允许的文件类型: {file_ext}")
            flash(f'不支持的文件类型: {file_ext}，请上传PDF或图片文件(支持: {", ".join(ALLOWED_EXTENSIONS)})')
            return redirect(request.url)
        
        # 安全地获取文件名并保存文件
        filename = secure_filename(original_filename)
        logger.info(f"安全文件名: {filename}")
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        save_filename = f"{timestamp}_{filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], save_filename)
        
        try:
            file.save(save_path)
            logger.info(f"文件已保存: {save_path}")
        except Exception as save_err:
            logger.exception(f"保存文件失败: {save_err}")
            flash('保存文件时出错')
            return redirect(request.url)
        
        # 检查文件是否保存成功
        saved_file = Path(save_path)
        if not saved_file.exists():
            logger.error(f"文件保存失败: {save_path}")
            flash('文件保存失败')
            return redirect(request.url)
        
        file_size = saved_file.stat().st_size
        logger.info(f"文件大小: {file_size} 字节")
        
        if file_size == 0:
            logger.error(f"保存的文件大小为0: {save_path}")
            flash('上传的文件为空')
            return redirect(request.url)
        
        # 验证文件类型
        if file_ext == '.pdf':
            logger.info("尝试验证PDF文件格式...")
            try:
                with open(save_path, 'rb') as f:
                    header = f.read(4)
                    if header != b'%PDF':
                        logger.warning(f"文件头不是标准PDF格式: {header}")
                        flash('上传的文件格式似乎不是标准PDF，可能导致处理失败')
                    else:
                        logger.info("验证成功: 标准PDF文件头")
            except Exception as e:
                logger.error(f"读取文件头失败: {e}")
        
        # 启动处理任务
        try:
            logger.info(f"开始处理文件: {save_path}")
            logger.info(f"文件扩展名: {file_ext}")
            logger.info(f"OCR处理器配置: 使用GPU={use_gpu}, poppler_path={ocr_handler.poppler_path}")
            
            newspaper_id = ocr_handler.process_file(save_path, newspaper_name)
            flash(f'文件上传成功并已处理，ID: {newspaper_id}')
            logger.info(f"文件处理成功, 报纸ID: {newspaper_id}")
            return redirect(url_for('view_newspaper', newspaper_id=newspaper_id))
        
        except Exception as e:
            logger.exception(f"处理文件出错: {e}")
            error_msg = str(e)
            
            # 对于常见错误提供更友好的信息
            if "poppler" in error_msg.lower() or "pdftoppm" in error_msg.lower():
                flash(f'PDF处理失败: 未安装Poppler或路径配置错误，请检查配置并参阅Poppler安装说明。错误: {error_msg}')
            elif "找不到pdftoppm" in error_msg:
                flash(f'PDF处理失败: 找不到pdftoppm工具，请确保Poppler正确安装并配置路径。')
            elif "PDF处理失败" in error_msg:
                flash(f'PDF处理失败: {error_msg}')
            elif "不支持的文件类型" in error_msg:
                flash(f'文件类型错误: 系统内部文件类型检测失败，请确保上传了正确的PDF或图片文件。')
            else:
                flash(f'处理文件时出错: {error_msg}')
            
            # 删除上传的文件
            try:
                os.remove(save_path)
                logger.info(f"由于处理失败，删除了上传的文件: {save_path}")
            except Exception as del_err:
                logger.error(f"删除失败的上传文件时出错: {del_err}")
            
            return redirect(request.url)
    
    # GET请求展示上传表单
    return render_template('upload.html')

@app.route('/newspapers')
def list_newspapers():
    """列出所有已上传的报纸"""
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 50, type=int)
    
    newspapers = get_newspapers(limit=limit, offset=offset)
    return render_template('newspapers.html', newspapers=newspapers)

@app.route('/newspaper/<int:newspaper_id>')
def view_newspaper(newspaper_id):
    """查看特定报纸的详细信息"""
    from database import get_session, Newspaper, NewspaperPage
    from sqlalchemy.orm import joinedload
    
    session = get_session()
    try:
        newspaper = session.query(Newspaper).filter_by(id=newspaper_id).first()
        if not newspaper:
            flash('报纸不存在')
            return redirect(url_for('index'))
        
        pages = session.query(NewspaperPage).options(
            joinedload(NewspaperPage.newspaper)
        ).filter_by(newspaper_id=newspaper_id).order_by(NewspaperPage.page_number).all()
        
        return render_template('newspaper_detail.html', newspaper=newspaper, pages=pages)
    finally:
        session.close()

@app.route('/page/<int:page_id>')
def view_page(page_id):
    """查看报纸页面详细信息"""
    from database import get_session, NewspaperPage, Article
    from sqlalchemy.orm import joinedload
    
    session = get_session()
    try:
        page = session.query(NewspaperPage).options(
            joinedload(NewspaperPage.newspaper)
        ).filter_by(id=page_id).first()
        
        if not page:
            flash('页面不存在')
            return redirect(url_for('index'))
        
        articles = session.query(Article).options(
            joinedload(Article.keywords)
        ).filter_by(page_id=page_id).all()
        
        return render_template('page_detail.html', page=page, articles=articles)
    finally:
        session.close()

@app.route('/article/<int:article_id>')
def view_article(article_id):
    """查看文章详细信息"""
    from database import get_session, Article, NewspaperPage
    
    session = get_session()
    try:
        article = session.query(Article).options(
            joinedload(Article.keywords),
            joinedload(Article.page).joinedload(NewspaperPage.newspaper)
        ).filter_by(id=article_id).first()
        
        if not article:
            flash('文章不存在')
            return redirect(url_for('index'))
        
        return render_template('article_detail.html', article=article)
    finally:
        session.close()

@app.route('/search', methods=['GET', 'POST'])
def search():
    """搜索功能"""
    if request.method == 'POST':
        search_text = request.form.get('search_text', '')
        search_type = request.form.get('search_type', 'content')
        
        if not search_text:
            flash('请输入搜索内容')
            return redirect(url_for('search'))
        
        if search_type == 'keyword':
            articles = search_articles_by_keyword(search_text)
        else:  # content search
            articles = search_articles_by_content(search_text)
        
        return render_template('search_results.html', 
                              articles=articles, 
                              search_text=search_text, 
                              search_type=search_type)
    
    return render_template('search.html')

@app.route('/data/images/<path:filename>')
def download_file(filename):
    """提供图片文件访问"""
    return send_from_directory(Path("data/processed"), filename)

@app.route('/api/search', methods=['GET'])
def api_search():
    """API接口：搜索文章"""
    search_text = request.args.get('q', '')
    search_type = request.args.get('type', 'content')
    limit = request.args.get('limit', 10, type=int)
    
    if not search_text:
        return jsonify({"error": "搜索内容不能为空"}), 400
    
    if search_type == 'keyword':
        articles = search_articles_by_keyword(search_text, limit=limit)
    else:
        articles = search_articles_by_content(search_text, limit=limit)
    
    # 转换为JSON可序列化格式
    results = []
    for article in articles:
        results.append({
            "id": article.id,
            "title": article.title,
            "content": article.content[:200] + "..." if len(article.content) > 200 else article.content,
            "date": article.extracted_date.isoformat() if article.extracted_date else None
        })
    
    return jsonify({"results": results})

@app.route('/api/ocr', methods=['POST'])
def api_ocr():
    """API接口：处理OCR请求"""
    # 检查是否有文件被上传
    if 'file' not in request.files:
        return jsonify({"error": "没有文件"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "没有选择文件"}), 400
    
    if file and allowed_file(file.filename):
        # 保存文件并处理
        filename = secure_filename(file.filename)
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        save_filename = f"{timestamp}_{filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], save_filename)
        file.save(save_path)
        
        try:
            newspaper_id = ocr_handler.process_file(save_path)
            return jsonify({
                "success": True,
                "newspaper_id": newspaper_id,
                "message": "文件处理成功"
            })
        except Exception as e:
            logger.error(f"API处理文件出错: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    return jsonify({"error": "不支持的文件类型"}), 400

if __name__ == '__main__':
    # 启动Web服务器
    app.run(debug=True, host='0.0.0.0', port=5000) 