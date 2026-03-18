"""
database.py - AI 门店军师 数据库模块
用于将客户信息、工单记录存入本地 SQLite 数据库，供 PC/手机多端查询。
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = "store_advisor.db"

def init_db():
    """初始化数据库，创建必要的表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建客户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            car_model TEXT,
            last_visit_date DATE,
            last_service TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 增加一个唯一索引，避免同名客户重复导入（简易处理：姓名+车型唯一）
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_name_car
        ON customers (name, car_model)
    ''')
    
    # 创建话术历史记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            message_content TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'draft'
        )
    ''')

    conn.commit()
    conn.close()

def upsert_customer(name, car_model, last_visit_date, last_service):
    """插入或更新客户记录。如果姓名+车型已存在，则更新最后到店时间和维修项目。"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # SQLite 支持 UPSERT (ON CONFLICT) -> 需要 SQLite 3.24+
    try:
        cursor.execute('''
            INSERT INTO customers (name, car_model, last_visit_date, last_service)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name, car_model) DO UPDATE SET
                last_visit_date=excluded.last_visit_date,
                last_service=excluded.last_service,
                created_at=CURRENT_TIMESTAMP
        ''', (name, car_model, last_visit_date, last_service))
    except sqlite3.Error as e:
        print(f"数据库保存错误 (客户 {name}): {e}")
        
    conn.commit()
    conn.close()

def update_customer_field(customer_id, field_name, new_value):
    """根据 ID 更新指定的客户字段"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 为防止 SQL 注入，只能更新固定的几个列名
    allowed_fields = {"姓名": "name", "上次维修项目": "last_service"}
    if field_name not in allowed_fields:
        return False
        
    db_col = allowed_fields[field_name]
    try:
        cursor.execute(f'UPDATE customers SET {db_col} = ? WHERE id = ?', (new_value, customer_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"更新字段错误: {e}")
    finally:
        conn.close()
    return True

def delete_all_customers():
    """清空所有客户数据（支持全量重新导入）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM customers')
    conn.commit()
    conn.close()

def get_all_customers():
    """获取所有客户记录，返回字典列表"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 让查询结果可以按列名访问
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM customers')
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def save_message_draft(customer_name, message_content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO message_history (customer_name, message_content)
        VALUES (?, ?)
    ''', (customer_name, message_content))
    conn.commit()
    conn.close()

def get_message_history():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM message_history ORDER BY generated_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

if __name__ == "__main__":
    init_db()
    print(f"✅ 数据库已初始化：{DB_PATH}")
