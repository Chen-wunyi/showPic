import numpy as np
import pandas as pd

# 1. 讀取 CSV 檔案
df = pd.read_csv('pfas_top10_peaks_(p1_p1216).csv')

# 參數設定
INTENSITY_POWER = 0.5
MZ_POWER = 2.0
MS2_TOLERANCE = 0.02  # 0.02 Da 截斷條件

cosine_similarities = []

for idx, row in df.iterrows():
  mz_old_list, int_old_list = [], []
  mz_new_list, int_new_list = [], []

  # 收集第1到第10大峰的資料（只收集強度大於0的有效峰）
  for i in range(1, 11):
    mz_o = float(row.get(f'第{i}大峰_m/z(舊)', 0) or 0)
    int_o = float(row.get(f'第{i}大峰_強度(舊)', 0) or 0)
    mz_n = float(row.get(f'第{i}大峰_m/z(新)', 0) or 0)
    int_n = float(row.get(f'第{i}大峰_強度(新)', 0) or 0)

    if int_o > 0:
      mz_old_list.append(mz_o)
      int_old_list.append(int_o)
    if int_n > 0:
      mz_new_list.append(mz_n)
      int_new_list.append(int_n)

  if not mz_old_list or not mz_new_list:
    cosine_similarities.append(0.0)
    continue

  # Match 邏輯：0.02 Da 容差與一對一配對
  matches = []
  query_matched = set()

  for l_idx, mz_l in enumerate(mz_old_list):
    best_q_idx = None
    min_diff = float('inf')
    for q_idx, mz_q in enumerate(mz_new_list):
      if q_idx in query_matched:
        continue
      diff = abs(mz_q - mz_l)
      if diff <= MS2_TOLERANCE and diff < min_diff:
        min_diff = diff
        best_q_idx = q_idx
    if best_q_idx is not None:
      matches.append((best_q_idx, l_idx))
      query_matched.add(best_q_idx)

  if not matches:
    cosine_similarities.append(0.0)
    continue

  # 計算加權值 (W = intensity^0.5 * mz^2.0)
  def calc_weights(mz_arr, int_arr):
    mz = np.array(mz_arr, dtype=float)
    intensity = np.array(int_arr, dtype=float)
    return (intensity**INTENSITY_POWER) * (mz**MZ_POWER)

  new_weights = calc_weights(mz_new_list, int_new_list)
  old_weights = calc_weights(mz_old_list, int_old_list)

  # 計算加權 Cosine Similarity
  # 分子：只加總成功 match 的峰權積
  numerator = 0.0
  for q_idx, l_idx in matches:
    numerator += new_weights[q_idx] * old_weights[l_idx]

  # 分母：只計算「實際有效峰」的權重平方和，不受空白或補零影響
  new_sum = np.sum(new_weights**2)
  old_sum = np.sum(old_weights**2)
  denominator = np.sqrt(new_sum * old_sum)

  if denominator == 0:
    score = 0.0
  else:
    score = numerator / denominator

  cosine_similarities.append(round(score, 6))

# 將結果存入新欄位與新檔案
df['Weighted_Cosine_Similarity'] = cosine_similarities
df.to_csv(
    'pfas_top10_peaks_with_weighted_cosine.csv', index=False, encoding='utf-8-sig'
)
print('已成功以修正後的有效峰分母計算加權 Cosine Similarity，並儲存至 pfas_top10_peaks_with_weighted_cosine.csv！')