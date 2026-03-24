from sklearn.discriminant_analysis import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier


import pandas as pd
import numpy as np

def build_match_features(df: pd.DataFrame):
    """Constrói features diferenciais (home - away) para cada estatística e janela temporal.

    Para cada janela (5, 10, 15 jogos) e cada papel (as_home, as_away), calcula a diferença
    entre as médias do time mandante e visitante para cada estatística.

    Naming: diff_{window}g_{role}_{stat_name}
    Exemplo: diff_5g_as_home_Ball possession
    """
    windows = [5, 10, 15]
    roles = ["as_home", "as_away"]

    meta_cols = ["game_id", "time", "home_team", "away_team", "home_score", "away_score", "result"]
    result = df[[c for c in meta_cols if c in df.columns]].copy()

    for w in windows:
        for role in roles:
            home_prefix = f"home_{w}g_{role}_"
            away_prefix = f"away_{w}g_{role}_"

            for home_col in [c for c in df.columns if c.startswith(home_prefix)]:
                stat_name = home_col[len(home_prefix):]
                away_col = f"{away_prefix}{stat_name}"
                if away_col in df.columns:
                    result[f"diff_{w}g_{role}_{stat_name}"] = df[home_col] - df[away_col]
    return result

def prepare_training_data(df):
    """Prepara os dados de treino: preenche NaN, gera features diferenciais e separa X/y.
    
    Args:
        df: DataFrame com features brutas da temporada
        
    Returns:
        tuple: (X, y) onde X são as features e y é o target (result)
    """
    df_filled = df.fillna(0)
    df_transformed = build_match_features(df_filled)
    X = df_transformed.drop(columns=["result"], errors='ignore')
    y = df_transformed["result"] if "result" in df_transformed.columns else None
    return X, y

def split_and_scale_data(X, y, test_size=0.2, random_state=42):
    """Separa dados em treino/teste e aplica StandardScaler.
    
    Args:
        X: Features
        y: Target
        test_size: Proporção do conjunto de teste
        random_state: Seed para reprodutibilidade
        
    Returns:
        tuple: (X_train_scaled, X_test_scaled, y_train, y_test, scaler)
    """
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler

def prepare_prediction_data(df_predict, reference_columns, scaler):
    """Prepara dados de predição: aplica transformações, alinha colunas e normaliza.
    
    Args:
        df_predict: DataFrame com features brutas do jogo a prever
        reference_columns: Colunas de referência do conjunto de treino
        scaler: StandardScaler já treinado
        
    Returns:
        array: Dados normalizados prontos para predição
    """
    df_filled = df_predict.fillna(0)
    df_transformed = build_match_features(df_filled)
    df_final = df_transformed.drop(columns=["result"], errors='ignore')
    
    # Alinhar colunas: adicionar colunas faltantes com 0
    for col in reference_columns:
        if col not in df_final.columns:
            df_final[col] = 0
    
    # Reordenar para ter as mesmas colunas na mesma ordem
    df_final = df_final[reference_columns]
    
    # Aplicar normalização
    return scaler.transform(df_final)

def train_logistic_regression(X_train, y_train):
    """Treina um modelo de regressão logística.
    
    Args:
        X_train: Features de treino (já normalizadas)
        y_train: Target de treino
        
    Returns:
        LogisticRegression: Modelo treinado
    """
    model = LogisticRegression(random_state=None)
    model.fit(X_train, y_train)
    return model


def train_random_forest(X_train, y_train):
    """Treina um modelo de Random Forest.
    
    Args:
        X_train: Features de treino (já normalizadas)
        y_train: Target de treino
        
    Returns:
        RandomForestClassifier: Modelo treinado
    """
    model = RandomForestClassifier(random_state=None)
    model.fit(X_train, y_train)
    return model

def train_xgboost(X_train, y_train):
    """Treina um modelo de XGBoost com suporte a classes customizadas.
    
    Args:
        X_train: Features de treino (já normalizadas)
        y_train: Target de treino
        
    Returns:
        XGBClassifierWithEncoder: Modelo treinado com encoder de label
    """
    # Criar e treinar o label encoder
    label_encoder = LabelEncoder()
    y_train_encoded = label_encoder.fit_transform(y_train)
    
    # Treinar o modelo XGBoost com as classes codificadas
    model = XGBClassifier(
        random_state=None, 
        use_label_encoder=False, 
        eval_metric='logloss'
    )
    model.fit(X_train, y_train_encoded)
    
    # Criar um wrapper que mantém o encoder
    class XGBClassifierWithEncoder:
        def __init__(self, xgb_model, encoder):
            self.model = xgb_model
            self.encoder = encoder
            self.classes_ = encoder.classes_
        
        def predict_proba(self, X):
            """Prediz probabilidades mantendo as classes originais."""
            return self.model.predict_proba(X)
        
        def predict(self, X):
            """Faz predição e decodifica para as classes originais."""
            y_pred_encoded = self.model.predict(X)
            return self.encoder.inverse_transform(y_pred_encoded)
    
    return XGBClassifierWithEncoder(model, label_encoder)