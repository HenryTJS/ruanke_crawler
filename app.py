from flask import Flask, request, jsonify, render_template
import pandas as pd
import numpy as np

app = Flask(__name__)

# 全局数据存储
data_store = {
    'df': pd.DataFrame()
}

# 数据加载模块
class DataLoader:
    @staticmethod
    def load_all_data():
        """加载所有需要的数据表"""
        try:
            data_store['df'] = pd.read_excel('中国大学表.xlsx')
            # 确保学科和专业列存在，如果不存在则创建空列
            for col in ['顶尖学科', '一流学科', '上榜学科', 'A+专业', 'A类专业', '上榜专业']:
                if col not in data_store['df'].columns:
                    data_store['df'][col] = 0
        except Exception as e:
            print(f"数据加载错误: {e}")
            data_store['df'] = pd.DataFrame()

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
        selected_rank_types = filter_params.get('rank_type', [])

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
        if selected_rank_types and len(selected_rank_types) > 0:
            filtered_df = filtered_df[filtered_df['排名类型'].isin(selected_rank_types)]

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
            return {"chart_data": [], "bar_data": [], "level_data": [], "total_count": 0, "rank_data": []}
        
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
        
        # 排名数据
        rank_data = []
        if '排名类型' in filtered_df.columns and '得分' in filtered_df.columns and '中文名称' in filtered_df.columns:
            selected_rank_type = filter_params.get('rank_type', ['中国大学排名（主榜）'])[0] if filter_params.get('rank_type') else '中国大学排名（主榜）'
            
            # 只处理与当前筛选排名类型匹配的数据
            rank_df = filtered_df[filtered_df['排名类型'] == selected_rank_type]
            
            if not rank_df.empty:
                # 按得分降序排序
                rank_df = rank_df.sort_values(by='得分', ascending=False)
                
                # 取前100名
                rank_df = rank_df.head(100)
                
                rank_data = [{
                    'name': row['中文名称'],
                    'score': float(row['得分'])
                } for _, row in rank_df.iterrows()]

        return {
            "chart_data": pie_data,
            "bar_data": bar_data,
            "level_data": level_data,
            "total_count": len(filtered_df),
            "rank_data": rank_data
        }

    @staticmethod
    def get_wordcloud_data(filter_params):
        """获取学科词云图数据"""
        filtered_df = DataFilter.filter_dataframe(filter_params)
        
        if filtered_df.empty:
            return []
        
        # 获取选择的学科类型
        subject_type = filter_params.get('subject_type', '顶尖学科')
        
        # 检查数据表中是否存在相应的列
        if subject_type not in filtered_df.columns:
            print(f"警告: 数据表中不存在 '{subject_type}' 列")
            return []
        
        # 过滤掉空值
        subject_df = filtered_df[['中文名称', subject_type]].dropna()
        
        # 将学科数量转换为数值类型
        subject_df[subject_type] = pd.to_numeric(subject_df[subject_type], errors='coerce')
        subject_df = subject_df.dropna()
        
        if subject_df.empty:
            print(f"警告: 没有有效的 '{subject_type}' 数据")
            return []
        
        # 按学科数量排序，取前50名
        subject_df = subject_df.sort_values(by=subject_type, ascending=False).head(50)
        
        # 转换为词云数据格式
        wordcloud_data = [{
            "name": row['中文名称'],
            "value": int(row[subject_type])
        } for _, row in subject_df.iterrows()]
        
        return wordcloud_data

    @staticmethod
    def get_major_wordcloud_data(filter_params):
        """获取专业词云图数据"""
        filtered_df = DataFilter.filter_dataframe(filter_params)
        
        if filtered_df.empty:
            return []
        
        # 获取选择的专业类型
        major_type = filter_params.get('major_type', 'A+专业')
        
        # 检查数据表中是否存在相应的列
        if major_type not in filtered_df.columns:
            print(f"警告: 数据表中不存在 '{major_type}' 列")
            return []
        
        # 过滤掉空值
        major_df = filtered_df[['中文名称', major_type]].dropna()
        
        # 将专业数量转换为数值类型
        major_df[major_type] = pd.to_numeric(major_df[major_type], errors='coerce')
        major_df = major_df.dropna()
        
        if major_df.empty:
            print(f"警告: 没有有效的 '{major_type}' 数据")
            return []
        
        # 按专业数量排序，取前50名
        major_df = major_df.sort_values(by=major_type, ascending=False).head(50)
        
        # 转换为词云数据格式
        wordcloud_data = [{
            "name": row['中文名称'],
            "value": int(row[major_type])
        } for _, row in major_df.iterrows()]
        
        return wordcloud_data

# 路由处理模块
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_options')
def get_options():
    """获取筛选选项"""
    if data_store['df'].empty:
        return jsonify({"province": [], "type": [], "level": [], "property": [], "rank_type": []})
        
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

    for lv in level_list:
        property_set.discard(lv)
    
    property_list = sorted(property_set)
    
    # 提取排名类型列表
    rank_type_list = sorted(data_store['df']['排名类型'].dropna().unique().tolist()) \
                    if '排名类型' in data_store['df'].columns else []

    return jsonify({
        "province": province_list,
        "type": type_list,
        "level": level_list,
        "property": property_list,
        "rank_type": rank_type_list
    })

@app.route('/get_chart_data', methods=['POST'])
def get_chart_data():
    """获取图表数据"""
    return jsonify(DataStatistics.get_chart_data(request.json or {}))

@app.route('/get_overview', methods=['POST'])
def get_overview():
    """获取概览数据"""
    return jsonify(DataStatistics.get_overview_data(request.json or {}))

@app.route('/get_wordcloud_data', methods=['POST'])
def get_wordcloud_data():
    """获取学科词云图数据"""
    return jsonify(DataStatistics.get_wordcloud_data(request.json or {}))

@app.route('/get_major_wordcloud_data', methods=['POST'])
def get_major_wordcloud_data():
    """获取专业词云图数据"""
    return jsonify(DataStatistics.get_major_wordcloud_data(request.json or {}))

# 应用初始化
if __name__ == '__main__':
    # 加载数据
    DataLoader.load_all_data()
    app.run(debug=True)