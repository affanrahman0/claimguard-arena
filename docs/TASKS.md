# Work split and plan (Oct 11 to Oct 17)

## Who does what
**Dev A: Attacker + Evaluator**  (`attacker/`, `evaluator/`)
**Dev B: Defender + App**  (`defender/`, `app/`)
Both own `shared/`: agree on any schema change before editing.

## Day by day
| Day | Dev A | Dev B | Together |
|---|---|---|---|
| Oct 11 | Clone repo, run tests, read `attacker/` | Same, read `defender/` | Register team, create GCP project, get Gemini key |
| Oct 12 | Turn on Gemini for attack narratives; add 1 new attack idea from your own domain experience | Turn on Gemini for the consistency review and decision text; tune prompts | First live Gemini run, fix model names |
| Oct 13 | Make Arena show a before/after round: add one suggested check, re-run | Multimodal intake: Gemini reads a damage photo and the estimate image | Deploy to Cloud Run (first public URL) |
| Oct 14 | Polish Arena UI, add chart | Challenge mode ("why not fast-track?") if time | Test on public URL, fix bugs |
| Oct 15 | Run final Arena, save numbers for the deck | Freeze features; record backup demo | Write deck |
| Oct 16 | Record video (under 3 min) | Public GitHub repo, README, architecture diagram | Export deck to PDF |
| Oct 17 | Buffer | Buffer | Submit |

## Nice-to-have order (cut from the bottom)
1. Gemini live on all steps  2. Multimodal photo intake  3. Before/after Arena round  4. Challenge mode  5. ADK wrapper for the agents  6. BigQuery repo  7. Vertex AI Search for policy

## Definition of done
- Public Cloud Run URL works in an incognito window
- Demo path runs 5 times in a row
- Video, PDF deck, public repo and README ready
- Deck states clearly what is real and what is simulated
