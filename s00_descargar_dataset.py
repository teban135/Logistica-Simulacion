"""
s00_descargar_dataset.py
Descarga el dataset desde Kaggle y lo guarda en data/raw/
"""

import kagglehub
import os
import shutil

def descargar_dataset():
    print("📥 Descargando dataset desde Kaggle...")
    path = kagglehub.dataset_download("ziya07/smart-logistics-supply-chain-dataset")
    print(f"✅ Dataset descargado en: {path}")
    
    # Crear directorio destino
    os.makedirs("data/raw", exist_ok=True)
    
    # Copiar archivos
    for file in os.listdir(path):
        if file.endswith('.csv'):
            src = os.path.join(path, file)
            dst = os.path.join("data/raw", file)
            shutil.copy(src, dst)
            print(f"   Copiado: {file}")
    
    print("✅ Listo. Dataset disponible en data/raw/")
    return "data/raw/Smart_Logistics_Dataset.csv"

if __name__ == "__main__":
    descargar_dataset()