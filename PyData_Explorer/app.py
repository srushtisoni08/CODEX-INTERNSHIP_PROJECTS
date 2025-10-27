import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

np.random.seed(42)
data = {
    'Product': ['Laptop', 'Phone', 'Tablet', 'Monitor', 'Keyboard', 
                'Mouse', 'Headphones', 'Speaker', 'Webcam', 'Charger'],
    'Sales': np.random.randint(50, 500, 10),
    'Revenue': np.random.randint(5000, 50000, 10),
    'Rating': np.random.uniform(3.5, 5.0, 10).round(2),
    'Stock': np.random.randint(10, 200, 10),
    'Category': ['Electronics', 'Electronics', 'Electronics', 'Electronics', 
                 'Accessories', 'Accessories', 'Audio', 'Audio', 'Video', 'Accessories']
}
df = pd.DataFrame(data)

print("=" * 60)
print("BASIC DATA ANALYSIS WITH PANDAS")
print("=" * 60)

print("\n1. First 5 rows of the dataset:")
print(df.head())

print("\n2. Dataset Information:")
print(df.info())

print("\n3. Statistical Summary:")
print(df.describe())

print("\n4. Average Values:")
print(f"   Average Sales: {df['Sales'].mean():.2f}")
print(f"   Average Revenue: ${df['Revenue'].mean():.2f}")
print(f"   Average Rating: {df['Rating'].mean():.2f}")
print(f"   Average Stock: {df['Stock'].mean():.2f}")

# 5. Group by analysis
print("\n5. Average Revenue by Category:")
category_stats = df.groupby('Category')['Revenue'].agg(['mean', 'sum', 'count'])
print(category_stats)

# 6. Find top performers
print("\n6. Top 3 Products by Revenue:")
top_products = df.nlargest(3, 'Revenue')[['Product', 'Revenue', 'Sales']]
print(top_products)

print("\n7. Correlation Matrix:")
correlation = df[['Sales', 'Revenue', 'Rating', 'Stock']].corr()
print(correlation)

print("\n" + "=" * 60)
print("CREATING VISUALIZATIONS")
print("=" * 60)

fig = plt.figure(figsize=(16, 12))

ax1 = plt.subplot(2, 3, 1)
colors = plt.cm.viridis(np.linspace(0, 1, len(df)))
ax1.bar(df['Product'], df['Revenue'], color=colors, edgecolor='black', linewidth=1.2)
ax1.set_xlabel('Product', fontsize=11, fontweight='bold')
ax1.set_ylabel('Revenue ($)', fontsize=11, fontweight='bold')
ax1.set_title('Revenue by Product', fontsize=13, fontweight='bold', pad=15)
ax1.tick_params(axis='x', rotation=45)
ax1.grid(axis='y', alpha=0.3, linestyle='--')
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

ax2 = plt.subplot(2, 3, 2)
scatter = ax2.scatter(df['Sales'], df['Revenue'], s=df['Rating']*100, 
                     c=df['Stock'], cmap='coolwarm', alpha=0.7, 
                     edgecolors='black', linewidth=1.5)
ax2.set_xlabel('Sales (Units)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Revenue ($)', fontsize=11, fontweight='bold')
ax2.set_title('Sales vs Revenue\n(Size=Rating, Color=Stock)', fontsize=13, fontweight='bold', pad=15)
ax2.grid(True, alpha=0.3, linestyle='--')
cbar = plt.colorbar(scatter, ax=ax2)
cbar.set_label('Stock Level', fontsize=10)

# 3. HEATMAP: Correlation Matrix
ax3 = plt.subplot(2, 3, 3)
sns.heatmap(correlation, annot=True, fmt='.2f', cmap='RdYlGn', 
            center=0, square=True, linewidths=2, cbar_kws={"shrink": 0.8},
            ax=ax3)
ax3.set_title('Correlation Heatmap', fontsize=13, fontweight='bold', pad=15)

# 4. HORIZONTAL BAR CHART: Average Revenue by Category
ax4 = plt.subplot(2, 3, 4)
category_avg = df.groupby('Category')['Revenue'].mean().sort_values()
colors_cat = plt.cm.plasma(np.linspace(0, 1, len(category_avg)))
ax4.barh(category_avg.index, category_avg.values, color=colors_cat, 
         edgecolor='black', linewidth=1.2)
ax4.set_xlabel('Average Revenue ($)', fontsize=11, fontweight='bold')
ax4.set_ylabel('Category', fontsize=11, fontweight='bold')
ax4.set_title('Average Revenue by Category', fontsize=13, fontweight='bold', pad=15)
ax4.grid(axis='x', alpha=0.3, linestyle='--')

# 5. PIE CHART: Sales Distribution by Category
ax5 = plt.subplot(2, 3, 5)
category_sales = df.groupby('Category')['Sales'].sum()
colors_pie = plt.cm.Set3(np.linspace(0, 1, len(category_sales)))
wedges, texts, autotexts = ax5.pie(category_sales.values, labels=category_sales.index, 
                                     autopct='%1.1f%%', startangle=90, colors=colors_pie,
                                     explode=[0.05]*len(category_sales), shadow=True)
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')
ax5.set_title('Sales Distribution by Category', fontsize=13, fontweight='bold', pad=15)

# 6. LINE PLOT: Rating Trends
ax6 = plt.subplot(2, 3, 6)
df_sorted = df.sort_values('Rating')
ax6.plot(range(len(df_sorted)), df_sorted['Rating'].values, 
         marker='o', linewidth=2.5, markersize=8, color='#2E86AB',
         markerfacecolor='#A23B72', markeredgecolor='black', markeredgewidth=1.5)
ax6.fill_between(range(len(df_sorted)), df_sorted['Rating'].values, 
                 alpha=0.3, color='#2E86AB')
ax6.set_xlabel('Product Index (sorted by rating)', fontsize=11, fontweight='bold')
ax6.set_ylabel('Rating', fontsize=11, fontweight='bold')
ax6.set_title('Product Ratings Distribution', fontsize=13, fontweight='bold', pad=15)
ax6.grid(True, alpha=0.3, linestyle='--')
ax6.set_ylim(3, 5.5)

plt.tight_layout()
plt.savefig('data_analysis_visualizations.png', dpi=300, bbox_inches='tight')
print("\n✓ Visualizations saved as 'data_analysis_visualizations.png'")
plt.show()

print("\n" + "=" * 60)
print("KEY INSIGHTS AND OBSERVATIONS")
print("=" * 60)

print(f"""
1. REVENUE ANALYSIS:
   - Highest revenue product: {df.loc[df['Revenue'].idxmax(), 'Product']} (${df['Revenue'].max():,.2f})
   - Lowest revenue product: {df.loc[df['Revenue'].idxmin(), 'Product']} (${df['Revenue'].min():,.2f})
   - Total revenue across all products: ${df['Revenue'].sum():,.2f}

2. SALES PERFORMANCE:
   - Total units sold: {df['Sales'].sum()} units
   - Best-selling product: {df.loc[df['Sales'].idxmax(), 'Product']} ({df['Sales'].max()} units)
   - Average sales per product: {df['Sales'].mean():.1f} units

3. CUSTOMER SATISFACTION:
   - Average product rating: {df['Rating'].mean():.2f}/5.00
   - Highest rated: {df.loc[df['Rating'].idxmax(), 'Product']} ({df['Rating'].max():.2f})
   - Products rated above 4.5: {len(df[df['Rating'] > 4.5])}

4. INVENTORY STATUS:
   - Total stock available: {df['Stock'].sum()} units
   - Products with low stock (<50 units): {len(df[df['Stock'] < 50])}

5. CORRELATION INSIGHTS:
   - Sales-Revenue correlation: {correlation.loc['Sales', 'Revenue']:.2f}
   {'Strong positive correlation suggests higher sales drive revenue' if correlation.loc['Sales', 'Revenue'] > 0.7 else 'Moderate correlation between sales and revenue'}
   
6. CATEGORY PERFORMANCE:
   - Most profitable category: {category_avg.idxmax()}
   - Category with most products: {df['Category'].value_counts().idxmax()}
""")

print("=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)