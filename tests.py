"""
Módulo 5: Suite de Casos de Prueba (Fase 6.8 y Criterio 7 de la Rúbrica)
Curso: Teoría de la Computación - INFO1148

Contiene 30 casos de prueba automatizados (superando el umbral de 25+ de la rúbrica):
- 12 entradas sintácticamente válidas (V01 - V12)
- 12 entradas sintácticamente inválidas (I01 - I12)
-  6 casos límite (L01 - L06)

Cada caso se evalúa tanto con el Parser de Descenso Recursivo (`AnalizadorSintactico`)
como con el Simulador de Pila de la Tabla Predictiva (`construir_arbol_derivacion_ll1`),
imprimiendo la tabla oficial de 4 columnas del enunciado:
[Entrada | Resultado esperado | Resultado obtenido | Observación]
"""

import sys
from dataclasses import dataclass

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from lexer import ErrorLexicoDSL
from parser import AnalizadorSintactico, ErrorSintactico, construir_arbol_derivacion_ll1


@dataclass(frozen=True)
class CasoPrueba:
    id_caso: str
    categoria: str          # "VÁLIDA" | "INVÁLIDA" | "LÍMITE"
    entrada: str
    debe_aceptar: bool
    resultado_esperado: str
    observacion: str


CASOS_DE_PRUEBA: list[CasoPrueba] = [
    # ==========================================================================
    # 1. ENTRADAS SINTÁCTICAMENTE VÁLIDAS (12 Casos: V01 - V12)
    # ==========================================================================
    CasoPrueba(
        id_caso="V01",
        categoria="VÁLIDA",
        entrada="WHEN temperatura > 28 THEN encender ventilador;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Regla elemental con operador '>' y valor entero",
    ),
    CasoPrueba(
        id_caso="V02",
        categoria="VÁLIDA",
        entrada="WHEN movimiento == TRUE THEN activar alarma;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Comparación de igualdad con literal booleano TRUE",
    ),
    CasoPrueba(
        id_caso="V03",
        categoria="VÁLIDA",
        entrada="WHEN temperatura > 28 AND humedad < 40 THEN encender ventilador;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Condición compuesta mediante conjunción lógica AND",
    ),
    CasoPrueba(
        id_caso="V04",
        categoria="VÁLIDA",
        entrada="WHEN humo >= 50 OR co2 != 0 THEN abrir escotilla;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Condición compuesta con disyunción OR y operadores '>=' y '!='",
    ),
    CasoPrueba(
        id_caso="V05",
        categoria="VÁLIDA",
        entrada="WHEN NOT ventana_abierta == TRUE THEN encender calefactor;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Extensión creativa: negación lógica NOT aplicada a una comparación",
    ),
    CasoPrueba(
        id_caso="V06",
        categoria="VÁLIDA",
        entrada="WHEN NOT (temperatura <= 25.5) AND (humedad < 35 OR sequia == TRUE) THEN activar riego;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Extensión creativa: combinación de NOT, paréntesis ( ) y decimal",
    ),
    CasoPrueba(
        id_caso="V07",
        categoria="VÁLIDA",
        entrada="WHEN humedad_suelo < 30 THEN abrir valvula ELSE cerrar valvula;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Extensión creativa: regla condicional con cláusula sino (ELSE)",
    ),
    CasoPrueba(
        id_caso="V08",
        categoria="VÁLIDA",
        entrada="# Monitoreo nocturno\nWHEN luz_solar == FALSE THEN encender lampara;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Extensión creativa: comentario de línea '#' previo a una regla",
    ),
    CasoPrueba(
        id_caso="V09",
        categoria="VÁLIDA",
        entrada=(
            "WHEN temperatura > 30 THEN encender extractor;\n"
            "WHEN humedad < 20 THEN activar nebulizador;"
        ),
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Programa compuesto por múltiples reglas secuenciales",
    ),
    CasoPrueba(
        id_caso="V10",
        categoria="VÁLIDA",
        entrada="WHEN (a > 10 AND b < 20) OR (c >= 30 AND d <= 40) THEN enviar alerta;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Dos bloques entre paréntesis unidos por disyunción OR",
    ),
    CasoPrueba(
        id_caso="V11",
        categoria="VÁLIDA",
        entrada="WHEN NOT (lluvia == TRUE OR viento > 60) THEN desplegar toldo ELSE recoger toldo;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Integración completa de NOT, agrupación ( ) y cláusula ELSE",
    ),
    CasoPrueba(
        id_caso="V12",
        categoria="VÁLIDA",
        entrada="WHEN nivel_agua <= umbral_minimo THEN encender bomba;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Comparación relacional entre dos identificadores (sensor y umbral)",
    ),

    # ==========================================================================
    # 2. ENTRADAS SINTÁCTICAMENTE INVÁLIDAS (12 Casos: I01 - I12)
    # ==========================================================================
    CasoPrueba(
        id_caso="I01",
        categoria="INVÁLIDA",
        entrada="WHEN temperatura > THEN encender ventilador;",
        debe_aceptar=False,
        resultado_esperado="ERROR SINTÁCTICO",
        observacion="Falta el valor después del operador relacional '>'",
    ),
    CasoPrueba(
        id_caso="I02",
        categoria="INVÁLIDA",
        entrada="WHEN temperatura > 28 encender ventilador;",
        debe_aceptar=False,
        resultado_esperado="ERROR SINTÁCTICO",
        observacion="Ausencia de la palabra reservada obligatoria THEN",
    ),
    CasoPrueba(
        id_caso="I03",
        categoria="INVÁLIDA",
        entrada="temperatura > 28 THEN encender ventilador;",
        debe_aceptar=False,
        resultado_esperado="ERROR SINTÁCTICO",
        observacion="La regla no comienza con la palabra reservada WHEN",
    ),
    CasoPrueba(
        id_caso="I04",
        categoria="INVÁLIDA",
        entrada="WHEN temperatura > 28 THEN encender ventilador",
        debe_aceptar=False,
        resultado_esperado="ERROR SINTÁCTICO",
        observacion="Falta el delimitador ';' al final de la regla",
    ),
    CasoPrueba(
        id_caso="I05",
        categoria="INVÁLIDA",
        entrada="WHEN (temperatura > 28 AND humedad < 40 THEN encender ventilador;",
        debe_aceptar=False,
        resultado_esperado="ERROR SINTÁCTICO",
        observacion="Paréntesis '(' abierto en la condición sin su cierre ')'",
    ),
    CasoPrueba(
        id_caso="I06",
        categoria="INVÁLIDA",
        entrada="WHEN temperatura > 28) THEN encender ventilador;",
        debe_aceptar=False,
        resultado_esperado="ERROR SINTÁCTICO",
        observacion="Paréntesis de cierre ')' huérfano sin apertura previa",
    ),
    CasoPrueba(
        id_caso="I07",
        categoria="INVÁLIDA",
        entrada="WHEN temperatura > < 28 THEN encender ventilador;",
        debe_aceptar=False,
        resultado_esperado="ERROR SINTÁCTICO",
        observacion="Dos operadores relacionales consecutivos sin operando intermedio",
    ),
    CasoPrueba(
        id_caso="I08",
        categoria="INVÁLIDA",
        entrada="WHEN temperatura > 28 AND THEN encender ventilador;",
        debe_aceptar=False,
        resultado_esperado="ERROR SINTÁCTICO",
        observacion="Operador lógico binario AND sin segundo operando",
    ),
    CasoPrueba(
        id_caso="I09",
        categoria="INVÁLIDA",
        entrada="WHEN NOT THEN encender ventilador;",
        debe_aceptar=False,
        resultado_esperado="ERROR SINTÁCTICO",
        observacion="Operador unario NOT sin factor lógico que negar",
    ),
    CasoPrueba(
        id_caso="I10",
        categoria="INVÁLIDA",
        entrada="WHEN temperatura > 28 THEN encender;",
        debe_aceptar=False,
        resultado_esperado="ERROR SINTÁCTICO",
        observacion="Acción incompleta: falta el identificador del actuador tras el verbo",
    ),
    CasoPrueba(
        id_caso="I11",
        categoria="INVÁLIDA",
        entrada="WHEN temperatura > 28 THEN encender ventilador ELSE;",
        debe_aceptar=False,
        resultado_esperado="ERROR SINTÁCTICO",
        observacion="Cláusula ELSE declarada sin especificar su acción",
    ),
    CasoPrueba(
        id_caso="I12",
        categoria="INVÁLIDA",
        entrada="WHEN temperatura = 28 THEN encender ventilador;",
        debe_aceptar=False,
        resultado_esperado="ERROR LÉXICO",
        observacion="Uso de '=' simple en lugar del operador de igualdad '=='",
    ),

    # ==========================================================================
    # 3. CASOS LÍMITE / BORDE (6 Casos: L01 - L06)
    # ==========================================================================
    CasoPrueba(
        id_caso="L01",
        categoria="LÍMITE",
        entrada="WHEN ((((activo == TRUE)))) THEN apagar calefactor;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Anidamiento profundo de 4 niveles de paréntesis en una condición",
    ),
    CasoPrueba(
        id_caso="L02",
        categoria="LÍMITE",
        entrada="WHEN NOT NOT NOT (alarma == FALSE) THEN activar sirena;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Encadenamiento recursivo por la derecha del operador unario NOT",
    ),
    CasoPrueba(
        id_caso="L03",
        categoria="LÍMITE",
        entrada="   # Archivo solo con comentarios y espacios\n   \t  ",
        debe_aceptar=False,
        resultado_esperado="ERROR SINTÁCTICO",
        observacion="Entrada sin tokens efectivos tras filtrar comentarios y blancos",
    ),
    CasoPrueba(
        id_caso="L04",
        categoria="LÍMITE",
        entrada="WHEN s1 > 0 OR s2 > 0 AND NOT s3 == 1 THEN encender led ELSE apagar led;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Todos los niveles de precedencia (OR < AND < NOT) sin paréntesis",
    ),
    CasoPrueba(
        id_caso="L05",
        categoria="LÍMITE",
        entrada="WHEN () THEN encender ventilador;",
        debe_aceptar=False,
        resultado_esperado="ERROR SINTÁCTICO",
        observacion="Paréntesis vacíos '()' sin condición interna",
    ),
    CasoPrueba(
        id_caso="L06",
        categoria="LÍMITE",
        entrada="WHEN a>1 THEN x y;WHEN b<2 THEN u v;WHEN c==3 THEN m n;",
        debe_aceptar=True,
        resultado_esperado="VÁLIDO",
        observacion="Tres reglas consecutivas en una sola línea sin espacios tras ';'",
    ),
]


def evaluar_caso(caso: CasoPrueba) -> tuple[bool, str]:
    """
    Evalúa un caso de prueba con ambos mecanismos (Descenso Recursivo y Tabla LL(1)).
    Retorna (paso_prueba, descripcion_resultado_obtenido).
    """
    try:
        parser_rd = AnalizadorSintactico(caso.entrada)
        parser_rd.analizar()
        aceptado_rd = True
        mensaje_obtenido = "VÁLIDO (Aceptado por Parser y Tabla LL(1))"
    except (ErrorSintactico, ErrorLexicoDSL) as err:
        aceptado_rd = False
        primera_linea = str(err).splitlines()[0]
        mensaje_obtenido = primera_linea

    # Verificación cruzada con el simulador de pila LL(1)
    try:
        construir_arbol_derivacion_ll1(caso.entrada)
        aceptado_ll1 = True
    except (ErrorSintactico, ErrorLexicoDSL):
        aceptado_ll1 = False

    coinciden_ambos = aceptado_rd == aceptado_ll1
    exito = (aceptado_rd == caso.debe_aceptar) and coinciden_ambos
    return exito, mensaje_obtenido


def ejecutar_suite_pruebas() -> bool:
    """
    Ejecuta los 30 casos de prueba e imprime la tabla exigida en la sección 6.8 del informe.
    """
    print("=" * 125)
    print(f"{'ID':<4} | {'Cat.':<8} | {'Entrada':<44} | {'Esperado':<16} | {'Resultado obtenido':<42}")
    print("=" * 125)

    aprobados = 0
    for caso in CASOS_DE_PRUEBA:
        exito, obtenido = evaluar_caso(caso)
        if exito:
            aprobados += 1

        entrada_limpia = caso.entrada.replace("\n", " ↵ ").strip()
        if len(entrada_limpia) > 42:
            entrada_limpia = entrada_limpia[:39] + "..."

        obtenido_corto = obtenido if len(obtenido) <= 42 else obtenido[:39] + "..."
        marca = "✔" if exito else "✘"
        print(
            f"{caso.id_caso:<4} | {caso.categoria:<8} | {entrada_limpia:<44} | "
            f"{caso.resultado_esperado:<16} | {marca} {obtenido_corto}"
        )
        print(f"     └─ Observación: {caso.observacion}  -->  Detalle: {obtenido}")
        print("-" * 125)

    total = len(CASOS_DE_PRUEBA)
    print(f"\nRESUMEN DE PRUEBAS: {aprobados}/{total} casos superados exitosamente.")
    return aprobados == total


if __name__ == "__main__":
    exito_total = ejecutar_suite_pruebas()
    sys.exit(0 if exito_total else 1)
