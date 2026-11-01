"""
Módulo 4: Analizador Sintáctico Predictivo LL(1) y Manejo de Errores (Fases 6.5, 6.7 y 6.9)
Curso: Teoría de la Computación - INFO1148

Implementa:
1. `ErrorSintactico`: Excepción enriquecida con posición exacta (línea, columna, índice)
   y visualización contextual del fragmento con puntero `^`.
2. `AnalizadorSintactico`: Parser predictivo por descenso recursivo LL(1) con correspondencia
   directa 1 a 1 con los 12 no terminales y 21 producciones de `grammar.py`.
3. `construir_arbol_derivacion_ll1`: Simuladora de pila dirigida por `TABLA_LL1` que construye
   el Árbol de Derivación Concreto y permite verificar la equivalencia entre la tabla y el parser.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from lexer import MARCA_EOF, TokenLexico, escanear_tokens
from grammar import (
    EPSILON,
    FIRST,
    FOLLOW,
    GRAMATICA_SISTEMA,
    SIMBOLO_INICIAL,
    TABLA_LL1,
)
from ast_nodes import (
    AccionActuadorAST,
    ComparacionSensorAST,
    NegacionLogicaAST,
    NodoAST,
    NodoArbol,
    OperacionLogicaAST,
    ProgramaAST,
    ReglaAutomatizacionAST,
    ValorSensorAST,
)

DESCRIPCION_TOKENS: dict[str, str] = {
    "WHEN":       "la palabra reservada 'WHEN'",
    "THEN":       "la palabra reservada 'THEN'",
    "ELSE":       "la palabra reservada 'ELSE'",
    "AND":        "el operador lógico 'AND'",
    "OR":         "el operador lógico 'OR'",
    "NOT":        "el operador de negación 'NOT'",
    "TRUE":       "el booleano 'TRUE'",
    "FALSE":      "el booleano 'FALSE'",
    "ID":         "un identificador (sensor, variable o actuador)",
    "NUM":        "un valor numérico",
    "OP_REL":     "un operador relacional (>, <, >=, <=, ==, !=)",
    "PARENT_IZQ": "el paréntesis de apertura '('",
    "PARENT_DER": "el paréntesis de cierre ')'",
    "PUNTO_COMA": "el delimitador punto y coma ';'",
    MARCA_EOF:    "el final de la entrada",
}


def formatear_token_encontrado(token: TokenLexico) -> str:
    """Devuelve una descripción legible del token actual para mensajes de error."""
    if token.tipo == MARCA_EOF:
        return "el final de la entrada"
    if token.tipo in ("WHEN", "THEN", "ELSE", "AND", "OR", "NOT", "TRUE", "FALSE"):
        return f"la palabra reservada '{token.lexema.upper()}'"
    if token.tipo == "ID":
        return f"el identificador '{token.lexema}'"
    if token.tipo == "NUM":
        return f"el número '{token.lexema}'"
    if token.tipo == "OP_REL":
        return f"el operador relacional '{token.lexema}'"
    return f"el símbolo '{token.lexema}'"


class ErrorSintactico(SyntaxError):
    """
    Excepción para errores sintácticos localizados (Fase 6.7).
    Entrega mensajes claros, contextuales y acompañados de un marcador visual `^`.
    """

    def __init__(
        self,
        detalle: str,
        token: TokenLexico | None = None,
        codigo_fuente: str = "",
    ):
        self.detalle = detalle
        self.token = token
        self.codigo_fuente = codigo_fuente
        self.linea = token.linea if token else 1
        self.columna = token.columna if token else 1
        self.posicion = token.indice if token else 0
        super().__init__(self.formatear_mensaje())

    def formatear_mensaje(self) -> str:
        if self.token is not None:
            cabecera = (
                f"Error sintáctico (línea {self.linea}, columna {self.columna}, "
                f"posición {self.posicion}): {self.detalle}"
            )
        else:
            cabecera = f"Error sintáctico: {self.detalle}"

        if self.codigo_fuente:
            renglones = self.codigo_fuente.splitlines()
            if 1 <= self.linea <= len(renglones):
                linea_texto = renglones[self.linea - 1]
                puntero = " " * max(0, self.columna - 1) + "^"
                return f"{cabecera}\n  {self.linea:>3} | {linea_texto}\n      | {puntero}"
        return cabecera


class AnalizadorSintactico:
    """
    Analizador sintáctico predictivo por Descenso Recursivo LL(1).
    Cada uno de los 12 no terminales de la gramática en `grammar.py` cuenta con
    su propio método `parse_<no_terminal>`, manteniendo trazabilidad exacta
    entre las 21 producciones formales y la implementación.
    """

    def __init__(self, entrada: str | list[TokenLexico] | list[tuple[str, str]]):
        if isinstance(entrada, str):
            self.codigo_fuente = entrada
            self.tokens = escanear_tokens(entrada, incluir_eof=True)
        elif entrada and isinstance(entrada[0], TokenLexico):
            self.codigo_fuente = ""
            lista = list(entrada)  # type: ignore[arg-type]
            if lista[-1].tipo != MARCA_EOF:
                ultimo = lista[-1]
                lista.append(TokenLexico(MARCA_EOF, MARCA_EOF, ultimo.linea, ultimo.columna + len(ultimo.lexema), ultimo.indice + len(ultimo.lexema)))
            self.tokens = lista
        else:
            # Soporte para lista de tuplas [(TIPO, lexema), ...] del notebook base
            self.codigo_fuente = ""
            convertidos: list[TokenLexico] = []
            offset = 0
            for idx, par in enumerate(entrada):  # type: ignore[arg-type]
                tipo, lex = par
                convertidos.append(TokenLexico(tipo, lex, 1, offset + 1, offset))
                offset += len(lex) + 1
            convertidos.append(TokenLexico(MARCA_EOF, MARCA_EOF, 1, offset + 1, offset))
            self.tokens = convertidos

        self.cursor = 0
        self.pila_parentesis: list[TokenLexico] = []

    def token_actual(self) -> TokenLexico:
        """Retorna el token de preanálisis (lookahead) actual."""
        return self.tokens[self.cursor]

    def avanzar(self) -> TokenLexico:
        """Consume el token actual y avanza el cursor al siguiente token."""
        actual = self.tokens[self.cursor]
        if actual.tipo != MARCA_EOF:
            self.cursor += 1
        return actual

    def lanzar_error(self, mensaje: str, token_referencia: TokenLexico | None = None) -> None:
        tok = token_referencia or self.token_actual()
        raise ErrorSintactico(mensaje, tok, self.codigo_fuente)

    def consumir(self, tipo_esperado: str, explicacion_contexto: str = "") -> TokenLexico:
        """
        Verifica que el token actual sea `tipo_esperado`. Si no coincide,
        emite un `ErrorSintactico` con un mensaje descriptivo y localizado.
        """
        actual = self.token_actual()
        if actual.tipo != tipo_esperado:
            nombre_esperado = DESCRIPCION_TOKENS.get(tipo_esperado, f"'{tipo_esperado}'")
            ctx = f" {explicacion_contexto}" if explicacion_contexto else ""
            self.lanzar_error(
                f"se esperaba {nombre_esperado}{ctx}, pero se encontró {formatear_token_encontrado(actual)}."
            )
        return self.avanzar()

    # ==========================================================================
    # PUNTO DE ENTRADA DEL PARSER
    # ==========================================================================

    def analizar(self) -> ProgramaAST:
        """Ejecuta el análisis sintáctico completo y devuelve la raíz del AST (`ProgramaAST`)."""
        if self.token_actual().tipo == MARCA_EOF:
            self.lanzar_error(
                "la entrada está vacía; se esperaba al menos una regla iniciada con la palabra reservada WHEN."
            )
        arbol_ast = self.parse_programa()
        if self.token_actual().tipo != MARCA_EOF:
            sobrante = self.token_actual()
            self.lanzar_error(
                f"símbolo inesperado {formatear_token_encontrado(sobrante)} cerca de la posición {sobrante.indice}."
            )
        return arbol_ast

    # ==========================================================================
    # MÉTODOS DE DESCENSO RECURSIVO (12 No Terminales / 21 Producciones)
    # ==========================================================================

    def parse_programa(self) -> ProgramaAST:
        """
        Producción (1): <programa> -> <regla> <resto_reglas>
        Conjunto FIRST(<programa>) = { WHEN }
        """
        actual = self.token_actual()
        if actual.tipo not in FIRST["<programa>"]:
            self.lanzar_error(
                f"se esperaba la palabra reservada WHEN al inicio del programa, "
                f"pero se encontró {formatear_token_encontrado(actual)}."
            )
        primera_regla = self.parse_regla()
        reglas_adicionales = self.parse_resto_reglas()
        return ProgramaAST(reglas=[primera_regla] + reglas_adicionales)

    def parse_resto_reglas(self) -> list[ReglaAutomatizacionAST]:
        """
        Producción (2): <resto_reglas> -> <regla> <resto_reglas>   (si lookahead ∈ { WHEN })
        Producción (3): <resto_reglas> -> ε                        (si lookahead ∈ FOLLOW = { $ })
        """
        actual = self.token_actual()
        if actual.tipo == "WHEN":
            siguiente_regla = self.parse_regla()
            return [siguiente_regla] + self.parse_resto_reglas()

        if actual.tipo in FOLLOW["<resto_reglas>"]:
            return []

        self.lanzar_error(
            f"se esperaba el inicio de una nueva regla ('WHEN') o el fin de la entrada después de ';', "
            f"pero se encontró {formatear_token_encontrado(actual)}."
        )
        return []

    def parse_regla(self) -> ReglaAutomatizacionAST:
        """
        Producción (4): <regla> -> WHEN <condicion> THEN <accion> <clausula_else> PUNTO_COMA
        """
        tok_when = self.consumir("WHEN", "para iniciar una regla de automatización")
        nodo_condicion = self.parse_condicion(contexto="después de la palabra reservada WHEN")
        self.consumir("THEN", "después de la condición de la regla")
        accion_principal = self.parse_accion(contexto="después de la palabra reservada THEN")
        accion_alternativa = self.parse_clausula_else()
        self.consumir("PUNTO_COMA", "al finalizar la regla")

        return ReglaAutomatizacionAST(
            condicion=nodo_condicion,
            accion_entonces=accion_principal,
            accion_sino=accion_alternativa,
            linea_origen=tok_when.linea,
        )

    def parse_clausula_else(self) -> AccionActuadorAST | None:
        """
        Producción (5): <clausula_else> -> ELSE <accion>   (si lookahead == ELSE)
        Producción (6): <clausula_else> -> ε               (si lookahead ∈ FOLLOW = { PUNTO_COMA })
        """
        actual = self.token_actual()
        if actual.tipo == "ELSE":
            self.avanzar()
            return self.parse_accion(contexto="después de la palabra reservada ELSE")

        if actual.tipo in FOLLOW["<clausula_else>"]:
            return None

        self.lanzar_error(
            f"se esperaba ';' para cerrar la regla (o la cláusula 'ELSE' para una acción alternativa), "
            f"pero se encontró {formatear_token_encontrado(actual)}."
        )
        return None

    def parse_condicion(self, contexto: str = "") -> NodoAST:
        """
        Producción (7): <condicion> -> <termino_and> <cola_or>
        Conjunto FIRST(<condicion>) = { NOT, PARENT_IZQ, ID }
        """
        izquierda = self.parse_termino_and(contexto)
        return self.parse_cola_or(izquierda)

    def parse_cola_or(self, acumulado_izq: NodoAST) -> NodoAST:
        """
        Producción (8): <cola_or> -> OR <termino_and> <cola_or>   (si lookahead == OR)
        Producción (9): <cola_or> -> ε                            (si lookahead ∈ FOLLOW = { THEN, PARENT_DER })
        """
        actual = self.token_actual()
        if actual.tipo == "OR":
            self.avanzar()
            derecha = self.parse_termino_and(contexto="después del operador lógico OR")
            combinado = OperacionLogicaAST(conector="OR", izquierda=acumulado_izq, derecha=derecha)
            return self.parse_cola_or(combinado)

        if actual.tipo == "PARENT_DER" and not self.pila_parentesis:
            self.lanzar_error("paréntesis de cierre ')' inesperado sin un '(' que lo abra.")

        if actual.tipo in FOLLOW["<cola_or>"]:
            return acumulado_izq

        if self.pila_parentesis:
            abierto = self.pila_parentesis[-1]
            self.lanzar_error(
                f"se esperaba ')' para cerrar el paréntesis abierto en la línea {abierto.linea}, "
                f"columna {abierto.columna} (o un conector lógico AND/OR), "
                f"pero se encontró {formatear_token_encontrado(actual)}."
            )

        self.lanzar_error(
            f"se esperaba la palabra reservada THEN (o un conector lógico AND / OR) después de la condición, "
            f"pero se encontró {formatear_token_encontrado(actual)}."
        )
        return acumulado_izq

    def parse_termino_and(self, contexto: str = "") -> NodoAST:
        """
        Producción (10): <termino_and> -> <factor_logico> <cola_and>
        Conjunto FIRST(<termino_and>) = { NOT, PARENT_IZQ, ID }
        """
        izquierda = self.parse_factor_logico(contexto)
        return self.parse_cola_and(izquierda)

    def parse_cola_and(self, acumulado_izq: NodoAST) -> NodoAST:
        """
        Producción (11): <cola_and> -> AND <factor_logico> <cola_and>  (si lookahead == AND)
        Producción (12): <cola_and> -> ε                               (si lookahead ∈ FOLLOW = { OR, THEN, PARENT_DER })
        """
        actual = self.token_actual()
        if actual.tipo == "AND":
            self.avanzar()
            derecha = self.parse_factor_logico(contexto="después del operador lógico AND")
            combinado = OperacionLogicaAST(conector="AND", izquierda=acumulado_izq, derecha=derecha)
            return self.parse_cola_and(combinado)

        if actual.tipo == "PARENT_DER" and not self.pila_parentesis:
            self.lanzar_error("paréntesis de cierre ')' inesperado sin un '(' previo que le corresponda.")

        if actual.tipo in FOLLOW["<cola_and>"]:
            return acumulado_izq

        if self.pila_parentesis:
            abierto = self.pila_parentesis[-1]
            self.lanzar_error(
                f"se esperaba ')' para cerrar el paréntesis abierto en la línea {abierto.linea}, "
                f"columna {abierto.columna} (o un operador AND/OR), "
                f"pero se encontró {formatear_token_encontrado(actual)}."
            )

        self.lanzar_error(
            f"se esperaba la palabra reservada THEN (o un operador lógico AND / OR) después de la comparación, "
            f"pero se encontró {formatear_token_encontrado(actual)}."
        )
        return acumulado_izq

    def parse_factor_logico(self, contexto: str = "") -> NodoAST:
        """
        Producción (13): <factor_logico> -> NOT <factor_logico>
        Producción (14): <factor_logico> -> PARENT_IZQ <condicion> PARENT_DER
        Producción (15): <factor_logico> -> <comparacion>
        """
        actual = self.token_actual()

        # (13) <factor_logico> -> NOT <factor_logico>
        if actual.tipo == "NOT":
            self.avanzar()
            operando = self.parse_factor_logico(contexto="después del operador NOT")
            return NegacionLogicaAST(subexpresion=operando)

        # (14) <factor_logico> -> PARENT_IZQ <condicion> PARENT_DER
        if actual.tipo == "PARENT_IZQ":
            tok_apertura = self.avanzar()
            self.pila_parentesis.append(tok_apertura)
            condicion_interna = self.parse_condicion(contexto="dentro de los paréntesis '(' ... ')'")
            if self.token_actual().tipo != "PARENT_DER":
                self.lanzar_error(
                    f"se esperaba ')' para cerrar el paréntesis abierto en la línea {tok_apertura.linea}, "
                    f"columna {tok_apertura.columna}, pero se encontró {formatear_token_encontrado(self.token_actual())}."
                )
            self.avanzar()
            self.pila_parentesis.pop()
            return condicion_interna

        # (15) <factor_logico> -> <comparacion>
        if actual.tipo == "ID":
            return self.parse_comparacion(contexto)

        ubicacion = f" {contexto}" if contexto else ""
        self.lanzar_error(
            f"se esperaba una condición válida (identificador de sensor, 'NOT' o '('){ubicacion}, "
            f"pero se encontró {formatear_token_encontrado(actual)}."
        )
        raise AssertionError("Inalcanzable")

    def parse_comparacion(self, contexto: str = "") -> ComparacionSensorAST:
        """
        Producción (16): <comparacion> -> ID OP_REL <valor>
        """
        tok_sensor = self.consumir("ID", contexto or "al inicio de la comparación")
        actual = self.token_actual()
        if actual.tipo != "OP_REL":
            self.lanzar_error(
                f"se esperaba un operador relacional (>, <, >=, <=, ==, !=) después del identificador '{tok_sensor.lexema}', "
                f"pero se encontró {formatear_token_encontrado(actual)}."
            )
        tok_op = self.avanzar()
        nodo_valor = self.parse_valor(operador_previo=tok_op.lexema)
        return ComparacionSensorAST(
            identificador_sensor=tok_sensor.lexema,
            operador=tok_op.lexema,
            umbral=nodo_valor,
        )

    def parse_valor(self, operador_previo: str = "") -> ValorSensorAST:
        """
        Producción (17): <valor> -> NUM
        Producción (18): <valor> -> TRUE
        Producción (19): <valor> -> FALSE
        Producción (20): <valor> -> ID
        """
        actual = self.token_actual()
        if actual.tipo in FIRST["<valor>"]:
            self.avanzar()
            return ValorSensorAST(tipo_dato=actual.tipo, lexema=actual.lexema)

        ref_op = f" después del operador {operador_previo}" if operador_previo else ""
        self.lanzar_error(
            f"se esperaba un valor (número, TRUE, FALSE o identificador){ref_op}, "
            f"pero se encontró {formatear_token_encontrado(actual)}."
        )
        raise AssertionError("Inalcanzable")

    def parse_accion(self, contexto: str = "") -> AccionActuadorAST:
        """
        Producción (21): <accion> -> ID ID
        """
        actual = self.token_actual()
        if actual.tipo != "ID":
            ubicacion = f" {contexto}" if contexto else ""
            self.lanzar_error(
                f"se esperaba una acción válida (verbo identificador, ej. 'encender' o 'activar'){ubicacion}, "
                f"pero se encontró {formatear_token_encontrado(actual)}."
            )
        tok_verbo = self.avanzar()

        if self.token_actual().tipo != "ID":
            self.lanzar_error(
                f"se esperaba el nombre del dispositivo/actuador (identificador) después de la acción '{tok_verbo.lexema}', "
                f"pero se encontró {formatear_token_encontrado(self.token_actual())}."
            )
        tok_actuador = self.avanzar()
        return AccionActuadorAST(comando=tok_verbo.lexema, dispositivo=tok_actuador.lexema)


# ==============================================================================
# SIMULADOR DIRIGIDO POR TABLA PREDICTIVA LL(1) (Árbol de Derivación Concreto)
# ==============================================================================

def construir_arbol_derivacion_ll1(
    codigo_fuente: str,
    registrar_traza: bool = False,
) -> tuple[NodoArbol, list[tuple[str, str, str]]]:
    """
    Ejecuta el algoritmo predictivo dirigido por la tabla `TABLA_LL1` usando una pila explícita.
    Retorna:
        (raiz_arbol_derivacion, traza_pasos)
    """
    tokens = escanear_tokens(codigo_fuente, incluir_eof=True)
    raiz = NodoArbol(etiqueta=SIMBOLO_INICIAL, categoria_visual="raiz")
    nodo_eof = NodoArbol(etiqueta=MARCA_EOF, categoria_visual="hoja")

    pila: list[tuple[str, NodoArbol]] = [(MARCA_EOF, nodo_eof), (SIMBOLO_INICIAL, raiz)]
    cursor = 0
    traza: list[tuple[str, str, str]] = []

    while pila:
        simbolo_tope, nodo_actual = pila[-1]
        token_lookahead = tokens[cursor]

        estado_pila = " ".join(s for s, _ in reversed(pila))
        entrada_restante = " ".join(t.tipo for t in tokens[cursor:])

        # Caso 1: El tope de la pila es un símbolo terminal (o $)
        if not GRAMATICA_SISTEMA.es_no_terminal(simbolo_tope):
            if simbolo_tope != token_lookahead.tipo:
                esperado_str = DESCRIPCION_TOKENS.get(simbolo_tope, f"'{simbolo_tope}'")
                raise ErrorSintactico(
                    f"se esperaba {esperado_str}, pero se encontró {formatear_token_encontrado(token_lookahead)}.",
                    token_lookahead,
                    codigo_fuente,
                )
            pila.pop()
            if simbolo_tope != MARCA_EOF:
                nodo_actual.valor = f"'{token_lookahead.lexema}'"
                nodo_actual.categoria_visual = "hoja"
                cursor += 1
            if registrar_traza:
                traza.append((estado_pila, entrada_restante, f"Consumir terminal {simbolo_tope}"))
            continue

        # Caso 2: El tope de la pila es un No Terminal -> consultar TABLA_LL1
        regla = TABLA_LL1[simbolo_tope].get(token_lookahead.tipo)
        if regla is None:
            esperados = [DESCRIPCION_TOKENS.get(t, t) for t in TABLA_LL1[simbolo_tope].keys()]
            raise ErrorSintactico(
                f"símbolo inesperado {formatear_token_encontrado(token_lookahead)} al expandir {simbolo_tope}; "
                f"se esperaba {', '.join(esperados)}.",
                token_lookahead,
                codigo_fuente,
            )

        pila.pop()
        hijos_nodos: list[NodoArbol] = []
        for simb_rhs in regla.cuerpo:
            es_nt = GRAMATICA_SISTEMA.es_no_terminal(simb_rhs)
            cat = "no_terminal" if es_nt else "hoja"
            hijos_nodos.append(NodoArbol(etiqueta=simb_rhs, categoria_visual=cat))

        nodo_actual.hijos = hijos_nodos

        # Apilar en orden inverso (excepto ε)
        for simb_rhs, nodo_hijo in reversed(list(zip(regla.cuerpo, hijos_nodos))):
            if simb_rhs != EPSILON:
                pila.append((simb_rhs, nodo_hijo))

        if registrar_traza:
            traza.append((estado_pila, entrada_restante, str(regla)))

    return raiz, traza


if __name__ == "__main__":
    ejemplo_valido = "WHEN NOT (temperatura <= 28) AND humedad < 40 THEN encender ventilador ELSE apagar ventilador;"
    print("=== PRUEBA DEL PARSER Y CONSTRUCCIÓN DEL AST ===")
    print(f"Entrada:\n  {ejemplo_valido}\n")
    parser = AnalizadorSintactico(ejemplo_valido)
    ast = parser.analizar()
    print(ast.mostrar_ast())
