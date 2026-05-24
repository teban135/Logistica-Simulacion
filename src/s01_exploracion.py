# src/s01_exploracion.py
"""
Exploraci n y visualizaci n del dataset
Genera gr ficos para el informe del Avance 2
"""
# Comando de ejecución: python src/s01_exploracion.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Definir rutas relativas al proyecto
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

def generar_visualizaciones():
    """Genera los 6 gr ficos requeridos para el Avance 2"""
    
    # Crear carpeta para gr ficos
    graficos_dir = os.path.join(PROJECT_ROOT, "resultados", "graficos")
    os.makedirs(graficos_dir, exist_ok=True)
    
    # Cargar datos
    data_path = os.path.join(PROJECT_ROOT, 'data', 'raw', 'smart_logistics_dataset.csv')
    df = pd.read_csv(data_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Hour'] = df['Timestamp'].dt.hour
    
    # Configurar estilo
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (10, 6)
    
    print("Generando visualizaciones...")
    
    # GR FICO 1: Histograma de Waiting_Time
    plt.figure()
    plt.hist(df['Waiting_Time'], bins=30, edgecolor='black', alpha=0.7, color='steelblue')
    plt.xlabel('Tiempo de espera (segundos)')
    plt.ylabel('Frecuencia')
    plt.title('Distribuci n del tiempo de espera observado')
    plt.axvline(df['Waiting_Time'].mean(), color='red', linestyle='--', 
                label=f"Media: {df['Waiting_Time'].mean():.0f}s")
    plt.legend()
    plt.savefig(os.path.join(graficos_dir, '01_histograma_waiting_time.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("  OK 01_histograma_waiting_time.png")
    
    # GR FICO 2: Boxplot por Traffic_Status
    plt.figure()
    sns.boxplot(data=df, x='Traffic_Status', y='Waiting_Time', palette='Set2')
    plt.xlabel('Estado del tr fico')
    plt.ylabel('Tiempo de espera (segundos)')
    plt.title('Impacto del tr fico en el tiempo de espera')
    plt.savefig(os.path.join(graficos_dir, '02_boxplot_trafico.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("  OK 02_boxplot_trafico.png")
    
    # GR FICO 3: Serie temporal de llegadas por hora
    llegadas_por_hora = df.groupby('Hour').size()
    plt.figure()
    plt.bar(llegadas_por_hora.index, llegadas_por_hora.values, color='coral', edgecolor='black')
    plt.xlabel('Hora del d a')
    plt.ylabel('N mero de llegadas')
    plt.title('Volumen de llegadas por hora del d a')
    plt.xticks(range(0, 24))
    plt.savefig(os.path.join(graficos_dir, '03_llegadas_por_hora.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("  OK 03_llegadas_por_hora.png")
    
    # GR FICO 4: Utilizaci n vs Tiempo de espera
    plt.figure()
    sns.scatterplot(data=df, x='Asset_Utilization', y='Waiting_Time', 
                    hue='Logistics_Delay', alpha=0.6)
    plt.xlabel('Utilizaci n del activo (%)')
    plt.ylabel('Tiempo de espera (segundos)')
    plt.title('Relaci n entre utilizaci n y tiempo de espera')
    plt.savefig(os.path.join(graficos_dir, '04_utilizacion_vs_espera.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("  OK 04_utilizacion_vs_espera.png")
    
    # GR FICO 5: Violinplot por Shipment_Status
    plt.figure()
    sns.violinplot(data=df, x='Shipment_Status', y='Waiting_Time', palette='muted')
    plt.xlabel('Estado del env o')
    plt.ylabel('Tiempo de espera (segundos)')
    plt.title('Distribuci n de espera por estado de env o')
    plt.savefig(os.path.join(graficos_dir, '05_violin_por_estado.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("  OK 05_violin_por_estado.png")
    
    # GR FICO 6: Mapa de calor de llegadas
    df['DayOfWeek'] = df['Timestamp'].dt.dayofweek
    heatmap_data = df.groupby(['Hour', 'DayOfWeek']).size().unstack(fill_value=0)
    plt.figure(figsize=(12, 6))
    sns.heatmap(heatmap_data, cmap='YlOrRd', annot=False, 
                cbar_kws={'label': 'N mero de llegadas'})
    plt.xlabel('D a de la semana (0=Lunes, 6=Domingo)')
    plt.ylabel('Hora del d a')
    plt.title('Mapa de calor: llegadas por hora y d a de semana')
    plt.savefig(os.path.join(graficos_dir, '06_heatmap_llegadas.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print("  OK 06_heatmap_llegadas.png")
    
    print(f"\nOK 6 gr ficos guardados en {graficos_dir}")

def extraer_tabla_parametros():
    """Extrae tabla de par metros para el informe"""
    
    # Cargar datos
    data_path = os.path.join(PROJECT_ROOT, 'data', 'raw', 'smart_logistics_dataset.csv')
    df = pd.read_csv(data_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # Calcular par metros
    dias_unicos = df['Timestamp'].dt.date.nunique()
    tiempo_total_seg = (df['Timestamp'].max() - df['Timestamp'].min()).total_seconds()
    
    # Crear tabla de par metros
    tabla = {
        'Par metro': [
            'N mero de camiones',
            'D as de datos',
            'Total llegadas registradas',
            'Media Waiting_Time (seg)',
            'Desviaci n est ndar Waiting_Time',
            'M nimo Waiting_Time',
            'M ximo Waiting_Time',
            'Percentil 80 Waiting_Time',
            'Percentil 90 Waiting_Time',
            'Utilizaci n media observada (%)',
            'Tasa llegada total (pedidos/hora)',
            'Temperatura media ( C)',
            'Humedad media (%)'
        ],
        'Valor': [
            df['Asset_ID'].nunique(),
            dias_unicos,
            len(df),
            round(df['Waiting_Time'].mean(), 1),
            round(df['Waiting_Time'].std(), 1),
            df['Waiting_Time'].min(),
            df['Waiting_Time'].max(),
            round(df['Waiting_Time'].quantile(0.80), 1),
            round(df['Waiting_Time'].quantile(0.90), 1),
            round(df['Asset_Utilization'].mean(), 1),
            round(len(df) / tiempo_total_seg * 3600, 2),
            round(df['Temperature'].mean(), 1),
            round(df['Humidity'].mean(), 1)
        ]
    }
    
    df_tabla = pd.DataFrame(tabla)
    
    # Guardar
    resultados_dir = os.path.join(PROJECT_ROOT, "resultados")
    os.makedirs(resultados_dir, exist_ok=True)
    df_tabla.to_csv(os.path.join(resultados_dir, 'tabla_parametros.csv'), index=False)
    
    print("\n[Tabla de par metros]")
    print(df_tabla.to_string(index=False))
    print(f"\nOK Tabla guardada en {os.path.join(resultados_dir, 'tabla_parametros.csv')}")
    
    # Tambi n guardar tasas por hora
    llegadas_por_hora = df.groupby(df['Timestamp'].dt.hour).size()
    tasa_por_hora = (llegadas_por_hora / dias_unicos).round(2)
    
    df_tasas = pd.DataFrame({
        'Hora': range(24),
        'Tasa_pedidos_por_hora': [tasa_por_hora.get(h, 0) for h in range(24)]
    })
    df_tasas.to_csv(os.path.join(resultados_dir, 'tasas_por_hora.csv'), index=False)
    print(f"OK Tasas por hora guardadas en {os.path.join(resultados_dir, 'tasas_por_hora.csv')}")
    
    return df_tabla

if __name__ == "__main__":
    generar_visualizaciones()
    extraer_tabla_parametros()
    print("\n  Exploraci n completada. Todo listo para el informe.")