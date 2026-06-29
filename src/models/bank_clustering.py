import pandas as pd
import numpy as np
import sqlite3
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from src.models.base_model import BaseModel
from src.utils import DB_PATH

class BankClustering(BaseModel):
    def __init__(self):
        super().__init__("bank_clustering")
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2)
        self.cluster_labels = None
        self.bank_names = None
        self.k = 4

    def _get_data(self):
        conn = sqlite3.connect(str(DB_PATH))
        df = pd.read_sql("SELECT * FROM bank_summary", conn)
        conn.close()
        cols = ["Total_ATMs", "Total_Cards", "Total_Txn_Vol", "Total_Txn_Val", "Digital_Share"]
        existent = [c for c in cols if c in df.columns]
        return df["Bank_Name"].values, df[existent].fillna(0)

    def train(self, k=None):
        self.k = k or 4
        names, X = self._get_data()
        self.bank_names = names
        X_scaled = self.scaler.fit_transform(X)
        X_pca = self.pca.fit_transform(X_scaled)
        self.model = KMeans(n_clusters=self.k, random_state=42, n_init=10)
        self.cluster_labels = self.model.fit_predict(X_scaled)
        self.X_pca = X_pca
        self.labels = self.cluster_labels
        sil = silhouette_score(X_scaled, self.cluster_labels)
        self.metrics = {
            "silhouette_score": round(sil, 4),
            "k_clusters": self.k,
            "pca_var_ratio": round(float(self.pca.explained_variance_ratio_.sum()), 4),
        }
        results = pd.DataFrame({
            "Bank": names, "Cluster": self.cluster_labels,
            "PCA1": X_pca[:, 0], "PCA2": X_pca[:, 1]
        })
        self.results = results
        self.is_trained = True
        self.save()
        return results

    def predict(self, features=None):
        return self.cluster_labels

    def get_optimal_k(self, max_k=8):
        _, X = self._get_data()
        X_scaled = self.scaler.fit_transform(X)
        scores = []
        for k in range(2, min(max_k + 1, len(X))):
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(X_scaled)
            scores.append((k, silhouette_score(X_scaled, labels)))
        return sorted(scores, key=lambda x: x[1], reverse=True)[0]

    def get_cluster_profiles(self):
        if self.results is None:
            return {}
        conn = sqlite3.connect(str(DB_PATH))
        df = pd.read_sql("SELECT * FROM bank_summary", conn)
        conn.close()
        df["Cluster"] = self.cluster_labels
        profiles = df.groupby("Cluster").mean(numeric_only=True).round(2)
        profiles["Count"] = df.groupby("Cluster").size()
        return profiles.to_dict(orient="index")
