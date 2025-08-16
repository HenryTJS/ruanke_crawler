from flask import Flask, request, jsonify, render_template
import pandas as pd

app = Flask(__name__)

# 加载数据
df = pd.read_excel('中国大学表.xlsx')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_options')
def get_options():
    property_set = set()
    if '院校归属' in df.columns:
        property_set.update(df['院校归属'].dropna().unique().tolist())
    if '院校特色' in df.columns:
        df['院校特色'].dropna().apply(
            lambda x: [property_set.add(i.strip()) for i in str(x).split('/') if i.strip()]
        )
    if '办学层次' in df.columns:
        property_set.update(df['办学层次'].dropna().unique().tolist())
    options = {
        "province": sorted(df['所在省份'].dropna().unique().tolist()),
        "property": sorted(property_set),
        "type": sorted(df['院校类型'].dropna().unique().tolist())
    }
    return jsonify(options)

@app.route('/get_chart_data', methods=['POST'])
def get_chart_data():
    data = request.json
    selected_provinces = data.get('province', [])
    selected_properties = data.get('property', [])
    selected_types = data.get('type', [])

    filtered_df = df.copy()
    if selected_provinces:
        filtered_df = filtered_df[filtered_df['所在省份'].isin(selected_provinces)]
    if selected_properties:
        def has_property(row):
            props = set()
            if '院校归属' in df.columns and pd.notna(row['院校归属']):
                props.add(row['院校归属'])
            if '办学层次' in df.columns and pd.notna(row['办学层次']):
                props.add(row['办学层次'])
            if '院校特色' in df.columns and pd.notna(row['院校特色']):
                props.update([i.strip() for i in str(row['院校特色']).split('/') if i.strip()])
            return any(p in props for p in selected_properties)
        filtered_df = filtered_df[filtered_df.apply(has_property, axis=1)]
    if selected_types:
        filtered_df = filtered_df[filtered_df['院校类型'].isin(selected_types)]

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
    total_count = len(filtered_df)
    return jsonify({
        "chart_data": pie_data,
        "bar_data": bar_data,
        "total_count": total_count
    })

@app.route('/get_overview', methods=['POST'])
def get_overview():
    data = request.json or {}
    selected_provinces = data.get('province', [])
    selected_properties = data.get('property', [])
    selected_types = data.get('type', [])

    filtered_df = df.copy()
    if selected_provinces:
        filtered_df = filtered_df[filtered_df['所在省份'].isin(selected_provinces)]
    if selected_properties:
        def has_property(row):
            props = set()
            if '院校归属' in df.columns and pd.notna(row['院校归属']):
                props.add(row['院校归属'])
            if '办学层次' in df.columns and pd.notna(row['办学层次']):
                props.add(row['办学层次'])
            if '院校特色' in df.columns and pd.notna(row['院校特色']):
                props.update([i.strip() for i in str(row['院校特色']).split('/') if i.strip()])
            return any(p in props for p in selected_properties)
        filtered_df = filtered_df[filtered_df.apply(has_property, axis=1)]
    if selected_types:
        filtered_df = filtered_df[filtered_df['院校类型'].isin(selected_types)]

    # 统计数据
    total_count = len(filtered_df)
    benke_count = len(filtered_df[filtered_df['办学层次'] == '普通本科'])
    num_985 = filtered_df['院校特色'].dropna().apply(lambda x: '985' in str(x).split('/')).sum()
    num_211 = filtered_df['院校特色'].dropna().apply(lambda x: '211' in str(x).split('/')).sum()
    num_doubletop = filtered_df['院校特色'].dropna().apply(lambda x: '双一流' in str(x).split('/')).sum()

    return jsonify({
        'total': int(total_count),
        'benke': int(benke_count),
        '985': int(num_985),
        '211': int(num_211),
        'doubletop': int(num_doubletop)
    })

if __name__ == '__main__':
    app.run(debug=True)