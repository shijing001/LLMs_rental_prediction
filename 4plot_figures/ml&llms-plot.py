import matplotlib.pyplot as plt
# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 上海数据
methods = ['MLR', 'RR', 'LR', 'DT', 'RF', 'DeepSeek-R1(20-shot)', 'GPT-3.5-Turbo(20-shot)']
rmse = [5.01e+3, 5.01e+3, 5.01e+3, 1.44e+3, 0.115e+3, 2.65e+3, 2.70e+3]
mae = [2.71e+3, 2.71e+3, 2.70e+3, 3.20e+2, 1.44e+1, 1.80e+3, 1.85e+3]

fig, ax1 = plt.subplots()

# 绘制 MSE 使用左侧的 y 轴
# ax1.set_xlabel('Methods')
ax1.set_xlabel('不同机器学习方法和大语言模型')
ax1.set_ylabel('RMSE')
ax1.plot(methods, rmse, marker='o', label='RMSE', color='tab:blue')
ax1.tick_params(axis='y')
ax1.set_ylim([min(rmse) * 0.9, max(rmse) * 1.1])  # 设置 y 轴范围

# 创建一个共享 x 轴的第二个 y 轴用于 MAE
ax2 = ax1.twinx()
ax2.set_ylabel('MAE')
ax2.plot(methods, mae, marker='x', label='MAE', color='tab:green')
ax2.tick_params(axis='y')
ax2.set_ylim([min(mae) * 0.9, max(mae) * 1.1])  # 设置 y 轴范围

# 合并图例
fig.tight_layout()
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines + lines2, labels + labels2, loc='best')

# 旋转横坐标标签并调整对齐方式
plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')  # ha参数控制对齐方式

# 调整底部边距防止标签被截断
plt.subplots_adjust(bottom=0.25)

plt.show()