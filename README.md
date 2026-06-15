# Consultor de Normas Oficiales Mexicanas (NOM) 
### Sistema Experto basado en Reglas para el Diagnóstico de Cumplimiento de la STPS

Este sistema experto automatiza el diagnóstico normativo en materia de seguridad, salud y organización en centros de trabajo mexicanos. Evaluando las características específicas de una empresa (número de trabajadores, actividades, maquinaria, materiales expuestos), el motor infiere de manera deductiva qué **Normas Oficiales Mexicanas (NOM)** de la STPS aplican obligatoriamente, proporcionando además un desglose detallado de obligaciones y un módulo de transparencia explicativa.


## Características Principales

- **Doble Agente de Interfaz (GUI / CLI):**
  - **Interfaz Gráfica (Por defecto):** Diseñada en Tkinter utilizando la paleta de colores institucional de la STPS (Azul Federal). Cuenta con paneles interactivos para responder cuestionarios guiados, una bitácora en vivo y un panel derecho con reportes listos en color verde institucional.
  - **Interfaz de Consola (CLI Chatbot):** Un chatbot interactivo que permite realizar diagnósticos y ejecutar comandos lógicos mediante procesamiento básico de lenguaje natural.
- **Motor de Inferencia Forward Chaining:** Algoritmo implementado desde cero que procesa reglas lógicas complejas asociando hechos de la memoria de trabajo temporal con condiciones normativas especificadas en la base de conocimientos.
- **Módulo de Transparencia ("Caja Blanca"):** El sistema rompe el paradigma de la "caja negra". Almacena un registro histórico (*Traza*) permitiendo al usuario auditar al sistema con preguntas como `por qué NOM-035` o `cómo`.
- **Arquitectura Ultra-Portable:** Escrito exclusivamente con librerías estándar de Python (`tkinter`, `json`, `pathlib`, `sys`), garantizando ejecución en cualquier entorno sin dependencias pesadas de terceros.

---

## Estructura del Proyecto

```text
proyecto_nom/
├── main.py                # Punto de entrada maestro (orquesta los agentes)
├── interfaz_grafica.py    # Interfaz Gráfica de Usuario (GUI en Tkinter)
├── sistema/
│   ├── interface.py       # Interfaz de Línea de Comandos (CLI Chatbot)
│   ├── motor_inferencia.py# Núcleo del Forward Chaining y gestión de recursos
│   └── explicacion.py     # Motor de transparencia y justificación de traza
└── conocimientos/
    ├── preguntas.json     # Declaración de variables y estructura del cuestionario
    └── reglas.json        # Base de Conocimiento (Reglas de producción de las NOM)
```

# Requisitos e Instalación
Python 3.9 o superior instalado en el equipo.

Descargar o clonar la estructura de carpetas manteniendo los archivos JSON dentro de la carpeta conocimientos/.

El sistema corre nativamente sin necesidad de entornos virtuales o comandos pip install complejos para su tiempo de ejecución básico.

# Modos de Uso

1. Ejecutar Interfaz Gráfica (Modo por Defecto)

  Para arrancar el consultor visual con diseño interactivo, ejecuta:

  ```bash
  python main.py
  ```

2. Ejecutar Modo Consola / Terminal

  Para iniciar el chatbot interactivo y auditar de forma directa el motor lógico, añade el flag `--terminal`:

  ```bash
  python main.py --terminal
  ```

  Comandos de auditoría en la consola:

  - `cómo`: Muestra la cadena de ejecución cronológica detallando qué reglas se dispararon y en qué orden.
  - `por qué [NOM]` (ejemplo: `por qué NOM-002`): Muestra exactamente qué hechos introducidos por ti cumplieron las premisas que obligaron al sistema a dictaminar la aplicación de dicha norma.
  - `reiniciar`: Limpia la memoria de trabajo para diagnosticar un nuevo establecimiento.
  - `salir`: Cierra el programa de forma segura.

## Compilación a Ejecutable (.exe)
El código del motor de inferencia incluye soporte dinámico mediante la función ruta_recurso() para resolver rutas temporales de PyInstaller (sys._MEIPASS). Puedes empaquetar todo el sistema en un único ejecutable autónomo para Windows/Linux sin consola visible corriendo:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --add-data "conocimientos;conocimientos" main.py
```

## Base de Conocimiento (JSON)
La inteligencia del sistema se puede expandir o modificar editando directamente los archivos de la carpeta conocimientos/:

preguntas.json: Define el orden de las preguntas, identificadores de variables y tipos de respuestas aceptadas.

reglas.json: Almacena las reglas de producción en formato estructurado:

```json
{
  "id": "R-SEG-02",
  "descripcion": "NOM-002 aplica cuando hay riesgo de incendio",
  "condiciones": {
    "riesgo_incendio": ["si"]
  },
  "conclusion": "aplica_NOM-002",
  "nom": "NOM-002-STPS-2010",
  "categoria": "Seguridad"
}
```

# Descargo de Responsabilidad Legal
Los dictámenes y reportes generados por este sistema experto son de carácter estrictamente orientativo y educativo. No sustituyen una inspección o dictamen formal de la STPS. Para validaciones legales definitivas, consulte el texto vigente de las NOM en el Diario Oficial de la Federación (DOF) o la plataforma oficial asinom.stps.gob.mx.
