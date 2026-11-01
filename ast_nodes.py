"""
Módulo 3: Árbol Sintáctico / AST y Exportación Visual (Fase 6.6)
Curso: Teoría de la Computación - INFO1148

Define:
1. `NodoArbol`: Estructura genérica para representar tanto el Árbol Sintáctico Abstracto (AST)
   como el Árbol de Derivación Concreto en texto jerárquico (ASCII) y formato Graphviz (`.dot`).
2. Jerarquía de clases del AST del lenguaje IoT (`ProgramaAST`, `ReglaAST`,
   `OperacionLogicaAST`, `NegacionLogicaAST`, `ComparacionSensorAST`, `ValorSensorAST`, `AccionActuadorAST`).
"""

import sys
from dataclasses import dataclass, field

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


@dataclass
class NodoArbol:
    """
    Nodo para visualización jerárquica de árboles sintácticos (AST o Derivación).
    """
    etiqueta: str
    valor: str | None = None
    hijos: list["NodoArbol"] = field(default_factory=list)
    categoria_visual: str = "no_terminal"  # "raiz", "operador", "accion", "hoja", "no_terminal"

    def agregar_hijo(self, hijo: "NodoArbol") -> None:
        self.hijos.append(hijo)

    def texto_completo(self) -> str:
        if self.valor is not None:
            return f"{self.etiqueta}: {self.valor}"
        return self.etiqueta

    def imprimir_jerarquico(self, prefijo: str = "", es_ultimo: bool = True, es_raiz: bool = True) -> str:
        """
        Genera una representación en texto jerárquico (con conectores ├── y └──)
        ideal para mostrar en consola e incluir directamente en el informe.
        """
        if es_raiz:
            lineas = [self.texto_completo()]
            prefijo_hijos = ""
        else:
            conector = "└── " if es_ultimo else "├── "
            lineas = [f"{prefijo}{conector}{self.texto_completo()}"]
            prefijo_hijos = prefijo + ("    " if es_ultimo else "│   ")

        total = len(self.hijos)
        for indice, hijo in enumerate(self.hijos):
            ultimo_hijo = indice == (total - 1)
            lineas.append(hijo.imprimir_jerarquico(prefijo_hijos, ultimo_hijo, es_raiz=False))

        return "\n".join(lineas)

    def exportar_graphviz_dot(self, nombre_grafo: str = "ArbolSintacticoIoT") -> str:
        """
        Exporta el árbol al formato DOT de Graphviz para generar diagramas PNG/PDF/SVG.
        """
        paleta_colores = {
            "raiz":        ('shape=doubleoctagon, style="filled", fillcolor="#d0e8ff"',),
            "operador":    ('shape=diamond, style="filled", fillcolor="#fff2cc"',),
            "accion":      ('shape=component, style="filled", fillcolor="#d5e8d4"',),
            "hoja":        ('shape=box, style="rounded,filled", fillcolor="#f5f5f5"',),
            "no_terminal": ('shape=ellipse, style="filled", fillcolor="#e1d5e7"',),
        }

        lineas = [
            f'digraph "{nombre_grafo}" {{',
            '  graph [rankdir=TB, nodesep=0.3, ranksep=0.5, fontname="Arial"];',
            '  node [fontname="Arial", fontsize=10];',
        ]
        secuencia_id = 0

        def recorrer(nodo: "NodoArbol") -> str:
            nonlocal secuencia_id
            identificador = f"nodo_{secuencia_id}"
            secuencia_id += 1

            texto_escapado = nodo.texto_completo().replace("\\", "\\\\").replace('"', '\\"')
            estilo = paleta_colores.get(nodo.categoria_visual, paleta_colores["no_terminal"])[0]
            lineas.append(f'  {identificador} [label="{texto_escapado}", {estilo}];')

            for hijo in nodo.hijos:
                id_hijo = recorrer(hijo)
                lineas.append(f"  {identificador} -> {id_hijo};")

            return identificador

        recorrer(self)
        lineas.append("}")
        return "\n".join(lineas)


# ==============================================================================
# CLASES DEL ÁRBOL SINTÁCTICO ABSTRACTO (AST) DEL LENGUAJE IoT
# ==============================================================================

class NodoAST:
    """Clase base abstracta para todos los nodos semánticos del AST."""

    def como_arbol_visual(self) -> NodoArbol:
        raise NotImplementedError

    def mostrar_ast(self) -> str:
        return self.como_arbol_visual().imprimir_jerarquico()


@dataclass
class ValorSensorAST(NodoAST):
    """Representa un valor constante o identificador en una comparación (NUM, TRUE, FALSE, ID)."""
    tipo_dato: str
    lexema: str

    def como_arbol_visual(self) -> NodoArbol:
        return NodoArbol(
            etiqueta=f"Valor({self.tipo_dato})",
            valor=f"'{self.lexema}'",
            categoria_visual="hoja",
        )


@dataclass
class ComparacionSensorAST(NodoAST):
    """Representa una comparación relacional: <sensor> <op_rel> <valor>."""
    identificador_sensor: str
    operador: str
    umbral: ValorSensorAST

    def como_arbol_visual(self) -> NodoArbol:
        nodo_sensor = NodoArbol(
            etiqueta="Sensor(ID)",
            valor=f"'{self.identificador_sensor}'",
            categoria_visual="hoja",
        )
        return NodoArbol(
            etiqueta="Comparación",
            valor=f"'{self.operador}'",
            hijos=[nodo_sensor, self.umbral.como_arbol_visual()],
            categoria_visual="operador",
        )


@dataclass
class NegacionLogicaAST(NodoAST):
    """Representa la extensión creativa de negación lógica: NOT <factor_logico>."""
    subexpresion: NodoAST

    def como_arbol_visual(self) -> NodoArbol:
        return NodoArbol(
            etiqueta="OperadorUnario",
            valor="'NOT'",
            hijos=[self.subexpresion.como_arbol_visual()],
            categoria_visual="operador",
        )


@dataclass
class OperacionLogicaAST(NodoAST):
    """Representa una conjunción (AND) o disyunción (OR) binaria asociativa a la izquierda."""
    conector: str  # "AND" | "OR"
    izquierda: NodoAST
    derecha: NodoAST

    def como_arbol_visual(self) -> NodoArbol:
        return NodoArbol(
            etiqueta="OperadorLógico",
            valor=f"'{self.conector}'",
            hijos=[self.izquierda.como_arbol_visual(), self.derecha.como_arbol_visual()],
            categoria_visual="operador",
        )


@dataclass
class AccionActuadorAST(NodoAST):
    """Representa un comando sobre un actuador del sistema IoT (ej. encender ventilador)."""
    comando: str
    dispositivo: str

    def como_arbol_visual(self) -> NodoArbol:
        return NodoArbol(
            etiqueta="Acción",
            valor=f"'{self.comando} -> {self.dispositivo}'",
            hijos=[
                NodoArbol("Verbo(ID)", f"'{self.comando}'", categoria_visual="hoja"),
                NodoArbol("Actuador(ID)", f"'{self.dispositivo}'", categoria_visual="hoja"),
            ],
            categoria_visual="accion",
        )


@dataclass
class ReglaAutomatizacionAST(NodoAST):
    """
    Representa una regla completa:
    WHEN <condicion> THEN <accion_entonces> [ELSE <accion_sino>] ;
    """
    condicion: NodoAST
    accion_entonces: AccionActuadorAST
    accion_sino: AccionActuadorAST | None = None
    linea_origen: int = 1

    def como_arbol_visual(self) -> NodoArbol:
        hijos_regla = [
            NodoArbol("Condición (WHEN)", hijos=[self.condicion.como_arbol_visual()]),
            NodoArbol("Entonces (THEN)", hijos=[self.accion_entonces.como_arbol_visual()]),
        ]
        if self.accion_sino is not None:
            hijos_regla.append(
                NodoArbol("Sino (ELSE)", hijos=[self.accion_sino.como_arbol_visual()])
            )
        return NodoArbol(
            etiqueta=f"ReglaIoT (línea {self.linea_origen})",
            hijos=hijos_regla,
            categoria_visual="raiz",
        )


@dataclass
class ProgramaAST(NodoAST):
    """Nodo raíz del AST que agrupa todas las reglas del programa IoT."""
    reglas: list[ReglaAutomatizacionAST] = field(default_factory=list)

    def como_arbol_visual(self) -> NodoArbol:
        return NodoArbol(
            etiqueta="ProgramaIoT",
            valor=f"{len(self.reglas)} regla(s)",
            hijos=[regla.como_arbol_visual() for regla in self.reglas],
            categoria_visual="raiz",
        )
