import uuid

import pandas as pd
import streamlit as st

from agente import (
    APP_NOMBRE,
    APP_VERSION,
    asegurar_base_lista,
    actualizar_base_documental,
    base_lista,
    eliminar_documento,
    guardar_archivos_subidos,
    listar_documentos,
    responder_pregunta,
)

st.set_page_config(
    page_title=f"{APP_NOMBRE} | AgriMaiz",
    page_icon="🌽",
    layout="wide",
)

if "sesion_id" not in st.session_state:
    st.session_state.sesion_id = str(uuid.uuid4())
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

st.title("🌽 AgriAsistente")
st.caption(
    f"Asistente documental de AgriMaiz · versión {APP_VERSION}. "
    "Las respuestas se generan con base en la documentación disponible."
)

consulta_tab, documentos_tab, arquitectura_tab = st.tabs(
    [
        "💬 Consultar al asistente",
        "📄 Base documental",
        "🧩 Arquitectura",
    ]
)

with consulta_tab:
    if base_lista():
        st.success("Base documental disponible.")
    else:
        st.info(
            "La interfaz ya está lista. El índice se preparará únicamente "
            "cuando hagas la primera pregunta o cuando pulses "
            "“Preparar base” en Base documental."
        )

    if st.button("Nueva conversación"):
        st.session_state.mensajes = []
        st.rerun()

    sugerencias = [
        "¿Cómo debo monitorear el gusano cogollero?",
        "¿Qué datos debo registrar durante el monitoreo?",
        "¿Qué señales indican que el daño sigue activo?",
        "¿Por qué es importante identificar el tamaño de las larvas?",
    ]

    st.write("**Preguntas frecuentes**")
    columnas = st.columns(2)
    pregunta_boton = None

    for indice, sugerencia in enumerate(sugerencias):
        if columnas[indice % 2].button(
            sugerencia,
            key=f"pregunta_{indice}",
            use_container_width=True,
        ):
            pregunta_boton = sugerencia

    for mensaje in st.session_state.mensajes:
        with st.chat_message(mensaje["rol"]):
            st.markdown(mensaje["contenido"])
            fuentes = mensaje.get("fuentes", [])
            if fuentes:
                with st.expander("Fuentes consultadas"):
                    tabla = pd.DataFrame(fuentes)
                    columnas_fuente = [
                        columna
                        for columna in ["numero", "referencia", "categoria"]
                        if columna in tabla.columns
                    ]
                    st.dataframe(
                        tabla[columnas_fuente],
                        use_container_width=True,
                        hide_index=True,
                    )

    pregunta_chat = st.chat_input(
        "Ejemplo: Encontré larvas pequeñas y hojas perforadas, ¿qué debo revisar?"
    )
    pregunta = pregunta_chat or pregunta_boton

    if pregunta:
        st.session_state.mensajes.append(
            {"rol": "user", "contenido": pregunta}
        )

        with st.chat_message("user"):
            st.markdown(pregunta)

        with st.chat_message("assistant"):
            try:
                if not base_lista():
                    with st.spinner(
                        "Preparando la base por primera vez. "
                        "Esto puede tardar algunos minutos..."
                    ):
                        asegurar_base_lista()

                with st.spinner("Consultando la base documental..."):
                    resultado = responder_pregunta(
                        pregunta,
                        candidatos_iniciales=40,
                        top_k_final=5,
                    )

                st.markdown(resultado["respuesta"])
                fuentes = resultado.get("fuentes", [])

                if fuentes:
                    with st.expander("Fuentes consultadas"):
                        tabla = pd.DataFrame(fuentes)
                        columnas_fuente = [
                            columna
                            for columna in ["numero", "referencia", "categoria"]
                            if columna in tabla.columns
                        ]
                        st.dataframe(
                            tabla[columnas_fuente],
                            use_container_width=True,
                            hide_index=True,
                        )

                st.session_state.mensajes.append(
                    {
                        "rol": "assistant",
                        "contenido": resultado["respuesta"],
                        "fuentes": fuentes,
                    }
                )
            except Exception as exc:
                st.error(f"No fue posible responder: {exc}")

with documentos_tab:
    st.subheader("Base documental")
    st.write(
        "Aquí puedes consultar los archivos disponibles, añadir documentos "
        "nuevos, eliminarlos o reconstruir la base."
    )

    estado_col, accion_col = st.columns([3, 1])
    with estado_col:
        if base_lista():
            st.success("La base está preparada y lista para consultas.")
        else:
            st.warning(
                "Los documentos están disponibles, pero el índice todavía "
                "no ha sido preparado."
            )

    with accion_col:
        if st.button(
            "Preparar base",
            type="primary",
            disabled=base_lista(),
            use_container_width=True,
        ):
            try:
                with st.spinner(
                    "Procesando documentos y preparando la base..."
                ):
                    asegurar_base_lista()
                st.success("Base preparada correctamente.")
                st.rerun()
            except Exception as exc:
                st.exception(exc)

    st.divider()
    st.markdown("### Añadir documentos")
    archivos = st.file_uploader(
        "Selecciona uno o varios archivos",
        type=[
            "pdf", "docx", "xlsx", "csv", "json",
            "html", "htm", "md", "txt",
        ],
        accept_multiple_files=True,
    )

    if archivos:
        tabla_archivos = pd.DataFrame(
            [
                {
                    "archivo": archivo.name,
                    "tamaño_kb": round(archivo.size / 1024, 1),
                }
                for archivo in archivos
            ]
        )
        st.dataframe(
            tabla_archivos,
            use_container_width=True,
            hide_index=True,
        )

    if st.button(
        "Agregar a la base documental",
        type="primary",
        disabled=not archivos,
    ):
        try:
            with st.spinner(
                "Agregando documentos y actualizando la base..."
            ):
                guardados = guardar_archivos_subidos(archivos)
                resultado = actualizar_base_documental()

            st.success(
                f"Se agregaron {len(guardados)} archivo(s) y la base quedó actualizada."
            )
            st.metric(
                "Fragmentos disponibles",
                resultado["procesamiento"]["fragmentos_generados"],
            )
        except Exception as exc:
            st.exception(exc)

    st.divider()
    st.markdown("### Documentos disponibles")
    documentos = listar_documentos()

    if not documentos:
        st.info("No hay documentos disponibles.")
    else:
        for documento in documentos:
            col_nombre, col_formato, col_tamano, col_accion = st.columns(
                [5, 1, 1, 1]
            )
            col_nombre.write(documento["archivo"])
            col_formato.write(documento["formato"])
            col_tamano.write(f'{documento["tamaño_kb"]} KB')

            if col_accion.button(
                "Eliminar",
                key=f'eliminar_{documento["archivo"]}',
            ):
                st.session_state[
                    f'confirmar_{documento["archivo"]}'
                ] = True

            if st.session_state.get(
                f'confirmar_{documento["archivo"]}',
                False,
            ):
                st.warning(
                    f'¿Confirmas eliminar {documento["archivo"]}?'
                )
                confirmar, cancelar = st.columns(2)

                if confirmar.button(
                    "Sí, eliminar y actualizar",
                    key=f'si_{documento["archivo"]}',
                ):
                    try:
                        with st.spinner(
                            "Eliminando documento y actualizando la base..."
                        ):
                            eliminar_documento(documento["archivo"])
                            actualizar_base_documental()

                        st.session_state.pop(
                            f'confirmar_{documento["archivo"]}',
                            None,
                        )
                        st.success("Documento eliminado y base actualizada.")
                        st.rerun()
                    except Exception as exc:
                        st.exception(exc)

                if cancelar.button(
                    "Cancelar",
                    key=f'no_{documento["archivo"]}',
                ):
                    st.session_state.pop(
                        f'confirmar_{documento["archivo"]}',
                        None,
                    )
                    st.rerun()

    st.divider()
    if st.button("Reconstruir la base documental"):
        try:
            with st.spinner(
                "Procesando e indexando todos los documentos..."
            ):
                resultado = actualizar_base_documental()

            st.success(
                "Base reconstruida correctamente: "
                f'{resultado["procesamiento"]["fragmentos_generados"]} fragmentos.'
            )
        except Exception as exc:
            st.exception(exc)

with arquitectura_tab:
    st.subheader("Arquitectura de AgriAsistente")
    st.write(
        "El diagrama muestra cómo se transforma una pregunta en una "
        "respuesta fundamentada en los documentos de AgriMaiz."
    )

    diagrama_rag = r'''
digraph {
    graph [
        rankdir=TB,
        bgcolor="transparent",
        pad="0.4",
        nodesep="0.45",
        ranksep="0.55"
    ]

    node [
        shape=box,
        style="rounded,filled",
        fillcolor="#F4F6FA",
        color="#6C63FF",
        fontname="Arial",
        fontsize=11,
        margin="0.18,0.10"
    ]

    edge [
        color="#555555",
        arrowsize=0.75,
        fontname="Arial",
        fontsize=9
    ]

    pregunta [label="Pregunta del usuario", shape=oval, fillcolor="#FFF4D6"]
    expansion [label="Expansión de la consulta"]
    vectorial [label="Búsqueda vectorial\nFAISS"]
    lexical [label="Búsqueda por palabras"]
    fusion [label="Fusión de candidatos"]
    reranking [label="Reranking + prioridad\nde fuentes"]
    confianza [label="Evaluación de confianza"]
    contexto [label="Construcción del contexto"]
    llm [label="Modelo de lenguaje\nGroq"]
    validacion [label="Validación de citas\ny evidencia"]
    respuesta [label="Respuesta con fuentes", shape=oval, fillcolor="#E8F7E8"]
    fallback [label="Respuesta segura:\ninformación insuficiente", fillcolor="#FFE8E8"]

    pregunta -> expansion
    expansion -> vectorial
    expansion -> lexical
    vectorial -> fusion
    lexical -> fusion
    fusion -> reranking
    reranking -> confianza
    confianza -> contexto [label=" suficiente"]
    confianza -> fallback [label=" insuficiente"]
    contexto -> llm
    llm -> validacion
    validacion -> respuesta
}
'''

    st.graphviz_chart(
        diagrama_rag,
        use_container_width=True,
    )

    st.markdown("### Actualización de la base documental")

    diagrama_documentos = r'''
digraph {
    graph [
        rankdir=LR,
        bgcolor="transparent",
        pad="0.3",
        nodesep="0.35",
        ranksep="0.45"
    ]

    node [
        shape=box,
        style="rounded,filled",
        fillcolor="#F4F6FA",
        color="#2E8B57",
        fontname="Arial",
        fontsize=10
    ]

    edge [color="#555555", arrowsize=0.7]

    archivos [label="PDF · Word · Excel\nCSV · JSON · HTML"]
    extraccion [label="Extracción y limpieza"]
    fragmentacion [label="Fragmentación y\nmetadatos"]
    embeddings [label="Embeddings"]
    faiss [label="Índice FAISS"]
    disponible [label="Disponible para consultas", shape=oval, fillcolor="#E8F7E8"]

    archivos -> extraccion -> fragmentacion -> embeddings -> faiss -> disponible
}
'''

    st.graphviz_chart(
        diagrama_documentos,
        use_container_width=True,
    )

    st.caption(
        "La interfaz oculta estos detalles durante una consulta normal, "
        "pero el diagrama permite mostrar el funcionamiento técnico del proyecto."
    )
