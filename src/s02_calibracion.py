"""
s02_calibracion.py
Extrae parámetros del dataset real para calibrar la simulación
"""
# Comando de ejecución: python src/s02_calibracion.py

import pandas as pd
import numpy as np
import os
# Definir rutas relativas al proyecto
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

def cargar_dataset():
    # Buscar el archivo CSV
    data_path = os.path.join(PROJECT_ROOT, "data", "raw")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"No se encontró la carpeta de datos en: {data_path}")
        
    for file in os.listdir(data_path):
        if file.endswith('.csv'):
            return pd.read_csv(os.path.join(data_path, file))
    raise FileNotFoundError(f"No se encontró ningún archivo CSV en {data_path}")

def calibrar_parametros(df):
    print("=" * 50)
    print("CALIBRACIÓN DE PARÁMETROS")
    print("=" * 50)
    
    # Convertir Timestamp
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # 1. Tasas de llegada por hora
    print("\n[Tasas de llegada por hora]")
    llegadas_por_hora = df.groupby(df['Timestamp'].dt.hour).size()
    dias_unicos = df['Timestamp'].dt.date.nunique()
    tasa_llegada_hora = (llegadas_por_hora / dias_unicos).to_dict()
    
    for hora in range(24):
        tasa = tasa_llegada_hora.get(hora, 0)
        if tasa > 0:
            print(f"   Hora {hora:02d}: {tasa:.2f} pedidos/hora")
    
    # 2. Estadísticas de Waiting_Time
    waiting_time = df['Waiting_Time']
    print(f"\n[Estadísticas de Waiting_Time observado]")
    print(f"   Media: {waiting_time.mean():.1f} segundos")
    print(f"   Mediana: {waiting_time.median():.1f} segundos")
    print(f"   Desv. estándar: {waiting_time.std():.1f}")
    print(f"   Percentil 80: {waiting_time.quantile(0.80):.1f} segundos")
    print(f"   Percentil 90: {waiting_time.quantile(0.90):.1f} segundos")
    print(f"   Máximo: {waiting_time.max():.1f} segundos")
    
    # 3. Utilización observada
    utilizacion_obs = df['Asset_Utilization'].mean() / 100
    print(f"\n[Utilización observada]")
    print(f"   Media de Asset_Utilization: {utilizacion_obs*100:.1f}%")
    
    # 4. Número de camiones
    num_camiones = df['Asset_ID'].nunique()
    print(f"\n[Flota]")
    print(f"   Camiones únicos: {num_camiones}")
    print(f"   IDs: {sorted(df['Asset_ID'].unique())}")
    
    # 5. Calcular tiempo de servicio esperado E[S]
    # Teorema de Little para M/M/c: E[Wq] = (E[S] * ρ) / (c * (1-ρ))
    # Despejamos E[S] ≈ (E[Wq] * c * (1-ρ)) / ρ
    
    # Tasa de llegada total (pedidos/segundo)
    tiempo_total_seg = (df['Timestamp'].max() - df['Timestamp'].min()).total_seconds()
    lambda_total = len(df) / tiempo_total_seg  # pedidos/segundo
    
    rho_obs = utilizacion_obs
    c = num_camiones
    E_Wq = waiting_time.mean()
    
    # Fórmula aproximada
    E_S = (E_Wq * c * (1 - rho_obs)) / rho_obs if rho_obs > 0 else 60
    
    print(f"\n[Parámetros calculados para simulación]")
    print(f"   lambda (tasa llegada total): {lambda_total*3600:.2f} pedidos/hora")
    print(f"   lambda_total: {lambda_total:.4f} pedidos/segundo")
    print(f"   E[S] (tiempo servicio esperado): {E_S:.1f} segundos ({E_S/60:.1f} minutos)")
    print(f"   rho (utilizacion esperada): {rho_obs:.3f}")
    
    # Verificar estabilidad
    rho_calculado = (lambda_total * E_S) / c
    print(f"\n[Verificación Ley de Little]")
    print(f"   rho calculado = lambda * E[S] / c = {rho_calculado:.3f}")
    print(f"   rho observado = {rho_obs:.3f}")
    
    if rho_calculado >= 1:
        print("   (!) ADVERTENCIA: Sistema inestable (rho >= 1). La cola crecerá infinitamente.")
    else:
        print("   (OK) Sistema estable (rho < 1)")
    
    # 6. Impacto del tráfico en tiempos de espera
    print(f"\n[Impacto del tráfico en Waiting_Time]")
    for estado in df['Traffic_Status'].unique():
        mask = df['Traffic_Status'] == estado
        media = df.loc[mask, 'Waiting_Time'].mean()
        print(f"   {estado}: {media:.1f} segundos (n={mask.sum()})")
    
    # Guardar parámetros
    params = {
        'num_camiones': c,
        'tiempo_servicio_mean': E_S,
        'tasa_llegada_por_hora': tasa_llegada_hora,
        # El umbral debe contemplar el Tiempo de Servicio (E[S]) + la tolerancia de espera
        'umbral_retraso': E_S + waiting_time.quantile(0.80),
        'utilizacion_obs': rho_obs,
        'lambda_total': lambda_total,
        'temp_ambiente': df['Temperature'].mean(),
        'humedad_ambiente': df['Humidity'].mean()
    }
    
    return params

def guardar_parametros(params):
    """Guarda parámetros en un archivo CSV para referencia"""
    import json
    
    # Guardar versión legible
    params_export = params.copy()
    params_export['tasa_llegada_por_hora'] = str(params_export['tasa_llegada_por_hora'])
    
    df_params = pd.DataFrame([params_export])
    output_path = os.path.join(PROJECT_ROOT, 'resultados', 'parametros_calibrados.csv')
    df_params.to_csv(output_path, index=False)
    
    # Guardar tasa por hora en formato tabla
    df_tasas = pd.DataFrame([
        {'hora': h, 'tasa_pedidos_por_hora': t} 
        for h, t in params['tasa_llegada_por_hora'].items()
    ])
    tasas_path = os.path.join(PROJECT_ROOT, 'resultados', 'tasas_llegada_por_hora.csv')
    df_tasas.to_csv(tasas_path, index=False)
    
    print("\n[Archivos guardados en]")
    print(f"   - {output_path}")
    print(f"   - {tasas_path}")

if __name__ == "__main__":
    resultados_dir = os.path.join(PROJECT_ROOT, "resultados")
    os.makedirs(resultados_dir, exist_ok=True)
    df = cargar_dataset()
    params = calibrar_parametros(df)
    guardar_parametros(params)