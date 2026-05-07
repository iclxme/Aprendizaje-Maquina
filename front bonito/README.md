# Frontend - Chatbot Deportes (front de virgito)

Archivos: `index.html`, `styles.css`, `app.js`.

Instrucciones rápidas:

1. Asegúrate de arrancar el backend (desde la raíz del repo):

```bash
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

2. Servir el frontend (opcional, para evitar problemas CORS usar un servidor simple):

```bash
# desde la carpeta "front de virgito"
python -m http.server 5500
# luego abrir http://127.0.0.1:5500
```

Si prefieres abrir `index.html` por archivo local, es posible pero algunos navegadores bloquean fetch por CORS. Recomiendo usar el servidor anterior.
