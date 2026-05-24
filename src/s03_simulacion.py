"""
s03_simulacion.py
Modelo de simulación en SimPy para el centro logístico
"""
# Comando de ejecución: python src/s03_simulacion.py (Solo para pruebas rápidas)

import simpy
import random
import numpy as np

class CentroLogistica:
    """
    Modelo de un centro de distribución logística con flota de camiones
    """
    
    def __init__(self, env, num_camiones, tiempo_servicio_mean, tasa_llegada_por_hora, umbral_retraso, 
                 multiplicadores_trafico=None, prob_fallo=0.234, tiempo_fallo_mean=36.0,
                 costo_retraso_pedido=50000.0, costo_hora_camion=45000.0,
                 temp_ambiente=24.0, humedad_ambiente=65.0, prob_clima=0.362):
        """
        Args:
            env: entorno SimPy
            num_camiones: número de camiones disponibles
            tiempo_servicio_mean: tiempo promedio de servicio (carga+tránsito+descarga) en segundos
            tasa_llegada_por_hora: dict {hora: pedidos_por_hora} para horas 0-23
            umbral_retraso: tiempo en segundos a partir del cual se considera retraso
            multiplicadores_trafico: dict {hora: factor}
            prob_fallo: probabilidad de avería mecánica durante el servicio
            tiempo_fallo_mean: tiempo promedio de retraso por avería (segundos)
            costo_retraso_pedido: multa por cada pedido que supera el umbral_retraso (COP)
            costo_hora_camion: costo operativo por hora por cada camión (COP)
        """
        self.env = env
        self.camiones = simpy.Resource(env, capacity=num_camiones)
        self.tiempo_servicio_mean = tiempo_servicio_mean
        self.tasa_llegada_por_hora = tasa_llegada_por_hora
        self.umbral_retraso = umbral_retraso
        self.multiplicadores_trafico = multiplicadores_trafico or {h: 1.0 for h in range(24)}
        
        # Nuevos parámetros
        self.prob_fallo = prob_fallo
        self.tiempo_fallo_mean = tiempo_fallo_mean
        self.costo_retraso_pedido = costo_retraso_pedido
        self.costo_hora_camion = costo_hora_camion
        self.temp_ambiente = temp_ambiente
        self.humedad_ambiente = humedad_ambiente
        self.prob_clima = prob_clima
        
        # Parámetros para Log-normal (M/G/c)
        # Asumimos CV = 0.5 (Desviación estándar es la mitad de la media)
        self.cv = 0.5
        self.sigma_log = np.sqrt(np.log(1 + self.cv**2))
        
        # Métricas
        self.tiempos_espera = []
        self.pedidos_atendidos = 0
        self.pedidos_retrasados = 0
        self.num_fallos = 0
        
        # Contadores de causas de retraso
        self.retrasos_mecanico = 0
        self.retrasos_clima = 0
        self.retrasos_trafico = 0
        self.retrasos_saturacion = 0
        
        # Para cálculo de utilización
        self.tiempo_ocupado_total = 0
        self.ultimo_cambio_estado = 0
        
    def _actualizar_utilizacion(self):
        """Actualiza el tiempo ocupado acumulado"""
        tiempo_actual = self.env.now
        ocupados = self.camiones.count
        if ocupados > 0:
            self.tiempo_ocupado_total += ocupados * (tiempo_actual - self.ultimo_cambio_estado)
        self.ultimo_cambio_estado = tiempo_actual
    
    def atender_pedido(self, pedido_id):
        """
        Proceso que atiende un pedido específico
        """
        llegada_time = self.env.now
        
        # Solicitar un camión
        with self.camiones.request() as request:
            # Registrar inicio de espera para métricas de utilización
            self._actualizar_utilizacion()
            
            yield request  # Esperar hasta que un camión esté disponible
            
            # Registrar fin de espera para métricas
            self._actualizar_utilizacion()
            
            # Calcular tiempo de espera en cola
            tiempo_espera = self.env.now - llegada_time
            self.tiempos_espera.append(tiempo_espera)
            self.pedidos_atendidos += 1
            
            # Verificar si hubo retraso (se movió a la lógica de categorización de causas abajo)
            # if tiempo_espera > self.umbral_retraso:
            #     self.pedidos_retrasados += 1
            
            # Simular el servicio (carga + tránsito + descarga)
            # Determinar hora actual para aplicar tráfico
            hora_actual = int((self.env.now % (24 * 3600)) / 3600)
            factor_trafico = self.multiplicadores_trafico.get(hora_actual, 1.0)
            
            # --- M/G/c: Distribución Log-normal ---
            # Ajustar media por tráfico y humedad
            factor_humedad = 1 + (max(0, self.humedad_ambiente - 60) / 100.0) * 0.2
            mean_ajustado = self.tiempo_servicio_mean * factor_trafico * factor_humedad
            
            # Calcular mu para la log-normal manteniendo la media deseada
            mu_log = np.log(mean_ajustado) - (self.sigma_log**2) / 2
            tiempo_servicio = np.random.lognormal(mu_log, self.sigma_log)
            
            # --- Eventos Aleatorios de Fallos ---
            prob_fallo_efectiva = self.prob_fallo * (1 + max(0, self.temp_ambiente - 25) * 0.05)
            fallo_ocurrio = False
            if random.random() < prob_fallo_efectiva:
                fallo_ocurrio = True
                self.num_fallos += 1
                retraso_fallo = random.expovariate(1.0 / self.tiempo_fallo_mean)
                tiempo_servicio += retraso_fallo
            
            # --- Eventos Climáticos ---
            clima_ocurrio = False
            if random.random() < self.prob_clima:
                clima_ocurrio = True
                # El clima añade un retraso variable (10% a 30% del tiempo base)
                retraso_clima = tiempo_servicio * random.uniform(0.1, 0.3)
                tiempo_servicio += retraso_clima
            
            yield self.env.timeout(tiempo_servicio)
            
            # --- Categorización de Causa de Retraso ---
            # Si el tiempo total desde llegada hasta fin de servicio supera el umbral
            if (self.env.now - llegada_time) > self.umbral_retraso:
                self.pedidos_retrasados += 1
                
                # Asignar causa principal
                if fallo_ocurrio:
                    self.retrasos_mecanico += 1
                elif clima_ocurrio:
                    self.retrasos_clima += 1
                elif factor_trafico > 1.0:
                    self.retrasos_trafico += 1
                else:
                    self.retrasos_saturacion += 1
    
    def generar_llegadas(self):
        """
        Generador de llegadas de pedidos con tasa no estacionaria
        """
        pedido_id = 0
        
        # Obtener lista de horas con tasa > 0
        horas_con_llegadas = [h for h, t in self.tasa_llegada_por_hora.items() if t > 0]
        
        if not horas_con_llegadas:
            # Si no hay tasas definidas, usar tasa constante de 1 pedido/minuto
            print("⚠️ No se encontraron tasas de llegada. Usando tasa por defecto.")
            while True:
                yield self.env.timeout(60)  # 1 minuto
                pedido_id += 1
                self.env.process(self.atender_pedido(pedido_id))
        
        while True:
            # Determinar hora actual del día (0-23)
            hora_actual = int((self.env.now % (24 * 3600)) / 3600)
            
            # Obtener tasa para esta hora (pedidos/segundo)
            tasa_hora = self.tasa_llegada_por_hora.get(hora_actual, 0)
            tasa_por_segundo = tasa_hora / 3600.0
            
            if tasa_por_segundo > 0:
                # Intervalo exponencial entre llegadas
                intervalo = random.expovariate(tasa_por_segundo)
                yield self.env.timeout(intervalo)
                
                pedido_id += 1
                self.env.process(self.atender_pedido(pedido_id))
            else:
                # No hay llegadas en esta hora, avanzar al siguiente intervalo con llegadas
                # Encontrar próxima hora con llegadas
                horas_futuras = [(h - hora_actual) % 24 for h in horas_con_llegadas]
                hora_siguiente = min([h for h in horas_futuras if h > 0] or [24])
                tiempo_avance = hora_siguiente * 3600
                yield self.env.timeout(tiempo_avance)
    
    def get_metricas(self, tiempo_simulacion):
        """
        Calcula métricas finales del sistema
        
        Returns:
            dict con métricas calculadas
        """
        # Calcular utilización promedio
        self._actualizar_utilizacion()
        utilizacion = self.tiempo_ocupado_total / (self.camiones.capacity * tiempo_simulacion)
        
        # Calcular tiempo promedio de espera
        Wq_mean = np.mean(self.tiempos_espera) if self.tiempos_espera else 0
        
        # Calcular probabilidad de retraso
        P_delay = self.pedidos_retrasados / self.pedidos_atendidos if self.pedidos_atendidos > 0 else 0
        
        # --- Implementación sugerida 2: Costos Operativos ---
        costo_penalizaciones = self.pedidos_retrasados * self.costo_retraso_pedido
        # Costo operativo = num_camiones * horas_totales * costo_hora
        costo_operativo_fijo = self.camiones.capacity * (tiempo_simulacion / 3600.0) * self.costo_hora_camion
        costo_total = costo_penalizaciones + costo_operativo_fijo
        
        return {
            'Wq_mean': Wq_mean,
            'P_delay': P_delay,
            'utilizacion': utilizacion,
            'pedidos_atendidos': self.pedidos_atendidos,
            'pedidos_retrasados': self.pedidos_retrasados,
            'num_fallos': self.num_fallos,
            'retrasos_mecanico': self.retrasos_mecanico,
            'retrasos_clima': self.retrasos_clima,
            'retrasos_trafico': self.retrasos_trafico,
            'retrasos_saturacion': self.retrasos_saturacion,
            'costo_penalizaciones': costo_penalizaciones,
            'costo_operativo_fijo': costo_operativo_fijo,
            'costo_total': costo_total
        }


def correr_simulacion(num_camiones, tiempo_servicio_mean, tasa_llegada_por_hora, 
                      umbral_retraso, multiplicadores_trafico=None, duracion_horas=168, seed=None,
                      prob_fallo=0.234, tiempo_fallo_mean=36.0, costo_retraso_pedido=50000.0, costo_hora_camion=45000.0,
                      temp_ambiente=24.0, humedad_ambiente=65.0, prob_clima=0.362):
    """
    Ejecuta una simulación y retorna las métricas
    
    Args:
        num_camiones: número de camiones
        tiempo_servicio_mean: tiempo medio de servicio (segundos)
        tasa_llegada_por_hora: dict con tasas por hora
        umbral_retraso: umbral para considerar retraso (segundos)
        duracion_horas: duración en horas
        seed: semilla para reproducibilidad
    
    Returns:
        dict con métricas de la simulación
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    # Crear entorno
    env = simpy.Environment()
    
    # Crear centro logístico
    centro = CentroLogistica(
        env=env,
        num_camiones=num_camiones,
        tiempo_servicio_mean=tiempo_servicio_mean,
        tasa_llegada_por_hora=tasa_llegada_por_hora,
        umbral_retraso=umbral_retraso,
        multiplicadores_trafico=multiplicadores_trafico,
        prob_fallo=prob_fallo,
        tiempo_fallo_mean=tiempo_fallo_mean,
        costo_retraso_pedido=costo_retraso_pedido,
        costo_hora_camion=costo_hora_camion,
        temp_ambiente=temp_ambiente,
        humedad_ambiente=humedad_ambiente,
        prob_clima=prob_clima
    )
    
    # Iniciar proceso de llegadas
    env.process(centro.generar_llegadas())
    
    # Ejecutar simulación
    duracion_segundos = duracion_horas * 3600
    env.run(until=duracion_segundos)
    
    # Obtener métricas
    metricas = centro.get_metricas(duracion_segundos)
    
    return metricas


# Prueba rápida del modelo
if __name__ == "__main__":
    print("🧪 Probando modelo de simulación...")
    
    # Parámetros de prueba
    tasa_prueba = {i: 10 for i in range(8, 20)}  # 10 pedidos/hora entre 8-20
    tasa_prueba.update({i: 0 for i in range(0, 8)})
    tasa_prueba.update({i: 2 for i in range(20, 24)})
    
    resultado = correr_simulacion(
        num_camiones=5,
        tiempo_servicio_mean=300,  # 5 minutos
        tasa_llegada_por_hora=tasa_prueba,
        umbral_retraso=20,  # 20 segundos
        duracion_horas=24,
        seed=42
    )
    
    print(f"✅ Prueba completada")
    print(f"   Pedidos atendidos: {resultado['pedidos_atendidos']}")
    print(f"   Wq promedio: {resultado['Wq_mean']:.1f} segundos")
    print(f"   P(Delay): {resultado['P_delay']:.3f}")
    print(f"   Utilización: {resultado['utilizacion']:.3f}")