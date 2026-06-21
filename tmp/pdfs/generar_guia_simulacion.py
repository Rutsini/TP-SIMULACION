from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output" / "pdf" / "guia_logica_simulacion_polideportivo_alberdi.pdf"


def registrar_fuentes():
    fuentes = [
        (
            "DejaVu",
            "DejaVu-Bold",
            Path(r"C:\Windows\Fonts\DejaVuSans.ttf"),
            Path(r"C:\Windows\Fonts\DejaVuSans-Bold.ttf"),
        ),
        (
            "Arial",
            "Arial-Bold",
            Path(r"C:\Windows\Fonts\arial.ttf"),
            Path(r"C:\Windows\Fonts\arialbd.ttf"),
        ),
    ]
    for normal, bold, normal_path, bold_path in fuentes:
        if normal_path.exists() and bold_path.exists():
            pdfmetrics.registerFont(TTFont(normal, str(normal_path)))
            pdfmetrics.registerFont(TTFont(bold, str(bold_path)))
            return normal, bold
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = registrar_fuentes()
AZUL = colors.HexColor("#173B57")
CELESTE = colors.HexColor("#EAF3F8")
TURQUESA = colors.HexColor("#2C7A7B")
GRIS = colors.HexColor("#52616B")
GRIS_CLARO = colors.HexColor("#F4F6F7")
BORDE = colors.HexColor("#C9D3D9")
NARANJA = colors.HexColor("#D97706")


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="TituloGuia",
        parent=styles["Title"],
        fontName=FONT_BOLD,
        fontSize=25,
        leading=30,
        textColor=AZUL,
        alignment=TA_LEFT,
        spaceAfter=12,
    )
)
styles.add(
    ParagraphStyle(
        name="SubtituloGuia",
        parent=styles["Normal"],
        fontName=FONT,
        fontSize=11.5,
        leading=17,
        textColor=GRIS,
        spaceAfter=16,
    )
)
styles.add(
    ParagraphStyle(
        name="H1Guia",
        parent=styles["Heading1"],
        fontName=FONT_BOLD,
        fontSize=17,
        leading=21,
        textColor=AZUL,
        spaceBefore=7,
        spaceAfter=9,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="H2Guia",
        parent=styles["Heading2"],
        fontName=FONT_BOLD,
        fontSize=12.5,
        leading=16,
        textColor=TURQUESA,
        spaceBefore=7,
        spaceAfter=5,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="CuerpoGuia",
        parent=styles["BodyText"],
        fontName=FONT,
        fontSize=9.6,
        leading=14.2,
        textColor=colors.HexColor("#202A30"),
        spaceAfter=7,
    )
)
styles.add(
    ParagraphStyle(
        name="BulletGuia",
        parent=styles["BodyText"],
        fontName=FONT,
        fontSize=9.5,
        leading=13.7,
        leftIndent=15,
        firstLineIndent=-8,
        bulletIndent=4,
        textColor=colors.HexColor("#202A30"),
        spaceAfter=4,
    )
)
styles.add(
    ParagraphStyle(
        name="CodigoGuia",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8.2,
        leading=11.2,
        leftIndent=9,
        rightIndent=9,
        borderColor=BORDE,
        borderWidth=0.6,
        borderPadding=8,
        backColor=GRIS_CLARO,
        spaceBefore=4,
        spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(
        name="LlamadoGuia",
        parent=styles["BodyText"],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=15,
        textColor=AZUL,
        borderColor=TURQUESA,
        borderWidth=0,
        borderLeftWidth=3,
        borderPadding=8,
        backColor=CELESTE,
        spaceBefore=5,
        spaceAfter=10,
    )
)
styles.add(
    ParagraphStyle(
        name="Tabla",
        parent=styles["BodyText"],
        fontName=FONT,
        fontSize=7.7,
        leading=10,
        textColor=colors.HexColor("#202A30"),
    )
)
styles.add(
    ParagraphStyle(
        name="TablaHeader",
        parent=styles["BodyText"],
        fontName=FONT_BOLD,
        fontSize=7.7,
        leading=10,
        textColor=colors.white,
        alignment=TA_CENTER,
    )
)


def P(text, style="CuerpoGuia"):
    return Paragraph(text, styles[style])


def bullet(text):
    return Paragraph("- " + text, styles["BulletGuia"])


def tabla(datos, anchos, encabezado=True):
    filas = []
    for i, fila in enumerate(datos):
        estilo = "TablaHeader" if encabezado and i == 0 else "Tabla"
        filas.append([P(str(celda), estilo) for celda in fila])
    t = Table(filas, colWidths=anchos, repeatRows=1 if encabezado else 0, hAlign="LEFT")
    comandos = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.45, BORDE),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if encabezado:
        comandos.append(("BACKGROUND", (0, 0), (-1, 0), AZUL))
        if len(filas) > 1:
            comandos.append(("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]))
    t.setStyle(TableStyle(comandos))
    return t


class GuiaDoc(BaseDocTemplate):
    pass


def encabezado_pie(canvas, doc):
    canvas.saveState()
    ancho, alto = A4
    canvas.setStrokeColor(BORDE)
    canvas.setLineWidth(0.5)
    canvas.line(1.7 * cm, alto - 1.35 * cm, ancho - 1.7 * cm, alto - 1.35 * cm)
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(GRIS)
    canvas.drawString(1.7 * cm, alto - 1.08 * cm, "TP 5 - Simulacion | Polideportivo Alberdi")
    canvas.drawRightString(ancho - 1.7 * cm, 0.9 * cm, f"Pagina {doc.page}")
    canvas.restoreState()


story = []
story += [
    Spacer(1, 0.65 * cm),
    P("Guia para comprender la simulacion", "TituloGuia"),
    P("Polideportivo Alberdi - logica de resolucion y lectura fila por fila", "SubtituloGuia"),
    P(
        "Objetivo: entender primero <b>como piensa el motor</b>, como se resuelve cada evento y como se construye una fila del vector de estado. La parte visual de Streamlit se presenta al final como una capa separada.",
        "LlamadoGuia",
    ),
    P("1. La idea central", "H1Guia"),
    P(
        "El programa implementa una <b>simulacion de eventos discretos</b>. El reloj no avanza minuto a minuto. En cada iteracion se busca el evento futuro con menor hora, el reloj salta directamente hasta esa hora, se actualizan acumuladores, se procesa el evento y se registra una nueva fila.",
    ),
    P("La regla mental para leer el vector de estado es:", "H2Guia"),
    P(
        "Fila anterior -> elegir el menor evento futuro -> avanzar el reloj -> ejecutar todas las consecuencias -> escribir la nueva fila.",
        "LlamadoGuia",
    ),
    P("Importante: la fila muestra el estado <b>despues</b> de procesar el evento que figura en su columna Evento.", "CuerpoGuia"),
    P("2. Eventos administrados", "H1Guia"),
]

for item in [
    "Llegada Futbol.",
    "Llegada HandBall.",
    "Llegada Basket.",
    "Fin Uso Cancha.",
    "Fin Limpieza.",
    "Fin Simulacion.",
]:
    story.append(bullet(item))

story += [
    P(
        "Los eventos que no estan programados tienen valor infinito. Por ejemplo, si nadie usa la cancha, Fin Uso Cancha queda en infinito. La funcion <b>_evento_minimo()</b> compara el diccionario de eventos y selecciona la hora menor.",
    ),
    P("3. Estado del sistema", "H1Guia"),
    P("El diccionario <b>estado</b> funciona como la memoria completa de la simulacion. Contiene:", "CuerpoGuia"),
]

for item in [
    "Reloj actual.",
    "Estado de la cancha: Libre, Ocupada o En Limpieza.",
    "Disciplina y grupo que estan usando la cancha.",
    "Una cola por disciplina.",
    "Objetos temporales correspondientes a los grupos activos.",
    "Horas de todos los eventos futuros.",
    "Acumuladores de espera, tiempo libre y tiempo ocupado.",
    "Contadores de atendidos, retirados y limpiezas.",
]:
    story.append(bullet(item))

story += [
    P("4. Distribuciones utilizadas", "H1Guia"),
    tabla(
        [
            ["Variable", "Distribucion", "Formula predeterminada"],
            ["Llegada Futbol", "Exponencial negativa", "X = -600 ln(1 - RND)"],
            ["Llegada HandBall", "Uniforme", "X = 600 + RND (840 - 600)"],
            ["Llegada Basket", "Uniforme", "X = 360 + RND (600 - 360)"],
            ["Uso Futbol", "Uniforme", "X = 80 + RND (100 - 80)"],
            ["Uso HandBall", "Uniforme", "X = 60 + RND (100 - 60)"],
            ["Uso Basket", "Uniforme", "X = 70 + RND (130 - 70)"],
        ],
        [4.0 * cm, 4.0 * cm, 8.6 * cm],
    ),
    Spacer(1, 8),
    P(
        "Un tiempo entre llegadas es una duracion. Para programar la llegada absoluta se suma al reloj: <b>proxima llegada = reloj actual + tiempo entre llegadas</b>.",
        "LlamadoGuia",
    ),
    P("5. Inicializacion con semilla 42", "H1Guia"),
    P(
        "Para seguir numeros reproducibles se ejecuto el motor con semilla 42 y parametros predeterminados. En el instante cero se generan las tres primeras llegadas.",
    ),
    tabla(
        [
            ["Disciplina", "RND", "Calculo", "Hora programada"],
            ["Futbol", "0.7740", "-600 ln(1 - 0.7740)", "892.2155"],
            ["HandBall", "0.4389", "600 + 0.4389 x 240", "705.3308"],
            ["Basket", "0.8586", "360 + 0.8586 x 240", "566.0635"],
        ],
        [3.0 * cm, 2.2 * cm, 6.7 * cm, 4.3 * cm],
    ),
    Spacer(1, 8),
    P("La fila de inicializacion queda conceptualmente asi:", "H2Guia"),
    P(
        "N = 0<br/>Reloj = 0<br/>Evento = Inicializacion<br/>Cancha = Libre<br/>Proxima Basket = 566.0635<br/>Proxima HandBall = 705.3308<br/>Proxima Futbol = 892.2155",
        "CodigoGuia",
    ),
    P(
        "Como 566.0635 es la menor de las horas programadas, el primer evento real sera <b>Llegada Basket</b>.",
    ),
    P("6. Ejecucion completa de la fila N = 1", "H1Guia"),
    P("Evento: Llegada Basket. Hora del evento: 566.0635.", "LlamadoGuia"),
    P("Paso A - Avanzar el reloj", "H2Guia"),
    P(
        "El reloj pasa de 0 a 566.0635. Como la cancha estuvo Libre durante todo el intervalo, ese delta se suma al tiempo libre acumulado.",
    ),
    P("delta = 566.0635 - 0 = 566.0635<br/>tiempo libre acumulado = 566.0635", "CodigoGuia"),
    P("Paso B - Programar la siguiente llegada de Basket", "H2Guia"),
    P(
        "Cada llegada programa inmediatamente la siguiente llegada de su misma disciplina. El nuevo RND es 0.6974.",
    ),
    P(
        "tiempo entre llegadas = 360 + 0.6974 x 240 = 527.3683<br/>proxima llegada Basket = 566.0635 + 527.3683 = 1093.4318",
        "CodigoGuia",
    ),
    P("Paso C - Verificar capacidad y crear el grupo", "H2Guia"),
    P(
        "La cola total vale 0 y la capacidad maxima es 5. Como 0 no es mayor ni igual que 5, el grupo no se retira. Se crea G1, disciplina Basket, inicialmente En Cola, con hora de llegada 566.0635.",
    ),
    P("Paso D - Iniciar el uso de la cancha", "H2Guia"),
    P(
        "Como la cancha estaba Libre, G1 es seleccionado inmediatamente. Sale de la cola, cambia a En Cancha y su espera queda en cero.",
    ),
    P(
        "tiempo espera G1 = 566.0635 - 566.0635 = 0<br/>RND uso = 0.0942<br/>tiempo uso Basket = 70 + 0.0942 x 60 = 75.6506<br/>fin de uso = 566.0635 + 75.6506 = 641.7141",
        "CodigoGuia",
    ),
    P("Resultado de la fila N = 1", "H2Guia"),
    tabla(
        [
            ["Campo", "Valor despues del evento"],
            ["Reloj", "566.0635"],
            ["Evento", "Llegada Basket"],
            ["Estado cancha", "Ocupada"],
            ["Disciplina / grupo actual", "Basket / G1"],
            ["Cola Basket", "0"],
            ["Proxima llegada Basket", "1093.4318"],
            ["Proximo fin de uso", "641.7141"],
            ["Tiempo libre acumulado", "566.0635"],
            ["Objeto activo", "G1-Basket-EnCancha"],
        ],
        [6.2 * cm, 10.0 * cm],
    ),
    Spacer(1, 8),
    P(
        "La cola Basket aparece en cero porque G1 se agrega a la cola y, en la misma ejecucion del evento, se retira para entrar a una cancha que estaba libre.",
        "LlamadoGuia",
    ),
    P("7. Ejecucion de la fila N = 2", "H1Guia"),
    P("Evento: Fin Uso Cancha. Hora del evento: 641.7141.", "LlamadoGuia"),
    P(
        "El reloj avanza desde 566.0635 hasta 641.7141. El delta es 75.6506 y, como la cancha estaba Ocupada, se suma al tiempo ocupado acumulado.",
    ),
    P("delta = 641.7141 - 566.0635 = 75.6506<br/>tiempo ocupado acumulado = 75.6506", "CodigoGuia"),
    P("Luego el grupo G1 finaliza:", "H2Guia"),
]

for item in [
    "Su hora de salida se fija en 641.7141.",
    "Su espera, que era 0, se agrega al acumulador de Basket.",
    "El contador de atendidos Basket pasa a 1.",
    "G1 se elimina de los objetos temporales activos.",
    "Se calcula el tiempo de limpieza y la cancha pasa a En Limpieza.",
]:
    story.append(bullet(item))

story += [
    P("8. Resolucion numerica de la limpieza", "H1Guia"),
    P("La ecuacion diferencial usada es:", "CuerpoGuia"),
    P("dD/dt = 0.6 C + t, con D(0) = 0", "CodigoGuia"),
    P(
        "C es la cantidad total de grupos que esperan al comenzar la limpieza. Para la primera limpieza C = 0, el objetivo de Basket es D = 300 y h = 0.1. Entonces la derivada queda dD/dt = t.",
    ),
    P("Metodo de Euler", "H2Guia"),
    P("D siguiente = D actual + h (0.6 C + t actual)", "CodigoGuia"),
    tabla(
        [
            ["Paso", "t actual", "D actual", "f(t,D)", "Incremento", "D siguiente"],
            ["1", "0.0", "0.00", "0.0", "0.00", "0.00"],
            ["2", "0.1", "0.00", "0.1", "0.01", "0.01"],
            ["3", "0.2", "0.01", "0.2", "0.02", "0.03"],
            ["4", "0.3", "0.03", "0.3", "0.03", "0.06"],
        ],
        [1.7 * cm, 2.4 * cm, 2.5 * cm, 2.3 * cm, 3.0 * cm, 3.0 * cm],
    ),
    Spacer(1, 8),
    P(
        "El ciclo continua hasta que D alcanza o supera 300. Se requieren 246 pasos: t = 24.6 y D final = 301.35. Por eso el fin de limpieza se programa en 641.7141 + 24.6 = 666.3141.",
        "LlamadoGuia",
    ),
    P("Metodo RK4", "H2Guia"),
    P(
        "Si se selecciona RK4, cada paso calcula cuatro pendientes intermedias k1, k2, k3 y k4. Luego combina esas pendientes para estimar mejor el incremento. El motor elige entre Euler y RK4 mediante el parametro metodo_integracion.",
    ),
    P("9. Fin de limpieza", "H1Guia"),
    P(
        "Cuando ocurre Fin Limpieza, la cancha pasa a Libre, el evento Fin Limpieza vuelve a infinito y el motor intenta seleccionar el siguiente grupo. Si hay alguien esperando, inicia su uso en esa misma fila; si no, la cancha permanece libre.",
    ),
    P("10. Regla de prioridad", "H1Guia"),
    P(
        "La funcion seleccionar_proximo_grupo implementa una prioridad especifica:",
    ),
]

for item in [
    "Si esperan grupos de Futbol o Basket, se comparan los primeros de esas dos colas y gana el que llego antes.",
    "HandBall se selecciona solamente cuando no espera ningun grupo de Futbol ni de Basket.",
    "Dentro de cada disciplina se mantiene el orden FIFO: primero en llegar, primero en salir.",
]:
    story.append(bullet(item))

story += [
    P("11. Objetos temporales", "H1Guia"),
    P(
        "Cada grupo es un objeto temporal mientras esta esperando o usando la cancha. Guarda id, disciplina, estado, hora de llegada, inicio de uso, salida y espera. Ejemplos de resumen:",
    ),
    P("G3-Futbol-EnCancha<br/>G4-Basket-EnCola", "CodigoGuia"),
    P(
        "Al finalizar el uso, el objeto se elimina. Sus datos relevantes ya quedaron incorporados en acumuladores y contadores.",
    ),
    P("12. Acumuladores, contadores y metricas", "H1Guia"),
    tabla(
        [
            ["Resultado", "Formula"],
            ["Espera promedio por disciplina", "Acumulador de espera / cantidad atendida"],
            ["Dias simulados", "Tiempo simulado / 1440"],
            ["Tiempo libre diario promedio", "Tiempo libre acumulado / dias simulados"],
            ["Limpiezas promedio por dia", "Cantidad de limpiezas / dias simulados"],
        ],
        [6.0 * cm, 10.3 * cm],
    ),
    Spacer(1, 8),
    P(
        "El tiempo se acumula segun el estado previo de la cancha durante cada salto del reloj. Si estaba Libre suma tiempo libre; si estaba Ocupada suma tiempo ocupado. El tiempo En Limpieza no se incluye en ninguno de esos dos acumuladores.",
        "LlamadoGuia",
    ),
    P("13. Flujo completo del motor", "H1Guia"),
]

for paso in [
    "Crear el generador aleatorio y el estado inicial.",
    "Programar Fin Simulacion.",
    "Generar la primera llegada de cada disciplina.",
    "Guardar la fila N = 0 de Inicializacion.",
    "Buscar el evento con hora minima.",
    "Actualizar tiempos acumulados usando el delta del reloj.",
    "Procesar la llegada, el fin de uso o el fin de limpieza.",
    "Crear la fila con el estado resultante.",
    "Repetir hasta Fin Simulacion o hasta superar el maximo de iteraciones.",
    "Calcular las metricas finales y devolver DataFrames para la interfaz.",
]:
    story.append(bullet(paso))

story += [
    P("14. Mapa de archivos", "H1Guia"),
    tabla(
        [
            ["Archivo", "Responsabilidad"],
            ["simulacion/motor.py", "Ciclo de eventos, llegadas, usos, limpiezas y creacion de filas."],
            ["simulacion/estado.py", "Estado inicial, objetos temporales, colas y prioridad."],
            ["simulacion/distribuciones.py", "Transformacion de RND en tiempos de llegada y uso."],
            ["simulacion/integracion.py", "Calculo del tiempo de limpieza mediante Euler o RK4."],
            ["simulacion/metricas.py", "Calculo de promedios y resultados finales."],
            ["app.py", "Parametros de Streamlit y presentacion visual de resultados."],
        ],
        [5.1 * cm, 11.2 * cm],
    ),
    Spacer(1, 8),
    PageBreak(),
    P("15. Como interpretar cualquier fila", "H1Guia"),
    P("Frente a una fila del vector de estado, conviene responder en este orden:", "CuerpoGuia"),
]

for item in [
    "Que evento ocurrio y a que hora.",
    "Desde que hora venia el reloj y cual fue el delta.",
    "En que estado estuvo la cancha durante ese delta.",
    "Que acumulador aumento.",
    "Que objeto se creo, cambio o elimino.",
    "Que RND se uso y que variable produjo.",
    "Que nuevo evento futuro se programo.",
    "Como quedaron las colas, la cancha y los contadores despues del evento.",
]:
    story.append(bullet(item))

story += [
    P(
        "Si se sigue ese orden, cada fila deja de ser una tabla enorme y pasa a ser una historia corta: ocurrio un evento, cambio una parte del estado y quedaron programadas las proximas acciones.",
        "LlamadoGuia",
    ),
    P("16. Capa visual de la aplicacion", "H1Guia"),
    P(
        "app.py no decide la logica del sistema. Su funcion principal es leer parametros desde la barra lateral, llamar a simular(parametros), reorganizar columnas para mostrarlas con encabezados agrupados y presentar metricas, vector de estado y tablas de integracion. Por eso, para comprobar la resolucion de los ejercicios, primero se debe mirar simulacion/motor.py y sus modulos auxiliares; app.py se estudia despues como capa de presentacion.",
    ),
]


OUTPUT.parent.mkdir(parents=True, exist_ok=True)
doc = GuiaDoc(
    str(OUTPUT),
    pagesize=A4,
    leftMargin=1.7 * cm,
    rightMargin=1.7 * cm,
    topMargin=1.7 * cm,
    bottomMargin=1.5 * cm,
    title="Guia de logica de simulacion - Polideportivo Alberdi",
    author="Codex",
)
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
doc.addPageTemplates([PageTemplate(id="guia", frames=[frame], onPage=encabezado_pie)])
doc.build(story)
print(OUTPUT)
