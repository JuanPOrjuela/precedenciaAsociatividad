"""Fachada: texto de entrada → tokens → árbol (tabla LL(1)) → AST → valor."""

from dataclasses import dataclass

from analizador import analizar, tokenizar
from evaluador import agrupacion, construir_ast, evaluar
from gramaticas import CALCULADORAS


@dataclass(repr=False)
class Resultado:
    arbol: object
    traza: list
    ast: object

    def __repr__(self):
        # Corto a propósito: si una prueba falla, pytest no imprime el árbol entero.
        return f"Resultado({self.agrupacion})"

    @property
    def agrupacion(self):
        return agrupacion(self.ast)

    @property
    def valor(self):
        return evaluar(self.ast)


def calcular(expresion, clave="G1"):
    variante = CALCULADORAS[clave]
    arbol, traza = analizar(variante.gramatica, tokenizar(expresion))
    return Resultado(arbol, traza, construir_ast(arbol))


def calcular_recursivo(expresion, clave="G1"):
    """Lo mismo, pero con el analizador de descenso recursivo."""
    return CALCULADORAS[clave].descenso_recursivo().analizar(tokenizar(expresion))
