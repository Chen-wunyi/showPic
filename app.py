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

# 讀取 CSV 數據到記憶體中
rows_data = []
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows_data.append(row)

os.makedirs('static', exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>PFAS 鏡像質譜比對檢視器</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; text-align: center; }
        .container { max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        form { margin: 20px 0; }
        input[type="number"] { padding: 8px; width: 80px; font-size: 16px; border: 1px solid #ccc; border-radius: 5px; text-align: center; }
        button { padding: 9px 20px; font-size: 16px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .gallery { display: flex; flex-direction: column; align-items: center; margin-top: 20px; }
        .plot-card { background: #fff; border: 1px solid #e1e4e8; border-radius: 8px; margin-bottom: 20px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); width: 100%; }
        img { max-width: 100%; height: auto; border-radius: 5px; }
        .error-box { color: red; background: #ffe6e6; padding: 15px; border-radius: 5px; text-align: left; white-space: pre-wrap; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>PFAS 模型重訓練鏡像質譜比對</h1>
        <p>輸入您想隨機檢視的分子數量（1 ~ 20），點擊送出即可產生對比圖：</p>
        
        <form method="POST">
            <label for="n_count">數量 (n)：</label>
            <input type="number" id="n_count" name="n_count" value="{{ n_value }}" min="1" max="20" required>
            <button type="submit">送出</button>
        </form>

        {% if error_message %}
            <div class="error-box"><strong>發生錯誤：</strong><br>{{ error_message }}</div>
        {% endif %}

        <div class="gallery">
            {% for img in images %}
                <div class="plot-card">
                    <img src="{{ img }}" alt="Mirror Mass Spectrum">
                </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    images = []
    n_value = 5
    error_message = None
    
    if rows_data and request.method == 'POST':
        try:
            n_value = int(request.form.get('n_count', 5))
            n_value = max(1, min(n_value, 20))
            
            selected_rows = random.sample(rows_data, min(n_value, len(rows_data)))
            
            for row in selected_rows:
                molecule_id = row.get('分子編號', 'Unknown')
                mz_old, int_old = [], []
                mz_new, int_new = [], []
                
                for i in range(1, 11):
                    try:
                        mz_o_val = row.get(f'第{i}大峰_m/z(舊)') or 0
                        int_o_val = row.get(f'第{i}大峰_強度(舊)') or 0
                        mz_n_val = row.get(f'第{i}大峰_m/z(新)') or 0
                        int_n_val = row.get(f'第{i}大峰_強度(新)') or 0
                        
                        mz_o = float(mz_o_val)
                        int_o = float(int_o_val)
                        mz_n = float(mz_n_val)
                        int_n = float(int_n_val)
                        
                        if int_o > 0:
                            mz_old.append(mz_o)
                            int_old.append(int_o)
                        if int_n > 0:
                            mz_new.append(mz_n)
                            int_n.append(int_n)
                    except (ValueError, TypeError):
                        pass
                
                # 建立畫布
                fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
                
                # 使用純 vlines 繪製，不呼叫 plt.plot 圓點，避開 Python 3.14 深層複製錯誤
                ax.vlines(mz_old, 0, int_old, color='royalblue', linewidth=2)
                ax.vlines(mz_new, 0, [-val for val in int_new], color='crimson', linewidth=2)
                    
                ax.axhline(0, color='black', linewidth=0.8)
                ax.set_title(f'Molecule: {molecule_id}', fontsize=10, fontweight='bold')
                ax.set_xlabel('m/z', fontsize=9)
                ax.set_ylabel('Intensity (%)', fontsize=9)
                ax.set_ylim(-110, 110)
                ax.grid(True, linestyle='--', alpha=0.3)
                
                img_path = f'static/{molecule_id}_{random.randint(1000,9999)}.png'
                fig.savefig(img_path, bbox_inches='tight')
                plt.close(fig)
                images.append(img_path)
        except Exception as e:
            error_message = traceback.format_exc()
            
    return render_template_string(HTML_TEMPLATE, images=images, n_value=n_value, error_message=error_message)

if __name__ == '__main__':
    app.run(debug=True)