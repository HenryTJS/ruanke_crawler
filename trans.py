import json
import sqlite3
import os

# 需要转换的JSON文件路径列表
json_files = [
    "static/json/bcur.json",
    "static/json/bcsr.json",
    "static/json/bcmr.json",
    "static/json/bcvcr.json",
    "static/json/gras.json"
]

def get_max_depth(data):
    """计算数据的最大深度"""
    max_depth = 0
    
    def traverse(node, depth):
        nonlocal max_depth
        max_depth = max(max_depth, depth)
        
        if 'subfields' in node and node['subfields']:
            for child in node['subfields']:
                traverse(child, depth + 1)
    
    for item in data:
        traverse(item, 1)
    
    return max_depth

def create_table(cursor, table_name, max_depth):
    """根据最大深度创建表"""
    columns = []
    for i in range(1, max_depth + 1):
        columns.extend([
            f'level{i}_number TEXT',
            f'level{i}_name TEXT'
        ])
    
    create_sql = f'''
    CREATE TABLE IF NOT EXISTS {table_name} (
        {', '.join(columns)}
    )
    '''
    cursor.execute(create_sql)

def insert_data(cursor, table_name, data, max_depth):
    """插入数据到数据库"""
    
    def traverse_and_insert(node, current_path, depth):
        path = current_path.copy()
        path.extend([node['number'], node['name']])
        
        if 'subfields' not in node or not node['subfields']:
            while len(path) < max_depth * 2:
                path.extend([None, None])
            
            placeholders = ', '.join(['?'] * len(path))
            cursor.execute(f'INSERT INTO {table_name} VALUES ({placeholders})', path)
        else:
            for child in node['subfields']:
                traverse_and_insert(child, path, depth + 1)
    
    cursor.execute(f'DELETE FROM {table_name}')
    
    for item in data:
        traverse_and_insert(item, [], 1)

def process_json_file(json_file_path, cursor):
    """处理单个JSON文件并导入数据库"""
    # 从文件名提取表名（去掉路径和扩展名）
    table_name = os.path.splitext(os.path.basename(json_file_path))[0]
    
    # 读取JSON数据
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 计算最大深度
    max_depth = get_max_depth(data)
    
    # 创建表并插入数据
    create_table(cursor, table_name, max_depth)
    insert_data(cursor, table_name, data, max_depth)
    
    print(f"已处理: {json_file_path} -> 表: {table_name}")

def main():
    """主函数"""
    # 连接数据库
    conn = sqlite3.connect('中国大学数据集.db')
    cursor = conn.cursor()
    
    try:
        # 处理所有JSON文件
        for json_file in json_files:
            process_json_file(json_file, cursor)
        
        # 提交更改
        conn.commit()
        print("所有数据已成功导入到中国大学数据集.db")
        
    except Exception as e:
        print(f"处理数据时出错: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()