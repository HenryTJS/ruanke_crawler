import json
import psycopg2
from psycopg2 import sql
from psycopg2 import extras
import pandas as pd

# ========== 数据库连接配置（请修改为您的实际参数）==========
DB_CONFIG = {
    "dbname": "bcmr",
    "user": "postgres",
    "password": "2022S3414ycx",
    "host": "localhost",
    "port": 5432
}

# ========== 建表 SQL（仅核心表）==========
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS hierarchy_node (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(50) NOT NULL,
    name        VARCHAR(200) NOT NULL,
    parent_id   INTEGER REFERENCES hierarchy_node(id) ON DELETE CASCADE,
    UNIQUE(code, name, parent_id)
);

CREATE TABLE IF NOT EXISTS hierarchy_node_year (
    id          SERIAL PRIMARY KEY,
    node_id     INTEGER NOT NULL REFERENCES hierarchy_node(id) ON DELETE CASCADE,
    year        INTEGER NOT NULL,
    UNIQUE(node_id, year)
);
"""

# ========== 插入节点（存在则返回已有ID）==========
INSERT_NODE_SQL = """
INSERT INTO hierarchy_node (code, name, parent_id)
VALUES (%s, %s, %s)
ON CONFLICT (code, name, parent_id) DO UPDATE SET code = EXCLUDED.code
RETURNING id;
"""

# ========== 插入年份（忽略重复）==========
INSERT_YEAR_SQL = """
INSERT INTO hierarchy_node_year (node_id, year)
VALUES (%s, %s)
ON CONFLICT DO NOTHING;
"""


def init_database():
    """
    确保目标数据库存在；若存在则清空所有表并重建核心表。
    """
    cfg = DB_CONFIG
    dbname = cfg['dbname']

    # 连接默认维护数据库（如 postgres）
    default_cfg = cfg.copy()
    default_cfg['dbname'] = 'postgres'  # 也可用 'template1'
    conn = psycopg2.connect(**default_cfg)
    conn.autocommit = True
    cur = conn.cursor()

    # 检查目标数据库是否存在
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
    exists = cur.fetchone() is not None

    if not exists:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
        print(f"数据库 {dbname} 已创建。")
    cur.close()
    conn.close()

    # 连接到目标数据库，清空所有表
    conn = psycopg2.connect(**cfg)
    conn.autocommit = False
    cur = conn.cursor()

    # 获取 public 模式下所有普通表
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """)
    tables = [row[0] for row in cur.fetchall()]

    if tables:
        # 逐个删除（使用 CASCADE 级联删除依赖对象）
        for table in tables:
            cur.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(table)))
        print(f"已删除 {len(tables)} 张表。")

    # 重建核心表
    cur.execute(CREATE_TABLES_SQL)
    conn.commit()
    cur.close()
    conn.close()
    print("数据库初始化完成（hierarchy_node 和 hierarchy_node_year 已重建）。")


def process_node(cursor, parent_id, node_dict, child_key):
    """
    递归处理一个节点及其子节点
    :param cursor: 数据库游标
    :param parent_id: 父节点ID（根节点为 None）
    :param node_dict: 当前节点的字典，必须包含 'number', 'name'，可选 'year' 和 child_key
    :param child_key: 子节点列表的键名（如 'subfields', 'children' 等）
    """
    code = node_dict.get("number")
    name = node_dict.get("name")
    if not code or not name:
        print("警告：节点缺少 number 或 name，跳过", node_dict)
        return

    # 插入节点（如果已存在则返回已有id）
    cursor.execute(INSERT_NODE_SQL, (code, name, parent_id))
    node_id = cursor.fetchone()[0]

    # 处理当前节点的年份列表
    years = node_dict.get("year")
    if years and isinstance(years, list):
        for y in years:
            if isinstance(y, int):
                cursor.execute(INSERT_YEAR_SQL, (node_id, y))

    # 递归处理子节点
    children = node_dict.get(child_key, [])
    if isinstance(children, list):
        for child in children:
            process_node(cursor, node_id, child, child_key)


def import_json_to_db(json_file_path, child_key="subfields"):
    """
    主入口函数：读取JSON文件，递归导入数据库（假设表已存在）
    :param json_file_path: JSON文件路径
    :param child_key: JSON中代表子节点数组的键名（默认 'subfields'）
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 假设 JSON 最外层是一个数组，每个元素是一个根节点
    for root_node in data:
        process_node(cursor, None, root_node, child_key)

    conn.commit()
    cursor.close()
    conn.close()
    print(f"数据导入完成！文件：{json_file_path}，子节点键名：{child_key}")


def save_dataframe_to_db(df: pd.DataFrame, type_name: str, year: int, code: str = None, db_config: dict = None):
    """
    将 pandas DataFrame 保存到数据库，表名为 type_name_year（例如 bcvcr_2025）。
    所有列默认使用 TEXT 类型以兼容各种字段。
    :param df: 要保存的 DataFrame
    :param type_name: 类型名（如 'bcvcr'）
    :param year: 年份
    :param db_config: 可选的数据库配置字典，若为 None 则使用模块级 DB_CONFIG
    """
    cfg = db_config or DB_CONFIG
    # 表名以 type_year[_code] 命名，code 可选但推荐用于区分同类型的不同子代码
    table_name = f"{type_name}_{year}"
    if code is not None:
        table_name = f"{table_name}_{code}"

    # 列名和占位符
    columns = [str(c) for c in df.columns]
    if not columns:
        print("警告：DataFrame 无列，跳过写入")
        return

    # 构建建表语句（所有列 TEXT），使用 sql.Identifier 安全化列名
    col_parts = [sql.SQL("{} TEXT").format(sql.Identifier(col)) for col in columns]
    cols_sql = sql.SQL(', ').join(col_parts)
    create_sql = sql.SQL("CREATE TABLE IF NOT EXISTS {table} (id SERIAL PRIMARY KEY, {cols})").format(
        table=sql.Identifier(table_name), cols=cols_sql
    )

    # 插入语句
    cols_ident = sql.SQL(', ').join(map(sql.Identifier, columns))
    values_placeholders = sql.SQL(', ').join(sql.Placeholder() * len(columns))
    insert_sql = sql.SQL("INSERT INTO {table} ({cols}) VALUES ({vals})").format(
        table=sql.Identifier(table_name), cols=cols_ident, vals=values_placeholders
    )

    conn = psycopg2.connect(**cfg)
    cur = conn.cursor()
    cur.execute(create_sql)

    # 使用 execute_values 批量插入
    records = [tuple(map(lambda v: None if pd.isna(v) else str(v), row)) for row in df.itertuples(index=False, name=None)]
    if records:
        extras.execute_values(cur, sql.SQL("INSERT INTO {table} ({cols}) VALUES %s").format(
            table=sql.Identifier(table_name), cols=cols_ident
        ), records)

    conn.commit()
    cur.close()
    conn.close()
    print(f"已将 {len(records)} 条记录写入表 {table_name}。")


if __name__ == "__main__":
    # 1. 初始化数据库（若不存在则创建，若存在则清空所有表并重建核心表）
    init_database()

    # 2. 导入层级数据
    import_json_to_db("json/bcmr.json", child_key="subfields")