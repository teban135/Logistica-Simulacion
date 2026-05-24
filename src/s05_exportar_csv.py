import sqlite3
# Comando de ejecución: python src/s05_exportar_csv.py
import pandas as pd
import os

# Definir rutas relativas al proyecto
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

def exportar_resultados(db_path=None, output_dir=None):
    """Exporta todas las tablas de SQLite a CSV"""
    
    if db_path is None:
        db_path = os.path.join(PROJECT_ROOT, 'simulacion.db')
    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, 'resultados')
        
    os.makedirs(output_dir, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    
    # Lista de tablas a exportar
    tablas = ['resultados', 'configuraciones']
    
    for tabla in tablas:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {tabla}", conn)
            output_path = os.path.join(output_dir, f'{tabla}.csv')
            df.to_csv(output_path, index=False)
            print(f"OK Exportada {tabla}: {len(df)} registros -> {output_path}")
        except Exception as e:
            print(f"[Error] No se pudo exportar {tabla}: {e}")
    
    # Estad sticas adicionales
    df_resultados = pd.read_sql_query("SELECT * FROM resultados", conn)
    
    if not df_resultados.empty:
        resumen = df_resultados.groupby('escenario').agg({
            'Wq_mean': ['mean', 'std', 'count'],
            'P_delay': ['mean', 'std'],
            'utilizacion': ['mean', 'std'],
            'num_fallos': ['mean'],
            'costo_total': ['mean']
        }).round(4)
        
        resumen.to_csv(os.path.join(output_dir, 'resumen_estadistico.csv'))
        print(f"OK Resumen estad stico guardado")
    
    conn.close()
    
    print(f"\n  Archivos disponibles en {output_dir}/")
    print("   - resultados.csv")
    print("   - configuraciones.csv")
    print("   - resumen_estadistico.csv")

def exportar_para_r():
    """Exporta datos formateados espec ficamente para R"""
    
    db_path = os.path.join(PROJECT_ROOT, 'simulacion.db')
    conn = sqlite3.connect(db_path)
    
    # Exportar resultados con formato amigable para R
    df = pd.read_sql_query("""
        SELECT 
            escenario,
            replica,
            Wq_mean as tiempo_espera_promedio,
            P_delay as prob_retraso,
            utilizacion,
            pedidos_atendidos,
            pedidos_retrasados,
            num_fallos,
            costo_total
        FROM resultados
        ORDER BY escenario, replica
    """, conn)
    
    output_path = os.path.join(PROJECT_ROOT, 'resultados', 'datos_para_r.csv')
    df.to_csv(output_path, index=False)
    print(f"OK {output_path} creado para an lisis en R")
    
    conn.close()

if __name__ == "__main__":
    exportar_resultados()
    exportar_para_r()
    print("\n  Listo para an lisis en R")