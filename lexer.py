"""
Módulo 1: Analizador Léxico (Lexer) - EcoSensor / SmartIoT DSL
Curso: Teoría de la Computación - INFO1148

Implementación propia basada en el notebook `anlizador_lexico1.ipynb` del curso,
extendida con:
- Rastreo exacto de fila y columna por cada token reconocido (`TokenLexico`).
- Soporte para comentarios de línea (`# ...`).
- Soporte para números enteros y de punto flotante (`28`, `25.5`).
- Palabras reservadas del dominio (`WHEN`, `THEN`, `ELSE`, `AND`, `OR`, `NOT`, `TRUE`, `FALSE`).
- Diagnóstico léxico localizado con indicador visual de columna.
"""

import re
import sys
from dataclasses import dataclass

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MARCA_EOF = "$"

PALABRAS_CLAVE = {
    "WHEN",
    "THEN",
    "ELSE",
    "AND",
    "OR",
    "NOT",
    "TRUE",
    "FALSE",
}

REGLAS_LEXICAS = [
    ("COMENTARIO", r"#[^\n]*"),
    ("NUM",        r"\d+(?:\.\d+)?"),
    ("OP_REL",     r">=|<=|==|!=|>|<"),
    ("PUNTO_COMA", r";"),
    ("PARENT_IZQ", r"\("),
    ("PARENT_DER", r"\)"),
    ("ID",         r"[A-Za-z_][A-Za-z0-9_]*"),
    ("ESPACIO",    r"[ \t\r\n]+"),
    ("ERROR",      r"."),
]

EXPRESION_MAESTRA = re.compile(
    "|".join(f"(?P<{nombre}>{patron})" for nombre, patron in REGLAS_LEXICAS)
)


@dataclass(frozen=True)
class TokenLexico:
    """Representa una unidad léxica enriquecida con sus coordenadas en el texto fuente."""
    tipo: str
    lexema: str
    linea: int
    columna: int
    indice: int

    def como_tupla(self) -> tuple[str, str]:
        return (self.tipo, self.lexema)


class ErrorLexicoDSL(ValueError):
    """Excepción lanzada cuando el escáner encuentra un carácter fuera del alfabeto."""

    def __init__(self, detalle: str, codigo_fuente: str, linea: int, columna: int, indice: int):
        self.detalle = detalle
        self.codigo_fuente = codigo_fuente
        self.linea = linea
        self.columna = columna
        self.indice = indice
        super().__init__(self.formatear_diagnostico())

    def formatear_diagnostico(self) -> str:
        encabezado = f"Error léxico [línea {self.linea}, columna {self.columna}]: {self.detalle}"
        lineas = self.codigo_fuente.splitlines()
        if 1 <= self.linea <= len(lineas):
            renglon = lineas[self.linea - 1]
            indicador = " " * (self.columna - 1) + "^"
            return f"{encabezado}\n  {self.linea:>3} | {renglon}\n      | {indicador}"
        return encabezado


def _calcular_coordenadas(texto: str, indice: int) -> tuple[int, int]:
    """Calcula (línea, columna) 1-based a partir del índice en la cadena."""
    linea = texto.count("\n", 0, indice) + 1
    ultimo_salto = texto.rfind("\n", 0, indice)
    columna = indice + 1 if ultimo_salto == -1 else indice - ultimo_salto
    return linea, columna


def escanear_tokens(cadena: str, incluir_eof: bool = True) -> list[TokenLexico]:
    """
    Escanea el código fuente y devuelve una lista de objetos `TokenLexico`
    con información de línea y columna. Si `incluir_eof` es True, añade el
    token marcador de fin de entrada `$` al final.
    """
    lista_tokens: list[TokenLexico] = []

    for coincidencia in EXPRESION_MAESTRA.finditer(cadena):
        categoria = coincidencia.lastgroup
        lexema = coincidencia.group()
        inicio = coincidencia.start()
        linea, columna = _calcular_coordenadas(cadena, inicio)

        if categoria in ("ESPACIO", "COMENTARIO"):
            continue

        if categoria == "ID" and lexema.upper() in PALABRAS_CLAVE:
            categoria = lexema.upper()

        elif categoria == "ERROR":
            sugerencia = ""
            if lexema == "=":
                sugerencia = " (¿quiso utilizar el operador de igualdad '=='?)"
            elif lexema in ("&", "|"):
                sugerencia = " (utilice los conectores lógicos 'AND' / 'OR')"
            raise ErrorLexicoDSL(
                detalle=f"Carácter ilegal '{lexema}' no perteneciente al alfabeto del lenguaje.{sugerencia}",
                codigo_fuente=cadena,
                linea=linea,
                columna=columna,
                indice=inicio,
            )

        lista_tokens.append(
            TokenLexico(
                tipo=categoria,
                lexema=lexema,
                linea=linea,
                columna=columna,
                indice=inicio,
            )
        )

    if incluir_eof:
        linea_fin, col_fin = _calcular_coordenadas(cadena, len(cadena))
        lista_tokens.append(
            TokenLexico(
                tipo=MARCA_EOF,
                lexema=MARCA_EOF,
                linea=linea_fin,
                columna=col_fin,
                indice=len(cadena),
            )
        )

    return lista_tokens


def analizador_lexico(cadena: str) -> list[tuple[str, str]]:
    """
    Función compatible con el formato original del notebook de cátedra:
    Retorna [(TIPO_TOKEN, lexema), ...] sin el marcador de fin '$'.
    """
    return [tok.como_tupla() for tok in escanear_tokens(cadena, incluir_eof=False)]


if __name__ == "__main__":
    muestra = (
        "# Regla de control de riego y ventilación en invernadero\n"
        "WHEN NOT (humedad_suelo >= 35.5) AND temperatura > 28 THEN activar riego ELSE apagar riego;"
    )
    print("=== PRUEBA DEL ESCÁNER LÉXICO ===")
    print(f"Código fuente:\n{muestra}\n")
    print(f"{'#':<3} | {'TIPO':<12} | {'LEXEMA':<16} | {'LÍNEA':<5} | {'COLUMNA':<7}")
    print("-" * 55)
    for idx, t in enumerate(escanear_tokens(muestra), start=1):
        print(f"{idx:<3} | {t.tipo:<12} | {t.lexema:<16} | {t.linea:<5} | {t.columna:<7}")
