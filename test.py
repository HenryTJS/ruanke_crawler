import json
import pandas as pd

with open('static/json/bcmr.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    df = pd.read_json(data)  
    print(df)