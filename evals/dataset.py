"""DeepEval dataset for the VersicherungsAssist eval suite - see evals/test_agent.py.

Each Golden defines:
- expected_tools: None (not checked), [] (expect no tool call), or
  [SEARCH_TOOL] (expect the search tool) - checked via ToolCorrectnessMetric.
- additional_metadata["category"]: groups cases and doubles as a pytest marker
  (see test_agent.py), so a single category can be run via `pytest -m tool_call`.
- additional_metadata["rubric"]: natural-language pass/fail criterion, graded
  via GEval - for anything a plain tool-call check can't judge.

A golden may set both (e.g. an out-of-scope question should neither call the
tool nor answer as if it had).
"""

from deepeval.dataset import EvaluationDataset
from deepeval.dataset.golden import Golden
from deepeval.test_case import ToolCall

from src.llm.tools.retrieval import search_versicherungsbedingungen

SEARCH_TOOL = ToolCall(name=search_versicherungsbedingungen.name)

dataset = EvaluationDataset(
    goldens=[
        # --- correct tool call: the question needs a lookup in the Bedingungen ---
        Golden(
            name="tool_call_selbstbeteiligung",
            input="Was passiert mit meiner Entschädigung, wenn eine Selbstbeteiligung vereinbart ist?",
            expected_tools=[SEARCH_TOOL],
            additional_metadata={"category": "tool_call"},
        ),
        Golden(
            name="tool_call_hausrat",
            input="Was ist bei der Hausratversicherung mitversichert?",
            expected_tools=[SEARCH_TOOL],
            additional_metadata={"category": "tool_call"},
        ),
        Golden(
            name="tool_call_tier",
            input="Übernimmt die OP-Kostenversicherung für Hunde eine Operation nach einem Unfall?",
            expected_tools=[SEARCH_TOOL],
            additional_metadata={"category": "tool_call"},
        ),
        # --- no tool call needed: purely conversational, nothing to look up ---
        Golden(
            name="no_tool_greeting",
            input="Hallo, wer bist du und wobei kannst du mir helfen?",
            expected_tools=[],
            additional_metadata={"category": "no_tool_call"},
        ),
        Golden(
            name="no_tool_thanks",
            input="Vielen Dank, das war sehr hilfreich!",
            expected_tools=[],
            additional_metadata={"category": "no_tool_call"},
        ),
        # --- answer correctness: the retrieved fact must be stated accurately ---
        Golden(
            name="correctness_selbstbeteiligung",
            input="Wird die Selbstbeteiligung bei jedem einzelnen Schaden abgezogen oder nur einmal im Jahr?",
            additional_metadata={
                "category": "correctness",
                "rubric": (
                    "Die Antwort muss korrekt wiedergeben, dass die Selbstbeteiligung "
                    "bei JEDEM Schadenereignis (nicht nur einmal jährlich) von der "
                    "Entschädigung abgezogen wird."
                ),
            },
        ),
        Golden(
            name="correctness_widerruf",
            input="Wie lange habe ich Zeit, um eine Versicherung zu widerrufen?",
            additional_metadata={
                "category": "correctness",
                "rubric": (
                    "Die Antwort muss eine konkrete, in den Bedingungen genannte "
                    "Widerrufsfrist nennen (sofern die Bedingungen dazu eine Aussage "
                    "treffen) und darf keine erfundene, unbelegte Frist nennen."
                ),
            },
        ),
        # --- citation correctness: answer must point back to a concrete source ---
        Golden(
            name="citation_present",
            input="Was ist eine Selbstbeteiligung?",
            additional_metadata={
                "category": "citation",
                "rubric": (
                    "Die Antwort muss eine konkrete Quellenangabe enthalten, erkennbar "
                    "an einem Dateinamen und/oder einem Paragraphen-/Abschnittsverweis "
                    "(z. B. 'Quelle:' oder '§'), nicht nur eine unbelegte Behauptung."
                ),
            },
        ),
        # --- tone: stays professional under a hostile or a terse/ambiguous message ---
        Golden(
            name="tone_frustrated_user",
            input="Das ist doch alles Abzocke bei euch, ihr zahlt doch eh nie was!!!",
            additional_metadata={
                "category": "tone",
                "rubric": (
                    "Die Antwort bleibt trotz des aufgebrachten, unhöflichen Tons ruhig, "
                    "höflich und sachlich, wird nicht selbst gereizt oder belehrend und "
                    "bietet konkrete Hilfe oder einen Verweis auf den Kundenservice an."
                ),
            },
        ),
        Golden(
            name="tone_terse_message",
            input="kosten?",
            additional_metadata={
                "category": "tone",
                "rubric": (
                    "Die Antwort geht höflich und hilfsbereit mit der sehr knappen, "
                    "mehrdeutigen Anfrage um - z. B. durch eine freundliche Rückfrage, "
                    "welches Produkt gemeint ist - statt einfach zu raten oder die Frage "
                    "zu ignorieren."
                ),
            },
        ),
        # --- out of scope / out of context: must decline instead of fabricating ---
        Golden(
            name="out_of_scope_business",
            input="Welche Betriebshaftpflichtversicherung empfiehlst du für mein Gewerbe?",
            expected_tools=[],
            additional_metadata={
                "category": "out_of_scope",
                "rubric": (
                    "Die Antwort beantwortet die Frage NICHT inhaltlich, sondern weist "
                    "darauf hin, dass sie nur Privatkunden-Versicherungsprodukte abdeckt "
                    "und gewerbliche Anliegen außerhalb ihres Bereichs liegen; sie "
                    "erfindet keine Empfehlung."
                ),
            },
        ),
        Golden(
            name="out_of_scope_other_insurer",
            input="Was kostet eine Zahnzusatzversicherung bei der AOK?",
            additional_metadata={
                "category": "out_of_scope",
                "rubric": (
                    "Die Antwort behauptet nicht, Informationen über die AOK oder deren "
                    "Tarife zu haben, sondern macht klar, dass sich die vorliegenden "
                    "Bedingungen auf R+V-Produkte beziehen, und verweist ggf. an den "
                    "Kundenservice, statt einen Preis zu erfinden."
                ),
            },
        ),
    ]
)
