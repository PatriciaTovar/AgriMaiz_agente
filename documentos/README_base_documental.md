# Base documental RAG para manejo del gusano cogollero en maíz

Esta carpeta contiene una base documental heterogénea diseñada para probar un asistente con arquitectura **RAG** sobre *Spodoptera frugiperda* en maíz.

## Objetivo

Organizar conocimiento técnico previamente extraído, limpiado, normalizado, clasificado y filtrado, de manera que pueda ser procesado por cargadores de documentos y recuperado por similitud semántica.

## Archivos

| Archivo | Formato | Función en el RAG |
|---|---|---|
| `manual_manejo_integrado.pdf` | PDF | Documento técnico narrativo sobre prevención, diagnóstico y manejo integrado. |
| `procedimiento_monitoreo.docx` | Word | Procedimiento operativo con pasos de inspección y registro. |
| `base_conocimiento.xlsx` | Excel | Tablas estructuradas de enemigos naturales, decisiones y fuentes. |
| `corpus_curado_rag.csv` | CSV | Fragmentos seleccionados del lote procesado, con metadatos y URL. |
| `categorias_sinonimos.json` | JSON | Taxonomía temática, sinónimos y reglas mínimas del asistente. |
| `preguntas_frecuentes.md` | Markdown | Preguntas y respuestas breves para recuperación directa. |
| `glosario.html` | HTML | Definiciones de conceptos técnicos en una página navegable. |
| `manifiesto_documental.json` | JSON | Inventario y propósito de cada documento. |

## Flujo recomendado

```text
Carga multiformato
    -> extracción de texto y metadatos
    -> fragmentación
    -> embeddings
    -> almacén vectorial
    -> recuperación
    -> respuesta fundamentada
```

## Reglas del asistente

1. Priorizar monitoreo y confirmación de larvas vivas.
2. Distinguir prevención, intervención y evaluación posterior.
3. No inventar dosis, umbrales o registros de productos.
4. Señalar cuándo una recomendación depende de región, clima o etapa fenológica.
5. Conservar la URL y metadatos del fragmento recuperado.
6. Incluir una advertencia cuando se mencione control químico.

> Material educativo y de apoyo a la toma de decisiones. Las recomendaciones deben adaptarse a la región, etapa del cultivo, nivel de infestación, etiqueta vigente del producto y normativa local. No sustituye el diagnóstico de personal técnico.
