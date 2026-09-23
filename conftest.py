"""Configuración de pytest.

Además de dejar importar los módulos de la raíz, cambia la salida de
`python -m pytest -v`: en vez de una línea por prueba con la ruta completa y el
porcentaje, agrupa las pruebas por tema y muestra gramática, operación y
resultado.

    Precedencia y asociatividad (analizador con tabla LL(1))
      ok  G1          8 - 3 - 2            ((8 - 3) - 2) = 3
      ok  G2          8 - 3 - 2            (8 - (3 - 2)) = 7

Con `-q` o sin opciones se ve la salida normal de pytest.
"""

import sys

import pytest
from _pytest import timing
from _pytest.terminal import TerminalReporter

ANCHO_GRAMATICA = 12
ANCHO_OPERACION = 24

# Primero la teoría, luego la calculadora y al final las pruebas al azar.
ORDEN_DE_ARCHIVOS = ["test_conjuntos", "test_calculadora", "test_aleatorio"]


def pytest_collection_modifyitems(items):
    def posicion(item):
        nombre = item.module.__name__.split(".")[-1]
        return ORDEN_DE_ARCHIVOS.index(nombre) if nombre in ORDEN_DE_ARCHIVOS else len(ORDEN_DE_ARCHIVOS)
    items.sort(key=posicion)  # sort es estable: dentro de cada archivo se respeta el orden


@pytest.fixture
def mostrar(request):
    """Las pruebas lo llaman para decir qué mostrar en su línea."""
    def _mostrar(gramatica="", operacion="", resultado=""):
        request.node.user_properties.append(("mostrar", (gramatica, operacion, resultado)))
    return _mostrar


@pytest.fixture(autouse=True)
def _seccion(request):
    # El título de cada grupo es la primera línea del docstring de la prueba.
    doc = (request.function.__doc__ or request.function.__name__).strip().splitlines()[0]
    request.node.user_properties.append(("seccion", doc))
    request.node.user_properties.append(("modulo", request.module.__name__.split(".")[-1]))


class ReporteOrdenado(TerminalReporter):
    def pytest_sessionstart(self, session):
        # En lugar de platform, cachedir, plugins, etc., solo un título.
        self._session = session
        self._session_start = timing.Instant()
        self.write_sep("=", "Calculadora LL(1): pruebas", bold=True)

    def pytest_collection(self):
        pass  # sin el "collecting ..."

    def report_collect(self, final=False):
        if final:
            n = self._numcollected
            self.write_line(f"{n} prueba encontrada" if n == 1 else f"{n} pruebas encontradas")

    def pytest_runtest_logstart(self, nodeid, location):
        pass  # no imprimir la ruta de cada prueba antes de correrla

    def pytest_runtest_logreport(self, report):
        self._tests_ran = True
        categoria, letra, palabra = self.config.hook.pytest_report_teststatus(report=report, config=self.config)
        self._add_stats(categoria, [report])
        if not letra and not palabra:
            return  # setup o teardown que salió bien
        self._progress_nodeids_reported.add(report.nodeid)

        props = dict(report.user_properties)
        modulo = props.get("modulo", report.nodeid.split("::")[0])
        seccion = props.get("seccion", report.nodeid.split("::")[-1])
        if modulo != getattr(self, "_modulo_actual", None):
            self._modulo_actual = modulo
            self.ensure_newline()
            self._tw.line()
            self._tw.sep("-", modulo + ".py", bold=True)
        if seccion != getattr(self, "_seccion_actual", None):
            self._seccion_actual = seccion
            self.ensure_newline()
            self._tw.line()
            self._tw.line(seccion, cyan=True, bold=True)

        if report.passed:
            estado, color = "ok", {"green": True}
        elif report.skipped:
            estado, color = "salta", {"yellow": True}
        else:
            estado, color = "FALLA", {"red": True, "bold": True}

        gramatica, operacion, resultado = props.get("mostrar", ("", "", ""))
        if not (gramatica or operacion or resultado):
            # La prueba no dijo qué mostrar: se usa el parámetro, si lo tiene.
            nombre = report.nodeid.split("::")[-1]
            operacion = nombre[nombre.find("[") + 1:-1] if "[" in nombre else ""
        if report.failed and report.when != "call":
            resultado = f"error en {report.when}"

        self._tw.write("  ")
        self._tw.write(f"{estado:<5}", **color)
        self._tw.write(f"  {gramatica:<{ANCHO_GRAMATICA}}{operacion:<{ANCHO_OPERACION}}{resultado}".rstrip())
        self._tw.line()
        self.flush()


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    if config.get_verbosity() < 1:
        return
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # para ε y → en la consola de Windows
    reporte = config.pluginmanager.getplugin("terminalreporter")
    if reporte is None or type(reporte) is not TerminalReporter:
        return
    config.pluginmanager.unregister(reporte)
    reporte.__class__ = ReporteOrdenado
    config.pluginmanager.register(reporte, "terminalreporter")
