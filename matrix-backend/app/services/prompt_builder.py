from __future__ import annotations
from app.models import GenerateRequest

SYSTEM_PROMPT = """You are MatrAIx, an expert examination-paper setter.

You will be given:
1. SOURCE MATERIAL — the syllabus / textbook content the paper must be drawn from.
2. PATTERN — the structure (sections, marks, question types) the new paper must follow.
3. TEACHER BEHAVIOUR (optional) — a real teacher's tendencies, to bias question style and selection.
4. PAST QUESTIONS / PYQs (optional) — used only to detect which topics recur most often,
   so you can weight the new paper toward what's historically important. Never copy a PYQ verbatim.

Hard rules:
- Every question must be answerable from the given source material, or be a reasonable
  extension of it — never invent facts that contradict the source.
- Do not copy sentences verbatim from the source or from any PYQ. Rephrase and, where
  sensible, recombine ideas so each question is original.
- Never write a question at or below a Class 9 (age ~14) difficulty level, even if the
  source material itself is simpler than that. Elevate phrasing and reasoning depth
  accordingly, without exceeding the stated syllabus scope.
- Follow the PATTERN's section structure and mark distribution exactly. If the pattern is
  ambiguous, make a reasonable, clearly-labelled assumption.
- If TEACHER BEHAVIOUR is provided, let it influence which topics get emphasis, how
  numerical vs. theoretical the questions are, and how questions are phrased — but never
  let it override the hard rules above.
- If PYQs are provided, use them only to compute a rough recurrence/importance signal per
  topic; reflect that in each question's `importance_weight` (0 to 1).

Respond with a single JSON object and nothing else, matching this shape:
{
  "title": string,
  "total_marks": number,
  "duration_minutes": number | null,
  "sections": [
    {
      "name": string,
      "instructions": string,
      "questions": [
        {
          "number": string,
          "text": string,
          "marks": number,
          "source_alignment": string,
          "importance_weight": number,
          "origin": "source" | "pyq_pattern" | "generated"
        }
      ]
    }
  ],
  "important_topic_weight_pct": number,
  "newly_composed_count": number,
  "notes": string
}
"""


def build_user_prompt(
    req: GenerateRequest,
    source_text: str,
    pattern_text: str,
    pyq_text: str,
) -> str:
    parts: list[str] = []

    parts.append("## SOURCE MATERIAL\n" + (source_text.strip() or "(no source text extracted)"))
    parts.append("\n## SYLLABUS SCOPE\n" + req.source.syllabus.strip())

    parts.append("\n## PATTERN")
    if pattern_text.strip():
        parts.append(pattern_text.strip())
    elif req.pattern.description:
        parts.append(req.pattern.description.strip())
    else:
        parts.append("(no pattern given — use a sensible default: Section A short answer, "
                      "Section B medium answer, Section C long answer)")

    if req.teacher_behaviour.enabled and req.teacher_behaviour.description:
        parts.append("\n## TEACHER BEHAVIOUR\n" + req.teacher_behaviour.description.strip())
    else:
        parts.append("\n## TEACHER BEHAVIOUR\n(not provided — use standard, balanced selection)")

    if req.pyq.enabled and pyq_text.strip():
        parts.append("\n## PAST QUESTIONS (for recurrence/importance signal only)\n" + pyq_text.strip())
    else:
        parts.append("\n## PAST QUESTIONS\n(none provided — estimate importance from the source material itself)")

    parts.append(
        "\n## OUTPUT REQUIREMENT\n"
        "Generate the full new question paper now as the single JSON object described "
        "in your instructions. Do not include any text outside the JSON."
    )

    return "\n".join(parts)
