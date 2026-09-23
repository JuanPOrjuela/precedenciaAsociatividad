"""Del árbol de derivación al árbol de sintaxis abstracta (AST) y su valor.

La asociatividad se decide por la forma de la "cola" (el no terminal primado):

    E' → + T E' | ε    (3 hijos)  → se acumula hacia la izquierda: ((a - b) - c)
    E' → + E    | ε    (2 hijos)  → el resto se agrupa a la derecha: (a - (b - c))
"""

from dataclasses import dataclass
from fractions import Fraction

from ll1 import EPS


class ErrorEvaluacion(Exception):
    pass


@dataclass
class Num:
    lexema: str

    @property
    def valor(self):
        return Fraction(self.lexema)


@dataclass
class Bin:
    op: str
    izq: object
    der: object


def construir_ast(nodo):
    hijos = nodo.hijos
    if len(hijos) == 1 and hijos[0].simbolo == "num":          # F → num
        return Num(hijos[0].token.lexema)
    if len(hijos) == 3 and hijos[0].simbolo == "(":            # F → ( E )
        return construir_ast(hijos[1])
    if len(hijos) == 2:                                        # X → Y X'
        return _cola(construir_ast(hijos[0]), hijos[1])
    raise ValueError(f"forma de nodo no reconocida: {nodo.simbolo}")


def _cola(izquierda, cola):
    hijos = cola.hijos
    if len(hijos) == 1 and hijos[0].simbolo == EPS:            # X' → ε
        return izquierda
    op = hijos[0].simbolo
    if len(hijos) == 3:                                        # X' → op Y X'
        return _cola(Bin(op, izquierda, construir_ast(hijos[1])), hijos[2])
    if len(hijos) == 2:                                        # X' → op X
        return Bin(op, izquierda, construir_ast(hijos[1]))
    raise ValueError(f"forma de cola no reconocida: {cola.simbolo}")


def evaluar(ast):
    if isinstance(ast, Num):
        return ast.valor
    a, b = evaluar(ast.izq), evaluar(ast.der)
    if ast.op == "+":
        return a + b
    if ast.op == "-":
        return a - b
    if ast.op == "*":
        return a * b
    if b == 0:
        raise ErrorEvaluacion("división por cero")
    return a / b


def agrupacion(ast):
    """Escribe el AST con todos los paréntesis: muestra cómo quedó agrupado."""
    if isinstance(ast, Num):
        return ast.lexema
    return f"({agrupacion(ast.izq)} {ast.op} {agrupacion(ast.der)})"


def formatear_valor(valor):
    if valor.denominator == 1:
        return str(valor.numerator)
    decimal = f"{float(valor):.6f}".rstrip("0").rstrip(".")
    return f"{valor} ≈ {decimal}"
