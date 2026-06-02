import numpy as np
import pandas as pd
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

def load_data():
    X = load_npz("data/final/feature_matrix.npz")
    X = normalize(X)
    df_index = pd.read_csv("data/final/mattresses_index.csv")
    return X, df_index


# ── Core ML ─────────────────────────────────────────────────────────────────
def get_query_vector(X, indices, weights):
    # log scale + normalize weights
    weights = np.log1p(weights)
    weights = weights / weights.sum()

    X_seeds = X[indices]

    # weighted sum (sparse-safe)
    query_vector = X_seeds.multiply(weights[:, None]).sum(axis=0)

    # convert to dense
    query_vector = np.asarray(query_vector).reshape(1, -1)

    # normalize for cosine
    query_vector = normalize(query_vector)

    return query_vector

def get_similar(df_filtered, X):
    if df_filtered.empty:
        return pd.DataFrame()
    top_seeds = df_filtered.sort_values("popularity_score", ascending=False).head(5)
    #seed_row  = top_seeds.sample(1).iloc[0]
    candidate_ids  = df_filtered.index.to_numpy()
    X_candidates   = X[candidate_ids]
    #query_id       = seed_row.name
    #query_vector   = X[query_id]
    weights = top_seeds["popularity_score"].values
    #weights = np.log1p(weights)
    #weights = weights / weights.sum()
    query_vector = get_query_vector(X, top_seeds.index, weights)
    scores         = cosine_similarity(query_vector, X_candidates).flatten()
    df_result = df_filtered.copy()
    df_result["similarity"] = scores
    #df_result = df_result[df_result.index != query_id]
    df_result = df_result.sort_values(by=["similarity","popularity_score"], ascending=[False,False])
    return df_result

def recommend(user_input, X, df_index):
    df_filtered = df_index.copy()
    if user_input.get("category"):
        df_filtered = df_filtered[df_filtered["category"] == user_input["category"]]
    if user_input.get("price_max") is not None:
        df_filtered = df_filtered[df_filtered["price"] <= user_input["price_max"]]
    if user_input.get("price_min") is not None:
        df_filtered = df_filtered[df_filtered["price"] >= user_input["price_min"]]
        
    # Xử lý khoảng độ dày mới
    if user_input.get("thickness_min") is not None:
        df_filtered = df_filtered[df_filtered["thickness"] >= user_input["thickness_min"]]
    if user_input.get("thickness_max") is not None:
        df_filtered = df_filtered[df_filtered["thickness"] < user_input["thickness_max"]]
        
    if user_input.get("width"):
        df_filtered = df_filtered[df_filtered["width"] == user_input["width"]]
    if user_input.get("length"):
        df_filtered = df_filtered[df_filtered["length"] == user_input["length"]]
    if user_input.get("firmness") is not None:
        df_filtered = df_filtered[df_filtered["firmness"] == user_input["firmness"]]
        
    df_result = get_similar(df_filtered, X)
    if df_result.empty:
        return pd.DataFrame()
    df_unique = (df_result.sort_values("similarity", ascending=False)
             .groupby("product_name")
             .first()
             .reset_index())

    # ---- Top 3 (random 3 trong top 3 = shuffle nhẹ) ----
    top3 = df_unique.head(3)
    top3 = top3.sample(frac=1)  # shuffle

    # ---- Top 12 tiếp theo ----
    next12 = df_unique.iloc[3:15]

    # lấy tối đa 7, nếu không đủ thì lấy hết
    n_remain = min(7, len(next12))
    top_rest = next12.sample(n=n_remain) if n_remain > 0 else pd.DataFrame()

    # ---- Gộp lại ----
    final_result = pd.concat([top3, top_rest]).reset_index(drop=True)

    return final_result


def recommend_userclick(user_click_row, X, df_index):
    df = df_index.copy()
    df_filtered = df[df["product_name"] != user_click_row["product_name"]]
    candidate_ids = df_filtered.index.to_numpy()
    X_candidates  = X[candidate_ids]
    # find index of clicked product
    mask = df.eq(user_click_row).all(axis=1)
    if not mask.any():
        # fallback: match by product_name only
        mask = (
            (df["product_name"] == user_click_row["product_name"]) &
            (df["width"] == user_click_row["width"]) &
            (df["length"] == user_click_row["length"]) &
            (df["thickness"] == user_click_row["thickness"])
        )
    idx    = df[mask].index[0]
    vector = X[idx]
    scores = cosine_similarity(vector, X_candidates).flatten()
    df_result = df_filtered.copy()
    df_result["similarity"] = scores
    df_result = df_result.sort_values(by=["similarity","popularity_score"], ascending=[False,False])
    df_unique = df_result.drop_duplicates(subset=["product_name"], keep="first")
    
    top10 = df_unique.head(10).reset_index(drop=True)
    top_fixed = top10.head(2)  # giữ 2 tốt nhất

    remaining = top10.iloc[2:]
    n_remain = min(3, len(remaining))

    top_random = remaining.sample(n=n_remain) if n_remain > 0 else pd.DataFrame()

    return pd.concat([top_fixed, top_random]).reset_index(drop=True)


def recommend_cold_start(df_index):
    df_sorted = df_index.copy()
    
    if df_sorted.empty:
        return pd.DataFrame()
    
    df_sorted = df_sorted.sort_values(by="popularity_score", ascending=False)
    df_unique = df_sorted.drop_duplicates(subset=["category", "product_name"])
    
    # Lấy top 5 mỗi category
    top5_per_cat = df_unique.groupby("category").head(5)
    
    # Random 3 mỗi category (KHÔNG dùng apply)
    result = []
    for _, group in top5_per_cat.groupby("category"):
        sampled = group.sample(n=min(3, len(group)))
        result.append(sampled)
    
    top_cold_start = pd.concat(result)
    
    return top_cold_start.sort_values(by="popularity_score", ascending=False).reset_index(drop=True)