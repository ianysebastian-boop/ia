import pytest
import importlib, sys, types, pathlib


@pytest.fixture
def app():
    dummy_pd = types.SimpleNamespace()

    class DummyFrame:
        def fillna(self, value):
            return self
        def iterrows(self):
            return iter([])

    dummy_pd.read_excel = lambda *a, **k: DummyFrame()
    dummy_pd.notna = lambda x: x is not None
    dummy_pd.isna = lambda x: x is None
    sys.modules['pandas'] = dummy_pd

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    if 'main5' in sys.modules:
        del sys.modules['main5']
    module = importlib.import_module('main5')

    module.especiales_dict = {
        "encaje": {
            "descripcion": "encaje simple",
            "requiere_medidas": [],
            "acciones": "encajar",
            "comentario": "",
            "incremento": 0,
            "incompatible_con": [],
        },
        "zapata": {
            "descripcion": "corte de zapata",
            "requiere_medidas": ["ancho"],
            "acciones": "cortar {ancho}",
            "comentario": "",
            "incremento": 10,
            "incompatible_con": [],
        },
        "incomp": {
            "descripcion": "especial incompatible",
            "requiere_medidas": [],
            "acciones": "",
            "comentario": "",
            "incremento": 0,
            "incompatible_con": ["s", "base"],
        },
    }

    modulos_info = {
        "D1000": {
            "Descripción": "Mueble base",
            "Colocaciones Permitidas": "S",
            "PUNTOS BASE": 100,
            "Tipo": "base",
            "Min S (mm)": 150,
            "Max S (mm)": 200,
            "Ancho (mm)": 600,
            "Profundo (mm)": 500,
        }
    }

    def fake_obtener_mueble(ref):
        return modulos_info.get(ref)

    module.obtener_mueble = fake_obtener_mueble
    return module


def test_analizar_entrada_valida(app):
    ref, ancho, alto, profundo, especiales = app.analizar_entrada(
        "D1000 180/600/500 encaje"
    )
    assert ref == "D1000"
    assert (ancho, alto, profundo) == (600, 180, 500)
    assert especiales == ["encaje"]


def test_analizar_entrada_invalida(app):
    resultado = app.analizar_entrada("D1000 180/600")
    assert resultado[0] == "D1000"
    assert resultado[1] is None


def test_procesar_especial_ok(app):
    salida, inc = app.procesar_especial("zapata", {"ancho": 50}, None, "base")
    assert "✅ Especial 'zapata'" in salida[0]
    assert inc == 10


def test_procesar_especial_falta_medida(app):
    salida, inc = app.procesar_especial("zapata", {}, None, "base")
    assert "requiere medida 'ancho'" in salida[0]
    assert inc == 0


def test_procesar_especial_incompatible(app):
    salida, inc = app.procesar_especial("incomp", {}, "S", "base")
    assert "incompatible" in salida[0]
    assert inc == 0


def test_analizar_mueble_ok(app):
    resultado = app.analizar_mueble("D1000", 600, 180, 500, ["encaje"])
    assert "Mueble base" in resultado
    assert "✅ Especial 'encaje'" in resultado
    assert "🎯 Puntos finales: 100.00" in resultado


def test_analizar_mueble_especial_incompatible(app):
    resultado = app.analizar_mueble("D1000", 600, 180, 500, ["incomp"])
    assert "incompatible" in resultado
