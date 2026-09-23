"""Herramientas LL(1) de la clase 05: PRIMEROS, SIGUIENTES, PRED y tabla.

Una gramática se escribe como texto, una regla por línea:

    E  -> T E'
    E' -> + T E' | - T E' | ε

Los no terminales son los que aparecen a la izquierda de una flecha; todo
lo demás es terminal. La cadena vacía se escribe `ε` (o `eps`).
"""

EPS = "ε"
FIN = "$"


class Gramatica:
    def __init__(self, producciones, inicial=None):
        # Cada producción es (A, (X1, X2, ...)); la tupla vacía representa ε.
        self.producciones = [(a, tuple(rhs)) for a, rhs in producciones]
        self.no_terminales = []
        for a, _ in self.producciones:
            if a not in self.no_terminales:
                self.no_terminales.append(a)
        self.inicial = inicial or self.no_terminales[0]
        self.terminales = []
        for _, rhs in self.producciones:
            for x in rhs:
                if x not in self.no_terminales and x not in self.terminales:
                    self.terminales.append(x)
        self._primeros = None
        self._siguientes = None

    # ------------------------------------------------------------------ texto
    @classmethod
    def desde_texto(cls, texto):
        producciones = []
        for linea in texto.strip().splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            izq, der = linea.replace("→", "->").split("->", 1)
            for alternativa in der.split("|"):
                simbolos = alternativa.split()
                if simbolos in (["ε"], ["eps"]):
                    simbolos = []
                producciones.append((izq.strip(), tuple(simbolos)))
        return cls(producciones)

    def __str__(self):
        lineas = []
        ancho = max(len(a) for a in self.no_terminales)
        for a in self.no_terminales:
            alternativas = [formatear_rhs(rhs) for b, rhs in self.producciones if b == a]
            lineas.append(f"{a.ljust(ancho)} → " + " | ".join(alternativas))
        return "\n".join(lineas)

    def es_terminal(self, x):
        return x not in self.no_terminales

    def alternativas(self, a):
        return [p for p in self.producciones if p[0] == a]

    # -------------------------------------------------------------- PRIMEROS
    def primeros_de(self, secuencia):
        """PRIMEROS de una secuencia X1...Xk (reglas de la diapositiva 11)."""
        primeros = self.primeros
        resultado = set()
        for x in secuencia:
            if self.es_terminal(x):
                resultado.add(x)
                return resultado
            resultado |= primeros[x] - {EPS}
            if EPS not in primeros[x]:
                return resultado
        resultado.add(EPS)  # todos los Xi eran anulables (o la secuencia es ε)
        return resultado

    @property
    def primeros(self):
        if self._primeros is None:
            # Punto fijo: se inicia en vacío y se repite hasta que nada cambie.
            self._primeros = {a: set() for a in self.no_terminales}
            cambio = True
            while cambio:
                cambio = False
                for a, rhs in self.producciones:
                    nuevo = self.primeros_de(rhs)
                    if not nuevo <= self._primeros[a]:
                        self._primeros[a] |= nuevo
                        cambio = True
        return self._primeros

    def anulables(self):
        return [a for a in self.no_terminales if EPS in self.primeros[a]]

    # ------------------------------------------------------------ SIGUIENTES
    @property
    def siguientes(self):
        if self._siguientes is None:
            sig = {a: set() for a in self.no_terminales}
            sig[self.inicial].add(FIN)
            cambio = True
            while cambio:
                cambio = False
                for a, rhs in self.producciones:
                    for i, b in enumerate(rhs):
                        if self.es_terminal(b):
                            continue
                        beta = rhs[i + 1:]
                        primeros_beta = self.primeros_de(beta)
                        nuevo = primeros_beta - {EPS}
                        if EPS in primeros_beta:  # beta vacía o anulable
                            nuevo |= sig[a]
                        if not nuevo <= sig[b]:
                            sig[b] |= nuevo
                            cambio = True
            self._siguientes = sig
        return self._siguientes

    # -------------------------------------------------------- PRED y tabla
    def prediccion(self, produccion):
        a, rhs = produccion
        pri = self.primeros_de(rhs)
        if EPS in pri:
            return (pri - {EPS}) | self.siguientes[a]
        return pri

    @property
    def tabla(self):
        """M[A, a] -> lista de producciones (más de una = conflicto LL(1))."""
        tabla = {}
        for p in self.producciones:
            for t in self.prediccion(p):
                tabla.setdefault((p[0], t), []).append(p)
        return tabla

    def conflictos(self):
        return [(a, t, prods) for (a, t), prods in self.tabla.items() if len(prods) > 1]

    def es_ll1(self):
        return not self.conflictos()

    def columnas(self):
        return self.terminales + [FIN]

    def ordenar(self, conjunto):
        orden = self.columnas() + [EPS]
        return sorted(conjunto, key=lambda x: orden.index(x) if x in orden else len(orden))


def formatear_rhs(rhs):
    return " ".join(rhs) if rhs else EPS


def formatear_produccion(p):
    return f"{p[0]} → {formatear_rhs(p[1])}"


# ------------------------------------------------------ transformaciones
def _nombre_nuevo(gramatica, a, usados):
    nombre = a + "'"
    while nombre in gramatica.no_terminales or nombre in usados:
        nombre += "'"
    usados.add(nombre)
    return nombre


def eliminar_recursion_izquierda(gramatica):
    """A → Aα | β  ⇒  A → βA',  A' → αA' | ε   (diapositiva 25)."""
    nuevas, usados = [], set()
    for a in gramatica.no_terminales:
        rhs_a = [rhs for b, rhs in gramatica.producciones if b == a]
        alfas = [rhs[1:] for rhs in rhs_a if rhs and rhs[0] == a]
        betas = [rhs for rhs in rhs_a if not rhs or rhs[0] != a]
        if not alfas:
            nuevas += [(a, rhs) for rhs in rhs_a]
            continue
        a2 = _nombre_nuevo(gramatica, a, usados)
        nuevas += [(a, beta + (a2,)) for beta in betas]
        nuevas += [(a2, alfa + (a2,)) for alfa in alfas]
        nuevas.append((a2, ()))
    return Gramatica(nuevas, gramatica.inicial)


def _prefijo_comun(secuencias):
    prefijo = []
    for simbolos in zip(*secuencias):
        if len(set(simbolos)) != 1:
            break
        prefijo.append(simbolos[0])
    return tuple(prefijo)


def factorizar_izquierda(gramatica):
    """A → αβ1 | αβ2  ⇒  A → αA',  A' → β1 | β2   (diapositiva 25)."""
    nuevas, usados = [], set()
    for a in gramatica.no_terminales:
        rhs_a = [rhs for b, rhs in gramatica.producciones if b == a]
        grupos = {}
        for rhs in rhs_a:
            grupos.setdefault(rhs[:1], []).append(rhs)
        hechos = set()
        pendientes = []
        for rhs in rhs_a:
            clave = rhs[:1]
            grupo = grupos[clave]
            if len(grupo) == 1 or not clave:
                nuevas.append((a, rhs))
            elif clave not in hechos:
                hechos.add(clave)
                alfa = _prefijo_comun(grupo)
                a2 = _nombre_nuevo(gramatica, a, usados)
                nuevas.append((a, alfa + (a2,)))
                pendientes += [(a2, rhs[len(alfa):]) for rhs in grupo]
        nuevas += pendientes
    resultado = Gramatica(nuevas, gramatica.inicial)
    # Un segundo paso por si quedaron prefijos comunes dentro de A'.
    if any(len(g) > 1 for g in _grupos_con_prefijo(resultado)):
        return factorizar_izquierda(resultado)
    return resultado


def _grupos_con_prefijo(gramatica):
    for a in gramatica.no_terminales:
        grupos = {}
        for rhs in (rhs for b, rhs in gramatica.producciones if b == a):
            if rhs:
                grupos.setdefault(rhs[0], []).append(rhs)
        yield from grupos.values()
