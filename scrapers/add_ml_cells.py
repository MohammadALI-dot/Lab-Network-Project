import os
import nbformat
from nbformat.v4 import new_markdown_cell as md, new_code_cell as code

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(ROOT, "notebooks", "ml_analysis.ipynb")
nb = nbformat.read(path, as_version=4)
if any("## 7. Train and test the models" in c.source for c in nb.cells):
    raise SystemExit("The model cells are already in the notebook. Nothing changed.")

NEW = [
md("## 7. Train and test the models\n"
   "Plan: keep 20% of the players aside as a test set that no model sees while it is built. "
   "Everything else (comparing models, choosing settings) uses only the other 80%, with 5-fold cross-validation. "
   "`minutes`, team and the player's id are NOT used as features."),
code("""from sklearn.model_selection import train_test_split, StratifiedKFold, RepeatedStratifiedKFold, cross_validate, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.dummy import DummyClassifier
from sklearn.base import clone
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score, ConfusionMatrixDisplay
import joblib

X, y = df[features], df['position']
idx_train, idx_test = train_test_split(df.index, test_size=0.2, stratify=y, random_state=42)
X_train, X_test = X.loc[idx_train], X.loc[idx_test]
y_train, y_test = y.loc[idx_train], y.loc[idx_test]
print('train:', len(X_train), y_train.value_counts().reindex(ORDER).to_dict())
print('test :', len(X_test), y_test.value_counts().reindex(ORDER).to_dict())"""),
md("### 7.1 First comparison with default settings (training players only)\n"
   "The baseline always answers the most common position. A real model must beat it clearly."),
code("""models = {
    'Baseline (most frequent)': DummyClassifier(strategy='most_frequent'),
    'Logistic Regression': Pipeline([('scale', StandardScaler()), ('clf', LogisticRegression(max_iter=3000, class_weight='balanced'))]),
    'k-NN': Pipeline([('scale', StandardScaler()), ('clf', KNeighborsClassifier())]),
    'Random Forest': RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42),
}
cv = StratifiedKFold(5, shuffle=True, random_state=42)
rows = []
for name, m in models.items():
    r = cross_validate(m, X_train, y_train, cv=cv, scoring=['accuracy', 'f1_macro'])
    rows.append({'model': name, 'cv_accuracy': r['test_accuracy'].mean(), 'cv_macro_f1': r['test_f1_macro'].mean()})
pd.DataFrame(rows).set_index('model').round(3)"""),
md("### 7.2 Choosing the best settings for each model (training players only)"),
code("""grids = {
    'Logistic Regression': (models['Logistic Regression'], {'clf__C': [0.03, 0.1, 0.3, 1, 3, 10]}),
    'k-NN': (models['k-NN'], {'clf__n_neighbors': [3, 5, 7, 9, 11, 15], 'clf__weights': ['uniform', 'distance']}),
    'Random Forest': (models['Random Forest'], {'max_depth': [None, 6, 10], 'min_samples_leaf': [1, 2, 4], 'max_features': ['sqrt', 0.5]}),
}
best = {}
for name, (m, g) in grids.items():
    gs = GridSearchCV(m, g, cv=cv, scoring='f1_macro', n_jobs=-1).fit(X_train, y_train)
    best[name] = gs
    print(f'{name}: cv macro-F1 = {gs.best_score_:.3f} | {gs.best_params_}')"""),
md("### 7.3 Final exam on the test players\nThe test players were never used above."),
code("""base = DummyClassifier(strategy='most_frequent').fit(X_train, y_train).predict(X_test)
results = [{'model': 'Baseline (most frequent)', 'cv_macro_f1': np.nan,
            'test_accuracy': accuracy_score(y_test, base), 'test_macro_f1': f1_score(y_test, base, average='macro')}]
preds = {}
for name, gs in best.items():
    preds[name] = gs.predict(X_test)
    results.append({'model': name, 'cv_macro_f1': gs.best_score_,
                    'test_accuracy': accuracy_score(y_test, preds[name]),
                    'test_macro_f1': f1_score(y_test, preds[name], average='macro')})
res = pd.DataFrame(results).set_index('model').round(3)
winner = res.drop('Baseline (most frequent)')['cv_macro_f1'].idxmax()
print('Best model by cross-validation:', winner)
res"""),
code("""fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
for ax, (name, p) in zip(axes, preds.items()):
    cm = confusion_matrix(y_test, p, labels=ORDER)
    ConfusionMatrixDisplay(cm, display_labels=ORDER).plot(ax=ax, cmap='Blues', colorbar=False)
    ax.set_title(f'{name}\\naccuracy {accuracy_score(y_test, p):.2f}')
plt.tight_layout()
plt.savefig('../report/figures/ml_confusion_matrices.png', dpi=150, bbox_inches='tight'); plt.show()
print(classification_report(y_test, preds[winner], labels=ORDER, digits=3, zero_division=0))"""),
md("### 7.4 More reliable score for the best model\n"
   "The test set is small (only a few goalkeepers), so one split can be lucky or unlucky. "
   "Here the best model is scored 15 times (5 folds, repeated 3 times) on all players."),
code("""rcv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=1)
r = cross_validate(clone(best[winner].best_estimator_), X, y, cv=rcv, scoring=['accuracy', 'f1_macro'])
print(f"{winner}: accuracy {r['test_accuracy'].mean():.3f} +/- {r['test_accuracy'].std():.3f} | "
      f"macro-F1 {r['test_f1_macro'].mean():.3f} +/- {r['test_f1_macro'].std():.3f}")"""),
md("### 7.5 Which statistics did the Random Forest use most?"),
code("""rf = best['Random Forest'].best_estimator_
imp = pd.Series(rf.feature_importances_, index=features).sort_values(ascending=False).head(15)
plt.figure(figsize=(8, 6))
sns.barplot(x=imp.values, y=imp.index, color='#70AD47')
plt.title('Random Forest: 15 most important features'); plt.xlabel('importance')
plt.savefig('../report/figures/ml_feature_importance.png', dpi=150, bbox_inches='tight'); plt.show()
imp.round(3)"""),
md("### 7.6 Which players were classified wrongly?"),
code("""wrong = df.loc[idx_test, ['name', 'position', 'minutes']].copy()
wrong['predicted'] = preds[winner]
wrong = wrong[wrong['position'] != wrong['predicted']]
print(len(wrong), 'of', len(idx_test), 'test players wrong')
print(pd.crosstab(wrong['position'], wrong['predicted']).to_string() if len(wrong) else 'none')
wrong.sort_values('minutes', ascending=False)"""),
md("## 8. The position suggestion function\n"
   "The final model is trained again on all players and saved to `models/position_model.joblib`. "
   "Its quality is the one measured above (test set and repeated cross-validation), not its score on players it has already seen."),
code("""final = clone(best[winner].best_estimator_).fit(X, y)
RATES = ['pass_accuracy', 'long_ball_accuracy', 'dribble_success', 'shot_conversion']
medians = X.median().to_dict()
os.makedirs('../models', exist_ok=True)
joblib.dump({'model': final, 'features': features, 'medians': medians}, '../models/position_model.joblib')

def suggest_position(stats):
    \"\"\"stats: dict of per-90 statistics. Missing ones count as 0 (percentages: the median).\"\"\"
    row = pd.DataFrame([{f: stats.get(f, medians[f] if f in RATES else 0.0) for f in features}])
    proba = pd.Series(final.predict_proba(row)[0], index=final.classes_).sort_values(ascending=False)
    return proba.index[0], proba.round(2).to_dict()

examples = {
    'defender-like': {'tackles_p90': 2.0, 'interceptions_p90': 1.2, 'clearances_p90': 4.0, 'passes_p90': 45, 'shots_p90': 0.3},
    'striker-like': {'shots_p90': 3.2, 'goals_p90': 0.6, 'shots_on_target_p90': 1.5, 'passes_p90': 18, 'clearances_p90': 0.4},
    'goalkeeper-like': {'saves_p90': 3.1, 'goals_conceded_p90': 1.2, 'passes_p90': 20, 'clearances_p90': 1.0},
}
for k, v in examples.items():
    print(k, '->', suggest_position(v))"""),
]
nb.cells.extend(NEW)
nbformat.write(nb, path)
print("added", len(NEW), "cells to", path)
