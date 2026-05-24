# 🚚 Documentación Integral: Simulación de Logística Inteligente

Este proyecto implementa un modelo de simulación de eventos discretos (DES) para un sistema logístico de transporte, integrando análisis de datos reales (Kaggle), calibración estadística y visualización avanzada.

---

## 1. Análisis y Uso de Variables del Dataset 📊

Los datos provienen del `smart_logistics_dataset.csv`. A continuación se detalla cómo se utiliza cada variable en el flujo del proyecto:

| Variable | Uso en el Código | Propósito Técnico |
| :--- | :--- | :--- |
| `Timestamp` | `s01_exploracion.py`, `s02_calibracion.py` | Se descompone en **Hora** y **Día de la semana** para calcular la tasa de llegada ($\lambda$) no estacionaria. |
| `Waiting_Time` | `s02_calibracion.py`, `s03_simulacion.py` | Define el tiempo de servicio base ($E[S]$) y el `umbral_retraso` para las métricas de calidad. |
| `Traffic_Status` | `s01_exploracion.py` | Se utiliza para validar estadísticamente que el tráfico aumenta el tiempo de espera, justificando los multiplicadores en la simulación. |
| `Logistics_Delay_Reason` | `calc_probs.py` (scratch), `s03_simulacion.py` | Se extrae la probabilidad de **Mechanical Failure** (23.4%) para introducir eventos aleatorios de avería. |
| `Asset_ID` | `s01_exploracion.py` | Determina el número único de recursos (camiones) para dimensionar el sistema ($c$). |
| `Temperature` / `Humidity` | `s03_simulacion.py` | **Factor de Estrés**: La temperatura afecta la tasa de fallos mecánicos y la humedad incrementa el tiempo de servicio base. |

---

## 2. Arquitectura del Modelo M/G/c 🧠

El proyecto evoluciona de un modelo M/M/c a un sistema de colas **M/G/c** para mayor realismo:

- **M (Llegadas):** Proceso de Poisson con tasa $\lambda$ variable por hora.
- **G (Servicio):** Tiempo de servicio con **Distribución Log-normal**. A diferencia de la exponencial, la log-normal captura mejor la variabilidad de procesos humanos y mecánicos, evitando tiempos excesivamente cortos y permitiendo un "pico" de probabilidad más natural.
    - Se asume un Coeficiente de Variación ($CV$) de 0.5.
    - El tiempo de servicio se ajusta dinámicamente según factores externos.
- **c (Servidores):** Flota de camiones (`simpy.Resource`).

### Ajustes Dinámicos (Realismo Logístico)
A diferencia de un modelo M/M/c teórico puro, este modelo añade:
1. **No-estacionariedad:** $\lambda$ cambia cada hora.
2. **Multiplicadores de Tráfico:** El tiempo de servicio medio se multiplica por 1.1x, 1.3x o 1.5x en horas pico.
3. **Interrupciones:** Un fallo mecánico añade un tiempo extra de servicio (retraso estocástico).

---

## 3. Lógica de Implementación (Script por Script) 🛠️

### `s01_exploracion.py`: Análisis de Variables
- **Cálculo de Días:** Se extrae de los valores únicos de fecha en `Timestamp` para normalizar las tasas de llegada.
- **Identificación de Patrones:** Se genera un mapa de calor que muestra en qué horas y días hay más saturación.

### `s02_calibracion.py`: Calibración Estadística
- **Promedio de Llegadas ($\lambda$):** Se calcula dividiendo el total de pedidos recibidos entre el tiempo total de observación.
  - **Tasa Global Observada:** **0.11 pedidos por hora**.
  - **Fluctuación por Hora:** La tasa no es constante; fluctúa desde un valle de **0.09 pedidos/hr** (1:00 PM) hasta un pico de **0.17 pedidos/hr** (10:00 AM).
- **Tiempo de Servicio Medio ($E[S]$):** Se calibró en **89.9 segundos** por pedido (representando el ciclo rápido de asignación y despacho).

### `s03_simulacion.py`: Motor de Eventos (SimPy)
- **Tiempo de Espera de Arribo:** Se calcula como `env.now - llegada_time` justo en el momento en que un camión queda disponible para el pedido.
- **Métrica de Utilización:** Se calcula integrando el tiempo que cada camión pasa ocupado:
  $$\text{Utilización} = \frac{\sum (\text{tiempo\_ocupado} \times \text{camiones\_activos})}{\text{capacidad\_total} \times \text{tiempo\_simulación}}$$
- **Probabilidad de Retraso ($P_{delay}$):** Ratio entre pedidos cuya espera superó el umbral y el total de pedidos atendidos.

### `s04_runner.py`: Ejecución y Persistencia
- **Réplicas:** Corre 30 simulaciones independientes por escenario para obtener intervalos de confianza (Ley de los Grandes Números).
- **Base de Datos:** Los resultados de cada réplica se guardan en `simulacion.db` usando SQL para asegurar la integridad de los datos.

---

### Análisis de Raíz de Retrasos (Root Cause Analysis)
El modelo ahora clasifica cada retraso según su causa principal para visualización en el dashboard:
- **Falla Mecánica**: Prioridad alta. Retraso debido a una avería del vehículo.
- **Clima**: Retraso debido a condiciones meteorológicas adversas (probabilidad 36.2%).
- **Tráfico**: Retraso ocurrido durante horas pico identificadas.
- **Saturación (Espera)**: Retraso debido exclusivamente al tiempo de espera en cola por falta de camiones disponibles.

## 4. Modelo de Costos y Fallos (Nuevas Funciones) 💸

### Impacto de Factores Ambientales (Sensores IoT)
El modelo integra la telemetría ambiental para ajustar el comportamiento del sistema en tiempo real:
1. **Temperatura Alta (>25°C)**: Incrementa la probabilidad de fallos mecánicos en un 5% por cada grado adicional, simulando el estrés térmico en los motores.
2. **Humedad Alta (>60%)**: Introduce un multiplicador de fricción operativa. Un exceso de humedad puede ralentizar las maniobras de carga/descarga o requerir una conducción más lenta, aumentando el tiempo de servicio hasta en un 20%.

### Impacto de Horas Pico en $P_{delay}$
Las horas pico (mañana, mediodía y tarde) aplican multiplicadores de tráfico (1.1x a 1.5x) directamente sobre el tiempo de servicio. Esto causa un efecto en cascada:
- Al aumentar el tiempo de servicio, los camiones permanecen ocupados más tiempo.
- La cola de pedidos crece rápidamente, aumentando exponencialmente el tiempo de espera en cola ($W_q$).
- Como resultado, la **Probabilidad de Retraso ($P_{delay}$)** aumenta significativamente durante estas ventanas de tiempo, superando el umbral de servicio definido.

### Cálculo de Costos
- **Moneda y Sustento:** Los costos se calculan en Pesos Colombianos (COP), basándose en valores referenciales adaptados del **SICE-TAC** (Sistema de Información de Costos Eficientes para el Transporte Automotor de Carga del Ministerio de Transporte de Colombia) para operaciones logísticas urbanas.
- **Costo Operativo Fijo:** Refleja el gasto de mantener la flota (salarios, combustible base, mantenimiento). Se calcula en **$45,000 COP** por cada hora que el camión está activo.
- **Penalizaciones:** Reflejan la pérdida de confianza del cliente o multas contractuales por entregas tardías. Es una métrica de costo de calidad, tasada en **$50,000 COP** por cada pedido retrasado.

---

## 5. Detalles de los Escenarios y Parámetros

### Sustento de las Horas Pico
Los intervalos y factores de las horas pico se sustentan en el **Urban Mobility Report** del **Texas A&M Transportation Institute (TTI)** y en patrones típicos de logística de "última milla". La congestión vehicular incrementa el tiempo de tránsito en los picos de demanda urbana, aplicándose los siguientes multiplicadores sobre el tiempo de servicio:
- **Mañana (07:00-09:00):** 1.3x
- **Mediodía (12:00-14:00):** 1.1x
- **Tarde (17:00-19:00):** 1.5x (congestión máxima, consistente con un 50% extra de demora).

### Escenarios Evaluados
Se han diseñado 4 escenarios de prueba (con 30 réplicas cada uno) para validar la robustez de la flota:
1. **Escenario E1 (Línea Base):** Configuración normal con el número de camiones ($c$) y tráfico extraídos directamente del dataset.
2. **Escenario E2 (Reducción de Flota):** Se reduce la cantidad de camiones disponibles a **8**. Funciona como una prueba de estrés operativo para medir el impacto en la probabilidad de retraso.
3. **Escenario E3 (Demanda Pico):** La flota se mantiene normal, pero la tasa de llegada de pedidos ($\lambda$) se **multiplica por 2** en todas las horas (ej. simulación de Black Friday).
4. **Escenario E4 (Prueba de Estrés Extrema):** El sistema se fuerza a saturarse reduciendo la flota a **1 solo camión**, con tiempos de servicio inflados (1 hora) y una demanda constante (2 pedidos/hora).

---

## 6. Resumen de Flujo de Datos

```mermaid
graph TD
    A[Dataset Kaggle] --> B(s01_exploracion.py)
    B --> C{Parámetros: λ, E[S], c}
    C --> D(s02_calibracion.py)
    D --> E(s03_simulacion.py: SimPy Engine)
    E --> F[Eventos: Tráfico, Fallos, Costos]
    F --> G(s04_runner.py: 120 Réplicas)
    G --> H[(simulacion.db)]
    H --> I(s05_exportar_csv.py)
    H --> J(s06_dashboard.py: Streamlit)
```

---
*Este proyecto integra la teoría de colas con la programación orientada a objetos para crear un gemelo digital (Digital Twin) de una operación logística urbana.*
