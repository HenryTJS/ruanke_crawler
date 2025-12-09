import json
import os
import pandas as pd

# 需要转换的JSON文件路径列表
json_files = [
    "json/bcur.json",
    "json/bcsr.json",
    "json/bcmr.json",
    "json/bcvcr.json",
    "json/gras.json"
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

def extract_data_to_dataframe(data, max_depth):
    """将数据提取为DataFrame"""
    rows = []
    
    def traverse_and_extract(node, current_path, depth):
        path = current_path.copy()
        path.extend([node.get('number', ''), node.get('name', '')])
        
        if 'subfields' not in node or not node['subfields']:
            # 到达叶子节点，添加数据
            while len(path) < max_depth * 2:
                path.extend(['', ''])
            rows.append(path)
        else:
            for child in node['subfields']:
                traverse_and_extract(child, path, depth + 1)
    
    for item in data:
        traverse_and_extract(item, [], 1)
    
    # 创建列名
    columns = []
    for i in range(1, max_depth + 1):
        columns.extend([f'层级{i}_编号', f'层级{i}_名称'])
    
    # 创建DataFrame
    df = pd.DataFrame(rows, columns=columns)
    return df

def process_json_file_with_pandas(json_file_path, writer):
    """处理单个JSON文件并添加到Excel工作簿（使用pandas）"""
    # 从文件名提取工作表名称（去掉路径和扩展名）
    sheet_name = os.path.splitext(os.path.basename(json_file_path))[0]
    
    # 读取JSON数据
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 计算最大深度
    max_depth = get_max_depth(data)
    
    # 提取数据为DataFrame
    df = extract_data_to_dataframe(data, max_depth)
    
    # 将DataFrame写入Excel
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"已处理: {json_file_path} -> 工作表: {sheet_name}, 共 {len(df)} 行数据")
    return len(df)

def main_with_pandas():
    """主函数（使用pandas版本）"""
    # 创建Excel写入器
    output_file = '中国大学数据集.xlsx'
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        total_rows = 0
            
        # 处理所有JSON文件
        for json_file in json_files:
            rows = process_json_file_with_pandas(json_file, writer)
            total_rows += rows
            
        print(f"\n所有数据已成功导出到 {output_file}")
        print(f"总共 {len(json_files)} 个工作表，{total_rows} 行数据")


if __name__ == "__main__":
    # 使用pandas版本
    main_with_pandas()