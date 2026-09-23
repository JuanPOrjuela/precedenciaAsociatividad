"""Analizador léxico y analizador predictivo dirigido por tabla (diapositiva 21)."""

from dataclasses import dataclass, field

from ll1 import EPS, FIN, formatear_produccion


class ErrorLexico(Exception):
    pass


class ErrorSintactico(Exception):
    def __init__(self, mensaje, posicion, encontrado, esperados):
        super().__init__(mensaje)
        self.posicion = posicion
        self.encontrado = encontrado
        self.esperados = esperados


@dataclass
class Token:
    tipo: str      # 'num', '+', '-', '*', '/', '(', ')' o '$'
    lexema: str
    posicion: int


def tokenizar(texto):
    tokens, i = [], 0
    while i < len(texto):
        c = texto[i]
        if c.isspace():
            i += 1
        elif c.isdigit() or (c == "." and texto[i + 1:i + 2].isdigit()):
            inicio = i
            while i < len(texto) and (texto[i].isdigit() or texto[i] == "."):
                i += 1
            lexema = texto[inicio:i]
            if lexema.count(".") > 1:
                raise ErrorLexico(f"número mal formado '{lexema}' en la posición {inicio}")
            tokens.append(Token("num", lexema, inicio))
        elif c in "+-*/()":
            tokens.append(Token(c, c, i))
            i += 1
        else:
            raise ErrorLexico(f"carácter no válido '{c}' en la posición {i}")
    tokens.append(Token(FIN, FIN, len(texto)))
    return tokens


@dataclass
class Nodo:
    """Nodo del árbol de derivación (árbol sintáctico concreto)."""
    simbolo: str
    hijos: list = field(default_factory=list)
    token: Token = None

    def dibujar(self, prefijo="", ultimo=True, raiz=True):
        etiqueta = self.simbolo
        if self.token is not None and self.simbolo == "num":
            etiqueta = f"num ({self.token.lexema})"
        lineas = [etiqueta if raiz else prefijo + ("└── " if ultimo else "├── ") + etiqueta]
        extension = "" if raiz else prefijo + ("    " if ultimo else "│   ")
        for i, hijo in enumerate(self.hijos):
            lineas.append(hijo.dibujar(extension, i == len(self.hijos) - 1, False))
        return "\n".join(lineas)


@dataclass
class PasoTraza:
    pila: str
    entrada: str
    accion: str


def analizar(gramatica, tokens):
    """Algoritmo predictivo con pila. Devuelve (árbol, traza)."""
    if not gramatica.es_ll1():
        raise ValueError("la gramática tiene conflictos LL(1); no se puede usar la tabla")
    tabla = gramatica.tabla
    raiz = Nodo(gramatica.inicial)
    pila = [Nodo(FIN), raiz]           # el tope es el final de la lista
    traza, i = [], 0

    def foto(accion):
        traza.append(PasoTraza(
            " ".join(n.simbolo for n in pila),
            " ".join(t.lexema for t in tokens[i:]),
            accion,
        ))

    while True:
        x, a = pila[-1], tokens[i]
        if x.simbolo == FIN and a.tipo == FIN:
            foto("aceptar")
            return raiz, traza
        if x.simbolo == FIN or gramatica.es_terminal(x.simbolo):
            if x.simbolo != a.tipo:
                foto(f"error: se esperaba '{x.simbolo}'")
                raise ErrorSintactico(
                    f"se esperaba '{x.simbolo}' pero llegó '{a.lexema}' (posición {a.posicion})",
                    a.posicion, a.lexema, [x.simbolo])
            foto(f"coincidir {a.lexema}")
            x.token = a
            pila.pop()
            i += 1
            continue
        celda = tabla.get((x.simbolo, a.tipo))
        if not celda:
            esperados = [t for t in gramatica.columnas() if (x.simbolo, t) in tabla]
            foto(f"error: M[{x.simbolo}, {a.tipo}] vacía")
            raise ErrorSintactico(
                f"token inesperado '{a.lexema}' (posición {a.posicion}); "
                f"se esperaba uno de: {', '.join(esperados)}",
                a.posicion, a.lexema, esperados)
        produccion = celda[0]
        foto(formatear_produccion(produccion))
        pila.pop()
        if produccion[1]:
            x.hijos = [Nodo(s) for s in produccion[1]]
            pila.extend(reversed(x.hijos))  # lado derecho en orden inverso
        else:
            x.hijos = [Nodo(EPS)]
