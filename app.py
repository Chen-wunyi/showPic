import csv
import os
import random
import traceback
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template_string, request

app = Flask(__name__)

CSV_FILE = 'pfas_top10_peaks_sorted_by_dot_product.csv'

# 讀取 CSV 數據：將每個分子的低、中、高能量資料分門別類存入字典
molecules_data = {}
if os.path.exists(CSV_FILE):
  with open(CSV_FILE, mode='r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
      mol_id = row.get('分子編號')
      energy_lvl = row.get('能量級別')  # 低能量/中能量/高能量
      if mol_id:
        mol_key = mol_id.strip().upper()
        if mol_key not in molecules_data:
          molecules_data[mol_key] = {}
        if energy_lvl:
          molecules_data[mol_key][energy_lvl] = row

os.makedirs('static', exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>PFAS 多分子質譜比對與分數檢視器</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; text-align: center; }
        .container { max-width: 1150px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        form { margin: 20px 0; }
        textarea { padding: 8px; width: 400px; height: 90px; font-size: 14px; border: 1px solid #ccc; border-radius: 5px; text-align: left; vertical-align: middle; }
        .btn-group { margin-top: 10px; }
        button { padding: 9px 20px; font-size: 16px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 0 5px; }
        button:hover { background-color: #0056b3; }
        .btn-preset { background-color: #6c757d; }
        .btn-preset:hover { background-color: #5a6268; }
        .molecule-row { background: #fff; border: 1px solid #e1e4e8; border-radius: 8px; margin-bottom: 30px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
        .molecule-title { font-size: 20px; font-weight: bold; color: #0056b3; margin-bottom: 15px; text-align: left; border-bottom: 2px solid #007bff; padding-bottom: 5px; }
        .plots-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
        .plot-item img { max-width: 100%; height: auto; border-radius: 5px; border: 1px solid #ddd; }
        .plot-item p { font-size: 14px; font-weight: bold; color: #444; margin: 5px 0; }
        .score-box { font-size: 13px; color: #666; margin-top: 4px; background: #f8f9fa; padding: 6px; border-radius: 4px; }
        .error-box { color: red; background: #ffe6e6; padding: 15px; border-radius: 5px; text-align: left; white-space: pre-wrap; margin-top: 20px; }
    </style>
    <script>
        function loadPreset(type) {
            let lowArr = ["P_64", "P_137", "P_141", "P_319", "P_388", "P_496", "P_776", "P_869", "P_925", "P_1174"];
            let highArr = ["P_1155", "P_1164", "P_1180", "P_1190", "P_1193", "P_1201", "P_1202"];
            let textarea = document.getElementById("mol_query");
            if (type === 'low') {
                textarea.value = lowArr.join("\\n");
            } else if (type === 'high') {
                textarea.value = highArr.join("\\n");
            }
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>PFAS 模型重訓練 - 多分子多能量鏡像檢視器</h1>
        <p>請輸入多個分子編號（可以換行、空格或逗號隔開），或點擊下方按鈕直接載入預設清單：</p>
        
        <form method="POST">
            <div>
                <textarea id="mol_query" name="mol_query" placeholder="例如: P_64 P_137 或直接換行貼上">{{ query_raw }}</textarea>
            </div>
            <div class="btn-group">
                <button type="submit">查詢</button>
                <button type="button" class="btn-preset" onclick="loadPreset('low')">Load Data (Low)</button>
                <button type="button" class="btn-preset" onclick="loadPreset('high')">Load Data (High)</button>
            </div>
        </form>

        {% if error_message %}
            <div class="error-box"><strong>提示訊息：</strong><br>{{ error_message }}</div>
        {% endif %}

        <div class="gallery">
            {% for item in results %}
                <div class="molecule-row">
                    <div class="molecule-title">分子編號: {{ item.mol_id }}</div>
                    <div class="plots-grid">
                        <!-- 低能量 -->
                        <div class="plot-item">
                            <p>低能量 (Low)</p>
                            {% if item.low_img %}
                                <img src="{{ item.low_img }}" alt="Low Energy">
                                <div class="score-box">
                                    Dot: {{ item.low_dot }}<br>
                                    Cosine: {{ item.low_cos }}
                                </div>
                            {% else %}
                                <p style="color: #999;">無此能量資料</p>
                            {% endif %}
                        </div>
                        <!-- 中能量 -->
                        <div class="plot-item">
                            <p>中能量 (Medium)</p>
                            {% if item.med_img %}
                                <img src="{{ item.med_img }}" alt="Medium Energy">
                                <div class="score-box">
                                    Dot: {{ item.med_dot }}<br>
                                    Cosine: {{ item.med_cos }}
                                </div>
                            {% else %}
                                <p style="color: #999;">無此能量資料</p>
                            {% endif %}
                        </div>
                        <!-- 高能量 -->
                        <div class="plot-item">
                            <p>高能量 (High)</p>
                            {% if item.high_img %}
                                <img src="{{ item.high_img }}" alt="High Energy">
                                <div class="score-box">
                                    Dot: {{ item.high_dot }}<br>
                                    Cosine: {{ item.high_cos }}
                                </div>
                            {% else %}
                                <p style="color: #999;">無此能量資料</p>
                            {% endif %}
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
  query_raw = ''
  error_message = None

  if request.method == 'POST':
    try:
      query_raw = request.form.get('mol_query', '').strip()
      # 更強健的切割方式：以換行、逗號或空白分割
      raw_lines = query_raw.replace(',', '\n').split('\n')
      mol_ids = [line.strip().upper() for line in raw_lines if line.strip()]
      mol_ids = list(dict.fromkeys(mol_ids))  # 去重但保持順序

      if not mol_ids:
        error_message = '請至少輸入一個有效的分子編號。'

      not_found = []
      for query_id in mol_ids:
        if query_id not in molecules_data:
          not_found.append(query_id)
          continue

        mol_dict = molecules_data[query_id]
        img_paths = {}
        energy_keys = [('低能量', 'low'), ('中能量', 'medium'), ('高能量', 'high')]

        for cn_key, en_key in energy_keys:
          row = mol_dict.get(cn_key)
          if not row:
            continue

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

          dot_val = row.get('Dot_Product', 'N/A')
          cos_val = row.get('Weighted_Cosine_Similarity', 'N/A')
          try:
            dot_val = f'{float(dot_val):.2f}'
          except:
            pass
          try:
            cos_val = f'{float(cos_val):.4f}'
          except:
            pass

          fig, ax = plt.subplots(figsize=(4, 2.5), dpi=120)
          if mz_old:
            ax.vlines(mz_old, 0, int_old, color='royalblue', linewidth=1.5)
          if mz_new:
            ax.vlines(
                mz_new,
                0,
                [-val for val in int_new],
                color='crimson',
                linewidth=1.5,
            )

          ax.axhline(0, color='black', linewidth=0.7)
          ax.set_xlabel('m/z', fontsize=8)
          ax.set_ylabel('Intensity (%)', fontsize=8)
          ax.set_ylim(-110, 110)
          ax.grid(True, linestyle='--', alpha=0.3)

          img_path = (
              f'static/{query_id}_{en_key}_{random.randint(1000,9999)}.png'
          )
          fig.savefig(img_path, bbox_inches='tight')
          plt.close(fig)

          img_paths[en_key] = {
              'img': img_path,
              'dot': dot_val,
              'cos': cos_val,
          }

        results.append({
            'mol_id': query_id,
            'low_img': img_paths.get('low', {}).get('img', ''),
            'low_dot': img_paths.get('low', {}).get('dot', ''),
            'low_cos': img_paths.get('low', {}).get('cos', ''),
            'med_img': img_paths.get('medium', {}).get('img', ''),
            'med_dot': img_paths.get('medium', {}).get('dot', ''),
            'med_cos': img_paths.get('medium', {}).get('cos', ''),
            'high_img': img_paths.get('high', {}).get('img', ''),
            'high_dot': img_paths.get('high', {}).get('dot', ''),
            'high_cos': img_paths.get('high', {}).get('cos', ''),
        })

      if not results and not error_message:
        error_message = (
            '找不到您輸入的任何分子編號，請確認編號是否正確（例如 P_64）。'
        )
      elif not_found:
        error_message = f'注意：以下分子編號在資料庫中找不到：{", ".join(not_found)}'

    except Exception as e:
      error_message = traceback.format_exc()

  return render_template_string(
      HTML_TEMPLATE,
      results=results,
      query_raw=query_raw,
      error_message=error_message,
  )


if __name__ == '__main__':
  app.run(debug=True)