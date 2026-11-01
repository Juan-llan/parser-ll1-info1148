"""
Punto de Entrada Principal (CLI y Demostración Completa)
Curso: Teoría de la Computación - INFO1148
Proyecto: Diseño e implementación de un analizador sintáctico (DSL Monitoreo Ambiental IoT)

Modos de uso:
  python main.py                              # Ejecuta demostración completa del proyecto
  python main.py -c "WHEN temp > 28 THEN ..." # Analiza una sentencia directamente
  python main.py -f ejemplos/reglas_iot.txt   # Analiza un archivo de reglas IoT
  python main.py --pruebas                    # Ejecuta los 30 casos de prueba
  python main.py --dot arbol_ast.dot          # Exporta el AST a formato Graphviz (.dot)
"""

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from lexer import ErrorLexicoDSL, escanear_tokens
from grammar import mostrar_first_follow, mostrar_gramatica, mostrar_tabla_ll1
from parser import AnalizadorSintactico, ErrorSintactico, construir_arbol_derivacion_ll1
from tests import ejecutar_suite_pruebas


def analizar_codigo(
    codigo: str,
    mostrar_tokens: bool = True,
    mostrar_derivacion: bool = False,
    mostrar_traza: bool = False,
    ruta_dot: str | None = None,
) -> bool:
    """Analiza una cadena de entrada, muestra su AST y reporta errores si existen."""
    try:
        if mostrar_tokens:
            tokens = escanear_tokens(codigo, incluir_eof=True)
            print("\n--- [A] Tokens Reconocidos por el Analizador Léxico ---")
            for t in tokens:
                print(f"  ({t.tipo:<10}, {t.lexema!r:<16})  [línea {t.linea}, col {t.columna}]")

        parser = AnalizadorSintactico(codigo)
        arbol_ast = parser.analizar()

        print("\n✔ ENTRADA SINTÁCTICAMENTE VÁLIDA")
        print("\n--- [B] Árbol Sintáctico Abstracto (AST) ---")
        print(arbol_ast.mostrar_ast())

        if mostrar_derivacion or mostrar_traza:
            arbol_deriv, traza = construir_arbol_derivacion_ll1(codigo, registrar_traza=mostrar_traza)
            if mostrar_derivacion:
                print("\n--- [C] Árbol de Derivación Concreto (Tabla LL(1)) ---")
                print(arbol_deriv.imprimir_jerarquico())
            if mostrar_traza:
                print("\n--- [D] Traza de la Pila Predictiva LL(1) ---")
                print(f"{'PASO':<5} | {'PILA (Tope a la izq.)':<42} | {'ACCIÓN / PRODUCCIÓN'}")
                print("-" * 95)
                for idx, (pila_str, _, accion_str) in enumerate(traza, start=1):
                    pila_corta = pila_str if len(pila_str) <= 42 else pila_str[:39] + "..."
                    print(f"{idx:<5} | {pila_corta:<42} | {accion_str}")

        if ruta_dot:
            contenido_dot = arbol_ast.como_arbol_visual().exportar_graphviz_dot()
            Path(ruta_dot).write_text(contenido_dot, encoding="utf-8")
            print(f"\n[Graphviz] Archivo DOT exportado exitosamente en: {ruta_dot}")

        return True

    except (ErrorLexicoDSL, ErrorSintactico) as err:
        print("\n✘ ENTRADA RECHAZADA:")
        print(err)
        return False


def ejecutar_demostracion_completa() -> None:
    """Recorre todas las fases exigidas en el enunciado del proyecto."""
    print("=" * 85)
    print("  PROYECTO INFO1148: ANALIZADOR SINTÁCTICO LL(1) - DSL MONITOREO AMBIENTAL IoT")
    print("=" * 85)

    # 1. Gramática, FIRST/FOLLOW y Tabla LL(1)
    mostrar_gramatica()
    mostrar_first_follow()
    mostrar_tabla_ll1()

    # 2. Ejemplo válido con extensiones creativas (# comentario, NOT, paréntesis y ELSE)
    ejemplo_valido = (
        "# Control automatizado de clima y ventilación en invernadero\n"
        "WHEN NOT (temperatura <= 28.5) AND (humedad < 40 OR co2 >= 800) "
        "THEN encender ventilador ELSE apagar ventilador;"
    )
    print("\n" + "=" * 85)
    print("  DEMOSTRACIÓN 1: ANÁLISIS DE SENTENCIA VÁLIDA Y CONSTRUCCIÓN DEL AST")
    print("=" * 85)
    print(f"Código de entrada:\n{ejemplo_valido}")
    analizar_codigo(ejemplo_valido, mostrar_tokens=True, mostrar_derivacion=False, mostrar_traza=True)

    # 3. Demostración de mensajes de error sintáctico localizados (Fase 6.7)
    print("\n" + "=" * 85)
    print("  DEMOSTRACIÓN 2: DETECCIÓN Y DIAGNÓSTICO DE ERRORES SINTÁCTICOS (Fase 6.7)")
    print("=" * 85)
    ejemplos_erroneos = [
        "WHEN temperatura > THEN encender ventilador;",
        "WHEN temperatura > 28 encender ventilador;",
        "WHEN (temperatura > 28 AND humedad < 40 THEN encender ventilador;",
    ]
    for codigo_err in ejemplos_erroneos:
        print(f"\nEntrada de prueba inválida: {codigo_err}")
        analizar_codigo(codigo_err, mostrar_tokens=False)


def main() -> None:
    arg_parser = argparse.ArgumentParser(
        description="Analizador Sintáctico Predictivo LL(1) para DSL de Monitoreo Ambiental IoT"
    )
    arg_parser.add_argument("-c", "--codigo", type=str, help="Cadena de código DSL a analizar")
    arg_parser.add_argument("-f", "--archivo", type=str, help="Ruta de un archivo con reglas DSL")
    arg_parser.add_argument("--pruebas", action="store_true", help="Ejecuta la suite de 30 casos de prueba")
    arg_parser.add_argument("--gramatica", action="store_true", help="Muestra la GLC, FIRST/FOLLOW y Tabla LL(1)")
    arg_parser.add_argument("--derivacion", action="store_true", help="Muestra también el árbol de derivación LL(1)")
    arg_parser.add_argument("--traza", action="store_true", help="Muestra la traza paso a paso de la pila LL(1)")
    arg_parser.add_argument("--dot", type=str, help="Exporta el AST a un archivo Graphviz (.dot)")

    args = arg_parser.parse_args()

    if args.gramatica:
        mostrar_gramatica()
        mostrar_first_follow()
        mostrar_tabla_ll1()
        return

    if args.pruebas:
        ejecutar_suite_pruebas()
        return

    if args.archivo:
        ruta = Path(args.archivo)
        if not ruta.is_file():
            print(f"Error: No se encontró el archivo '{args.archivo}'.")
            sys.exit(1)
        contenido = ruta.read_text(encoding="utf-8")
        print(f"=== Analizando archivo: {ruta} ===")
        exito = analizar_codigo(
            contenido,
            mostrar_tokens=True,
            mostrar_derivacion=args.derivacion,
            mostrar_traza=args.traza,
            ruta_dot=args.dot,
        )
        sys.exit(0 if exito else 1)

    if args.codigo is not None:
        exito = analizar_codigo(
            args.codigo,
            mostrar_tokens=True,
            mostrar_derivacion=args.derivacion,
            mostrar_traza=args.traza,
            ruta_dot=args.dot,
        )
        sys.exit(0 if exito else 1)

    # Si no se pasan argumentos, ejecuta la demostración integral
    ejecutar_demostracion_completa()


if __name__ == "__main__":
    main()
