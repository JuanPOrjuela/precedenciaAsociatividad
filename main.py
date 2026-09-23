"""Calculadora LL(1): prueba las cuatro gramáticas desde la consola.

Ejemplos:
    python main.py "8 - 3 - 2"                 # compara G1..G4
    python main.py "2 + 3 * 4" -g G3 --traza   # traza de la pila
    python main.py "2 + 3 * 4" -g G1 --arbol   # árbol de derivación
    python main.py --tabla G1                  # PRIMEROS, SIGUIENTES, PRED, tabla
    python main.py --tabla G1_original         # muestra los conflictos
    python main.py                             # modo interactivo
"""

import argparse
import sys

from analizador import ErrorLexico, ErrorSintactico
from calculadora import calcular
from evaluador import ErrorEvaluacion, formatear_valor
from gramaticas import CALCULADORAS, todas_las_gramaticas
from ll1 import Gramatica, formatear_produccion, formatear_rhs


def tabla_texto(filas, encabezado):
    anchos = [max(len(str(f[i])) for f in filas + [encabezado]) for i in range(len(encabezado))]
    linea = lambda f: "  ".join(str(c).ljust(w) for c, w in zip(f, anchos)).rstrip()
    separador = "  ".join("-" * w for w in anchos)
    return "\n".join([linea(encabezado), separador] + [linea(f) for f in filas])


def conjunto(g, c):
    return "{ " + ", ".join(g.ordenar(c)) + " }"


def mostrar_conjuntos(nombre, texto):
    g = Gramatica.desde_texto(texto)
    print(f"== Gramática {nombre} ==\n{g}\n")
    filas = [(a, conjunto(g, g.primeros[a]), conjunto(g, g.siguientes[a])) for a in g.no_terminales]
    print(tabla_texto(filas, ("No terminal", "PRIMEROS", "SIGUIENTES")), "\n")
    filas = [(formatear_produccion(p), conjunto(g, g.primeros_de(p[1])), conjunto(g, g.prediccion(p)))
             for p in g.producciones]
    print(tabla_texto(filas, ("Producción", "PRIMEROS(α)", "PRED")), "\n")
    tabla = g.tabla
    filas = []
    for a in g.no_terminales:
        fila = [a]
        for t in g.columnas():
            celda = tabla.get((a, t), [])
            fila.append(" / ".join(formatear_rhs(p[1]) for p in celda) if celda else "–")
        filas.append(fila)
    print("Tabla LL(1) (cada celda es el lado derecho que se aplica):")
    print(tabla_texto(filas, ["M"] + g.columnas()), "\n")
    conflictos = g.conflictos()
    if not conflictos:
        print("[OK] Sin conflictos: la gramática es LL(1).")
    else:
        print(f"[X] {len(conflictos)} celda(s) con conflicto: la gramática NO es LL(1).")
        for a, t, prods in conflictos:
            print(f"   M[{a}, {t}] = " + "  y  ".join(formatear_produccion(p) for p in prods))


def procesar(expresion, claves, traza=False, arbol=False):
    filas = []
    for clave in claves:
        try:
            r = calcular(expresion, clave)
            filas.append((clave, CALCULADORAS[clave].titulo, r.agrupacion, formatear_valor(r.valor)))
        except (ErrorLexico, ErrorSintactico) as e:
            filas.append((clave, CALCULADORAS[clave].titulo, "error", str(e)))
            continue
        except ErrorEvaluacion as e:
            filas.append((clave, CALCULADORAS[clave].titulo, r.agrupacion, f"error: {e}"))
        if traza:
            print(f"\nTraza con {clave}:")
            print(tabla_texto([(p.pila, p.entrada, p.accion) for p in r.traza],
                              ("Pila", "Entrada", "Acción")))
        if arbol:
            print(f"\nÁrbol de derivación con {clave}:\n{r.arbol.dibujar()}")
    print()
    print(tabla_texto(filas, ("", "Gramática", "Agrupación", "Resultado")))


def modo_interactivo(claves):
    print("Calculadora LL(1). Escribe una expresión (o 'salir').")
    while True:
        try:
            linea = input("> ").strip()
        except EOFError:
            break
        if linea.lower() in ("salir", "exit", "q"):
            break
        if linea:
            procesar(linea, claves)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # para ε y → en la consola de Windows
    parser = argparse.ArgumentParser(description="Calculadora con gramáticas LL(1)")
    parser.add_argument("expresion", nargs="?", help="expresión a evaluar, entre comillas")
    parser.add_argument("-g", "--gramatica", choices=list(CALCULADORAS), help="usar solo una gramática")
    parser.add_argument("--traza", action="store_true", help="mostrar la traza de la pila")
    parser.add_argument("--arbol", action="store_true", help="mostrar el árbol de derivación")
    parser.add_argument("--tabla", metavar="NOMBRE", help="mostrar conjuntos y tabla de una gramática")
    parser.add_argument("--listar", action="store_true", help="listar las gramáticas disponibles")
    args = parser.parse_args(argv)

    gramaticas = todas_las_gramaticas()
    if args.listar:
        for nombre, texto in gramaticas.items():
            print(f"== {nombre} ==\n{Gramatica.desde_texto(texto)}\n")
        return
    if args.tabla:
        if args.tabla not in gramaticas:
            parser.error(f"gramática desconocida; opciones: {', '.join(gramaticas)}")
        mostrar_conjuntos(args.tabla, gramaticas[args.tabla])
        return
    claves = [args.gramatica] if args.gramatica else list(CALCULADORAS)
    if args.expresion is None:
        modo_interactivo(claves)
    else:
        procesar(args.expresion, claves, args.traza, args.arbol)


if __name__ == "__main__":
    main()
