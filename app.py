from flask import Flask, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '中国大学数据集.db')

@app.route('/')
def index():
    """主页路由"""
    return render_template('index.html')  # 确保 templates 文件夹中有 index.html 文件

@app.route('/get_province_data')
def get_province_data():
    """统计 universities 表中省市列的数据"""
    if not os.path.exists(DATABASE_PATH):
        return jsonify({"error": "数据库文件不存在"}), 500

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        query = "SELECT 省市, COUNT(*) as 数量 FROM universities GROUP BY 省市"
        cursor.execute(query)
        data = [{"name": row[0], "value": row[1]} for row in cursor.fetchall()]
        conn.close()
        return jsonify(data)
    except sqlite3.Error as e:
        return jsonify({"error": f"数据库查询失败: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)