import streamlit as st
import math
import random
import networkx as nx
import matplotlib.pyplot as plt
from itertools import permutations


def obtener_aristas_faltantes(recorrido, aristas):
    """Identifica las conexiones faltantes para cerrar un recorrido."""
    faltantes = []

    for i in range(len(recorrido)):
        nodo_a = recorrido[i]
        nodo_b = recorrido[(i + 1) % len(recorrido)]

        arista = tuple(sorted([nodo_a, nodo_b]))

        if arista not in aristas:
            faltantes.append(arista)

    return faltantes


def generar_recorridos(nodos):
    """Genera candidatos sin repetir el inicio ni el sentido inverso."""
    inicio = nodos[0]
    restantes = nodos[1:]

    for orden in permutations(restantes):
        if orden[0] < orden[-1]:
            recorrido = [inicio] + list(orden)
            yield recorrido


def diagnosticar_grafo(nodos, aristas):
    """Busca un ciclo válido o una propuesta con menos aristas faltantes."""
    mejor_recorrido = None
    mejores_faltantes = None

    for recorrido in generar_recorridos(nodos):
        faltantes = obtener_aristas_faltantes(recorrido, aristas)

        if not faltantes:
            return {"tiene_ciclo": True, "recorrido": recorrido, "faltantes": []}

        if mejores_faltantes is None or len(faltantes) < len(mejores_faltantes):
            mejor_recorrido = recorrido
            mejores_faltantes = faltantes

    return {
        "tiene_ciclo": False,
        "recorrido": mejor_recorrido,
        "faltantes": mejores_faltantes,
    }


def reiniciar_busqueda():
    """Borra el progreso de la búsqueda de ciclos."""
    st.session_state["busqueda"] = {
        "iniciada": False,
        "terminada": False,
        "generador": None,
        "recorrido_actual": None,
        "indice_conexion": 0,
        "aristas_comprobadas": [],
        "arista_faltante": None,
        "ciclos_validos": [],
        "candidatos_revisados": 0,
        "mensaje": "",
        "resultados": None,
    }


def comprobar_siguiente_conexion():
    """Comprueba una conexión del recorrido actual."""
    busqueda = st.session_state["busqueda"]
    recorrido = busqueda["recorrido_actual"]
    i = busqueda["indice_conexion"]

    if recorrido is None:
        return

    if busqueda["arista_faltante"] is not None or i >= len(recorrido):
        siguiente = next(busqueda["generador"], None)

        busqueda["recorrido_actual"] = siguiente
        busqueda["indice_conexion"] = 0
        busqueda["aristas_comprobadas"] = []
        busqueda["arista_faltante"] = None

        if siguiente is None:
            busqueda["terminada"] = True
            busqueda["mensaje"] = (
                "Búsqueda terminada. " "Se revisaron todos los recorridos candidatos."
            )
        else:
            busqueda["mensaje"] = (
                "Nuevo candidato preparado. "
                "Pulsa Siguiente paso para comprobar su primera conexión."
            )

        return

    nodo_a = recorrido[i]
    nodo_b = recorrido[(i + 1) % len(recorrido)]
    arista = tuple(sorted([nodo_a, nodo_b]))

    if arista in st.session_state["aristas"]:
        busqueda["aristas_comprobadas"].append(arista)
        busqueda["indice_conexion"] += 1
        busqueda["mensaje"] = f"La conexión {nodo_a}–{nodo_b} existe."

        if busqueda["indice_conexion"] == len(recorrido):
            busqueda["ciclos_validos"].append(recorrido.copy())
            busqueda["candidatos_revisados"] += 1
            busqueda["mensaje"] = (
                "Todas las conexiones existen, incluido el regreso "
                "al inicio. Ciclo hamiltoniano válido."
            )
    else:
        busqueda["arista_faltante"] = arista
        busqueda["candidatos_revisados"] += 1
        busqueda["mensaje"] = (
            f"La conexión {nodo_a}–{nodo_b} no existe. " "Se descarta este candidato."
        )


def completar_busqueda():
    """Completa la revisión de los candidatos pendientes."""
    busqueda = st.session_state["busqueda"]

    if not busqueda["iniciada"] or busqueda["terminada"]:
        return

    while not busqueda["terminada"]:
        comprobar_siguiente_conexion()


def construir_matriz_costos(nodos, aristas):
    """Construye la matriz de pesos del grafo."""
    matriz = []

    for nodo_a in nodos:
        fila = []

        for nodo_b in nodos:
            if nodo_a == nodo_b:
                costo = 0
            else:
                arista = tuple(sorted([nodo_a, nodo_b]))
                costo = aristas.get(arista, math.inf)

            fila.append(costo)

        matriz.append(fila)

    return matriz


def calcular_costo_ciclo(recorrido, nodos, matriz):
    """Suma los costos de un ciclo, incluido el regreso al inicio."""
    total = 0

    for i in range(len(recorrido)):
        origen = recorrido[i]
        destino = recorrido[(i + 1) % len(recorrido)]

        fila = nodos.index(origen)
        columna = nodos.index(destino)

        total += matriz[fila][columna]

    return total


def iniciar_busqueda():
    """Reinicia la búsqueda antes de actualizar el gráfico."""
    reiniciar_busqueda()

    busqueda = st.session_state["busqueda"]

    busqueda["generador"] = generar_recorridos(st.session_state["nodos"])

    busqueda["recorrido_actual"] = next(busqueda["generador"], None)

    busqueda["iniciada"] = True
    busqueda["mensaje"] = (
        "Primer candidato preparado. " "Todavía no se han comprobado sus conexiones."
    )


def mostrar_grafo(
    grafo, posiciones, aristas_resaltadas=None, arista_faltante=None, color="#16A34A"
):
    """Dibuja el grafo y resalta las conexiones indicadas."""
    figura, eje = plt.subplots(figsize=(10, 8))

    nx.draw_networkx(
        grafo,
        pos=posiciones,
        ax=eje,
        node_color="#38BDF8",
        node_size=900,
        font_size=12,
        font_weight="bold",
        edge_color="#64748B",
        width=1.5,
    )

    if aristas_resaltadas:
        nx.draw_networkx_edges(
            grafo,
            pos=posiciones,
            edgelist=aristas_resaltadas,
            ax=eje,
            edge_color=color,
            width=4,
        )

    if arista_faltante is not None:
        nx.draw_networkx_edges(
            grafo,
            pos=posiciones,
            edgelist=[arista_faltante],
            ax=eje,
            edge_color="#DC2626",
            style="dashed",
            width=3,
        )

    nx.draw_networkx_edge_labels(
        grafo,
        pos=posiciones,
        edge_labels=nx.get_edge_attributes(grafo, "weight"),
        ax=eje,
        font_size=8,
        rotate=False,
        label_pos=0.35,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.9, "pad": 0.2},
    )

    eje.set_aspect("equal")
    eje.margins(0.20)
    eje.set_axis_off()

    st.pyplot(figura)
    plt.close(figura)


# 1. Configuración de la página
st.set_page_config(
    page_title="Agente viajero", layout="wide", initial_sidebar_state="expanded"
)

# Estado inicial de la configuración
if "configurado" not in st.session_state:
    st.session_state["configurado"] = False
if "busqueda" not in st.session_state:
    reiniciar_busqueda()

# 2. Encabezado principal
st.title("Problema del agente viajero")
st.write("Construye un grafo y explora sus recorridos mediante fuerza bruta.")

# 3. Configuración en la barra izquierda
with st.sidebar:
    st.header("Configuración")
    st.write("Elige los datos iniciales del grafo.")

    with st.form("configuracion_grafo"):
        n = st.number_input(
            "Cantidad de nodos", min_value=5, max_value=10, value=5, step=1
        )

        modo = st.radio("Generación del grafo", options=["Manual", "Aleatoria"])

        confirmar = st.form_submit_button("Crear o reiniciar grafo")

    st.caption(
        "Entre 5 y 10 nodos. Crear o reiniciar elimina las conexiones anteriores"
    )

# 4. Distribución del espacio principal
tab_construccion, tab_pasos, tab_resultados = st.tabs(
    ["Construcción", "Paso a paso", "Resultados"]
)

with tab_construccion:
    zona_grafo, zona_explicacion = st.columns([2, 1], gap="large")

with tab_pasos:
    grafico_pasos, controles_pasos = st.columns([2, 1], gap="large")
with tab_resultados:
    datos_resultados, graficos_resultados = st.columns([1, 1], gap="large")
# 5. Área central
with zona_grafo:
    st.subheader("Área del grafo")

    if confirmar:
        etiquetas = list("ABCDEFGHIJ")

        st.session_state["nodos"] = etiquetas[:n]
        st.session_state["modo"] = modo
        st.session_state["aristas"] = {}
        reiniciar_busqueda()

        if modo == "Aleatoria":
            orden = st.session_state["nodos"].copy()
            random.shuffle(orden)

            # Crear un ciclo que visite todos los nodos
            for i in range(len(orden)):
                nodo_a = orden[i]
                nodo_b = orden[(i + 1) % len(orden)]

                arista = tuple(sorted([nodo_a, nodo_b]))
                st.session_state["aristas"][arista] = random.randint(1, 100)

            # Agregar algunas conexiones adicionales
            nodos = st.session_state["nodos"]

            for i in range(len(nodos)):
                for j in range(i + 1, len(nodos)):
                    arista = tuple(sorted([nodos[i], nodos[j]]))

                    if arista not in st.session_state["aristas"]:
                        if random.random() < 0.4:
                            st.session_state["aristas"][arista] = random.randint(1, 100)

        st.session_state["configurado"] = True

    if st.session_state["configurado"]:
        st.success("Configuración recibida.")

        st.write("Cantidad de nodos:", len(st.session_state["nodos"]))
        st.write("Modo seleccionado:", st.session_state["modo"])
        st.write("Nodos:", ", ".join(st.session_state["nodos"]))

        if st.session_state["modo"] == "Manual":
            st.subheader("Agregar una conexión")

            nodos = st.session_state["nodos"]

            with st.form("nueva_arista"):
                nodo_a = st.selectbox("Primer nodo", options=nodos)
                nodo_b = st.selectbox("Segundo nodo", options=nodos, index=1)

                peso = st.number_input(
                    "Peso de la conexión", min_value=0.0, value=1.0, step=1.0
                )

                agregar = st.form_submit_button("Agregar arista")

            if agregar:
                arista = tuple(sorted([nodo_a, nodo_b]))

                if nodo_a == nodo_b:
                    st.error("Selecciona dos nodos distintos.")
                elif not math.isfinite(peso) or peso <= 0:
                    st.error("El peso debe ser un número finito mayor que cero.")
                elif arista in st.session_state["aristas"]:
                    st.warning("Esa conexión ya existe.")
                else:
                    st.session_state["aristas"][arista] = peso
                    reiniciar_busqueda()
                    st.success("Arista guardada correctamente.")

        else:
            st.success("Grafo aleatorio generado con al menos un ciclo hamiltoniano.")

    else:
        st.info(
            "Completa la configuración de la izquierda y pulsa Crear o reiniciar grafo."
        )

# 6. Conexiones en el panel derecho
with zona_explicacion:
    st.subheader("Conexiones del grafo")

    if st.session_state["configurado"]:
        aristas = st.session_state["aristas"]

        st.write("Total de conexiones:", len(aristas))

        if aristas:
            filas = []

            for conexion, peso in sorted(aristas.items()):
                filas.append(
                    {"Conexión": f"{conexion[0]} — {conexion[1]}", "Peso": peso}
                )

            st.dataframe(filas, hide_index=True)

            st.caption(
                "Cada conexión puede recorrerse en ambos sentidos " "con el mismo peso."
            )
        else:
            st.info("Agrega una conexión para verla aquí con su peso.")
    else:
        st.info("Crea un grafo para consultar sus conexiones.")
# 7. Representación gráfica
if st.session_state["configurado"]:
    grafo = nx.Graph()
    grafo.add_nodes_from(st.session_state["nodos"])

    for conexion, costo in st.session_state["aristas"].items():
        grafo.add_edge(conexion[0], conexion[1], weight=costo)

    posiciones = nx.circular_layout(grafo)

    with zona_grafo:
        st.subheader("Representación del grafo")
        mostrar_grafo(grafo, posiciones)

    with grafico_pasos:
        st.subheader("Recorrido en revisión")

        busqueda = st.session_state["busqueda"]

        mostrar_grafo(
            grafo,
            posiciones,
            aristas_resaltadas=busqueda["aristas_comprobadas"],
            arista_faltante=busqueda["arista_faltante"],
        )

        st.caption(
            "Verde: conexiones comprobadas. " "Rojo discontinuo: conexión faltante."
        )

# 8. Verificación del grafo
with zona_grafo:
    if st.session_state["configurado"]:
        st.subheader("Verificación de ciclos hamiltonianos")

        verificar = st.button("Verificar grafo")

        if verificar:
            with st.spinner("Revisando los recorridos posibles..."):
                diagnostico = diagnosticar_grafo(
                    st.session_state["nodos"], st.session_state["aristas"]
                )

            recorrido = diagnostico["recorrido"]
            recorrido_cerrado = recorrido + [recorrido[0]]
            texto_recorrido = " → ".join(recorrido_cerrado)

            if diagnostico["tiene_ciclo"]:
                st.success("Grafo válido: existe al menos un ciclo hamiltoniano.")
            else:
                st.warning("El grafo no tiene ningún ciclo hamiltoniano.")
                st.write("Recorrido propuesto:", texto_recorrido)
                st.write(
                    "Cantidad mínima de aristas que debes agregar:",
                    len(diagnostico["faltantes"]),
                )

                for nodo_a, nodo_b in diagnostico["faltantes"]:
                    st.write(f"• Conectar {nodo_a} con {nodo_b}")

                st.info(
                    "Esta es una propuesta; pueden existir otras "
                    "con la misma cantidad de aristas faltantes. "
                    "Agrega las conexiones indicadas con sus pesos "
                    "y vuelve a verificar el grafo."
                )
# Guía debajo del grafo y su verificación
with zona_grafo:
    st.subheader("Cómo construir tu grafo")

    st.write(
        "1. Elige la cantidad de nodos y el modo de generación " "en la barra lateral."
    )
    st.write(
        "2. En modo manual, selecciona dos nodos e ingresa "
        "un peso positivo para conectarlos."
    )
    st.write("3. Consulta las conexiones y sus pesos en la tabla " "de la derecha.")
    st.write(
        "4. Pulsa Verificar grafo. Si faltan conexiones para "
        "completar un ciclo, revisa la propuesta y agrégalas."
    )
    st.write(
        "5. Entra a Paso a paso para explorar los recorridos "
        "y después consulta Resultados."
    )

# 9. Búsqueda paso a paso
with controles_pasos:
    if st.session_state["configurado"]:
        st.subheader("Exploración de ciclos hamiltonianos")

        st.button("Iniciar o reiniciar búsqueda", on_click=iniciar_busqueda)

        busqueda = st.session_state["busqueda"]

        if busqueda["iniciada"]:
            st.button(
                "Siguiente paso",
                on_click=comprobar_siguiente_conexion,
                disabled=busqueda["terminada"],
            )

            st.button(
                "Completar búsqueda",
                on_click=completar_busqueda,
                disabled=busqueda["terminada"],
            )

            recorrido = busqueda["recorrido_actual"]

            if recorrido is not None:
                recorrido_cerrado = recorrido + [recorrido[0]]

                st.write("Recorrido candidato:", " → ".join(recorrido_cerrado))

            st.info(busqueda["mensaje"])

            st.write("Candidatos revisados:", busqueda["candidatos_revisados"])

            st.write("Ciclos válidos encontrados:", len(busqueda["ciclos_validos"]))
# Resumen debajo de los controles
with controles_pasos:
    if st.session_state["configurado"]:
        busqueda = st.session_state["busqueda"]
        cantidad_nodos = len(st.session_state["nodos"])

        total_candidatos = math.factorial(cantidad_nodos - 1) // 2
        revisados = busqueda["candidatos_revisados"]
        validos = len(busqueda["ciclos_validos"])
        descartados = revisados - validos

        st.subheader("Resumen de la exploración")
        st.write("Candidatos por revisar:", total_candidatos - revisados)
        st.write("Candidatos descartados:", descartados)

        st.caption(
            "Cada candidato se cuenta una sola vez: "
            "su recorrido inverso representa el mismo ciclo."
        )

        if busqueda["aristas_comprobadas"]:
            st.markdown("**Conexiones comprobadas del candidato actual**")

            for nodo_a, nodo_b in busqueda["aristas_comprobadas"]:
                st.write(f"✓ {nodo_a} — {nodo_b}")

        if busqueda["arista_faltante"] is not None:
            nodo_a, nodo_b = busqueda["arista_faltante"]
            st.warning(f"Conexión faltante: {nodo_a} — {nodo_b}")

        if busqueda["terminada"]:
            st.success("Exploración finalizada. Consulta la pestaña Resultados.")
# 10. Matriz de costos
with datos_resultados:
    if st.session_state["configurado"]:
        busqueda = st.session_state["busqueda"]

        if busqueda["terminada"] and busqueda["ciclos_validos"]:
            st.subheader("Matriz de costos")

            nodos = st.session_state["nodos"]
            matriz = construir_matriz_costos(nodos, st.session_state["aristas"])

            filas_tabla = []

            for i, nodo in enumerate(nodos):
                fila = {"Nodo": nodo}

                for j, destino in enumerate(nodos):
                    costo = matriz[i][j]
                    fila[destino] = "-" if costo == math.inf else f"{costo:g}"

                filas_tabla.append(fila)

            st.table(filas_tabla)
            st.caption(
                "El - indica que no existe una conexión directa. "
                "Los ceros de la diagonal representan "
                "el costo de permanecer en el mismo nodo."
            )
# 11. Costos de los ciclos encontrados
with datos_resultados:
    if st.session_state["configurado"]:
        busqueda = st.session_state["busqueda"]

        if busqueda["terminada"] and busqueda["ciclos_validos"]:
            st.subheader("Costos de los ciclos hamiltonianos")

            if busqueda.get("resultados") is None:
                resultados = []

                for numero, ciclo in enumerate(busqueda["ciclos_validos"], start=1):
                    costo = calcular_costo_ciclo(ciclo, nodos, matriz)

                    recorrido_cerrado = ciclo + [ciclo[0]]

                    resultados.append(
                        {
                            "Número": numero,
                            "Ciclo": " → ".join(recorrido_cerrado),
                            "Costo total": costo,
                        }
                    )

                busqueda["resultados"] = resultados

            resultados = busqueda["resultados"]
            st.write("Total de ciclos encontrados:", len(resultados))
            st.dataframe(resultados, hide_index=True)

            costo_minimo = min(resultado["Costo total"] for resultado in resultados)

            optimos = []

            for resultado in resultados:
                if resultado["Costo total"] == costo_minimo:
                    optimos.append(resultado)

            mejor_resultado = optimos[0]

            with graficos_resultados:
                st.subheader("Solución óptima")

                st.success(f"Ciclo óptimo: {mejor_resultado['Ciclo']}")
                st.metric("Costo mínimo total", f"{costo_minimo:g}")

                if len(optimos) > 1:
                    st.info(
                        f"Se encontraron {len(optimos)} ciclos "
                        "con el mismo costo mínimo. "
                        "Se muestra uno de ellos."
                    )

                st.subheader("Visualización de ciclos")

                vista = st.radio(
                    "¿Qué ciclo deseas mostrar?",
                    ["Ciclo óptimo", "Elegir otro ciclo"],
                    horizontal=True,
                )

                if vista == "Ciclo óptimo":
                    indice_elegido = mejor_resultado["Número"] - 1
                    color_ciclo = "#16A34A"
                    leyenda = "Verde: conexiones del ciclo óptimo mostrado."
                else:
                    numero_elegido = st.number_input(
                        "Número del ciclo",
                        min_value=1,
                        max_value=len(resultados),
                        value=1,
                        step=1,
                    )

                    indice_elegido = numero_elegido - 1
                    color_ciclo = "#2563EB"
                    leyenda = "Azul: conexiones del ciclo seleccionado."

                ciclo_elegido = busqueda["ciclos_validos"][indice_elegido]
                resultado_elegido = resultados[indice_elegido]

                st.write("Recorrido mostrado:", resultado_elegido["Ciclo"])
                st.write("Costo del recorrido:", resultado_elegido["Costo total"])

                aristas_elegidas = []

                for i in range(len(ciclo_elegido)):
                    origen = ciclo_elegido[i]
                    destino = ciclo_elegido[(i + 1) % len(ciclo_elegido)]

                    arista = tuple(sorted([origen, destino]))
                    aristas_elegidas.append(arista)

                mostrar_grafo(
                    grafo,
                    posiciones,
                    aristas_resaltadas=aristas_elegidas,
                    color=color_ciclo,
                )

                st.caption(leyenda + " Gris: otras conexiones disponibles en el grafo.")

        elif busqueda["terminada"]:
            st.warning(
                "No se encontraron ciclos hamiltonianos. "
                "Vuelve a Construcción y pulsa Verificar grafo "
                "para consultar las conexiones faltantes."
            )
        else:
            st.info(
                "Completa la búsqueda en Paso a paso " "para consultar los resultados."
            )
    else:
        st.info("Primero crea un grafo en la pestaña Construcción.")
