import sys
from sistema.motor_inferencia import MotorInferencia   # noqa — verificar imports
from sistema.explicacion import ModuloExplicacion       # noqa


def main():
    # Detectar modo de ejecución por argumento de línea de comandos
    if "--terminal" in sys.argv:
        # Modo terminal — útil para desarrollo y depuración
        from sistema.interface import iniciar
        iniciar()
    else:
        # Modo GUI — modo por defecto para el usuario final
        from interfaz_grafica import iniciar_gui
        iniciar_gui()


if __name__ == "__main__":
    main()
