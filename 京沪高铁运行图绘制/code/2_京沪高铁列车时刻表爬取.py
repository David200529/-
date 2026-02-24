import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re

# 1. 设置路径
base_path = r"E:\desktop\铁路研究\京沪高铁运行可视化"
source_file = os.path.join(base_path, "京沪高铁沿线车站时刻表_python爬取.xlsx")
output_file = os.path.join(base_path, "京沪高铁全线列车时刻表_各列车经停站.xlsx")

# 2. 读取之前保存的车站总表，提取不重复的车次数字
try:
    source_df = pd.read_excel(source_file)
    # 提取“车次数字”列，去重，转为字符串列表
    train_numbers = source_df['车次数字'].astype(str).unique().tolist()
    print(f"✅ 成功读取源文件，共发现 {len(train_numbers)} 个不重复的车次。")
except Exception as e:
    print(f"🚨 读取源文件失败: {e}")
    train_numbers = []

# 3. 准备循环爬取
all_details = []
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

for num in train_numbers:
    # 构造 URL (例如 g1.html, g2.html)
    url = f"https://www.crecc.com/huoche/g{num}.html"
    try:
        print(f"正在爬取车次 G{num} ...", end=" ")
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'

        # 使用 pandas 直接读取网页中的所有表格
        # [0]通常是基本信息，[1]通常是我们要的详细时刻表
        tables = pd.read_html(response.text)

        # 寻找包含“到达时间”关键词的那个表格
        target_df = None
        for df in tables:
            if '到达时间' in df.columns or '发车时间' in df.columns:
                target_df = df
                break

        if target_df is not None:
            # --- 数据清洗 ---
            # A. 添加所属车次列
            target_df['所属车次'] = f"G{num}"


            # B. 清洗“到达时间”和“发车时间” (只保留 00:00 格式)
            # 使用正则表达式提取：匹配两位数字:两位数字
            def clean_time(text):
                if pd.isna(text): return text
                match = re.search(r'\d{2}:\d{2}', str(text))
                return match.group(0) if match else text


            if '到达时间' in target_df.columns:
                target_df['到达时间'] = target_df['到达时间'].apply(clean_time)
            if '发车时间' in target_df.columns:
                target_df['发车时间'] = target_df['发车时间'].apply(clean_time)

            # C. 清洗“停留时间” (去掉“分钟”二字)
            if '停留时间' in target_df.columns:
                target_df['停留时间'] = target_df['停留时间'].astype(str).str.replace('分钟', '', regex=False)

            all_details.append(target_df)
            print(f"成功 (获取到 {len(target_df)} 站)")
        else:
            print("未找到时刻表表格")

        # 频率控制：抓取很快，稍微歇一下避免被封
        time.sleep(0.5)

    except Exception as e:
        print(f"失败 (G{num}): {e}")

# 4. 合并并最终保存
if all_details:
    final_big_df = pd.concat(all_details, axis=0, ignore_index=True)

    # 再次确保输出目录存在
    os.makedirs(base_path, exist_ok=True)

    final_big_df.to_excel(output_file, index=False)
    print(f"\n✨【大功告成】✨")
    print(f"所有车次详细数据已合并并清洗完毕！")
    print(f"保存路径: {output_file}")
else:
    print("\n❌ 未能抓取到任何详情数据。")