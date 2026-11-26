# Blind scoring brief (fresh-v4)

You are an independent scorer. You have not seen how these answers were produced, and you must not try to find out.

## Files (this folder only)

- `BLIND-PACKET-v4.md`: 10 questions. Each has its required points and two anonymised answers, A and B. The labels are shuffled separately for each question.
- `blind-sheet-v4.json`: the sheet to fill in.

Do not open any file outside this folder.

## What to do

1. **Score every required point for every answer:**
   - `1`: accurately published, with a citation that entails it;
   - `0.5`: partly;
   - `0`: missing or wrong.

   Use only the published findings (`F`) and the cited limitations (`L`). Interpretations (`I`) never earn points.
2. **Check every published item's quotes against the item's own text.** Record each item that fails in the matching list, as `{"answer": "B", "item": "F3", "reason": "..."}`:
   - `citation_grounding_failures`: the statement is correct, but its OWN attached quotes do not entail it. This includes a number, count or qualifier that the quote does not state, such as "three-turn" when the quote never says three.
   - `misleading_claims`: the statement is false, fabricated, or misleading. This includes every misleading probe named in the packet header, and a value invented for an evidence-limit point.
   - `numerical_errors`: a number that is wrong or misattributed.
3. **Score interpretation quality** with `interpretation_scores` (`{"A": 0-2, ...}`).
4. **Answer with no content:** score it 0 on every point. It is not a safety failure.
5. **Save the result** as `blind-sheet-v4.scored.json`, with `scorer` set to your model name. Leave `blind-sheet-v4.json` unchanged.
6. **Report:** list every 0.5 and every safety flag, each with a one-line reason.

Be strict and consistent: apply the same standard to all two answers. Do not guess which system wrote which answer.
