import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Set publication styling parameters
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#374151'
plt.rcParams['axes.linewidth'] = 0.8

fig, ax1 = plt.subplots(figsize=(12, 6), dpi=300)
fig.patch.set_facecolor('#080B11')
ax1.set_facecolor('#0E131F')

dates = pd.date_range(start='2022-01-01', periods=48, freq='M')
mau = np.linspace(1.2, 8.5, 48) + np.random.normal(0, 0.2, 48) # Millions
arpu = 15.0 + np.sin(np.linspace(0, 8, 48)) * 3.5 + np.random.normal(0, 0.4, 48) # USD

# Primary Axis: MAU (Emerald Bar Plot)
color1 = '#10B981'
ax1.set_xlabel('Reporting Month', color='#9CA3AF', fontsize=11, labelpad=10)
ax1.set_ylabel('Monthly Active Users (Millions)', color=color1, fontsize=11, labelpad=10)
bars = ax1.bar(dates, mau, width=20, color=color1, alpha=0.35, label='MAU (M)')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.tick_params(axis='x', labelcolor='#9CA3AF')
ax1.grid(axis='y', color='#374151', linestyle='--', alpha=0.3)

# Secondary Axis: ARPU (Cyan Line Plot)
ax2 = ax1.twinx()
color2 = '#06B6D4'
ax2.set_ylabel('Average Revenue Per User ($ ARPU)', color=color2, fontsize=11, labelpad=10)
line = ax2.plot(dates, arpu, color=color2, linewidth=2.5, marker='o', markersize=4, label='ARPU ($)')
ax2.tick_params(axis='y', labelcolor=color2)

# Styling Spines
for ax in [ax1, ax2]:
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_color('#374151')
    ax.spines['right'].set_color('#374151')
    ax.spines['bottom'].set_color('#374151')

plt.title('Enterprise SaaS Growth: User Scale vs. Monetization Efficiency (2022-2025)',
          color='#F3F4F6', fontsize=14, fontweight='bold', pad=15)

plt.tight_layout()
plt.savefig('/mnt/data/saas_growth_dual_axis.png', dpi=300, facecolor=fig.get_facecolor())
plt.show()
