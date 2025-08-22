from flask import Flask, request, jsonify, render_template
import pandas as pd
import os

app = Flask(__name__)

# 加载数据
try:
    # 主大学数据表
    df = pd.read_excel('中国大学表.xlsx')
    
    # 排名数据表
    rank_files = {
        'university': '中国大学排名.xlsx',
        'college': '中国高职院校排名.xlsx'
    }
    
    # 检查并加载排名数据，强制所有列作为字符串读取
    rank_dfs = {}
    for key, filename in rank_files.items():
        if os.path.exists(filename):
            # 使用dtype=str参数强制所有列作为字符串读取
            rank_dfs[key] = pd.read_excel(filename, dtype=str)
            # 确保第一列名称统一为"院校名称"
            first_col = rank_dfs[key].columns[0]
            if first_col != "院校名称":
                rank_dfs[key] = rank_dfs[key].rename(columns={first_col: "院校名称"})
        else:
            print(f"警告: 未找到排名文件 {filename}")
            rank_dfs[key] = None
    
    # 加载学科排名数据
    if os.path.exists('中国最好学科排名.xlsx'):
        discipline_df = pd.read_excel('中国最好学科排名.xlsx')
        # 确保第一列名称为"院校名称"
        if discipline_df.columns[0] != "院校名称":
            discipline_df = discipline_df.rename(columns={discipline_df.columns[0]: "院校名称"})
    else:
        print("警告: 未找到学科排名文件 中国最好学科排名.xlsx")
        discipline_df = None
    
    # 新增：加载专业排名数据
    if os.path.exists('中国大学专业排名.xlsx'):
        major_df = pd.read_excel('中国大学专业排名.xlsx')
        # 确保第一列名称为"院校名称"
        if major_df.columns[0] != "院校名称":
            major_df = major_df.rename(columns={major_df.columns[0]: "院校名称"})
    else:
        print("警告: 未找到专业排名文件 中国大学专业排名.xlsx")
        major_df = None
except Exception as e:
    print(f"数据加载错误: {e}")
    df = pd.DataFrame()
    rank_dfs = {'university': None, 'college': None}
    discipline_df = None
    major_df = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_options')
def get_options():
    if df.empty:
        return jsonify({"province": [], "type": [], "level": [], "property": []})
        
    province_list = sorted(df['所在省份'].dropna().unique().tolist()) if '所在省份' in df.columns else []
    type_list = sorted(df['院校类型'].dropna().unique().tolist()) if '院校类型' in df.columns else []
    level_list = [i for i in df['办学层次'].dropna().unique().tolist() if i in ["普通本科", "职业本科", "高职（专科）"]] if '办学层次' in df.columns else []
    property_set = set()
    
    if '院校归属' in df.columns:
        property_set.update(df['院校归属'].dropna().unique().tolist())
    if '院校特色' in df.columns:
        df['院校特色'].dropna().apply(
            lambda x: [property_set.add(i.strip()) for i in str(x).split('/') if i.strip()]
        )
    
    for lv in level_list:
        property_set.discard(lv)
    
    property_list = sorted(property_set)

    options = {
        "province": province_list,
        "type": type_list,
        "level": level_list,
        "property": property_list
    }
    return jsonify(options)

@app.route('/get_chart_data', methods=['POST'])
def get_chart_data():
    if df.empty:
        return jsonify({"chart_data": [], "bar_data": [], "level_data": [], "total_count": 0})
        
    data = request.json
    selected_provinces = data.get('province', [])
    selected_types = data.get('type', [])
    selected_levels = data.get('level', [])
    selected_properties = data.get('property', [])

    filtered_df = df.copy()
    if selected_provinces:
        filtered_df = filtered_df[filtered_df['所在省份'].isin(selected_provinces)]
    if selected_types:
        filtered_df = filtered_df[filtered_df['院校类型'].isin(selected_types)]
    if selected_levels:
        filtered_df = filtered_df[filtered_df['办学层次'].isin(selected_levels)]
    if selected_properties:
        def has_property(row):
            props = set()
            if '院校归属' in df.columns and pd.notna(row['院校归属']):
                props.add(row['院校归属'])
            if '院校特色' in df.columns and pd.notna(row['院校特色']):
                props.update([i.strip() for i in str(row['院校特色']).split('/') if i.strip()])
            return any(p in props for p in selected_properties)
        filtered_df = filtered_df[filtered_df.apply(has_property, axis=1)]

    # 饼图数据
    type_counts = filtered_df['院校类型'].value_counts().reset_index()
    type_counts.columns = ['院校类型', '数量']
    pie_data = [{"name": row["院校类型"], "value": row["数量"]} 
                for _, row in type_counts.iterrows()]

    # 省份分布数据
    province_counts = filtered_df['所在省份'].value_counts().reset_index()
    province_counts.columns = ['省份', '数量']
    province_counts = province_counts.sort_values(by='数量', ascending=False)
    bar_data = [{"name": row["省份"], "value": row["数量"]} 
                for _, row in province_counts.iterrows()]

    # 办学层次分布数据
    level_list = ["普通本科", "职业本科", "高职（专科）"]
    level_counts = filtered_df['办学层次'].value_counts().reindex(level_list, fill_value=0).reset_index()
    level_counts.columns = ['办学层次', '数量']
    level_data = [{"name": row["办学层次"], "value": row["数量"]} 
                  for _, row in level_counts.iterrows()]

    total_count = len(filtered_df)
    return jsonify({
        "chart_data": pie_data,
        "bar_data": bar_data,
        "level_data": level_data,
        "total_count": total_count
    })

@app.route('/get_overview', methods=['POST'])
def get_overview():
    if df.empty:
        return jsonify({'total': 0, 'benke': 0, '985': 0, '211': 0, 'doubletop': 0})
        
    data = request.json or {}
    selected_provinces = data.get('province', [])
    selected_types = data.get('type', [])
    selected_levels = data.get('level', [])
    selected_properties = data.get('property', [])

    filtered_df = df.copy()
    if selected_provinces:
        filtered_df = filtered_df[filtered_df['所在省份'].isin(selected_provinces)]
    if selected_types:
        filtered_df = filtered_df[filtered_df['院校类型'].isin(selected_types)]
    if selected_levels:
        filtered_df = filtered_df[filtered_df['办学层次'].isin(selected_levels)]
    if selected_properties:
        def has_property(row):
            props = set()
            if '院校归属' in df.columns and pd.notna(row['院校归属']):
                props.add(row['院校归属'])
            if '院校特色' in df.columns and pd.notna(row['院校特色']):
                props.update([i.strip() for i in str(row['院校特色']).split('/') if i.strip()])
            return any(p in props for p in selected_properties)
        filtered_df = filtered_df[filtered_df.apply(has_property, axis=1)]

    # 统计数据
    total_count = len(filtered_df)
    benke_count = len(filtered_df[filtered_df['办学层次'] == '普通本科']) if '办学层次' in filtered_df.columns else 0
    num_985 = filtered_df['院校特色'].dropna().apply(lambda x: '985' in str(x).split('/')).sum() if '院校特色' in filtered_df.columns else 0
    num_211 = filtered_df['院校特色'].dropna().apply(lambda x: '211' in str(x).split('/')).sum() if '院校特色' in filtered_df.columns else 0
    num_doubletop = filtered_df['院校特色'].dropna().apply(lambda x: '双一流' in str(x).split('/')).sum() if '院校特色' in filtered_df.columns else 0

    return jsonify({
        'total': int(total_count),
        'benke': int(benke_count),
        '985': int(num_985),
        '211': int(num_211),
        'doubletop': int(num_doubletop)
    })

# 获取符合筛选条件的大学列表，用于下拉选择
@app.route('/get_universities_list', methods=['POST'])
def get_universities_list():
    if df.empty or '中文名称' not in df.columns:
        return jsonify({"universities": []})
        
    data = request.json or {}
    selected_provinces = data.get('province', [])
    selected_types = data.get('type', [])
    selected_levels = data.get('level', [])
    selected_properties = data.get('property', [])

    filtered_df = df.copy()
    if selected_provinces:
        filtered_df = filtered_df[filtered_df['所在省份'].isin(selected_provinces)]
    if selected_types:
        filtered_df = filtered_df[filtered_df['院校类型'].isin(selected_types)]
    if selected_levels:
        filtered_df = filtered_df[filtered_df['办学层次'].isin(selected_levels)]
    if selected_properties:
        def has_property(row):
            props = set()
            if '院校归属' in df.columns and pd.notna(row['院校归属']):
                props.add(row['院校归属'])
            if '院校特色' in df.columns and pd.notna(row['院校特色']):
                props.update([i.strip() for i in str(row['院校特色']).split('/') if i.strip()])
            return any(p in props for p in selected_properties)
        filtered_df = filtered_df[filtered_df.apply(has_property, axis=1)]
    
    # 提取所有符合条件的大学名称
    universities = [{"name": name} for name in filtered_df['中文名称'].dropna().unique()]
    universities.sort(key=lambda x: x['name'])  # 按名称排序
    
    return jsonify({"universities": universities})

# 获取指定大学的排名信息
@app.route('/get_university_rank', methods=['POST'])
def get_university_rank():
    data = request.json or {}
    university_name = data.get('university_name', '')
    
    if not university_name:
        return jsonify([])
    
    rank_info = []
    
    # 检查两个排名文件
    for key, rank_df in rank_dfs.items():
        if rank_df is None:
            continue
            
        # 查找大学在排名表中的行
        matched_rows = rank_df[rank_df['院校名称'] == university_name]
        for _, row in matched_rows.iterrows():
            # 检查所有排名列
            for col in rank_df.columns[1:]:
                rank_value = row[col]
                if pd.notna(rank_value) and str(rank_value).strip():
                    # 处理带有+号的排名（如"500+"）
                    rank_str = str(rank_value).strip()
                    if rank_str.endswith('+'):
                        try:
                            # 提取数字部分并转换为整数
                            num_part = rank_str[:-1]
                            if num_part.isdigit():
                                rank_info.append({
                                    "rank_type": col,
                                    "rank": int(num_part),
                                    "rank_display": rank_str
                                })
                        except ValueError:
                            # 如果处理失败，跳过这个排名
                            continue
                    elif rank_str.replace(',', '').isdigit():
                        # 处理普通数字排名（可能包含逗号，如"1,000"）
                        rank_info.append({
                            "rank_type": col,
                            "rank": int(rank_str.replace(',', '')),
                            "rank_display": rank_str
                        })
    
    # 去重并按排名类型排序
    seen = set()
    unique_rank_info = []
    for item in rank_info:
        # 使用排名类型和数值作为唯一标识
        key = f"{item['rank_type']}_{item['rank']}"
        if key not in seen:
            seen.add(key)
            unique_rank_info.append(item)
    
    unique_rank_info.sort(key=lambda x: x['rank'])
    
    return jsonify(unique_rank_info)

# 新增：获取指定大学的学科排名信息
@app.route('/get_university_discipline_rank', methods=['POST'])
def get_university_discipline_rank():
    global discipline_df
    
    data = request.json or {}
    university_name = data.get('university_name', '')
    
    if not university_name or discipline_df is None:
        return jsonify([])
    
    # 查找大学在学科排名表中的行
    try:
        # 确保院校名称列是字符串类型
        discipline_df['院校名称'] = discipline_df['院校名称'].astype(str)
        matched_rows = discipline_df[discipline_df['院校名称'] == university_name]
        
        if matched_rows.empty:
            return jsonify([])
        
        # 提取所有学科排名数据
        discipline_data = []
        
        # 遍历所有列（除了院校名称列）
        for column in discipline_df.columns[1:]:
            rank = matched_rows[column].iloc[0]  # 获取该学科对应的排名
            if pd.notna(rank) and str(rank).strip():
                discipline_data.append({
                    "discipline": column,
                    "rank": str(rank).strip()
                })
        
        return jsonify(discipline_data)
    except Exception as e:
        print(f"获取学科排名数据时出错: {e}")
        return jsonify([])
    
# 新增：获取指定大学的专业排名信息
@app.route('/get_university_major_rank', methods=['POST'])
def get_university_major_rank():
    global major_df
    
    data = request.json or {}
    university_name = data.get('university_name', '')
    
    if not university_name or major_df is None:
        return jsonify([])
    
    # 查找大学在专业排名表中的行
    try:
        # 确保院校名称列是字符串类型
        major_df['院校名称'] = major_df['院校名称'].astype(str)
        matched_rows = major_df[major_df['院校名称'] == university_name]
        
        if matched_rows.empty:
            return jsonify([])
        
        # 提取所有专业排名数据
        major_data = []
        
        # 遍历所有列（除了院校名称列）
        for column in major_df.columns[1:]:
            rank = matched_rows[column].iloc[0]  # 获取该专业对应的排名
            if pd.notna(rank) and str(rank).strip():
                major_data.append({
                    "major": column,
                    "rank": str(rank).strip()
                })
        
        return jsonify(major_data)
    except Exception as e:
        print(f"获取专业排名数据时出错: {e}")
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)