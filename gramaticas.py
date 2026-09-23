"""Las gramáticas del taller.

Las cuatro calculadoras salen de cruzar dos decisiones:

                          asociatividad izquierda   asociatividad derecha
    * y / pesan más               G1                        G2
    + y - pesan más               G3                        G4
"""

from dataclasses import dataclass

from descenso_recursivo import DescensoRecursivo
from ll1 import Gramatica


@dataclass
class Variante:
    clave: str
    titulo: str
    texto: str
    niveles: list          # de menor a mayor precedencia
    asociatividad: str
    original: str = ""     # versión "natural" antes de transformarla a LL(1)

    @property
    def gramatica(self):
        return Gramatica.desde_texto(self.texto)

    @property
    def gramatica_original(self):
        return Gramatica.desde_texto(self.original)

    def descenso_recursivo(self):
        return DescensoRecursivo(self.niveles, self.asociatividad)


SUMA = ("+", "-")
PRODUCTO = ("*", "/")

CALCULADORAS = {
    "G1": Variante(
        "G1", "* y / primero, asociatividad izquierda",
        """
        E  -> T E'
        E' -> + T E' | - T E' | ε
        T  -> F T'
        T' -> * F T' | / F T' | ε
        F  -> ( E ) | num
        """,
        [SUMA, PRODUCTO], "izquierda",
        original="""
        E -> E + T | E - T | T
        T -> T * F | T / F | F
        F -> ( E ) | num
        """,
    ),
    "G2": Variante(
        "G2", "* y / primero, asociatividad derecha",
        """
        E  -> T E'
        E' -> + E | - E | ε
        T  -> F T'
        T' -> * T | / T | ε
        F  -> ( E ) | num
        """,
        [SUMA, PRODUCTO], "derecha",
        original="""
        E -> T + E | T - E | T
        T -> F * T | F / T | F
        F -> ( E ) | num
        """,
    ),
    "G3": Variante(
        "G3", "+ y - primero, asociatividad izquierda",
        """
        E  -> T E'
        E' -> * T E' | / T E' | ε
        T  -> F T'
        T' -> + F T' | - F T' | ε
        F  -> ( E ) | num
        """,
        [PRODUCTO, SUMA], "izquierda",
        original="""
        E -> E * T | E / T | T
        T -> T + F | T - F | F
        F -> ( E ) | num
        """,
    ),
    "G4": Variante(
        "G4", "+ y - primero, asociatividad derecha",
        """
        E  -> T E'
        E' -> * E | / E | ε
        T  -> F T'
        T' -> + T | - T | ε
        F  -> ( E ) | num
        """,
        [PRODUCTO, SUMA], "derecha",
        original="""
        E -> T * E | T / E | T
        T -> F + T | F - T | F
        F -> ( E ) | num
        """,
    ),
}

# La gramática "ingenua": un solo nivel. Es ambigua y no dice nada de
# precedencia ni de asociatividad.
AMBIGUA = """
E -> E + E | E - E | E * E | E / E | ( E ) | num
"""

# Ejemplos de las diapositivas, para comprobar que los conjuntos coinciden.
EJEMPLO_CLASE = """
A -> B C | ant A all
B -> big C | ε
C -> cat | cow
"""

ACTIVIDAD_CLASE = """
S -> A B C
A -> uno | ε
B -> dos
C -> tres | ε
"""


def todas_las_gramaticas():
    """Nombre → texto, para la opción --tabla de main.py."""
    gramaticas = {}
    for clave, v in CALCULADORAS.items():
        gramaticas[clave] = v.texto
        gramaticas[clave + "_original"] = v.original
    gramaticas["AMBIGUA"] = AMBIGUA
    gramaticas["EJEMPLO_CLASE"] = EJEMPLO_CLASE
    gramaticas["ACTIVIDAD_CLASE"] = ACTIVIDAD_CLASE
    return gramaticas
