
import pandas as pd
import numpy as np
import joblib
import argparse
from sklearn.preprocessing import LabelEncoder, StandardScaler, PolynomialFeatures
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from xgboost import XGBClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

MODEL_FILE = 'crop_recommendation_model.joblib'
ENC_FILE = 'label_encoder.joblib'

# ─── Training and saving model ───────────────────────────────────────────────
def train_and_save(csv_path):
    df = pd.read_csv(csv_path)

    # Encode label
    le = LabelEncoder()
    df['label'] = le.fit_transform(df['label'])
    joblib.dump(le, ENC_FILE)

    # Features and target
    X = df.drop(['label'], axis=1)
    y = df['label']

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Pipeline with SMOTE, polynomial features, scaling, feature selection, stacking
    smote = SMOTE(random_state=42)
    poly = PolynomialFeatures(degree=2, include_bias=False)
    scaler = StandardScaler()
    selector = SelectKBest(score_func=f_classif, k=10)

    base_learners = [
        ('rf', RandomForestClassifier(n_estimators=200, max_depth=15,
                                      class_weight='balanced', random_state=42)),
        ('xgb', XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                              use_label_encoder=False, eval_metric='mlogloss', random_state=42)),
        ('svm', SVC(kernel='rbf', C=10, gamma='scale', probability=True, random_state=42))
    ]
    meta = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)

    stack = StackingClassifier(
        estimators=base_learners,
        final_estimator=meta,
        passthrough=True,
        n_jobs=-1
    )

    pipeline = ImbPipeline([
        ('smote', smote),
        ('poly', poly),
        ('scale', scaler),
        ('select', selector),
        ('stack', stack)
    ])

    # GridSearchCV for logistic regression C param
    param_grid = {
        'stack__final_estimator__C': [0.1, 1, 10],
        'stack__final_estimator__penalty': ['l2'],
    }
    gs = GridSearchCV(pipeline, param_grid, cv=5, scoring='accuracy', n_jobs=-1, verbose=1)
    print("Training pipeline…")
    gs.fit(X_train, y_train)
    best_model = gs.best_estimator_
    print("Best params:", gs.best_params_)
    print("CV accuracy:", gs.best_score_)

    # Evaluate on test set
    y_pred = best_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Test accuracy: {acc:.3f}")

    print("\nClassification report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Save model and label encoder
    joblib.dump(best_model, MODEL_FILE)

    print("Models saved:", MODEL_FILE, ENC_FILE)
    return best_model, le

# ─── Load models ──────────────────────────────────────────────────────────────
def load_models():
    model = joblib.load(MODEL_FILE)
    le = joblib.load(ENC_FILE)
    return model, le

# ─── Suggestion by features ────────────────────────────────────────────────────
def suggest_by_features(model, le, features):
    """
    features: [N, P, K, temperature, humidity, ph, rainfall]
    """
    X_new = np.array([features])
    pred = model.predict(X_new)[0]
    return le.inverse_transform([pred])[0]

# ─── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crop Recommendation CLI")
    parser.add_argument('--train', action='store_true', help='Train and save model')
    parser.add_argument('--path', type=str, default='Crop_recommendation.csv', help='CSV file path')
    parser.add_argument('--N', type=float, required=False)
    parser.add_argument('--P', type=float, required=False)
    parser.add_argument('--K', type=float, required=False)
    parser.add_argument('--temperature', type=float, required=False)
    parser.add_argument('--humidity', type=float, required=False)
    parser.add_argument('--ph', type=float, required=False)
    parser.add_argument('--rainfall', type=float, required=False)
    args = parser.parse_args()

    if args.train:
        train_and_save(args.path)
        exit()

    model, le = load_models()
    df = pd.read_csv(args.path)

    feats = [args.N, args.P, args.K, args.temperature, args.humidity, args.ph, args.rainfall]
    if None in feats:
        print("Error: All feature values (N, P, K, temperature, humidity, ph, rainfall) must be provided.")
        exit(1)

    pred_label = suggest_by_features(model, le, feats)
    print("Crop recommendation:", pred_label)
