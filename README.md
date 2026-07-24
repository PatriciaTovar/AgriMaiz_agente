# AgriAsistente V4

Aplicación RAG para consultar y administrar la documentación interna de AgriMaiz.

## Cambios principales

- Se puede preguntar directamente sin cargar documentos.
- La pestaña **Base documental** no requiere contraseña.
- Permite añadir, eliminar y reconstruir la base documental.
- El procesamiento y la actualización del índice ocurren automáticamente.
- La recuperación prioriza procedimientos, manuales y preguntas frecuentes.
- Se reforzó la búsqueda para las cuatro preguntas sugeridas.
- Las fuentes se muestran una sola vez.
- La página abre inmediatamente; la base se prepara de forma diferida.
- Incluye una pestaña con diagramas de la arquitectura RAG y del flujo documental.

## Estructura

```text
agrimaiz_agente_rag_v4/
├── app.py
├── agente.py
├── documentos/
├── almacenamiento/
├── requirements.txt
├── .env.example
├── Dockerfile
└── deploy_oci.md
```

## Preparar el entorno virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configuración

Copia `.env.example` como `.env` y agrega tu clave y modelo:

```env
GROQ_API_KEY=tu_clave
GROQ_MODEL=tu_modelo_disponible
```

## Ejecutar

```powershell
streamlit run app.py
```

La primera ejecución puede tardar mientras se construye el índice con los
documentos incluidos.


## Inicio más rápido

La aplicación ya no procesa la base mientras carga la página. Si el índice no
existe, puedes:

1. hacer la primera pregunta y esperar la preparación inicial; o
2. abrir **Base documental** y pulsar **Preparar base**.

Después de esa primera preparación, las siguientes aperturas son mucho más rápidas.

## Diagramas

La pestaña **Arquitectura** muestra:

- el flujo completo de consulta RAG;
- el flujo de actualización de documentos.
