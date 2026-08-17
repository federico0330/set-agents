"""ai/scripts/narration_lint.py -- ADR-0057 / 028-narracion-que-ensena, paquete N1
(`campos-que-obligan`).

Guards the WRITE PATH of `log-narrative`. `PKG-007` is a POINTER: it lets a reader
who already knows the story resume it, but it teaches a reader who does not know the
story nothing. The first version of this guard measured LENGTH (a floor on
characters) and an independent SPEC_CHALLENGE broke it with 8 of 9 crafted attacks --
including the literal case that started this feature, a space instead of a hyphen
("PKG 007") -- by diluting the floor with padding
(docs/specs/028-narracion-que-ensena/spec.md, section "El corpus de ataque").

This version measures PUNTERO DENSITY PER CLAUSE: a ratio, not a count. Padding a
narration with filler clauses does not help, because every filler clause added to
dilute the ratio is itself a clause the guard can search for a pointer in -- and an
empty one just adds to the denominator with nothing in the numerator, which does
not raise the ratio either; the only way to lower density is to write fewer
pointers or say more real content.

Public entry point: `lint_narrative(...) -> list[Violation]`. Empty list = pass.
`render_rejection(violations)` turns that list into the ONE message this guard's own
AC-06 holds itself to: it must name what is missing, why it matters (a sentence of
consequence, not a bare code), and show a corrected, runnable invocation -- a message
that only says `NARRATION_LINT_FAIL learned=missing` fails its own AC.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

try:  # narration_lint.py is imported both as a top-level module (tests, via
    # tests/__init__.py's sys.path insert of ai/scripts/) and from inside
    # feature_state_lib/cli_reporting.py, which lives one package level deeper but
    # shares the same ai/scripts/ sys.path entry -- so a plain top-level import
    # resolves in both callers. The try/except only guards against being imported
    # from a working directory where that path was never inserted (e.g. a stray
    # `python3 narration_lint.py` from elsewhere).
    from feature_state_lib.model import PHASES
except ImportError:  # pragma: no cover - defensive, see comment above
    PHASES = {
        "REQUIREMENTS", "SPEC_DRAFT", "SPEC_CHALLENGE", "USER_APPROVAL",
        "PACKAGE_PLANNING", "PACKAGE_IMPLEMENTATION", "PACKAGE_GATES",
        "PACKAGE_REVIEW", "PACKAGE_REPAIR", "DELTA_REVIEW", "PACKAGE_TESTING",
        "PACKAGE_RUNTIME_QA", "PACKAGE_ACCEPTED", "INTEGRATION", "DONE", "BLOCKED",
    }


@dataclass(frozen=True)
class Violation:
    code: str
    message: str


MILESTONE_RESULTS = {"done", "blocked"}
CLOSE_ONLY_FIELDS = ("milestone", "learned", "next_step", "why", "alternative")

# --- AC-04, "Familias de identificadores" ------------------------------------------
# Cada familia matchea una forma de puntero medida contra las 178 entradas reales de
# narrative-log.jsonl (spec, tabla de familias). El orden de aplicación no importa:
# los spans se funden antes de contar, así que un mismo texto nunca cuenta doble por
# aparecer en dos familias (p.ej. "PKG-007" matchea xx_nnn Y sería candidato de
# flex_sep si tuviera espacio -- nunca las dos a la vez sobre el mismo texto).

_EVIDENCE_FILE_LINE = re.compile(
    r"\b[\w][\w./-]*\.(?:py|sh|md|json|jsonl|toml|ya?ml|ts|tsx|js|ini|cfg)"
    r":\d+(?:-\d+)?\b",
    re.IGNORECASE,
)

# N1-F01: los prefijos de identificador que este repo usa DE VERDAD, medidos sobre
# docs/specs/, docs/adr/ y ai/state/ (`grep -rhoE "\b[A-Z]{2,6}-[0-9]{2,4}\b" | sort |
# uniq -c`): AC 9516, ADR 3159, PKG 2047, SEC 849, SPAWN 416, PR 357, RP 346, DR 236,
# FD 164, SC 154, RF 87, REV 61, DLT 28.
#
# Por qué una lista y no `re.IGNORECASE` sobre `flex_sep`: en minúscula, `[A-Z]{2,6}[ _]
# \d{2,4}` deja de describir identificadores y pasa a describir prosa castellana con
# números -- medido: "corrió 528", "en 300", "el 2026", "de 1256" matchean todas. Esa
# es exactamente la evidencia numérica que ADR-0026 exige y que esta guarda debería
# premiar, no castigar. La mayúscula era el desambiguador; al perderla hay que reponerlo
# con vocabulario.
_IDENT_PREFIXES = (
    "ac", "adr", "pkg", "sec", "spawn", "pr", "rp", "dr", "fd", "sc", "rf", "rev", "dlt",
)

_FAMILY_PATTERNS = {
    # Pn/Dn/Rn pelado: "P1", "D3", "R3" (spec, familia 1, 23 invisibles antes de E-2).
    # N1-F01: en minúscula también -- "d5", "p1". El riesgo de falso positivo en prosa
    # castellana es despreciable con la forma letra+dígitos pegados.
    "pn_dn_rn": re.compile(r"\b[PDR]\d{1,3}\b", re.IGNORECASE),
    # Compuesto letra+numero-letra+numero: "P2-F01", el ejemplo D-2 de la propia spec.
    # N1-F01: case-insensitive; la forma compuesta ya es lo bastante específica.
    "compound": re.compile(r"\b[A-Z]\d{1,3}-[A-Z]\d{1,3}\b", re.IGNORECASE),
    # N1-F01, familia nueva: los mismos identificadores en minúscula o mezclados
    # ("pkg 007" -- B0 literal de Federico --, "adr-0057", "Sec_012"), acotados al
    # vocabulario medido de `_IDENT_PREFIXES` para no tragarse prosa con números.
    # Los spans se funden con los de xx_nnn/flex_sep, así que "PKG-007" nunca cuenta dos veces.
    "lower_ident": re.compile(
        r"\b(?:" + "|".join(_IDENT_PREFIXES) + r")[ _-]?\d{1,4}\b", re.IGNORECASE
    ),
    # XX-nnn: "SC-01", "SEC-007", "FD-010", "PKG-007" (familia 2).
    "xx_nnn": re.compile(r"\b[A-Z]{2,6}-\d{2,4}\b"),
    # Separador flexible: "PKG 007", "PKG_007" -- el caso literal de Federico (B0).
    "flex_sep": re.compile(r"\b[A-Z]{2,6}[ _]\d{2,4}\b"),
    # feature-id NNN-slug: "028-narracion-que-ensena" (familia 4).
    "feature_id": re.compile(r"\b\d{3}-[a-z][a-z0-9]*(?:-[a-z0-9]+)*\b", re.IGNORECASE),
    # Archivo suelto SIN archivo:línea (familia 3): "spec.md", "verify.sh". El
    # archivo:línea (evidencia, ADR-0026) se resta más abajo, nunca cuenta acá.
    # N1-F01: case-insensitive junto con `_EVIDENCE_FILE_LINE` -- si sólo uno de los dos
    # lo fuera, "Spec.MD:12" contaría como puntero en vez de restarse como evidencia.
    "bare_file": re.compile(
        r"\b[\w][\w./-]*\.(?:py|sh|md|json|jsonl|toml|ya?ml|ts|tsx|js|ini|cfg)\b",
        re.IGNORECASE,
    ),
}


def _merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def find_pointers(text: str) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Return (pointer_spans, evidence_spans) over `text`.

    `evidence_spans` are `archivo:línea` citations -- AC-04b: obligatory in `tech`
    (ADR-0026) and therefore explicitly NOT a pointer there. `pointer_spans` never
    overlaps an evidence span: a family match fully inside one is evidence, not a
    bare pointer (e.g. "model.py:199" is evidence; the bare "model.py" a sentence
    later is a pointer).
    """
    if not text:
        return [], []
    evidence_spans = _merge_spans([m.span() for m in _EVIDENCE_FILE_LINE.finditer(text)])
    raw_spans: list[tuple[int, int]] = []
    for pattern in _FAMILY_PATTERNS.values():
        for m in pattern.finditer(text):
            span = m.span()
            if any(ev[0] <= span[0] and span[1] <= ev[1] for ev in evidence_spans):
                continue
            raw_spans.append(span)
    return _merge_spans(raw_spans), evidence_spans


_STRONG_SEP = re.compile(r"[.;:,()]+")
_CONJUNCTIONS = re.compile(r"\b(?:y|o|pero|sino|aunque)\b", re.IGNORECASE)


def _mask(text: str, spans: list[tuple[int, int]], replacement: str = "PTR") -> str:
    if not spans:
        return text
    out = []
    last = 0
    for start, end in spans:
        out.append(text[last:start])
        out.append(replacement)
        last = end
    out.append(text[last:])
    return "".join(out)


_MIN_WORDS_PER_CLAUSE = 2


def clause_count(masked_text: str) -> int:
    """Cláusulas = segmentos entre separadores fuertes (`. ; : , ( )`) o conjunciones
    (`y`, `o`, `pero`, `sino`, `aunque`). Nunca cero -- un texto sin puntuación es UNA
    cláusula, así que su densidad se dispara con el primer puntero.

    N1-F02: sólo cuentan al denominador las cláusulas con al menos
    `_MIN_WORDS_PER_CLAUSE` palabras. El docstring del módulo afirmaba que "agregar
    cláusulas de relleno exige agregar cláusulas reales"; era falso, y se midió:
    `"listo, bien, hecho, avanza, cerrado, PKG-007 reparado, seguimos, todo en orden,
    ok."` daba densidad 0.111 y pasaba limpio, siendo en los hechos sólo "PKG-007
    reparado" envuelto en muletillas. Una palabra suelta no es una cláusula; diluir el
    denominador ahora exige escribir prosa de verdad, que es justamente lo que se pide.
    """
    parts = _STRONG_SEP.split(masked_text)
    clauses: list[str] = []
    for part in parts:
        clauses.extend(_CONJUNCTIONS.split(part))
    substantive = [c for c in (c.strip() for c in clauses) if len(c.split()) >= _MIN_WORDS_PER_CLAUSE]
    return max(len(substantive), 1)


def pointer_density(text: str) -> float:
    """AC-04a. `text`'s own pointers (never its evidence citations) divided by the
    clause count of `text` with BOTH pointers and evidence masked out first -- a
    period inside "spec.md" must never be read as a clause separator, or a single
    bare-filename pointer would inflate its own denominator."""
    if not text:
        return 0.0
    pointer_spans, evidence_spans = find_pointers(text)
    masked = _mask(text, _merge_spans(pointer_spans + evidence_spans))
    return len(pointer_spans) / clause_count(masked)


def strip_pointers_and_evidence(text: str) -> str:
    """AC-04b: content check helper. Removes pointers AND evidence citations
    (replacement="", not "PTR" -- we want to know what is LEFT, not count clauses)."""
    if not text:
        return ""
    pointer_spans, evidence_spans = find_pointers(text)
    return _mask(text, _merge_spans(pointer_spans + evidence_spans), replacement="")


_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")

# Palabras funcionales del castellano (AC-04c). Prototipo escrito a mano para esta
# guarda -- spec, "Sin verificar #4": su cobertura no está medida contra un corpus
# externo, y es un punto de partida a calibrar, no un contrato.
_SPANISH_FUNCTION_WORDS = {
    "de", "la", "el", "en", "y", "a", "que", "los", "del", "se", "las", "por", "un",
    "una", "unos", "unas", "con", "no", "para", "su", "sus", "al", "lo", "como",
    "mas", "más", "o", "pero", "le", "les", "ya", "este", "esta", "estos", "estas",
    "esto", "eso", "ese", "esa", "esos", "esas", "si", "sí", "entre", "cuando",
    "muy", "sin", "sobre", "también", "tambien", "hasta", "hay", "donde", "quien",
    "quienes", "desde", "todo", "todos", "toda", "todas", "nos", "durante", "uno",
    "ni", "contra", "otro", "otra", "otros", "otras", "ante", "ellos", "ellas", "e",
    "mi", "mis", "tu", "tus", "él", "ella", "nosotros", "nosotras", "vosotros",
    "vosotras", "ustedes", "usted", "yo", "qué", "cual", "cuál", "cuales", "poco",
    "algo", "algunos", "algunas", "nada", "mucho", "mucha", "muchos", "muchas",
    "es", "son", "fue", "fueron", "era", "eran", "está", "están", "estaba",
    "estaban", "hice", "hizo", "hicimos", "quedó", "quedaron", "sigue", "siguió",
    "porque", "así", "asi", "aún", "aun", "ya", "tras", "bajo", "según", "segun",
    "cada", "cuyo", "cuya", "mismo", "misma", "mismos", "mismas",
}


def spanish_function_ratio(text: str) -> float:
    words = [w.lower() for w in _WORD.findall(text)]
    if not words:
        return 0.0
    functional = sum(1 for w in words if w in _SPANISH_FUNCTION_WORDS)
    return functional / len(words)


def has_content(text: str) -> bool:
    return bool(_WORD.search(text or ""))


# --- Thresholds (AC-04a/AC-04c/AC-05). Declared, calibratable -- spec "Sin
# verificar #1": only LENGTH has a prior source (the existing render_bitacora.py
# truncation); the rest are a first cut against a nine-attack corpus and a handful
# of good examples, not a validated contract. ------------------------------------
DENSITY_THRESHOLD = 0.35
SPANISH_RATIO_THRESHOLD = 0.25
LONG_FIELD_LIMIT = 400   # client, tech
SHORT_FIELD_LIMIT = 240  # learned, next, why, alternative


def _phase_name_present(text: str) -> bool:
    words = re.findall(r"\b[A-Z][A-Z_]{2,}\b", text or "")
    return any(w in PHASES for w in words)


def _quality_violations(client, tech, learned, next_step, why, alternative) -> list["Violation"]:
    """AC-05 (topes), AC-04a (densidad) y AC-04c (registro Cliente:) -- las reglas que
    hablan de la CALIDAD de la narración, no de si es una apertura o un cierre.

    Extraídas a su propia función por N1-F03: vivían dentro de `lint_narrative`,
    después de la salida temprana de `--result started`, así que una apertura no las
    veía nunca. Se aplican ahora en los dos caminos.
    """
    violations: list[Violation] = []
    # --- AC-05: topes de longitud (nunca piso) ------------------------------------
    for field_name, value, limit in (
        ("client", client, LONG_FIELD_LIMIT),
        ("tech", tech, LONG_FIELD_LIMIT),
        ("learned", learned, SHORT_FIELD_LIMIT),
        ("next", next_step, SHORT_FIELD_LIMIT),
        ("why", why, SHORT_FIELD_LIMIT),
        ("alternative", alternative, SHORT_FIELD_LIMIT),
    ):
        if value and len(value) > limit:
            violations.append(Violation(
                f"LENGTH_EXCEEDED_{field_name.upper()}",
                f"--{field_name} supera los {limit} caracteres ({len(value)}): un "
                "campo así de largo invita a rellenar en vez de resumir con "
                "precisión, y además se trunca a mitad de oración en las "
                "superficies que lo leen (bitácora, digest) -- exactamente el "
                "defecto D-4(d)/D-4(e) que esta feature existe para cerrar.",
            ))

    # --- AC-04a: densidad de punteros por cláusula --------------------------------
    if client:
        density = pointer_density(client)
        if density > DENSITY_THRESHOLD:
            violations.append(Violation(
                "CLIENT_POINTER_DENSITY",
                f"--client tiene demasiados identificadores por cláusula "
                f"(densidad={density:.2f} > {DENSITY_THRESHOLD}): un identificador "
                "ayuda a UBICAR, pero una oración hecha de identificadores no dice "
                "QUÉ pasó -- quien lo lea va a tener que abrir la spec para "
                "traducirlo, que es el defecto exacto que el registro Cliente: "
                "existe para evitar.",
            ))
    if tech:
        density = pointer_density(tech)
        if density > DENSITY_THRESHOLD:
            violations.append(Violation(
                "TECH_POINTER_DENSITY",
                f"--tech tiene demasiados identificadores por cláusula "
                f"(densidad={density:.2f} > {DENSITY_THRESHOLD}): la evidencia "
                "archivo:línea no cuenta acá (ADR-0026 la exige), pero un índice de "
                "identificadores sin prosa alrededor sigue siendo un puntero, no una "
                "explicación -- decí qué pasaba y por qué, con el archivo:línea como "
                "prueba, no como el contenido entero.",
            ))

    # --- AC-04c: registro Cliente:, castellano y sin identificadores --------------
    if client:
        client_pointers, _ = find_pointers(client)
        if client_pointers or _phase_name_present(client):
            violations.append(Violation(
                "CLIENT_HAS_IDENTIFIER",
                "--client contiene un identificador o un nombre de fase interno: el "
                "registro Cliente: es para alguien sin contexto técnico "
                "(orchestrator.md:786-788) -- un identificador ahí no ubica a nadie, "
                "sólo confirma que quien lo escribió no tradujo la narración.",
            ))
        ratio = spanish_function_ratio(client)
        if ratio < SPANISH_RATIO_THRESHOLD:
            violations.append(Violation(
                "CLIENT_NOT_SPANISH",
                f"--client no parece estar en castellano llano (proporción de "
                f"palabras funcionales={ratio:.2f} < {SPANISH_RATIO_THRESHOLD}): el "
                "registro Cliente: existe para que alguien sin contexto técnico "
                "entienda qué cambió -- jerga o inglés crudo ahí lo vacía de "
                "sentido.",
            ))

    return violations


def lint_narrative(
    *,
    client: str,
    tech: str,
    result: str,
    milestone: str | None = None,
    learned: str | None = None,
    next_step: str | None = None,
    why: str | None = None,
    alternative: str | None = None,
    feature_id: str | None = None,
    phase: str | None = None,
    human_decision: bool = False,
) -> list[Violation]:
    """AC-01..AC-08. Pure function, no I/O, no state read (AC-07's own rationale:
    a guard hooked into the single CLI dispatch that consulted live state would read
    PRODUCTION state under test -- the exact ADR-0051 family 027 just repaired).
    Every input the guard needs travels as an explicit argument."""
    violations: list[Violation] = []

    # --- AC-08a: cierre disfrazado de apertura ------------------------------------
    if result == "started":
        disguised = milestone is not None or any([learned, next_step, why, alternative])
        if disguised:
            violations.append(Violation(
                "CLOSE_DISGUISED_AS_START",
                "--result started trae campos que sólo tienen sentido en un cierre "
                "(--milestone/--learned/--next/--why/--alternative): esto es un cierre "
                "disfrazado de apertura, y --result started además desaparece del "
                "digest (cli_reporting.py filtra 'started' de 'Qué quedó listo'), así "
                "que el trabajo real que este cierre describe nunca le llega a nadie. "
                "Usá --result done o --result blocked.",
            ))
        # N1-F03: la salida temprana devolvía CERO violaciones cuando el llamador
        # omitía los flags delatores -- y omitirlos es justamente lo que haría quien
        # quiere esquivar la guarda a propósito, no por descuido. Un cierre completo
        # escrito como `--result started`, con prosa de cierre y sin ningún flag,
        # pasaba limpio y después el digest lo filtraba, así que el trabajo que
        # describía no le llegaba a nadie. Las obligaciones DE CIERRE (milestone,
        # learned/next/why, feature-id) siguen sin aplicar a una apertura legítima,
        # pero la CALIDAD de la narración se exige igual: una apertura hecha de
        # punteros es tan ilegible como un cierre hecho de punteros.
        violations.extend(_quality_violations(client, tech, learned, next_step, why, alternative))
        return violations

    is_milestone_result = result in MILESTONE_RESULTS

    # --- AC-02: --milestone, sin default, obligatorio en done|blocked ------------
    if is_milestone_result and milestone is None:
        violations.append(Violation(
            "MILESTONE_REQUIRED",
            "Falta --milestone yes|no: sin él no se sabe si este cierre es uno de "
            "los hitos que Federico va a leer en STATUS.md/BUENOS-DIAS.md (ADR-0027), "
            "y esta guarda no puede decidir a ciegas si learned/next/why son "
            "obligatorios acá. No se infiere del estado (E-3): declaralo.",
        ))

    is_declared_milestone = milestone == "yes"

    # --- AC-02: learned/next/why obligatorios sólo en hitos -----------------------
    if is_declared_milestone:
        if not learned:
            violations.append(Violation(
                "LEARNED_MISSING",
                "Falta --learned: sin esto, quien lea este cierre no sabe qué "
                "aprendimos que antes no sabíamos -- va a tener que abrir la spec "
                "para enterarse, que es exactamente lo que esta guarda existe para "
                "evitar. Vale el caso honesto \"nada nuevo: confirmó que X\".",
            ))
        if not next_step:
            violations.append(Violation(
                "NEXT_MISSING",
                "Falta --next: sin el próximo paso escrito acá, el lector tiene que "
                "reconstruirlo desde el estado o desde la spec en vez de leerlo.",
            ))
        if not why:
            violations.append(Violation(
                "WHY_MISSING",
                "Falta --why: sin el porqué, --next es un nombre sin razón -- el "
                "lector no puede juzgar si el paso que sigue es el correcto.",
            ))

    # --- AC-03: --alternative, sólo en bloqueo técnico y PACKAGE_PLANNING --------
    alternative_required = (
        (result == "blocked" and not human_decision)
        or (phase == "PACKAGE_PLANNING" and result == "done")
    )
    if alternative_required and not alternative:
        violations.append(Violation(
            "ALTERNATIVE_REQUIRED",
            "Falta --alternative (o --alternative none con su --why): en un "
            "bloqueo técnico o al elegir el próximo paquete en PACKAGE_PLANNING hay "
            "más de un camino posible, y sin la alternativa nombrada el lector no "
            "puede juzgar si la elección fue razonable.",
        ))
    if alternative and alternative.strip().lower() == "none" and not why:
        violations.append(Violation(
            "ALTERNATIVE_NONE_NEEDS_WHY",
            "--alternative none es un valor legal, pero exige un --why que explique "
            "por qué el camino es único -- sin eso, \"none\" es indistinguible de no "
            "haber pensado la alternativa.",
        ))

    # --- AC-07: --feature-id obligatorio al cerrar --------------------------------
    if is_milestone_result and not feature_id:
        violations.append(Violation(
            "FEATURE_ID_REQUIRED",
            "Falta --feature-id: un cierre sin feature-id se registra como "
            "'sin-feature' y no se puede ubicar en ninguna bitácora por feature ni "
            "en el digest -- queda huérfano.",
        ))

    violations.extend(_quality_violations(client, tech, learned, next_step, why, alternative))

    # --- AC-04b: learned/next/why no pueden ser sólo un puntero -------------------
    for field_name, value in (("learned", learned), ("next", next_step), ("why", why)):
        if value and not has_content(strip_pointers_and_evidence(value)):
            violations.append(Violation(
                f"{field_name.upper()}_NO_CONTENT",
                f"--{field_name} queda vacío de contenido una vez que se descuentan "
                "los identificadores y la evidencia archivo:línea: no puede ser "
                "sólo un puntero, tiene que decir algo en prosa que un lector sin "
                "el contexto pueda entender.",
            ))

    # --- AC-05b: contención, reemplaza la regla del 70% (E-11) --------------------
    if why and next_step:
        why_norm, next_norm = why.strip().lower(), next_step.strip().lower()
        if why_norm and next_norm and (why_norm in next_norm or next_norm in why_norm):
            violations.append(Violation(
                "WHY_CONTAINS_NEXT",
                "--why repite --next casi textualmente (uno contiene al otro como "
                "subcadena): un porqué que repite el paso no es un porqué, es el "
                "mismo paso dos veces. Decí qué se rompe, qué queda sin saber, o "
                "qué se paga si no se hace -- \"porque es lo que sigue\" no es un "
                "porqué (spec, sección \"Qué es una narración que enseña\").",
            ))

    return violations


EXAMPLE_INVOCATION = """\
python3 ai/scripts/feature-state.py log-narrative --result done --milestone yes \\
  --client "<qué cambió, en castellano llano, sin identificadores>" \\
  --tech "<qué pasaba, por qué pasaba, con qué archivo:línea se comprueba>" \\
  --learned "<qué sabemos ahora que no sabíamos antes>" \\
  --next "<qué sigue>" \\
  --why "<qué se rompe, qué queda sin saber, o qué se paga si no se hace>" \\
  --feature-id <feature-id>"""


def render_rejection(violations: list[Violation]) -> str:
    """AC-06: the message IS an example of the doctrine it enforces. Every
    violation's own text already names the field and states a consequence (never a
    bare code); this wraps them with a header and the one runnable corrected
    example every rejection ends with."""
    lines = ["NARRATION_LINT_FAIL", ""]
    for v in violations:
        lines.append(f"- [{v.code}] {v.message}")
    lines += [
        "",
        "Ejemplo que sí pasa (adaptá los valores entre <>, no los dejes literales):",
        EXAMPLE_INVOCATION,
    ]
    return "\n".join(lines)
