# Estado Actual del Proyecto: Simulación Logística

Este documento resume los hitos alcanzados, el análisis de la fuente de datos de Kaggle y la implementación de lógica dinámica para el Avance 3.

## 1. Análisis de Fuente de Datos (Kaggle) 📊
Los datos provienen del [Smart Logistics Supply Chain Dataset](https://www.kaggle.com/datasets/ziya07/smart-logistics-supply-chain-dataset). Se validó el uso de las siguientes variables clave:

| Variable | Significado en el Modelo | Estado |
| :--- | :--- | :--- |
| `Traffic_Status` | Define la congestión en ruta (Low, Medium, Heavy). | **Implementado** |
| `Logistics_Delay_Reason` | Causa raíz de la demora (Traffic, Weather, Mechanical). | *En revisión para eventos aleatorios* |
| `Temperature` / `Humidity` | Sensores IoT que afectan la eficiencia operativa y probabilidad de fallo. | **Implementado** |
| `Waiting_Time` | Tiempo observado de espera en el sistema real. | **Base de Calibración** |

---

## 2. Hitos Completados ✅

### Análisis Exploratorio (EDA)
*   **Script:** `s01_exploracion.py`
*   **Logro:** Análisis de 1,000 registros. Se identificó que el tráfico tiene una correlación directa con el aumento del `Waiting_Time`.

### Motor de Simulación Dinámico (Novedad)
*   **Script:** `s03_simulacion.py`
*   **Logro:** Se abandonó el tiempo de servicio constante. Ahora el modelo aplica **Multiplicadores de Tráfico** basados en la hora del día para mayor realismo.
*   **Horas Pico Implementadas (Basado en estándares de transporte urbano):**
    *   **Mañana (07:00-09:00):** Factor 1.3x
    *   **Mediodía (12:00-14:00):** Factor 1.1x
    *   **Tarde (17:00-19:00):** Factor 1.5x (Hora de mayor congestión)
*   **Sustento Técnico:** Estos intervalos y factores se basan en el *Urban Mobility Report* del Texas A&M Transportation Institute (TTI) y patrones típicos de logística de "última milla", donde se observa que la congestión vehicular aumenta el tiempo de tránsito entre un 30% y 50% durante los picos de demanda urbana.

### Ejecución de Escenarios
*   **Script:** `s04_runner.py`
*   **Escenarios:** Se ejecutan 4 configuraciones (Base, Flota Reducida, Demanda Pico, Estrés) integrando los nuevos factores de tráfico.

---

## 3. Implementaciones Sugeridas (Próximos Pasos) 🚀

1.  **Eventos Aleatorios de Fallos:** ✅ Implementado en `s03_simulacion.py`. Se usa la probabilidad del 23.4% extraída del dataset para averías mecánicas.
2.  **Costos Operativos:** ✅ Implementado. Se integraron penalizaciones por retraso ($50/pedido) y costos operativos fijos por camión ($25/hora).
3.  **Distribuciones No-Exponenciales:** ✅ Migrado a la distribución **Log-normal** (Modelo M/G/c).
4.  **Dashboard en Streamlit:** ✅ Implementado. Incluye métricas de paquetes entregados, análisis de causas de retraso (Pie Chart) y comparativa de escenarios.

---

## 4. Guía de Ejecución Rápida
1. `python src/s01_exploracion.py` (Visualizaciones)
2. `python src/s02_calibracion.py` (Calibración de λ y E[S])
3. `python src/s04_runner.py` (Simulación con tráfico dinámico)
4. `python src/s05_exportar_csv.py` (Exportación a SQLite/CSV)
