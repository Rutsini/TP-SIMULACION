"""Calculo de metricas finales."""

from __future__ import annotations

from typing import Dict

from .estado import DISCIPLINAS


def calcular_metricas_finales(
    estado: Dict,
    tiempo_simulado: float,
    minutos_por_dia: float = 1440.0,
) -> Dict[str, float]:
    """Calcula indicadores finales a partir de acumuladores."""
    dias = tiempo_simulado / minutos_por_dia if tiempo_simulado > 0 and minutos_por_dia > 0 else 0
    metricas = {}

    for disciplina in DISCIPLINAS:
        atendidos = estado["atendidos"][disciplina]
        espera = estado["acum_espera"][disciplina] / atendidos if atendidos else 0.0
        metricas[f"Espera promedio {disciplina}"] = espera

    metricas["Tiempo libre diario promedio"] = estado["tiempo_libre"] / dias if dias else estado["tiempo_libre"]
    metricas["Cantidad promedio de limpiezas por dia"] = estado["cantidad_limpiezas"] / dias if dias else 0.0
    metricas["Porcentaje de tiempo libre de cancha"] = (
        estado["tiempo_libre"] / tiempo_simulado * 100 if tiempo_simulado > 0 else 0.0
    )
    metricas["Porcentaje de tiempo ocupado de cancha"] = (
        estado["tiempo_ocupado"] / tiempo_simulado * 100 if tiempo_simulado > 0 else 0.0
    )
    metricas["Grupos retirados totales"] = sum(estado["retirados"].values())
    metricas["Maxima cola total"] = estado["maxima_cola_total"]
    return metricas
