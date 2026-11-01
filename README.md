# Proyecto: Analizador Sintáctico LL(1) para DSL de Monitoreo Ambiental y Automatización IoT

**Asignatura:** Teoría de la Computación (INFO1148)  
**Lenguaje de implementación:** Python 3 (Biblioteca Estándar)  
**Tema central:** Análisis sintáctico predictivo LL(1), Gramáticas Libres de Contexto (GLC), FIRST/FOLLOW y AST

---

## 1. Descripción del Dominio y Propósito del Lenguaje
Este proyecto diseña e implementa un **Lenguaje de Dominio Específico (DSL)** orientado al **monitoreo ambiental, control de invernaderos inteligentes y domótica IoT**.  
El lenguaje permite declarar reglas reactivas que evalúan el estado de sensores (`temperatura`, `humedad_suelo`, `co2`, `movimiento`, `humo`, `calidad_aire`) mediante operadores relacionales y lógicos para comandar actuadores (`encender ventilador`, `activar riego`, `abrir valvula`, etc.).

### Extensiones Creativas Incorporadas (Sección 6.9)
1. **Operador lógico unario `NOT`** de máxima precedencia para negar condiciones o bloques parentizados.
2. **Agrupación jerárquica mediante paréntesis `( <condicion> )`** para controlar explícitamente la precedencia entre `OR` y `AND`.
3. **Cláusula condicional alternativa `ELSE <accion>`** opcional al final de cada regla (`WHEN <condicion> THEN <accion> [ELSE <accion>];`).
4. **Comentarios de línea (`# ...`)** en el código fuente, filtrados durante el análisis léxico conservando el conteo exacto de líneas y columnas.

---

## 2. Estructura del Proyecto

```text
parser-ll1-info1148/
├── main.py               # CLI principal y demostración integral de todas las fases
├── lexer.py              # Fase 6.1 y 7: Escáner léxico con rastreo de línea/columna y comentarios
├── grammar.py            # Fases 6.2, 6.3 y 6.4: GLC (21 producciones), FIRST, FOLLOW y Tabla LL(1)
├── ast_nodes.py          # Fase 6.6: Clases del AST, árbol jerárquico ASCII y exportación Graphviz (.dot)
├── parser.py             # Fases 6.5, 6.7 y 6.9: Parser de descenso recursivo LL(1), simulador de pila y errores
├── tests.py              # Fase 6.8: Suite automatizada de 30 casos de prueba (12 válidos, 12 inválidos, 6 límite)
├── ejemplos/
│   └── reglas_iot.txt    # Archivo auxiliar con reglas de monitoreo ambiental e invernadero IoT
└── README.md             # Documentación técnica y guía de ejecución reproducible
```

---

## 3. Requisitos y Dependencias
- **Python 3.10 o superior**.
- **Sin dependencias externas:** Todo el cálculo de `FIRST`, `FOLLOW`, `TABLA_LL1`, el descenso recursivo y la construcción del AST están implementados desde cero utilizando únicamente la biblioteca estándar de Python (`re`, `dataclasses`, `argparse`, `pathlib`).

---

## 4. Instrucciones de Ejecución

Clonar el repositorio y entrar en la carpeta del proyecto:
```bash
git clone https://github.com/Juan-llan/parser-ll1-info1148.git
cd parser-ll1-info1148
```

### A. Demostración completa del proyecto
Muestra la gramática, conjuntos `FIRST`/`FOLLOW`, tabla predictiva `LL(1)`, análisis de una regla con extensiones creativas, su AST, traza de la pila y diagnóstico de errores:
```bash
python main.py
```

### B. Ejecutar la batería de 30 casos de prueba (Fase 6.8)
Evalúa las 12 entradas válidas, 12 inválidas y 6 casos límite e imprime la tabla comparativa exigida en el informe:
```bash
python tests.py
# o también:
python main.py --pruebas
```

### C. Analizar un archivo de reglas IoT
```bash
python main.py -f ejemplos/reglas_iot.txt
```

### D. Analizar una sentencia puntual desde la terminal (con árbol de derivación y traza)
```bash
python main.py -c "WHEN NOT (temperatura <= 28) AND humedad < 40 THEN encender ventilador ELSE apagar ventilador;" --derivacion --traza
```

### E. Exportar el AST a formato Graphviz (`.dot`)
```bash
python main.py -f ejemplos/reglas_iot.txt --dot ast_invernadero.dot
```

---

## 5. Gramática Libre de Contexto LL(1) (Resumen)

Símbolo inicial: `<programa>`

```text
( 1) <programa>         -> <regla> <resto_reglas>
( 2) <resto_reglas>     -> <regla> <resto_reglas>
( 3) <resto_reglas>     -> ε
( 4) <regla>            -> WHEN <condicion> THEN <accion> <clausula_else> PUNTO_COMA
( 5) <clausula_else>    -> ELSE <accion>
( 6) <clausula_else>    -> ε
( 7) <condicion>        -> <termino_and> <cola_or>
( 8) <cola_or>          -> OR <termino_and> <cola_or>
( 9) <cola_or>          -> ε
(10) <termino_and>      -> <factor_logico> <cola_and>
(11) <cola_and>         -> AND <factor_logico> <cola_and>
(12) <cola_and>         -> ε
(13) <factor_logico>    -> NOT <factor_logico>
(14) <factor_logico>    -> PARENT_IZQ <condicion> PARENT_DER
(15) <factor_logico>    -> <comparacion>
(16) <comparacion>      -> ID OP_REL <valor>
(17) <valor>            -> NUM
(18) <valor>            -> TRUE
(19) <valor>            -> FALSE
(20) <valor>            -> ID
(21) <accion>           -> ID ID
```

---

## 6. Ejemplo de Salida (AST y Manejo de Errores)

### Entrada válida:
```text
WHEN NOT (temperatura <= 28.5) AND humedad < 40 THEN encender ventilador ELSE apagar ventilador;
```
**AST Generado:**
```text
ProgramaIoT: 1 regla(s)
└── ReglaIoT (línea 1)
    ├── Condición (WHEN)
    │   └── OperadorLógico: 'AND'
    │       ├── OperadorUnario: 'NOT'
    │       │   └── Comparación: '<='
    │       │       ├── Sensor(ID): 'temperatura'
    │       │       └── Valor(NUM): '28.5'
    │       └── Comparación: '<'
    │           ├── Sensor(ID): 'humedad'
    │           └── Valor(NUM): '40'
    ├── Entonces (THEN)
    │   └── Acción: 'encender -> ventilador'
    │       ├── Verbo(ID): 'encender'
    │       └── Actuador(ID): 'ventilador'
    └── Sino (ELSE)
        └── Acción: 'apagar -> ventilador'
            ├── Verbo(ID): 'apagar'
            └── Actuador(ID): 'ventilador'
```

### Entrada inválida (Diagnóstico localizado con línea, columna y puntero `^`):
```text
Error sintáctico (línea 1, columna 20, posición 19): se esperaba un valor (número, TRUE, FALSE o identificador) después del operador >, pero se encontró la palabra reservada 'THEN'.
    1 | WHEN temperatura > THEN encender ventilador;
      |                    ^
```
