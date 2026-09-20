# crops/management/commands/train_model.py
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your original ML training code
import pandas as pd
import numpy as np
import joblib
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

class Command(BaseCommand):
    help = 'Train and save the crop recommendation model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-path',
            type=str,
            default='Crop_recommendation.csv',
            help='Path to the CSV dataset file'
        )

    def handle(self, *args, **options):
        csv_path = options['data_path']
        
        if not os.path.exists(csv_path):
            self.stdout.write(
                self.style.ERROR(f'Dataset file not found: {csv_path}')
            )
            return

        self.stdout.write('Loading dataset...')
        try:
            # Ensure ml_models directory exists
            os.makedirs(settings.ML_MODEL_PATH, exist_ok=True)
            
            # Train the model using your original code
            self.train_and_save_model(csv_path)
            
            self.stdout.write(
                self.style.SUCCESS('Model training completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Training failed: {str(e)}')
            )

    def train_and_save_model(self, csv_path):
        """Train and save the crop recommendation model"""
        
        # Load data
        df = pd.read_csv(csv_path)
        self.stdout.write(f'Loaded {len(df)} samples')

        # Encode labels
        le = LabelEncoder()
        df['label'] = le.fit_transform(df['label'])
        
        # Features and target
        X = df.drop(['label'], axis=1)
        y = df['label']
        
        self.stdout.write(f'Features: {list(X.columns)}')
        self.stdout.write(f'Classes: {list(le.classes_)}')

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Create pipeline with SMOTE, polynomial features, scaling, feature selection, stacking
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
        
        self.stdout.write('Starting grid search...')
        gs = GridSearchCV(pipeline, param_grid, cv=5, scoring='accuracy', n_jobs=-1, verbose=1)
        gs.fit(X_train, y_train)
        best_model = gs.best_estimator_
        
        self.stdout.write(f'Best params: {gs.best_params_}')
        self.stdout.write(f'CV accuracy: {gs.best_score_:.3f}')

        # Evaluate on test set
        y_pred = best_model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        self.stdout.write(f'Test accuracy: {acc:.3f}')

        # Print classification report
        self.stdout.write('\nClassification report:')
        report = classification_report(y_test, y_pred, zero_division=0)
        self.stdout.write(report)

        # Save model and label encoder
        model_path = settings.CROP_MODEL_FILE
        encoder_path = settings.LABEL_ENCODER_FILE
        
        joblib.dump(best_model, model_path)
        joblib.dump(le, encoder_path)

        self.stdout.write(f'Model saved to: {model_path}')
        self.stdout.write(f'Label encoder saved to: {encoder_path}')