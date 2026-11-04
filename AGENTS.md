# Agent instructions

This repo checks an outbound agent's drafts claim by claim against the lead's real fields. It reads the files outbound-agent-scorecard writes: `runs/facts.json` (from `scorecard.py facts`) and `runs/agent.json` (the agent's drafts). Nothing is sent.

1. Run `python3 claimcheck.py check runs/facts.json runs/agent.json` and show every FAIL line.
2. Fix a draft from the FAIL line: drop the claim, or rest it on the field the line names. Run `check` again until no line is left.
3. Only if the user asks for a second opinion: `python3 claimcheck.py judge ...`. It calls Claude once per draft; show the count first.

Never ask for or handle an API key: the user writes `ANTHROPIC_API_KEY` into `.env`. Never commit `.env`, `data/` or `runs/`: they hold real people's data.

When you change a rule in `claimcheck.py`, run `python3 -m unittest` and `python3 claimcheck.py eval traps --min-recall 0.9 --max-false-flags 0`. To add a trap, change `make_traps.py` and run it; never edit `traps/` by hand.
