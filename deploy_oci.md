# Deploy mínimo en OCI

Para el desafío se propone:

1. Construir la imagen con el `Dockerfile`.
2. Publicarla en OCI Container Registry.
3. Ejecutarla en una instancia OCI Compute.
4. Abrir el puerto 8501 mediante las reglas de red necesarias.
5. Guardar `GROQ_API_KEY` y `GROQ_MODEL` como variables seguras de la instancia.

Comandos generales:

```bash
docker build -t agrimaiz-asistente .
docker run -p 8501:8501 --env-file .env agrimaiz-asistente
```

La carpeta `documentos/` y `almacenamiento/` deben montarse como volúmenes persistentes en la nube.
