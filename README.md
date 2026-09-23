# Calculadora LL(1): precedencia y asociatividad

Taller de **Lenguajes de Programación (2026-2)** basado en la sesión 05, *Análisis sintáctico descendente:
predicción, conjuntos PRIMEROS y SIGUIENTES*.

Aquí probamos la gramática de una calculadora con `+`, `-`, `*` y `/` en cuatro versiones, y comprobamos
cómo cambia el resultado según la **precedencia** y la **asociatividad**. Todo se hace con un analizador
descendente **LL(1)** escrito desde cero en Python: el programa calcula PRIMEROS, SIGUIENTES, los
conjuntos de predicción y la tabla LL(1), y detecta conflictos.

```
$ python main.py "8 - 3 - 2"

    Gramática                               Agrupación     Resultado
--  --------------------------------------  -------------  ---------
G1  * y / primero, asociatividad izquierda  ((8 - 3) - 2)  3
G2  * y / primero, asociatividad derecha    (8 - (3 - 2))  7
G3  + y - primero, asociatividad izquierda  ((8 - 3) - 2)  3
G4  + y - primero, asociatividad derecha    (8 - (3 - 2))  7
```

## Las cuatro gramáticas

Salen de cruzar dos decisiones:

|                     | Asociatividad por la izquierda | Asociatividad por la derecha |
|---------------------|:------------------------------:|:----------------------------:|
| **`*` y `/` pesan más** | G1                         | G2                           |
| **`+` y `-` pesan más** | G3                         | G4                           |

- **Precedencia** = en qué nivel de la gramática está el operador. Mientras más abajo, más fuerte.
- **Asociatividad** = hacia qué lado va la recursión.

Estas son las versiones finales, ya transformadas para que sean LL(1):

```
G1 (* / primero, izquierda)          G2 (* / primero, derecha)
E  → T E'                            E  → T E'
E' → + T E' | - T E' | ε             E' → + E | - E | ε
T  → F T'                            T  → F T'
T' → * F T' | / F T' | ε             T' → * T | / T | ε
F  → ( E ) | num                     F  → ( E ) | num

G3 (+ - primero, izquierda)          G4 (+ - primero, derecha)
E  → T E'                            E  → T E'
E' → * T E' | / T E' | ε             E' → * E | / E | ε
T  → F T'                            T  → F T'
T' → + F T' | - F T' | ε             T' → + T | - T | ε
F  → ( E ) | num                     F  → ( E ) | num
```

Las versiones "naturales" (`E → E + T | T` y `E → T + E | T`) **no son LL(1)**: las primeras tienen
recursión por la izquierda y las segundas un prefijo común. El programa aplica las transformaciones de
la clase (quitar la recursión izquierda y factorizar) y una prueba verifica que el resultado es
exactamente la gramática de arriba.

## Requisitos

- Python 3.10 o superior. El programa no usa librerías externas.
- `pytest`, solo para correr las pruebas:

```bash
pip install pytest
```

## Uso

```bash
python main.py "2 + 3 * 4"             # compara las cuatro gramáticas
python main.py "2 + 3 * 4" -g G3       # usa solo una gramática
python main.py "2 + 3 * 4" --traza     # muestra la pila paso a paso
python main.py "2 + 3 * 4" --arbol     # dibuja el árbol de derivación
python main.py --tabla G1              # PRIMEROS, SIGUIENTES, PRED y tabla LL(1)
python main.py --tabla G1_original     # la versión sin transformar, con sus conflictos
python main.py --listar                # todas las gramáticas disponibles
python main.py                         # modo interactivo (escribe "salir" para terminar)
```

En Windows puede que tengas que usar `py` en lugar de `python`.

Con `--tabla` se puede ver cualquiera de estas gramáticas: `G1` a `G4`, `G1_original` a `G4_original`,
`AMBIGUA`, `EJEMPLO_CLASE` y `ACTIVIDAD_CLASE` (las dos últimas son las de las diapositivas).

### Ejemplo: la tabla de G1

```
$ python main.py --tabla G1
...
No terminal  PRIMEROS     SIGUIENTES
-----------  -----------  --------------------
E            { (, num }   { ), $ }
E'           { +, -, ε }  { ), $ }
T            { (, num }   { +, -, ), $ }
T'           { *, /, ε }  { +, -, ), $ }
F            { (, num }   { +, -, *, /, ), $ }

Tabla LL(1) (cada celda es el lado derecho que se aplica):
M   +       -       *       /       (      )  num   $
--  ------  ------  ------  ------  -----  -  ----  -
E   –       –       –       –       T E'   –  T E'  –
E'  + T E'  - T E'  –       –       –      ε  –     ε
T   –       –       –       –       F T'   –  F T'  –
T'  ε       ε       * F T'  / F T'  –      ε  –     ε
F   –       –       –       –       ( E )  –  num   –

[OK] Sin conflictos: la gramática es LL(1).
```

## Resultados

| Expresión        | G1              | G2              | G3              | G4              |
|------------------|-----------------|-----------------|-----------------|-----------------|
| `8 - 3 - 2`      | 3               | 7               | 3               | 7               |
| `100 / 10 / 5 / 2` | 1             | 25              | 1               | 25              |
| `2 + 3 * 4`      | 14              | 14              | 20              | 20              |
| `10 - 4 / 2`     | 8               | 8               | 3               | 3               |
| `2 * 3 - 1 - 1`  | 4               | 6               | 2               | 6               |
| `(2 + 3) * 4`    | 20              | 20              | 20              | 20              |
| `4 / 2 - 2`      | 0               | 0               | división por 0  | división por 0  |

- Con un solo tipo de operador (`8 - 3 - 2`) solo importa la asociatividad: G1 = G3 y G2 = G4.
- Con operadores de distinto nivel (`2 + 3 * 4`) solo importa la precedencia: G1 = G2 y G3 = G4.
- `2 * 3 - 1 - 1` da una agrupación distinta en cada una de las cuatro gramáticas.
- Los paréntesis siempre mandan.

## Cómo funciona

```
"2 + 3 * 4" → tokens → analizador con tabla LL(1) → árbol de derivación → AST → 14
```

| Archivo                 | Qué hace |
|-------------------------|----------|
| `ll1.py`                | Lee una gramática en texto y calcula PRIMEROS, SIGUIENTES, PRED, la tabla LL(1) y los conflictos. También quita la recursión izquierda y factoriza. |
| `gramaticas.py`         | Las cuatro calculadoras, sus versiones originales, la gramática ambigua y los ejemplos de clase. |
| `analizador.py`         | Analizador léxico y analizador predictivo con pila. Guarda la traza y arma el árbol de derivación. |
| `evaluador.py`          | Pasa del árbol de derivación al AST y lo evalúa con fracciones exactas (`1 / 3` da `1/3`). |
| `descenso_recursivo.py` | Una segunda implementación con descenso recursivo, para comparar. |
| `calculadora.py`        | Une todo: texto → resultado. |
| `main.py`               | Programa de consola. |
| `tests/`                | Pruebas con pytest. |
| `conftest.py`           | Configuración de pytest: deja importar los módulos de la raíz y ordena la salida de `pytest -v`. |

**El detalle de la asociatividad por la izquierda.** Al quitar la recursión izquierda, G1 queda con
`E' → - T E'`, que es recursiva por la derecha, así que el árbol de derivación se inclina a la derecha
aunque la resta sea por la izquierda. Para calcular bien, el evaluador va acumulando de izquierda a
derecha (en descenso recursivo eso es un `while`). En G2, en cambio, la cola es `E' → - E` y el lado
derecho se resuelve primero.

## Pruebas

```bash
python -m pytest -v
```

Con `-v` las pruebas salen agrupadas por tema, y cada línea dice la gramática, la operación y el
resultado:

```
========================= Calculadora LL(1): pruebas ==========================
182 pruebas encontradas

------------------------------ test_conjuntos.py ------------------------------

Ejemplos de la presentación 05
  ok     Ejemplo     PRIMEROS(A)             { ant, big, cat, cow }
  ok     Ejemplo     SIGUIENTES(C)           { all, cat, cow, $ }  (la diapositiva 16 dice { all, $ })
  ...

----------------------------- test_calculadora.py -----------------------------

Precedencia y asociatividad (analizador con tabla LL(1))
  ok     G1          8 - 3 - 2               ((8 - 3) - 2) = 3
  ok     G1          2 + 3 * 4               (2 + (3 * 4)) = 14
  ...
  ok     G3          2 + 3 * 4               ((2 + 3) * 4) = 20
  ...

============================= 182 passed in 0.62s =============================
```

Este formato lo arma `conftest.py`. Si alguna prueba falla, aparece como `FALLA` y al final pytest
muestra el detalle de siempre. Con `python -m pytest` (sin `-v`) se ve la salida normal de puntos.

Son 182 pruebas y todas pasan:

- **`test_conjuntos.py`**: PRIMEROS, SIGUIENTES y PRED contra los ejemplos de las diapositivas; que
  G1-G4 sean LL(1) y que las originales y la ambigua no; que las transformaciones den las gramáticas finales.
- **`test_calculadora.py`**: agrupación y valor de cada expresión en las cuatro gramáticas, con la tabla
  LL(1) y con descenso recursivo; errores sintácticos, léxicos y división por cero.
- **`test_aleatorio.py`**: 300 expresiones al azar por gramática. La tabla y el descenso recursivo deben
  construir el mismo AST, y G1 debe dar lo mismo que Python (que usa la misma convención).

## Algo que encontramos

En el ejemplo de la diapositiva 16 (`A → B C | ant A all`, `B → big C | ε`, `C → cat | cow`) aparece
`SIGUIENTES(C) = { all, $ }`. El programa da `{ all, cat, cow, $ }`, y creemos que tiene razón: por
`B → big C`, todo lo que sigue a `B` también sigue a `C`, y `SIGUIENTES(B) = { cat, cow }`. La tabla
LL(1) no cambia, porque `C` no tiene producción vacía.

## Limitaciones

- No hay menos unario: `-3` es un error de sintaxis. Se podría agregar con `F → - F`.
- Solo están los cuatro operadores (no hay potencia ni funciones).
- Ante un error, el analizador se detiene en el primero; no hay recuperación en modo pánico.
