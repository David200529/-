import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import datetime
from tqdm import tqdm  # 导入进度条库

# --- 1. 参数配置区 ---
FILE_PATH = r"E:\desktop\铁路研究\京沪高铁运行可视化\京沪高铁全线列车时刻表_各列车经停站.xlsx"
SAVE_PATH = r"E:\desktop\铁路研究\京沪高铁运行可视化\京沪高铁动态运行图.gif"

FPS = 15
TIME_STEP = 60  # 60秒一帧，颗粒度极高
START_TIME = "04:00"
END_TIME = "23:59"
STAY_DURATION = 180

HUBS = ["北京南", "济南西", "南京南", "上海虹桥"]

STATIONS = {
    "北京南": 0, "廊坊": 60, "天津南": 124, "沧州西": 219, "德州东": 314,
    "济南西": 406, "泰安": 463, "曲阜东": 535, "滕州东": 591, "枣庄": 627,
    "徐州东": 692, "宿州东": 760, "蚌埠南": 844, "定远": 897, "滁州": 959,
    "南京南": 1023, "镇江南": 1088, "丹阳北": 1120, "常州北": 1153,
    "无锡东": 1210, "苏州北": 1236, "昆山南": 1267, "上海虹桥": 1318,
    "上海": 1360
}


def t2s(t):
    if pd.isna(t) or t == '----' or str(t).strip() == "": return None
    if isinstance(t, datetime.time): return t.hour * 3600 + t.minute * 60
    try:
        parts = str(t).split(':')
        return int(parts[0]) * 3600 + int(parts[1]) * 60
    except:
        return None


# --- 2. 数据准备 ---
print("正在装载全天数据...")
df = pd.read_excel(FILE_PATH)
df['arr_s'] = df['到达时间'].apply(t2s)
df['dep_s'] = df['发车时间'].apply(t2s)
phys_trains = df['车次'].unique()

# --- 3. 绘图与动画 ---
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
fig, ax = plt.subplots(figsize=(26, 12), dpi=80)

# 计算总帧数
total_frames = int((t2s(END_TIME) - t2s(START_TIME)) / TIME_STEP)

# 创建进度条对象
pbar = tqdm(total=total_frames, desc="[正在渲染京沪高铁运行图]", unit="帧")


def update(frame):
    ax.clear()
    curr_s = t2s(START_TIME) + frame * TIME_STEP
    curr_t_str = str(datetime.timedelta(seconds=curr_s))

    # 更新进度条
    pbar.update(1)

    ax.axhline(0, color='#333333', lw=2.5, alpha=0.6)

    for name, dist in STATIONS.items():
        is_hub = name in HUBS
        ax.axvline(dist, color='darkred' if is_hub else '#cccccc',
                   alpha=0.25 if is_hub else 0.1, lw=2 if is_hub else 1)
        ax.text(dist, -2.4, name, fontsize=13 if is_hub else 10,
                color='darkred' if is_hub else '#555555',
                fontweight='bold' if is_hub else 'normal',
                ha='center', va='top', rotation=90)

    # 底部图例
    leg_y = -3.8
    ax.scatter(150, leg_y, c='blue', s=70);
    ax.text(175, leg_y, "上行", fontsize=13, va='center')
    ax.scatter(350, leg_y, c='red', s=70);
    ax.text(375, leg_y, "下行", fontsize=13, va='center')
    ax.scatter(550, leg_y, c='#00FF00', s=70, edgecolors='#333333');
    ax.text(575, leg_y, "停站", fontsize=13, va='center')
    ax.scatter(750, leg_y, c='purple', s=80, marker='s');
    ax.text(775, leg_y, "终到", fontsize=13, va='center')

    occ = {s: 0 for s in STATIONS.keys()}
    term_occ = {s: 0 for s in STATIONS.keys()}

    for tid in phys_trains:
        t_data = df[df['车次'] == tid].sort_values('站次')
        main_line = t_data[t_data['车站'].isin(STATIONS.keys())]
        if main_line.empty: continue

        last_row = main_line.iloc[-1]
        term_sta = last_row['车站']
        term_time = last_row['arr_s'] if last_row['arr_s'] else last_row['dep_s']
        is_up = STATIONS.get(last_row['车站'], 0) < STATIONS.get(main_line.iloc[0]['车站'], 0)

        found = False
        for i in range(len(main_line)):
            row = main_line.iloc[i]
            if row['arr_s'] and row['dep_s'] and row['arr_s'] <= curr_s <= row['dep_s']:
                if i == len(main_line) - 1: break
                pos = STATIONS[row['车站']]
                count = occ[row['车站']]
                occ[row['车站']] += 1
                offset = (-0.45 if is_up else 0.45) * (1 + count * 0.35)
                ax.scatter(pos, offset, c='#00FF00', s=90, edgecolors='white', zorder=10)
                ax.text(pos, offset + (0.12 if not is_up else -0.25), tid,
                        fontsize=8.5, rotation=45, color='darkgreen', fontweight='bold', alpha=0.9)
                found = True;
                break

            if i < len(main_line) - 1:
                next_row = main_line.iloc[i + 1]
                if row['dep_s'] and next_row['arr_s'] and row['dep_s'] < curr_s < next_row['arr_s']:
                    ratio = (curr_s - row['dep_s']) / (next_row['arr_s'] - row['dep_s'])
                    pos = STATIONS[row['车站']] + (STATIONS[next_row['车站']] - STATIONS[row['车站']]) * ratio
                    offset = -0.9 if is_up else 0.9
                    ax.scatter(pos, offset, c='blue' if is_up else 'red', s=60, zorder=5, alpha=0.8)
                    ax.text(pos, offset + (0.12 if not is_up else -0.25), tid,
                            fontsize=8, rotation=45, alpha=0.7)
                    found = True;
                    break

        if not found and term_time and term_time <= curr_s <= (term_time + STAY_DURATION):
            count = term_occ[term_sta]
            term_occ[term_sta] += 1
            side_x = STATIONS[term_sta] + (count * 22)
            side_y = -1.7 if is_up else 1.7
            ax.scatter(side_x, side_y, c='purple', s=80, marker='s', alpha=0.6, zorder=15)
            ax.text(side_x, side_y + (0.12 if not is_up else -0.28), tid,
                    fontsize=7.5, color='purple', rotation=45)

    ax.set_xlim(-100, 1480)
    ax.set_ylim(-4.5, 2.8)
    ax.set_yticks([])
    ax.set_title(f"京沪高铁动态运行图 - 模拟时间: {curr_t_str}", fontsize=22, pad=15)


# 渲染动画
ani = FuncAnimation(fig, update, frames=total_frames)

# 开始保存
ani.save(SAVE_PATH, writer='pillow', fps=FPS)

# 渲染结束关闭进度条
pbar.close()
print(f"\n>>> 运行图绘制完成！文件已保存：{SAVE_PATH}")