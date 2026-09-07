"""Safe, age-aware Plotly visualizations for FastLearn lessons and chat."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Callable

import sqlalchemy as sa


LANGUAGES = ("en", "et", "lt", "es")
TRACE_TYPES = {"bar", "pie", "scatter", "sankey"}
VISUAL_REQUEST = re.compile(
    r"\b(?:chart|diagram|graph|plot|visuali[sz]e|visual(?:ly)?|show me|draw it)\b",
    re.IGNORECASE,
)

INK = "#18332f"
MUTED = "#64748b"
GREEN = "#25756b"
YELLOW = "#f2c94c"
BLUE = "#3b82f6"
CORAL = "#e76f51"
PURPLE = "#7c3aed"
GRID = "#dce8e5"


def _t(en, et, lt, es, lang: str):
    return {"en": en, "et": et, "lt": lt, "es": es}.get(lang, en)


def _layout(*, x_title: str = "", y_title: str = "", **extra) -> dict:
    layout = {
        "height": 340,
        "autosize": True,
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "#fbfdfc",
        "font": {"family": "Inter, system-ui, sans-serif", "size": 13, "color": INK},
        "margin": {"l": 58, "r": 24, "t": 24, "b": 52},
        "hoverlabel": {"bgcolor": "white", "font": {"color": INK}},
        "xaxis": {"title": {"text": x_title}, "gridcolor": GRID, "zerolinecolor": GRID},
        "yaxis": {"title": {"text": y_title}, "gridcolor": GRID, "zerolinecolor": GRID},
        "legend": {"orientation": "h", "y": 1.08, "x": 0},
    }
    layout.update(extra)
    return layout


def _spec(
    source_key: str,
    title: str,
    description: str,
    alt_text: str,
    data: list[dict],
    layout: dict,
    columns: list[str],
    rows: list[list],
    *,
    lang: str = "en",
) -> dict:
    return validate({
        "version": 1,
        "source_key": source_key,
        "renderer": "plotly",
        "title": title,
        "description": description,
        "alt_text": alt_text,
        "audience": {"min_age": 8, "max_age": 16},
        "data": data,
        "layout": layout,
        "config": {
            "responsive": True,
            "displayModeBar": True,
            "displaylogo": False,
            "scrollZoom": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d", "sendDataToCloud"],
        },
        "table": {"columns": columns, "rows": rows},
        "ui": {
            "accessible_data": _t("View accessible data", "Vaata ligipääsetavaid andmeid", "Peržiūrėti prieinamus duomenis", "Ver datos accesibles", lang),
            "load_error": _t(
                "The interactive chart could not load. Use the accessible data below.",
                "Interaktiivset graafikut ei saanud laadida. Kasuta allolevaid ligipääsetavaid andmeid.",
                "Interaktyvios diagramos nepavyko įkelti. Naudokite toliau pateiktus prieinamus duomenis.",
                "No se pudo cargar el gráfico interactivo. Utiliza los datos accesibles de abajo.",
                lang,
            ),
            "interactive_visualization": _t("Interactive visualization", "Interaktiivne visualiseering", "Interaktyvi vizualizacija", "Visualización interactiva", lang),
        },
        "source_note": _t(
            "FastLearn educational illustration",
            "FastLearni õppeillustratsioon",
            "FastLearn mokomoji iliustracija",
            "Ilustración educativa de FastLearn",
            lang,
        ),
    })


def validate(spec: dict) -> dict:
    """Return a JSON-safe visualization after enforcing the browser contract."""
    item = json.loads(json.dumps(spec))
    if item.get("renderer") != "plotly" or item.get("version") != 1:
        raise ValueError("unsupported visualization contract")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,80}", item.get("source_key", "")):
        raise ValueError("invalid visualization source key")
    traces = item.get("data")
    if not isinstance(traces, list) or not 1 <= len(traces) <= 8:
        raise ValueError("visualization must contain one to eight traces")
    if any(trace.get("type", "scatter") not in TRACE_TYPES for trace in traces):
        raise ValueError("unsupported Plotly trace type")
    point_count = sum(
        max(len(trace.get(key, [])) for key in ("x", "y", "labels", "values") if isinstance(trace.get(key), list))
        if any(isinstance(trace.get(key), list) for key in ("x", "y", "labels", "values")) else 0
        for trace in traces
    )
    if point_count > 500:
        raise ValueError("visualization contains too many points")
    if len(json.dumps(item)) > 100_000:
        raise ValueError("visualization payload is too large")
    if not item.get("alt_text") or not item.get("table", {}).get("columns"):
        raise ValueError("accessible description and data table are required")
    return item


def wants_visual(message: str) -> bool:
    return bool(VISUAL_REQUEST.search(message or ""))


def _variables(lang: str) -> dict:
    x = list(range(-4, 6))
    y = [2 * value + 5 for value in x]
    variable = _t("x value", "x väärtus", "x reikšmė", "valor de x", lang)
    expression = _t("2x + 5", "2x + 5", "2x + 5", "2x + 5", lang)
    return _spec(
        "math-variable-pattern",
        _t("A variable changes a pattern", "Muutuja muudab mustrit", "Kintamasis keičia dėsningumą", "Una variable cambia un patrón", lang),
        _t("Hover over the points to see how each x produces one value of 2x + 5.", "Liigu punktidele, et näha, kuidas iga x annab avaldise 2x + 5 väärtuse.", "Užvesk ant taškų ir pamatyk, kaip kiekvienas x sukuria 2x + 5 reikšmę.", "Pasa sobre los puntos para ver cómo cada x produce un valor de 2x + 5.", lang),
        _t("A rising straight line showing y equals two x plus five from x minus four to five.", "Tõusev sirge, mis näitab y võrdub kaks x pluss viis.", "Kylanti tiesė rodo y lygu du x plius penki.", "Una recta ascendente que muestra y igual a dos x más cinco.", lang),
        [{"type": "scatter", "mode": "lines+markers", "name": expression, "x": x, "y": y,
          "line": {"color": GREEN, "width": 4}, "marker": {"color": YELLOW, "size": 9},
          "hovertemplate": "x = %{x}<br>2x + 5 = %{y}<extra></extra>"}],
        _layout(x_title=variable, y_title=expression),
        [variable, expression], [[a, b] for a, b in zip(x, y)], lang=lang,
    )


def _equations(lang: str) -> dict:
    steps = [
        _t("Start", "Algus", "Pradžia", "Inicio", lang),
        _t("Subtract 3", "Lahuta 3", "Atimk 3", "Resta 3", lang),
        _t("Divide by 2", "Jaga 2-ga", "Padalink iš 2", "Divide entre 2", lang),
    ]
    values = [11, 8, 4]
    left = _t("Left side", "Vasak pool", "Kairė pusė", "Lado izquierdo", lang)
    right = _t("Right side", "Parem pool", "Dešinė pusė", "Lado derecho", lang)
    return _spec(
        "math-equation-balance",
        _t("Keep both sides balanced", "Hoia mõlemad pooled tasakaalus", "Išlaikyk abi puses lygias", "Mantén ambos lados equilibrados", lang),
        _t("Each operation changes both sides by the same amount until x = 4.", "Iga tehe muudab mõlemat poolt võrdselt, kuni x = 4.", "Kiekvienas veiksmas vienodai keičia abi puses, kol x = 4.", "Cada operación cambia ambos lados por igual hasta que x = 4.", lang),
        _t("Three paired bars stay equal while an equation is simplified from eleven to four.", "Kolm võrdset tulbapaari näitavad võrrandi lihtsustamist üheteistkümnelt neljale.", "Trys vienodų stulpelių poros rodo lygties supaprastinimą nuo vienuolikos iki keturių.", "Tres pares de barras iguales muestran una ecuación simplificada de once a cuatro.", lang),
        [
            {"type": "bar", "name": left, "x": steps, "y": values, "marker": {"color": GREEN}, "hovertemplate": "%{x}<br>%{y}<extra></extra>"},
            {"type": "bar", "name": right, "x": steps, "y": values, "marker": {"color": YELLOW}, "hovertemplate": "%{x}<br>%{y}<extra></extra>"},
        ],
        _layout(y_title=_t("Value", "Väärtus", "Reikšmė", "Valor", lang), barmode="group"),
        [_t("Step", "Samm", "Žingsnis", "Paso", lang), left, right],
        [[step, value, value] for step, value in zip(steps, values)], lang=lang,
    )


def _geometry(lang: str) -> dict:
    shapes = [_t("Square 4×4", "Ruut 4×4", "Kvadratas 4×4", "Cuadrado 4×4", lang), _t("Rectangle 6×3", "Ristkülik 6×3", "Stačiakampis 6×3", "Rectángulo 6×3", lang), _t("Triangle 3–4–5", "Kolmnurk 3–4–5", "Trikampis 3–4–5", "Triángulo 3–4–5", lang)]
    area = [16, 18, 6]
    perimeter = [16, 18, 12]
    area_name = _t("Area", "Pindala", "Plotas", "Área", lang)
    perimeter_name = _t("Perimeter", "Ümbermõõt", "Perimetras", "Perímetro", lang)
    return _spec(
        "math-area-perimeter",
        _t("Area and perimeter describe different things", "Pindala ja ümbermõõt kirjeldavad erinevaid asju", "Plotas ir perimetras apibūdina skirtingus dalykus", "Área y perímetro describen cosas distintas", lang),
        _t("Compare the space inside each shape with the distance around it.", "Võrdle kujundi sees olevat pinda selle ümber oleva pikkusega.", "Palygink figūros vidinį plotą su atstumu aplink ją.", "Compara el espacio interior de cada figura con la distancia que la rodea.", lang),
        _t("Grouped bars compare area and perimeter for a square, rectangle and right triangle.", "Rühmitatud tulbad võrdlevad ruudu, ristküliku ja täisnurkse kolmnurga pindala ning ümbermõõtu.", "Sugrupuoti stulpeliai lygina kvadrato, stačiakampio ir stačiojo trikampio plotą bei perimetrą.", "Barras agrupadas comparan área y perímetro de un cuadrado, rectángulo y triángulo rectángulo.", lang),
        [
            {"type": "bar", "name": area_name, "x": shapes, "y": area, "marker": {"color": BLUE}},
            {"type": "bar", "name": perimeter_name, "x": shapes, "y": perimeter, "marker": {"color": CORAL}},
        ],
        _layout(y_title=_t("Square or linear units", "Ruut- või pikkusühikud", "Kvadratiniai arba ilgio vienetai", "Unidades cuadradas o lineales", lang), barmode="group"),
        [_t("Shape", "Kujund", "Figūra", "Figura", lang), area_name, perimeter_name],
        [[shape, a, p] for shape, a, p in zip(shapes, area, perimeter)], lang=lang,
    )


def _motion(lang: str) -> dict:
    time = list(range(7))
    velocity = [5 * second for second in time]
    return _spec(
        "physics-velocity-time",
        _t("Constant acceleration changes velocity evenly", "Püsiv kiirendus muudab kiirust ühtlaselt", "Pastovus pagreitis greitį keičia tolygiai", "La aceleración constante cambia la velocidad uniformemente", lang),
        _t("Hover to inspect velocity. The shaded area represents distance travelled.", "Kiiruse vaatamiseks liigu punktidele. Varjutatud ala näitab läbitud teepikkust.", "Užvesk ant taškų greičiui pamatyti. Nuspalvintas plotas rodo nueitą atstumą.", "Pasa sobre los puntos para ver la velocidad. El área sombreada representa la distancia recorrida.", lang),
        _t("A velocity-time line rises from zero to thirty metres per second over six seconds.", "Kiiruse ja aja graafik tõuseb kuue sekundiga nullist kolmekümne meetrini sekundis.", "Greičio ir laiko linija per šešias sekundes kyla nuo nulio iki trisdešimties metrų per sekundę.", "Una línea velocidad-tiempo sube de cero a treinta metros por segundo en seis segundos.", lang),
        [{"type": "scatter", "mode": "lines+markers", "name": _t("Velocity", "Kiirus", "Greitis", "Velocidad", lang), "x": time, "y": velocity,
          "fill": "tozeroy", "fillcolor": "rgba(37,117,107,.18)", "line": {"color": GREEN, "width": 4},
          "marker": {"size": 8, "color": YELLOW}, "hovertemplate": "%{x} s<br>%{y} m/s<extra></extra>"}],
        _layout(x_title=_t("Time (s)", "Aeg (s)", "Laikas (s)", "Tiempo (s)", lang), y_title=_t("Velocity (m/s)", "Kiirus (m/s)", "Greitis (m/s)", "Velocidad (m/s)", lang)),
        [_t("Time (s)", "Aeg (s)", "Laikas (s)", "Tiempo (s)", lang), _t("Velocity (m/s)", "Kiirus (m/s)", "Greitis (m/s)", "Velocidad (m/s)", lang)],
        [[a, b] for a, b in zip(time, velocity)], lang=lang,
    )


def _newton(lang: str) -> dict:
    acceleration = list(range(7))
    masses = [(2, GREEN), (5, PURPLE)]
    traces = [{"type": "scatter", "mode": "lines+markers", "name": f"m = {mass} kg", "x": acceleration,
               "y": [mass * value for value in acceleration], "line": {"color": color, "width": 4},
               "hovertemplate": f"m = {mass} kg<br>a = %{{x}} m/s²<br>F = %{{y}} N<extra></extra>"} for mass, color in masses]
    return _spec(
        "physics-force-mass-acceleration",
        _t("Force grows with mass and acceleration", "Jõud kasvab massi ja kiirendusega", "Jėga didėja kartu su mase ir pagreičiu", "La fuerza crece con la masa y la aceleración", lang),
        _t("Compare F = ma for two objects. The heavier object needs more force for the same acceleration.", "Võrdle F = ma kahe keha puhul. Raskem keha vajab sama kiirenduse jaoks rohkem jõudu.", "Palygink F = ma dviem kūnams. Sunkesniam kūnui tam pačiam pagreičiui reikia daugiau jėgos.", "Compara F = ma para dos objetos. El más pesado necesita más fuerza para la misma aceleración.", lang),
        _t("Two straight lines show force increasing faster for a five-kilogram object than for a two-kilogram object.", "Kaks sirget näitavad, et viiekilogrammise keha jõud kasvab kiiremini kui kahekilogrammisel.", "Dvi tiesės rodo, kad penkių kilogramų kūno jėga didėja greičiau nei dviejų kilogramų kūno.", "Dos rectas muestran que la fuerza aumenta más rápido para un objeto de cinco kilos que para uno de dos.", lang),
        traces,
        _layout(x_title=_t("Acceleration (m/s²)", "Kiirendus (m/s²)", "Pagreitis (m/s²)", "Aceleración (m/s²)", lang), y_title=_t("Force (N)", "Jõud (N)", "Jėga (N)", "Fuerza (N)", lang)),
        [_t("Acceleration", "Kiirendus", "Pagreitis", "Aceleración", lang), "2 kg", "5 kg"],
        [[value, value * 2, value * 5] for value in acceleration], lang=lang,
    )


def _tectonics(lang: str) -> dict:
    x = list(range(11))
    plate_a = [3, 3, 3, 3, 3, 2.8, 2.3, 1.8, 1.4, 1.1, .9]
    plate_b = [3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2]
    return _spec(
        "geography-convergent-boundary",
        _t("At a convergent boundary, one plate can sink", "Koonduval laamapiiril võib üks laam vajuda", "Susiduriančioje riboje viena plokštė gali grimzti", "En un límite convergente, una placa puede hundirse", lang),
        _t("Hover over the profiles and zoom into the subduction zone.", "Liigu profiilidele ja suumi sukeldumisvööndisse.", "Užvesk ant profilių ir priartink subdukcijos zoną.", "Pasa sobre los perfiles y amplía la zona de subducción.", lang),
        _t("A cross-section shows one tectonic plate bending beneath another at a convergent boundary.", "Läbilõige näitab ühe laama paindumist teise alla koonduval piiril.", "Skerspjūvis rodo vieną tektoninę plokštę panyrant po kita susiduriančioje riboje.", "Un corte transversal muestra una placa tectónica doblándose bajo otra en un límite convergente.", lang),
        [
            {"type": "scatter", "mode": "lines", "name": _t("Oceanic plate", "Ookeaniline laam", "Vandenyninė plokštė", "Placa oceánica", lang), "x": x, "y": plate_a, "line": {"color": BLUE, "width": 12}, "hovertemplate": "%{x}, %{y}<extra></extra>"},
            {"type": "scatter", "mode": "lines", "name": _t("Continental plate", "Mandriline laam", "Žemyninė plokštė", "Placa continental", lang), "x": x, "y": plate_b, "line": {"color": CORAL, "width": 16}, "hovertemplate": "%{x}, %{y}<extra></extra>"},
        ],
        _layout(x_title=_t("Cross-section", "Läbilõige", "Skerspjūvis", "Corte transversal", lang), y_title=_t("Relative depth", "Suhteline sügavus", "Santykinis gylis", "Profundidad relativa", lang),
                yaxis={"title": {"text": _t("Relative depth", "Suhteline sügavus", "Santykinis gylis", "Profundidad relativa", lang)}, "range": [0, 5], "gridcolor": GRID},
                annotations=[{"x": 6.2, "y": 2.35, "text": _t("Subduction", "Sukeldumine", "Subdukcija", "Subducción", lang), "showarrow": True, "arrowhead": 2}]),
        [_t("Position", "Asukoht", "Padėtis", "Posición", lang), _t("Oceanic plate", "Ookeaniline laam", "Vandenyninė plokštė", "Placa oceánica", lang), _t("Continental plate", "Mandriline laam", "Žemyninė plokštė", "Placa continental", lang)],
        [[a, b, c] for a, b, c in zip(x, plate_a, plate_b)], lang=lang,
    )


def _urbanisation(lang: str) -> dict:
    labels = [_t("Rural community", "Maakogukond", "Kaimo bendruomenė", "Comunidad rural", lang), _t("Push factors", "Tõuketegurid", "Stūmos veiksniai", "Factores de expulsión", lang), _t("Pull factors", "Tõmbetegurid", "Traukos veiksniai", "Factores de atracción", lang), _t("Growing city", "Kasvav linn", "Augantis miestas", "Ciudad en crecimiento", lang)]
    return _spec(
        "geography-urbanisation-flow",
        _t("Push and pull factors shape urbanisation", "Tõuke- ja tõmbetegurid kujundavad linnastumist", "Stūmos ir traukos veiksniai formuoja urbanizaciją", "Los factores de expulsión y atracción modelan la urbanización", lang),
        _t("Hover over each flow to connect reasons for migration with city growth. Widths are illustrative, not population statistics.", "Liigu voogudele, et seostada rände põhjuseid linna kasvuga. Laiused on näitlikud, mitte rahvastikustatistika.", "Užvesk ant srautų ir susiek migracijos priežastis su miesto augimu. Plotis iliustracinis, ne gyventojų statistika.", "Pasa sobre cada flujo para conectar las razones de migración con el crecimiento urbano. Los anchos son ilustrativos, no estadísticas.", lang),
        _t("A flow diagram connects a rural community through push and pull factors to a growing city.", "Vooskeem ühendab maakogukonna tõuke- ja tõmbetegurite kaudu kasvava linnaga.", "Srautų diagrama sieja kaimo bendruomenę per stūmos ir traukos veiksnius su augančiu miestu.", "Un diagrama de flujo conecta una comunidad rural mediante factores de expulsión y atracción con una ciudad en crecimiento.", lang),
        [{"type": "sankey", "orientation": "h", "node": {"label": labels, "color": [GREEN, CORAL, BLUE, PURPLE], "pad": 22, "thickness": 24},
          "link": {"source": [0, 0, 1, 2], "target": [1, 2, 3, 3], "value": [3, 4, 3, 4], "color": ["rgba(231,111,81,.25)", "rgba(59,130,246,.25)", "rgba(231,111,81,.25)", "rgba(59,130,246,.25)"]}}],
        _layout(x_title="", y_title="", margin={"l": 24, "r": 24, "t": 24, "b": 24}),
        [_t("From", "Kust", "Iš", "Desde", lang), _t("To", "Kuhu", "Į", "Hasta", lang), _t("Illustrative weight", "Näitlik kaal", "Iliustracinis svoris", "Peso ilustrativo", lang)],
        [[labels[0], labels[1], 3], [labels[0], labels[2], 4], [labels[1], labels[3], 3], [labels[2], labels[3], 4]], lang=lang,
    )


def _elements_of_art(lang: str) -> dict:
    labels = [_t("Red", "Punane", "Raudona", "Rojo", lang), _t("Orange", "Oranž", "Oranžinė", "Naranja", lang), _t("Yellow", "Kollane", "Geltona", "Amarillo", lang), _t("Green", "Roheline", "Žalia", "Verde", lang), _t("Blue", "Sinine", "Mėlyna", "Azul", lang), _t("Violet", "Violetne", "Violetinė", "Violeta", lang)]
    colors = ["#ef4444", "#f97316", "#facc15", "#22c55e", "#3b82f6", "#8b5cf6"]
    return _spec(
        "art-colour-wheel",
        _t("Colour relationships form a wheel", "Värvisuhted moodustavad ringi", "Spalvų ryšiai sudaro ratą", "Las relaciones de color forman una rueda", lang),
        _t("Hover over each hue. Opposite colours create strong contrast; neighbours create harmony.", "Liigu igale toonile. Vastandvärvid loovad tugeva kontrasti ja naabrid harmoonia.", "Užvesk ant kiekvieno atspalvio. Priešingos spalvos kuria kontrastą, gretimos – harmoniją.", "Pasa sobre cada tono. Los colores opuestos crean contraste y los vecinos, armonía.", lang),
        _t("A six-part colour wheel shows red, orange, yellow, green, blue and violet around a circle.", "Kuueosaline värviring näitab ringis punast, oranži, kollast, rohelist, sinist ja violetset.", "Šešių dalių spalvų ratas rodo raudoną, oranžinę, geltoną, žalią, mėlyną ir violetinę.", "Una rueda de seis partes muestra rojo, naranja, amarillo, verde, azul y violeta.", lang),
        [{"type": "pie", "labels": labels, "values": [1] * 6, "hole": .42, "sort": False, "direction": "clockwise",
          "marker": {"colors": colors, "line": {"color": "white", "width": 3}}, "textinfo": "label", "hovertemplate": "%{label}<extra></extra>"}],
        _layout(x_title="", y_title="", showlegend=False, margin={"l": 24, "r": 24, "t": 16, "b": 16}),
        [_t("Hue", "Värvitoon", "Atspalvis", "Tono", lang), _t("Neighbouring hues", "Naabertoonid", "Gretimi atspalviai", "Tonos vecinos", lang)],
        [[label, f"{labels[(index - 1) % 6]}, {labels[(index + 1) % 6]}"] for index, label in enumerate(labels)], lang=lang,
    )


def _composition(lang: str) -> dict:
    return _spec(
        "art-rule-of-thirds",
        _t("Composition guides the viewer's eye", "Kompositsioon juhib vaataja pilku", "Kompozicija veda žiūrovo žvilgsnį", "La composición guía la mirada", lang),
        _t("The guide lines divide the frame into thirds. Hover over the focal point and eye path.", "Abijooned jagavad kaadri kolmandikeks. Liigu fookuspunktile ja pilgu teekonnale.", "Pagalbinės linijos dalija kadrą į trečdalius. Užvesk ant židinio ir žvilgsnio kelio.", "Las guías dividen el marco en tercios. Pasa sobre el punto focal y el recorrido visual.", lang),
        _t("A rectangular frame has rule-of-thirds lines, a focal point near an intersection and a three-point eye path.", "Ristkülikukujulisel kaadril on kolmandike jooned, fookuspunkt lõike lähedal ja kolmepunktiline pilgutee.", "Stačiakampiame kadre matomos trečdalių linijos, židinys prie sankirtos ir trijų taškų žvilgsnio kelias.", "Un marco rectangular muestra líneas de tercios, un punto focal cerca de una intersección y un recorrido visual de tres puntos.", lang),
        [{"type": "scatter", "mode": "lines+markers+text", "name": _t("Eye path", "Pilgu teekond", "Žvilgsnio kelias", "Recorrido visual", lang),
          "x": [66, 42, 24], "y": [66, 47, 28], "text": ["1", "2", "3"], "textposition": "top center",
          "line": {"color": GREEN, "width": 3, "dash": "dot"}, "marker": {"size": [18, 13, 10], "color": [YELLOW, BLUE, CORAL]},
          "hovertemplate": _t("Viewing stop %{text}<extra></extra>", "Vaatamispunkt %{text}<extra></extra>", "Žvilgsnio taškas %{text}<extra></extra>", "Parada visual %{text}<extra></extra>", lang)}],
        _layout(x_title="", y_title="", showlegend=False, xaxis={"range": [0, 100], "visible": False}, yaxis={"range": [0, 100], "visible": False},
                shapes=[
                    {"type": "rect", "x0": 2, "x1": 98, "y0": 2, "y1": 98, "line": {"color": INK, "width": 3}},
                    *[{"type": "line", "x0": value, "x1": value, "y0": 2, "y1": 98, "line": {"color": MUTED, "dash": "dash"}} for value in (33, 66)],
                    *[{"type": "line", "x0": 2, "x1": 98, "y0": value, "y1": value, "line": {"color": MUTED, "dash": "dash"}} for value in (33, 66)],
                ]),
        [_t("Viewing order", "Vaatamise järjekord", "Žvilgsnio tvarka", "Orden visual", lang), "x", "y"],
        [[1, 66, 66], [2, 42, 47], [3, 24, 28]], lang=lang,
    )


BUILDERS: dict[tuple[str, str], Callable[[str], dict]] = {
    ("mathematics-foundations", "Variables and Expressions"): _variables,
    ("mathematics-foundations", "Solving Linear Equations"): _equations,
    ("mathematics-foundations", "Shapes, Area, and Perimeter"): _geometry,
    ("physics-essentials", "Speed, Velocity, and Acceleration"): _motion,
    ("physics-essentials", "Newton's Laws of Motion"): _newton,
    ("geography-physical-human", "Plate Tectonics and Earthquakes"): _tectonics,
    ("geography-physical-human", "Urbanisation and Megacities"): _urbanisation,
    ("art-principles", "The Elements of Art"): _elements_of_art,
    ("art-principles", "Composition and Visual Meaning"): _composition,
}


def curated(course_slug: str, lesson_title: str, lang: str = "en") -> list[dict]:
    builder = BUILDERS.get((course_slug, lesson_title))
    if not builder:
        builder = next((candidate for (_slug, title), candidate in BUILDERS.items() if title == lesson_title), None)
    return [builder(lang if lang in LANGUAGES else "en")] if builder else []


def for_lesson_id(conn, lesson_id: int, lang: str = "en", schema: str = "fastlms") -> list[dict]:
    """Return curated visuals, overridden or extended by approved lesson specs."""
    row = conn.execute(sa.text("""
        SELECT c.slug AS course_slug, l.title AS lesson_title
        FROM {schema}.lessons l
        JOIN {schema}.modules m ON m.id = l.module_id
        JOIN {schema}.courses c ON c.id = m.course_id
        WHERE l.id = :lesson
    """.format(schema=schema)), {"lesson": lesson_id}).mappings().first()
    if not row:
        return []
    items = {item["source_key"]: item for item in curated(row["course_slug"], row["lesson_title"], lang)}
    approved = conn.execute(sa.text("""
        SELECT localized_specs FROM {schema}.lesson_visualizations
        WHERE lesson_id = :lesson ORDER BY id
    """.format(schema=schema)), {"lesson": lesson_id}).scalars().all()
    for localized in approved:
        payload = localized if isinstance(localized, dict) else json.loads(localized)
        candidate = payload.get(lang) or payload.get("en")
        if candidate:
            safe = validate(candidate)
            items[safe["source_key"]] = safe
    return [deepcopy(item) for item in items.values()]


def draft_payload(course_slug: str, lesson_title: str) -> dict[str, dict] | None:
    payload = {lang: curated(course_slug, lesson_title, lang) for lang in LANGUAGES}
    return {lang: items[0] for lang, items in payload.items()} if all(payload.values()) else None
