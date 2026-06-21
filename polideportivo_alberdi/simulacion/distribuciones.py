"""Funciones de distribucion para la simulacion."""

from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np


def exponencial_negativa(media: float, rng: np.random.Generator) -> Tuple[float, float]:
    """Genera una variable exponencial negativa con la media indicada."""
    rnd = float(rng.random())
    valor = -media * math.log(1 - rnd)
    return valor, rnd


def uniforme(a: float, b: float, rng: np.random.Generator) -> Tuple[float, float]:
    """Genera una variable uniforme entre a y b."""
    rnd = float(rng.random())
    valor = a + rnd * (b - a)
    return valor, rnd


def generar_llegada(disciplina: str, rng: np.random.Generator, parametros: Dict[str, Dict[str, float]],) -> Tuple[float, float]:
    """Genera el tiempo hasta la proxima llegada para una disciplina."""
    if disciplina == "Futbol":
        return exponencial_negativa(parametros["Futbol"]["media"], rng)
    if disciplina == "HandBall":
        return uniforme(parametros["HandBall"]["min"], parametros["HandBall"]["max"], rng)
    if disciplina == "Basket":
        return uniforme(parametros["Basket"]["min"], parametros["Basket"]["max"], rng)
    raise ValueError(f"Disciplina desconocida: {disciplina}")


def generar_uso(disciplina: str, rng: np.random.Generator, parametros: Dict[str, Dict[str, float]], ) -> Tuple[float, float]:
    """Genera el tiempo de uso de cancha para una disciplina."""
    if disciplina not in parametros:
        raise ValueError(f"Disciplina desconocida: {disciplina}")
    return uniforme(parametros[disciplina]["min"], parametros[disciplina]["max"], rng)
