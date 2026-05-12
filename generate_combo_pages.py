#!/usr/bin/env python3
"""
generate_combo_pages.py
Skapar kombisidor: lon-efter-skatt-{belopp}-{kommun-slug}.html
för alla kombinationer av lönenivåer och kommuner.
"""

import os
import math

OUTPUT_DIR = "/Users/johnniehydling/Documents/lonefterskatt"

# Skatteberäkningskonstanter 2026
PBB = 58500
STATE_THRESH = 660400   # under 66 år
STATE_THRESH_65 = 760500  # 66 år eller äldre
BURIAL = 0.00292

KOMMUNER = [
    {"slug": "stockholm",   "name": "Stockholm",   "rate": 30.55, "region": "Stockholms län"},
    {"slug": "goteborg",    "name": "Göteborg",    "rate": 32.60, "region": "Västra Götalands län"},
    {"slug": "malmo",       "name": "Malmö",       "rate": 32.42, "region": "Skåne län"},
    {"slug": "uppsala",     "name": "Uppsala",     "rate": 33.18, "region": "Uppsala län"},
    {"slug": "vasteras",    "name": "Västerås",    "rate": 31.76, "region": "Västmanlands län"},
    {"slug": "orebro",      "name": "Örebro",      "rate": 34.45, "region": "Örebro län"},
    {"slug": "linkoping",   "name": "Linköping",   "rate": 31.75, "region": "Östergötlands län"},
    {"slug": "helsingborg", "name": "Helsingborg", "rate": 31.39, "region": "Skåne län"},
    {"slug": "jonkoping",   "name": "Jönköping",   "rate": 33.40, "region": "Jönköpings län"},
    {"slug": "norrkoping",  "name": "Norrköping",  "rate": 33.75, "region": "Östergötlands län"},
    {"slug": "lund",        "name": "Lund",        "rate": 32.42, "region": "Skåne län"},
    {"slug": "umea",        "name": "Umeå",        "rate": 34.75, "region": "Västernorrlands län"},
    {"slug": "gavle",       "name": "Gävle",       "rate": 33.77, "region": "Gävleborgs län"},
    {"slug": "boras",       "name": "Borås",       "rate": 32.79, "region": "Västra Götalands län"},
    {"slug": "sundsvall",   "name": "Sundsvall",   "rate": 33.88, "region": "Västernorrlands län"},
    {"slug": "eskilstuna",  "name": "Eskilstuna",  "rate": 32.85, "region": "Södermanlands län"},
    {"slug": "halmstad",    "name": "Halmstad",    "rate": 32.38, "region": "Hallands län"},
    {"slug": "karlstad",    "name": "Karlstad",    "rate": 33.55, "region": "Värmlands län"},
    {"slug": "nacka",       "name": "Nacka",       "rate": 30.11, "region": "Stockholms län"},
    {"slug": "lulea",       "name": "Luleå",       "rate": 33.84, "region": "Norrbottens län"},
    {"slug": "sodertalje",  "name": "Södertälje",  "rate": 33.16, "region": "Stockholms län"},
    {"slug": "huddinge",    "name": "Huddinge",    "rate": 31.71, "region": "Stockholms län"},
    {"slug": "solna",       "name": "Solna",       "rate": 29.70, "region": "Stockholms län"},
    {"slug": "jarfalla",    "name": "Järfälla",    "rate": 31.52, "region": "Stockholms län"},
    {"slug": "taby",        "name": "Täby",        "rate": 31.90, "region": "Stockholms län"},
    {"slug": "danderyd",    "name": "Danderyd",    "rate": 30.58, "region": "Stockholms län"},
    {"slug": "lidingo",     "name": "Lidingö",     "rate": 29.67, "region": "Stockholms län"},
    {"slug": "sollentuna",  "name": "Sollentuna",  "rate": 30.45, "region": "Stockholms län"},
    {"slug": "osteraker",   "name": "Österåker",   "rate": 28.93, "region": "Stockholms län"},
    {"slug": "karlskoga",   "name": "Karlskoga",   "rate": 33.17, "region": "Örebro län"},
    {"slug": "vaxjo",       "name": "Växjö",       "rate": 32.67, "region": "Kronobergs län"},
]

SALARY_LEVELS = [20000, 25000, 30000, 35000, 40000, 45000, 50000, 55000, 60000, 70000, 80000, 90000, 100000]

RIKSSNITT = 32.38


def grundavdrag_normal(y):
    if y <= 0:       return 0
    if y <= 44200:   return y
    if y <= 124200:  return 44200
    if y <= 199700:  return 44200 + (y - 124200) * (3000/75500)
    if y <= 367700:  return 47100
    if y <= 468600:  return 47100 - (y - 367700) * (31700/100900)
    return 15400


def grundavdrag_senior(y):
    if y <= 0:        return 0
    if y <= 65700:    return y
    if y <= 116400:   return 65700 + (y - 65700) * 0.249
    if y <= 210000:   return 78300 + (y - 116400) * 0.470
    if y <= 430000:   return 122300
    if y <= 700000:   return 122300 - (y - 430000) * (85300/270000)
    return 37000


def jobbskatteavdrag(y, k_rate):
    a = k_rate / 100
    if y <= 0:
        return 0
    elif y <= 0.91 * PBB:
        j = 0
    elif y <= 3.24 * PBB:
        j = (0.2832 * PBB + 0.3294 * (y - 0.91 * PBB)) * a
    elif y <= 8.08 * PBB:
        j = (0.2832 * PBB + 0.3294 * (3.24 - 0.91) * PBB + 0.1215 * (y - 3.24 * PBB)) * a
    elif y <= 13.54 * PBB:
        base = (0.2832 * PBB + 0.3294 * (3.24 - 0.91) * PBB + 0.1215 * (8.08 - 3.24) * PBB) * a
        j = base - 0.03 * (y - 8.08 * PBB) * a
    else:
        base2 = ((0.2832 * PBB + 0.3294 * (3.24 - 0.91) * PBB + 0.1215 * (8.08 - 3.24) * PBB)
                 - 0.03 * (13.54 - 8.08) * PBB) * a
        j = max(0, base2 - 0.03 * (y - 13.54 * PBB) * a)
    return max(0, min(j, 36800))


def calc_net(monthly, k_rate, senior=False):
    gy = monthly * 12
    if gy <= 0:
        return 0, 0, 0
    thresh = STATE_THRESH_65 if senior else STATE_THRESH
    ga = grundavdrag_senior(gy) if senior else grundavdrag_normal(gy)
    tax_kom_base = max(0, gy - ga)
    tax_kom = tax_kom_base * (k_rate / 100)
    tax_beg = tax_kom_base * BURIAL
    stat_base = max(0, tax_kom_base - (thresh - ga)) if gy > thresh else 0
    tax_stat = stat_base * 0.20
    jobb_av = jobbskatteavdrag(gy, k_rate)
    total_year = max(0, tax_kom + tax_beg + tax_stat - jobb_av)
    net_year = gy - total_year
    net_month = net_year / 12
    tax_month = total_year / 12
    eff_rate = (total_year / gy * 100) if gy > 0 else 0
    return round(net_month), round(tax_month), round(eff_rate, 1)


def fmt_se(n):
    """Formatera tal med svenska tusentalsseparatorer."""
    return f"{int(round(n)):,}".replace(",", " ")  # narrow no-break space


def fmt_kr(n):
    return fmt_se(n) + " kr"


def salary_label(s):
    return fmt_se(s) + " kr"


def generate_page(salary, kommun):
    slug = kommun["slug"]
    name = kommun["name"]
    rate = kommun["rate"]
    region = kommun["region"]

    net, tax, eff = calc_net(salary, rate)
    net_rikssnitt, _, eff_rikssnitt = calc_net(salary, RIKSSNITT)

    # Diff vs rikssnitt
    diff = net - net_rikssnitt
    diff_year = diff * 12
    diff_str = ("+" if diff >= 0 else "") + fmt_kr(diff)
    diff_year_str = ("+" if diff_year >= 0 else "") + fmt_kr(abs(diff_year))

    above_below = "lägre" if rate < RIKSSNITT else "högre"
    diff_pe = round(abs(rate - RIKSSNITT), 2)

    # Statlig skatt?
    pays_state = salary * 12 > STATE_THRESH

    sal_label = salary_label(salary)
    sal_no_space = str(salary)

    page_title = f"Lön efter skatt {sal_label}/mån i {name} 2026 – {fmt_kr(net)} netto"
    meta_desc = (
        f"{sal_label} i lön efter skatt i {name} 2026: kommunalskatt {rate}% ger "
        f"{fmt_kr(net)} netto per månad. Effektiv skatt {eff}%. "
        f"Räkna ut din nettolön."
    )
    canonical = f"https://lonefterskatt.com/lon-efter-skatt-{sal_no_space}-{slug}.html"

    # Välj 5 relaterade kommuner (exclude current)
    all_sorted = sorted(KOMMUNER, key=lambda x: x["rate"])
    related = [k for k in all_sorted if k["slug"] != slug][:5]

    related_cards_html = ""
    for rk in related:
        rnet, _, _ = calc_net(salary, rk["rate"])
        related_cards_html += f"""    <a href="/lon-efter-skatt-{sal_no_space}-{rk['slug']}.html" class="related-c">
      <div class="related-name">{rk['name']}</div>
      <div class="related-rate">{fmt_kr(rnet)} netto</div>
    </a>
"""

    # Länk till kommunsida och lönesida
    # Tabell: visa nettolön för alla kommuner vid denna lönenivå
    table_rows = ""
    all_by_rate = sorted(KOMMUNER, key=lambda x: x["rate"])
    for k in all_by_rate:
        knet, ktax, keff = calc_net(salary, k["rate"])
        highlight = ' style="background:var(--surface2);"' if k["slug"] == slug else ""
        link_open = f'<a href="/lon-efter-skatt-{sal_no_space}-{k["slug"]}.html">'
        link_close = '</a>'
        if k["slug"] == slug:
            link_open = '<strong>'
            link_close = '</strong>'
        table_rows += (
            f'        <tr{highlight}><td>{link_open}{k["name"]}{link_close}</td>'
            f'<td>{k["rate"]}%</td>'
            f'<td>{fmt_kr(ktax)}</td>'
            f'<td class="net">{fmt_kr(knet)}</td></tr>\n'
        )

    # Skatteuppdelning vid rikssnitt för denna lönenivå
    gy = salary * 12
    ga = grundavdrag_normal(gy)
    tax_kom_base = max(0, gy - ga)
    tax_kom_month = round(tax_kom_base * (rate / 100) / 12)
    tax_beg_month = round(tax_kom_base * BURIAL / 12)
    jobb_av_month = round(jobbskatteavdrag(gy, rate) / 12)
    stat_base = max(0, tax_kom_base - (STATE_THRESH - ga)) if gy > STATE_THRESH else 0
    tax_stat_month = round(stat_base * 0.20 / 12)

    # JSON-LD FAQ
    faq_q1 = f"Hur mycket är {sal_label}/mån i lön efter skatt i {name} 2026?"
    faq_a1 = (
        f"Med en bruttolön på {sal_label} per månad i {name} blir nettolönen "
        f"cirka {fmt_kr(net)} per månad 2026. Kommunalskatten i {name} är {rate} procent, "
        f"och den effektiva skattesatsen blir {eff} procent."
    )
    faq_q2 = f"Hur mycket skatt betalar jag på {sal_label}/mån i {name}?"
    faq_a2 = (
        f"Vid en bruttolön på {sal_label} per månad i {name} betalar du cirka {fmt_kr(tax)} "
        f"i skatt per månad. Det motsvarar en effektiv skattesats på {eff} procent."
    )
    faq_q3 = f"Är skatten i {name} hög eller låg jämfört med rikssnittet?"
    faq_a3 = (
        f"{name}s kommunalskatt på {rate} procent är {diff_pe} procentenheter {above_below} "
        f"än rikssnittet på {RIKSSNITT} procent. Det innebär att du på {sal_label} i månaden "
        f"får {diff_str} per månad jämfört med en genomsnittskommun."
    )
    faq_q4 = f"Betalar jag statlig inkomstskatt på {sal_label}/mån i {name}?"
    if pays_state:
        faq_a4 = (
            f"Ja, med {sal_label} i månaden ({fmt_kr(salary*12)} per år) överstiger du "
            f"brytpunkten på 660 400 kr per år. En del av din inkomst beskattas med "
            f"ytterligare 20 procent statlig skatt."
        )
    else:
        faq_a4 = (
            f"Nej, {sal_label} i månaden ({fmt_kr(salary*12)} per år) är under brytpunkten "
            f"på 660 400 kr per år. Du betalar bara kommunalskatt, inte statlig inkomstskatt."
        )

    html = f"""<!DOCTYPE html>
<html lang="sv">
<head>

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4Q115Z1ZNM"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-4Q115Z1ZNM');
</script>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title}</title>
<meta name="description" content="{meta_desc}">
<link rel="canonical" href="{canonical}">

<!-- Strukturerad data: BreadcrumbList -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{"@type": "ListItem", "position": 1, "name": "Hem", "item": "https://lonefterskatt.com"}},
    {{"@type": "ListItem", "position": 2, "name": "Lön efter skatt {name}", "item": "https://lonefterskatt.com/lon-efter-skatt-{slug}.html"}},
    {{"@type": "ListItem", "position": 3, "name": "{sal_label}/mån i {name}", "item": "{canonical}"}}
  ]
}}
</script>

<!-- Strukturerad data: FAQPage -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {{"@type": "Question", "name": "{faq_q1}", "acceptedAnswer": {{"@type": "Answer", "text": "{faq_a1}"}}}},
    {{"@type": "Question", "name": "{faq_q2}", "acceptedAnswer": {{"@type": "Answer", "text": "{faq_a2}"}}}},
    {{"@type": "Question", "name": "{faq_q3}", "acceptedAnswer": {{"@type": "Answer", "text": "{faq_a3}"}}}},
    {{"@type": "Question", "name": "{faq_q4}", "acceptedAnswer": {{"@type": "Answer", "text": "{faq_a4}"}}}}
  ]
}}
</script>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap"></noscript>

<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
  --bg: #0E0F11; --surface: #161719; --surface2: #1E2023; --surface3: #26292D;
  --border: rgba(255,255,255,0.07); --border2: rgba(255,255,255,0.12);
  --ink: #F0EEE8; --ink2: #9B9A96; --ink3: #5C5B58;
  --ice: #A8D4E6; --ice-dim: rgba(168,212,230,0.12);
  --pine: #4E9B7A; --amber: #D4884A; --red: #C0584A; --gold: #C8A96E;
  --radius: 14px; --radius-sm: 8px;
}}
body {{ font-family: 'Outfit', sans-serif; background: var(--bg); color: var(--ink); min-height: 100vh; line-height: 1.6; }}
.main-nav {{ display: flex; align-items: center; padding: 0 24px; border-bottom: 1px solid var(--border); position: sticky; top: 0; background: rgba(14,15,17,0.95); backdrop-filter: blur(12px); z-index: 100; height: 52px; }}
.nav-brand {{ font-size: 0.95rem; font-weight: 600; color: var(--ink); text-decoration: none; letter-spacing: -0.02em; white-space: nowrap; margin-right: 28px; flex-shrink: 0; }}
.nav-brand span {{ color: var(--ice); }}
.nav-links {{ list-style: none; display: flex; align-items: center; gap: 2px; flex: 1; overflow: hidden; }}
.nav-links li a {{ display: block; font-size: 12.5px; font-weight: 400; color: var(--ink3); text-decoration: none; padding: 6px 10px; border-radius: var(--radius-sm); white-space: nowrap; transition: color 0.15s, background 0.15s; }}
.nav-links li a:hover {{ color: var(--ink); background: var(--surface2); }}
.nav-toggle {{ display: none; background: none; border: none; color: var(--ink2); font-size: 1.2rem; cursor: pointer; padding: 6px; margin-left: auto; }}
@media (max-width: 740px) {{
  .main-nav {{ position: relative; }}
  .nav-brand {{ flex: 1; }}
  .nav-toggle {{ display: block; }}
  .nav-links {{ display: none; position: absolute; top: 52px; left: 0; right: 0; flex-direction: column; align-items: flex-start; background: rgba(14,15,17,0.98); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); padding: 4px 0 8px; gap: 0; width: 100%; }}
  .nav-links.open {{ display: flex; }}
  .nav-links li {{ width: 100%; }}
  .nav-links li a {{ padding: 12px 20px; font-size: 13px; border-radius: 0; border-bottom: 1px solid var(--border); width: 100%; white-space: normal; }}
  .nav-links li:last-child a {{ border-bottom: none; }}
}}
.breadcrumb {{ max-width: 680px; margin: 0 auto; padding: 16px 20px 0; font-size: 12px; color: var(--ink3); }}
.breadcrumb a {{ color: var(--ink3); text-decoration: none; }}
.breadcrumb a:hover {{ color: var(--ink); }}
.breadcrumb .sep {{ margin: 0 8px; opacity: 0.5; }}
.breadcrumb .current {{ color: var(--ink2); }}
header.kommun-header {{ position: relative; padding: 40px 24px 36px; text-align: center; border-bottom: 1px solid var(--border); overflow: hidden; }}
header.kommun-header::after {{ content: ''; position: absolute; top: -100px; left: 50%; transform: translateX(-50%); width: 700px; height: 320px; background: radial-gradient(ellipse at center, rgba(168,212,230,0.07) 0%, transparent 70%); pointer-events: none; }}
.eyebrow {{ display: inline-flex; align-items: center; gap: 8px; font-size: 11px; font-weight: 500; letter-spacing: 0.16em; text-transform: uppercase; color: var(--ice); opacity: 0.7; margin-bottom: 18px; }}
.eyebrow::before, .eyebrow::after {{ content: ''; width: 28px; height: 1px; background: var(--ice); opacity: 0.35; }}
h1 {{ font-size: clamp(2rem, 4.5vw, 3.2rem); font-weight: 700; letter-spacing: -0.035em; line-height: 1.05; color: var(--ink); margin-bottom: 14px; position: relative; }}
h1 em {{ font-style: normal; color: var(--ice); }}
header.kommun-header p {{ font-size: 0.95rem; color: var(--ink2); max-width: 540px; margin: 0 auto; font-weight: 300; line-height: 1.75; position: relative; }}
.container {{ max-width: 1000px; margin: 0 auto; padding: 36px 20px 80px; }}
.grid {{ display: grid; grid-template-columns: 1fr; gap: 18px; max-width: 680px; margin: 0 auto; }}
.fact-box {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; max-width: 680px; margin: 0 auto 24px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 0; }}
@media (max-width: 500px) {{ .fact-box {{ grid-template-columns: 1fr 1fr; }} .fact-box .fact:nth-child(3) {{ grid-column: 1 / -1; padding-top: 16px; margin-top: 8px; border-top: 1px solid var(--border); }} }}
.fact {{ padding: 0 16px; }}
.fact:not(:first-child) {{ border-left: 1px solid var(--border); }}
@media (max-width: 500px) {{ .fact:not(:first-child) {{ border-left: none; }} .fact:nth-child(2) {{ border-left: 1px solid var(--border); }} }}
.fact-label {{ font-size: 10px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink3); margin-bottom: 6px; }}
.fact-val {{ font-family: 'DM Mono', monospace; font-size: 1.4rem; font-weight: 500; color: var(--ice); line-height: 1.1; }}
.fact-sub {{ font-size: 11px; color: var(--ink3); margin-top: 4px; }}
.prose {{ max-width: 680px; margin: 0 auto; color: var(--ink2); font-weight: 300; line-height: 1.8; font-size: 0.95rem; }}
.prose p {{ margin-bottom: 16px; }}
.prose strong {{ color: var(--ink); font-weight: 500; }}
.prose h2 {{ font-size: 1.5rem; font-weight: 600; color: var(--ink); letter-spacing: -0.02em; margin: 40px 0 16px; line-height: 1.2; }}
.prose a {{ color: var(--ice); text-decoration: none; border-bottom: 1px solid rgba(168,212,230,0.3); }}
.prose a:hover {{ border-bottom-color: var(--ice); }}
.salary-table-wrap {{ max-width: 680px; margin: 24px auto; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }}
.salary-table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
.salary-table thead th {{ background: var(--surface2); font-size: 10px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink3); text-align: right; padding: 12px 16px; border-bottom: 1px solid var(--border); }}
.salary-table thead th:first-child {{ text-align: left; }}
.salary-table tbody td {{ padding: 12px 16px; border-bottom: 1px solid var(--border); font-family: 'DM Mono', monospace; text-align: right; color: var(--ink); font-size: 0.88rem; }}
.salary-table tbody td:first-child {{ text-align: left; color: var(--ink2); font-family: 'Outfit', sans-serif; }}
.salary-table tbody td:first-child a {{ color: var(--ink); text-decoration: none; }}
.salary-table tbody td:first-child a:hover {{ color: var(--ice); }}
.salary-table tbody tr:last-child td {{ border-bottom: none; }}
.salary-table tbody tr:hover {{ background: var(--surface2); }}
.salary-table .net {{ color: var(--ice); font-weight: 500; }}
.card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 26px; }}
.card-label {{ font-size: 10px; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; color: var(--ink3); margin-bottom: 20px; }}
.bd-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 18px; }}
@media (max-width: 500px) {{ .bd-grid {{ grid-template-columns: 1fr 1fr; }} }}
.bd-item {{ background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 13px 15px; }}
.bd-label {{ font-size: 10px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink3); margin-bottom: 4px; }}
.bd-val {{ font-family: 'DM Mono', monospace; font-size: 0.98rem; font-weight: 500; color: var(--ink); }}
.bd-item.pos .bd-val {{ color: var(--pine); }}
.bd-item.neg .bd-val {{ color: var(--red); }}
.net-hero {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 28px; position: relative; overflow: hidden; }}
.net-hero::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent 0%, var(--ice) 40%, transparent 100%); opacity: 0.4; }}
.hero-eyebrow {{ font-size: 10px; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; color: var(--ink3); margin-bottom: 10px; }}
.hero-amount {{ font-family: 'DM Mono', monospace; font-size: clamp(2.4rem, 4vw, 3.2rem); font-weight: 500; letter-spacing: -0.03em; line-height: 1; color: var(--ink); }}
.hero-amount .amt-num {{ color: var(--ice); }}
.hero-amount .amt-unit {{ font-size: 1rem; color: var(--ink3); font-weight: 400; margin-left: 4px; }}
.hero-sub {{ font-size: 12px; color: var(--ink3); margin-top: 8px; font-weight: 300; }}
.divider {{ height: 1px; background: var(--border); margin: 18px 0; }}
.related-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; max-width: 680px; margin: 0 auto; }}
@media (max-width: 600px) {{ .related-grid {{ grid-template-columns: 1fr 1fr; }} }}
.related-c {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px 16px; text-decoration: none; transition: border-color 0.15s, background 0.15s; }}
.related-c:hover {{ border-color: var(--border2); background: var(--surface2); }}
.related-name {{ font-size: 13px; font-weight: 500; color: var(--ink); margin-bottom: 3px; }}
.related-rate {{ font-family: 'DM Mono', monospace; font-size: 11px; color: var(--ice); }}
.faq-section {{ max-width: 680px; margin: 40px auto 0; scroll-margin-top: 64px; }}
.faq-section h2 {{ font-size: 1.5rem; font-weight: 600; color: var(--ink); margin-bottom: 20px; letter-spacing: -0.02em; }}
.faq-item {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); margin-bottom: 8px; overflow: hidden; transition: border-color 0.15s; }}
.faq-item[open] {{ border-color: var(--border2); }}
.faq-item summary {{ padding: 14px 18px; font-size: 0.92rem; font-weight: 500; color: var(--ink); cursor: pointer; list-style: none; display: flex; justify-content: space-between; align-items: center; gap: 12px; }}
.faq-item summary::-webkit-details-marker {{ display: none; }}
.faq-item summary::after {{ content: '+'; color: var(--ice); font-size: 1.2rem; font-weight: 300; transition: transform 0.2s; flex-shrink: 0; }}
.faq-item[open] summary::after {{ transform: rotate(45deg); }}
.faq-item summary:hover {{ background: var(--surface2); }}
.faq-item p {{ padding: 0 18px 16px; font-size: 0.88rem; color: var(--ink2); line-height: 1.7; font-weight: 300; }}
footer {{ border-top: 1px solid var(--border); padding: 28px 20px; text-align: center; font-size: 11px; color: var(--ink3); line-height: 1.9; }}
footer a {{ color: var(--ink3); }}
</style>
</head>
<body>

<nav class="main-nav">
  <a href="/" class="nav-brand">lön<span>efterskatt</span>.com</a>
  <button class="nav-toggle" onclick="toggleMenu()" aria-label="Meny">&#9776;</button>
  <ul class="nav-links" id="nav-links">
    <li><a href="/#faq">Vanliga frågor</a></li>
    <li><a href="/kommunerna-med-lagst-skatt-i-sverige-2026.html">Kommuner med lägst skatt 2026</a></li>
    <li><a href="/varfor-forsvinner-sa-mycket-av-min-lon-i-skatt.html">Varför försvinner så mycket av min lön i skatt?</a></li>
    <li><a href="/sa-mycket-mindre-skatt-betalar-du-som-jobbar.html">Jobbskatteavdraget</a></li>
    <li><a href="/sa-mycket-sparar-du-pa-att-ga-ur-svenska-kyrkan.html">Gå ur Svenska kyrkan</a></li>
  </ul>
</nav>

<nav class="breadcrumb" aria-label="Brödsmulor">
  <a href="/">Hem</a>
  <span class="sep">›</span>
  <a href="/lon-efter-skatt-{slug}.html">Lön efter skatt {name}</a>
  <span class="sep">›</span>
  <span class="current">{sal_label}/mån</span>
</nav>

<header class="kommun-header">
  <div class="eyebrow">Uppdaterad för 2026</div>
  <h1>{sal_label}/mån efter skatt<br><em>i {name}</em></h1>
  <p>Med en bruttolön på {sal_label} i månaden och {name}s kommunalskatt på {rate}% blir nettolönen <strong>{fmt_kr(net)}</strong> per månad 2026.</p>
</header>

<div class="container">

  <div class="fact-box">
    <div class="fact">
      <div class="fact-label">Nettolön / månad</div>
      <div class="fact-val">{fmt_se(net)}</div>
      <div class="fact-sub">kr per månad</div>
    </div>
    <div class="fact">
      <div class="fact-label">Effektiv skatt</div>
      <div class="fact-val">{eff}%</div>
      <div class="fact-sub">kommunalskatt {rate}%</div>
    </div>
    <div class="fact">
      <div class="fact-label">Vs rikssnitt</div>
      <div class="fact-val">{diff_str}</div>
      <div class="fact-sub">per månad</div>
    </div>
  </div>

  <div class="prose">
    <p>En bruttolön på <strong>{sal_label} per månad</strong> i {name} ({region}) ger en nettolön på <strong>{fmt_kr(net)}</strong> efter skatt 2026. {name}s kommunalskatt är {rate} procent — {diff_pe} procentenheter {above_below} än rikssnittet på {RIKSSNITT} procent.</p>
    <p>Jämfört med en genomsnittskommun får du {diff_str} per månad, eller {diff_year_str} per år, {'mer' if diff >= 0 else 'mindre'} i plånboken.</p>
  </div>

  <div class="prose">
    <h2>Skatteuppdelning — {sal_label}/mån i {name}</h2>
  </div>

  <div class="grid" style="margin-top: 18px;">
    <div class="card">
      <div class="card-label">Beräkning per månad</div>
      <div class="bd-grid">
        <div class="bd-item">
          <div class="bd-label">Bruttolön</div>
          <div class="bd-val">{fmt_kr(salary)}</div>
        </div>
        <div class="bd-item pos">
          <div class="bd-label">Grundavdrag</div>
          <div class="bd-val">{fmt_kr(round(grundavdrag_normal(gy)/12))}</div>
        </div>
        <div class="bd-item pos">
          <div class="bd-label">Jobbskatteavdrag</div>
          <div class="bd-val">{fmt_kr(jobb_av_month)}</div>
        </div>
        <div class="bd-item neg">
          <div class="bd-label">Kommunalskatt</div>
          <div class="bd-val">{fmt_kr(tax_kom_month)}</div>
        </div>
        <div class="bd-item neg">
          <div class="bd-label">Statlig skatt</div>
          <div class="bd-val">{fmt_kr(tax_stat_month)}</div>
        </div>
        <div class="bd-item neg">
          <div class="bd-label">Begravningsavgift</div>
          <div class="bd-val">{fmt_kr(tax_beg_month)}</div>
        </div>
      </div>
    </div>

    <div class="net-hero">
      <div class="hero-eyebrow">Lön efter skatt / månad</div>
      <div class="hero-amount">
        <span class="amt-num">{fmt_se(net)}</span><span class="amt-unit">kr</span>
      </div>
      <div class="hero-sub">{fmt_kr(net*12)} per år</div>
      <div class="divider"></div>
      <p style="font-size: 12px; color: var(--ink3);">
        Räkna med kyrkoavgift och exakt församling i <a href="/" style="color:var(--ice);">huvudkalkylatorn</a>.
      </p>
    </div>
  </div>

  <div class="prose">
    <h2>{sal_label}/mån — jämförelse alla kommuner</h2>
    <p>Så här skiljer sig nettolönen för {sal_label} i månaden beroende på kommun:</p>
  </div>

  <div class="salary-table-wrap">
    <table class="salary-table">
      <thead>
        <tr>
          <th>Kommun</th>
          <th>Skattesats</th>
          <th>Skatt / mån</th>
          <th>Netto / mån</th>
        </tr>
      </thead>
      <tbody>
{table_rows}      </tbody>
    </table>
  </div>

  <div class="prose">
    <h2>Relaterade kommuner — {sal_label}/mån</h2>
    <p>Se nettolönen för {sal_label} i andra kommuner:</p>
  </div>

  <div class="related-grid">
{related_cards_html}  </div>

  <div class="prose" style="margin-top:40px;">
    <p>Läs mer om lön efter skatt i <a href="/lon-efter-skatt-{slug}.html">{name}</a> generellt, eller se hur {sal_label} ser ut vid <a href="/lon-efter-skatt-{sal_no_space}.html">alla kommuner på riksnivå</a>.</p>
  </div>

  <section class="faq-section" id="faq" aria-labelledby="faq-rubrik">
    <h2 id="faq-rubrik">Vanliga frågor — {sal_label}/mån i {name}</h2>

    <details class="faq-item">
      <summary>{faq_q1}</summary>
      <p>{faq_a1}</p>
    </details>

    <details class="faq-item">
      <summary>{faq_q2}</summary>
      <p>{faq_a2}</p>
    </details>

    <details class="faq-item">
      <summary>{faq_q3}</summary>
      <p>{faq_a3}</p>
    </details>

    <details class="faq-item">
      <summary>{faq_q4}</summary>
      <p>{faq_a4}</p>
    </details>
  </section>

</div>

<footer>
  Beräkningarna bygger på Skatteverkets och SCBs officiella skattesatser för 2026.<br>
  Resultaten är uppskattningar – kontakta Skatteverket för exakt besked.
  <a href="/integritetspolicy.html">Integritetspolicy</a>
</footer>

<script>
function toggleMenu() {{ document.getElementById('nav-links').classList.toggle('open'); }}
</script>

</body>
</html>
"""
    return html


def main():
    total = 0
    for salary in SALARY_LEVELS:
        for kommun in KOMMUNER:
            filename = f"lon-efter-skatt-{salary}-{kommun['slug']}.html"
            filepath = os.path.join(OUTPUT_DIR, filename)
            content = generate_page(salary, kommun)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            total += 1
            print(f"  Skapade: {filename}")
    print(f"\nKlart! {total} kombisidor skapade.")


if __name__ == "__main__":
    main()
