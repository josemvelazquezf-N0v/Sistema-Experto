import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
from pathlib import Path

# Importar los módulos del sistema (sin cambios)
from sistema.motor_inferencia import MotorInferencia
from sistema.explicacion import ModuloExplicacion


# ── Constantes de color y fuente ────────────────────────────────────────────
COLOR_PRIMARIO    = "#003B6F"   # Azul STPS — encabezados y botones
COLOR_SECUNDARIO  = "#0057A8"   # Azul medio — hover y acento
COLOR_FONDO_IZQ   = "#E8F0FA"   # Azul muy claro — panel de preguntas
COLOR_FONDO_DER   = "#FFFFFF"   # Blanco — panel de resultados
COLOR_VERDE       = "#1A7A4A"   # Verde — normas identificadas y éxito
COLOR_GRIS        = "#5A5A5A"   # Gris — texto secundario
COLOR_GRIS_CLARO  = "#F0F0F0"   # Gris muy claro — separadores
COLOR_TEXTO       = "#1A1A1A"   # Casi negro — texto principal

FUENTE_TITULO     = ("Segoe UI", 13, "bold")
FUENTE_SUBTITULO  = ("Segoe UI", 10, "bold")
FUENTE_NORMAL     = ("Segoe UI", 10)
FUENTE_SMALL      = ("Segoe UI", 9)
FUENTE_MONO       = ("Consolas", 9)     # Para el reporte final


class AplicacionSE(tk.Tk):
    """
    Ventana principal de la aplicación.
    Hereda de tk.Tk directamente para tener control total del root window.
    """

    def __init__(self):
        super().__init__()

        # ── Configuración de ventana ─────────────────────────────────
        self.title("Sistema Experto — NOM STPS")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(bg=COLOR_PRIMARIO)

        # Centrar ventana en pantalla al abrir
        self._centrar_ventana(1100, 700)

        # ── Instanciar motor y explicador ────────────────────────────
        self.motor      = MotorInferencia()
        self.explicador = ModuloExplicacion()

        # ── Cargar preguntas ─────────────────────────────────────────
        from sistema.motor_inferencia import ruta_recurso
        ruta = ruta_recurso("conocimientos/preguntas.json")
        with open(ruta, encoding="utf-8") as f:
            self.preguntas = json.load(f)["preguntas"]

        # Estado de la sesión
        self.indice_pregunta = 0        # Pregunta actual en el flujo
        self.ultima_nom      = None     # Para el botón "¿Por qué?"
        self.noms_log        = []       # Log de NOMs identificadas en tiempo real

        # ── Construir la UI ──────────────────────────────────────────
        self._construir_ui()
        self._mostrar_pregunta()

    # ════════════════════════════════════════════════════════════════
    # Construcción de la interfaz
    # ════════════════════════════════════════════════════════════════

    def _construir_ui(self):
        """Construye todos los widgets de la ventana principal."""

        # ── Encabezado superior ──────────────────────────────────────
        frame_header = tk.Frame(self, bg=COLOR_PRIMARIO, pady=10)
        frame_header.pack(fill="x")

        tk.Label(
            frame_header,
            text="SISTEMA EXPERTO — NORMAS NOM-STPS",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg=COLOR_PRIMARIO,
        ).pack(side="left", padx=20)

        tk.Label(
            frame_header,
            text="Diagnóstico de normas aplicables a tu centro de trabajo",
            font=FUENTE_SMALL,
            fg="#A8C8F0",
            bg=COLOR_PRIMARIO,
        ).pack(side="left", padx=5)

        # Botón reiniciar en el header
        tk.Button(
            frame_header,
            text="↺  Nueva sesión",
            font=FUENTE_SMALL,
            bg="#0057A8",
            fg="white",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._reiniciar_sesion,
        ).pack(side="right", padx=20)

        # ── Separador ────────────────────────────────────────────────
        tk.Frame(self, bg="#001F3F", height=2).pack(fill="x")

        # ── Contenedor principal (dos paneles) ───────────────────────
        frame_main = tk.Frame(self, bg=COLOR_PRIMARIO)
        frame_main.pack(fill="both", expand=True, padx=2, pady=2)

        # Panel izquierdo — diagnóstico
        # Ancho fijo de 420px, el derecho toma el resto
        self.panel_izq = tk.Frame(
            frame_main,
            bg=COLOR_FONDO_IZQ,
            width=420,
        )
        self.panel_izq.pack(side="left", fill="y")
        self.panel_izq.pack_propagate(False)  # Mantener ancho fijo

        # Panel derecho — resultados
        self.panel_der = tk.Frame(frame_main, bg=COLOR_FONDO_DER)
        self.panel_der.pack(side="right", fill="both", expand=True)

        # ── Construir contenido de cada panel ────────────────────────
        self._construir_panel_izquierdo()
        self._construir_panel_derecho()

    def _construir_panel_izquierdo(self):
        """Panel izquierdo: encabezado, área de pregunta, opciones, log de normas."""

        # Título del panel
        tk.Label(
            self.panel_izq,
            text="Diagnóstico",
            font=FUENTE_TITULO,
            fg=COLOR_PRIMARIO,
            bg=COLOR_FONDO_IZQ,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(18, 4))

        # Barra de progreso
        frame_prog = tk.Frame(self.panel_izq, bg=COLOR_FONDO_IZQ)
        frame_prog.pack(fill="x", padx=20, pady=(0, 10))

        self.lbl_progreso = tk.Label(
            frame_prog,
            text="Pregunta 1 de 26",
            font=FUENTE_SMALL,
            fg=COLOR_GRIS,
            bg=COLOR_FONDO_IZQ,
        )
        self.lbl_progreso.pack(anchor="w")

        self.barra_progreso = ttk.Progressbar(
            frame_prog,
            orient="horizontal",
            mode="determinate",
            maximum=len(self.preguntas),
        )
        self.barra_progreso.pack(fill="x", pady=(2, 0))

        # Separador
        tk.Frame(self.panel_izq, bg=COLOR_GRIS_CLARO, height=1).pack(fill="x", padx=20, pady=8)

        # Área de pregunta — frame scrollable para textos largos
        frame_pregunta = tk.Frame(self.panel_izq, bg=COLOR_FONDO_IZQ)
        frame_pregunta.pack(fill="x", padx=20, pady=(0, 10))

        self.lbl_pregunta = tk.Label(
            frame_pregunta,
            text="",
            font=("Segoe UI", 11),
            fg=COLOR_TEXTO,
            bg=COLOR_FONDO_IZQ,
            wraplength=360,      # Wrap automático para preguntas largas
            justify="left",
            anchor="w",
        )
        self.lbl_pregunta.pack(fill="x")

        # Área de opciones — frame contenedor que se reconstruye en cada pregunta
        self.frame_opciones = tk.Frame(self.panel_izq, bg=COLOR_FONDO_IZQ)
        self.frame_opciones.pack(fill="x", padx=20, pady=(5, 0))

        # Variable para radiobuttons
        self.var_seleccion = tk.StringVar(value="")

        # Separador
        tk.Frame(self.panel_izq, bg=COLOR_GRIS_CLARO, height=1).pack(fill="x", padx=20, pady=12)

        # Botón confirmar
        self.btn_confirmar = tk.Button(
            self.panel_izq,
            text="Confirmar →",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
            command=self._confirmar_respuesta,
        )
        self.btn_confirmar.pack(padx=20, pady=(0, 10), anchor="e")

        # Separador
        tk.Frame(self.panel_izq, bg=COLOR_GRIS_CLARO, height=1).pack(fill="x", padx=20, pady=4)

        # Log de normas identificadas en tiempo real
        tk.Label(
            self.panel_izq,
            text="Normas identificadas",
            font=FUENTE_SUBTITULO,
            fg=COLOR_PRIMARIO,
            bg=COLOR_FONDO_IZQ,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(8, 4))

        # ScrolledText para el log — crece hacia abajo
        self.txt_log = scrolledtext.ScrolledText(
            self.panel_izq,
            font=FUENTE_SMALL,
            fg=COLOR_VERDE,
            bg="#F0F8F4",
            relief="flat",
            height=8,
            state="disabled",   # Solo lectura
            wrap="word",
        )
        self.txt_log.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _construir_panel_derecho(self):
        """Panel derecho: estado inicial y área de reporte final."""

        # Encabezado del panel derecho
        frame_der_header = tk.Frame(self.panel_der, bg="#F5F8FF", pady=12)
        frame_der_header.pack(fill="x")

        tk.Label(
            frame_der_header,
            text="Reporte de resultados",
            font=FUENTE_TITULO,
            fg=COLOR_PRIMARIO,
            bg="#F5F8FF",
            anchor="w",
        ).pack(side="left", padx=20)

        # Botones de acción post-diagnóstico (inicialmente ocultos)
        self.frame_botones_reporte = tk.Frame(frame_der_header, bg="#F5F8FF")
        self.frame_botones_reporte.pack(side="right", padx=20)

        tk.Button(
            self.frame_botones_reporte,
            text="¿Por qué?",
            font=FUENTE_SMALL,
            bg=COLOR_SECUNDARIO,
            fg="white",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._mostrar_por_que,
        ).pack(side="left", padx=4)

        tk.Button(
            self.frame_botones_reporte,
            text="¿Cómo?",
            font=FUENTE_SMALL,
            bg=COLOR_SECUNDARIO,
            fg="white",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._mostrar_como,
        ).pack(side="left", padx=4)

        # Ocultar botones hasta que termine el diagnóstico
        self.frame_botones_reporte.pack_forget()

        tk.Frame(self.panel_der, bg=COLOR_GRIS_CLARO, height=1).pack(fill="x")

        # Área principal de resultados — ScrolledText
        self.txt_reporte = scrolledtext.ScrolledText(
            self.panel_der,
            font=FUENTE_MONO,
            fg=COLOR_TEXTO,
            bg=COLOR_FONDO_DER,
            relief="flat",
            padx=20,
            pady=15,
            state="disabled",
            wrap="word",
            spacing1=2,    # Espacio antes de cada línea
            spacing3=2,    # Espacio después de cada línea
        )
        self.txt_reporte.pack(fill="both", expand=True)

        # Configurar tags de color para el texto del reporte
        self.txt_reporte.tag_config("titulo",     foreground=COLOR_PRIMARIO,  font=("Segoe UI", 11, "bold"))
        self.txt_reporte.tag_config("nom",        foreground=COLOR_PRIMARIO,  font=("Segoe UI", 10, "bold"))
        self.txt_reporte.tag_config("categoria",  foreground=COLOR_SECUNDARIO, font=("Segoe UI", 9))
        self.txt_reporte.tag_config("contexto",   foreground=COLOR_GRIS,      font=("Segoe UI", 9, "italic"))
        self.txt_reporte.tag_config("obligacion", foreground=COLOR_TEXTO,     font=("Segoe UI", 9))
        self.txt_reporte.tag_config("verde",      foreground=COLOR_VERDE,     font=("Segoe UI", 9, "bold"))
        self.txt_reporte.tag_config("separador",  foreground=COLOR_GRIS_CLARO)
        self.txt_reporte.tag_config("nota",       foreground=COLOR_GRIS,      font=("Segoe UI", 8, "italic"))

        # Mensaje inicial en el panel derecho
        self._escribir_reporte(
            "Completa el diagnóstico en el panel izquierdo.\n\n"
            "Las normas aplicables a tu centro de trabajo\n"
            "aparecerán aquí al finalizar.",
            tag="contexto"
        )

    # ════════════════════════════════════════════════════════════════
    # Lógica del flujo de diagnóstico
    # ════════════════════════════════════════════════════════════════

    def _mostrar_pregunta(self):
        """Actualiza el panel izquierdo con la pregunta actual."""

        if self.indice_pregunta >= len(self.preguntas):
            # Todas las preguntas respondidas → generar reporte
            self._generar_reporte_final()
            return

        pregunta = self.preguntas[self.indice_pregunta]

        # Actualizar label de progreso y barra
        num = self.indice_pregunta + 1
        total = len(self.preguntas)
        self.lbl_progreso.config(text=f"Pregunta {num} de {total}")
        self.barra_progreso["value"] = self.indice_pregunta

        # Actualizar texto de la pregunta
        self.lbl_pregunta.config(text=pregunta["texto"])

        # Destruir opciones anteriores y reconstruir
        # Por qué destruir y reconstruir en lugar de reconfigurar:
        # El número de opciones varía entre preguntas (2 a 4 opciones).
        # Es más limpio regenerar que animar los radiobuttons existentes.
        for widget in self.frame_opciones.winfo_children():
            widget.destroy()

        self.var_seleccion = tk.StringVar(value="")

        for opcion in pregunta["opciones"]:
            rb = tk.Radiobutton(
                self.frame_opciones,
                text=opcion["etiqueta"],
                value=opcion["valor"],
                variable=self.var_seleccion,
                font=FUENTE_NORMAL,
                fg=COLOR_TEXTO,
                bg=COLOR_FONDO_IZQ,
                activebackground=COLOR_FONDO_IZQ,
                selectcolor="#C8DCFA",   # Azul claro cuando está seleccionado
                anchor="w",
                wraplength=340,
                justify="left",
                cursor="hand2",
            )
            rb.pack(fill="x", pady=3)

    def _confirmar_respuesta(self):
        """
        Procesa la respuesta seleccionada.
        Inserta el hecho en el motor, ejecuta inferencia y avanza.
        """
        valor = self.var_seleccion.get()

        if not valor:
            # El usuario no seleccionó ninguna opción
            messagebox.showwarning(
                "Selección requerida",
                "Por favor selecciona una opción antes de continuar."
            )
            return

        pregunta = self.preguntas[self.indice_pregunta]

        # Insertar hecho en working memory del motor
        self.motor.agregar_hecho(pregunta["id"], valor)

        # Ejecutar el motor — dispara todas las reglas que ahora matchean
        disparadas = self.motor.ejecutar()

        # Actualizar log de normas identificadas en tiempo real
        nuevas = [r for r in disparadas if r["conclusion"].startswith("aplica_")]
        for r in nuevas:
            self._agregar_al_log(r["nom"], r["categoria"])
            self.ultima_nom = r["nom"]

        # Avanzar a la siguiente pregunta
        self.indice_pregunta += 1
        self._mostrar_pregunta()

    # ════════════════════════════════════════════════════════════════
    # Reporte final
    # ════════════════════════════════════════════════════════════════

    def _generar_reporte_final(self):
        """
        Al terminar todas las preguntas, genera el reporte visual en el panel derecho.
        Usa tags de color para distinguir secciones en lugar de texto plano.
        """
        # Completar barra de progreso
        self.barra_progreso["value"] = len(self.preguntas)
        self.lbl_progreso.config(text=f"✓ Diagnóstico completado")
        self.lbl_pregunta.config(text="Diagnóstico finalizado.\nRevisa el reporte en el panel derecho.")

        # Ocultar botón confirmar y opciones
        self.btn_confirmar.pack_forget()
        for widget in self.frame_opciones.winfo_children():
            widget.destroy()

        # Mostrar botones de explicación en panel derecho
        self.frame_botones_reporte.pack(side="right", padx=20)

        # Limpiar área de reporte
        self.txt_reporte.config(state="normal")
        self.txt_reporte.delete("1.0", "end")

        # Obtener NOMs aplicables
        noms = self.motor.obtener_noms_aplicables()
        sub_reglas = [
            p for p in self.motor.traza
            if not p["conclusion"].startswith("aplica_")
        ]

        if not noms:
            self._escribir_reporte("No se identificaron normas aplicables.\n", tag="contexto")
            self.txt_reporte.config(state="disabled")
            return

        # ── Encabezado del reporte ───────────────────────────────────
        self._insertar_reporte("DIAGNÓSTICO COMPLETADO — NORMAS NOM-STPS\n", tag="titulo")
        self._insertar_reporte(
            f"Se identificaron {len(noms)} norma(s) aplicable(s) para tu centro de trabajo.\n\n",
            tag="contexto"
        )

        # ── Una sección por cada NOM ─────────────────────────────────
        for i, paso in enumerate(noms, 1):
            nom        = paso["nom"]
            categoria  = paso["categoria"]
            resumen    = paso["resumen"]
            obligaciones = paso["obligaciones"]

            # Buscar sub-reglas de esta NOM (ej: NOM-035 extendida)
            ext = next(
                (s for s in sub_reglas if s.get("nom") == nom), None
            )

            # Línea separadora
            self._insertar_reporte("─" * 55 + "\n", tag="separador")

            # Nombre y categoría
            self._insertar_reporte(f"{i}. {nom}", tag="nom")
            self._insertar_reporte(f"  [{categoria}]\n\n", tag="categoria")

            # Contexto / resumen
            self._insertar_reporte("Contexto:\n", tag="verde")
            self._insertar_reporte(f"{resumen}\n\n", tag="contexto")

            # Obligaciones del patrón
            self._insertar_reporte("Obligaciones principales del patrón:\n", tag="verde")
            for ob in obligaciones:
                self._insertar_reporte(f"  • {ob}\n", tag="obligacion")

            # Obligaciones extendidas si existen
            if ext:
                self._insertar_reporte(
                    "\nObligaciones adicionales (por número de trabajadores):\n",
                    tag="verde"
                )
                for ob in ext.get("obligaciones", []):
                    self._insertar_reporte(f"  • {ob}\n", tag="obligacion")

            self._insertar_reporte("\n")

        # ── Nota final ───────────────────────────────────────────────
        self._insertar_reporte("─" * 55 + "\n", tag="separador")
        self._insertar_reporte(
            "NOTA: Este diagnóstico es orientativo. Consulta el texto\n"
            "oficial de cada NOM en el DOF o en asinom.stps.gob.mx\n"
            "para verificación legal.\n",
            tag="nota"
        )

        # Volver a solo lectura
        self.txt_reporte.config(state="disabled")

    # ════════════════════════════════════════════════════════════════
    # Comandos de explicación
    # ════════════════════════════════════════════════════════════════

    def _mostrar_por_que(self):
        """Abre ventana emergente con la explicación de la última NOM."""
        if not self.ultima_nom:
            messagebox.showinfo("Sin norma", "Aún no se ha identificado ninguna norma.")
            return
        texto = self.explicador.por_que(self.motor.traza, self.ultima_nom)
        self._ventana_explicacion(f"¿Por qué aplica {self.ultima_nom}?", texto)

    def _mostrar_como(self):
        """Abre ventana emergente con la cadena de razonamiento completa."""
        texto = self.explicador.como(self.motor.traza)
        self._ventana_explicacion("Cadena de razonamiento completa", texto)

    def _ventana_explicacion(self, titulo: str, texto: str):
        """
        Crea una ventana Toplevel para mostrar explicaciones.
        Toplevel es la forma correcta de hacer ventanas secundarias en tkinter
        — no bloquea la ventana principal.
        """
        ventana = tk.Toplevel(self)
        ventana.title(titulo)
        ventana.geometry("620x450")
        ventana.configure(bg=COLOR_FONDO_DER)
        ventana.grab_set()   # Modal — enfoca esta ventana

        # Centrar sobre la ventana principal
        x = self.winfo_x() + 240
        y = self.winfo_y() + 125
        ventana.geometry(f"+{x}+{y}")

        # Encabezado
        tk.Label(
            ventana,
            text=titulo,
            font=FUENTE_SUBTITULO,
            fg=COLOR_PRIMARIO,
            bg=COLOR_FONDO_DER,
        ).pack(fill="x", padx=20, pady=(15, 5))

        tk.Frame(ventana, bg=COLOR_GRIS_CLARO, height=1).pack(fill="x", padx=20)

        # Área de texto scrollable
        txt = scrolledtext.ScrolledText(
            ventana,
            font=FUENTE_MONO,
            fg=COLOR_TEXTO,
            bg="#FAFAFA",
            relief="flat",
            padx=15,
            pady=10,
            wrap="word",
        )
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", texto)
        txt.config(state="disabled")

        # Botón cerrar
        tk.Button(
            ventana,
            text="Cerrar",
            font=FUENTE_SMALL,
            bg=COLOR_PRIMARIO,
            fg="white",
            relief="flat",
            padx=14,
            pady=5,
            cursor="hand2",
            command=ventana.destroy,
        ).pack(pady=(0, 12))

    # ════════════════════════════════════════════════════════════════
    # Utilidades
    # ════════════════════════════════════════════════════════════════

    def _reiniciar_sesion(self):
        """Reinicia el motor y vuelve al estado inicial."""
        if messagebox.askyesno(
            "Nueva sesión",
            "¿Deseas iniciar un nuevo diagnóstico?\nSe perderán los resultados actuales."
        ):
            self.motor.reiniciar()
            self.indice_pregunta = 0
            self.ultima_nom      = None
            self.noms_log        = []

            # Restaurar botón confirmar
            self.btn_confirmar.pack(padx=20, pady=(0, 10), anchor="e")

            # Limpiar log
            self.txt_log.config(state="normal")
            self.txt_log.delete("1.0", "end")
            self.txt_log.config(state="disabled")

            # Limpiar reporte y mostrar mensaje inicial
            self.txt_reporte.config(state="normal")
            self.txt_reporte.delete("1.0", "end")
            self.txt_reporte.config(state="disabled")
            self._escribir_reporte(
                "Completa el diagnóstico en el panel izquierdo.\n\n"
                "Las normas aplicables aparecerán aquí al finalizar.",
                tag="contexto"
            )

            # Ocultar botones de reporte
            self.frame_botones_reporte.pack_forget()

            # Restaurar barra de progreso
            self.barra_progreso["value"] = 0

            # Mostrar primera pregunta
            self._mostrar_pregunta()

    def _agregar_al_log(self, nom: str, categoria: str):
        """Agrega una entrada al log de normas identificadas en tiempo real."""
        self.txt_log.config(state="normal")
        self.txt_log.insert("end", f"✓ {nom}  [{categoria}]\n")
        self.txt_log.see("end")   # Auto-scroll al final
        self.txt_log.config(state="disabled")

    def _insertar_reporte(self, texto: str, tag: str = None):
        """Inserta texto en el área de reporte con un tag de color opcional."""
        if tag:
            self.txt_reporte.insert("end", texto, tag)
        else:
            self.txt_reporte.insert("end", texto)

    def _escribir_reporte(self, texto: str, tag: str = None):
        """Limpia el reporte y escribe texto nuevo."""
        self.txt_reporte.config(state="normal")
        self.txt_reporte.delete("1.0", "end")
        if tag:
            self.txt_reporte.insert("1.0", texto, tag)
        else:
            self.txt_reporte.insert("1.0", texto)
        self.txt_reporte.config(state="disabled")

    def _centrar_ventana(self, ancho: int, alto: int):
        """Centra la ventana en la pantalla al abrir."""
        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto  // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")


# ── Entry point ──────────────────────────────────────────────────────────────

def iniciar_gui():
    """Inicia la aplicación gráfica. Llamado desde main.py."""
    app = AplicacionSE()
    app.mainloop()   # Loop principal de eventos de tkinter


if __name__ == "__main__":
    # Permite correr este archivo directamente durante desarrollo
    iniciar_gui()
