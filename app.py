from flask import Flask, request, jsonify, render_template
import pandas as pd
import os

app = Flask(__name__)

# 全局数据存储
data_store = {
    'df': pd.DataFrame(),
    'rank_dfs': {'university': None, 'college': None},
    'discipline_df': None,
    'major_df': None
}

# 数据加载模块
class DataLoader:
    @staticmethod
    def load_all_data():
        """加载所有需要的数据表"""
        try:
            # 主大学数据表
            data_store['df'] = pd.read_excel('中国大学表.xlsx')
            
            # 排名数据表
            rank_files = {
                'university': '中国大学排名.xlsx',
                'college': '中国高职院校排名.xlsx'
            }
            
            # 检查并加载排名数据
            for key, filename in rank_files.items():
                if os.path.exists(filename):
                    # 强制所有列作为字符串读取
                    df = pd.read_excel(filename, dtype=str)
                    # 确保第一列名称统一为"院校名称"
                    first_col = df.columns[0]
                    if first_col != "院校名称":
                        df = df.rename(columns={first_col: "院校名称"})
                    data_store['rank_dfs'][key] = df
                else:
                    print(f"警告: 未找到排名文件 {filename}")
                    data_store['rank_dfs'][key] = None
            
            # 加载学科排名数据
            if os.path.exists('中国最好学科排名.xlsx'):
                discipline_df = pd.read_excel('中国最好学科排名.xlsx')
                # 确保第一列名称为"院校名称"
                if discipline_df.columns[0] != "院校名称":
                    discipline_df = discipline_df.rename(columns={discipline_df.columns[0]: "院校名称"})
                data_store['discipline_df'] = discipline_df
            else:
                print("警告: 未找到学科排名文件 中国最好学科排名.xlsx")
                data_store['discipline_df'] = None
            
            # 加载专业排名数据
            if os.path.exists('中国大学专业排名.xlsx'):
                major_df = pd.read_excel('中国大学专业排名.xlsx')
                # 确保第一列名称为"院校名称"
                if major_df.columns[0] != "院校名称":
                    major_df = major_df.rename(columns={major_df.columns[0]: "院校名称"})
                data_store['major_df'] = major_df
            else:
                print("警告: 未找到专业排名文件 中国大学专业排名.xlsx")
                data_store['major_df'] = None
                
        except Exception as e:
            print(f"数据加载错误: {e}")
            # 初始化空数据结构
            data_store['df'] = pd.DataFrame()
            data_store['rank_dfs'] = {'university': None, 'college': None}
            data_store['discipline_df'] = None
            data_store['major_df'] = None

# 数据筛选模块
class DataFilter:
    @staticmethod
    def filter_dataframe(filter_params):
        """根据筛选参数过滤数据，空参数返回全部数据"""
        if data_store['df'].empty:
            return pd.DataFrame()
            
        filtered_df = data_store['df'].copy()
        selected_provinces = filter_params.get('province', [])
        selected_types = filter_params.get('type', [])
        selected_levels = filter_params.get('level', [])
        selected_properties = filter_params.get('property', [])

        # 只有当筛选条件不为空时才应用筛选
        if selected_provinces and len(selected_provinces) > 0:
            filtered_df = filtered_df[filtered_df['所在省份'].isin(selected_provinces)]
        if selected_types and len(selected_types) > 0:
            filtered_df = filtered_df[filtered_df['院校类型'].isin(selected_types)]
        if selected_levels and len(selected_levels) > 0:
            filtered_df = filtered_df[filtered_df['办学层次'].isin(selected_levels)]
        if selected_properties and len(selected_properties) > 0:
            filtered_df = filtered_df[filtered_df.apply(
                lambda row: DataFilter.has_property(row, selected_properties), axis=1
            )]

        return filtered_df
    
    @staticmethod
    def has_property(row, selected_properties):
        """检查院校是否具有选中的特性"""
        props = set()
        if '院校归属' in data_store['df'].columns and pd.notna(row['院校归属']):
            props.add(row['院校归属'])
        if '院校特色' in data_store['df'].columns and pd.notna(row['院校特色']):
            props.update([i.strip() for i in str(row['院校特色']).split('/') if i.strip()])
        return any(p in props for p in selected_properties)

# 数据统计模块
class DataStatistics:
    @staticmethod
    def get_overview_data(filter_params):
        """获取概览统计数据"""
        filtered_df = DataFilter.filter_dataframe(filter_params)
        
        if filtered_df.empty:
            return {'total': 0, 'benke': 0, '985': 0, '211': 0, 'doubletop': 0}
        
        # 统计数据
        total_count = len(filtered_df)
        benke_count = len(filtered_df[filtered_df['办学层次'] == '普通本科']) if '办学层次' in filtered_df.columns else 0
        
        # 特色院校统计
        特色_col = '院校特色'
        num_985 = 0
        num_211 = 0
        num_doubletop = 0
        
        if 特色_col in filtered_df.columns:
            num_985 = filtered_df[特色_col].dropna().apply(
                lambda x: '985' in str(x).split('/')
            ).sum()
            num_211 = filtered_df[特色_col].dropna().apply(
                lambda x: '211' in str(x).split('/')
            ).sum()
            num_doubletop = filtered_df[特色_col].dropna().apply(
                lambda x: '双一流' in str(x).split('/')
            ).sum()

        return {
            'total': int(total_count),
            'benke': int(benke_count),
            '985': int(num_985),
            '211': int(num_211),
            'doubletop': int(num_doubletop)
        }
    
    @staticmethod
    def get_chart_data(filter_params):
        """获取图表所需数据"""
        filtered_df = DataFilter.filter_dataframe(filter_params)
        
        if filtered_df.empty:
            return {"chart_data": [], "bar_data": [], "level_data": [], "total_count": 0}
        
        # 饼图数据（院校类型分布）
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

        return {
            "chart_data": pie_data,
            "bar_data": bar_data,
            "level_data": level_data,
            "total_count": len(filtered_df)
        }

# 路由处理模块
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_options')
def get_options():
    """获取筛选选项"""
    if data_store['df'].empty:
        return jsonify({"province": [], "type": [], "level": [], "property": []})
        
    # 提取省份列表
    province_list = sorted(data_store['df']['所在省份'].dropna().unique().tolist()) \
                   if '所在省份' in data_store['df'].columns else []
    
    # 提取院校类型列表
    type_list = sorted(data_store['df']['院校类型'].dropna().unique().tolist()) \
               if '院校类型' in data_store['df'].columns else []
    
    # 提取办学层次列表
    level_list = []
    if '办学层次' in data_store['df'].columns:
        valid_levels = ["普通本科", "职业本科", "高职（专科）"]
        level_list = [i for i in data_store['df']['办学层次'].dropna().unique().tolist() 
                     if i in valid_levels]
    
    # 提取院校特性列表
    property_set = set()
    if '院校归属' in data_store['df'].columns:
        property_set.update(data_store['df']['院校归属'].dropna().unique().tolist())
    if '院校特色' in data_store['df'].columns:
        data_store['df']['院校特色'].dropna().apply(
            lambda x: [property_set.add(i.strip()) for i in str(x).split('/') if i.strip()]
        )
    
    # 移除层次相关特性，避免重复
    for lv in level_list:
        property_set.discard(lv)
    
    property_list = sorted(property_set)

    return jsonify({
        "province": province_list,
        "type": type_list,
        "level": level_list,
        "property": property_list
    })

@app.route('/get_chart_data', methods=['POST'])
def get_chart_data():
    """获取图表数据"""
    return jsonify(DataStatistics.get_chart_data(request.json or {}))

@app.route('/get_overview', methods=['POST'])
def get_overview():
    """获取概览数据"""
    return jsonify(DataStatistics.get_overview_data(request.json or {}))

@app.route('/get_universities_list', methods=['POST'])
def get_universities_list():
    """获取符合筛选条件的大学列表"""
    if data_store['df'].empty or '中文名称' not in data_store['df'].columns:
        return jsonify({"universities": []})
        
    filtered_df = DataFilter.filter_dataframe(request.json or {})
    
    # 提取所有符合条件的大学名称
    universities = [{"name": name} for name in filtered_df['中文名称'].dropna().unique()]
    universities.sort(key=lambda x: x['name'])  # 按名称排序
    
    return jsonify({"universities": universities})

@app.route('/get_university_rank', methods=['POST'])
def get_university_rank():
    """获取指定大学的排名信息"""
    data = request.json or {}
    university_name = data.get('university_name', '')
    
    if not university_name:
        return jsonify([])
    
    rank_info = []
    
    # 检查两个排名文件
    for key, rank_df in data_store['rank_dfs'].items():
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
                            continue  # 处理失败则跳过
                    elif rank_str.replace(',', '').isdigit():
                        # 处理普通数字排名（可能包含逗号）
                        rank_info.append({
                            "rank_type": col,
                            "rank": int(rank_str.replace(',', '')),
                            "rank_display": rank_str
                        })
    
    # 去重并按排名类型排序
    seen = set()
    unique_rank_info = []
    for item in rank_info:
        key = f"{item['rank_type']}_{item['rank']}"
        if key not in seen:
            seen.add(key)
            unique_rank_info.append(item)
    
    unique_rank_info.sort(key=lambda x: x['rank'])
    
    return jsonify(unique_rank_info)

@app.route('/get_university_discipline_rank', methods=['POST'])
def get_university_discipline_rank():
    """获取指定大学的学科排名信息"""
    data = request.json or {}
    university_name = data.get('university_name', '')
    
    if not university_name or data_store['discipline_df'] is None:
        return jsonify([])
    
    try:
        # 查找大学在学科排名表中的行
        discipline_df = data_store['discipline_df'].copy()
        discipline_df['院校名称'] = discipline_df['院校名称'].astype(str)
        matched_rows = discipline_df[discipline_df['院校名称'] == university_name]
        
        if matched_rows.empty:
            return jsonify([])
        
        # 提取所有学科排名数据
        discipline_data = []
        for column in discipline_df.columns[1:]:
            rank = matched_rows[column].iloc[0]
            if pd.notna(rank) and str(rank).strip():
                discipline_data.append({
                    "discipline": column,
                    "rank": str(rank).strip()
                })
        
        return jsonify(discipline_data)
    except Exception as e:
        print(f"获取学科排名数据时出错: {e}")
        return jsonify([])

@app.route('/get_university_major_rank', methods=['POST'])
def get_university_major_rank():
    """获取指定大学的专业排名信息"""
    data = request.json or {}
    university_name = data.get('university_name', '')
    
    if not university_name or data_store['major_df'] is None:
        return jsonify([])
    
    try:
        # 查找大学在专业排名表中的行
        major_df = data_store['major_df'].copy()
        major_df['院校名称'] = major_df['院校名称'].astype(str)
        matched_rows = major_df[major_df['院校名称'] == university_name]
        
        if matched_rows.empty:
            return jsonify([])
        
        # 提取所有专业排名数据
        major_data = []
        for column in major_df.columns[1:]:
            rank = matched_rows[column].iloc[0]
            if pd.notna(rank) and str(rank).strip():
                major_data.append({
                    "major": column,
                    "rank": str(rank).strip()
                })
        
        return jsonify(major_data)
    except Exception as e:
        print(f"获取专业排名数据时出错: {e}")
        return jsonify([])

# 应用初始化
if __name__ == '__main__':
    # 加载数据
    DataLoader.load_all_data()
    app.run(debug=True)