import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Comando de ejecución: python -m streamlit run src/s06_dashboard.py

# Configuración de la página
st.set_page_config(
    page_title="Smart Logistics Dashboard",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado para un look "Premium"
css = """
<style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    h1, h2, h3 { color: #00d4ff; }
    .stButton>button { background-color: #00d4ff; color: white; border-radius: 5px; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# Rutas
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, 'simulacion.db')

def load_data():
    if not os.path.exists(DB_PATH):
        return None, None
    
    conn = sqlite3.connect(DB_PATH)
    df_res = pd.read_sql_query("SELECT * FROM resultados", conn)
    df_conf = pd.read_sql_query("SELECT * FROM configuraciones", conn)
    conn.close()
    return df_res, df_conf

# Título Principal
st.title("🚚 Dashboard de Simulación Logística Inteligente")
st.markdown("Visualización en tiempo real de la utilización de la flota, fallos mecánicos y costos operativos.")

# Cargar Datos
df_res, df_conf = load_data()

if df_res is None or df_res.empty:
    st.warning("⚠️ No se encontraron resultados. Por favor, ejecute la simulación primero (`python src/s04_runner.py`).")
else:
    # Sidebar - Filtros
    st.sidebar.header("Filtros")
    escenarios = df_res['escenario'].unique()
    selected_escenario = st.sidebar.selectbox("Seleccionar Escenario", escenarios)
    
    # Filtrar datos
    df_filtered = df_res[df_res['escenario'] == selected_escenario]
    
    # Métricas Principales
    st.header(f"📊 Métricas: {selected_escenario}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        util_avg = df_filtered['utilizacion'].mean()
        st.metric("Utilización Media", f"{util_avg:.2%}", delta=None)
        
    with col2:
        delay_prob = df_filtered['P_delay'].mean()
        st.metric("P(Retraso)", f"{delay_prob:.2%}", delta=None, delta_color="inverse")
        
    with col3:
        avg_fallos = df_filtered['num_fallos'].mean()
        st.metric("Promedio Fallos", f"{avg_fallos:.1f}", delta=None, delta_color="inverse")
        
    with col4:
        total_cost = df_filtered['costo_total'].mean()
        st.metric("Costo Promedio", f"COP ${total_cost:,.0f}", delta=None, delta_color="inverse")

    # Nueva fila de métricas de paquetes
    # Se muestran PROMEDIOS por réplica (semana simulada), no sumas acumuladas
    col_pkg1, col_pkg2, col_pkg3, col_pkg4 = st.columns(4)
    with col_pkg1:
        avg_atendidos = df_filtered['pedidos_atendidos'].mean()
        st.metric("Promedio Entregados/Semana", f"{avg_atendidos:,.0f}")
    with col_pkg2:
        avg_retrasados = df_filtered['pedidos_retrasados'].mean()
        st.metric("Promedio Retrasados/Semana", f"{avg_retrasados:,.0f}", delta_color="inverse")
    with col_pkg3:
        avg_fallos_sem = df_filtered['num_fallos'].mean()
        st.metric("Fallos Mecánicos/Semana", f"{avg_fallos_sem:.1f}")
    with col_pkg4:
        perc_retraso = df_filtered['P_delay'].mean()
        st.metric("% Global Retraso", f"{perc_retraso:.1%}")

    # Layout de Gráficos
    row1_col1, row1_col2 = st.columns(2)
    
    with row1_col1:
        st.subheader("⏱️ Distribución de Tiempos de Espera (Wq)")
        fig_wq = px.histogram(df_filtered, x="Wq_mean", 
                             nbins=15, 
                             title="Histograma de Wq por Réplica",
                             labels={"Wq_mean": "Tiempo de Espera (seg)"},
                             color_discrete_sequence=['#00d4ff'])
        fig_wq.update_layout(template="plotly_dark")
        st.plotly_chart(fig_wq, use_container_width=True)
        
    with row1_col2:
        st.subheader("💰 Desglose de Costos")
        # Promediar costos para el pie chart
        costs = df_filtered[['costo_penalizaciones', 'costo_operativo_fijo']].mean()
        fig_costs = px.pie(values=costs.values, 
                          names=["Penalizaciones", "Costo Operativo"],
                          title="Distribución de Costos Totales",
                          hole=0.4,
                          color_discrete_sequence=['#ff4b4b', '#00d4ff'])
        fig_costs.update_layout(template="plotly_dark")
        st.plotly_chart(fig_costs, use_container_width=True)

    # Segunda fila de gráficos: Causas de Retraso
    row2_col1, row2_col2 = st.columns(2)
    
    with row2_col1:
        st.subheader("🚩 Causas de Retraso")
        # Sumar causas de retraso
        causas_cols = ['retrasos_mecanico', 'retrasos_clima', 'retrasos_trafico', 'retrasos_saturacion']
        causas_labels = ['Falla Mecánica', 'Clima', 'Tráfico', 'Saturación (Espera)']
        causas_values = df_filtered[causas_cols].sum()
        
        fig_causas = px.pie(values=causas_values.values, 
                           names=causas_labels,
                           title="Análisis de Raíz de Retrasos",
                           hole=0.4,
                           color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_causas.update_layout(template="plotly_dark")
        st.plotly_chart(fig_causas, use_container_width=True)
        
    with row2_col2:
        st.subheader("📈 Tendencia de Retrasos por Réplica")
        fig_trend = px.line(df_filtered, x="replica", y="pedidos_retrasados",
                           title="Evolución de Retrasos en Réplicas",
                           labels={"replica": "Número de Réplica", "pedidos_retrasados": "Pedidos con Retraso"},
                           markers=True)
        fig_trend.update_layout(template="plotly_dark")
        st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()
    
    # Comparativa de Escenarios
    st.header("🏁 Comparativa entre Escenarios")
    
    resumen = df_res.groupby('escenario').agg({
        'utilizacion': 'mean',
        'P_delay': 'mean',
        'costo_total': 'mean',
        'num_fallos': 'mean'
    }).reset_index()
    
    col_comp1, col_comp2 = st.columns(2)
    
    with col_comp1:
        fig_comp_util = px.bar(resumen, x='escenario', y='utilizacion', 
                              title="Utilización por Escenario",
                              color='utilizacion',
                              color_continuous_scale='Viridis')
        fig_comp_util.update_layout(template="plotly_dark")
        st.plotly_chart(fig_comp_util, use_container_width=True)
        
    with col_comp2:
        fig_comp_cost = px.bar(resumen, x='escenario', y='costo_total', 
                              title="Costo Total por Escenario",
                              color='costo_total',
                              color_continuous_scale='Reds')
        fig_comp_cost.update_layout(template="plotly_dark")
        st.plotly_chart(fig_comp_cost, use_container_width=True)

    # Detalle de Datos
    if st.checkbox("Mostrar tabla de datos detallada"):
        st.dataframe(df_filtered.style.highlight_max(axis=0, subset=['costo_total']))

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Desarrollado por Antigravity AI - Simulación Logística 2026")
