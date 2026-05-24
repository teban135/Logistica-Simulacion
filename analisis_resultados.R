# analisis_resultados.R
# Análisis estadístico y visualización de resultados

# Cargar librerías
library(ggplot2)
library(dplyr)
library(tidyr)
library(knitr)

# Establecer tema limpio para gráficos
theme_clean <- theme_minimal() +
  theme(
    plot.title = element_text(hjust = 0.5, face = "bold", size = 14),
    axis.title = element_text(face = "bold", size = 11),
    legend.position = "bottom"
  )

# ============================================================
# 1. CARGAR DATOS
# ============================================================

cat(" Cargando datos...\n")

resultados <- read.csv('resultados/resultados.csv', stringsAsFactors = FALSE)
configs <- read.csv('resultados/configuraciones.csv', stringsAsFactors = FALSE)

cat(" Cargados", nrow(resultados), "registros de", 
    length(unique(resultados$escenario)), "escenarios\n")

# Ver estructura
print(str(resultados))

# ============================================================
# 2. ESTADÍSTICAS DESCRIPTIVAS
# ============================================================

cat("\n Estadísticas por escenario:\n")

estadisticas <- resultados %>%
  group_by(escenario) %>%
  summarise(
    n_replicas = n(),
    Wq_mean = mean(Wq_mean, na.rm = TRUE),
    Wq_sd = sd(Wq_mean, na.rm = TRUE),
    Wq_ic_inf = t.test(Wq_mean)$conf.int[1],
    Wq_ic_sup = t.test(Wq_mean)$conf.int[2],
    P_delay_mean = mean(P_delay, na.rm = TRUE),
    P_delay_sd = sd(P_delay, na.rm = TRUE),
    utilizacion_mean = mean(utilizacion, na.rm = TRUE),
    utilizacion_sd = sd(utilizacion, na.rm = TRUE),
    total_pedidos = sum(pedidos_atendidos, na.rm = TRUE)
  ) %>%
  mutate(across(where(is.numeric), ~ round(., 3)))

print(estadisticas)

# Guardar tabla
write.csv(estadisticas, 'resultados/graficos_R/estadisticas_escenarios.csv', row.names = FALSE)

# ============================================================
# 3. GRÁFICO 1: Boxplot de tiempos de espera por escenario
# ============================================================

cat("\n Generando gráfico 1: Boxplot Wq...\n")

p1 <- ggplot(resultados, aes(x = escenario, y = Wq_mean, fill = escenario)) +
  geom_boxplot(alpha = 0.7) +
  stat_summary(fun = mean, geom = "point", shape = 18, size = 3, color = "red") +
  labs(
    title = "Tiempo promedio de espera en cola (Wq) por escenario",
    subtitle = "Cada punto rojo representa la media del escenario",
    x = "Escenario",
    y = "Tiempo de espera (segundos)"
  ) +
  theme_clean +
  theme(legend.position = "none") +
  scale_fill_brewer(palette = "Set2")

ggsave("resultados/graficos_R/01_boxplot_wq.png", p1, width = 8, height = 6, dpi = 300)
print(p1)

# ============================================================
# 4. GRÁFICO 2: Intervalos de confianza para Wq
# ============================================================

cat("\n Generando gráfico 2: IC al 95%...\n")

p2 <- ggplot(estadisticas, aes(x = escenario, y = Wq_mean)) +
  geom_point(size = 4, color = "steelblue") +
  geom_errorbar(aes(ymin = Wq_ic_inf, ymax = Wq_ic_sup), width = 0.2, size = 1) +
  labs(
    title = "Intervalos de confianza al 95% para tiempo de espera",
    subtitle = "Barras horizontales representan el margen de error",
    x = "Escenario",
    y = "Tiempo de espera (segundos)"
  ) +
  theme_clean +
  coord_flip()

ggsave("resultados/graficos_R/02_intervalos_confianza.png", p2, width = 8, height = 5, dpi = 300)
print(p2)

# ============================================================
# 5. GRÁFICO 3: Probabilidad de retraso por escenario
# ============================================================

cat("\n Generando gráfico 3: P(Delay)...\n")

p3 <- ggplot(resultados, aes(x = escenario, y = P_delay, fill = escenario))