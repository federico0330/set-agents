"""ADR-0057 / 028-narracion-que-ensena, paquete N1 (`campos-que-obligan`).

Prueba el CONTRATO DE ESCRITURA: `narration_lint.py` (la guarda pura, sin I/O) y
`log-narrative` (el verbo del CLI que la invoca antes de escribir). Dos niveles:

- Nivel función: `narration_lint.lint_narrative` importado directo -- rápido, y es
  donde vive el corpus de nueve ataques (spec, sección "El corpus de ataque"; la
  spec lo declara NORMATIVO, fijo ahí y no en un scratchpad).
- Nivel CLI: subprocess contra el espejo `PROYECTO/ai/scripts/feature-state.py`
  (mismo patrón que `tests/test_harness.py::FEATURE_STATE` -- la suite ejerce el
  espejo, nunca `ai/scripts/` directo, así que un fix que sólo viva en
  `ai/scripts/` pasa en verde y deja el repo real sin la guarda).

Gates propios de la spec (sección "Gates"):
  1. Toda prueba nueva se demuestra en las dos direcciones -- rojo y verde --, ver
     `AttackCorpusTests` y `GuardCliTests`.
  2. Los nueve ataques del corpus corren en rojo (ocho) y B5 corre en verde,
     declarado como limitación conocida (ver `AttackCorpusTests.test_b5_survives_and_is_declared`).
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import narration_lint as nl

import tests  # noqa: F401 -- side effect: sandboxes HOME/TMPDIR, see tests/__init__.py

ROOT = Path(__file__).resolve().parents[1]
FEATURE_STATE = ROOT / "PROYECTO/ai/scripts/feature-state.py"


def run(*args, check=False):
    return subprocess.run(
        args, cwd=ROOT, env=dict(os.environ), text=True, capture_output=True, check=check,
    )


def log_narrative(*extra, log_file=None):
    with tempfile.TemporaryDirectory() as td:
        target = Path(log_file) if log_file else Path(td) / "narrative-log.jsonl"
        result = run("python3", str(FEATURE_STATE), "log-narrative", *extra,
                      "--log-file", str(target))
        entries = []
        if target.exists():
            entries = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
        return result, entries


# ---------------------------------------------------------------------------------
# El corpus de ataque (spec, "El corpus de ataque"). B0 es TEXTUAL -- pegado tal cual
# la spec lo fija, para que no haya ambigüedad de qué tiene que fallar. B1..B4, B6..B8
# son instancias propias construidas para calzar con la FAMILIA que cada fila describe
# (la spec sólo fija el texto literal de B0; el resto es descripción de familia). B5
# también sale de la spec casi textual (sección "No muerde, y hay que decirlo").
# ---------------------------------------------------------------------------------

GOOD_REFERENCE = dict(
    client="Se corrigió la simulación incompleta para que los tests no dependan de la red.",
    tech=("Faltaba el stub de pnpm y el instalador intentaba calentar Pi por red; ya quedó "
          "simulado (feature_state_lib/cli_lifecycle.py:81), el focal termina en 2,6 segundos."),
    result="done", milestone="yes",
    learned="La falla no era del build sino de una dependencia de red que el entorno de test nunca debió tocar.",
    next_step="Confirmar que el resto de la suite no tiene la misma dependencia oculta.",
    why="Si queda otra simulación incompleta, el próximo cambio va a fallar por la misma causa y nadie va a saber por qué.",
    feature_id="feat-x",
)

B0 = dict(
    client="Hice el fix del paquete siete.",
    tech="PKG 007 reparado, sigue el item A de spec.md.",
    result="done", milestone="yes",
    learned="Que el item A todavía sigue pendiente.",
    next_step="Hacer el item A que quedó de spec.md.",
    why="Porque es lo que sigue en spec.md.",
    feature_id="feat-x",
)

B1 = dict(  # D-2 example verbatim-ish: rango FD-001..FD-010, inglés crudo
    client="Se cerraron los hallazgos FD-001 a FD-010 del ciclo tres, sin novedad para el resto.",
    tech=("R3 complete within authorized budget (spawns 14-16, cycle 3/3): "
          "FD-001..FD-010 closed (6 resolved, 4 resolved-by-approved-exception "
          "per r3-threat-model-amendment)."),
    result="done", milestone="yes",
    learned="FD-001..FD-010 quedaron cerrados según r3-threat-model-amendment.",
    next_step="Seguir con el ciclo cuatro.",
    why="Porque FD-001..FD-010 ya no bloquean el gate de repair.",
    feature_id="feat-x",
)

B2 = dict(  # índice de hallazgos, familia compound P2-F0n
    client="Se revisó el paquete dos y quedaron hallazgos pendientes de reparar.",
    tech=("Review independiente repair_required: P2-F01 descendientes sin frontera, "
          "P2-F02 symlink-padre, P2-F03 estado global al cambiar HOME."),
    result="done", milestone="yes",
    learned="Los tres hallazgos comparten la misma causa: la frontera de escritura no se hereda.",
    next_step="Reparar la herencia de frontera antes de tocar los tres hallazgos por separado.",
    why="Si no se repara la herencia, cualquier hallazgo nuevo va a reabrir la misma clase de bug.",
    feature_id="feat-x",
)

B3 = dict(  # familia XX-nnn
    client="Se revisaron los hallazgos de seguridad de este ciclo.",
    tech="SC-01, SEC-007 y FD-010 quedaron confirmados tras la revisión cruzada.",
    result="done", milestone="yes",
    learned="Los tres hallazgos comparten la misma causa raíz en la validación de entrada.",
    next_step="Reparar la validación de entrada de una sola vez para los tres.",
    why="Repararlos por separado tres veces cuesta más que arreglar la validación una sola vez.",
    feature_id="feat-x",
)

B4 = dict(  # Pn/Dn/Rn pelados
    client="Se cerró el paquete dos y sigue el paquete tres.",
    tech="P2 cerrado, D3 pendiente, R3 no aplica.",
    result="done", milestone="yes",
    learned="D3 quedó pendiente porque falta la evidencia que P2 iba a producir.",
    next_step="Resolver la evidencia faltante antes de abrir P3.",
    why="Si se abre P3 sin esa evidencia, P3 va a repetir la misma pregunta sin poder contestarla.",
    feature_id="feat-x",
)

B5 = dict(  # prosa vaga alrededor de archivos sueltos -- declarada VERDE (spec)
    client="El paquete quedó cerrado siguiendo lo acordado con el equipo.",
    tech="Se revisó la documentación antes de cerrar y el gate quedó verde.",
    result="done", milestone="yes",
    learned="Que la revisión no encontró discrepancias entre los dos documentos.",
    next_step="Cerrar el paquete y avisar al equipo.",
    why="Porque acceptance.md depende de lo que quedó escrito en spec.md.",
    feature_id="feat-x",
)

B6 = dict(  # feature-id NNN-slug
    client="Se cerró la feature del enrutamiento confiable sin deuda pendiente.",
    tech="003-trusted-routing-pi-runtime quedó cerrada tras el ciclo tres, sin hallazgos abiertos.",
    result="done", milestone="yes",
    learned="003-trusted-routing-pi-runtime no tenía deuda pendiente al cerrar.",
    next_step="Archivar 003-trusted-routing-pi-runtime y liberar el slot.",
    why="Archivarla ahora evita que alguien la confunda con trabajo todavía abierto.",
    feature_id="feat-x",
)

B7 = dict(  # next y why idénticos carácter por carácter
    client="Se decidió el siguiente paso del paquete.",
    tech="Se valida el gate antes de avanzar a integración, con verify.sh:1 como evidencia.",
    result="done", milestone="yes",
    learned="El gate estaba verde antes de lo esperado.",
    next_step="Correr el gate de integración",
    why="Correr el gate de integración",
    feature_id="feat-x",
)

B8 = dict(  # cierre disfrazado de apertura
    client="Se cerró el paquete siete sin avisar.",
    tech="El paquete siete quedó listo, con verify.sh:10 como evidencia.",
    result="started",
    milestone="yes",
    learned="El paquete siete no tenía deuda pendiente.",
    next_step="Pasar al paquete ocho.",
    why="Porque el paquete siete ya cumplió su criterio de cierre.",
    feature_id="feat-x",
)

CORPUS_EXPECT_RED = {"B0": B0, "B1": B1, "B2": B2, "B3": B3, "B4": B4, "B6": B6, "B7": B7, "B8": B8}


class AttackCorpusTests(unittest.TestCase):
    """Gate propio de la spec: 'Los nueve ataques del corpus corren en rojo' (ocho) y
    B5 corre en verde, declarado como limitación conocida."""

    def test_good_reference_passes(self):
        violations = nl.lint_narrative(**GOOD_REFERENCE)
        self.assertEqual(violations, [], violations)

    def test_eight_attacks_are_rejected(self):
        for name, attack in CORPUS_EXPECT_RED.items():
            with self.subTest(attack=name):
                violations = nl.lint_narrative(**attack)
                self.assertTrue(violations, f"{name} debía dar rojo y dio verde")

    def test_b5_survives_and_is_declared(self):
        """B5 (spec, 'No muerde'): prosa vaga alrededor de nombres de archivo sueltos
        en `why` pasa las reglas -- densidad no se mide en learned/next/why (sólo en
        client/tech, AC-04a), y el chequeo de contenido de AC-04b sólo exige que quede
        AL MENOS una palabra de prosa tras borrar los punteros, que "Porque ... depende
        de lo que quedó escrito en ..." cumple trivialmente. Limitación conocida,
        declarada acá y en la evidencia del paquete -- no un bug a esconder."""
        violations = nl.lint_narrative(**B5)
        self.assertEqual(violations, [], f"B5 debía sobrevivir (verde) y dio: {violations}")

    def test_b0_literal_from_spec_is_rejected(self):
        """B0 pegado tal cual la spec lo fija (sección 'El corpus de ataque'), el caso
        literal de Federico: 'PKG 007' con espacio en vez de guión."""
        violations = nl.lint_narrative(**B0)
        self.assertTrue(violations)
        # PKG 007 / spec.md sin línea disparan densidad de punteros en --tech.
        self.assertTrue(any(v.code == "TECH_POINTER_DENSITY" for v in violations))


class PointerDensityUnitTests(unittest.TestCase):
    """AC-04a: cociente, no piso. Rellenar con cláusulas de relleno no ayuda -- una
    cláusula vacía sube el denominador pero no baja el numerador de punteros reales."""

    def test_density_is_a_ratio_padding_without_a_new_clause_does_not_dilute_it(self):
        base = "PKG-007 reparado."
        # Same single clause, same single pointer, just more filler WORDS inside it
        # (no comma/period/conjunction to open a new clause) -- a ratio does not
        # reward this kind of padding, exactly the spec's claim ("rellenar no
        # ayuda"): the numerator (1 pointer) and the denominator (1 clause) are both
        # unchanged, so density stays identical.
        padded_same_clause = "PKG-007 reparado igual que antes sin ningún cambio real."
        self.assertGreater(nl.pointer_density(base), nl.DENSITY_THRESHOLD)
        self.assertEqual(nl.pointer_density(base), nl.pointer_density(padded_same_clause))

    def test_a_real_explanatory_clause_lowers_density(self):
        pointer_only = "PKG-007."
        with_real_content = ("PKG-007 tenía un stub de pnpm ausente, el instalador "
                              "intentaba calentar Pi por red y el test fallaba por eso.")
        self.assertGreater(nl.pointer_density(pointer_only), nl.DENSITY_THRESHOLD)
        self.assertLessEqual(nl.pointer_density(with_real_content), nl.DENSITY_THRESHOLD)

    def test_padding_with_contentless_clauses_no_longer_dilutes_density(self):
        """N1-F02: era una limitación declarada -- rellenar con conjunciones o comas SIN
        contenido real inflaba el denominador y bajaba la densidad por debajo del umbral.
        El review independiente de 028 la reprodujo con dos ataques medidos, así que
        `clause_count` pasó a exigir `_MIN_WORDS_PER_CLAUSE` palabras por cláusula.
        Ninguna de las dos formas de relleno diluye ya. (Este test reemplaza a
        `test_known_limitation_conjunction_only_padding_still_dilutes_density`, que
        pedía por escrito ser actualizado si la heurística mejoraba.)"""
        pointer_only = "PKG-007."
        conjunction_padded = "PKG-007 y además y también y encima y more."
        comma_padded = "listo, bien, hecho, avanza, cerrado, PKG-007 reparado, seguimos, ok."
        self.assertGreater(nl.pointer_density(pointer_only), nl.DENSITY_THRESHOLD)
        self.assertGreater(nl.pointer_density(conjunction_padded), nl.DENSITY_THRESHOLD,
                           "relleno por conjunciones no debe diluir la densidad")
        self.assertGreater(nl.pointer_density(comma_padded), nl.DENSITY_THRESHOLD,
                           "relleno por comas no debe diluir la densidad")

    def test_lowercase_identifiers_are_pointers_too(self):
        """N1-F01: las familias se escribieron con `[A-Z]` sin IGNORECASE, así que el
        MISMO texto pasaba o no según la caja -- `pkg 007` (el B0 literal de Federico)
        era invisible y `PKG 007` se detectaba. Medido por el review independiente."""
        for text in ("pkg 007 reparado", "adr-0057 cerrado", "d5-f01 reparado", "Sec_012 abierto"):
            with self.subTest(text=text):
                spans, _ = nl.find_pointers(text)
                self.assertTrue(spans, f"{text!r} debería contar como puntero")

    def test_numeric_prose_is_not_mistaken_for_an_identifier(self):
        """La contracara de N1-F01: bajar la caja a ciegas convertía la evidencia
        numérica que ADR-0026 exige en punteros -- "corrió 528", "en 300", "el 2026" y
        "de 1256" matcheaban todas contra `flex_sep` con IGNORECASE. Por eso la familia
        nueva está acotada al vocabulario medido de `_IDENT_PREFIXES`."""
        for text in ("la suite corrio 528 tests sin fallar",
                     "el gate quedo en 300 milisegundos",
                     "desde el 2026 que esto no se toca",
                     "de 1256 pruebas pasaron todas"):
            with self.subTest(text=text):
                spans, _ = nl.find_pointers(text)
                self.assertEqual(spans, [], f"{text!r} es prosa con números, no un puntero")

    def test_evidence_file_line_does_not_count_as_pointer_in_tech(self):
        text = "El fix está en model.py:199, no en el archivo suelto."
        spans, evidence = nl.find_pointers(text)
        self.assertEqual(spans, [])
        self.assertEqual(len(evidence), 1)

    def test_bare_file_without_line_counts_as_pointer(self):
        spans, evidence = nl.find_pointers("Sigue el item A de spec.md.")
        self.assertEqual(evidence, [])
        self.assertEqual(len(spans), 1)


class Ac02MilestoneTests(unittest.TestCase):
    """AC-02: --milestone yes|no, sin default, obligatorio en done|blocked. learned/
    next/why obligatorios sólo cuando milestone=yes."""

    def test_started_never_requires_milestone(self):
        # N1-F03: `started` ya no sale sin pasar por nada -- las reglas de CALIDAD
        # (densidad, registro Cliente:) se le aplican igual, sólo las obligaciones de
        # CIERRE quedan exentas. Por eso el fixture pasó de "avanzamos" a una frase
        # real: una apertura escrita como la escribiría un humano, que es lo que el
        # test siempre quiso representar.
        violations = nl.lint_narrative(
            client="Arrancamos a mirar por qué la instalación se colgaba en el primer arranque.",
            tech="spawn intra-fase para acotar la causa antes de tocar nada",
            result="started")
        self.assertEqual(violations, [])

    def test_started_still_faces_the_quality_bar(self):
        """N1-F03: la salida temprana de `--result started` devolvía CERO violaciones
        cuando el llamador omitía los flags delatores -- y omitirlos es exactamente lo
        que haría quien esquiva la guarda a propósito. Las obligaciones de CIERRE siguen
        exentas; la calidad de la narración, no."""
        violations = nl.lint_narrative(
            client="Arrancamos con PKG-007 y con SEC-012 del ciclo.",
            tech="pkg 007, sec 012, adr-0057.",
            result="started")
        codes = {v.code for v in violations}
        self.assertIn("CLIENT_HAS_IDENTIFIER", codes)
        self.assertIn("TECH_POINTER_DENSITY", codes)

    def test_done_without_milestone_is_rejected(self):
        violations = nl.lint_narrative(client="listo", tech="listo", result="done",
                                        feature_id="feat-x")
        self.assertTrue(any(v.code == "MILESTONE_REQUIRED" for v in violations))

    def test_blocked_without_milestone_is_rejected(self):
        violations = nl.lint_narrative(client="bloqueado", tech="bloqueado",
                                        result="blocked", feature_id="feat-x",
                                        human_decision=True)
        self.assertTrue(any(v.code == "MILESTONE_REQUIRED" for v in violations))

    def test_milestone_no_does_not_require_learned_next_why(self):
        violations = nl.lint_narrative(
            client="avanzamos con el paquete", tech="spawn intra-fase, render diferido",
            result="done", milestone="no", feature_id="feat-x",
        )
        self.assertEqual(violations, [])

    def test_milestone_yes_requires_learned_next_why(self):
        violations = nl.lint_narrative(
            client="ya podés cobrar con tarjeta", tech="cierre del paquete de pagos, gate verde",
            result="done", milestone="yes", feature_id="feat-n",
        )
        codes = {v.code for v in violations}
        self.assertEqual(codes, {"LEARNED_MISSING", "NEXT_MISSING", "WHY_MISSING"})


class Ac03AlternativeTests(unittest.TestCase):
    """AC-03: --alternative sólo obligatorio en (a) blocked técnico y (b)
    PACKAGE_PLANNING. HUMAN_DECISION_REQUIRED nunca lo exige. 'none' es legal, pero
    exige --why."""

    def test_technical_block_requires_alternative(self):
        violations = nl.lint_narrative(
            client="quedó bloqueado", tech="bloqueado por falta de credencial",
            result="blocked", milestone="yes",
            learned="x", next_step="y", why="z", feature_id="feat-x",
        )
        self.assertTrue(any(v.code == "ALTERNATIVE_REQUIRED" for v in violations))

    def test_human_decision_block_does_not_require_alternative(self):
        violations = nl.lint_narrative(
            client="quedó bloqueado, corresponde tu decisión",
            tech="bloqueado por HUMAN_DECISION_REQUIRED",
            result="blocked", milestone="yes",
            learned="x", next_step="y", why="z", feature_id="feat-x",
            human_decision=True,
        )
        self.assertFalse(any(v.code == "ALTERNATIVE_REQUIRED" for v in violations))

    def test_package_planning_close_requires_alternative(self):
        violations = nl.lint_narrative(
            client="se planificó el próximo paquete", tech="se armó el paquete siguiente",
            result="done", milestone="yes",
            learned="x", next_step="y", why="z", feature_id="feat-x",
            phase="PACKAGE_PLANNING",
        )
        self.assertTrue(any(v.code == "ALTERNATIVE_REQUIRED" for v in violations))

    def test_other_phase_close_does_not_require_alternative(self):
        violations = nl.lint_narrative(
            client="se cerró el paquete", tech="gates verdes",
            result="done", milestone="yes",
            learned="x", next_step="y", why="z", feature_id="feat-x",
            phase="PACKAGE_TESTING",
        )
        self.assertFalse(any(v.code == "ALTERNATIVE_REQUIRED" for v in violations))

    def test_alternative_none_without_why_is_rejected(self):
        violations = nl.lint_narrative(
            client="se planificó el próximo paquete", tech="se armó el paquete siguiente",
            result="done", milestone="yes",
            learned="x", next_step="y", why="",
            alternative="none", feature_id="feat-x", phase="PACKAGE_PLANNING",
        )
        self.assertTrue(any(v.code == "ALTERNATIVE_NONE_NEEDS_WHY" for v in violations))

    def test_alternative_none_with_why_is_legal(self):
        violations = nl.lint_narrative(
            client="se planificó el próximo paquete", tech="se armó el paquete siguiente",
            result="done", milestone="yes",
            learned="no había otra opción real",
            next_step="arrancar el paquete único que queda",
            why="es el único paquete que no tiene dependencias pendientes",
            alternative="none", feature_id="feat-x", phase="PACKAGE_PLANNING",
        )
        self.assertEqual(violations, [])


class Ac04cClientTests(unittest.TestCase):
    """AC-04c: registro Cliente: en castellano, cero punteros, cero nombres de fase."""

    def test_client_with_identifier_is_rejected(self):
        violations = nl.lint_narrative(
            client="El paquete PKG-007 quedó listo.", tech="cierre normal",
            result="done", milestone="no", feature_id="feat-x",
        )
        self.assertTrue(any(v.code == "CLIENT_HAS_IDENTIFIER" for v in violations))

    def test_client_with_phase_name_is_rejected(self):
        violations = nl.lint_narrative(
            client="Ya estamos en PACKAGE_REVIEW y avanza bien.", tech="cierre normal",
            result="done", milestone="no", feature_id="feat-x",
        )
        self.assertTrue(any(v.code == "CLIENT_HAS_IDENTIFIER" for v in violations))

    def test_client_in_raw_english_is_rejected(self):
        violations = nl.lint_narrative(
            client="The package is now ready for the next review cycle.",
            tech="cierre normal",
            result="done", milestone="no", feature_id="feat-x",
        )
        self.assertTrue(any(v.code == "CLIENT_NOT_SPANISH" for v in violations))

    def test_tech_english_prose_is_legitimate(self):
        # AC-04c aplica sólo a client -- prosa técnica en inglés en tech es legítima.
        violations = nl.lint_narrative(
            client="Ya se puede usar la función nueva sin problemas.",
            tech="The missing pnpm stub made the installer reach the network before the fix.",
            result="done", milestone="no", feature_id="feat-x",
        )
        self.assertFalse(any(v.code in ("CLIENT_NOT_SPANISH", "CLIENT_HAS_IDENTIFIER") for v in violations))


class Ac04bContentTests(unittest.TestCase):
    """AC-04b: learned/next/why no pueden ser sólo un puntero."""

    def test_why_that_is_only_a_pointer_is_rejected(self):
        violations = nl.lint_narrative(
            client="se corrigió el problema", tech="ver el archivo",
            result="done", milestone="yes",
            learned="algo nuevo", next_step="seguir",
            why="spec.md",
            feature_id="feat-x",
        )
        self.assertTrue(any(v.code == "WHY_NO_CONTENT" for v in violations))

    def test_why_that_is_a_pointer_plus_evidence_line_is_still_rejected(self):
        violations = nl.lint_narrative(
            client="se corrigió el problema", tech="ver el archivo con evidencia",
            result="done", milestone="yes",
            learned="algo nuevo", next_step="seguir",
            why="verify.sh:12",
            feature_id="feat-x",
        )
        self.assertTrue(any(v.code == "WHY_NO_CONTENT" for v in violations))


class Ac05LengthTests(unittest.TestCase):
    """AC-05: sólo topes, ningún piso. client/tech 400, resto 240."""

    def test_client_over_400_is_rejected(self):
        violations = nl.lint_narrative(
            client="x" * 401, tech="ok", result="done", milestone="no", feature_id="feat-x",
        )
        self.assertTrue(any(v.code == "LENGTH_EXCEEDED_CLIENT" for v in violations))

    def test_why_over_240_is_rejected(self):
        violations = nl.lint_narrative(
            client="ok", tech="ok", result="done", milestone="yes",
            learned="ok", next_step="ok", why="x" * 241, feature_id="feat-x",
        )
        self.assertTrue(any(v.code == "LENGTH_EXCEEDED_WHY" for v in violations))

    def test_no_floor_a_two_word_field_is_never_rejected_for_being_short(self):
        violations = nl.lint_narrative(
            client="listo ya", tech="gate verde", result="done", milestone="no",
            feature_id="feat-x",
        )
        self.assertFalse(any(v.code.startswith("LENGTH_") for v in violations))


class Ac05bContentionTests(unittest.TestCase):
    """AC-05b: contención reemplaza la regla del 70% (E-11) -- why no puede contener a
    next como subcadena ni al revés."""

    def test_identical_next_and_why_is_rejected(self):
        violations = nl.lint_narrative(**B7)
        self.assertTrue(any(v.code == "WHY_CONTAINS_NEXT" for v in violations))

    def test_synonym_paraphrase_that_does_not_contain_the_substring_is_not_flagged(self):
        violations = nl.lint_narrative(
            client="se avanzó al siguiente paso", tech="gate verde, avanza el paquete",
            result="done", milestone="yes",
            learned="el gate pasó antes de lo esperado",
            next_step="correr el gate de integración",
            why="si no se corre ahora, el próximo repair batch va a chocar con un estado a medio escribir",
            feature_id="feat-x",
        )
        self.assertFalse(any(v.code == "WHY_CONTAINS_NEXT" for v in violations))


class Ac06MessageTests(unittest.TestCase):
    """AC-06: el mensaje de rechazo ES un ejemplo de la doctrina. Prueba textual: el
    texto contiene el nombre del campo, una oración de consecuencia y un ejemplo
    ejecutable -- 'un error que sólo diga NARRATION_LINT_FAIL learned=missing
    reprueba su propio AC'."""

    def test_message_names_field_explains_consequence_and_shows_runnable_example(self):
        violations = nl.lint_narrative(
            client="listo", tech="listo", result="done", milestone="yes", feature_id="feat-x",
        )
        message = nl.render_rejection(violations)
        self.assertIn("--learned", message)
        self.assertIn("--next", message)
        self.assertIn("--why", message)
        # "por qué importa" -- cada violación es una oración de consecuencia, no un código pelado.
        self.assertIn("no sabe", message)
        # invocación corregida, ejecutable
        self.assertIn("python3 ai/scripts/feature-state.py log-narrative", message)
        self.assertIn("--feature-id", message)
        # el propio AC-06 nombra el anti-ejemplo que reprueba
        self.assertNotEqual(message.strip(), "NARRATION_LINT_FAIL learned=missing")


class Ac07FeatureIdTests(unittest.TestCase):
    """AC-07: --feature-id obligatorio al cerrar (result done|blocked)."""

    def test_close_without_feature_id_is_rejected(self):
        violations = nl.lint_narrative(client="listo", tech="listo", result="done",
                                        milestone="no")
        self.assertTrue(any(v.code == "FEATURE_ID_REQUIRED" for v in violations))

    def test_started_without_feature_id_is_not_rejected(self):
        violations = nl.lint_narrative(client="avanzamos", tech="spawn intra-fase",
                                        result="started")
        self.assertFalse(any(v.code == "FEATURE_ID_REQUIRED" for v in violations))


class Ac08CloseDisguisedAsStartTests(unittest.TestCase):
    """AC-08 (E-9): --result started con campos de cierre es un bypass de la guarda
    entera -- --result started ni siquiera aparece en el digest."""

    def test_started_with_learned_is_rejected(self):
        violations = nl.lint_narrative(
            client="avanzamos", tech="avanzamos",
            result="started", learned="algo que sólo tiene sentido en un cierre",
        )
        self.assertTrue(any(v.code == "CLOSE_DISGUISED_AS_START" for v in violations))

    def test_plain_started_is_never_flagged_as_disguised(self):
        violations = nl.lint_narrative(client="avanzamos", tech="spawn intra-fase",
                                        result="started")
        self.assertFalse(any(v.code == "CLOSE_DISGUISED_AS_START" for v in violations))


class GuardCliTests(unittest.TestCase):
    """Nivel CLI, contra el espejo PROYECTO/ai/scripts/feature-state.py -- el mismo
    binario que ejerce tests/test_harness.py (FEATURE_STATE). Demuestra las DOS
    DIRECCIONES en vivo: la narración pobre falla el proceso real, la buena escribe
    la entrada real."""

    def test_poor_narration_is_rejected_by_the_real_cli(self):
        result, entries = log_narrative(
            "--result", "done", "--milestone", "yes",
            "--client", B0["client"], "--tech", B0["tech"],
            "--learned", B0["learned"], "--next", B0["next_step"], "--why", B0["why"],
            "--feature-id", "feat-x",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NARRATION_LINT_FAIL", result.stderr)
        self.assertIn("--tech", result.stderr)
        self.assertEqual(entries, [], "una narración rechazada no debe llegar al log")

    def test_good_narration_is_written_by_the_real_cli(self):
        result, entries = log_narrative(
            "--result", "done", "--milestone", "yes",
            "--client", GOOD_REFERENCE["client"], "--tech", GOOD_REFERENCE["tech"],
            "--learned", GOOD_REFERENCE["learned"], "--next", GOOD_REFERENCE["next_step"],
            "--why", GOOD_REFERENCE["why"], "--feature-id", "feat-x",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["client"], GOOD_REFERENCE["client"])
        self.assertEqual(entries[0]["milestone"], "yes")
        self.assertEqual(entries[0]["why"], GOOD_REFERENCE["why"])

    def test_legacy_entry_without_new_keys_still_absent_not_none(self):
        """AC-01: compatibilidad por AUSENCIA de clave, nunca por valor centinela.
        Una entrada sin milestone/learned/next/why/alternative (como las 178
        preexistentes) nunca debe verse en el log recién escrito con esas claves en
        None/"-" -- sólo faltan del todo cuando el llamador no las pasó."""
        result, entries = log_narrative(
            "--result", "started",
            "--client", "Arrancamos a mirar por qué la instalación se colgaba en el primer arranque.",
            "--tech", "spawn intra-fase para acotar la causa antes de tocar nada",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        entry = entries[0]
        for key in ("milestone", "learned", "next", "why", "alternative"):
            self.assertNotIn(key, entry, f"{key} no debería existir en una entrada legacy")

    def test_milestone_without_default_is_required_at_close_by_the_real_cli(self):
        result, entries = log_narrative(
            "--result", "done", "--client", "listo", "--tech", "listo",
            "--feature-id", "feat-x",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MILESTONE_REQUIRED", result.stderr)
        self.assertEqual(entries, [])

    def test_mirror_parity_ai_scripts_vs_proyecto(self):
        """El espejo es obligatorio (encargo): ambas copias de narration_lint.py y
        feature-state.py deben coincidir byte a byte."""
        top = ROOT / "ai/scripts/narration_lint.py"
        mirror = ROOT / "PROYECTO/ai/scripts/narration_lint.py"
        self.assertEqual(top.read_bytes(), mirror.read_bytes())
        top_fs = ROOT / "ai/scripts/feature-state.py"
        mirror_fs = ROOT / "PROYECTO/ai/scripts/feature-state.py"
        self.assertEqual(top_fs.read_bytes(), mirror_fs.read_bytes())
        top_cr = ROOT / "ai/scripts/feature_state_lib/cli_reporting.py"
        mirror_cr = ROOT / "PROYECTO/ai/scripts/feature_state_lib/cli_reporting.py"
        self.assertEqual(top_cr.read_bytes(), mirror_cr.read_bytes())


if __name__ == "__main__":
    unittest.main()
