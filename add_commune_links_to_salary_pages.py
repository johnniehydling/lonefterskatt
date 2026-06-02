#!/usr/bin/env python3
"""
Adds a "Lön efter skatt X kr i din kommun" section to each of the 13
salary-level pages, linking to all 32 commune combo pages.
"""

import os
import re

DIR = "/Users/johnniehydling/Documents/lonefterskatt"

KOMMUNER = [
    {"slug": "stockholm",   "name": "Stockholm",   "rate": 30.55},
    {"slug": "goteborg",    "name": "Göteborg",    "rate": 32.60},
    {"slug": "malmo",       "name": "Malmö",       "rate": 32.42},
    {"slug": "uppsala",     "name": "Uppsala",     "rate": 33.18},
    {"slug": "vasteras",    "name": "Västerås",    "rate": 31.76},
    {"slug": "orebro",      "name": "Örebro",      "rate": 34.45},
    {"slug": "linkoping",   "name": "Linköping",   "rate": 31.75},
    {"slug": "helsingborg", "name": "Helsingborg", "rate": 31.39},
    {"slug": "jonkoping",   "name": "Jönköping",   "rate": 33.40},
    {"slug": "norrkoping",  "name": "Norrköping",  "rate": 33.75},
    {"slug": "lund",        "name": "Lund",        "rate": 32.42},
    {"slug": "umea",        "name": "Umeå",        "rate": 34.75},
    {"slug": "gavle",       "name": "Gävle",       "rate": 33.77},
    {"slug": "boras",       "name": "Borås",       "rate": 32.79},
    {"slug": "sundsvall",   "name": "Sundsvall",   "rate": 33.88},
    {"slug": "eskilstuna",  "name": "Eskilstuna",  "rate": 32.85},
    {"slug": "halmstad",    "name": "Halmstad",    "rate": 32.38},
    {"slug": "karlstad",    "name": "Karlstad",    "rate": 33.55},
    {"slug": "nacka",       "name": "Nacka",       "rate": 30.11},
    {"slug": "lulea",       "name": "Luleå",       "rate": 33.84},
    {"slug": "sodertalje",  "name": "Södertälje",  "rate": 33.16},
    {"slug": "huddinge",    "name": "Huddinge",    "rate": 31.71},
    {"slug": "solna",       "name": "Solna",       "rate": 29.70},
    {"slug": "jarfalla",    "name": "Järfälla",    "rate": 31.52},
    {"slug": "taby",        "name": "Täby",        "rate": 31.90},
    {"slug": "danderyd",    "name": "Danderyd",    "rate": 30.58},
    {"slug": "lidingo",     "name": "Lidingö",     "rate": 29.67},
    {"slug": "sollentuna",  "name": "Sollentuna",  "rate": 30.45},
    {"slug": "osteraker",   "name": "Österåker",   "rate": 28.93},
    {"slug": "karlskoga",   "name": "Karlskoga",   "rate": 33.17},
    {"slug": "vaxjo",       "name": "Växjö",       "rate": 32.67},
    {"slug": "kungsbacka",  "name": "Kungsbacka",  "rate": 32.58},
]

SALARY_LEVELS = [20000, 25000, 30000, 35000, 40000, 45000, 50000, 55000, 60000, 70000, 80000, 90000, 100000]

# Tax calc helpers
PBB = 58500
STATE_THRESH = 660400
BURIAL = 0.00292

def grundavdrag_normal(y):
    if y <= 0:       return 0
    if y <= 44200:   return y
    if y <= 135700:  return 44200 + (y - 44200) * 0.2
    if y <= 155700:  return 62500 + (y - 135700) * 0.05
    if y <= 350000:  return 63500
    if y <= 630000:  return 63500 - (y - 350000) * 0.1
    return 35500

def jobbskatteavdrag_normal(y, rate):
    ra = rate / 100
    if y <= 44200:
        base = (0.9914 * y - 11200) * ra
    elif y <= 135500:
        base = (0.9914 * y - 11200 + 0.334 * (y - 44200)) * ra
    elif y <= 249300:
        base = (0.9914 * y - 11200 + 0.334 * (135500 - 44200) + 0.125 * (y - 135500)) * ra
    elif y <= 660400:
        base = (0.9914 * y - 11200 + 0.334 * (135500 - 44200) + 0.125 * (249300 - 135500)) * ra
    else:
        base = (0.9914 * y - 11200 + 0.334 * (135500 - 44200) + 0.125 * (249300 - 135500)) * ra
        reduction = 0.03 * (y - 660400)
        base = max(0, base - reduction)
    return max(0, base)

def calc_net(gross_monthly, rate):
    y = gross_monthly * 12
    ra = rate / 100
    ga = grundavdrag_normal(y) / 12
    jsa = jobbskatteavdrag_normal(y, rate) / 12
    kommunalskatt = (gross_monthly - ga) * ra
    burial = gross_monthly * BURIAL
    state_tax = 0.2 * max(0, y - STATE_THRESH) / 12 if y > STATE_THRESH else 0
    net = gross_monthly - kommunalskatt - burial - state_tax + jsa
    return round(net)

def fmt(n):
    return f"{n:,}".replace(",", " ")

def build_commune_section(salary):
    formatted_salary = fmt(salary)
    # Build cards HTML for all communes
    cards = []
    for k in KOMMUNER:
        net = calc_net(salary, k["rate"])
        rate_str = f"{k['rate']:.2f}".replace(".", ",") + "%"
        net_str = fmt(net)
        cards.append(
            f'    <a href="/lon-efter-skatt-{salary}-{k["slug"]}.html" class="related-c">'
            f'<div class="related-name">{k["name"]}</div>'
            f'<div class="related-rate">{net_str} kr netto</div></a>'
        )
    cards_html = "\n".join(cards)

    section = f"""
  <div class="prose">
    <h2>Lön efter skatt {formatted_salary} kr per kommun</h2>
    <p>Se exakt nettolön, skatteuppdelning och jämförelser för just {formatted_salary} kr i varje enskild kommun.</p>
  </div>

  <div class="related-grid" style="grid-template-columns: repeat(4, 1fr); margin-bottom: 32px;">
{cards_html}
  </div>
"""
    return section

def process_file(salary):
    filename = f"lon-efter-skatt-{salary}.html"
    filepath = os.path.join(DIR, filename)
    if not os.path.exists(filepath):
        print(f"SKIP (not found): {filename}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if already updated
    if f"lon-efter-skatt-{salary}-stockholm.html" in content:
        print(f"ALREADY DONE: {filename}")
        return

    commune_section = build_commune_section(salary)

    # Insert before "Relaterade inkomstnivåer" section
    marker = '  <div class="prose">\n    <h2>Relaterade inkomstnivåer</h2>'
    if marker not in content:
        print(f"MARKER NOT FOUND in {filename}")
        return

    new_content = content.replace(marker, commune_section + marker)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"UPDATED: {filename}")

for salary in SALARY_LEVELS:
    process_file(salary)

print("Done.")
