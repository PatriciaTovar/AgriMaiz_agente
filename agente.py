"""Agente RAG simplificado de AgriMaiz.

Este archivo concentra configuración, procesamiento documental, indexación,
recuperación, generación y validación.
"""
from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DOCUMENTOS_DIR = BASE_DIR / "documentos"
ALMACENAMIENTO_DIR = BASE_DIR / "almacenamiento"
DATOS_PROCESADOS_DIR = ALMACENAMIENTO_DIR / "datos_procesados"

MANIFIESTO_PATH = DOCUMENTOS_DIR / "manifiesto_documental.json"
SALIDA_INVENTARIO = DATOS_PROCESADOS_DIR / "inventario_documental.json"
SALIDA_DOCUMENTOS = DATOS_PROCESADOS_DIR / "documentos_extraidos.jsonl"
SALIDA_FRAGMENTOS = DATOS_PROCESADOS_DIR / "fragmentos.jsonl"
SALIDA_RESUMEN = DATOS_PROCESADOS_DIR / "resumen_procesamiento.json"

EMPRESA = "AgriMaiz"
IDIOMA = "es-MX"

EXTENSIONES_SOPORTADAS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".csv",
    ".json",
    ".md",
    ".html",
    ".htm",
    ".txt",
}

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# Fase 3: indexación vectorial
VECTORSTORE_DIR = ALMACENAMIENTO_DIR / "indice_faiss"
INDICE_INFO_PATH = ALMACENAMIENTO_DIR / "indice_info.json"
MODELO_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K_DEFAULT = 5

# Fase 4: recuperación RAG
CANDIDATOS_INICIALES = 20
TOP_K_RERANK = 5
MODELO_RERANKER = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
MAX_CARACTERES_CONTEXTO = 7000

# Fase 5: generación y validación
LLM_PROVIDER = "groq"
GROQ_MODEL_ENV = "GROQ_MODEL"
TEMPERATURA_LLM = 0
MAX_REINTENTOS_GENERACION = 1
UMBRAL_RERANK_CROSS_ENCODER = -1.0
UMBRAL_RERANK_LEXICO = 0.12
MENSAJE_SIN_RESPUESTA = (
    "No encontré información suficiente en los documentos disponibles "
    "para responder esta pregunta con seguridad."
)

# Fase 6: interfaz, despliegue y mantenimiento
REGISTROS_DIR = ALMACENAMIENTO_DIR / "registros"
FEEDBACK_PATH = REGISTROS_DIR / "feedback.jsonl"
CONSULTAS_PATH = REGISTROS_DIR / "consultas.jsonl"
ESTADO_DOCUMENTOS_PATH = REGISTROS_DIR / "estado_documentos.json"
METRICAS_PATH = REGISTROS_DIR / "metricas.json"
APP_NOMBRE = "AgriAsistente"
APP_VERSION = "4.0.0"


# Prioridad editorial: los documentos diseñados y curados para responder
# preguntas deben pesar más que los corpus masivos.
PRIORIDAD_FUENTES = {
    "procedimiento_monitoreo.docx": 1.00,
    "preguntas_frecuentes.md": 0.95,
    "manual_manejo_integrado.pdf": 0.92,
    "README_base_documental.md": 0.80,
    "base_conocimiento.xlsx": 0.68,
    "glosario.html": 0.62,
    "corpus_curado_rag.csv": 0.42,
    "categorias_sinonimos.json": 0.25,
    "manifiesto_documental.json": 0.20,
}

FUENTES_PREFERIDAS_POR_INTENCION = {
    "registro_monitoreo": {
        "palabras": {"registrar", "registro", "anotar", "datos"},
        "archivos": {
            "procedimiento_monitoreo.docx": 1.40,
            "preguntas_frecuentes.md": 0.35,
            "manual_manejo_integrado.pdf": 0.25,
        },
    },
    "monitoreo": {
        "palabras": {"monitorear", "monitoreo", "revisar", "muestreo"},
        "archivos": {
            "procedimiento_monitoreo.docx": 1.15,
            "manual_manejo_integrado.pdf": 0.55,
            "preguntas_frecuentes.md": 0.45,
        },
    },
    "danio_activo": {
        "palabras": {"señales", "activo", "daño", "indicios"},
        "archivos": {
            "manual_manejo_integrado.pdf": 1.00,
            "preguntas_frecuentes.md": 0.75,
            "procedimiento_monitoreo.docx": 0.60,
        },
    },
    "tamano_larval": {
        "palabras": {"tamaño", "larvas", "larval", "pequeñas", "grandes"},
        "archivos": {
            "manual_manejo_integrado.pdf": 1.00,
            "preguntas_frecuentes.md": 0.70,
            "procedimiento_monitoreo.docx": 0.55,
        },
    },
}


def bonificacion_fuente_por_consulta(consulta: str, archivo: str) -> float:
    """Bonifica fuentes especialmente adecuadas para la intención consultada."""
    tokens = _tokens(consulta)
    bonificacion = 0.0
    for regla in FUENTES_PREFERIDAS_POR_INTENCION.values():
        if tokens & regla["palabras"]:
            bonificacion = max(
                bonificacion,
                float(regla["archivos"].get(archivo, 0.0)),
            )
    return bonificacion


CONSULTAS_EXPANDIDAS = {
    "registrar": (
        "datos de monitoreo fecha ubicación lote responsable etapa fenológica "
        "plantas revisadas plantas dañadas larvas vivas tamaño larval "
        "porcentaje infestación observaciones acción tomada seguimiento"
    ),
    "registro": (
        "datos de monitoreo fecha ubicación lote responsable etapa fenológica "
        "plantas revisadas plantas dañadas larvas vivas tamaño larval "
        "porcentaje infestación observaciones acción tomada seguimiento"
    ),
    "monitorear": (
        "inspección muestreo revisar plantas larvas vivas daño reciente "
        "ventanitas perforaciones excremento cogollo registrar porcentaje"
    ),
    "monitoreo": (
        "inspección muestreo revisar plantas larvas vivas daño reciente "
        "ventanitas perforaciones excremento cogollo registrar porcentaje"
    ),
    "señales": (
        "indicios daño activo larvas vivas ventanitas raspados perforaciones "
        "excremento material semejante a aserrín cogollo"
    ),
    "tamaño": (
        "tamaño larval larvas pequeñas medianas grandes eficacia control "
        "protegidas dentro del cogollo"
    ),
}


# Palabras del dominio usadas para mejorar la recuperación.
TERMINOS_DOMINIO = {
    "maíz", "maiz", "gusano", "cogollero", "spodoptera", "frugiperda",
    "larva", "larvas", "cogollo", "monitoreo", "daño", "manejo",
    "control", "cultivo", "plaga",
}

def guardar_archivos_subidos(archivos) -> list[str]:
    """Guarda archivos cargados desde Streamlit en documentos/."""
    DOCUMENTOS_DIR.mkdir(parents=True, exist_ok=True)
    guardados: list[str] = []
    for archivo in archivos or []:
        nombre = Path(archivo.name).name
        extension = Path(nombre).suffix.lower()
        if extension not in EXTENSIONES_SOPORTADAS:
            raise ValueError(f"Formato no soportado: {extension}")
        destino = DOCUMENTOS_DIR / nombre
        destino.write_bytes(archivo.getbuffer())
        guardados.append(nombre)
    return guardados

def actualizar_base_documental() -> dict[str, Any]:
    """Procesa todos los documentos y reconstruye el índice."""
    procesamiento = procesar_todos()
    indexacion = construir_indice(sobrescribir=True)
    return {"procesamiento": procesamiento, "indexacion": indexacion}

def listar_documentos() -> list[dict[str, Any]]:
    """Lista los documentos actuales de forma amigable."""
    salida = []
    for path in sorted(DOCUMENTOS_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in EXTENSIONES_SOPORTADAS:
            salida.append({
                "archivo": path.name,
                "formato": path.suffix.lower(),
                "tamaño_kb": round(path.stat().st_size / 1024, 1),
            })
    return salida


def eliminar_documento(nombre: str) -> bool:
    """Elimina un documento por nombre, evitando rutas externas."""
    nombre_seguro = Path(nombre).name
    destino = DOCUMENTOS_DIR / nombre_seguro
    if not destino.exists() or not destino.is_file():
        return False
    destino.unlink()
    return True


def base_lista() -> bool:
    """Indica si ya existen fragmentos e índice vectorial utilizables."""
    return (
        SALIDA_FRAGMENTOS.exists()
        and VECTORSTORE_DIR.exists()
        and (VECTORSTORE_DIR / "index.faiss").exists()
        and (VECTORSTORE_DIR / "index.pkl").exists()
    )


def asegurar_base_lista() -> dict[str, Any]:
    """Inicializa automáticamente la base incluida la primera vez."""
    if base_lista():
        return {"actualizada": False, "motivo": "La base ya estaba disponible."}

    if not any(
        p.is_file() and p.suffix.lower() in EXTENSIONES_SOPORTADAS
        for p in DOCUMENTOS_DIR.iterdir()
    ):
        raise FileNotFoundError("No hay documentos disponibles para crear la base.")

    resultado = actualizar_base_documental()
    return {
        "actualizada": True,
        "motivo": "La base se creó automáticamente.",
        "resultado": resultado,
    }


def expandir_consulta(pregunta: str) -> str:
    """Amplía preguntas breves con vocabulario agronómico relacionado."""
    texto = pregunta.strip()
    tokens = _tokens(texto)
    expansiones: list[str] = []

    for clave, expansion in CONSULTAS_EXPANDIDAS.items():
        if clave in tokens:
            expansiones.append(expansion)

    if not tokens & TERMINOS_DOMINIO:
        expansiones.append("gusano cogollero maíz manejo integrado")

    if not expansiones:
        return texto

    return f"{texto} {' '.join(expansiones)}"




# ========================================================================
# procesamiento/limpieza.py
# ========================================================================

import re
import unicodedata


PATRONES_PIE_ENCABEZADO = [
    r"^\s*página\s+\d+\s*(de\s+\d+)?\s*$",
    r"^\s*\d+\s*$",
]


def normalizar_unicode(texto: str) -> str:
    return unicodedata.normalize("NFKC", texto)


def limpiar_lineas(texto: str) -> str:
    lineas_limpias: list[str] = []

    for linea in texto.splitlines():
        linea = re.sub(r"[ \t]+", " ", linea).strip()

        if not linea:
            lineas_limpias.append("")
            continue

        if any(re.match(patron, linea, flags=re.IGNORECASE) for patron in PATRONES_PIE_ENCABEZADO):
            continue

        lineas_limpias.append(linea)

    texto = "\n".join(lineas_limpias)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def limpiar_texto(texto: str) -> str:
    if not texto:
        return ""

    texto = normalizar_unicode(texto)
    texto = texto.replace("\x00", " ")
    texto = re.sub(r"[\u200b-\u200d\uFEFF]", "", texto)
    texto = limpiar_lineas(texto)
    texto = re.sub(r" {2,}", " ", texto)
    return texto.strip()


# ========================================================================
# procesamiento/inventario.py
# ========================================================================

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any



def calcular_hash(path: Path) -> str:
    sha256 = hashlib.sha256()
    with path.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            sha256.update(bloque)
    return sha256.hexdigest()


def cargar_manifiesto() -> dict[str, Any]:
    if not MANIFIESTO_PATH.exists():
        return {}

    with MANIFIESTO_PATH.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def indexar_manifiesto(manifiesto: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indice: dict[str, dict[str, Any]] = {}
    for item in manifiesto.get("documentos", []):
        nombre = item.get("archivo")
        if nombre:
            indice[nombre] = item
    return indice


def construir_inventario() -> list[dict[str, Any]]:
    manifiesto = cargar_manifiesto()
    indice = indexar_manifiesto(manifiesto)
    inventario: list[dict[str, Any]] = []

    for path in sorted(DOCUMENTOS_DIR.iterdir()):
        if not path.is_file():
            continue

        extension = path.suffix.lower()
        estado = "soportado" if extension in EXTENSIONES_SOPORTADAS else "no_soportado"
        info_manifiesto = indice.get(path.name, {})

        stat = path.stat()
        inventario.append(
            {
                "archivo": path.name,
                "ruta_relativa": str(path.relative_to(DOCUMENTOS_DIR.parent)),
                "extension": extension,
                "tipo": info_manifiesto.get("tipo", extension.removeprefix(".").upper()),
                "uso": info_manifiesto.get("uso", "sin especificar"),
                "categoria": info_manifiesto.get("categoria", "documentacion_tecnica"),
                "responsable": info_manifiesto.get("responsable", "Área Técnica AgriMaiz"),
                "version": manifiesto.get("version", "1.0"),
                "estado": estado,
                "tamano_bytes": stat.st_size,
                "fecha_modificacion_utc": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
                "sha256": calcular_hash(path),
            }
        )

    return inventario


def detectar_duplicados(inventario: list[dict[str, Any]]) -> list[list[str]]:
    por_hash: dict[str, list[str]] = {}
    for item in inventario:
        por_hash.setdefault(item["sha256"], []).append(item["archivo"])

    return [nombres for nombres in por_hash.values() if len(nombres) > 1]


def guardar_inventario() -> dict[str, Any]:
    SALIDA_INVENTARIO.parent.mkdir(parents=True, exist_ok=True)
    inventario = construir_inventario()
    resultado = {
        "total_archivos": len(inventario),
        "duplicados": detectar_duplicados(inventario),
        "documentos": inventario,
    }

    with SALIDA_INVENTARIO.open("w", encoding="utf-8") as archivo:
        json.dump(resultado, archivo, ensure_ascii=False, indent=2)

    return resultado


if __name__ == "__main__":
    resultado = guardar_inventario()
    print(f"Inventario generado: {SALIDA_INVENTARIO}")
    print(f"Archivos encontrados: {resultado['total_archivos']}")
    print(f"Grupos duplicados: {len(resultado['duplicados'])}")


# ========================================================================
# procesamiento/cargadores.py
# ========================================================================

import json
from pathlib import Path
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup
from docx import Document as DocxDocument
from langchain_core.documents import Document
from pypdf import PdfReader



class FormatoNoSoportadoError(ValueError):
    pass


def metadata_base(path: Path, **extras: Any) -> dict[str, Any]:
    return {
        "archivo": path.name,
        "ruta": str(path),
        "extension": path.suffix.lower(),
        **extras,
    }


def cargar_pdf(path: Path) -> list[Document]:
    reader = PdfReader(str(path))
    documentos: list[Document] = []

    for indice, pagina in enumerate(reader.pages, start=1):
        texto = limpiar_texto(pagina.extract_text() or "")
        if texto:
            documentos.append(
                Document(
                    page_content=texto,
                    metadata=metadata_base(path, pagina=indice, unidad="pagina"),
                )
            )

    return documentos


def cargar_docx(path: Path) -> list[Document]:
    doc = DocxDocument(str(path))
    documentos: list[Document] = []
    bloque: list[str] = []
    seccion = "inicio"

    def guardar_bloque() -> None:
        nonlocal bloque
        texto = limpiar_texto("\n".join(bloque))
        if texto:
            documentos.append(
                Document(
                    page_content=texto,
                    metadata=metadata_base(path, seccion=seccion, unidad="seccion"),
                )
            )
        bloque = []

    for parrafo in doc.paragraphs:
        texto = parrafo.text.strip()
        estilo = (parrafo.style.name or "").lower() if parrafo.style else ""

        if texto and ("heading" in estilo or "título" in estilo or "titulo" in estilo):
            guardar_bloque()
            seccion = texto
            bloque.append(texto)
        elif texto:
            bloque.append(texto)

    for numero_tabla, tabla in enumerate(doc.tables, start=1):
        filas = []
        for fila in tabla.rows:
            celdas = [limpiar_texto(celda.text) for celda in fila.cells]
            filas.append(" | ".join(celdas))
        texto_tabla = limpiar_texto("\n".join(filas))
        if texto_tabla:
            bloque.append(f"\nTabla {numero_tabla}\n{texto_tabla}")

    guardar_bloque()
    return documentos


def cargar_xlsx(path: Path) -> list[Document]:
    hojas = pd.read_excel(path, sheet_name=None)
    documentos: list[Document] = []

    for nombre_hoja, df in hojas.items():
        df = df.dropna(how="all").dropna(axis=1, how="all")
        if df.empty:
            continue

        filas: list[str] = []
        columnas = [str(col) for col in df.columns]

        for numero_fila, (_, fila) in enumerate(df.iterrows(), start=2):
            pares = []
            for columna, valor in zip(columnas, fila.tolist()):
                if pd.notna(valor):
                    pares.append(f"{columna}: {valor}")
            if pares:
                filas.append(f"Fila {numero_fila}. " + "; ".join(pares))

        texto = limpiar_texto("\n".join(filas))
        if texto:
            documentos.append(
                Document(
                    page_content=texto,
                    metadata=metadata_base(
                        path,
                        hoja=nombre_hoja,
                        unidad="hoja",
                        filas=len(df),
                        columnas=columnas,
                    ),
                )
            )

    return documentos


def cargar_csv(path: Path) -> list[Document]:
    df = pd.read_csv(path)
    documentos: list[Document] = []
    columnas = [str(col) for col in df.columns]

    for indice, fila in df.iterrows():
        pares = []
        for columna, valor in zip(columnas, fila.tolist()):
            if pd.notna(valor):
                pares.append(f"{columna}: {valor}")

        texto = limpiar_texto("; ".join(pares))
        if texto:
            documentos.append(
                Document(
                    page_content=texto,
                    metadata=metadata_base(
                        path,
                        fila=int(indice) + 2,
                        unidad="fila",
                    ),
                )
            )

    return documentos


def convertir_json_a_texto(valor: Any, prefijo: str = "") -> list[str]:
    lineas: list[str] = []

    if isinstance(valor, dict):
        for clave, contenido in valor.items():
            nuevo_prefijo = f"{prefijo}.{clave}" if prefijo else str(clave)
            lineas.extend(convertir_json_a_texto(contenido, nuevo_prefijo))
    elif isinstance(valor, list):
        for indice, contenido in enumerate(valor):
            nuevo_prefijo = f"{prefijo}[{indice}]"
            lineas.extend(convertir_json_a_texto(contenido, nuevo_prefijo))
    else:
        lineas.append(f"{prefijo}: {valor}")

    return lineas


def cargar_json(path: Path) -> list[Document]:
    with path.open("r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    texto = limpiar_texto("\n".join(convertir_json_a_texto(datos)))
    return [
        Document(
            page_content=texto,
            metadata=metadata_base(path, unidad="documento"),
        )
    ] if texto else []


def cargar_html(path: Path) -> list[Document]:
    contenido = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(contenido, "html.parser")

    for etiqueta in soup(["script", "style", "noscript"]):
        etiqueta.decompose()

    titulo = soup.title.get_text(" ", strip=True) if soup.title else path.stem
    texto = limpiar_texto(soup.get_text("\n", strip=True))

    return [
        Document(
            page_content=texto,
            metadata=metadata_base(path, titulo=titulo, unidad="documento"),
        )
    ] if texto else []


def cargar_texto(path: Path) -> list[Document]:
    texto = limpiar_texto(path.read_text(encoding="utf-8"))
    return [
        Document(
            page_content=texto,
            metadata=metadata_base(path, unidad="documento"),
        )
    ] if texto else []


def cargar_archivo(path: Path) -> list[Document]:
    extension = path.suffix.lower()

    cargadores = {
        ".pdf": cargar_pdf,
        ".docx": cargar_docx,
        ".xlsx": cargar_xlsx,
        ".csv": cargar_csv,
        ".json": cargar_json,
        ".html": cargar_html,
        ".htm": cargar_html,
        ".md": cargar_texto,
        ".txt": cargar_texto,
    }

    cargador = cargadores.get(extension)
    if cargador is None:
        raise FormatoNoSoportadoError(
            f"Formato no soportado: {extension} ({path.name})"
        )

    return cargador(path)


# ========================================================================
# procesamiento/metadatos.py
# ========================================================================

import json
from pathlib import Path
from typing import Any



def cargar_indice_manifiesto() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    if not MANIFIESTO_PATH.exists():
        return {}, {}

    with MANIFIESTO_PATH.open("r", encoding="utf-8") as archivo:
        manifiesto = json.load(archivo)

    indice = {
        item["archivo"]: item
        for item in manifiesto.get("documentos", [])
        if item.get("archivo")
    }
    return manifiesto, indice


def enriquecer_metadata(
    metadata: dict[str, Any],
    manifiesto: dict[str, Any],
    indice: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    nombre = metadata.get("archivo", "")
    info = indice.get(nombre, {})

    categoria_por_archivo = {
        "manual_manejo_integrado.pdf": "manejo",
        "procedimiento_monitoreo.docx": "monitoreo",
        "base_conocimiento.xlsx": "conocimiento_estructurado",
        "corpus_curado_rag.csv": "corpus_rag",
        "categorias_sinonimos.json": "taxonomia",
        "preguntas_frecuentes.md": "preguntas_frecuentes",
        "glosario.html": "glosario",
        "manifiesto_documental.json": "inventario",
        "README_base_documental.md": "documentacion",
    }

    return {
        **metadata,
        "empresa": EMPRESA,
        "proyecto": manifiesto.get(
            "nombre",
            "Base documental RAG para manejo del gusano cogollero en maíz",
        ),
        "version": manifiesto.get("version", "1.0"),
        "fecha_generacion": manifiesto.get("fecha_generacion"),
        "tipo_documental": info.get("tipo", metadata.get("extension", "").upper()),
        "uso": info.get("uso", "consulta interna"),
        "categoria": info.get(
            "categoria",
            categoria_por_archivo.get(nombre, "documentacion_tecnica"),
        ),
        "responsable": info.get("responsable", "Área Técnica AgriMaiz"),
        "estado_documental": info.get("estado", "vigente"),
    }


# ========================================================================
# procesamiento/fragmentacion.py
# ========================================================================

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter



def crear_divisor() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=[
            "\n## ",
            "\n### ",
            "\n\n",
            "\n",
            ". ",
            "; ",
            ", ",
            " ",
            "",
        ],
    )


def fragmentar_documentos(documentos: list[Document]) -> list[Document]:
    divisor = crear_divisor()
    fragmentos = divisor.split_documents(documentos)

    contador_por_archivo: dict[str, int] = {}
    for fragmento in fragmentos:
        archivo = fragmento.metadata.get("archivo", "desconocido")
        contador_por_archivo[archivo] = contador_por_archivo.get(archivo, 0) + 1
        fragmento.metadata["chunk_id"] = (
            f"{archivo}::chunk_{contador_por_archivo[archivo]:04d}"
        )
        fragmento.metadata["chunk_index"] = contador_por_archivo[archivo] - 1
        fragmento.metadata["longitud_caracteres"] = len(fragmento.page_content)

    return fragmentos


# ========================================================================
# procesamiento/procesar_documentos.py
# ========================================================================

import json
import traceback
from collections import Counter
from pathlib import Path
from typing import Any

from langchain_core.documents import Document



def serializar_documento(documento: Document) -> dict[str, Any]:
    return {
        "page_content": documento.page_content,
        "metadata": documento.metadata,
    }


def guardar_jsonl(path: Path, documentos: list[Document]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as archivo:
        for documento in documentos:
            archivo.write(
                json.dumps(
                    serializar_documento(documento),
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )


def procesar_todos() -> dict[str, Any]:
    DATOS_PROCESADOS_DIR.mkdir(parents=True, exist_ok=True)
    inventario = guardar_inventario()
    manifiesto, indice_manifiesto = cargar_indice_manifiesto()

    documentos_extraidos: list[Document] = []
    errores: list[dict[str, str]] = []

    for path in sorted(DOCUMENTOS_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in EXTENSIONES_SOPORTADAS:
            continue
        if path == MANIFIESTO_PATH:
            # También se procesa; esta condición solo deja clara la intención.
            pass

        try:
            documentos_archivo = cargar_archivo(path)
            for documento in documentos_archivo:
                documento.metadata = enriquecer_metadata(
                    documento.metadata,
                    manifiesto,
                    indice_manifiesto,
                )
            documentos_extraidos.extend(documentos_archivo)
            print(
                f"[OK] {path.name}: "
                f"{len(documentos_archivo)} unidad(es) extraída(s)"
            )
        except Exception as exc:
            errores.append(
                {
                    "archivo": path.name,
                    "error": str(exc),
                    "detalle": traceback.format_exc(),
                }
            )
            print(f"[ERROR] {path.name}: {exc}")

    fragmentos = fragmentar_documentos(documentos_extraidos)

    guardar_jsonl(SALIDA_DOCUMENTOS, documentos_extraidos)
    guardar_jsonl(SALIDA_FRAGMENTOS, fragmentos)

    formatos = Counter(
        documento.metadata.get("extension", "sin_extension")
        for documento in documentos_extraidos
    )
    categorias = Counter(
        fragmento.metadata.get("categoria", "sin_categoria")
        for fragmento in fragmentos
    )

    resumen = {
        "empresa": "AgriMaiz",
        "archivos_en_inventario": inventario["total_archivos"],
        "unidades_documentales_extraidas": len(documentos_extraidos),
        "fragmentos_generados": len(fragmentos),
        "formatos": dict(formatos),
        "categorias": dict(categorias),
        "errores": errores,
        "salidas": {
            "inventario": str(DATOS_PROCESADOS_DIR / "inventario_documental.json"),
            "documentos": str(SALIDA_DOCUMENTOS),
            "fragmentos": str(SALIDA_FRAGMENTOS),
        },
    }

    with SALIDA_RESUMEN.open("w", encoding="utf-8") as archivo:
        json.dump(resumen, archivo, ensure_ascii=False, indent=2, default=str)

    return resumen


if __name__ == "__main__":
    resultado = procesar_todos()
    print("\n=== RESUMEN ===")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


# ========================================================================
# indexacion/embeddings.py
# ========================================================================

from langchain_huggingface import HuggingFaceEmbeddings



def crear_modelo_embeddings() -> HuggingFaceEmbeddings:
    """Crea el mismo modelo para indexar documentos y consultas.

    La normalización permite utilizar producto interno como equivalente
    de similitud coseno dentro del índice FAISS.
    """
    return HuggingFaceEmbeddings(
        model_name=MODELO_EMBEDDINGS,
        model_kwargs={"device": "cpu"},
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 32,
        },
    )


# ========================================================================
# indexacion/cargar_fragmentos.py
# ========================================================================

import json
from pathlib import Path

from langchain_core.documents import Document



def cargar_fragmentos_jsonl(path: Path = SALIDA_FRAGMENTOS) -> list[Document]:
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Ejecuta primero: "
            "python -m procesamiento.procesar_documentos"
        )

    documentos: list[Document] = []

    with path.open("r", encoding="utf-8") as archivo:
        for numero_linea, linea in enumerate(archivo, start=1):
            linea = linea.strip()
            if not linea:
                continue

            try:
                item = json.loads(linea)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"JSON inválido en {path}, línea {numero_linea}: {exc}"
                ) from exc

            contenido = str(item.get("page_content", "")).strip()
            metadata = item.get("metadata", {})

            if contenido:
                documentos.append(
                    Document(page_content=contenido, metadata=metadata)
                )

    if not documentos:
        raise ValueError("El archivo de fragmentos no contiene documentos válidos.")

    return documentos


# ========================================================================
# indexacion/indexar.py
# ========================================================================

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_community.vectorstores import FAISS



def construir_indice(sobrescribir: bool = True) -> dict[str, Any]:
    """Genera embeddings y guarda un índice FAISS persistente."""
    documentos = cargar_fragmentos_jsonl()

    if VECTORSTORE_DIR.exists() and any(VECTORSTORE_DIR.iterdir()):
        if not sobrescribir:
            raise FileExistsError(
                f"El índice ya existe en {VECTORSTORE_DIR}. "
                "Usa sobrescribir=True para regenerarlo."
            )

    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    INDICE_INFO_PATH.parent.mkdir(parents=True, exist_ok=True)

    embeddings = crear_modelo_embeddings()
    vectorstore = FAISS.from_documents(
        documents=documentos,
        embedding=embeddings,
    )
    vectorstore.save_local(str(VECTORSTORE_DIR))

    categorias = Counter(
        doc.metadata.get("categoria", "sin_categoria")
        for doc in documentos
    )
    archivos = Counter(
        doc.metadata.get("archivo", "sin_archivo")
        for doc in documentos
    )

    info = {
        "empresa": "AgriMaiz",
        "fecha_indexacion_utc": datetime.now(timezone.utc).isoformat(),
        "modelo_embeddings": MODELO_EMBEDDINGS,
        "dimension_vector": 384,
        "total_vectores": len(documentos),
        "motor_vectorial": "FAISS",
        "metrica_aproximada": "similitud coseno mediante embeddings normalizados",
        "categorias": dict(categorias),
        "archivos": dict(archivos),
        "ruta_indice": str(VECTORSTORE_DIR),
    }

    with INDICE_INFO_PATH.open("w", encoding="utf-8") as archivo:
        json.dump(info, archivo, ensure_ascii=False, indent=2)

    return info


if __name__ == "__main__":
    resultado = construir_indice(sobrescribir=True)
    print("\n=== ÍNDICE CREADO ===")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


# ========================================================================
# indexacion/buscar.py
# ========================================================================

from typing import Any, Callable

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document



def cargar_indice() -> FAISS:
    if not VECTORSTORE_DIR.exists():
        raise FileNotFoundError(
            "El índice FAISS todavía no existe. Ejecuta: "
            "python -m indexacion.indexar"
        )

    embeddings = crear_modelo_embeddings()

    # El índice fue creado localmente por este proyecto.
    return FAISS.load_local(
        str(VECTORSTORE_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )


def crear_filtro_metadata(
    categoria: str | None = None,
    archivo: str | None = None,
    responsable: str | None = None,
) -> Callable[[dict[str, Any]], bool] | None:
    filtros = {
        "categoria": categoria,
        "archivo": archivo,
        "responsable": responsable,
    }
    filtros = {clave: valor for clave, valor in filtros.items() if valor}

    if not filtros:
        return None

    def coincide(metadata: dict[str, Any]) -> bool:
        return all(
            str(metadata.get(clave, "")).lower() == str(valor).lower()
            for clave, valor in filtros.items()
        )

    return coincide


def buscar_fragmentos(
    consulta: str,
    k: int = TOP_K_DEFAULT,
    categoria: str | None = None,
    archivo: str | None = None,
    responsable: str | None = None,
) -> list[tuple[Document, float]]:
    if not consulta.strip():
        raise ValueError("La consulta no puede estar vacía.")

    vectorstore = cargar_indice()
    filtro = crear_filtro_metadata(
        categoria=categoria,
        archivo=archivo,
        responsable=responsable,
    )

    # score menor = mayor cercanía en la implementación FAISS usada.
    return vectorstore.similarity_search_with_score(
        consulta,
        k=k,
        filter=filtro,
        fetch_k=max(k * 5, 20),
    )


def convertir_resultados(
    resultados: list[tuple[Document, float]],
) -> list[dict[str, Any]]:
    salida = []

    for posicion, (documento, score) in enumerate(resultados, start=1):
        salida.append(
            {
                "posicion": posicion,
                "distancia": float(score),
                "contenido": documento.page_content,
                "metadata": documento.metadata,
            }
        )

    return salida


if __name__ == "__main__":
    pregunta = "¿Cómo reconocer un ataque temprano del gusano cogollero?"
    resultados = buscar_fragmentos(pregunta, k=5)

    for item in convertir_resultados(resultados):
        meta = item["metadata"]
        print(
            f"\n#{item['posicion']} | distancia={item['distancia']:.4f} | "
            f"{meta.get('archivo')} | {meta.get('categoria')}"
        )
        print(item["contenido"][:500])


# ========================================================================
# rag/filtros.py
# ========================================================================

from datetime import datetime
from typing import Any, Callable


def _normalizar(valor: Any) -> str:
    return str(valor or "").strip().lower()


def crear_filtro_rag(
    categoria: str | None = None,
    archivo: str | None = None,
    responsable: str | None = None,
    estado_documental: str | None = "vigente",
    fecha_desde: str | None = None,
) -> Callable[[dict[str, Any]], bool] | None:
    filtros_texto = {
        "categoria": categoria,
        "archivo": archivo,
        "responsable": responsable,
        "estado_documental": estado_documental,
    }
    filtros_texto = {
        clave: valor
        for clave, valor in filtros_texto.items()
        if valor not in (None, "")
    }

    fecha_minima = None
    if fecha_desde:
        fecha_minima = datetime.fromisoformat(fecha_desde)

    if not filtros_texto and fecha_minima is None:
        return None

    def coincide(metadata: dict[str, Any]) -> bool:
        for clave, valor in filtros_texto.items():
            if _normalizar(metadata.get(clave)) != _normalizar(valor):
                return False

        if fecha_minima is not None:
            fecha_doc = metadata.get("fecha_generacion")
            if not fecha_doc:
                return False
            try:
                fecha_doc_dt = datetime.fromisoformat(str(fecha_doc))
            except ValueError:
                return False
            if fecha_doc_dt < fecha_minima:
                return False

        return True

    return coincide


# ========================================================================
# rag/reranker.py
# ========================================================================

import re
from functools import lru_cache
from typing import Any

from langchain_core.documents import Document



@lru_cache(maxsize=1)
def cargar_reranker():
    try:
        from sentence_transformers import CrossEncoder
        return CrossEncoder(MODELO_RERANKER)
    except Exception:
        return None


def _tokens(texto: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-záéíóúñü0-9]+", texto.lower())
        if len(token) > 2
    }


def puntaje_lexico(consulta: str, contenido: str) -> float:
    consulta_tokens = _tokens(consulta)
    contenido_tokens = _tokens(contenido)

    if not consulta_tokens or not contenido_tokens:
        return 0.0

    sinonimos = {
        "registrar": {"registro", "anotar", "datos", "fecha", "ubicacion", "plantas"},
        "monitorear": {"monitoreo", "revisar", "muestreo", "inspeccion"},
        "señales": {"indicios", "sintomas", "daño", "ventanitas", "perforaciones"},
        "activo": {"larvas", "vivas", "excremento", "cogollo"},
        "tamaño": {"pequeñas", "medianas", "grandes", "larval"},
        "importante": {"eficacia", "susceptibles", "protegidas"},
    }
    consulta_ampliada = set(consulta_tokens)
    for token in list(consulta_tokens):
        consulta_ampliada.update(sinonimos.get(token, set()))

    interseccion = consulta_ampliada & contenido_tokens
    cobertura = len(interseccion) / max(len(consulta_ampliada), 1)
    densidad = len(interseccion) / max(len(contenido_tokens), 1)
    dominio = len(TERMINOS_DOMINIO & contenido_tokens) / max(len(TERMINOS_DOMINIO), 1)
    return (0.72 * cobertura) + (0.08 * densidad) + (0.20 * dominio)


def rerankear(
    consulta: str,
    candidatos: list[tuple[Document, float]],
    top_k: int,
) -> list[dict[str, Any]]:
    if not candidatos:
        return []

    modelo = cargar_reranker()

    if modelo is not None:
        pares = [(consulta, documento.page_content) for documento, _ in candidatos]
        scores = modelo.predict(pares)

        resultados = []
        consulta_tokens = _tokens(consulta)
        terminos_tema = {"maíz", "maiz", "gusano", "cogollero", "spodoptera", "frugiperda", "larva", "larvas", "cogollo", "monitoreo", "manejo", "control", "daño"}
        for (documento, distancia), score in zip(candidatos, scores):
            contenido_tokens = _tokens(documento.page_content)
            coincidencias = len(consulta_tokens & contenido_tokens)
            coincidencia_tema = len(terminos_tema & contenido_tokens)
            ajuste = min(coincidencias * 0.08, 0.40) + min(coincidencia_tema * 0.03, 0.18)
            texto = documento.page_content.strip()
            archivo = str(documento.metadata.get("archivo", ""))
            prioridad = PRIORIDAD_FUENTES.get(archivo, 0.50)
            ajuste += (prioridad - 0.50) * 0.85
            ajuste += bonificacion_fuente_por_consulta(consulta, archivo)

            # Penaliza fragmentos probablemente ajenos o muy deteriorados.
            tokens_texto = _tokens(texto)
            terminos_ruido = {
                "bermudagrass", "chile", "tomate", "durazno", "triflura",
                "picudo", "paratrioza", "rhodesgrass",
            }
            if terminos_ruido & tokens_texto and not {
                "frugiperda", "cogollero", "maíz", "maiz"
            } & tokens_texto:
                ajuste -= 1.10

            if len(texto) < 180:
                ajuste -= 0.20
            if len(texto.split()) > 70 and texto.count(".") < 2:
                ajuste -= 0.30

            resultados.append({
                "documento": documento,
                "distancia_vectorial": float(distancia),
                "puntaje_reranker": float(score) + ajuste,
                "puntaje_modelo": float(score),
                "ajuste_tematico": ajuste,
                "metodo_reranking": "cross_encoder_hibrido",
            })
    else:
        resultados = [
            {
                "documento": documento,
                "distancia_vectorial": float(distancia),
                "puntaje_reranker": (
                    puntaje_lexico(consulta, documento.page_content)
                    + (
                        PRIORIDAD_FUENTES.get(
                            str(documento.metadata.get("archivo", "")),
                            0.50,
                        )
                        - 0.50
                    )
                    * 0.35
                    + bonificacion_fuente_por_consulta(
                        consulta,
                        str(documento.metadata.get("archivo", "")),
                    )
                ),
                "metodo_reranking": "lexico_fallback",
            }
            for documento, distancia in candidatos
        ]

    resultados.sort(
        key=lambda item: item["puntaje_reranker"],
        reverse=True,
    )

    return resultados[:top_k]


# ========================================================================
# rag/contexto.py
# ========================================================================

from typing import Any



def referencia_documental(metadata: dict[str, Any]) -> str:
    partes = [metadata.get("archivo", "archivo desconocido")]

    if metadata.get("pagina"):
        partes.append(f"página {metadata['pagina']}")
    if metadata.get("seccion"):
        partes.append(f"sección {metadata['seccion']}")
    if metadata.get("hoja"):
        partes.append(f"hoja {metadata['hoja']}")
    if metadata.get("fila"):
        partes.append(f"fila {metadata['fila']}")

    return " · ".join(str(parte) for parte in partes)


def ensamblar_contexto(
    resultados: list[dict[str, Any]],
    max_caracteres: int = MAX_CARACTERES_CONTEXTO,
) -> dict[str, Any]:
    bloques: list[str] = []
    fuentes: list[dict[str, Any]] = []
    caracteres = 0

    for item in resultados:
        documento = item["documento"]
        metadata = documento.metadata
        referencia = referencia_documental(metadata)

        bloque = (
            f"[FUENTE {item['posicion']}]\n"
            f"Referencia: {referencia}\n"
            f"Categoría: {metadata.get('categoria', 'sin categoría')}\n"
            f"Responsable: {metadata.get('responsable', 'sin responsable')}\n"
            f"Contenido:\n{documento.page_content.strip()}\n"
        )

        if bloques and caracteres + len(bloque) > max_caracteres:
            break

        bloques.append(bloque)
        caracteres += len(bloque)

        fuentes.append(
            {
                "numero": item["posicion"],
                "archivo": metadata.get("archivo"),
                "categoria": metadata.get("categoria"),
                "referencia": referencia,
                "chunk_id": metadata.get("chunk_id"),
                "puntaje_reranker": item.get("puntaje_reranker"),
                "distancia_vectorial": item.get("distancia_vectorial"),
                "metodo_reranking": item.get("metodo_reranking"),
            }
        )

    return {
        "contexto": "\n\n".join(bloques),
        "fuentes": fuentes,
        "caracteres_contexto": caracteres,
        "fragmentos_incluidos": len(fuentes),
    }


# ========================================================================
# rag/recuperador.py
# ========================================================================

from typing import Any



def recuperar_contexto(
    consulta: str,
    candidatos_iniciales: int = CANDIDATOS_INICIALES,
    top_k_final: int = TOP_K_RERANK,
    categoria: str | None = None,
    archivo: str | None = None,
    responsable: str | None = None,
    estado_documental: str | None = "vigente",
    fecha_desde: str | None = None,
) -> list[dict[str, Any]]:
    if not consulta.strip():
        raise ValueError("La consulta no puede estar vacía.")

    vectorstore = cargar_indice()
    filtro = crear_filtro_rag(
        categoria=categoria,
        archivo=archivo,
        responsable=responsable,
        estado_documental=estado_documental,
        fecha_desde=fecha_desde,
    )

    candidatos = vectorstore.similarity_search_with_score(
        consulta,
        k=candidatos_iniciales,
        filter=filtro,
        fetch_k=max(candidatos_iniciales * 5, 50),
    )

    # Búsqueda híbrida: agrega candidatos por coincidencia de palabras.
    try:
        fragmentos = cargar_fragmentos_jsonl()
        lexicales = []
        for doc in fragmentos:
            if filtro and not filtro(doc.metadata):
                continue
            score_lex = puntaje_lexico(consulta, doc.page_content)
            if score_lex > 0.08:
                lexicales.append((doc, max(0.0, 1.0 - score_lex)))
        lexicales.sort(key=lambda item: item[1])

        vistos = {
            (doc.metadata.get("chunk_id"), doc.metadata.get("archivo"))
            for doc, _ in candidatos
        }
        for doc, distancia in lexicales[:candidatos_iniciales]:
            clave = (doc.metadata.get("chunk_id"), doc.metadata.get("archivo"))
            if clave not in vistos:
                candidatos.append((doc, distancia))
                vistos.add(clave)
    except Exception:
        pass

    resultados = rerankear(
        consulta=consulta,
        candidatos=candidatos,
        top_k=top_k_final,
    )

    for posicion, item in enumerate(resultados, start=1):
        item["posicion"] = posicion

    return resultados


# ========================================================================
# rag/servicio_rag.py
# ========================================================================

from typing import Any



def preparar_consulta_rag(
    pregunta: str,
    categoria: str | None = None,
    archivo: str | None = None,
    responsable: str | None = None,
    estado_documental: str | None = "vigente",
    fecha_desde: str | None = None,
    candidatos_iniciales: int = 20,
    top_k_final: int = 5,
) -> dict[str, Any]:
    consulta_expandida = expandir_consulta(pregunta)

    resultados = recuperar_contexto(
        consulta=consulta_expandida,
        candidatos_iniciales=candidatos_iniciales,
        top_k_final=top_k_final,
        categoria=categoria,
        archivo=archivo,
        responsable=responsable,
        estado_documental=estado_documental,
        fecha_desde=fecha_desde,
    )

    ensamblado = ensamblar_contexto(resultados)

    return {
        "pregunta": pregunta,
        "contexto": ensamblado["contexto"],
        "fuentes": ensamblado["fuentes"],
        "caracteres_contexto": ensamblado["caracteres_contexto"],
        "fragmentos_incluidos": ensamblado["fragmentos_incluidos"],
        "resultados_crudos": resultados,
    }


if __name__ == "__main__":
    pregunta = "¿Cómo se debe monitorear el gusano cogollero en maíz?"
    resultado = preparar_consulta_rag(pregunta)

    print("\n=== CONTEXTO RAG ===\n")
    print(resultado["contexto"])
    print("\n=== FUENTES ===")
    for fuente in resultado["fuentes"]:
        print(fuente)


# ========================================================================
# generacion/prompt.py
# ========================================================================

from langchain_core.prompts import ChatPromptTemplate


PROMPT_SISTEMA = """
Eres AgriAsistente, el asistente documental interno de AgriMaiz.

REGLAS OBLIGATORIAS:
1. Responde exclusivamente con información contenida en el CONTEXTO.
2. No uses conocimiento externo, aunque creas conocer la respuesta.
3. No inventes dosis, productos, umbrales, fechas, contactos ni procedimientos.
4. Toda afirmación sustantiva debe estar respaldada por una cita con el formato
   [FUENTE n], utilizando únicamente números de fuente presentes en el contexto.
5. Cuando los documentos no sean suficientes, responde exactamente:
   "No encontré información suficiente en los documentos disponibles para responder esta pregunta con seguridad."
6. Si la consulta pide una dosis o recomendación química específica y el contexto
   no contiene etiqueta vigente aplicable, indícalo expresamente.
7. Diferencia información general de instrucciones específicas para una parcela.
8. Responde en español claro y profesional.
9. No incluyas una sección de fuentes inventada; utiliza solo las referencias
   recibidas en el contexto.

FORMATO:
- Respuesta directa y breve.
- Detalles necesarios en párrafos o viñetas.
- Citas [FUENTE n] colocadas junto a la información respaldada.
- Una línea final de advertencia cuando se trate de manejo agronómico específico.
""".strip()


def crear_prompt_respuesta() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", PROMPT_SISTEMA),
            (
                "human",
                """
PREGUNTA:
{pregunta}

CONTEXTO DOCUMENTAL:
{contexto}

Redacta la respuesta fundamentada.
""".strip(),
            ),
        ]
    )


def crear_prompt_regeneracion() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", PROMPT_SISTEMA),
            (
                "human",
                """
PREGUNTA:
{pregunta}

CONTEXTO DOCUMENTAL:
{contexto}

RESPUESTA ANTERIOR:
{respuesta_anterior}

PROBLEMAS DETECTADOS:
{problemas}

Regenera la respuesta corrigiendo todos los problemas. No agregues información
que no aparezca en el contexto.
""".strip(),
            ),
        ]
    )


# ========================================================================
# generacion/modelo.py
# ========================================================================

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq



def crear_llm() -> ChatGroq:
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")
    modelo = os.getenv(GROQ_MODEL_ENV)

    if not api_key:
        raise RuntimeError(
            "No se encontró GROQ_API_KEY. Crea un archivo .env a partir "
            "de .env.example y agrega tu clave."
        )

    if not modelo:
        raise RuntimeError(
            f"No se encontró {GROQ_MODEL_ENV}. Define en .env el nombre "
            "de un modelo disponible en tu cuenta de Groq."
        )

    return ChatGroq(
        api_key=api_key,
        model_name=modelo,
        temperature=TEMPERATURA_LLM,
    )


# ========================================================================
# generacion/confianza.py
# ========================================================================

from typing import Any



def evaluar_confianza_recuperacion(
    resultados: list[dict[str, Any]],
) -> dict[str, Any]:
    if not resultados:
        return {
            "suficiente": False,
            "motivo": "No se recuperaron fragmentos.",
            "puntaje": None,
            "metodo": None,
        }

    mejor = resultados[0]
    metodo = mejor.get("metodo_reranking")
    puntaje = float(mejor.get("puntaje_reranker", 0.0))

    if str(metodo).startswith("cross_encoder"):
        umbral = UMBRAL_RERANK_CROSS_ENCODER
    else:
        umbral = UMBRAL_RERANK_LEXICO

    documento = mejor.get("documento")
    contenido = documento.page_content if documento is not None else ""
    score_lexico = puntaje_lexico("", contenido)
    # La consulta ya fue considerada por el reranker. Además, se acepta
    # evidencia documental claramente temática con distancia razonable.
    distancia = float(mejor.get("distancia_vectorial", 99.0))
    evidencia_tematica = len(TERMINOS_DOMINIO & _tokens(contenido)) >= 3
    prioridad = PRIORIDAD_FUENTES.get(
        str(documento.metadata.get("archivo", "")) if documento else "",
        0.50,
    )
    bonificacion_intencion = bonificacion_fuente_por_consulta(
        contenido,
        str(documento.metadata.get("archivo", "")) if documento else "",
    )
    suficiente = (
        puntaje >= umbral
        or (evidencia_tematica and distancia <= 1.10)
        or (prioridad >= 0.90 and distancia <= 1.20)
        or (bonificacion_intencion >= 0.60 and distancia <= 1.25)
    )

    return {
        "suficiente": suficiente,
        "motivo": (
            "Se recuperó evidencia documental suficiente."
            if suficiente
            else "La relevancia del mejor fragmento es insuficiente."
        ),
        "puntaje": puntaje,
        "umbral": umbral,
        "distancia_vectorial": distancia,
        "evidencia_tematica": evidencia_tematica,
        "metodo": metodo,
    }


# ========================================================================
# generacion/fuentes.py
# ========================================================================

from typing import Any


def formatear_fuentes(fuentes: list[dict[str, Any]]) -> str:
    if not fuentes:
        return ""

    lineas = ["### Fuentes consultadas"]

    for fuente in fuentes:
        referencia = fuente.get("referencia") or fuente.get("archivo")
        categoria = fuente.get("categoria", "sin categoría")
        lineas.append(
            f"- [FUENTE {fuente['numero']}] {referencia} "
            f"— categoría: {categoria}"
        )

    return "\n".join(lineas)


# ========================================================================
# generacion/validador.py
# ========================================================================

import re
from typing import Any


PATRON_CITA = re.compile(r"\[FUENTE\s+(\d+)\]", re.IGNORECASE)
PATRON_NUMERO = re.compile(
    r"(?<![\w])(?:\d+(?:[.,]\d+)?)(?:\s?%|\s?[a-zA-Z]+)?"
)


def normalizar_numero(valor: str) -> str:
    return re.sub(r"\s+", "", valor.lower().replace(",", "."))


def extraer_numeros(texto: str) -> set[str]:
    return {
        normalizar_numero(coincidencia.group(0))
        for coincidencia in PATRON_NUMERO.finditer(texto)
    }


def validar_respuesta(
    respuesta: str,
    contexto: str,
    fuentes: list[dict[str, Any]],
) -> dict[str, Any]:
    problemas: list[str] = []
    citas = [int(numero) for numero in PATRON_CITA.findall(respuesta)]
    fuentes_validas = {int(fuente["numero"]) for fuente in fuentes}

    if not respuesta.strip():
        problemas.append("La respuesta está vacía.")

    if fuentes and not citas:
        problemas.append("La respuesta no incluye citas [FUENTE n].")

    citas_invalidas = sorted(set(citas) - fuentes_validas)
    if citas_invalidas:
        problemas.append(
            "La respuesta cita fuentes inexistentes: "
            + ", ".join(map(str, citas_invalidas))
            + "."
        )

    numeros_respuesta = extraer_numeros(respuesta)
    numeros_contexto = extraer_numeros(contexto)

    # Los números utilizados en las etiquetas [FUENTE n] no son afirmaciones.
    numeros_citas = {str(numero) for numero in citas}
    numeros_no_respaldados = sorted(
        numero
        for numero in numeros_respuesta
        if numero not in numeros_contexto and numero not in numeros_citas
    )

    if numeros_no_respaldados:
        problemas.append(
            "La respuesta contiene números no encontrados en el contexto: "
            + ", ".join(numeros_no_respaldados[:10])
            + "."
        )

    expresiones_riesgo = [
        "según mi conocimiento",
        "generalmente se recomienda aplicar",
        "puedo asegurar",
        "sin duda",
    ]
    for expresion in expresiones_riesgo:
        if expresion in respuesta.lower():
            problemas.append(
                f"Se detectó una expresión de posible conocimiento externo: "
                f"'{expresion}'."
            )

    return {
        "valida": not problemas,
        "problemas": problemas,
        "citas": sorted(set(citas)),
        "numeros_no_respaldados": numeros_no_respaldados,
    }


# ========================================================================
# generacion/servicio_respuesta.py
# ========================================================================

from typing import Any

from langchain_core.output_parsers import StrOutputParser



def responder_pregunta(
    pregunta: str,
    categoria: str | None = None,
    archivo: str | None = None,
    responsable: str | None = None,
    candidatos_iniciales: int = 20,
    top_k_final: int = 5,
) -> dict[str, Any]:
    recuperacion = preparar_consulta_rag(
        pregunta=pregunta,
        categoria=categoria,
        archivo=archivo,
        responsable=responsable,
        candidatos_iniciales=candidatos_iniciales,
        top_k_final=top_k_final,
    )

    confianza = evaluar_confianza_recuperacion(
        recuperacion["resultados_crudos"]
    )

    if (
        not confianza["suficiente"]
        or not recuperacion["contexto"].strip()
        or not recuperacion["fuentes"]
    ):
        return {
            "pregunta": pregunta,
            "respuesta": MENSAJE_SIN_RESPUESTA,
            "respuesta_con_fuentes": MENSAJE_SIN_RESPUESTA,
            "fuentes": [],
            "confianza": confianza,
            "validacion": {
                "valida": True,
                "problemas": [],
                "tipo": "fallback_sin_contexto",
            },
            "recuperacion": recuperacion,
            "uso_fallback": True,
        }

    llm = crear_llm()
    cadena = crear_prompt_respuesta() | llm | StrOutputParser()

    respuesta = cadena.invoke(
        {
            "pregunta": pregunta,
            "contexto": recuperacion["contexto"],
        }
    ).strip()

    validacion = validar_respuesta(
        respuesta=respuesta,
        contexto=recuperacion["contexto"],
        fuentes=recuperacion["fuentes"],
    )

    intentos = 0
    while not validacion["valida"] and intentos < MAX_REINTENTOS_GENERACION:
        intentos += 1
        cadena_regeneracion = (
            crear_prompt_regeneracion() | llm | StrOutputParser()
        )
        respuesta = cadena_regeneracion.invoke(
            {
                "pregunta": pregunta,
                "contexto": recuperacion["contexto"],
                "respuesta_anterior": respuesta,
                "problemas": "\n".join(
                    f"- {problema}"
                    for problema in validacion["problemas"]
                ),
            }
        ).strip()

        validacion = validar_respuesta(
            respuesta=respuesta,
            contexto=recuperacion["contexto"],
            fuentes=recuperacion["fuentes"],
        )

    if not validacion["valida"]:
        respuesta_final = MENSAJE_SIN_RESPUESTA
        fuentes_finales: list[dict[str, Any]] = []
        uso_fallback = True
    else:
        respuesta_final = respuesta
        fuentes_finales = recuperacion["fuentes"]
        uso_fallback = False

    bloque_fuentes = formatear_fuentes(fuentes_finales)
    respuesta_con_fuentes = respuesta_final
    if bloque_fuentes:
        respuesta_con_fuentes += "\n\n" + bloque_fuentes

    return {
        "pregunta": pregunta,
        "respuesta": respuesta_final,
        "respuesta_con_fuentes": respuesta_con_fuentes,
        "fuentes": fuentes_finales,
        "confianza": confianza,
        "validacion": {
            **validacion,
            "intentos_regeneracion": intentos,
        },
        "recuperacion": recuperacion,
        "uso_fallback": uso_fallback,
    }


if __name__ == "__main__":
    resultado = responder_pregunta(
        "¿Qué debo registrar durante el monitoreo del gusano cogollero?"
    )
    print(resultado["respuesta_con_fuentes"])
    print("\nValidación:", resultado["validacion"])


# ========================================================================
# API PÚBLICA SIMPLIFICADA
# ========================================================================
def ejecutar_pipeline_completo() -> dict:
    """Procesa los documentos y reconstruye el índice FAISS."""
    procesamiento = procesar_todos()
    indexacion = construir_indice(sobrescribir=True)
    return {"procesamiento": procesamiento, "indexacion": indexacion}
