import streamlit as st
from core import (
    init_db, get_student, create_request, get_request,
    get_requirements, validate_request, list_requests, faq_answer
)

st.set_page_config(page_title="UniTramite AI | Atención a Estudiantes", page_icon="🎓", layout="wide")
init_db()

st.title("🎓 Chatbot de Atención a Estudiantes")
st.caption("UniTramite AI · Prototipo académico con datos simulados")
st.warning("Demostración: no conecta con sistemas reales de la universidad. Usa exclusivamente los estudiantes y tickets ficticios incluidos.")

with st.sidebar:
    st.header("Menú")
    section = st.radio("Selecciona una función", [
        "Conversar con el chatbot",
        "Consultar una solicitud",
        "Panel de solicitudes",
        "Preguntas frecuentes",
        "Acerca del prototipo"
    ])
    st.divider()
    st.caption("Versión 0.1 · Canal web activo")

if section == "Conversar con el chatbot":
    st.subheader("Atención conversacional")
    st.write("Puedes solicitar un récord académico, una certificación de estudio o ayuda para consultar un ticket.")
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "¡Hola! Soy UniTramite AI. Puedo ayudarte con récords académicos, certificaciones y seguimiento de solicitudes. Para empezar, indícame tu matrícula ficticia (por ejemplo, 2024-1001) y qué trámite necesitas."
        }]
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = st.chat_input("Escribe tu consulta...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        text = prompt.lower().strip()
        response = None

        # Seguimiento de tickets
        import re
        ticket_match = re.search(r"(UT-\d{6})", prompt.upper())
        if ticket_match:
            req = get_request(ticket_match.group(1))
            if req:
                response = (
                    f"**Solicitud {req['ticket']}**\n\n"
                    f"- Tipo: {req['request_type']}\n"
                    f"- Estado: **{req['status']}**\n"
                    f"- Fecha de creación: {req['created_at']}\n"
                    f"- Observación: {req['notes']}"
                )
            else:
                response = "No encontré ese ticket en la base de datos simulada. Verifica el identificador o solicita ayuda al personal de atención."

        # Identificar intención y matrícula
        elif any(k in text for k in ["récord", "record", "historial académico"]):
            st.session_state.pending_type = "Récord académico"
            response = "Puedo registrar una solicitud de récord académico. Para la demostración, escribe tu matrícula ficticia (ej.: 2024-1001). No compartas datos personales reales."
        elif any(k in text for k in ["certificación", "certificado", "constancia", "estudio"]):
            st.session_state.pending_type = "Certificación de estudio"
            response = "Puedo registrar una solicitud de certificación de estudio. Escribe tu matrícula ficticia (ej.: 2024-1001). No uses datos personales reales."
        elif any(k in text for k in ["estado", "seguimiento", "ticket", "solicitud"]):
            response = "Para consultar el estado, envíame el identificador del ticket (formato UT-000001). También puedes usar la sección «Consultar una solicitud»."
        else:
            import re
            student_match = re.search(r"\b\d{4}-\d{4}\b", prompt)
            if student_match and st.session_state.get("pending_type"):
                student_id = student_match.group(0)
                student = get_student(student_id)
                if not student:
                    response = "La matrícula no existe en los datos de prueba. Prueba con 2024-1001, 2024-1002 o 2023-2040."
                else:
                    request_type = st.session_state.pending_type
                    checks = validate_request(student, request_type)
                    missing = [name for name, ok in checks.items() if not ok]
                    if missing:
                        ticket = create_request(student_id, request_type, "Pendiente de revisión", "No cumple: " + ", ".join(missing))
                        response = (
                            f"Registré la solicitud **{ticket}**, pero queda **Pendiente de revisión**.\n\n"
                            f"Validaciones que requieren atención: {', '.join(missing)}.\n\n"
                            "El prototipo no rechaza definitivamente la solicitud ni sustituye la revisión de la oficina académica."
                        )
                    else:
                        ticket = create_request(student_id, request_type, "Recibida", "Validaciones simuladas completadas; pendiente de revisión institucional.")
                        response = (
                            f"Las validaciones simuladas se completaron y registré la solicitud **{ticket}** con estado **Recibida**.\n\n"
                            "Esto no significa que el documento haya sido emitido. La oficina académica debe procesar la solicitud."
                        )
                    st.session_state.pending_type = None
            else:
                response = faq_answer(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

elif section == "Consultar una solicitud":
    st.subheader("Seguimiento por ticket")
    ticket = st.text_input("Identificador de ticket", placeholder="UT-000001").strip().upper()
    if st.button("Consultar", type="primary"):
        if not ticket:
            st.info("Introduce un identificador.")
        else:
            req = get_request(ticket)
            if req:
                st.success(f"Estado: {req['status']}")
                st.write(f"**Tipo:** {req['request_type']}")
                st.write(f"**Fecha:** {req['created_at']}")
                st.write(f"**Observación:** {req['notes']}")
            else:
                st.error("No se encontró el ticket en la base simulada.")

elif section == "Panel de solicitudes":
    st.subheader("Panel de control — datos ficticios")
    rows = list_requests()
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption("Los tickets son demostrativos. En producción, este panel requeriría autenticación y permisos por rol.")
    else:
        st.info("Todavía no hay solicitudes. Crea una desde el chatbot.")

elif section == "Preguntas frecuentes":
    st.subheader("Preguntas frecuentes")
    questions = [
        "¿Cómo solicito un récord académico?",
        "¿Cómo solicito una certificación de estudio?",
        "¿Cómo consulto el estado de mi solicitud?",
        "¿El chatbot emite documentos oficiales?",
        "¿Qué hago si mi paz y salvo está pendiente?"
    ]
    for q in questions:
        with st.expander(q):
            st.write(faq_answer(q))

else:
    st.subheader("Alcance y limitaciones")
    st.markdown("""
**Incluido en esta versión**
- Interfaz web conversacional.
- Tres flujos: récord académico, certificación y seguimiento de tickets.
- Reglas deterministas sobre datos ficticios.
- Registro local de solicitudes SQLite.
- Panel básico de solicitudes.

**No incluido todavía**
- LLM conectado a un proveedor.
- WhatsApp Business API activa.
- Integración con sistemas académicos reales.
- Autenticación real de estudiantes.
- Emisión o firma de documentos oficiales.

**Principio de seguridad:** el chatbot no debe inventar datos ni afirmar que emitió un documento cuando solo registró una solicitud.
""")
