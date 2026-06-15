import json
import sys
from pathlib import Path


def ruta_recurso(ruta_relativa: str) -> Path:
    """
    Resuelve rutas de archivos tanto en desarrollo como dentro de un .exe.

    Cuando PyInstaller genera el .exe, los archivos de datos se extraen
    a una carpeta temporal (sys._MEIPASS). Esta función detecta si estamos
    corriendo como .exe y ajusta la ruta automáticamente.

    Sin esta función, el .exe no encontraría los JSONs y fallaría al arrancar.
    """
    if getattr(sys, "frozen", False):
        # Corriendo como .exe generado por PyInstaller
        base = Path(sys._MEIPASS)
    else:
        # Corriendo normalmente con python main.py
        base = Path(__file__).parent.parent

    return base / ruta_relativa


class MotorInferencia:

    def __init__(self, ruta_reglas: str = None):
        # Usar helper de ruta para compatibilidad con .exe
        if ruta_reglas is None:
            ruta_reglas = ruta_recurso("conocimientos/reglas.json")

        with open(ruta_reglas, encoding="utf-8") as f:
            datos = json.load(f)

        # Lista de dicts — cada dict es una regla con id, condiciones, conclusion, etc.
        # Se filtran las entradas que solo tienen "_seccion" (son separadores visuales)
        self.reglas: list[dict] = [
            r for r in datos["reglas"] if "condiciones" in r
        ]

        # Working memory: dict de hechos conocidos { clave_hecho: valor_hecho }
        # Ejemplo: { "num_trabajadores": "mas_de_100", "usa_maquinaria": "si" }
        self.memoria_trabajo: dict[str, str] = {}

        # Traza: lista ordenada de reglas disparadas durante ejecutar()
        # Cada entrada registra qué regla disparó, con qué hechos, y qué concluyó
        self.traza: list[dict] = []

        # Set de conclusiones activas — lookup O(1) para evitar disparos duplicados
        self.conclusiones: set[str] = set()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def agregar_hecho(self, clave: str, valor: str) -> None:
        """
        Inserta un hecho en la memoria de trabajo.
        Llamado por el chatbot cada vez que el usuario responde una pregunta.
        """
        self.memoria_trabajo[clave] = valor

    def ejecutar(self) -> list[dict]:
        """
        Ejecuta un ciclo de forward chaining sobre todas las reglas.

        Para cada regla no disparada aún, verifica si sus condiciones
        están satisfechas en memoria_trabajo. Si matchea, la dispara.

        Retorna la lista de reglas disparadas en este ciclo.
        Puede llamarse múltiples veces — cada llamada solo dispara
        reglas nuevas cuyas condiciones se cumplan con los hechos actuales.
        """
        disparadas: list[dict] = []

        for regla in self.reglas:
            # Saltar si esta conclusión ya fue derivada (evita duplicados)
            if regla["conclusion"] in self.conclusiones:
                continue

            if self._matchea(regla["condiciones"]):
                self._disparar(regla)
                disparadas.append(regla)

        return disparadas

    def reiniciar(self) -> None:
        """Limpia memoria, traza y conclusiones para iniciar una nueva sesión."""
        self.memoria_trabajo.clear()
        self.traza.clear()
        self.conclusiones.clear()

    def obtener_noms_aplicables(self) -> list[dict]:
        """
        Retorna solo las entradas de la traza que representan NOMs principales.

        Filtra por conclusiones que empiezan con 'aplica_' para separar
        las normas principales de sub-reglas como 'NOM-035_obligaciones_extendidas'.
        """
        return [
            entrada for entrada in self.traza
            if entrada["conclusion"].startswith("aplica_")
        ]

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _matchea(self, condiciones: dict) -> bool:
        """
        Verifica si todas las condiciones de una regla están satisfechas
        en la memoria de trabajo.

        condiciones es un dict { clave_hecho: [lista de valores aceptables] }.
        Una condición vacía {} matchea siempre — regla universal (NOM-001, etc).
        """
        for clave, valores_aceptables in condiciones.items():
            if clave not in self.memoria_trabajo:
                return False
            if self.memoria_trabajo[clave] not in valores_aceptables:
                return False
        return True

    def _disparar(self, regla: dict) -> None:
        """
        Dispara una regla: agrega su conclusión a memoria y registra en traza.
        """
        conclusion = regla["conclusion"]

        self.memoria_trabajo[conclusion] = "verdadero"
        self.conclusiones.add(conclusion)

        self.traza.append({
            "id_regla":              regla["id"],
            "descripcion":           regla["descripcion"],
            "condiciones_matcheadas": {
                k: v for k, v in self.memoria_trabajo.items()
                if not k.startswith("aplica_") and v != "verdadero"
            },
            "conclusion":   conclusion,
            "nom":          regla.get("nom", ""),
            "categoria":    regla.get("categoria", ""),
            "obligaciones": regla.get("obligaciones", []),
            "resumen":      regla.get("resumen", ""),
        })
