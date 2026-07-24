# 🌽 AgriAsistente

AgriAsistente es un asistente inteligente basado en Retrieval-Augmented Generation (RAG) diseñado para consultar documentación técnica sobre el manejo integrado de *Spodoptera frugiperda* (gusano cogollero) en maíz.

El sistema utiliza búsqueda híbrida sobre una base documental propia y un modelo de lenguaje para generar respuestas fundamentadas con referencias a las fuentes consultadas.

---

# Características

- Recuperación de información mediante RAG.
- Base documental editable desde la interfaz.
- Actualización automática del índice.
- Respuestas con referencias bibliográficas.
- Arquitectura visual integrada.
- Despliegue en Oracle Cloud Infrastructure.
- Contenedorización mediante Docker/Podman.

---

# Tecnologías

- Python 3.11
- Streamlit
- LangChain
- FAISS
- Sentence Transformers
- Groq API
- OCI Compute
- Podman
- Git

---

# Arquitectura

El flujo general del sistema es:

Pregunta del usuario

↓

Recuperación híbrida

↓

Re-ranking

↓

Construcción del contexto

↓

LLM (Groq)

↓

Respuesta con fuentes

---

# Instalación

```bash
git clone https://github.com/PatriciaTovar/AgriMaiz_agente.git
cd AgriMaiz_agente

python -m venv .venv

source .venv/bin/activate
```

Instalar dependencias

```bash
pip install -r requirements.txt
```

---

# Variables de entorno

```env
GROQ_API_KEY=xxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile
```

---

# Ejecutar

```bash
streamlit run app.py
```

---

# Despliegue en OCI

El proyecto fue desplegado en Oracle Cloud Infrastructure utilizando:

- Oracle Linux 8
- OCI Compute
- Podman
- Puerto 8501
- Almacenamiento persistente

La guía completa se encuentra en:

deploy_oci.md

---

# Registro de ejecución

La ejecución del sistema en la nube se documentó mediante:

- registros JSONL
- evidencias de ejecución
- capturas de pantalla
- pruebas desde OCI

Consultar:

registro_ejecucion.md

---

# Autor

Patricia Guadalupe Tovar De La Torre

Maestría en Cómputo Aplicado

Colegio de Postgraduados
