from flask import Flask, request, jsonify, render_template
import pandas as pd
import sqlite3
from pathlib import Path

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
            # 检查数据库文件是否存在
            db_path = '中国大学数据集.db'
            if not Path(db_path).exists():
                raise FileNotFoundError(f"数据库文件 {db_path} 不存在")
            
            # 连接SQLite数据库
            conn = sqlite3.connect(db_path)
            
            # 假设数据库中有一个名为'universities'的表，包含所有大学数据
            # 如果表结构不同，需要调整查询语句和列名处理
            query = "SELECT * FROM universities"
            data_store['df'] = pd.read_sql_query(query, conn)
            
            # 关闭数据库连接
            conn.close()
            
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
        selected_properties = filter_params.get('property', [])
        selected_rank_types = filter_params.get('rank_type', [])

        # 只有当筛选条件不为空时才应用筛选
        if selected_provinces and len(selected_provinces) > 0:
            # 将标准化的省份名称转换回原始名称进行筛选
            original_province_names = [reverse_standardize_province_name(province) for province in selected_provinces]
            filtered_df = filtered_df[filtered_df['所在省份'].isin(original_province_names)]
        if selected_types and len(selected_types) > 0:
            filtered_df = filtered_df[filtered_df['院校类型'].isin(selected_types)]
        if selected_properties and len(selected_properties) > 0:
            # 检查是否包含办学层次选项
            level_options = ["普通本科", "职业本科", "高职（专科）"]
            level_selections = [prop for prop in selected_properties if prop in level_options]
            property_selections = [prop for prop in selected_properties if prop not in level_options]
            
            # 应用办学层次筛选
            if level_selections:
                filtered_df = filtered_df[filtered_df['办学层次'].isin(level_selections)]
            
            # 应用院校特性筛选
            if property_selections:
                filtered_df = filtered_df[filtered_df.apply(
                    lambda row: DataFilter.has_property(row, property_selections), axis=1
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
    def get_chart_data(filter_params):
        filtered_df = DataFilter.filter_dataframe(filter_params)

        if filtered_df.empty:
            return {"feature_bar": [], "bar_data": [], "total_count": 0, "rank_data": []}

        # 新：院校特性占比（横向柱状图数据）
        selected_properties = filter_params.get('property', []) or []
        # 基础集：按省份、类型、排名类型过滤，并且若选择了院校特性，也将其作为筛选范围
        base_params = {
            'province': filter_params.get('province', []),
            'type': filter_params.get('type', []),
            'rank_type': filter_params.get('rank_type', []),
            'property': selected_properties
        }
        base_df = DataFilter.filter_dataframe(base_params)
        feature_bar = []
        total_base = len(base_df)
        if total_base > 0:
            # 无论是否选择特性，都从当前范围自动枚举全部特性/类型/层次
            props_detected = set()
            if '院校特色' in base_df.columns:
                base_df['院校特色'].dropna().apply(
                    lambda x: [props_detected.add(i.strip()) for i in str(x).split('/') if i.strip()]
                )
            if '院校归属' in base_df.columns:
                base_df['院校归属'].dropna().apply(
                    lambda x: props_detected.add(str(x).strip()) if str(x).strip() else None
                )
            if '院校类型' in base_df.columns:
                base_df['院校类型'].dropna().apply(
                    lambda x: props_detected.add(str(x).strip()) if str(x).strip() else None
                )
            if '办学层次' in base_df.columns:
                base_df['办学层次'].dropna().apply(
                    lambda x: props_detected.add(str(x).strip()) if str(x).strip() else None
                )
            props_for_bar = sorted([p for p in props_detected if p])
            # 计数时对每行做“任一匹配”以避免同一行重复计数
            def row_has_prop(row, prop):
                has_feature = False
                if '院校特色' in row and pd.notna(row['院校特色']):
                    has_feature = any(i.strip() == prop for i in str(row['院校特色']).split('/') if i.strip())
                if not has_feature and '院校归属' in row and pd.notna(row['院校归属']):
                    has_feature = str(row['院校归属']).strip() == prop
                if not has_feature and '院校类型' in row and pd.notna(row['院校类型']):
                    has_feature = str(row['院校类型']).strip() == prop
                if not has_feature and '办学层次' in row and pd.notna(row['办学层次']):
                    has_feature = str(row['办学层次']).strip() == prop
                return has_feature
            for prop in props_for_bar:
                count = int(base_df.apply(lambda r: row_has_prop(r, prop), axis=1).sum())
                percent = round((count / total_base) * 100, 2) if total_base else 0
                feature_bar.append({"name": prop, "value": percent, "count": int(count), "total": int(total_base)})

        # 省份分布数据（地图）
        province_counts = filtered_df['所在省份'].value_counts().reset_index()
        province_counts.columns = ['省份', '数量']
        province_counts = province_counts.sort_values(by='数量', ascending=False)
        bar_data = [{"name": standardize_province_name(row["省份"]), "value": row["数量"]}
                    for _, row in province_counts.iterrows()]
        
        # 排名数据
        rank_data = []
        if '排名类型' in filtered_df.columns and '得分' in filtered_df.columns and '中文名称' in filtered_df.columns:
            selected_rank_type = filter_params.get('rank_type', [])
            # 如果未选或选了"全部"，只显示主榜
            if not selected_rank_type or selected_rank_type[0] in ['', '全部']:
                rank_df = filtered_df[filtered_df['排名类型'] == '中国大学排名（主榜）']
            else:
                rank_df = filtered_df[filtered_df['排名类型'] == selected_rank_type[0]]
            if not rank_df.empty:
                rank_df = rank_df.sort_values(by='得分', ascending=False)
                # 返回所有符合条件的数据
                rank_data = [{
                    'name': row['中文名称'],
                    'score': float(row['得分']),
                    'rank_type': row['排名类型'],
                    'ranking': int(row['排名'])
                } for _, row in rank_df.iterrows()]

        # 按占比降序排序
        feature_bar = sorted(feature_bar, key=lambda x: x["value"], reverse=True)
        return {
            "feature_bar": feature_bar,
            "bar_data": bar_data,
            "total_count": len(filtered_df),
            "rank_data": rank_data
        }

    @staticmethod
    def get_university_table_data(filter_params):
        """获取大学表格数据"""
        filtered_df = DataFilter.filter_dataframe(filter_params)
        
        if filtered_df.empty:
            return []
        
        # 始终以院校代码为排序依据（若存在该列）
        if '院校代码' in filtered_df.columns:
            filtered_df = filtered_df.sort_values(by='院校代码', na_position='last')
        
        # 选择需要的列
        columns = ['中文名称', '所在省份', '院校类型', '办学层次']
        
        # 检查哪些列存在
        available_columns = [col for col in columns if col in filtered_df.columns]
        
        if not available_columns:
            return []
        
        # 获取数据
        table_data = filtered_df[available_columns].copy()
        
        # 添加排名信息（如果有的话）
        if '排名' in filtered_df.columns:
            table_data['排名'] = filtered_df['排名']
        elif '中国大学排名（主榜）' in filtered_df.columns:
            table_data['排名'] = filtered_df['中国大学排名（主榜）']
        else:
            table_data['排名'] = None
        
        # 重命名列以匹配前端
        column_mapping = {
            '中文名称': 'name',
            '所在省份': 'province', 
            '院校类型': 'type',
            '办学层次': 'level',
            '排名': 'rank'
        }
        
        table_data = table_data.rename(columns=column_mapping)
        
        # 删除表格层面的其它排序逻辑：以院校代码排序已在上方完成
        
        # 转换为字典列表，处理NaN值
        result = []
        for _, row in table_data.iterrows():
            result.append({
                'name': str(row.get('name', '')) if pd.notna(row.get('name')) else '',
                'province': str(row.get('province', '')) if pd.notna(row.get('province')) else '',
                'type': str(row.get('type', '')) if pd.notna(row.get('type')) else '',
                'level': str(row.get('level', '')) if pd.notna(row.get('level')) else '',
                'rank': int(row.get('rank')) if pd.notna(row.get('rank')) else None
            })
        
        return result

# 路由处理模块（保持不变）
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_options')
def get_options():
    """获取筛选选项"""
    if data_store['df'].empty:
        return jsonify({"province": [], "type": [], "level": [], "property": [], "rank_type": []})
        
    # 提取省份列表
    province_list = sorted([x for x in data_store['df']['所在省份'].dropna().unique().tolist() if str(x).strip()]) \
                   if '所在省份' in data_store['df'].columns else []
    
    # 提取院校类型列表（基础）
    type_list = sorted([x for x in data_store['df']['院校类型'].dropna().unique().tolist() if str(x).strip()]) \
               if '院校类型' in data_store['df'].columns else []
    
    # 提取办学层次列表
    level_list = []
    if '办学层次' in data_store['df'].columns:
        valid_levels = ["普通本科", "职业本科", "高职（专科）"]
        level_list = [i for i in data_store['df']['办学层次'].dropna().unique().tolist() 
                     if i in valid_levels and str(i).strip()]
    
    # 提取院校特性列表
    property_set = set()
    if '院校归属' in data_store['df'].columns:
        property_set.update([x for x in data_store['df']['院校归属'].dropna().unique().tolist() if str(x).strip()])
    if '院校特色' in data_store['df'].columns:
        data_store['df']['院校特色'].dropna().apply(
            lambda x: [property_set.add(i.strip()) for i in str(x).split('/') if i.strip()]
        )

    # 移除空字符串和办学层次
    for lv in level_list:
        property_set.discard(lv)
    property_set.discard('')
    property_set.discard(None)
    
    property_list = sorted([x for x in property_set if str(x).strip()])
    
    # 按需合并：将“院校特性”加入原“院校类型”的16个选项中（去重）
    type_list = sorted(list({*type_list, *property_list}))
    
    # 提取排名类型列表
    rank_type_list = sorted([x for x in data_store['df']['排名类型'].dropna().unique().tolist() if str(x).strip()]) \
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


@app.route('/get_university_table_data', methods=['POST'])
def get_university_table_data():
    """获取大学表格数据"""
    return jsonify(DataStatistics.get_university_table_data(request.json or {}))

# 标准省份名映射
PROVINCE_NAME_MAP = {
    "广西": "广西壮族自治区",
    "内蒙古": "内蒙古自治区",
    "西藏": "西藏自治区",
    "宁夏": "宁夏回族自治区",
    "新疆": "新疆维吾尔自治区",
    "香港": "香港特别行政区",
    "澳门": "澳门特别行政区",
    "重庆": "重庆市",
    "北京": "北京市",
    "天津": "天津市",
    "上海": "上海市",
}

# 反向映射：从标准化名称到原始名称
REVERSE_PROVINCE_NAME_MAP = {v: k for k, v in PROVINCE_NAME_MAP.items()}
# 添加省后缀的反向映射
for province in ["河北", "山西", "辽宁", "吉林", "黑龙江", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南", "广东", "海南", "四川", "贵州", "云南", "陕西", "甘肃", "青海"]:
    REVERSE_PROVINCE_NAME_MAP[province + "省"] = province

def standardize_province_name(name):
    name = str(name).strip()
    return PROVINCE_NAME_MAP.get(name, name + "省" if name in ["河北", "山西", "辽宁", "吉林", "黑龙江", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南", "广东", "海南", "四川", "贵州", "云南", "陕西", "甘肃", "青海"] else name)

def reverse_standardize_province_name(name):
    """将标准化的省份名称转换回原始名称"""
    name = str(name).strip()
    return REVERSE_PROVINCE_NAME_MAP.get(name, name)

# 应用初始化
if __name__ == '__main__':
    # 加载数据
    DataLoader.load_all_data()
    app.run(debug=True)