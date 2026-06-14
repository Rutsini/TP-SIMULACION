"""Metodos de integracion para calcular tiempos de limpieza."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple


def derivada_limpieza(t: float, d: float, c: int, coeficiente_c: float) -> float:
    """Ecuacion diferencial dD/dt = coeficiente_c * C + t."""
    return coeficiente_c * c + t


def _paso_euler(
    t: float,
    d: float,
    h: float,
    c: int,
    coeficiente_c: float,
    f: Callable[[float, float, int, float], float],
) -> float:
    return d + h * f(t, d, c, coeficiente_c)


def _paso_rk4(
    t: float,
    d: float,
    h: float,
    c: int,
    coeficiente_c: float,
    f: Callable[[float, float, int, float], float],
) -> float:
    k1 = f(t, d, c, coeficiente_c)
    k2 = f(t + h / 2, d + h * k1 / 2, c, coeficiente_c)
    k3 = f(t + h / 2, d + h * k2 / 2, c, coeficiente_c)
    k4 = f(t + h, d + h * k3, c, coeficiente_c)
    return d + (h / 6) * (k1 + 2 * k2 + 2 * k3 + k4)


def calcular_limpieza(
    d_objetivo: float,
    c_inicial: int,
    h: float,
    metodo: str = "Euler",
    coeficiente_c: float = 0.6,
    guardar_pasos: bool = False,
) -> Tuple[float, int, Optional[List[Dict[str, float]]]]:
    """Integra hasta que D alcance el objetivo y devuelve tiempo, pasos y detalle opcional."""
    if h <= 0:
        raise ValueError("El paso h debe ser mayor a cero.")
    if d_objetivo <= 0:
        return 0.0, 0, [] if guardar_pasos else None

    paso = _paso_rk4 if metodo == "RK4" else _paso_euler
    t = 0.0
    d = 0.0
    pasos = 0
    detalle = [] if guardar_pasos else None

    while d < d_objetivo and pasos < 1_000_000:
        d_anterior = d
        t_anterior = t
        d = paso(t, d, h, c_inicial, coeficiente_c, derivada_limpieza)
        t += h
        pasos += 1
        if guardar_pasos:
            detalle.append(
                {
                    "Paso": pasos,
                    "t inicial": t_anterior,
                    "D inicial": d_anterior,
                    "t final": t,
                    "D final": d,
                }
            )

    return t, pasos, detalle
