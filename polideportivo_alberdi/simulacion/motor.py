"""Motor principal de simulacion por eventos discretos."""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .distribuciones import generar_llegada, generar_uso
from .estado import (
    DISCIPLINAS,
    EVENTO_LLEGADA,
    cola_total,
    crear_estado_inicial,
    crear_grupo,
    objetos_temporales_activos,
    elegir_siguiente_grupo,
)
from .integracion import calcular_limpieza
from .metricas import calcular_metricas_finales


def _debe_guardar_fila(
    reloj: float,
    mostrar_todas: bool,
    hora_desde: float,
    cantidad_filas: int,
    guardadas_en_rango: int,
) -> bool:
    if mostrar_todas:
        return True
    return reloj >= hora_desde and guardadas_en_rango < cantidad_filas


def _formatear_valor(valor):
    if isinstance(valor, float):
        if math.isinf(valor):
            return ""
        return round(valor, 4)
    return valor


def _evento_minimo(eventos: Dict[str, float]) -> Tuple[str, float]:
    return min(eventos.items(), key=lambda item: item[1])


def _evento_minimo_simulable(eventos: Dict[str, float]) -> Tuple[str, float]:
    eventos_simulables = {
        evento: hora
        for evento, hora in eventos.items()
        if evento != "Fin Simulacion"
    }
    if not eventos_simulables:
        return "Fin Simulacion", float("inf")
    return _evento_minimo(eventos_simulables)


def _parametros_llegadas_por_defecto() -> Dict:
    return {
        "Futbol": {"media": 600.0},
        "HandBall": {"min": 600.0, "max": 840.0},
        "Basket": {"min": 360.0, "max": 600.0},
    }


def _parametros_usos_por_defecto() -> Dict:
    return {
        "Futbol": {"min": 80.0, "max": 100.0},
        "HandBall": {"min": 60.0, "max": 100.0},
        "Basket": {"min": 70.0, "max": 130.0},
    }


def _cerrar_intervalo_estado_cancha(estado: Dict, reloj: float) -> None:
    delta = reloj - estado["hora_ultimo_cambio_estado_cancha"]
    if delta <= 0:
        return
    if estado["estado_cancha"] == "Libre":
        estado["tiempo_libre"] += delta
    estado["hora_ultimo_cambio_estado_cancha"] = reloj


def _cambiar_estado_cancha(estado: Dict, nuevo_estado: str, reloj: float) -> None:
    if estado["estado_cancha"] == nuevo_estado:
        return
    _cerrar_intervalo_estado_cancha(estado, reloj)
    estado["estado_cancha"] = nuevo_estado


def _registrar_variable_generada(estado: Dict, tipo: str, rnd: float, valor: float) -> None:
    estado["variables_generadas"].append({"tipo": tipo, "rnd": rnd, "valor": valor})
    estado["rnd_usado"] = " | ".join(str(round(item["rnd"], 4)) for item in estado["variables_generadas"])
    estado["valor_generado"] = " | ".join(str(round(item["valor"], 4)) for item in estado["variables_generadas"])
    estado["tipo_variable_generada"] = " | ".join(item["tipo"] for item in estado["variables_generadas"])


def _limpiar_variables_generadas(estado: Dict) -> None:
    estado["variables_generadas"] = []
    estado["rnd_usado"] = ""
    estado["valor_generado"] = ""
    estado["tipo_variable_generada"] = ""


def _limpiar_integracion_generada(estado: Dict) -> None:
    estado["id_limpieza_generada"] = "-"
    estado["metodo_integracion_limpieza"] = "-"
    estado["h_integracion_limpieza"] = "-"
    estado["valor_integracion_limpieza"] = "-"
    estado["tiempo_limpieza_generado"] = "-"
    estado["d_objetivo_limpieza"] = "-"
    estado["c_inicio_limpieza"] = "-"


def _programar_llegada(
    estado: Dict,
    disciplina: str,
    rng: np.random.Generator,
    reloj: float,
    parametros_llegadas: Dict,
) -> None:
    tiempo, rnd = generar_llegada(disciplina, rng, parametros_llegadas)
    estado["eventos"][EVENTO_LLEGADA[disciplina]] = reloj + tiempo
    estado["ultimo_rnd_llegada"] = rnd
    _registrar_variable_generada(estado, f"Llegada {disciplina}", rnd, tiempo)


def _iniciar_uso_si_corresponde(
    estado: Dict,
    rng: np.random.Generator,
    reloj: float,
    parametros_usos: Dict,
) -> None:
    if estado["estado_cancha"] != "Libre":
        return

    grupo = elegir_siguiente_grupo(estado)
    if grupo is None:
        estado["disciplina_actual"] = ""
        estado["grupo_actual"] = None
        return

    tiempo_uso, rnd = generar_uso(grupo["disciplina"], rng, parametros_usos)
    grupo["estado"] = "En Cancha"
    grupo["hora_inicio_uso"] = reloj
    grupo["tiempo_espera"] = reloj - grupo["hora_llegada"]
    _cambiar_estado_cancha(estado, "Ocupada", reloj)
    estado["disciplina_actual"] = grupo["disciplina"]
    estado["grupo_actual"] = grupo["id"]
    estado["eventos"]["Fin Uso Cancha"] = reloj + tiempo_uso
    estado["ultimo_rnd_uso"] = rnd
    _registrar_variable_generada(estado, f"Uso {grupo['disciplina']}", rnd, tiempo_uso)


def _procesar_llegada(
    estado: Dict,
    disciplina: str,
    rng: np.random.Generator,
    reloj: float,
    capacidad_cola: int,
    parametros_llegadas: Dict,
    parametros_usos: Dict,
) -> None:
    _programar_llegada(estado, disciplina, rng, reloj, parametros_llegadas)

    if cola_total(estado) >= capacidad_cola:
        return

    grupo = crear_grupo(estado, disciplina, reloj)
    estado["colas"][disciplina].append(grupo["id"])
    estado["maxima_cola_total"] = max(estado["maxima_cola_total"], cola_total(estado))
    _iniciar_uso_si_corresponde(estado, rng, reloj, parametros_usos)


def _procesar_fin_uso(
    estado: Dict,
    iteracion: int,
    evento: str,
    reloj: float,
    objetivos_limpieza: Dict[str, float],
    h: float,
    metodo: str,
    coeficiente_limpieza: float,
    guardar_pasos_integracion: bool,
    integraciones: List[Dict],
) -> None:
    grupo_id = estado["grupo_actual"]
    if grupo_id is None:
        estado["eventos"]["Fin Uso Cancha"] = float("inf")
        return

    grupo = estado["objetos"][grupo_id]
    grupo["hora_salida"] = reloj
    disciplina = grupo["disciplina"]
    estado["acum_espera"][disciplina] += grupo["tiempo_espera"] or 0.0
    estado["atendidos"][disciplina] += 1
    del estado["objetos"][grupo_id]

    c_inicial = cola_total(estado)
    d_objetivo = objetivos_limpieza[disciplina]
    tiempo_limpieza, pasos, valor_final_d, detalle = calcular_limpieza(
        d_objetivo=d_objetivo,
        c_inicial=c_inicial,
        h=h,
        metodo=metodo,
        coeficiente_c=coeficiente_limpieza,
        guardar_pasos=guardar_pasos_integracion,
    )

    limpieza_numero = estado["proximo_id_limpieza"]
    limpieza_id = f"L{limpieza_numero}"
    estado["proximo_id_limpieza"] += 1
    estado["cantidad_limpiezas"] += 1
    _cambiar_estado_cancha(estado, "En Limpieza", reloj)
    estado["disciplina_limpieza"] = disciplina
    estado["disciplina_actual"] = ""
    estado["grupo_actual"] = None
    estado["eventos"]["Fin Uso Cancha"] = float("inf")
    estado["eventos"]["Fin Limpieza"] = reloj + tiempo_limpieza
    estado["id_limpieza_generada"] = limpieza_id
    estado["metodo_integracion_limpieza"] = metodo
    estado["h_integracion_limpieza"] = h
    estado["valor_integracion_limpieza"] = tiempo_limpieza
    estado["tiempo_limpieza_generado"] = tiempo_limpieza
    estado["d_objetivo_limpieza"] = d_objetivo
    estado["c_inicio_limpieza"] = c_inicial
    estado["tipo_variable_generada"] = "Integracion Limpieza"
    estado["valor_generado"] = tiempo_limpieza

    fila_integracion = {
        "ID Limpieza": limpieza_id,
        "Disciplina": disciplina,
        "D Objetivo": d_objetivo,
        "C inicial": c_inicial,
        "h": h,
        "Metodo": metodo,
        "Tiempo resultante de limpieza": tiempo_limpieza,
        "Valor final D": valor_final_d,
        "Cantidad de pasos": pasos,
        "Evento/Fila origen": f"{iteracion} - {evento}",
    }
    if guardar_pasos_integracion:
        fila_integracion["Pasos internos"] = detalle
    integraciones.append(fila_integracion)


def _procesar_fin_limpieza(
    estado: Dict,
    rng: np.random.Generator,
    reloj: float,
    parametros_usos: Dict,
) -> None:
    _cambiar_estado_cancha(estado, "Libre", reloj)
    estado["eventos"]["Fin Limpieza"] = float("inf")
    estado["disciplina_limpieza"] = ""
    _iniciar_uso_si_corresponde(estado, rng, reloj, parametros_usos)


def _crear_fila(iteracion: int, reloj: float, evento: str, estado: Dict) -> Dict:
    fila = {
        "N": iteracion,
        "Reloj": reloj,
        "Evento": evento,
        "Proxima Llegada Futbol": estado["eventos"]["Llegada Futbol"],
        "Proxima Llegada HandBall": estado["eventos"]["Llegada HandBall"],
        "Proxima Llegada Basket": estado["eventos"]["Llegada Basket"],
        "Proximo Fin Uso": estado["eventos"]["Fin Uso Cancha"],
        "Proximo Fin Limpieza": estado["eventos"]["Fin Limpieza"],
        "ID Limpieza": estado["id_limpieza_generada"],
        "Metodo Integracion": estado["metodo_integracion_limpieza"],
        "h Integracion": estado["h_integracion_limpieza"],
        "Valor Integracion Limpieza": estado["valor_integracion_limpieza"],
        "Estado Cancha": estado["estado_cancha"],
        "Disciplina Actual": estado["disciplina_actual"],
        "ID Grupo Actual": estado["grupo_actual"] or "",
        "Cola Futbol": len(estado["colas"]["Futbol"]),
        "Cola HandBall": len(estado["colas"]["HandBall"]),
        "Cola Basket": len(estado["colas"]["Basket"]),
        "Cola Total": cola_total(estado),
        "RND usado": estado["rnd_usado"],
        "Valor generado": estado["valor_generado"],
        "Tipo variable generada": estado["tipo_variable_generada"],
        "Ultimo RND Llegada": estado["ultimo_rnd_llegada"],
        "Ultimo RND Uso": estado["ultimo_rnd_uso"],
        "Tiempo Limpieza Generado": estado["tiempo_limpieza_generado"],
        "D Objetivo Limpieza": estado["d_objetivo_limpieza"],
        "C al iniciar limpieza": estado["c_inicio_limpieza"],
        "Acum Espera Futbol": estado["acum_espera"]["Futbol"],
        "Acum Espera HandBall": estado["acum_espera"]["HandBall"],
        "Acum Espera Basket": estado["acum_espera"]["Basket"],
        "Cantidad Atendidos Futbol": estado["atendidos"]["Futbol"],
        "Cantidad Atendidos HandBall": estado["atendidos"]["HandBall"],
        "Cantidad Atendidos Basket": estado["atendidos"]["Basket"],
        "Tiempo Libre Acumulado": estado["tiempo_libre"],
        "Cantidad Limpiezas": estado["cantidad_limpiezas"],
        "Maxima Cola Total": estado["maxima_cola_total"],
        "Objetos Temporales": objetos_temporales_activos(estado),
    }
    return {clave: _formatear_valor(valor) for clave, valor in fila.items()}


def simular(parametros: Dict) -> Dict:
    """Ejecuta la simulacion y devuelve vector de estado, integraciones y metricas."""
    rng = np.random.default_rng(parametros.get("semilla"))
    estado = crear_estado_inicial()
    tiempo_simulacion = float(parametros["tiempo_simulacion"])
    max_iteraciones_solicitadas = int(parametros["max_iteraciones"])
    limite_maximo_iteraciones = 100000
    max_iteraciones = min(max_iteraciones_solicitadas, limite_maximo_iteraciones)
    parametros_llegadas = parametros.get("parametros_llegadas", _parametros_llegadas_por_defecto())
    parametros_usos = parametros.get("parametros_usos", _parametros_usos_por_defecto())
    estado["eventos"]["Fin Simulacion"] = tiempo_simulacion

    for disciplina in DISCIPLINAS:
        _programar_llegada(estado, disciplina, rng, 0.0, parametros_llegadas)

    filas: List[Dict] = []
    ultima_fila = _crear_fila(0, 0.0, "Inicializacion", estado)
    filas_completas: List[Dict] = [ultima_fila]
    guardadas_en_rango = 0
    if _debe_guardar_fila(
        0.0,
        parametros["mostrar_todas"],
        parametros["hora_desde"],
        parametros["cantidad_filas"],
        guardadas_en_rango,
    ):
        filas.append(ultima_fila)
        guardadas_en_rango += 1

    integraciones: List[Dict] = []
    iteracion = 0
    evento = "Inicializacion"
    motivo_finalizacion = ""

    while iteracion < max_iteraciones and estado["reloj"] < tiempo_simulacion:
        evento, hora_evento = _evento_minimo_simulable(estado["eventos"])
        if math.isinf(hora_evento) or hora_evento > tiempo_simulacion:
            _cerrar_intervalo_estado_cancha(estado, tiempo_simulacion)
            estado["reloj"] = tiempo_simulacion
            iteracion += 1
            _limpiar_variables_generadas(estado)
            _limpiar_integracion_generada(estado)
            ultima_fila = _crear_fila(iteracion, estado["reloj"], "Fin Simulacion", estado)
            ultima_fila["Objetos Temporales"] = []
            motivo_finalizacion = "tiempo"
            break

        estado["reloj"] = hora_evento
        iteracion += 1
        _limpiar_variables_generadas(estado)
        _limpiar_integracion_generada(estado)

        if evento.startswith("Llegada"):
            disciplina = evento.replace("Llegada ", "")
            _procesar_llegada(
                estado,
                disciplina,
                rng,
                estado["reloj"],
                int(parametros["capacidad_cola"]),
                parametros_llegadas,
                parametros_usos,
            )
        elif evento == "Fin Uso Cancha":
            _procesar_fin_uso(
                estado,
                iteracion,
                evento,
                estado["reloj"],
                parametros["objetivos_limpieza"],
                float(parametros["h"]),
                parametros["metodo_integracion"],
                float(parametros.get("coeficiente_limpieza", 0.6)),
                bool(parametros["guardar_pasos_integracion"]),
                integraciones,
            )
        elif evento == "Fin Limpieza":
            _procesar_fin_limpieza(estado, rng, estado["reloj"], parametros_usos)

        ultima_fila = _crear_fila(iteracion, estado["reloj"], evento, estado)
        filas_completas.append(ultima_fila)
        if _debe_guardar_fila(
            estado["reloj"],
            parametros["mostrar_todas"],
            parametros["hora_desde"],
            parametros["cantidad_filas"],
            guardadas_en_rango,
        ):
            filas.append(ultima_fila)
            guardadas_en_rango += 1

    if not motivo_finalizacion:
        _cerrar_intervalo_estado_cancha(estado, estado["reloj"])
        ultima_fila = _crear_fila(iteracion, estado["reloj"], evento, estado)
        if filas_completas:
            filas_completas[-1] = ultima_fila
        if filas and filas[-1].get("N") == ultima_fila["N"]:
            filas[-1] = ultima_fila

        if estado["reloj"] >= tiempo_simulacion:
            motivo_finalizacion = "tiempo"
        elif iteracion >= limite_maximo_iteraciones:
            motivo_finalizacion = "limite_maximo_iteraciones"
        elif iteracion >= max_iteraciones:
            motivo_finalizacion = "cantidad_iteraciones"
        else:
            motivo_finalizacion = "sin_eventos"

    if not filas or filas[-1] != ultima_fila:
        filas.append(ultima_fila)
    if not filas_completas or filas_completas[-1] != ultima_fila:
        filas_completas.append(ultima_fila)

    mensajes_finalizacion = {
        "tiempo": "Finalizó por tiempo X",
        "cantidad_iteraciones": "Finalizó por cantidad N de iteraciones",
        "limite_maximo_iteraciones": "Finalizó por límite máximo de 100000 iteraciones",
        "sin_eventos": "Finalizó porque no hay más eventos pendientes",
    }

    tiempo_final = float(estado["reloj"])
    return {
        "vector_estado": pd.DataFrame(filas),
        "vector_estado_completo": pd.DataFrame(filas_completas),
        "integraciones": pd.DataFrame(integraciones).round(4),
        "metricas": {
            clave: round(valor, 4)
            for clave, valor in calcular_metricas_finales(estado, tiempo_final).items()
        },
        "iteraciones": iteracion,
        "tiempo_final": round(tiempo_final, 4),
        "motivo_finalizacion": motivo_finalizacion,
        "mensaje_finalizacion": mensajes_finalizacion[motivo_finalizacion],
        "estado_final": estado,
    }
