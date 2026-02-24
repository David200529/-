import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

# 1. 定义车站列表 (严格按照你的顺序)
stations = [
    "北京南", "廊坊", "天津南", "沧州西", "德州东", "济南西",
    "泰安", "曲阜东", "滕州东", "枣庄", "徐州东", "宿州东",
    "蚌埠南", "定远", "滁州", "南京南", "镇江南", "丹阳北",
    "常州北", "无锡东", "苏州北", "昆山南", "上海虹桥", "上海"
]

base_url = 'https://www.crecc.com/search/station/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 存放所有车站 DataFrame 的列表
all_frames = []

print("🚀 开始批量爬取京沪高铁沿线车站数据...")

# 2. 循环爬取每个车站
for station in stations:
    try:
        print(f"正在抓取: {station}...", end=" ")
        response = requests.get(base_url, params={'name': station}, headers=headers, timeout=10)
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')

        if table:
            # 提取表格数据
            rows = table.find_all('tr')
            table_data = []
            for row in rows:
                cols = [ele.text.strip() for ele in row.find_all(['th', 'td'])]
                if cols:
                    table_data.append(cols)

            # 转换为 DataFrame
            df_temp = pd.DataFrame(table_data[1:], columns=table_data[0])

            # --- 数据清洗步骤 ---
            # A. 新开一列“当前车站”，填充车站名
            df_temp['当前车站'] = station

            # B. 只保留“车次”列以“G”开头的行
            # 注意：如果列名不叫“车次”，请根据实际网页表头微调
            if '车次' in df_temp.columns:
                df_temp = df_temp[df_temp['车次'].str.startswith('G', na=False)].copy()

                # C. 新开一列“车次数字”，去掉首字符“G”
                df_temp['车次数字'] = df_temp['车次'].str[1:]

            all_frames.append(df_temp)
            print(f"完成 (获取到 {len(df_temp)} 条G字头记录)")
        else:
            print(f"跳过 (未找到表格)")

        # 适当休眠，保护对方服务器，也是保护自己的IP
        time.sleep(1)

    except Exception as e:
        print(f"出错: {station} - {e}")

# 3. 合并所有数据
if all_frames:
    print("\n📊 正在合并数据并导出...")
    final_df = pd.concat(all_frames, axis=0, ignore_index=True)

    # 4. 保存到指定路径
    save_path = r"E:\desktop\铁路研究\京沪高铁运行可视化\京沪高铁沿线车站时刻表_python爬取.xlsx"

    # 检查文件夹是否存在，不存在则创建
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    final_df.to_excel(save_path, index=False)
    print(f"✨ 大功告成！文件已保存至:\n{save_path}")
else:
    print("❌ 未抓取到任何有效数据，请检查网络或网站结构。")