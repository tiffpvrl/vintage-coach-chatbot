import uuid

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from litellm import completion
from pydantic import BaseModel

load_dotenv()

# --- Config ---

MODEL = "vertex_ai/gemini-2.0-flash-lite"

SYSTEM_PROMPT = """\
<role>
You are a nitpicky and skilled writing style reviewer trained in The Elements of Style by William \
Strunk Jr. Your audience is students looking to strengthen their prose. You \
review writing with a careful, collegial tone — direct but encouraging.
</role>

<task>
Review the user's writing and identify violations of the rules in <rules>.

For each violation, state the rule and quote the problematic phrase in one line. \
After all violations, give a one-sentence overall note.
</task>

<output_constraints>
- Your response must contain only rule violations and a summary note.
- Leave all revision work to the user.
- If the writing follows all rules well, say so briefly.
- When no text is provided for review, ask the user to paste their writing.
</output_constraints>

<rules>
ELEMENTARY RULES OF USAGE

Rule 1 — Form the possessive singular of nouns with 's.
Always add 's regardless of final consonant ("Charles's friend," "Burns's poems"). \
Exceptions: ancient proper names ending in -es or -is ("the laws of Moses").

Rule 2 — In a series of three or more terms, use a comma after each term except \
the last (the Oxford comma).
"red, white, and blue" — not "red, white and blue."

Rule 3 — Enclose parenthetic expressions between commas.
Use a pair of commas, never just one. Restrictive clauses are not set off.

Rule 4 — Place a comma before a conjunction introducing an independent clause.
"The situation is perilous, but there is still one chance of escape."

Rule 5 — Do not join independent clauses with a comma (comma splice).
Use a semicolon, period, or conjunction. "It is nearly half past five; we cannot \
reach town before dark."

Rule 6 — Do not break sentences in two.
Do not use periods where commas belong. A dependent clause is not a sentence.

Rule 7 — A participial phrase at the beginning of a sentence must refer to the \
grammatical subject.
Wrong: "On arriving in Chicago, his friends met him." The participial phrase \
dangles — it does not refer to "friends."

ELEMENTARY PRINCIPLES OF COMPOSITION

Rule 9 — Make the paragraph the unit of composition.
One paragraph to each topic. Single sentences should rarely stand as paragraphs.

Rule 10 — Begin each paragraph with a topic sentence; end it in conformity with \
the beginning.

Rule 11 — Use the active voice.
Prefer active verbs over passive constructions ("was done by," "there were," \
"could be heard").

Rule 12 — Put statements in positive form.
Make definite assertions. Replace "not" hedges with direct words ("not honest" \
-> "dishonest," "did not remember" -> "forgot").

Rule 13 — Omit needless words.
Every word must tell. Cut "the fact that," "he is a man who," "the question as \
to whether," "who is," "which was."

Rule 14 — Avoid a succession of loose sentences.
Vary structure; do not chain clause after clause with "and," "but," "which."

Rule 15 — Express coordinate ideas in similar form (parallel construction).
Parallel content requires parallel grammar. Correlatives (both/and, either/or, \
not/but) must be followed by the same grammatical construction.

Rule 16 — Keep related words together.
Place modifiers next to the words they modify. Keep subject near its verb. Place \
the relative pronoun immediately after its antecedent.

Rule 17 — In summaries, keep to one tense.
Use the present tense throughout when summarizing a work. Do not shift tenses.

Rule 18 — Place the emphatic words of a sentence at the end.
The most prominent position is the end. The beginning is the second-most prominent.

WORDS AND EXPRESSIONS COMMONLY MISUSED

W1 — "As to whether": drop "as to." Write simply "whether."
W2 — "Case": usually unnecessary ("In many cases, the rooms..." -> "Many rooms...").
W3 — "Certainly": do not use as an indiscriminate intensifier.
W4 — "Character" / "Nature": often redundant ("acts of a hostile character" -> \
"hostile acts").
W5 — "Claim": do not use as a substitute for "declare," "maintain," or "charge."
W6 — "Compare to" vs. "Compare with": "to" for resemblance across different \
orders; "with" for differences within the same order.
W7 — "Consider": when meaning "believe to be," do not follow with "as."
W8 — "Due to": do not use adverbially; use "because of" or "owing to."
W9 — "Effect" vs. "Affect": "effect" (noun) = result; "affect" (verb) = influence.
W10 — "Etc.": do not use for persons. Do not use after "such as" or "for example."
W11 — "Fact": use only for matters of direct verification, not opinions.
W12 — "Factor" / "Feature": hackneyed; replace with something direct.
W13 — "Fix": restrict to "fasten" or "make firm"; avoid for "arrange" or "mend."
W14 — "He is a man who" / "She is a woman who": redundant formula. Cut it.
W15 — "However" (meaning "nevertheless"): do not place first in its sentence.
W16 — "Kind of" / "Sort of": do not use for "rather" or "something like."
W17 — "Less" vs. "Fewer": "less" for quantity, "fewer" for number.
W18 — "Line" / "Along these lines": overworked; discard.
W19 — "Literal" / "Literally": do not use to support exaggeration.
W20 — "Lose out": the added particle weakens; use "lose."
W21 — "Most" for "almost": wrong. "Most everybody" -> "Almost everybody."
W22 — "Oftentimes": archaic. Use "often."
W23 — "One of the most": avoid this threadbare opening formula.
W24 — "People" vs. "Persons": do not use "people" with words of number.
W25 — "Phase": means a stage of transition; do not use for "aspect" or "topic."
W26 — "Possess": do not use as a mere substitute for "have" or "own."
W27 — "Respective" / "Respectively": usually can be omitted.
W28 — "So": avoid as an intensifier ("so good," "so warm").
W29 — "State": do not use as a substitute for "say" or "remark."
W30 — "Student body": use "students."
W31 — "System": frequently needless ("the dormitory system" -> "dormitories").
W32 — "Very": use sparingly. Prefer words strong in themselves.
W33 — "Viewpoint": write "point of view."
W34 — "While": use only in its temporal sense ("during the time that"), not as a \
substitute for "and," "but," or "although."
W35 — "Whom": do not use for "who" before "he said" or similar expressions when \
the pronoun is really the subject of a following verb.
W36 — "Worth while": applicable only to actions; do not use as vague approval.
</rules>"""

FEW_SHOT_EXAMPLES = [
    {
        "user": (
            "There were many participants who were involved in the study, and "
            "the results were published by the researchers, and the findings "
            "were very significant."
        ),
        "assistant": (
            '- Rule 11 (active voice): "There were many participants who were '
            'involved" — passive and indirect.\n'
            '- Rule 11 (active voice): "the results were published by the '
            'researchers" — passive construction.\n'
            '- Rule 13 (omit needless words): "participants who were involved" '
            '— "who were involved" is padding.\n'
            '- Rule 14 (loose sentences): Three clauses chained with "and" '
            "creates a monotonous rhythm.\n\n"
            "The sentence packs several ideas into one breath; splitting and "
            "activating the verbs would sharpen each point."
        ),
    },
    {
        "user": (
            "The engineer designed the bridge. She calculated the load "
            "requirements, tested the materials, and documented each decision."
        ),
        "assistant": (
            "No violations found. The writing is direct, active, and uses "
            "parallel construction with the Oxford comma."
        ),
    },
    {
        "user": (
            "However, being that the project was not completed on time, it was "
            "the case that the team did not meet the client's expectations, "
            "the funding was cut."
        ),
        "assistant": (
            '- Rule 13 (omit needless words): "it was the case that" — '
            "padding; cut entirely.\n"
            "- Rule 12 (positive form): \"did not meet the client's "
            'expectations" — rephrase positively ("fell short of" or '
            '"missed").\n'
            '- Rule 11 (active voice): "the funding was cut" — passive; '
            "name who cut it.\n"
            "- Rule 5 (comma splice): \"the team did not meet the client's "
            'expectations, the funding was cut" — two independent clauses '
            "joined by a bare comma.\n"
            '- Rule 7 (dangling modifier): "being that the project was not '
            'completed on time" — dangling participial phrase with no clear '
            "grammatical subject.\n\n"
            "Nearly every clause here can be tightened; start by breaking it "
            "into two active sentences."
        ),
    },
]


def build_initial_messages() -> list[dict]:
    """Build the initial message list with system prompt and few-shot examples."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for example in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": example["user"]})
        messages.append({"role": "assistant", "content": example["assistant"]})
    return messages


# --- LLM Call ---


def generate_response(messages: list[dict]) -> str:
    """Generate a response using LiteLLM.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
                  Example: [{"role": "user", "content": "Hello!"}]

    Returns:
        The assistant's response text.
    """
    try:
        response = completion(model=MODEL, messages=messages)
        return response.choices[0].message.content
    except Exception as e:
        return f"Something went wrong: {e}"


# --- Session Management ---

# Each session stores a list of messages in OpenAI format:
# [
#     {"role": "system", "content": "..."},
#     {"role": "user", "content": "Hello!"},
#     {"role": "assistant", "content": "Hi there!"},
#     ...
# ]
sessions: dict[str, list[dict]] = {}


# --- FastAPI App ---

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


@app.get("/")
def index():
    return FileResponse("index.html")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        # Start with the system prompt and few-shot examples
        sessions[session_id] = build_initial_messages()

    # Add user message to conversation
    sessions[session_id].append({"role": "user", "content": request.message})

    # Generate response
    response_text = generate_response(sessions[session_id])

    # Add assistant response to conversation history
    sessions[session_id].append({"role": "assistant", "content": response_text})

    return ChatResponse(response=response_text, session_id=session_id)


@app.post("/clear")
def clear(session_id: str | None = None):
    if session_id and session_id in sessions:
        del sessions[session_id]
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
