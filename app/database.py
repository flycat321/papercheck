from sqlalchemy import create_engine, Column, Integer, String, Text, Date, ForeignKey, Float, Table, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, joinedload
import datetime
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库路径配置
DB_PATH = os.getenv('DB_PATH', 'sqlite:///data/newspaper.db')

Base = declarative_base()

# 创建文章和关键词的多对多关系表
article_keyword = Table(
    'article_keyword', 
    Base.metadata,
    Column('article_id', Integer, ForeignKey('article.id')),
    Column('keyword_id', Integer, ForeignKey('keyword.id'))
)

class Newspaper(Base):
    """报纸模型，表示一份报纸"""
    __tablename__ = 'newspaper'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # 报纸名称
    issue_date = Column(Date, nullable=True)    # 发行日期
    issue_number = Column(String(50), nullable=True)  # 期号
    file_path = Column(String(255), nullable=False)  # 原始文件路径
    ocr_status = Column(Integer, default=0)  # OCR状态：0未处理，1已处理，2处理错误
    total_pages = Column(Integer, default=1)  # 总页数
    created_at = Column(DateTime, default=datetime.datetime.now)
    
    # 关联关系
    pages = relationship("NewspaperPage", back_populates="newspaper", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Newspaper(name='{self.name}', date='{self.issue_date}', issue='{self.issue_number}')>"

class NewspaperPage(Base):
    """报纸页面模型，表示报纸的一个页面"""
    __tablename__ = 'newspaper_page'
    
    id = Column(Integer, primary_key=True)
    newspaper_id = Column(Integer, ForeignKey('newspaper.id'))
    page_number = Column(Integer, nullable=False)  # 页码
    page_image_path = Column(String(255), nullable=False)  # 页面图片路径
    ocr_text = Column(Text, nullable=True)  # 整页OCR文本
    
    # 关联关系
    newspaper = relationship("Newspaper", back_populates="pages")
    articles = relationship("Article", back_populates="page", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<NewspaperPage(newspaper_id={self.newspaper_id}, page_number={self.page_number})>"

class Article(Base):
    """文章模型，表示从报纸中提取的一篇文章"""
    __tablename__ = 'article'
    
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('newspaper_page.id'))
    title = Column(String(255), nullable=True)  # 文章标题
    content = Column(Text, nullable=True)  # 文章内容
    position_x = Column(Float, nullable=True)  # 文章在页面上的X坐标（相对位置）
    position_y = Column(Float, nullable=True)  # 文章在页面上的Y坐标（相对位置）
    width = Column(Float, nullable=True)  # 文章宽度（相对）
    height = Column(Float, nullable=True)  # 文章高度（相对）
    extracted_date = Column(Date, nullable=True)  # 从文章内容中提取的日期
    
    # 关联关系
    page = relationship("NewspaperPage", back_populates="articles")
    keywords = relationship("Keyword", secondary=article_keyword, back_populates="articles")
    
    def __repr__(self):
        return f"<Article(title='{self.title[:20]}...', page_id={self.page_id})>"

class Keyword(Base):
    """关键词模型，用于标记和检索文章"""
    __tablename__ = 'keyword'
    
    id = Column(Integer, primary_key=True)
    word = Column(String(50), nullable=False, unique=True)
    
    # 关联关系
    articles = relationship("Article", secondary=article_keyword, back_populates="keywords")
    
    def __repr__(self):
        return f"<Keyword(word='{self.word}')>"

# 初始化数据库连接
def init_db():
    """初始化数据库，创建所有表"""
    engine = create_engine(DB_PATH)
    Base.metadata.create_all(engine)
    return engine

# 创建会话
def get_session():
    """获取数据库会话"""
    engine = create_engine(DB_PATH)
    Session = sessionmaker(bind=engine)
    return Session()

# 添加报纸记录
def add_newspaper(name, file_path, issue_date=None, issue_number=None, total_pages=1):
    """添加一份新的报纸记录"""
    session = get_session()
    try:
        newspaper = Newspaper(
            name=name,
            file_path=file_path,
            issue_date=issue_date,
            issue_number=issue_number,
            total_pages=total_pages
        )
        session.add(newspaper)
        session.commit()
        return newspaper.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# 添加报纸页面记录
def add_newspaper_page(newspaper_id, page_number, page_image_path, ocr_text=None):
    """添加报纸页面记录"""
    session = get_session()
    try:
        page = NewspaperPage(
            newspaper_id=newspaper_id,
            page_number=page_number,
            page_image_path=page_image_path,
            ocr_text=ocr_text
        )
        session.add(page)
        session.commit()
        return page.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# 更新报纸的OCR状态
def update_newspaper_ocr_status(newspaper_id, status):
    """更新报纸的OCR处理状态"""
    session = get_session()
    try:
        newspaper = session.query(Newspaper).filter_by(id=newspaper_id).first()
        if newspaper:
            newspaper.ocr_status = status
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# 查询报纸列表
def get_newspapers(limit=100, offset=0):
    """获取报纸列表"""
    session = get_session()
    try:
        newspapers = session.query(Newspaper).order_by(Newspaper.created_at.desc()).limit(limit).offset(offset).all()
        return newspapers
    finally:
        session.close()

# 根据关键词搜索文章
def search_articles_by_keyword(keyword, limit=50):
    """根据关键词搜索文章"""
    session = get_session()
    try:
        articles = session.query(Article).options(
            joinedload(Article.keywords),  # 预加载关键词关系
            joinedload(Article.page).joinedload(NewspaperPage.newspaper)  # 预加载页面和报纸关系
        ).join(
            article_keyword
        ).join(
            Keyword
        ).filter(
            Keyword.word == keyword
        ).limit(limit).all()
        
        return articles
    finally:
        session.close()

# 全文搜索
def search_articles_by_content(search_text, limit=50):
    """在文章内容中搜索文本"""
    session = get_session()
    try:
        # 简单的LIKE查询，实际应用中可能需要全文索引
        articles = session.query(Article).options(
            joinedload(Article.keywords),  # 预加载关键词关系
            joinedload(Article.page).joinedload(NewspaperPage.newspaper)  # 预加载页面和报纸关系
        ).filter(
            Article.content.like(f'%{search_text}%')
        ).limit(limit).all()
        
        return articles
    finally:
        session.close()

# 初始化数据库（如果需要）
if __name__ == "__main__":
    init_db() 