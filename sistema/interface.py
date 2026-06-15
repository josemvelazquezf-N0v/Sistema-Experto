import json
from pathlib import Path

# Importar los módulos del sistema
from sistema.motor_inferencia import MotorInferencia
from sistema.explicacion import ModuloExplicacion

# ---------------------------------------------------------------------------
# TODO (fase 2): Pipeline PDF → knowledge base
#
# El script fuente_datos/extraer_texto.py convierte PDFs del DOF en texto
# plano para que el knowledge engineer codifique reglas en reglas.json.
# No es parte del runtime — es un dev tool.
#
# Uso: python fuente_datos/extraer_texto.py fuente_datos/pdfs/NOM-035.pdf
# Requiere: pip install pdfplumber
# ---------------------------------------------------------------------------


# Ruta al archivo de preguntas — usa helper para compatibilidad con .exe
from sistema.motor_inferencia import ruta_recurso
RUTA_PREGUNTAS = ruta_recurso("conocimientos/preguntas.json")

# Keywords que activan comandos especiales (case-insensitive)
KEYWORDS_POR_QUE  = {"por que", "por qué", "why", "¿por qué?", "¿por que?"}
KEYWORDS_COMO     = {"como", "cómo", "how", "¿cómo?", "¿como?", "como llegaste"}
KEYWORDS_REINICIO = {"reiniciar", "restart", "nueva sesion", "nueva sesión", "reset"}
KEYWORDS_SALIR    = {"salir", "exit", "quit", "q", "bye"}


def cargar_preguntas() -> list[dict]:
    """Carga el catálogo de preguntas desde preguntas.json."""
    with open(RUTA_PREGUNTAS, encoding="utf-8") as f:
        return json.load(f)["preguntas"]


def imprimir_encabezado() -> None:
    """Imprime el encabezado del sistema al iniciar."""
    print("\n" + "═" * 62)
    print("  SISTEMA EXPERTO — NORMAS NOM-STPS")
    print("  Diagnóstico de normas aplicables a tu centro de trabajo")
    print("═" * 62)
    print("  Comandos disponibles en cualquier momento:")
    print("    'por qué'   → explica cómo se identificó la última norma")
    print("    'cómo'      → muestra la cadena completa de razonamiento")
    print("    'reiniciar' → inicia un nuevo diagnóstico")
    print("    'salir'     → cierra el sistema")
    print("═" * 62 + "\n")


def hacer_pregunta(pregunta: dict) -> str | None:
    """
    Muestra una pregunta con sus opciones numeradas y espera una respuesta.

    Retorna:
      - El valor canónico seleccionado (ej: "si", "mas_de_100")
      - "__salir__", "__reiniciar__", "__por_que__", "__como__" si se detecta keyword

    Por qué retornar el valor y no la etiqueta:
      El motor trabaja con valores internos ('mas_de_100'), no con las
      etiquetas visibles ('Más de 100'). La separación etiqueta/valor en
      preguntas.json permite cambiar el texto al usuario sin tocar las reglas.
    """
    print(f"  {pregunta['texto']}")
    opciones = pregunta["opciones"]

    # Mostrar opciones numeradas
    for i, opcion in enumerate(opciones, 1):
        print(f"    {i}. {opcion['etiqueta']}")

    while True:
        entrada = input("\n  Tu respuesta: ").strip().lower()

        # ── Detección de keywords especiales ──────────────────────────
        # Se hace ANTES de validar el número para que siempre funcionen
        if entrada in KEYWORDS_SALIR:
            return "__salir__"
        if entrada in KEYWORDS_REINICIO:
            return "__reiniciar__"
        if entrada in KEYWORDS_POR_QUE:
            return "__por_que__"
        if entrada in KEYWORDS_COMO:
            return "__como__"

        # ── Validar selección numérica ─────────────────────────────────
        if entrada.isdigit():
            idx = int(entrada) - 1  # Convertir a índice base-0
            if 0 <= idx < len(opciones):
                seleccionada = opciones[idx]
                print(f"  → {seleccionada['etiqueta']}\n")
                return seleccionada["valor"]  # Retornar el valor canónico

        print(f"  ⚠  Ingresa un número del 1 al {len(opciones)}.")


def ejecutar_sesion(
    preguntas:  list[dict],
    motor:      MotorInferencia,
    explicador: ModuloExplicacion,
) -> str:
    """
    Ejecuta una sesión completa de diagnóstico.

    Itera sobre todas las preguntas, inserta los hechos en el motor
    y muestra notificaciones cuando se identifican normas nuevas.

    Retorna:
      'reiniciar' → el caller debe iniciar una nueva sesión
      'salir'     → el caller debe terminar el programa
    """
    motor.reiniciar()  # Limpiar estado de sesión anterior
    ultima_nom = None  # Referencia para el comando 'por qué'
    indice = 0         # Índice explícito para poder repetir preguntas con keywords

    print("  Responde las siguientes preguntas sobre tu centro de trabajo.\n")

    # Iterar con índice explícito en lugar de for-each
    # porque los keywords deben re-mostrar la pregunta actual
    while indice < len(preguntas):
        pregunta = preguntas[indice]
        resultado = hacer_pregunta(pregunta)

        # ── Manejo de keywords ─────────────────────────────────────────
        if resultado == "__salir__":
            return "salir"

        if resultado == "__reiniciar__":
            print("\n  Reiniciando diagnóstico...\n")
            return "reiniciar"

        if resultado == "__por_que__":
            # Explicar la última NOM identificada, si existe
            if ultima_nom:
                print(explicador.por_que(motor.traza, ultima_nom))
            else:
                print("\n  Aún no se han identificado normas. Continúa respondiendo.\n")
            continue  # Re-mostrar la misma pregunta (indice no avanza)

        if resultado == "__como__":
            print(explicador.como(motor.traza))
            continue  # Re-mostrar la misma pregunta

        # ── Hecho válido — insertar en memoria y correr el motor ───────
        motor.agregar_hecho(pregunta["id"], resultado)

        # Ejecutar el motor: dispara todas las reglas que ahora matchean
        disparadas = motor.ejecutar()

        # Notificar al usuario cada vez que se identifica una norma nueva
        nuevas_noms = [r for r in disparadas if r["conclusion"].startswith("aplica_")]
        for r in nuevas_noms:
            print(f"  [motor] Norma identificada: {r['nom']}")
            ultima_nom = r["nom"]  # Actualizar referencia para 'por qué'

        indice += 1  # Avanzar a la siguiente pregunta

    # ── Todas las preguntas respondidas — mostrar reporte final ────────
    print(explicador.resumen_final(motor.traza))

    # Ofrecer comandos adicionales post-diagnóstico
    print("\n  ¿Deseas más información?")
    print("    'cómo'              → cadena de razonamiento completa")
    print("    'por qué NOM-XXX'   → explica una norma específica")
    print("    'reiniciar'         → nuevo diagnóstico")
    print("    'salir'             → cerrar el sistema\n")

    # Loop post-diagnóstico para comandos de explicación
    while True:
        entrada = input("  > ").strip().lower()

        if entrada in KEYWORDS_SALIR:
            return "salir"

        if entrada in KEYWORDS_REINICIO:
            return "reiniciar"

        if entrada in KEYWORDS_COMO:
            print(explicador.como(motor.traza))

        elif entrada.startswith("por qué") or entrada.startswith("por que"):
            # Extraer el nombre de la NOM del input
            # Ej: "por qué NOM-035" → fragmento = "NOM-035"
            partes = entrada.split()
            fragmento = " ".join(partes[2:]).upper() if len(partes) > 2 else ""

            if fragmento:
                # Buscar en la traza la NOM que contenga el fragmento
                coincidencia = next(
                    (paso["nom"] for paso in motor.traza
                     if fragmento in paso.get("nom", "")),
                    None
                )
                if coincidencia:
                    print(explicador.por_que(motor.traza, coincidencia))
                else:
                    print(f"\n  No encontré '{fragmento}' entre las normas identificadas.\n")
            elif ultima_nom:
                # Sin fragmento → explicar la última NOM identificada
                print(explicador.por_que(motor.traza, ultima_nom))
            else:
                print("\n  Especifica la norma. Ejemplo: 'por qué NOM-035'\n")

        else:
            print("  Comando no reconocido. Usa 'cómo', 'por qué', 'reiniciar' o 'salir'.")


def iniciar() -> None:
    """
    Entry point del chatbot.
    Carga los recursos y ejecuta el loop principal de sesiones.
    """
    preguntas  = cargar_preguntas()
    motor      = MotorInferencia()
    explicador = ModuloExplicacion()

    imprimir_encabezado()

    # Loop principal — permite múltiples sesiones sin reiniciar el programa
    while True:
        resultado = ejecutar_sesion(preguntas, motor, explicador)
        if resultado == "salir":
            print("\n  Hasta luego.\n")
            break
        # Si resultado == "reiniciar", el while itera y ejecutar_sesion se llama de nuevo
