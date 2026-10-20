# UniTramite AI — Chatbot de Atención a Estudiantes

Prototipo académico para demostrar flujos de atención estudiantil inspirados en el documento UniTramite AI. Incluye una interfaz web interactiva, validaciones deterministas con datos ficticios y seguimiento de solicitudes mediante tickets.

> **Aviso:** este proyecto es una demostración. No está conectado a sistemas reales de la universidad, no valida identidades reales y no emite documentos oficiales. Los requisitos implementados son ilustrativos y deben contrastarse con las normas institucionales antes de cualquier uso real.

## 1. ¿Qué hace?

- Permite conversar con el chatbot desde una interfaz web.
- Simula solicitudes de récord académico y certificación de estudio.
- Comprueba requisitos usando registros ficticios.
- Genera un ticket y permite consultar su estado.
- Muestra un panel de solicitudes almacenadas en SQLite (local) o PostgreSQL (nube).
- Incluye un webhook inicial para planificar la futura conexión con WhatsApp Business; **WhatsApp no está conectado en esta versión**.

## 2. Datos: procedencia y significado

Los datos de estudiantes están en `data/students.json` y fueron creados artificialmente para este prototipo. No provienen de la UASD ni contienen datos personales reales.

| Matrícula ficticia | Matrícula activa | Paz y salvo | Caso de prueba |
|---|---:|---:|---|
| `2024-1001` | Sí | Sí | Cumple los requisitos ilustrativos del récord |
| `2024-1002` | Sí | No | Tiene paz y salvo pendiente |
| `2023-2040` | No | Sí | Matrícula inactiva |

Las reglas están definidas en `core.py`:
- Récord académico: matrícula activa y paz y salvo.
- Certificación de estudio: matrícula activa.

Estas reglas son ejemplos de desarrollo, no una afirmación sobre los requisitos oficiales vigentes de una universidad.

Los estudiantes **no se guardan** en la base de datos: se leen siempre de `data/students.json`. Lo que se guarda son las **solicitudes (tickets)**, en la tabla `requests`:

- **Sin configurar nada:** se usa el archivo local `unitramite.db` (SQLite), que se crea automáticamente al iniciar la aplicación.
- **Con la variable `DATABASE_URL`:** se usa PostgreSQL en la nube (Neon, Supabase u otro). La tabla y la secuencia de tickets se crean solas al arrancar. Ver la sección 9.

## 3. Requisitos

- Python 3.10 o superior.
- `pip`.
- VS Code u otro editor (opcional).

## 4. Instalación reproducible

Descarga o clona el repositorio y entra en la carpeta del proyecto.

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell bloquea la activación, abre una terminal CMD y usa:

```bat
.venv\Scripts\activate.bat
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Ejecutar la demo

Desde la carpeta raíz y con el entorno virtual activado:

```bash
streamlit run app.py
```

Streamlit mostrará una dirección local, normalmente `http://localhost:8501`. Ábrela en un navegador.

### Guion de demostración en clase

1. En «Conversar con el chatbot», escribe: `Necesito un récord académico`.
2. Cuando lo solicite, escribe la matrícula ficticia `2024-1001`. Debe registrar una solicitud y mostrar un ticket.
3. Repite el proceso con `2024-1002`; debe dejar la solicitud pendiente de revisión porque el paz y salvo figura pendiente.
4. En «Consultar una solicitud», consulta el ticket que acabas de recibir.
5. En «Panel de solicitudes», muestra el registro local.
6. Prueba una pregunta frecuente, por ejemplo: `¿El chatbot emite documentos oficiales?`.

Los identificadores de tickets se generan en ejecución; usa el ticket que muestra la aplicación en lugar de asumir que tendrá siempre un número determinado.

## 6. Ejecutar pruebas automatizadas

```bash
python -m unittest discover -s tests -v
```

Las pruebas verifican algunas funciones de validación y el formato de ticket. No sustituyen una evaluación completa del chatbot ni prueban una integración con WhatsApp.

## 7. Estructura del proyecto

```text
UniTramiteAI_Prototipo/
├── app.py
├── core.py
├── whatsapp_webhook.py
├── requirements.txt
├── README.md
├── data/
│   └── students.json
└── tests/
    └── test_core.py
```

## 8. Publicarlo en GitHub

1. Crea un repositorio vacío en GitHub, por ejemplo `unitramite-ai`.
2. Abre la terminal en la carpeta del proyecto.
3. Ejecuta:

```bash
git init
git add .
git commit -m "Entrega inicial del prototipo UniTramite AI"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/unitramite-ai.git
git push -u origin main
```

Sustituye `TU_USUARIO` por tu usuario real de GitHub y usa la URL que GitHub asigne a tu repositorio. No subas contraseñas, tokens ni archivos `.env`.

## 9. Publicar una demo en Streamlit Community Cloud

1. Sube el repositorio a GitHub.
2. Entra en Streamlit Community Cloud y conecta tu cuenta de GitHub.
3. Selecciona el repositorio, la rama `main` y el archivo principal `app.py`.
4. Despliega la aplicación.
5. Abre la URL pública y repite el guion de demostración.

### Guardar las solicitudes en PostgreSQL (recomendado)

En Streamlit Community Cloud el archivo SQLite se borra cada vez que la app se reinicia o se vuelve a desplegar. Para que las solicitudes no se pierdan, usa una base PostgreSQL gestionada:

1. Crea una cuenta gratuita en [Neon](https://neon.tech) (o [Supabase](https://supabase.com)) y crea un proyecto/base de datos.
2. Copia la cadena de conexión. Tiene esta forma: `postgresql://usuario:contraseña@host/base?sslmode=require`.
3. En Streamlit Community Cloud abre tu app → **Settings → Secrets** y añade:

   ```toml
   DATABASE_URL = "postgresql://usuario:contraseña@host/base?sslmode=require"
   ```

4. Reinicia la app. Crea una solicitud desde el chatbot y compruébala en el «Panel de solicitudes» y en el editor de tablas de Neon/Supabase (tabla `requests`).

Para usar PostgreSQL en tu computadora, crea el archivo `.streamlit/secrets.toml` con la misma línea, o define la variable de entorno `DATABASE_URL` antes de `streamlit run app.py`. Ese archivo está en `.gitignore`: **nunca subas la contraseña a GitHub**.

Las pruebas usan SQLite temporal. Para repetirlas también contra PostgreSQL, define `TEST_DATABASE_URL` apuntando a una base **de pruebas** (las pruebas borran su tabla `requests`):

```bash
TEST_DATABASE_URL="postgresql://..." python -m unittest discover -s tests -v
```

La disponibilidad del servicio y los pasos de la plataforma pueden cambiar. Antes de presentar, verifica que la URL pública abra correctamente.

## 10. Limitaciones conocidas y próximos pasos

- La aplicación web es el canal que funciona en esta versión.
- El webhook de WhatsApp es solo una estructura inicial: no envía respuestas ni tiene validación de firma completa.
- La matrícula ficticia sirve para demostrar el flujo, no para autenticar a una persona.
- El estado académico y el paz y salvo se consultan en datos estáticos de prueba.
- El LLM/RAG, la base de conocimiento institucional y la integración real están pendientes.
- Para producción hacen falta autenticación, autorización, protección de datos, manejo seguro de credenciales, auditoría y pruebas de seguridad.

## 11. Relación con el documento original

El documento de UniTramite AI propone atención mediante LLM y WhatsApp Business, y describe gestión de récords, certificaciones y seguimiento de solicitudes. Esta implementación es un **MVP académico parcial**: demuestra esos flujos mediante una interfaz web, reglas simples y datos simulados. Las decisiones de tecnología, datos de prueba y validaciones son nuevas decisiones del prototipo.
