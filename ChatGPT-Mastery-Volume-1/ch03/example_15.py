fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
# ... plotting logic for 12 categories ...
ax.legend(
    loc='upper left',
    bbox_to_anchor=(1.02, 1.0),
    frameon=True,
    facecolor='#111827',
    edgecolor='#374151',
    fontsize=9,
    ncol=1
)
plt.tight_layout()
plt.savefig('/mnt/data/decollided_product_trends.png', dpi=300, bbox_inches='tight')
plt.close(fig)
