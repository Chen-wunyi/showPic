import os
import random
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template_string, request

app = Flask(__name__)

# 讀取您的比對資料 CSV
CSV_FILE = 'pfas_top10_peaks_comparison_msp_to_msp_test.csv'
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = None

os.makedirs('static', exist_ok=True)

# 內嵌的網頁前端 HTML 畫面
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
    </style>
</head>
<body>
    <div class="container">
        <h1>PFAS 模型重訓練鏡像質譜比對</h1>
        <p>輸入您想隨機檢視的分子數量（1 ~ 20），點擊送出即可產生對比圖：</p>
        
        <form method="POST">
            <label for="n_count">數量 (n)：</label>
            <input type="number" id="n_count" name="n_count" value="{{ n_value }}" min="1" max="20" required>
            <button type="submit">隨機產生圖表</button>
        </form>

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
    
    if df is not None and request.method == 'POST':
        try:
            n_value = int(request.form.get('n_count', 5))
        except ValueError:
            n_value = 5
        n_value = max(1, min(n_value, 20))
        
        selected_rows = df.sample(n=min(n_value, len(df)))
        
        for idx, row in selected_rows.iterrows():
            molecule_id = row['分子編號']
            mz_old, int_old = [], []
            mz_new, int_new = [], []
            
            for i in range(1, 11):
                mz_o = row[f'第{i}大峰_m/z(舊)']
                int_o = row[f'第{i}大峰_強度(舊)']
                mz_n = row[f'第{i}大峰_m/z(新)']
                int_n = row[f'第{i}大峰_強度(新)']
                
                if not pd.isna(mz_o) and int_o > 0:
                    mz_old.append(mz_o)
                    int_old.append(int_o)
                if not pd.isna(mz_n) and int_n > 0:
                    mz_new.append(mz_n)
                    int_new.append(int_n)
            
            plt.figure(figsize=(8, 4), dpi=150)
            for m, intensity in zip(mz_old, int_old):
                plt.vlines(m, 0, intensity, color='royalblue', linewidth=1.5)
                plt.plot(m, intensity, 'o', color='royalblue', markersize=4)
            for m, intensity in zip(mz_new, int_new):
                plt.vlines(m, 0, -intensity, color='crimson', linewidth=1.5)
                plt.plot(m, -intensity, 'o', color='crimson', markersize=4)
                
            plt.axhline(0, color='black', linewidth=0.8)
            plt.title(f'Molecule: {molecule_id}', fontsize=10, fontweight='bold')
            plt.xlabel('m/z', fontsize=9)
            plt.ylabel('Intensity (%)', fontsize=9)
            plt.yticks([-100, -50, 0, 50, 100], ['100', '50', '0', '50', '100'])
            plt.ylim(-110, 110)
            plt.grid(True, linestyle='--', alpha=0.3)
            plt.tight_layout()
            
            img_path = f'static/{molecule_id}_{random.randint(1000,9999)}.png'
            plt.savefig(img_path)
            plt.close()
            images.append(img_path)
            
    return render_template_string(HTML_TEMPLATE, images=images, n_value=n_value)

if __name__ == '__main__':
    app.run(debug=True)