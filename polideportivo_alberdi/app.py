"""Interfaz Streamlit para la simulacion del Polideportivo Alberdi."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from simulacion.motor import simular


def _dividir_valores_generados(valor) -> list[str]:
    if pd.isna(valor) or valor == "":
        return []
    return [parte.strip() for parte in str(valor).split(" | ")]


def _buscar_variable_generada(fila: pd.Series, tipo_buscado: str) -> tuple[str, str]:
    tipos = _dividir_valores_generados(fila.get("Tipo variable generada", ""))
    rnds = _dividir_valores_generados(fila.get("RND usado", ""))
    valores = _dividir_valores_generados(fila.get("Valor generado", ""))

    for indice, tipo in enumerate(tipos):
        if tipo == tipo_buscado:
            rnd = rnds[indice] if indice < len(rnds) else ""
            valor = valores[indice] if indice < len(valores) else ""
            return rnd, valor
    return "", ""


def _estado_objeto_legible(estado: str) -> str:
    estados = {
        "EnCola": "En Cola",
        "EnCancha": "En Cancha",
    }
    return estados.get(estado, estado)


def _parsear_objetos_temporales(resumen) -> list[dict]:
    if pd.isna(resumen) or resumen == "":
        return []

    objetos = []
    for parte in str(resumen).split("|"):
        campos = [campo.strip() for campo in parte.strip().split("-", 2)]
        if len(campos) < 3:
            continue
        equipo, disciplina, estado = campos
        objetos.append(
            {
                "equipo": equipo,
                "numero": _numero_equipo(equipo),
                "disciplina": disciplina,
                "estado": _estado_objeto_legible(estado),
            }
        )
    return objetos


def _numero_equipo(equipo: str) -> int:
    digitos = "".join(caracter for caracter in str(equipo) if caracter.isdigit())
    return int(digitos) if digitos else 0


def _orden_cola_futbol_basket(resumen) -> str:
    objetos = _parsear_objetos_temporales(resumen)
    en_cola = [
        f"{objeto['equipo']}-{objeto['disciplina']}"
        for objeto in objetos
        if objeto["disciplina"] in ("Futbol", "Basket") and objeto["estado"] == "En Cola"
    ]
    return " | ".join(en_cola)


def _mapear_horas_llegada_visibles(df: pd.DataFrame) -> dict[str, str]:
    horas = {}
    if "Objetos Temporales Activos" not in df.columns:
        return horas

    for _, fila in df.iterrows():
        reloj = fila.get("Reloj", "")
        for objeto in _parsear_objetos_temporales(fila.get("Objetos Temporales Activos", "")):
            horas.setdefault(objeto["equipo"], reloj)
    return horas


def _serie_desde_columna(df: pd.DataFrame, columna: str, valor_por_defecto: str = "-") -> pd.Series:
    if columna in df.columns:
        return df[columna]
    return pd.Series([valor_por_defecto] * len(df), index=df.index)


def _serie_variable_generada(df: pd.DataFrame, tipo_buscado: str, posicion: int) -> pd.Series:
    valores = []
    for _, fila in df.iterrows():
        rnd, valor = _buscar_variable_generada(fila, tipo_buscado)
        valores.append(rnd if posicion == 0 else valor)
    return pd.Series(valores, index=df.index).replace("", "-")


def _serie_orden_cola_futbol_basket(df: pd.DataFrame) -> pd.Series:
    if "Objetos Temporales Activos" not in df.columns:
        return pd.Series(["-"] * len(df), index=df.index)

    return df["Objetos Temporales Activos"].apply(
        lambda resumen: _orden_cola_futbol_basket(resumen) or "-"
    )


def _equipos_temporales_visibles(df: pd.DataFrame, max_objetos_temporales: int | None) -> list[str]:
    equipos = set()
    if "Objetos Temporales Activos" not in df.columns:
        return []

    for resumen in df["Objetos Temporales Activos"]:
        for objeto in _parsear_objetos_temporales(resumen):
            equipos.add(objeto["equipo"])

    equipos_ordenados = sorted(equipos, key=_numero_equipo)
    if max_objetos_temporales is not None:
        return equipos_ordenados[:max_objetos_temporales]
    return equipos_ordenados


def _columnas_objetos_temporales(
    df: pd.DataFrame,
    max_objetos_temporales: int | None = None,
) -> dict[tuple[str, str], pd.Series]:
    columnas = {}
    horas_llegada = _mapear_horas_llegada_visibles(df)
    equipos = _equipos_temporales_visibles(df, max_objetos_temporales)

    for equipo in equipos:
        tipos = []
        estados = []
        horas = []
        for _, fila in df.iterrows():
            objetos = {
                objeto["equipo"]: objeto
                for objeto in _parsear_objetos_temporales(fila.get("Objetos Temporales Activos", ""))
            }
            objeto = objetos.get(equipo)
            tipos.append(objeto["disciplina"] if objeto else "-")
            estados.append(objeto["estado"] if objeto else "-")
            horas.append(horas_llegada.get(equipo, "-") if objeto else "-")

        grupo = f"OBJETOS TEMPORALES - Equipo {_numero_equipo(equipo)}"
        columnas[(grupo, "Tipo")] = pd.Series(tipos, index=df.index)
        columnas[(grupo, "Estado")] = pd.Series(estados, index=df.index)
        columnas[(grupo, "Hora Llegada")] = pd.Series(horas, index=df.index)

    return columnas


def preparar_vector_con_encabezados(
    df: pd.DataFrame,
    max_objetos_temporales: int | None = None,
) -> pd.DataFrame:
    df_base = df.copy()
    columnas_visuales = {
        ("", "N"): _serie_desde_columna(df_base, "N"),
        ("", "Evento"): _serie_desde_columna(df_base, "Evento"),
        ("", "Reloj"): _serie_desde_columna(df_base, "Reloj"),
        ("Llegada GF", "Rnd"): _serie_variable_generada(df_base, "Llegada Futbol", 0),
        ("Llegada GF", "Tiempo Entre Llegada"): _serie_variable_generada(df_base, "Llegada Futbol", 1),
        ("Llegada GF", "Próxima Llegada"): _serie_desde_columna(df_base, "Proxima Llegada Futbol"),
        ("Llegada GH", "Rnd"): _serie_variable_generada(df_base, "Llegada HandBall", 0),
        ("Llegada GH", "Tiempo Entre Llegada"): _serie_variable_generada(df_base, "Llegada HandBall", 1),
        ("Llegada GH", "Próxima Llegada"): _serie_desde_columna(df_base, "Proxima Llegada HandBall"),
        ("Llegada GB", "Rnd"): _serie_variable_generada(df_base, "Llegada Basket", 0),
        ("Llegada GB", "Tiempo Entre Llegada"): _serie_variable_generada(df_base, "Llegada Basket", 1),
        ("Llegada GB", "Próxima Llegada"): _serie_desde_columna(df_base, "Proxima Llegada Basket"),
        ("Cancha", "Estado"): _serie_desde_columna(df_base, "Estado Cancha"),
        ("Cancha", "Disciplina Actual"): _serie_desde_columna(df_base, "Disciplina Actual"),
        ("Cancha", "RND Uso"): pd.concat(
            [
                _serie_variable_generada(df_base, "Uso Futbol", 0),
                _serie_variable_generada(df_base, "Uso HandBall", 0),
                _serie_variable_generada(df_base, "Uso Basket", 0),
            ],
            axis=1,
        ).apply(lambda fila: next((valor for valor in fila if valor != "-"), "-"), axis=1),
        ("Cancha", "Tiempo de uso"): pd.concat(
            [
                _serie_variable_generada(df_base, "Uso Futbol", 1),
                _serie_variable_generada(df_base, "Uso HandBall", 1),
                _serie_variable_generada(df_base, "Uso Basket", 1),
            ],
            axis=1,
        ).apply(lambda fila: next((valor for valor in fila if valor != "-"), "-"), axis=1),
        ("Cancha", "Próximo fin de uso"): _serie_desde_columna(df_base, "Proximo Fin Uso"),
        ("Cancha", "Tiempo de Limpieza"): _serie_desde_columna(df_base, "Tiempo Limpieza Generado"),
        ("Cancha", "Próximo fin de limpieza"): _serie_desde_columna(df_base, "Proximo Fin Limpieza"),
        ("Cancha", "Cola GF"): _serie_desde_columna(df_base, "Cola Futbol"),
        ("Cancha", "Cola GH"): _serie_desde_columna(df_base, "Cola HandBall"),
        ("Cancha", "Cola GB"): _serie_desde_columna(df_base, "Cola Basket"),
        ("Acumuladores / Contadores", "Acumulador Tiempo Espera GF"): _serie_desde_columna(df_base, "Acum Espera Futbol"),
        ("Acumuladores / Contadores", "Acumulador Tiempo Espera GH"): _serie_desde_columna(df_base, "Acum Espera HandBall"),
        ("Acumuladores / Contadores", "Acumulador Tiempo Espera GB"): _serie_desde_columna(df_base, "Acum Espera Basket"),
        ("Acumuladores / Contadores", "Contador Limpiezas"): _serie_desde_columna(df_base, "Cantidad Limpiezas"),
        ("Acumuladores / Contadores", "Acumulador Tiempo Libre Cancha"): _serie_desde_columna(df_base, "Tiempo Libre Acumulado"),
        ("Acumuladores / Contadores", "Contador GF Atendidos"): _serie_desde_columna(df_base, "Cantidad Atendidos Futbol"),
        ("Acumuladores / Contadores", "Contador GH Atendidos"): _serie_desde_columna(df_base, "Cantidad Atendidos HandBall"),
        ("Acumuladores / Contadores", "Contador GB Atendidos"): _serie_desde_columna(df_base, "Cantidad Atendidos Basket"),
        ("Orden Cola Fútbol/Basket", "Orden Cola Fútbol/Basket"): _serie_orden_cola_futbol_basket(df_base),
    }

    columnas_visuales.update(_columnas_objetos_temporales(df_base, max_objetos_temporales))
    columnas_visuales[("Objetos Temporales", "Resumen")] = _serie_desde_columna(
        df_base,
        "Objetos Temporales Activos",
    )

    df_visual = pd.DataFrame(columnas_visuales, index=df_base.index).fillna("-")
    df_visual.columns = pd.MultiIndex.from_tuples(df_visual.columns)
    return df_visual


def _mostrar_metricas(metricas: dict) -> None:
    columnas = st.columns(5)
    claves = [
        "Espera promedio Futbol",
        "Espera promedio HandBall",
        "Espera promedio Basket",
        "Tiempo libre diario promedio de la cancha",
        "Limpiezas promedio por dia",
    ]

    for indice, clave in enumerate(claves):
        valor = metricas.get(clave, 0)
        columnas[indice].metric(clave, f"{valor:.4f}" if isinstance(valor, float) else valor)


def _resumen_integraciones(integraciones: pd.DataFrame) -> pd.DataFrame:
    columnas = [
        "ID Limpieza",
        "Disciplina",
        "D Objetivo",
        "C inicial",
        "h",
        "Metodo",
        "Tiempo resultante de limpieza",
        "Valor final D",
        "Cantidad de pasos",
        "Evento/Fila origen",
    ]
    columnas_presentes = [columna for columna in columnas if columna in integraciones.columns]
    return integraciones[columnas_presentes].copy().round(4)


def _detalle_integraciones_general(integraciones: pd.DataFrame) -> pd.DataFrame:
    if "Pasos internos" not in integraciones.columns:
        return pd.DataFrame()

    filas = []
    for _, integracion in integraciones.iterrows():
        pasos = integracion.get("Pasos internos", [])
        if not isinstance(pasos, list):
            continue
        for paso in pasos:
            filas.append(
                {
                    "ID Limpieza": integracion.get("ID Limpieza", "-"),
                    "Disciplina": integracion.get("Disciplina", "-"),
                    "Metodo": integracion.get("Metodo", "-"),
                    **paso,
                }
            )

    if not filas:
        return pd.DataFrame()

    columnas = [
        "ID Limpieza",
        "Disciplina",
        "Metodo",
        "Paso",
        "t actual",
        "D actual",
        "C",
        "h",
        "f(t,D)",
        "k1",
        "k2",
        "k3",
        "k4",
        "Incremento",
        "D siguiente",
        "D Objetivo",
        "Alcanza objetivo",
    ]
    return pd.DataFrame(filas).reindex(columns=columnas).fillna("-").round(4)


def _detalle_integracion_para_mostrar(detalle: pd.DataFrame, metodo: str) -> pd.DataFrame:
    if detalle.empty:
        return detalle

    if metodo == "RK4":
        columnas = [
            "Paso",
            "t actual",
            "D actual",
            "C",
            "h",
            "k1",
            "k2",
            "k3",
            "k4",
            "Incremento",
            "D siguiente",
            "Alcanza objetivo",
        ]
        detalle_visual = detalle[columnas].copy()
        return detalle_visual.rename(columns={"Incremento": "Incremento RK4"}).round(4)

    columnas = [
        "Paso",
        "t actual",
        "D actual",
        "C",
        "h",
        "f(t,D)",
        "Incremento",
        "D siguiente",
        "Alcanza objetivo",
    ]
    detalle_visual = detalle[columnas].copy()
    return detalle_visual.rename(
        columns={
            "f(t,D)": "f(t,D) = 0.6*C + t",
            "Incremento": "Incremento = h * f(t,D)",
        }
    ).round(4)


def _mostrar_tablas_integracion(integraciones: pd.DataFrame) -> None:
    st.subheader("Tablas de integracion")
    if integraciones.empty:
        st.info("Todavia no se realizaron limpiezas.")
        return

    resumen = _resumen_integraciones(integraciones)
    st.dataframe(resumen, use_container_width=True, height=280)
    st.download_button(
        "Descargar resumen de integraciones en CSV",
        data=resumen.to_csv(index=False).encode("utf-8-sig"),
        file_name="resumen_integraciones.csv",
        mime="text/csv",
    )

    detalle_general = _detalle_integraciones_general(integraciones)
    if detalle_general.empty:
        st.info("Active 'Guardar y mostrar detalle de integraciones' y vuelva a simular para ver los pasos internos.")
        return

    st.download_button(
        "Descargar detalle de integraciones en CSV",
        data=detalle_general.to_csv(index=False).encode("utf-8-sig"),
        file_name="detalle_integraciones.csv",
        mime="text/csv",
    )

    for _, integracion in integraciones.iterrows():
        id_limpieza = integracion.get("ID Limpieza", "-")
        disciplina = integracion.get("Disciplina", "-")
        metodo = integracion.get("Metodo", "-")
        detalle = detalle_general[detalle_general["ID Limpieza"] == id_limpieza]
        if detalle.empty:
            continue

        with st.expander(f"Limpieza {id_limpieza} - {disciplina} - {metodo}"):
            st.dataframe(
                _detalle_integracion_para_mostrar(detalle, metodo),
                use_container_width=True,
                height=300,
            )


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
    mostrar_encabezados_agrupados = st.sidebar.checkbox("Mostrar encabezados agrupados", value=True)
    max_objetos_temporales = st.sidebar.number_input(
        "Cantidad maxima de objetos temporales a mostrar (0 = todos)",
        min_value=0,
        value=0,
        step=1,
    )

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
    guardar_pasos_integracion = st.sidebar.checkbox("Guardar y mostrar detalle de integraciones", value=True)

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
        "mostrar_encabezados_agrupados": mostrar_encabezados_agrupados,
        "max_objetos_temporales": None if int(max_objetos_temporales) == 0 else int(max_objetos_temporales),
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
        "parametros_llegadas": parametros_llegadas,
        "parametros_usos": parametros_usos,
    }


def _mostrar_formulas() -> None:
    with st.expander("Formulas utilizadas"):
        st.markdown(
            """
            **Exponencial negativa**

            `X = -media * ln(1 - RND)`

            **Uniforme**

            `X = a + RND * (b - a)`

            **Ecuacion de limpieza**

            `dD/dt = 0.6 * C + t`,  con `D(0) = 0`.

            **Euler**

            `D siguiente = D actual + h * (coeficiente * C + t actual)`

            **RK4**

            Se calcula con cuatro pendientes intermedias `k1`, `k2`, `k3` y `k4`

            `k1 = 0.6 * C + t_actual`

            `k2 = 0.6 * C + (t_actual + h / 2)`

            `k3 = 0.6 * C + (t_actual + h / 2)`
            
            `k4 = 0.6 * C + (t_actual + h)`
            
            **Ecuación de RK4**

            `D_siguiente = D_actual + (h / 6) * (k1 + 2*k2 + 2*k3 + k4)`

            **Promedios de espera**

            `espera promedio por disciplina = acumulador de espera de la disciplina / cantidad de grupos atendidos de esa disciplina`

            **Tiempo libre diario promedio**

            `tiempo libre diario promedio = tiempo libre acumulado / dias simulados`

            **Limpiezas promedio por dia**

            `limpiezas promedio por dia = cantidad de limpiezas realizadas / dias simulados`

            **Dias simulados**

            `dias simulados = tiempo simulado / 1440`
            """
        )


def main() -> None:
    st.set_page_config(page_title="Simulacion: Polideportivo Alberdi", layout="wide")
    st.title("Simulacion: Polideportivo Alberdi")
    st.caption("Simulacion de eventos discretos - Sistema de colas con prioridad")

    parametros = _parametros_sidebar()

    if st.sidebar.button("Simular", type="primary", use_container_width=True):
        with st.spinner("Simulando eventos..."):
            try:
                resultado = simular(parametros)
            except RuntimeError as error:
                st.error(str(error))
                return
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
    if parametros["mostrar_todas"]:
        st.caption("Mostrando todas las filas simuladas.")
    else:
        st.caption(
            f"Mostrando hasta {parametros['cantidad_filas']} filas "
            f"desde el minuto {parametros['hora_desde']:.4f}."
        )
    vector_estado = resultado["vector_estado"]
    if not vector_estado.empty:
        if parametros["mostrar_encabezados_agrupados"]:
            vector_estado_visual = preparar_vector_con_encabezados(
                vector_estado,
                max_objetos_temporales=parametros["max_objetos_temporales"],
            )
            st.dataframe(vector_estado_visual, use_container_width=True, height=600)
        else:
            st.dataframe(vector_estado, use_container_width=True, height=600)
    else:
        st.warning("No se generaron filas para mostrar.")

    _mostrar_tablas_integracion(resultado["integraciones"])

    _mostrar_formulas()


if __name__ == "__main__":
    main()
