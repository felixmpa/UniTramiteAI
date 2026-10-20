import sqlite3
from pathlib import Path
from datetime import datetime
import json
import re

ROOT = Path(__file__).parent
DB_PATH = ROOT / "unitramite.db"
SEED_PATH = ROOT / "data" / "students.json"

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            ticket TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            request_type TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            notes TEXT NOT NULL
        )""")
        count = con.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    # Seed tickets only once
    if count == 0:
        con = connect()
        con.execute(
            "INSERT OR IGNORE INTO requests VALUES (?, ?, ?, ?, ?, ?)",
            ("UT-000001", "2024-1001", "Récord académico", "En proceso", "2026-10-01 09:30", "Solicitud de demostración.")
        )
        con.commit()
        con.close()

def get_student(student_id):
    with open(SEED_PATH, encoding="utf-8") as f:
        students = json.load(f)
    return students.get(student_id)

def get_requirements(request_type):
    return {
        "Récord académico": ["matricula_activa", "paz_y_salvo"],
        "Certificación de estudio": ["matricula_activa"]
    }.get(request_type, [])

def validate_request(student, request_type):
    """Return named boolean checks; these rules are illustrative, not official policy."""
    requirements = get_requirements(request_type)
    labels = {
        "matricula_activa": "matrícula activa",
        "paz_y_salvo": "paz y salvo"
    }
    return {labels[r]: bool(student.get(r, False)) for r in requirements}

def create_request(student_id, request_type, status, notes):
    with connect() as con:
        last = con.execute("SELECT ticket FROM requests ORDER BY ticket DESC LIMIT 1").fetchone()
        number = int(last["ticket"].split("-")[1]) + 1 if last else 1
        ticket = f"UT-{number:06d}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        con.execute(
            "INSERT INTO requests VALUES (?, ?, ?, ?, ?, ?)",
            (ticket, student_id, request_type, status, now, notes)
        )
    return ticket

def get_request(ticket):
    with connect() as con:
        row = con.execute("SELECT * FROM requests WHERE ticket = ?", (ticket,)).fetchone()
    return dict(row) if row else None

def list_requests():
    with connect() as con:
        rows = con.execute("""
            SELECT ticket AS Ticket, student_id AS Matrícula,
                   request_type AS Trámite, status AS Estado,
                   created_at AS Fecha, notes AS Observación
            FROM requests ORDER BY created_at DESC
        """).fetchall()
    return [dict(r) for r in rows]

def faq_answer(question):
    q = question.lower()
    if any(k in q for k in ["récord", "record", "historial académico"]):
        return "Puedes solicitar un récord académico desde el chatbot. El prototipo verifica matrícula activa y paz y salvo con datos ficticios y registra un ticket. Los requisitos reales deben confirmarse con la universidad."
    if any(k in q for k in ["certificación", "certificado", "constancia"]):
        return "Puedes solicitar una certificación de estudio. En esta demostración se verifica la matrícula activa. La emisión oficial corresponde al área académica."
    if any(k in q for k in ["estado", "seguimiento", "ticket", "solicitud"]):
        return "Para consultar una solicitud, introduce su identificador, por ejemplo UT-000001, en la sección de seguimiento."
    if "paz y salvo" in q:
        return "Si tu paz y salvo aparece pendiente, el chatbot registra el caso para revisión. No puede modificar estados financieros ni conceder excepciones."
    if any(k in q for k in ["emite", "documento oficial", "oficial"]):
        return "No. Este prototipo registra solicitudes y demuestra validaciones. No emite documentos oficiales ni tiene conexión con los sistemas universitarios."
    return "Puedo orientarte sobre récords académicos, certificaciones y seguimiento de solicitudes. Si tu caso requiere una decisión administrativa, debe revisarlo el personal autorizado."

def validate_ticket_format(ticket):
    return bool(re.fullmatch(r"UT-\d{6}", ticket or ""))

def detect_request_type(text):
    t = text.lower()
    if any(k in t for k in ["récord", "record", "historial académico"]):
        return "Récord académico"
    if any(k in t for k in ["certificación", "certificacion", "certificado", "constancia", "estudio"]):
        return "Certificación de estudio"
    return None

def format_request(req):
    return (
        f"**Solicitud {req['ticket']}**\n\n"
        f"- Tipo: {req['request_type']}\n"
        f"- Estado: **{req['status']}**\n"
        f"- Fecha de creación: {req['created_at']}\n"
        f"- Observación: {req['notes']}"
    )

def register_request(student_id, request_type):
    """Validate the student and store the request; returns the chatbot reply."""
    student = get_student(student_id)
    checks = validate_request(student, request_type)
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        ticket = create_request(student_id, request_type, "Pendiente de revisión", "No cumple: " + ", ".join(missing))
        return (
            f"Registré la solicitud **{ticket}**, pero queda **Pendiente de revisión**.\n\n"
            f"Validaciones que requieren atención: {', '.join(missing)}.\n\n"
            "El prototipo no rechaza definitivamente la solicitud ni sustituye la revisión de la oficina académica."
        )
    ticket = create_request(student_id, request_type, "Recibida", "Validaciones simuladas completadas; pendiente de revisión institucional.")
    return (
        f"Las validaciones simuladas se completaron y registré la solicitud **{ticket}** con estado **Recibida**.\n\n"
        "Esto no significa que el documento haya sido emitido. La oficina académica debe procesar la solicitud."
    )

def handle_message(prompt, state):
    """Return the chatbot reply. `state` keeps pending_type/pending_student between turns and is updated in place."""
    ticket_match = re.search(r"UT-\d{6}", prompt.upper())
    if ticket_match:
        req = get_request(ticket_match.group(0))
        if req:
            return format_request(req)
        return "No encontré ese ticket en la base de datos simulada. Verifica el identificador o solicita ayuda al personal de atención."

    request_type = detect_request_type(prompt)
    if request_type:
        state["pending_type"] = request_type
    student_match = re.search(r"\b\d{4}-\d{4}\b", prompt)
    if student_match:
        if not get_student(student_match.group(0)):
            state["pending_student"] = None
            return "La matrícula no existe en los datos de prueba. Prueba con 2024-1001, 2024-1002 o 2023-2040."
        state["pending_student"] = student_match.group(0)

    if state.get("pending_type") and state.get("pending_student"):
        response = register_request(state["pending_student"], state["pending_type"])
        state["pending_type"] = state["pending_student"] = None
        return response
    if request_type == "Récord académico":
        return "Puedo registrar una solicitud de récord académico. Para la demostración, escribe tu matrícula ficticia (ej.: 2024-1001). No compartas datos personales reales."
    if request_type == "Certificación de estudio":
        return "Puedo registrar una solicitud de certificación de estudio. Escribe tu matrícula ficticia (ej.: 2024-1001). No uses datos personales reales."
    if student_match:
        return f"Tengo tu matrícula **{state['pending_student']}**. ¿Qué trámite necesitas: récord académico o certificación de estudio?"
    if any(k in prompt.lower() for k in ["estado", "seguimiento", "ticket", "solicitud"]):
        return "Para consultar el estado, envíame el identificador del ticket (formato UT-000001). También puedes usar la sección «Consultar una solicitud»."
    return faq_answer(prompt)
