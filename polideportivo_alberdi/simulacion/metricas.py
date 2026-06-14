"""Calculo de metricas finales."""

from __future__ import annotations

from typing import Dict

from .estado import DISCIPLINAS


def calcular_metricas_finales(
    estado: Dict,
    tiempo_simulado: float,
) -> Dict[str, float]:
    """Calcula solo las metricas finales pedidas por el enunciado."""
    dias = tiempo_simulado / 1440 if tiempo_simulado > 0 else 0
    metricas = {}

    for disciplina in DISCIPLINAS:
        atendidos = estado["atendidos"][disciplina]
        espera = estado["acum_espera"][disciplina] / atendidos if atendidos else 0.0
        metricas[f"Espera promedio {disciplina}"] = espera

    metricas["Tiempo libre diario promedio de la cancha"] = estado["tiempo_libre"] / dias if dias else 0.0
    metricas["Limpiezas promedio por dia"] = estado["cantidad_limpiezas"] / dias if dias else 0.0
    return metricas
