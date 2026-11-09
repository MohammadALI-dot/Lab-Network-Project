import os
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell as md, new_code_cell as code

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
nb = new_notebook()
nb.cells = [
md("# Position classifier: data exploration (EDA)\n"
   "Goal: predict a player's position (GK, DF, MF, FW) from per-90-minute statistics.\n"
   "Data: `data/clean_data.csv`, produced by `scrapers/clean_data.py` from the La Liga 2026/2027 scrape."),
code("""import os
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_selection import f_classif

os.makedirs('../report/figures', exist_ok=True)
sns.set_theme(style='whitegrid')
ORDER = ['GK', 'DF', 'MF', 'FW']
df = pd.read_csv('../data/clean_data.csv')
NOT_FEATURES = ['id', 'name', 'teamId', 'position_code', 'position_group', 'position', 'minutes']
features = [c for c in df.columns if c not in NOT_FEATURES]
print('players:', len(df), '| features:', len(features))
print('empty cells:', int(df[features].isna().sum().sum()))
df[['name', 'position', 'minutes'] + features[:6]].head()"""),
md("## 1. How many players per position?\nGoalkeepers are few, so accuracy alone will be misleading: a model that never predicts GK still looks good."),
code("""counts = df['position'].value_counts().reindex(ORDER)
ax = sns.barplot(x=counts.index, y=counts.values, order=ORDER)
for i, v in enumerate(counts.values):
    ax.text(i, v, str(v), ha='center', va='bottom')
ax.set_title('Players per position'); ax.set_ylabel('players')
plt.savefig('../report/figures/eda_class_counts.png', dpi=150, bbox_inches='tight'); plt.show()
print((counts / counts.sum() * 100).round(1).to_string())"""),
md("## 2. Which statistics separate the positions?\nThe F-score measures how different the position averages are, compared with the spread inside each position. Higher = more useful for the model."),
code("""F, p = f_classif(df[features], df['position'])
rank = pd.Series(F, index=features).sort_values(ascending=False)
plt.figure(figsize=(8, 8))
sns.barplot(x=rank.values, y=rank.index, color='#4472C4')
plt.title('Separating power of each feature (ANOVA F-score)'); plt.xlabel('F-score')
plt.savefig('../report/figures/eda_feature_scores.png', dpi=150, bbox_inches='tight'); plt.show()
rank.head(10).round(1)"""),
md("## 3. Distribution of the best features by position"),
code("""top6 = list(rank.index[:6])
fig, axes = plt.subplots(2, 3, figsize=(14, 7))
for ax, f in zip(axes.flat, top6):
    sns.boxplot(data=df, x='position', y=f, order=ORDER, ax=ax)
    ax.set_title(f)
plt.tight_layout()
plt.savefig('../report/figures/eda_boxplots.png', dpi=150, bbox_inches='tight'); plt.show()"""),
md("## 4. Average profile of each position\nValues are scaled 0 to 1 per feature, so different units can be compared."),
code("""prof = df.groupby('position')[features].mean().reindex(ORDER)
prof_scaled = (prof - prof.min()) / (prof.max() - prof.min() + 1e-9)
plt.figure(figsize=(14, 4))
sns.heatmap(prof_scaled, cmap='viridis', cbar_kws={'label': 'scaled average'})
plt.title('Average profile per position'); plt.xticks(rotation=90)
plt.savefig('../report/figures/eda_profile_heatmap.png', dpi=150, bbox_inches='tight'); plt.show()"""),
md("## 5. Correlation between features\nStrongly correlated features carry the same information."),
code("""corr = df[features].corr()
plt.figure(figsize=(12, 10))
sns.heatmap(corr, cmap='coolwarm', center=0, square=True, cbar_kws={'shrink': .7})
plt.title('Correlation matrix')
plt.savefig('../report/figures/eda_correlation.png', dpi=150, bbox_inches='tight'); plt.show()
pairs = corr.where(np.triu(np.ones(corr.shape, dtype=bool), 1)).stack()
pairs[pairs.abs() > 0.85].sort_values(ascending=False).round(2)"""),
md("## 6. Which positions look alike?\nAverage distance between position profiles (small = easy to confuse). Expect the closest pair to be among DF, MF and FW."),
code("""z = (df[features] - df[features].mean()) / (df[features].std() + 1e-9)
zp = z.groupby(df['position']).mean().reindex(ORDER)
dist = pd.DataFrame([[np.linalg.norm(zp.loc[a] - zp.loc[b]) for b in ORDER] for a in ORDER],
                    index=ORDER, columns=ORDER).round(2)
dist"""),
]
path = os.path.join(ROOT, "notebooks", "ml_analysis.ipynb")
nbf.write(nb, path)
print("created", path)
