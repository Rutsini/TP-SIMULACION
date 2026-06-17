"""Interfaz Streamlit para la simulacion del Polideportivo Alberdi."""

from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from simulacion.motor import simular


def aplicar_supertitulos_vector(df: pd.DataFrame) -> pd.DataFrame:
    grupos = {
        "Evento": [
            "N",
            "Reloj",
            "Evento",
            "RND usado",
            "Valor generado",
            "Tipo variable generada",
        ],
        "Llegada GF": [
            "Proxima Llegada Futbol",
        ],
        "Llegada GH": [
            "Proxima Llegada HandBall",
        ],
        "Llegada GB": [
            "Proxima Llegada Basket",
        ],
        "Cancha": [
            "Estado Cancha",
            "Disciplina Actual",
            "ID Grupo Actual",
            "Ultimo RND Uso",
            "Proximo Fin Uso",
        ],
        "Limpieza": [
            "ID Limpieza",
            "Metodo Integracion",
            "h Integracion",
            "Valor Integracion Limpieza",
            "Tiempo Limpieza Generado",
            "D Objetivo Limpieza",
            "C al iniciar limpieza",
            "Proximo Fin Limpieza",
        ],
        "Colas": [
            "Cola Futbol",
            "Cola HandBall",
            "Cola Basket",
            "Cola Total",
        ],
        "Acumuladores y Contadores": [
            "Acum Espera Futbol",
            "Acum Espera HandBall",
            "Acum Espera Basket",
            "Cantidad Atendidos Futbol",
            "Cantidad Atendidos HandBall",
            "Cantidad Atendidos Basket",
            "Retirados Futbol",
            "Retirados HandBall",
            "Retirados Basket",
            "Tiempo Libre Acumulado",
            "Tiempo Ocupado Acumulado",
            "Cantidad Limpiezas",
            "Maxima Cola Total",
        ],
        "Objetos Temporales": [
            "Objetos Temporales Activos",
        ],
    }

    columnas_con_grupo = []
    for columna in df.columns:
        grupo_encontrado = "Otros"
        for grupo, columnas in grupos.items():
            if columna in columnas:
                grupo_encontrado = grupo
                break
        columnas_con_grupo.append((grupo_encontrado, columna))

    df_visual = df.copy()
    df_visual.columns = pd.MultiIndex.from_tuples(columnas_con_grupo)
    return df_visual


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
                "disciplina": disciplina,
                "estado": _estado_objeto_legible(estado),
            }
        )
    return objetos


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


def _preparar_vector_excel(
    df: pd.DataFrame,
    mostrar_objetos_en_columnas: bool,
    max_objetos_temporales: int,
) -> pd.DataFrame:
    df_visual = df.copy()

    for disciplina in ("Futbol", "HandBall", "Basket"):
        rnds = []
        tiempos = []
        for _, fila in df_visual.iterrows():
            rnd, tiempo = _buscar_variable_generada(fila, f"Llegada {disciplina}")
            rnds.append(rnd)
            tiempos.append(tiempo)
        df_visual[f"RND Llegada {disciplina}"] = rnds
        df_visual[f"Tiempo Entre Llegada {disciplina}"] = tiempos

    rnds_uso = []
    tiempos_uso = []
    for _, fila in df_visual.iterrows():
        rnd_uso = ""
        tiempo_uso = ""
        for disciplina in ("Futbol", "HandBall", "Basket"):
            rnd, tiempo = _buscar_variable_generada(fila, f"Uso {disciplina}")
            if rnd or tiempo:
                rnd_uso = rnd
                tiempo_uso = tiempo
                break
        rnds_uso.append(rnd_uso)
        tiempos_uso.append(tiempo_uso)
    df_visual["RND Uso"] = rnds_uso
    df_visual["Tiempo de Uso"] = tiempos_uso

    if "Objetos Temporales Activos" in df_visual.columns:
        df_visual["Orden Cola Futbol/Basket"] = df_visual["Objetos Temporales Activos"].apply(
            _orden_cola_futbol_basket
        )
    else:
        df_visual["Orden Cola Futbol/Basket"] = ""

    if mostrar_objetos_en_columnas:
        horas_llegada = _mapear_horas_llegada_visibles(df_visual)
        for numero_objeto in range(1, max_objetos_temporales + 1):
            equipos = []
            tipos = []
            estados = []
            horas = []
            for _, fila in df_visual.iterrows():
                objetos = _parsear_objetos_temporales(fila.get("Objetos Temporales Activos", ""))
                objeto = objetos[numero_objeto - 1] if numero_objeto <= len(objetos) else None
                equipos.append(objeto["equipo"] if objeto else "")
                tipos.append(objeto["disciplina"] if objeto else "")
                estados.append(objeto["estado"] if objeto else "")
                horas.append(horas_llegada.get(objeto["equipo"], "") if objeto else "")
            df_visual[f"Equipo {numero_objeto}"] = equipos
            df_visual[f"Equipo {numero_objeto} Tipo"] = tipos
            df_visual[f"Equipo {numero_objeto} Estado"] = estados
            df_visual[f"Equipo {numero_objeto} Hora Llegada"] = horas

    return df_visual


def _bloques_vector_excel(mostrar_objetos_en_columnas: bool, max_objetos_temporales: int) -> list[tuple[str, list[str]]]:
    bloques = [
        ("Evento", ["N", "Evento", "Reloj"]),
        (
            "Llegada GF",
            ["RND Llegada Futbol", "Tiempo Entre Llegada Futbol", "Proxima Llegada Futbol"],
        ),
        (
            "Llegada GH",
            ["RND Llegada HandBall", "Tiempo Entre Llegada HandBall", "Proxima Llegada HandBall"],
        ),
        (
            "Llegada GB",
            ["RND Llegada Basket", "Tiempo Entre Llegada Basket", "Proxima Llegada Basket"],
        ),
        (
            "Cancha",
            [
                "Estado Cancha",
                "Disciplina Actual",
                "ID Grupo Actual",
                "RND Uso",
                "Tiempo de Uso",
                "Proximo Fin Uso",
                "Tiempo Limpieza Generado",
                "Proximo Fin Limpieza",
                "Cola Futbol",
                "Cola HandBall",
                "Cola Basket",
            ],
        ),
        (
            "Limpieza",
            [
                "ID Limpieza",
                "Metodo Integracion",
                "h Integracion",
                "Valor Integracion Limpieza",
                "D Objetivo Limpieza",
                "C al iniciar limpieza",
            ],
        ),
        (
            "Acumuladores / Contadores",
            [
                "Acum Espera Futbol",
                "Acum Espera HandBall",
                "Acum Espera Basket",
                "Cantidad Limpiezas",
                "Tiempo Libre Acumulado",
                "Cantidad Atendidos Futbol",
                "Cantidad Atendidos HandBall",
                "Cantidad Atendidos Basket",
                "Retirados Futbol",
                "Retirados HandBall",
                "Retirados Basket",
                "Maxima Cola Total",
            ],
        ),
        ("Orden Cola Futbol/Basket", ["Orden Cola Futbol/Basket"]),
    ]

    if mostrar_objetos_en_columnas:
        columnas_objetos = []
        for numero_objeto in range(1, max_objetos_temporales + 1):
            columnas_objetos.extend(
                [
                    f"Equipo {numero_objeto}",
                    f"Equipo {numero_objeto} Tipo",
                    f"Equipo {numero_objeto} Estado",
                    f"Equipo {numero_objeto} Hora Llegada",
                ]
            )
        bloques.append(("Objetos Temporales", columnas_objetos + ["Objetos Temporales Activos"]))
    else:
        bloques.append(("Objetos Temporales", ["Objetos Temporales Activos"]))

    return bloques


def _color_bloque(nombre: str) -> str:
    colores = {
        "Evento": "#f3f4f6",
        "Llegada GF": "#dbeafe",
        "Llegada GH": "#dbeafe",
        "Llegada GB": "#dbeafe",
        "Cancha": "#fee2e2",
        "Limpieza": "#fef3c7",
        "Acumuladores / Contadores": "#e5e7eb",
        "Orden Cola Futbol/Basket": "#ede9fe",
        "Objetos Temporales": "#dcfce7",
        "Otros": "#f8fafc",
    }
    return colores.get(nombre, "#f8fafc")


def renderizar_vector_excel(
    df: pd.DataFrame,
    mostrar_objetos_en_columnas: bool = False,
    max_objetos_temporales: int = 3,
) -> str:
    df_visual = _preparar_vector_excel(
        df,
        mostrar_objetos_en_columnas=mostrar_objetos_en_columnas,
        max_objetos_temporales=max_objetos_temporales,
    )
    bloques = _bloques_vector_excel(mostrar_objetos_en_columnas, max_objetos_temporales)

    columnas_ordenadas = []
    grupos_por_columna = {}
    for grupo, columnas in bloques:
        for columna in columnas:
            if columna in df_visual.columns and columna not in columnas_ordenadas:
                columnas_ordenadas.append(columna)
                grupos_por_columna[columna] = grupo

    columnas_otros = [
        columna
        for columna in df_visual.columns
        if columna not in columnas_ordenadas
    ]
    if columnas_otros:
        for columna in columnas_otros:
            grupos_por_columna[columna] = "Otros"
        columnas_ordenadas.extend(columnas_otros)
        bloques.append(("Otros", columnas_otros))

    encabezado_grupos = []
    for grupo, columnas in bloques:
        columnas_presentes = [columna for columna in columnas if columna in columnas_ordenadas]
        if not columnas_presentes:
            continue
        color = _color_bloque(grupo)
        encabezado_grupos.append(
            f'<th colspan="{len(columnas_presentes)}" style="background:{color};">{escape(grupo)}</th>'
        )

    encabezado_columnas = []
    for columna in columnas_ordenadas:
        color = _color_bloque(grupos_por_columna[columna])
        encabezado_columnas.append(
            f'<th style="background:{color};">{escape(str(columna))}</th>'
        )

    filas_html = []
    for _, fila in df_visual[columnas_ordenadas].iterrows():
        celdas = []
        for columna in columnas_ordenadas:
            color = _color_bloque(grupos_por_columna[columna])
            valor = "" if pd.isna(fila[columna]) else fila[columna]
            celdas.append(
                f'<td style="background:{color};">{escape(str(valor))}</td>'
            )
        filas_html.append(f"<tr>{''.join(celdas)}</tr>")

    return f"""
    <style>
        .vector-excel-container {{
            overflow: auto;
            max-height: 650px;
            border: 1px solid #c7ccd1;
            border-radius: 4px;
        }}
        .vector-excel {{
            border-collapse: collapse;
            width: max-content;
            min-width: 100%;
            font-size: 12px;
            line-height: 1.25;
            color: #111827;
        }}
        .vector-excel th,
        .vector-excel td {{
            border: 1px solid #c7ccd1;
            padding: 4px 6px;
            text-align: center;
            vertical-align: middle;
            white-space: nowrap;
            min-width: 86px;
        }}
        .vector-excel thead tr:first-child th {{
            position: sticky;
            top: 0;
            z-index: 3;
            font-weight: 700;
        }}
        .vector-excel thead tr:nth-child(2) th {{
            position: sticky;
            top: 27px;
            z-index: 2;
            font-weight: 600;
        }}
    </style>
    <div class="vector-excel-container">
        <table class="vector-excel">
            <thead>
                <tr>{''.join(encabezado_grupos)}</tr>
                <tr>{''.join(encabezado_columnas)}</tr>
            </thead>
            <tbody>
                {''.join(filas_html)}
            </tbody>
        </table>
    </div>
    """


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
    mostrar_vector_excel = st.sidebar.checkbox("Mostrar vector con formato tipo Excel", value=True)
    formato_objetos_temporales = st.sidebar.radio(
        "Objetos temporales",
        ["Resumen", "Columnas"],
        horizontal=True,
    )
    max_objetos_temporales = 3
    if formato_objetos_temporales == "Columnas":
        max_objetos_temporales = st.sidebar.number_input(
            "Cantidad maxima de objetos temporales a mostrar como columnas",
            min_value=1,
            max_value=20,
            value=3,
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
        "mostrar_vector_excel": mostrar_vector_excel,
        "mostrar_objetos_en_columnas": formato_objetos_temporales == "Columnas",
        "max_objetos_temporales": int(max_objetos_temporales),
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
    if parametros["mostrar_todas"]:
        st.caption("Mostrando todas las filas simuladas.")
    else:
        st.caption(
            f"Mostrando hasta {parametros['cantidad_filas']} filas "
            f"desde el minuto {parametros['hora_desde']:.4f}."
        )
    vector_estado = resultado["vector_estado"]
    if not vector_estado.empty:
        if parametros["mostrar_vector_excel"]:
            html_vector = renderizar_vector_excel(
                vector_estado,
                mostrar_objetos_en_columnas=parametros["mostrar_objetos_en_columnas"],
                max_objetos_temporales=parametros["max_objetos_temporales"],
            )
            st.markdown(html_vector, unsafe_allow_html=True)
        else:
            st.dataframe(vector_estado, use_container_width=True, height=820)
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
