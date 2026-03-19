from sklearn.discriminant_analysis import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import pandas as pd

def build_match_features(df: pd.DataFrame):
    """Constrói features diferenciais (home - away) para cada estatística e janela temporal.

    Para cada janela (5, 10, 15 jogos) e cada papel (as_home, as_away), calcula a diferença
    entre as médias do time mandante e visitante para cada estatística.

    Naming: diff_{window}g_{role}_{stat_name}
    Exemplo: diff_5g_as_home_Ball possession
    """
    windows = [5, 10, 15]
    roles = ["as_home", "as_away"]

    meta_cols = ["game_id", "time", "home_team", "away_team", "home_score", "away_score", "is_home_team_winner"]
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
        tuple: (X, y) onde X são as features e y é o target (is_home_team_winner)
    """
    df_filled = df.fillna(0)
    df_transformed = build_match_features(df_filled)
    X = df_transformed.drop(columns=["is_home_team_winner"])
    y = df_transformed["is_home_team_winner"]
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
    df_final = df_transformed.drop(columns=["is_home_team_winner"], errors='ignore')
    
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
