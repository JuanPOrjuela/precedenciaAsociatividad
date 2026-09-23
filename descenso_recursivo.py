"""Descenso recursivo (diapositiva 23): un procedimiento por nivel de la gramática.

Sirve como segunda implementación para comparar contra la tabla LL(1).
`niveles` va de la precedencia más baja a la más alta, por ejemplo
[("+", "-"), ("*", "/")] para la precedencia de siempre.
"""

from analizador import ErrorSintactico
from evaluador import Bin, Num


class DescensoRecursivo:
    def __init__(self, niveles, asociatividad):
        assert asociatividad in ("izquierda", "derecha")
        self.niveles = niveles
        self.asociatividad = asociatividad

    def analizar(self, tokens):
        self.tokens, self.i = tokens, 0
        ast = self._nivel(0)
        if self.actual.tipo != "$":
            self._error(self._esperados_despues())
        return ast

    @property
    def actual(self):
        return self.tokens[self.i]

    def _coincidir(self, tipo):
        if self.actual.tipo != tipo:
            self._error([tipo])
        token = self.actual
        self.i += 1
        return token

    def _error(self, esperados):
        a = self.actual
        raise ErrorSintactico(
            f"token inesperado '{a.lexema}' (posición {a.posicion}); "
            f"se esperaba uno de: {', '.join(esperados)}",
            a.posicion, a.lexema, esperados)

    def _esperados_despues(self):
        return [op for nivel in self.niveles for op in nivel] + [")", "$"]

    def _nivel(self, k):
        if k == len(self.niveles):
            return self._factor()
        izquierda = self._nivel(k + 1)
        if self.asociatividad == "izquierda":
            # E → T E',  E' → op T E' | ε   se vuelve un ciclo que acumula.
            while self.actual.tipo in self.niveles[k]:
                op = self._coincidir(self.actual.tipo).tipo
                izquierda = Bin(op, izquierda, self._nivel(k + 1))
            return izquierda
        # E → T E',  E' → op E | ε   : el lado derecho vuelve a llamar al mismo nivel.
        if self.actual.tipo in self.niveles[k]:
            op = self._coincidir(self.actual.tipo).tipo
            return Bin(op, izquierda, self._nivel(k))
        return izquierda

    def _factor(self):
        if self.actual.tipo == "num":
            return Num(self._coincidir("num").lexema)
        if self.actual.tipo == "(":
            self._coincidir("(")
            ast = self._nivel(0)
            self._coincidir(")")
            return ast
        self._error(["num", "("])
