import os
import random
import csv
import traceback
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template_string, request

app = Flask(__name__)

CSV_FILE = 'pfas_top10_peaks_comparison_msp_to_msp_test.csv'

# 讀取 CSV 數據：將每個分子的低、中、高能量資料分門別類存入字典
# 結構: { 'P_1': { '低能量': {row}, '中能量': {row}, '高能量': {row} }, ... }
molecules_data = {}
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mol_id = row.get('分子編號')
            energy_lvl = row.get('能量級別') # 假設 CSV 內有名為「能量級別」的欄位 (低能量/中能量/高能量)
            if mol_id:
                if mol_id not in molecules_data:
                    molecules_data[mol_id] = {}
                if energy_lvl:
                    molecules_data[mol_id][energy_lvl] = row

os.makedirs('static', exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>PFAS 三種能量鏡像質譜比對檢視器</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; text-align: center; }
        .container { max-width: 1100px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        form { margin: 20px 0; }
        input[type="number"] { padding: 8px; width: 80px; font-size: 16px; border: 1px solid #ccc; border-radius: 5px; text-align: center; }
        button { padding: 9px 20px; font-size: 16px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .molecule-row { background: #fff; border: 1px solid #e1e4e8; border-radius: 8px; margin-bottom: 30px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
        .molecule-title { font-size: 18px; font-weight: bold; color: #0056b3; margin-bottom: 15px; text-align: left; border-bottom: 2px solid #007bff; padding-bottom: 5px; }
        .plots-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
        .plot-item img { max-width: 100%; height: auto; border-radius: 5px; border: 1px solid #ddd; }
        .plot-item p { font-size: 14px; font-weight: bold; color: #444; margin: 5px 0; }
        .error-box { color: red; background: #ffe6e6; padding: 15px; border-radius: 5px; text-align: left; white-space: pre-wrap; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>PFAS 模型重訓練 - 低中高能量鏡像質譜比對</h1>
        <p>輸入您想隨機檢視的分子數量（1 ~ 20），系統將為每個分子並排呈現「低、中、高」三種能量對比圖：</p>
        
        <form method="POST">
            <label for="n_count">分子數量 (n)：</label>
            <input type="number" id="n_count" name="n_count" value="{{ n_value }}" min="1" max="20" required>
            <button type="submit">送出</button>
        </form>

        {% if error_message %}
            <div class="error-box"><strong>發生錯誤：</strong><br>{{ error_message }}</div>
        {% endif %}

        <div class="gallery">
            {% for item in results %}
                <div class="molecule-row">
                    <div class="molecule-title">分子編號: {{ item.mol_id }}</div>
                    <div class="plots-grid">
                        <div class="plot-item">
                            <p>低能量 (Low)</p>
                            <img src="{{ item.low_img }}" alt="Low Energy">
                        </div>
                        <div class="plot-item">
                            <p>中能量 (Medium)</p>
                            <img src="{{ item.med_img }}" alt="Medium Energy">
                        </div>
                        <div class="plot-item">
                            <p>高能量 (High)</p>
                            <img src="{{ item.high_img }}" alt="High Energy">
                        </div>
                    </div>
                </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    n_value = 3
    error_message = None
    
    if molecules_data and request.method == 'POST':
        try:
            n_value = int(request.form.get('n_count', 3))
            n_value = max(1, min(n_value, 20))
            
            # 隨機挑選 n 個分子
            available_mol_ids = list(molecules_data.keys())
            selected_mols = random.sample(available_mol_ids, min(n_value, len(available_mol_ids)))
            
            for mol_id in selected_mols:
                mol_dict = molecules_data[mol_id]
                
                img_paths = {}
                energy_keys = [('低能量', 'low'), ('中能量', 'medium'), ('高能量', 'high')]
                
                for cn_key, en_key in energy_keys:
                    row = mol_dict.get(cn_key, {})
                    mz_old, int_old = [], []
                    mz_new, int_new = [], []
                    
                    for i in range(1, 11):
                        try:
                            mz_o = float(row.get(f'第{i}大峰_m/z(舊)', 0) or 0)
                            int_o = float(row.get(f'第{i}大峰_強度(舊)', 0) or 0)
                            mz_n = float(row.get(f'第{i}大峰_m/z(新)', 0) or 0)
                            int_n = float(row.get(f'第{i}大峰_強度(新)', 0) or 0)
                            
                            if int_o > 0:
                                mz_old.append(mz_o)
                                int_old.append(int_o)
                            if int_n > 0:
                                mz_new.append(mz_n)
                                int_new.append(int_n)
                        except (ValueError, TypeError):
                            pass
                    
                    # 畫圖
                    fig, ax = plt.subplots(figsize=(4, 2.5), dpi=120)
                    if mz_old:
                        ax.vlines(mz_old, 0, int_old, color='royalblue', linewidth=1.5)
                    if mz_new:
                        ax.vlines(mz_new, 0, [-val for val in int_new], color='crimson', linewidth=1.5)
                        
                    ax.axhline(0, color='black', linewidth=0.7)
                    ax.set_xlabel('m/z', fontsize=8)
                    ax.set_ylabel('Intensity (%)', fontsize=8)
                    ax.set_ylim(-110, 110)
                    ax.grid(True, linestyle='--', alpha=0.3)
                    
                    img_path = f'static/{mol_id}_{en_key}_{random.randint(1000,9999)}.png'
                    fig.savefig(img_path, bbox_inches='tight')
                    plt.close(fig)
                    img_paths[en_key] = img_path
                
                results.append({
                    'mol_id': mol_id,
                    'low_img': img_paths.get('low', ''),
                    'med_img': img_paths.get('medium', ''),
                    'high_img': img_paths.get('high', '')
                })
        except Exception as e:
            error_message = traceback.format_exc()
            
    return render_template_string(HTML_TEMPLATE, results=results, n_value=n_value, error_message=error_message)

if __name__ == '__main__':
    app.run(debug=True)