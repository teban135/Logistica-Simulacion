"""
s04_runner.py
Ejecuta múltiples réplicas de simulación y guarda resultados en SQLite
"""
# Comando de ejecución: python src/s04_runner.py

import sqlite3
import os
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Definir rutas relativas al proyecto
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Importar módulos propios
from s03_simulacion import correr_simulacion

# Configuración de Tráfico CON picos (situación problemática real)
# Basado en Urban Mobility Report (TTI): +30-50% en horas pico
MULTIPLICADORES_TRAFICO_CON_PICO = {h: 1.0 for h in range(24)}
# Pico Mañana (07:00 - 09:00)
MULTIPLICADORES_TRAFICO_CON_PICO.update({7: 1.3, 8: 1.3, 9: 1.2})
# Pico Mediodía (12:00 - 14:00)
MULTIPLICADORES_TRAFICO_CON_PICO.update({12: 1.1, 13: 1.1, 14: 1.1})
# Pico Tarde (17:00 - 19:00)
MULTIPLICADORES_TRAFICO_CON_PICO.update({17: 1.5, 18: 1.5, 19: 1.4})

# Configuración de Tráfico SIN picos (intervención: despacho en horario distribuido)
# Simula turnos de distribución fuera de hora pico (estrategia de gestión operativa)
MULTIPLICADORES_TRAFICO_SIN_PICO = {h: 1.0 for h in range(24)}

# Alias para compatibilidad
MULTIPLICADORES_TRAFICO_BASE = MULTIPLICADORES_TRAFICO_CON_PICO

def crear_base_datos(db_path=None):
    """Crea la base de datos SQLite con las tablas necesarias"""
    if db_path is None:
        db_path = os.path.join(PROJECT_ROOT, 'simulacion.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabla de resultados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            escenario TEXT,
            replica INTEGER,
            fecha_ejecucion TEXT,
            semilla INTEGER,
            num_camiones INTEGER,
            duracion_horas REAL,
            Wq_mean REAL,
            P_delay REAL,
            utilizacion REAL,
            pedidos_atendidos INTEGER,
            pedidos_retrasados INTEGER,
            num_fallos INTEGER,
            retrasos_mecanico INTEGER,
            retrasos_clima INTEGER,
            retrasos_trafico INTEGER,
            retrasos_saturacion INTEGER,
            costo_penalizaciones REAL,
            costo_operativo_fijo REAL,
            costo_total REAL
        )
    ''')
    
    # Tabla de parámetros (para trazabilidad)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuraciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            escenario TEXT,
            tiempo_servicio_mean REAL,
            umbral_retraso REAL,
            tasa_llegada_json TEXT,
            fecha_creacion TEXT
        )
    ''')
    
    conn.commit()
    return conn

def guardar_configuracion(conn, escenario, params):
    """Guarda la configuración del escenario"""
    cursor = conn.cursor()
    
    # Convertir tasa_llegada a JSON
    tasa_json = json.dumps(params['tasa_llegada_por_hora'])
    
    cursor.execute('''
        INSERT INTO configuraciones (escenario, tiempo_servicio_mean, umbral_retraso, tasa_llegada_json, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        escenario,
        params['tiempo_servicio_mean'],
        params['umbral_retraso'],
        tasa_json,
        datetime.now().isoformat()
    ))
    conn.commit()

def guardar_resultado(conn, escenario, replica, semilla, metricas, num_camiones, duracion_horas):
    """Guarda los resultados de una réplica"""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO resultados 
        (escenario, replica, fecha_ejecucion, semilla, num_camiones, duracion_horas,
         Wq_mean, P_delay, utilizacion, pedidos_atendidos, pedidos_retrasados,
         num_fallos, retrasos_mecanico, retrasos_clima, retrasos_trafico, retrasos_saturacion,
         costo_penalizaciones, costo_operativo_fijo, costo_total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        escenario,
        replica,
        datetime.now().isoformat(),
        semilla,
        num_camiones,
        duracion_horas,
        metricas['Wq_mean'],
        metricas['P_delay'],
        metricas['utilizacion'],
        metricas['pedidos_atendidos'],
        metricas['pedidos_retrasados'],
        metricas['num_fallos'],
        metricas['retrasos_mecanico'],
        metricas['retrasos_clima'],
        metricas['retrasos_trafico'],
        metricas['retrasos_saturacion'],
        metricas['costo_penalizaciones'],
        metricas['costo_operativo_fijo'],
        metricas['costo_total']
    ))
    conn.commit()

def correr_experimento(escenario, num_camiones, params_simulacion, 
                       multiplicadores_trafico=None, replicas=30, duracion_horas=168, verbose=True):
    """
    Ejecuta un experimento completo con múltiples réplicas
    
    Args:
        escenario: nombre del escenario (ej: 'E1_base')
        num_camiones: número de camiones a usar
        params_simulacion: diccionario con parámetros (tiempo_servicio_mean, etc)
        replicas: número de réplicas
        duracion_horas: duración en horas
        verbose: mostrar progreso
    """
    conn = crear_base_datos()
    
    # Guardar configuración del escenario
    guardar_configuracion(conn, escenario, params_simulacion)
    
    resultados = []
    
    for r in range(1, replicas + 1):
        # Usar semilla diferente para cada réplica
        semilla = 1000 * r + hash(escenario) % 1000
        
        if verbose:
            print(f"   Ejecutando {escenario}, réplica {r}/{replicas} (semilla={semilla})")
        
        try:
            metricas = correr_simulacion(
                num_camiones=num_camiones,
                tiempo_servicio_mean=params_simulacion['tiempo_servicio_mean'],
                tasa_llegada_por_hora=params_simulacion['tasa_llegada_por_hora'],
                umbral_retraso=params_simulacion['umbral_retraso'],
                multiplicadores_trafico=multiplicadores_trafico,
                duracion_horas=duracion_horas,
                seed=semilla,
                prob_fallo=params_simulacion.get('prob_fallo', 0.234),
                tiempo_fallo_mean=params_simulacion.get('tiempo_fallo_mean', 36.0),
                costo_retraso_pedido=params_simulacion.get('costo_retraso_pedido', 50000.0),
                costo_hora_camion=params_simulacion.get('costo_hora_camion', 45000.0),
                temp_ambiente=params_simulacion.get('temp_ambiente', 24.0),
                humedad_ambiente=params_simulacion.get('humedad_ambiente', 65.0)
            )
            
            guardar_resultado(conn, escenario, r, semilla, metricas, 
                            num_camiones, duracion_horas)
            resultados.append(metricas)
            
        except Exception as e:
            print(f"   [Error] en réplica {r}: {e}")
            continue
    
    conn.close()
    
    # Resumen
    if resultados:
        print(f"\n[Resumen {escenario}]")
        print(f"   Réplicas exitosas: {len(resultados)}/{replicas}")
        print(f"   Wq_mean promedio: {np.mean([r['Wq_mean'] for r in resultados]):.1f} seg")
        print(f"   P_delay promedio: {np.mean([r['P_delay'] for r in resultados]):.3f}")
        print(f"   Utilización promedio: {np.mean([r['utilizacion'] for r in resultados]):.3f}")
        print(f"   Viajes atendidos promedio: {np.mean([r['pedidos_atendidos'] for r in resultados]):.0f}")
        print(f"   Costo Total promedio: COP ${np.mean([r['costo_total'] for r in resultados]):,.2f}")
        print(f"   Num Fallos promedio: {np.mean([r['num_fallos'] for r in resultados]):.1f}")
    
    return resultados

def cargar_parametros_calibrados():
    """Carga los parámetros calibrados desde el archivo CSV"""
    try:
        tasas_path = os.path.join(PROJECT_ROOT, 'resultados', 'tasas_llegada_por_hora.csv')
        df_tasas = pd.read_csv(tasas_path)
        tasa_llegada = {row['hora']: row['tasa_pedidos_por_hora'] for _, row in df_tasas.iterrows()}
        
        params_path = os.path.join(PROJECT_ROOT, 'resultados', 'parametros_calibrados.csv')
        df_params = pd.read_csv(params_path)
        
        return {
            'num_camiones': int(df_params['num_camiones'].iloc[0]),
            'tiempo_servicio_mean': float(df_params['tiempo_servicio_mean'].iloc[0]),
            'tasa_llegada_por_hora': tasa_llegada,
            'umbral_retraso': float(df_params['umbral_retraso'].iloc[0]),
            'temp_ambiente': float(df_params['temp_ambiente'].iloc[0]),
            'humedad_ambiente': float(df_params['humedad_ambiente'].iloc[0])
        }
    except FileNotFoundError:
        print("[Error] No se encontraron parámetros calibrados.")
        print(f"   Buscando en: {PROJECT_ROOT}/resultados/")
        print("   Ejecute primero s02_calibracion.py")
        return None

def main():
    """Ejecuta todos los experimentos"""
    print("=" * 60)
    print("SIMULACIÓN DE LOGÍSTICA INTELIGENTE")
    print("=" * 60)
    
    # Cargar parámetros calibrados
    params = cargar_parametros_calibrados()
    if params is None:
        return
    
    print(f"\n[Parámetros cargados]")
    print(f"   Camiones base: {params['num_camiones']}")
    print(f"   Tiempo servicio E[S]: {params['tiempo_servicio_mean']:.1f} seg")
    print(f"   Umbral retraso: {params['umbral_retraso']:.1f} seg")
    
    # Crear directorio de resultados
    resultados_dir = os.path.join(PROJECT_ROOT, "resultados")
    os.makedirs(resultados_dir, exist_ok=True)
    
    # =========================================================
    # Demanda realista alta: λ × 850
    # Con la tasa base de ~0.12 ped/hora, x850 ≈ 102 ped/hora.
    # Con 3 camiones y E[S]=90 seg → ρ ≈ 0.85 (sistema saturado).
    # Esto garantiza cola real (Wq > 0) para demostrar mejoras.
    # Para rho = lambda * ES / c = (102/3600) * 90 / 3 ≈ 0.85
    # =========================================================
    params_demanda_alta = params.copy()
    params_demanda_alta['tasa_llegada_por_hora'] = {
        h: t * 850 for h, t in params['tasa_llegada_por_hora'].items()
    }

    # =========================================================
    # ESCENARIO E1: Situación Actual Problemática (Línea Base)
    # Flota mínima (3 camiones) + Demanda alta + Tráfico pico
    # → Sistema saturado: Wq alto, P(delay) > 40%
    # → Este es el PROBLEMA que queremos resolver
    # =========================================================
    print("\n" + "=" * 40)
    print("ESCENARIO E1: Situación Actual (3 camiones, demanda alta, tráfico pico)")
    print("=" * 40)

    correr_experimento(
        escenario='E1_situacion_actual',
        num_camiones=3,
        params_simulacion=params_demanda_alta,
        multiplicadores_trafico=MULTIPLICADORES_TRAFICO_CON_PICO,
        replicas=30,
        duracion_horas=168
    )

    # =========================================================
    # ESCENARIO E2: Intervención — Ampliación de Flota
    # 8 camiones + Demanda alta + Tráfico pico
    # → Misma presión de demanda y tráfico que E1
    # → Intervención: +5 camiones adicionales
    # → Pregunta: ¿Cuánto reduce el Wq solo con más flota?
    # =========================================================
    print("\n" + "=" * 40)
    print("ESCENARIO E2: Más Flota (8 camiones, demanda alta, tráfico pico)")
    print("=" * 40)

    correr_experimento(
        escenario='E2_mas_camiones',
        num_camiones=8,
        params_simulacion=params_demanda_alta,
        multiplicadores_trafico=MULTIPLICADORES_TRAFICO_CON_PICO,
        replicas=30,
        duracion_horas=168
    )

    # =========================================================
    # ESCENARIO E3: Intervención — Gestión de Demanda (Sin Picos)
    # 3 camiones + Demanda alta + SIN tráfico pico
    # → Misma flota que E1 (sin inversión extra en camiones)
    # → Intervención: despachar en horarios distribuidos fuera de pico
    # → Pregunta: ¿Cuánto reduce el Wq solo con gestión operativa?
    # =========================================================
    print("\n" + "=" * 40)
    print("ESCENARIO E3: Demanda Distribuida (3 camiones, demanda alta, sin pico)")
    print("=" * 40)

    correr_experimento(
        escenario='E3_demanda_distribuida',
        num_camiones=3,
        params_simulacion=params_demanda_alta,
        multiplicadores_trafico=MULTIPLICADORES_TRAFICO_SIN_PICO,
        replicas=30,
        duracion_horas=168
    )

    # =========================================================
    # ESCENARIO E4: Solución Óptima Combinada
    # 6 camiones + Demanda alta + SIN tráfico pico
    # → Combina ambas intervenciones: flota balanceada + gestión operativa
    # → Pregunta: ¿Cuál es la reducción máxima de Wq al combinar ambas?
    # → Este es el escenario RECOMENDADO (menor Wq, costo equilibrado)
    # =========================================================
    print("\n" + "=" * 40)
    print("ESCENARIO E4: Solucion Optima (6 camiones, demanda alta, sin pico)")
    print("=" * 40)

    correr_experimento(
        escenario='E4_solucion_optima',
        num_camiones=6,
        params_simulacion=params_demanda_alta,
        multiplicadores_trafico=MULTIPLICADORES_TRAFICO_SIN_PICO,
        replicas=30,
        duracion_horas=168
    )

    print("\n" + "=" * 60)
    print("SIMULACION COMPLETADA")
    print("=" * 60)
    print("\nResultados guardados en: simulacion.db")
    print("Ejecute s05_exportar_csv.py para exportar a CSV")
    print("Luego abra analisis_entrega3.Rmd en RStudio")

if __name__ == "__main__":
    main()