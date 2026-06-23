"""Estado inicial y helpers de objetos temporales."""

from __future__ import annotations

from collections import deque
from typing import Deque, Dict, List, Optional


DISCIPLINAS = ("Futbol", "HandBall", "Basket")
EVENTO_LLEGADA = {
    "Futbol": "Llegada Futbol",
    "HandBall": "Llegada HandBall",
    "Basket": "Llegada Basket",
}


def crear_estado_inicial() -> Dict:
    """Crea el estado mutable de la simulacion."""
    return {
        "reloj": 0.0,
        "estado_cancha": "Libre",
        "hora_ultimo_cambio_estado_cancha": 0.0,
        "disciplina_actual": "",
        "grupo_actual": None,
        "colas": {disciplina: deque() for disciplina in DISCIPLINAS},
        "objetos": {},
        "proximo_id_grupo": 1,
        "proximo_id_limpieza": 1,
        "eventos": {
            "Llegada Futbol": float("inf"),
            "Llegada HandBall": float("inf"),
            "Llegada Basket": float("inf"),
            "Fin Uso Cancha": float("inf"),
            "Fin Limpieza": float("inf"),
            "Fin Simulacion": float("inf"),
        },
        "ultimo_rnd_llegada": "",
        "ultimo_rnd_uso": "",
        "rnd_usado": "",
        "valor_generado": "",
        "tipo_variable_generada": "",
        "variables_generadas": [],
        "id_limpieza_generada": "-",
        "metodo_integracion_limpieza": "-",
        "h_integracion_limpieza": "-",
        "valor_integracion_limpieza": "-",
        "tiempo_limpieza_generado": "-",
        "d_objetivo_limpieza": "-",
        "c_inicio_limpieza": "-",
        "disciplina_limpieza": "",
        "acum_espera": {disciplina: 0.0 for disciplina in DISCIPLINAS},
        "atendidos": {disciplina: 0 for disciplina in DISCIPLINAS},
        "tiempo_libre": 0.0,
        "cantidad_limpiezas": 0,
        "maxima_cola_total": 0,
    }


def crear_grupo(estado: Dict, disciplina: str, hora_llegada: float) -> Dict:
    """Crea y registra un grupo activo."""
    grupo_id = estado["proximo_id_grupo"]
    estado["proximo_id_grupo"] += 1
    grupo = {
        "id": grupo_id,
        "disciplina": disciplina,
        "estado": "En Cola",
        "hora_llegada": hora_llegada,
        "hora_inicio_uso": None,
        "hora_salida": None,
        "tiempo_espera": None,
    }
    estado["objetos"][grupo_id] = grupo
    return grupo


def cola_total(estado: Dict) -> int:
    """Devuelve la cantidad total de grupos esperando."""
    return sum(len(estado["colas"][disciplina]) for disciplina in DISCIPLINAS)


def elegir_siguiente_grupo(estado: Dict) -> Optional[Dict]:
    """Elige el proximo grupo respetando prioridad y orden entre Futbol/Basket."""
    candidatos_prioritarios: List[Dict] = []
    for disciplina in ("Futbol", "Basket"):
        if estado["colas"][disciplina]:
            grupo_id = estado["colas"][disciplina][0]
            candidatos_prioritarios.append(estado["objetos"][grupo_id])

    if candidatos_prioritarios:
        elegido = min(candidatos_prioritarios, key=lambda g: g["hora_llegada"])
        estado["colas"][elegido["disciplina"]].popleft()
        return elegido

    if estado["colas"]["HandBall"]:
        grupo_id = estado["colas"]["HandBall"].popleft()
        return estado["objetos"][grupo_id]

    return None


def objetos_temporales_activos(estado: Dict) -> List[Dict]:
    """Devuelve los objetos temporales activos como datos estructurados."""
    objetos = []
    for grupo in sorted(estado["objetos"].values(), key=lambda g: g["id"]):
        objetos.append(
            {
                "equipo": f"G{grupo['id']}",
                "numero": grupo["id"],
                "disciplina": grupo["disciplina"],
                "estado": grupo["estado"],
                "hora_llegada": round(grupo["hora_llegada"], 4),
            }
        )
    return objetos
