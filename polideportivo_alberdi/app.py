"""Interfaz Streamlit para la simulacion del Polideportivo Alberdi."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from simulacion.motor import simular


def _mostrar_metricas(metricas: dict) -> None:
    columnas = st.columns(4)
    claves = [
        "Espera promedio Futbol",
        "Espera promedio HandBall",
        "Espera promedio Basket",
        "Tiempo libre diario promedio",
        "Cantidad promedio de limpiezas por dia",
        "Porcentaje de tiempo libre de cancha",
        "Porcentaje de tiempo ocupado de cancha",
        "Grupos retirados totales",
        "Maxima cola total",
    ]

    for indice, clave in enumerate(claves):
        valor = metricas.get(clave, 0)
        sufijo = "%"
        if "Porcentaje" not in clave:
            sufijo = ""
        columnas[indice % 4].metric(clave, f"{valor:.4f}{sufijo}" if isinstance(valor, float) else valor)


def _parametros_sidebar() -> dict:
    st.sidebar.header("Parametros")
    tiempo_simulacion = st.sidebar.number_input(
        "Tiempo X de simulacion (minutos)",
        min_value=1.0,
        value=1440.0,
        step=60.0,
    )
    max_iteraciones = st.sidebar.number_input(
        "Maximo N de iteraciones",
        min_value=1,
        max_value=100000,
        value=10000,
        step=100,
    )
    hora_desde = st.sidebar.number_input("Hora j desde donde mostrar", min_value=0.0, value=0.0, step=60.0)
    cantidad_filas = st.sidebar.number_input("Cantidad i de filas a mostrar", min_value=1, value=200, step=10)
    mostrar_todas = st.sidebar.checkbox("Mostrar todas las filas", value=False)

    semilla_texto = st.sidebar.text_input("Semilla aleatoria opcional", value="")
    semilla = None
    if semilla_texto.strip():
        try:
            semilla = int(semilla_texto)
        except ValueError:
            st.sidebar.warning("La semilla debe ser un numero entero.")

    st.sidebar.divider()
    h = st.sidebar.number_input("h de integracion", min_value=0.0001, value=0.1, step=0.1, format="%.4f")
    coeficiente_limpieza = st.sidebar.number_input(
        "Coeficiente C de limpieza",
        min_value=0.0,
        value=0.6,
        step=0.1,
        format="%.4f",
    )
    d_futbol = st.sidebar.number_input("D objetivo Futbol", min_value=0.0, value=100.0, step=10.0)
    d_handball = st.sidebar.number_input("D objetivo HandBall", min_value=0.0, value=200.0, step=10.0)
    d_basket = st.sidebar.number_input("D objetivo Basket", min_value=0.0, value=300.0, step=10.0)
    capacidad_cola = st.sidebar.number_input("Capacidad maxima de cola", min_value=0, value=5, step=1)
    metodo_integracion = st.sidebar.selectbox("Metodo de integracion", ["Euler", "RK4"])
    guardar_pasos_integracion = st.sidebar.checkbox("Guardar pasos internos de integracion", value=False)

    with st.sidebar.expander("Parametros avanzados"):
        media_llegada_futbol = st.number_input("Media llegada Futbol", min_value=0.0001, value=600.0, step=10.0)
        min_llegada_handball = st.number_input("Minimo llegada HandBall", min_value=0.0, value=600.0, step=10.0)
        max_llegada_handball = st.number_input("Maximo llegada HandBall", min_value=0.0, value=840.0, step=10.0)
        min_llegada_basket = st.number_input("Minimo llegada Basket", min_value=0.0, value=360.0, step=10.0)
        max_llegada_basket = st.number_input("Maximo llegada Basket", min_value=0.0, value=600.0, step=10.0)
        min_uso_futbol = st.number_input("Minimo uso Futbol", min_value=0.0, value=80.0, step=5.0)
        max_uso_futbol = st.number_input("Maximo uso Futbol", min_value=0.0, value=100.0, step=5.0)
        min_uso_handball = st.number_input("Minimo uso HandBall", min_value=0.0, value=60.0, step=5.0)
        max_uso_handball = st.number_input("Maximo uso HandBall", min_value=0.0, value=100.0, step=5.0)
        min_uso_basket = st.number_input("Minimo uso Basket", min_value=0.0, value=70.0, step=5.0)
        max_uso_basket = st.number_input("Maximo uso Basket", min_value=0.0, value=130.0, step=5.0)
        minutos_por_dia = st.number_input("Minutos por dia para metricas", min_value=1.0, value=1440.0, step=60.0)

    parametros_llegadas = {
        "Futbol": {"media": media_llegada_futbol},
        "HandBall": {"min": min(min_llegada_handball, max_llegada_handball), "max": max(min_llegada_handball, max_llegada_handball)},
        "Basket": {"min": min(min_llegada_basket, max_llegada_basket), "max": max(min_llegada_basket, max_llegada_basket)},
    }
    parametros_usos = {
        "Futbol": {"min": min(min_uso_futbol, max_uso_futbol), "max": max(min_uso_futbol, max_uso_futbol)},
        "HandBall": {"min": min(min_uso_handball, max_uso_handball), "max": max(min_uso_handball, max_uso_handball)},
        "Basket": {"min": min(min_uso_basket, max_uso_basket), "max": max(min_uso_basket, max_uso_basket)},
    }

    return {
        "tiempo_simulacion": tiempo_simulacion,
        "max_iteraciones": int(max_iteraciones),
        "hora_desde": hora_desde,
        "cantidad_filas": int(cantidad_filas),
        "mostrar_todas": mostrar_todas,
        "semilla": semilla,
        "h": h,
        "objetivos_limpieza": {
            "Futbol": d_futbol,
            "HandBall": d_handball,
            "Basket": d_basket,
        },
        "capacidad_cola": int(capacidad_cola),
        "metodo_integracion": metodo_integracion,
        "guardar_pasos_integracion": guardar_pasos_integracion,
        "coeficiente_limpieza": coeficiente_limpieza,
        "minutos_por_dia": minutos_por_dia,
        "parametros_llegadas": parametros_llegadas,
        "parametros_usos": parametros_usos,
    }


def _mostrar_formulas() -> None:
    with st.expander("Formulas utilizadas"):
        st.markdown(
            """
            **Exponencial negativa**

            `X = -media * ln(1 - RND)`

            Para Futbol se usa media `600` minutos.

            **Uniforme**

            `X = a + RND * (b - a)`

            **Ecuacion de limpieza**

            `dD/dt = coeficiente * C + t`, con `D(0) = 0`.

            Por defecto el coeficiente es `0.6`. La limpieza finaliza cuando `D >= D objetivo`.

            **Euler**

            `D siguiente = D actual + h * (coeficiente * C + t actual)`

            **RK4**

            Se calcula con cuatro pendientes intermedias `k1`, `k2`, `k3` y `k4`.

            **Promedios de espera**

            `espera promedio disciplina = acum espera disciplina / cantidad atendidos disciplina`

            **Tiempo libre diario promedio**

            `tiempo libre diario promedio = tiempo libre acumulado / (tiempo simulado / 1440)`

            **Limpiezas promedio por dia**

            `limpiezas promedio por dia = cantidad limpiezas / (tiempo simulado / 1440)`

            **Porcentaje de ocupacion/libre**

            `porcentaje ocupado = tiempo ocupado acumulado / tiempo simulado * 100`

            `porcentaje libre = tiempo libre acumulado / tiempo simulado * 100`
            """
        )


def main() -> None:
    st.set_page_config(page_title="Simulacion: Polideportivo Alberdi", layout="wide")
    st.title("Simulacion: Polideportivo Alberdi")
    st.caption("Simulacion de eventos discretos - Sistema de colas con prioridad")

    parametros = _parametros_sidebar()

    if st.sidebar.button("Simular", type="primary", use_container_width=True):
        with st.spinner("Simulando eventos..."):
            resultado = simular(parametros)
        st.session_state["resultado"] = resultado

    resultado = st.session_state.get("resultado")
    if resultado is None:
        st.info("Configure los parametros y presione Simular.")
        _mostrar_formulas()
        return

    st.subheader("Metricas finales")
    _mostrar_metricas(resultado["metricas"])
    st.caption(
        f"Tiempo final: {resultado['tiempo_final']:.4f} minutos | "
        f"Iteraciones procesadas: {resultado['iteraciones']}"
    )

    st.subheader("Vector de estado")
    vector_estado = resultado["vector_estado"]
    if not vector_estado.empty:
        st.dataframe(vector_estado, use_container_width=True, height=520)
    else:
        st.warning("No se generaron filas para mostrar.")

    st.subheader("Integraciones realizadas")
    integraciones = resultado["integraciones"]
    if not integraciones.empty:
        st.dataframe(integraciones, use_container_width=True, height=280)
        if "Pasos internos" in integraciones.columns:
            pasos = []
            for _, fila in integraciones.iterrows():
                for paso in fila["Pasos internos"]:
                    pasos.append({"ID Limpieza": fila["ID Limpieza"], **paso})
            if pasos:
                st.subheader("Pasos internos de integracion")
                st.dataframe(pd.DataFrame(pasos).round(4), use_container_width=True, height=280)
    else:
        st.info("Todavia no se realizaron limpiezas.")

    _mostrar_formulas()


if __name__ == "__main__":
    main()
