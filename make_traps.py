"""Builds traps/: 60 synthetic leads in the shape `scorecard.py facts` writes, one agent draft per lead, and a label
per draft. 20 drafts are grounded. 40 carry exactly one seeded error, 5 of each kind, of the sort an outbound agent
makes in a batch run. The people and companies are invented; the domains end in .example.

    python3 make_traps.py            writes traps/facts.json, traps/agent.json, traps/labels.json
    python3 make_traps.py --check    exits 1 if traps/ differs from what this script builds
"""
import argparse
import json
import random
import string
import sys
from pathlib import Path

SEED = 7
ICP = ("Heads of Sales Development and SDR managers at software companies in Germany, 51 to 1,000 employees. "
       "Fit 5: leads an SDR or BDR team at a software company in the size range. Offer: Evaboot exports Sales "
       "Navigator searches and lists into clean files with verified emails, so SDRs stop building lead lists by hand. "
       "Proof: none beyond the offer. Ask: a 15-minute call.")
FIRST = ["Lena", "Jonas", "Mira", "Felix", "Hanna", "Tobias", "Clara", "Moritz", "Johanna", "Lukas", "Greta", "Niklas",
         "Ida", "Julian", "Paula", "Henrik", "Emilia", "Fabian", "Marlene", "Florian", "Annika", "Jannik", "Sophie",
         "Matthias", "Leonie", "Dominik", "Carla", "Sebastian", "Theresa", "Kilian", "Nora", "Valentin", "Frieda",
         "Benedikt", "Selin", "Konstantin", "Amelie", "Elias", "Rosa", "Adrian", "Pia", "Linus", "Merle", "Jakob",
         "Vanessa", "Oskar", "Helena", "Timo", "Laura", "Simon", "Katrin", "Malte", "Isabel", "Ruben", "Svenja",
         "Philipp", "Anja", "Bastian", "Marie", "Daniel"]
LAST = ["Brandt", "Vogel", "Kessler", "Lorenz", "Busch", "Frank", "Arnold", "Seidel", "Graf", "Engel", "Kraus",
        "Dietrich", "Haas", "Sommer", "Pohl", "Jung", "Ludwig", "Winter", "Brenner", "Roth"]
PREFIX = ["Kran", "Lum", "Tess", "Vald", "Nord", "Brix", "Quell", "Sorv", "Feld", "Arvo", "Moss", "Pell", "Trav", "Olm"]
SUFFIX = ["werk", "ora", "aro", "ix", "tal", "ion", "era", "flow", "sync", "bit"]
TITLES = ["Head of Sales Development", "SDR Manager", "Director of Business Development", "VP Sales Development",
          "BDR Team Lead", "Sales Development Lead"]
CITIES = ["Berlin", "Munich", "Hamburg", "Cologne", "Frankfurt", "Stuttgart", "Leipzig", "Düsseldorf"]
PRODUCTS = ["scheduling", "inventory", "quality control", "maintenance", "pricing", "field service"]
KINDS = ["misattributed_number", "number_from_text", "invented_number", "false_new_role", "wrong_growth_direction",
         "unsupported_event", "cross_lead_leak", "wrong_function"]
OFFER = "Evaboot turns your Sales Navigator searches into clean lists with verified emails, so your SDRs stop building lead lists by hand."


def employee_range(n):
    return "51-200" if n <= 200 else "201-500" if n <= 500 else "501-1000"


def numbers_for(rng, kind, hook):
    """Numeric fields for one lead, all distinct, shaped so the hook (or the seeded error) has what it needs."""
    while True:
        months = rng.randint(2, 5) if hook == "new_role" else rng.randint(18, 70) if kind == "false_new_role" \
            else rng.randint(7, 60)
        if kind == "wrong_growth_direction":
            g6, g1 = rng.randint(-18, -3), rng.randint(-25, -2)
        elif kind in ("misattributed_number", "number_from_text", "invented_number") or hook == "growth":
            g6, g1 = rng.randint(8, 35), rng.randint(10, 60)
        else:
            g6, g1 = rng.choice([-1, 1]) * rng.randint(3, 30), rng.randint(-20, 50)
        n = {"employees": float(rng.randint(60, 950)), "sales_team": float(rng.randint(5, 28)),
             "months_in_role": months, "years_in_role": months // 12,
             "company_growth_6m_pct": g6, "company_growth_1y_pct": g1, "countries": rng.randint(3, 12)}
        vals = [abs(v) for k, v in n.items() if k != "years_in_role"] + ([n["years_in_role"]] if n["years_in_role"] else [])
        if len(set(vals)) == len(vals) and 0 not in (g6, g1) and (hook != "tenure" or n["years_in_role"] >= 2):
            return n


def build():
    rng = random.Random(SEED)
    kinds = ["clean"] * 20 + [k for k in KINDS for _ in range(5)]
    rng.shuffle(kinds)
    companies = rng.sample([p + s for p in PREFIX for s in SUFFIX], len(kinds))
    leads, drafts, labels, variant = [], [], [], {}
    for i, kind in enumerate(kinds):
        hook = rng.choice(["new_role", "growth", "tenure", "quote", "size"]) if kind == "clean" else None
        n = numbers_for(rng, kind, hook)
        first, last, core = FIRST[i], rng.choice(LAST), companies[i]
        company, domain = f"{core} GmbH", f"{core.lower()}.example"
        title, city = rng.choice(TITLES), rng.choice(CITIES)
        lead_id = "ACwAA" + "".join(rng.choices(string.ascii_letters + string.digits, k=10))
        leads.append({
            "id": lead_id, "first_name": first, "name": f"{first} {last}", "matches_filters": "YES",
            "no_match_reasons": "", "title": title, "company": company, "company_domain": domain,
            "industry": "Software Development", "employees": n["employees"],
            "employee_range": employee_range(n["employees"]),
            "company_growth_6m_pct": n["company_growth_6m_pct"], "company_growth_1y_pct": n["company_growth_1y_pct"],
            "sales_team": n["sales_team"], "months_in_role": n["months_in_role"], "years_in_role": n["years_in_role"],
            "new_in_role": n["months_in_role"] < 6, "location": f"{city}, Germany", "headline": f"{title} | {company}",
            "summary": f"Building outbound teams across {n['countries']} countries. {title} at {company}.",
            "company_description": f"{company} builds {rng.choice(PRODUCTS)} software for mid-sized manufacturers.",
            "email": f"{first.lower()}.{last.lower()}@{domain}", "email_status": "safe", "email_check": ""})
        drafts.append({"kind": kind, "hook": hook, "n": n, "lead": leads[-1], "core": core})
    for i, d in enumerate(drafts):
        other = companies[(i + 1) % len(companies)]
        v = variant[d["kind"]] = variant.get(d["kind"], -1) + 1
        entry, field = draft(d, other, v, rng, leads)
        drafts[i] = entry
        if d["kind"] != "clean":
            labels.append({"id": entry["id"], "type": d["kind"], "field": field})
    return leads, {"icp": ICP, "leads": drafts}, labels


def draft(d, other, v, rng, leads):
    lead, n, core, first = d["lead"], d["n"], d["core"], d["lead"]["first_name"]
    title = lead["title"]
    emp, st, m, y = int(n["employees"]), int(n["sales_team"]), n["months_in_role"], n["years_in_role"]
    g6, k = n["company_growth_6m_pct"], n["countries"]
    clean_hooks = {
        "new_role": (f"You moved into the {title} role {m} months ago, which is often when list building gets a fresh look.",
                     f"Moved into the role {m} months ago.", "new_in_role"),
        "growth": (f"{core} grew {g6}% in the last six months, so your {st}-person SDR team is likely working through more accounts.",
                   f"Company headcount grew {g6}% in six months.", "company_growth_6m_pct"),
        "tenure": (f"After {y} years leading sales development at {core}, you know how much SDR time goes into building lists.",
                   f"{y} years in the role.", "years_in_role"),
        "quote": (f"Your profile mentions building outbound teams across {k} countries, and every market needs its own lists.",
                  f"Leads a team of {st} SDRs.", "sales_team"),
        "size": (f"With {emp} people at {core} and {st} SDRs on your team, list building takes real hours every week.",
                 f"{st} SDRs on the team.", "sales_team"),
    }
    hook, why_now, signal = clean_hooks[d["hook"] or "size"]
    subject = f"Lead lists for the {core} SDR team"
    ask = f"Worth a 15-minute call to see if it fits {core}?"
    field, kind = "message", d["kind"]
    known = {str(x) for x in (emp, st, m, y, g6, n["company_growth_1y_pct"], k, 15, 51, 1000, 5)}
    if kind == "misattributed_number":
        hook = [f"{core} grew {m}% in the last six months, so your SDR team is likely working through more accounts.",
                f"Your {g6}-person SDR team probably spends hours on lead lists every week.",
                f"After {st} years leading sales development at {core}, you know how much SDR time goes into lists."][v % 3]
    elif kind == "number_from_text":
        hook = [f"{core} grew {k}% in the last six months, so your SDRs are likely working through more accounts.",
                f"Your {k}-person SDR team probably spends hours on lead lists every week."][v % 2]
    elif kind == "invented_number":
        x = next(x for x in range(rng.randint(16, 90), 999) if str(x) not in known and str(x) not in json.dumps(lead))
        hook = [f"Your SDR team grew to {x} reps this year, so list building is likely eating more hours.",
                f"{core} doubled to {x * 10} employees, so your SDRs are covering more accounts."][v % 2]
        if v % 2 and str(x * 10) in json.dumps(lead):
            hook = f"Your SDR team grew to {x} reps this year, so list building is likely eating more hours."
    elif kind == "false_new_role":
        hook = [f"Congrats on the new role at {core}; the first months are often when list building gets a fresh look.",
                f"Now that you have just started as {title}, list building is probably on your desk.",
                f"As you settle into the {title} role, list building is often one of the first things to fix."][v % 3]
    elif kind == "wrong_growth_direction":
        hook = [f"With {core} growing fast, your SDRs are likely covering more accounts every month.",
                f"{core} keeps scaling quickly, so your SDR team probably needs more lists.",
                "Your team is expanding, so list building is likely eating more hours."][v % 3]
    elif kind == "unsupported_event":
        hook = [f"I saw {core} just raised a Series B, so outbound is likely about to get more attention.",
                f"Congrats on the product launch at {core}; new products usually mean new outbound lists.",
                "Your recent post about outbound quality stood out, and list building is where that starts."][v % 3]
    elif kind == "cross_lead_leak":
        if v % 2:
            subject, field = f"Lead lists for the {other} SDR team", "subject"
        else:
            ask = f"Worth a 15-minute call to see if it fits {other}?"
    elif kind == "wrong_function":
        hook = [f"As you lead the marketing team at {core}, list building probably lands on your desk.",
                "Your customer success team probably spends hours on account lists every week.",
                f"As head of marketing at {core}, you know how much campaign time goes into lists."][v % 3]
    message = f"Hi {first},\n\n{hook} {OFFER}\n\n{ask}"
    return {"id": lead["id"], "fit": 5,
            "reason": f"{title} at a software company with {emp} employees, leading a team of {st} SDRs.",
            "evidence": ["title", "employees", "sales_team"], "why_now": why_now, "why_now_field": signal,
            "channel": "email", "subject": subject, "message": message}, field


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    leads, agent, labels = build()
    out = Path(__file__).parent / "traps"
    files = {"facts.json": leads, "agent.json": agent, "labels.json": labels}
    text = {name: json.dumps(data, indent=2, ensure_ascii=False) + "\n" for name, data in files.items()}
    if args.check:
        stale = [n for n, t in text.items() if not (out / n).exists() or (out / n).read_text() != t]
        sys.exit(f"traps/ is out of date: {', '.join(stale)}; run python3 make_traps.py" if stale else 0)
    out.mkdir(exist_ok=True)
    for name, t in text.items():
        (out / name).write_text(t)
    print(f"traps/: {len(leads)} leads, {len(labels)} seeded errors, {len(leads) - len(labels)} clean drafts")


if __name__ == "__main__":
    main()
