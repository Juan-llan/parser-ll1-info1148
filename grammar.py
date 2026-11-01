"""
Módulo 2: Gramática Libre de Contexto (GLC), Conjuntos FIRST/FOLLOW y Tabla LL(1)
Curso: Teoría de la Computación - INFO1148

Implementación propia orientada a objetos para:
- Fase 6.2: Definición formal de la GLC (notación <no_terminal> del enunciado).
- Fase 6.3: Cálculo formal de conjuntos FIRST y FOLLOW y verificación de propiedades.
- Fase 6.4: Construcción de la Tabla Predictiva LL(1) y comprobación de ausencia de conflictos.

Extensiones creativas integradas en la gramática:
1. Operador lógico unario `NOT` de máxima precedencia.
2. Agrupación jerárquica con paréntesis `( <condicion> )`.
3. Cláusula opcional `ELSE <accion>` al final de cada regla condicional.
4. Comentarios `# ...` gestionados a nivel léxico.
"""

import sys
from dataclasses import dataclass

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EPSILON = "ε"
EOF_SIMBOLO = "$"

SIMBOLO_INICIAL = "<programa>"


@dataclass(frozen=True)
class ReglaProduccion:
    """Representa una regla de producción numerada: A -> α."""
    numero: int
    cabeza: str
    cuerpo: tuple[str, ...]

    def __str__(self) -> str:
        derecha = " ".join(self.cuerpo)
        return f"({self.numero:>2}) {self.cabeza:<18} -> {derecha}"


# ==============================================================================
# 1. DEFINICIÓN DE PRODUCCIONES DE LA GRAMÁTICA LL(1) (Fase 6.2)
# ==============================================================================
# Precedencia de operadores lógicos:
#   Nivel 1 (menor): OR   (<condicion> y <cola_or>)
#   Nivel 2 (medio): AND  (<termino_and> y <cola_and>)
#   Nivel 3 (mayor): NOT y Paréntesis (<factor_logico>)

DEFINICION_GRAMATICA: list[tuple[str, list[str]]] = [
    # Estructura general del programa (una o más reglas)
    ("<programa>",       ["<regla>", "<resto_reglas>"]),
    ("<resto_reglas>",   ["<regla>", "<resto_reglas>"]),
    ("<resto_reglas>",   [EPSILON]),

    # Estructura de sentencia principal + extensión creativa ELSE opcional
    ("<regla>",          ["WHEN", "<condicion>", "THEN", "<accion>", "<clausula_else>", "PUNTO_COMA"]),
    ("<clausula_else>",  ["ELSE", "<accion>"]),
    ("<clausula_else>",  [EPSILON]),

    # Expresiones lógicas con disyunción (OR)
    ("<condicion>",      ["<termino_and>", "<cola_or>"]),
    ("<cola_or>",        ["OR", "<termino_and>", "<cola_or>"]),
    ("<cola_or>",        [EPSILON]),

    # Expresiones lógicas con conjunción (AND)
    ("<termino_and>",    ["<factor_logico>", "<cola_and>"]),
    ("<cola_and>",       ["AND", "<factor_logico>", "<cola_and>"]),
    ("<cola_and>",       [EPSILON]),

    # Factor lógico: negación NOT, agrupación entre paréntesis o comparación relacional
    ("<factor_logico>",  ["NOT", "<factor_logico>"]),
    ("<factor_logico>",  ["PARENT_IZQ", "<condicion>", "PARENT_DER"]),
    ("<factor_logico>",  ["<comparacion>"]),

    # Comparación de sensores/variables y valores admitidos
    ("<comparacion>",    ["ID", "OP_REL", "<valor>"]),
    ("<valor>",          ["NUM"]),
    ("<valor>",          ["TRUE"]),
    ("<valor>",          ["FALSE"]),
    ("<valor>",          ["ID"]),

    # Acción sobre dispositivo/actuador (verbo + actuador, ej: encender ventilador)
    ("<accion>",         ["ID", "ID"]),
]


class AnalizadorGramaticaLL1:
    """
    Calcula los conjuntos FIRST, FOLLOW y la Tabla Predictiva LL(1)
    a partir de la definición formal de la Gramática Libre de Contexto.
    """

    def __init__(self, definicion: list[tuple[str, list[str]]], simbolo_inicial: str = SIMBOLO_INICIAL):
        self.simbolo_inicial = simbolo_inicial
        self.producciones: list[ReglaProduccion] = [
            ReglaProduccion(numero=i, cabeza=nt, cuerpo=tuple(rhs))
            for i, (nt, rhs) in enumerate(definicion, start=1)
        ]
        self.no_terminales: list[str] = list(dict.fromkeys(p.cabeza for p in self.producciones))
        self.terminales: list[str] = list(
            dict.fromkeys(
                simb
                for p in self.producciones
                for simb in p.cuerpo
                if not simb.startswith("<") and simb != EPSILON
            )
        )
        self.columnas_tabla: list[str] = self.terminales + [EOF_SIMBOLO]

        self.first: dict[str, set[str]] = self._calcular_conjuntos_first()
        self.follow: dict[str, set[str]] = self._calcular_conjuntos_follow()
        self.tabla_ll1, self.conflictos = self._construir_tabla_predictiva()

    def es_no_terminal(self, simbolo: str) -> bool:
        return simbolo.startswith("<") and simbolo.endswith(">")

    def evaluar_first_secuencia(self, secuencia: tuple[str, ...] | list[str]) -> set[str]:
        """Calcula FIRST(α) para cualquier secuencia de símbolos gramaticales α."""
        if not secuencia or secuencia[0] == EPSILON:
            return {EPSILON}

        resultado: set[str] = set()
        todos_anulables = True

        for simbolo in secuencia:
            if not self.es_no_terminal(simbolo):
                resultado.add(simbolo)
                todos_anulables = False
                break

            first_simbolo = self.first[simbolo]
            resultado.update(first_simbolo - {EPSILON})
            if EPSILON not in first_simbolo:
                todos_anulables = False
                break

        if todos_anulables:
            resultado.add(EPSILON)

        return resultado

    def _calcular_conjuntos_first(self) -> dict[str, set[str]]:
        first: dict[str, set[str]] = {nt: set() for nt in self.no_terminales}
        hubo_cambios = True

        while hubo_cambios:
            hubo_cambios = False
            for prod in self.producciones:
                # Evaluar usando los conjuntos parciales actuales
                nuevos: set[str] = set()
                anulable = True
                for simb in prod.cuerpo:
                    if simb == EPSILON:
                        nuevos.add(EPSILON)
                        anulable = False
                        break
                    if not self.es_no_terminal(simb):
                        nuevos.add(simb)
                        anulable = False
                        break
                    nuevos.update(first[simb] - {EPSILON})
                    if EPSILON not in first[simb]:
                        anulable = False
                        break
                if anulable:
                    nuevos.add(EPSILON)

                tamano_previo = len(first[prod.cabeza])
                first[prod.cabeza].update(nuevos)
                if len(first[prod.cabeza]) > tamano_previo:
                    hubo_cambios = True

        return first

    def _calcular_conjuntos_follow(self) -> dict[str, set[str]]:
        follow: dict[str, set[str]] = {nt: set() for nt in self.no_terminales}
        follow[self.simbolo_inicial].add(EOF_SIMBOLO)
        hubo_cambios = True

        while hubo_cambios:
            hubo_cambios = False
            for prod in self.producciones:
                cuerpo = prod.cuerpo
                for indice, simbolo in enumerate(cuerpo):
                    if not self.es_no_terminal(simbolo):
                        continue

                    sufijo = cuerpo[indice + 1:]
                    first_sufijo = self.evaluar_first_secuencia(sufijo) if sufijo else {EPSILON}

                    agregar = first_sufijo - {EPSILON}
                    if EPSILON in first_sufijo:
                        agregar.update(follow[prod.cabeza])

                    tamano_previo = len(follow[simbolo])
                    follow[simbolo].update(agregar)
                    if len(follow[simbolo]) > tamano_previo:
                        hubo_cambios = True

        return follow

    def _construir_tabla_predictiva(
        self,
    ) -> tuple[dict[str, dict[str, ReglaProduccion]], list[tuple[str, str, list[int]]]]:
        matriz_candidatos: dict[str, dict[str, list[ReglaProduccion]]] = {
            nt: {} for nt in self.no_terminales
        }

        for prod in self.producciones:
            first_rhs = self.evaluar_first_secuencia(prod.cuerpo)
            for terminal in first_rhs - {EPSILON}:
                matriz_candidatos[prod.cabeza].setdefault(terminal, []).append(prod)

            if EPSILON in first_rhs:
                for terminal_follow in self.follow[prod.cabeza]:
                    matriz_candidatos[prod.cabeza].setdefault(terminal_follow, []).append(prod)

        conflictos: list[tuple[str, str, list[int]]] = []
        tabla_unica: dict[str, dict[str, ReglaProduccion]] = {nt: {} for nt in self.no_terminales}

        for nt, fila in matriz_candidatos.items():
            for term, lista_prods in fila.items():
                tabla_unica[nt][term] = lista_prods[0]
                if len(lista_prods) > 1:
                    conflictos.append((nt, term, [p.numero for p in lista_prods]))

        return tabla_unica, conflictos

    def es_gramatica_ll1(self) -> bool:
        return len(self.conflictos) == 0


# Instancia global reutilizable por otros módulos
GRAMATICA_SISTEMA = AnalizadorGramaticaLL1(DEFINICION_GRAMATICA)
NO_TERMINALES = GRAMATICA_SISTEMA.no_terminales
TERMINALES = GRAMATICA_SISTEMA.terminales
FIRST = GRAMATICA_SISTEMA.first
FOLLOW = GRAMATICA_SISTEMA.follow
TABLA_LL1 = GRAMATICA_SISTEMA.tabla_ll1


def mostrar_gramatica() -> None:
    """Imprime las producciones numeradas de la GLC."""
    print("=== 1. GRAMÁTICA LIBRE DE CONTEXTO (GLC) ===")
    print(f"Símbolo inicial: {GRAMATICA_SISTEMA.simbolo_inicial}")
    print(f"No terminales ({len(NO_TERMINALES)}): {', '.join(NO_TERMINALES)}")
    print(f"Terminales ({len(TERMINALES)}): {', '.join(TERMINALES)}\n")
    for prod in GRAMATICA_SISTEMA.producciones:
        print(f"  {prod}")


def mostrar_first_follow() -> None:
    """Imprime la tabla comparativa de conjuntos FIRST y FOLLOW."""
    print("\n=== 2. CONJUNTOS FIRST Y FOLLOW ===")
    print(f"{'NO TERMINAL':<18} | {'FIRST':<38} | {'FOLLOW'}")
    print("-" * 95)
    for nt in NO_TERMINALES:
        str_first = "{ " + ", ".join(sorted(FIRST[nt])) + " }"
        str_follow = "{ " + ", ".join(sorted(FOLLOW[nt])) + " }"
        print(f"{nt:<18} | {str_first:<38} | {str_follow}")


def mostrar_tabla_ll1() -> None:
    """Imprime la Tabla Predictiva LL(1) indicando el número de producción en cada celda."""
    print("\n=== 3. TABLA PREDICTIVA LL(1) (Números de Producción) ===")
    columnas = GRAMATICA_SISTEMA.columnas_tabla
    encabezado = f"{'No Terminal':<18} |" + "|".join(f"{col:^6}" for col in columnas)
    print(encabezado)
    print("-" * len(encabezado))

    for nt in NO_TERMINALES:
        celdas = []
        for col in columnas:
            regla = TABLA_LL1[nt].get(col)
            celdas.append(f"{f'({regla.numero})':^6}" if regla else f"{'·':^6}")
        print(f"{nt:<18} |" + "|".join(celdas))

    estado = "SÍ ES LL(1) (0 conflictos detectados)" if GRAMATICA_SISTEMA.es_gramatica_ll1() else f"NO ES LL(1): {GRAMATICA_SISTEMA.conflictos}"
    print(f"\nVerificación formal LL(1): {estado}")


if __name__ == "__main__":
    mostrar_gramatica()
    mostrar_first_follow()
    mostrar_tabla_ll1()
