class ModuloExplicacion:

    def por_que(self, traza: list[dict], nom: str) -> str:
        """
        Explica por qué una NOM específica fue identificada en esta sesión.

        Busca en la traza las entradas cuyo campo 'nom' coincida con el
        argumento y muestra las condiciones que activaron esa regla.
        """
        # Filtrar entradas de la traza que correspondan a la NOM solicitada
        relevantes = [paso for paso in traza if paso.get("nom") == nom]

        if not relevantes:
            return f"\n  La norma {nom} no fue identificada en esta sesión.\n"

        lineas = [f"\n  ¿Por qué aplica {nom}?", "  " + "─" * 50]

        for paso in relevantes:
            lineas.append(f"  Regla [{paso['id_regla']}]: {paso['descripcion']}")

            # Mostrar los hechos que activaron la regla (sin conclusiones intermedias)
            hechos = paso.get("condiciones_matcheadas", {})
            if hechos:
                lineas.append("  Hechos que activaron esta regla:")
                for clave, valor in hechos.items():
                    lineas.append(f"    • {clave} = {valor}")
            else:
                # Regla universal — condiciones vacías
                lineas.append("  → Regla universal: aplica a todos los centros de trabajo.")

        return "\n".join(lineas)

    def como(self, traza: list[dict]) -> str:
        """
        Muestra la cadena completa de razonamiento paso a paso.

        Útil para auditar qué reglas se dispararon, en qué orden,
        y qué conclusión derivó cada una.
        """
        if not traza:
            return "\n  No se han disparado reglas aún.\n"

        lineas = ["\n  Cadena de razonamiento completa:", "  " + "─" * 50]

        for i, paso in enumerate(traza, 1):
            lineas.append(f"  Paso {i:02d} [{paso['id_regla']}]")
            lineas.append(f"         {paso['descripcion']}")
            lineas.append(f"         → Conclusión: {paso['conclusion']}")
            lineas.append("")

        return "\n".join(lineas)

    def resumen_final(self, traza: list[dict]) -> str:
        """
        Genera el reporte final estructurado con todas las NOMs aplicables.

        Para cada NOM incluye:
          - Nombre y categoría
          - Resumen de contexto (a qué aplica, por qué importa)
          - Lista de obligaciones principales del patrón

        El resumen de contexto es la 'verificación final' que permite
        al usuario confirmar que la norma efectivamente aplica a su situación
        antes de revisar las obligaciones.

        Filtra solo conclusiones 'aplica_*' para excluir sub-reglas como
        'NOM-035_obligaciones_extendidas' del conteo principal.
        """
        # Separar NOMs principales de sub-reglas
        noms_principales = [
            paso for paso in traza
            if paso["conclusion"].startswith("aplica_")
        ]

        # Sub-reglas con obligaciones adicionales (ej: NOM-035 extendida)
        sub_reglas = [
            paso for paso in traza
            if not paso["conclusion"].startswith("aplica_")
        ]

        if not noms_principales:
            return (
                "\n" + "═" * 62 + "\n"
                "  ⚠  No se identificaron normas aplicables.\n"
                "  Verifica que hayas respondido todas las preguntas.\n"
                + "═" * 62
            )

        lineas = [
            "\n" + "═" * 62,
            "  DIAGNÓSTICO COMPLETADO — NORMAS NOM-STPS APLICABLES",
            "═" * 62,
            f"  Se identificaron {len(noms_principales)} norma(s) aplicable(s):\n",
        ]

        for i, paso in enumerate(noms_principales, 1):
            nom       = paso["nom"]
            categoria = paso["categoria"]
            obligaciones = paso["obligaciones"]
            contexto  = paso["resumen"]

            lineas.append("─" * 62)
            lineas.append(f"  {i}. {nom}  [{categoria}]")
            lineas.append("")

            # Contexto / resumen — permite al usuario verificar que la norma aplica
            lineas.append("  Contexto:")
            lineas += self._wrap_texto(contexto, ancho=56, sangria="    ")
            lineas.append("")

            # Buscar si hay obligaciones extendidas para esta NOM
            ext = next(
                (s for s in sub_reglas if s.get("nom") == nom), None
            )

            lineas.append("  Obligaciones principales del patrón:")
            for ob in obligaciones:
                lineas += self._wrap_texto(f"• {ob}", ancho=54, sangria="    ")

            # Agregar obligaciones extendidas si existen
            if ext:
                lineas.append("")
                lineas.append("  Obligaciones adicionales (por número de trabajadores):")
                for ob in ext.get("obligaciones", []):
                    lineas += self._wrap_texto(f"• {ob}", ancho=54, sangria="    ")

            lineas.append("")

        lineas.append("═" * 62)
        lineas.append(
            "  NOTA: Este diagnóstico es orientativo. Consulta el\n"
            "  texto oficial de cada NOM en el DOF o en:\n"
            "  asinom.stps.gob.mx para verificación legal."
        )
        lineas.append("═" * 62)

        return "\n".join(lineas)

    # ------------------------------------------------------------------
    # Helper privado
    # ------------------------------------------------------------------

    def _wrap_texto(self, texto: str, ancho: int, sangria: str) -> list[str]:
        """
        Divide un texto largo en líneas de máximo 'ancho' caracteres.
        Agrega 'sangria' al inicio de cada línea.
        Retorna lista de strings para agregar a lineas[].
        """
        palabras = texto.split()
        lineas = []
        buffer = sangria

        for palabra in palabras:
            # Si agregar la palabra excede el ancho, guardar línea y empezar nueva
            if len(buffer) + len(palabra) + 1 > ancho + len(sangria):
                lineas.append(buffer.rstrip())
                buffer = sangria + palabra
            else:
                buffer += (" " if buffer.strip() else "") + palabra

        if buffer.strip():
            lineas.append(buffer.rstrip())

        return lineas
