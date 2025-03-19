"""
数据库升级脚本 - 为newspaper_page表添加text_direction和text_type列
"""
import sqlite3
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取数据库路径
from database import DB_PATH

# 从SQLite连接字符串中提取实际文件路径
db_file = DB_PATH.replace('sqlite:///', '')

def upgrade_database():
    """升级数据库结构，添加缺失的列"""
    print(f"连接数据库: {db_file}")
    
    # 确认文件存在
    if not os.path.exists(db_file):
        print(f"错误: 数据库文件不存在: {db_file}")
        return False
    
    # 连接数据库
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # 检查newspaper_page表中是否已有text_direction列
        cursor.execute("PRAGMA table_info(newspaper_page)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # 添加缺失的列
        if 'text_direction' not in column_names:
            print("添加text_direction列...")
            cursor.execute("ALTER TABLE newspaper_page ADD COLUMN text_direction VARCHAR(20) DEFAULT 'horizontal'")
        
        if 'text_type' not in column_names:
            print("添加text_type列...")
            cursor.execute("ALTER TABLE newspaper_page ADD COLUMN text_type VARCHAR(20) DEFAULT 'simplified'")
        
        # 提交更改
        conn.commit()
        print("数据库升级成功!")
        return True
    
    except Exception as e:
        conn.rollback()
        print(f"数据库升级失败: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    upgrade_database() 