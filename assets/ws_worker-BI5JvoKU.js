async function e(e){let t=await crypto.subtle.digest(`SHA-256`,e);return Array.from(new Uint8Array(t)).map(e=>e.toString(16).padStart(2,`0`)).join(``)}const t=self;let n=null;async function r(e){let n=e=>t.postMessage({kind:`status`,text:e});n(e.msg.loading);let r=await(await import(
/* @vite-ignore */
e.base+`pyodide/pyodide.mjs`)).loadPyodide({indexURL:e.base+`pyodide/`});for(let t of e.wheels){n(`${e.msg.installing} ${t}…`);let i=await fetch(e.base+`downloads/wheels/`+t);if(!i.ok)throw Error(`${e.msg.http} ${t} (HTTP ${i.status})`);r.globals.set(`_wheel_bytes`,new Uint8Array(await i.arrayBuffer())),await r.runPythonAsync(`import io, site, zipfile
zipfile.ZipFile(io.BytesIO(bytes(_wheel_bytes.to_py()))).extractall(site.getsitepackages()[0])
del _wheel_bytes
`)}return r.globals.set(`_wp_src`,`"""S.T.A.R. everyday products (first batch, 2026-10-20): Italian tax code, Italian VAT number, IBAN, working days.\r
\r
Pure Python (standard library only), so it runs unchanged in the visitor's browser (Pyodide) and under pytest, where it\r
is compared with independent implementations (python-stdnum, schwifty, holidays, dateutil) that are NEVER shipped.\r
Same contract as ws_tasks.py: a task returns result, tools, transforms, checks, warnings; errors carry a code.\r
\r
Sources of the rules:\r
  codice fiscale  D.M. 23/12/1976 (format and check character), D.P.R. 605/1973; omocodia: letters L-V replace the\r
                  digits from the right (Agenzia delle Entrate)\r
  partita IVA     11 digits: 7 serial, 3 office code, 1 check digit computed with the Luhn mod-10 rule\r
  IBAN            ISO 13616 (structure), ISO 7064 MOD 97-10 (check digits), SWIFT IBAN registry (lengths)\r
  working days    L. 260/1949 art. 2 as amended (national holidays; 4 October from 2026, L. 151/2025; 17 March 2011 only,\r
                  D.L. 5/2011), Gregorian Easter\r
"""\r
from __future__ import annotations\r
\r
import datetime as dt\r
import re\r
import unicodedata\r
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation\r
\r
VERSION = "0.1.0"\r
TOOL = {"name": "S.T.A.R. everyday products (ws_products)", "version": VERSION}\r
\r
\r
class ProductError(Exception):\r
    """Same shape as ws_tasks.TaskError (code + args_), so the page shows a translated message, never a traceback."""\r
    def __init__(self, code, **args):\r
        super().__init__(code)\r
        self.code, self.args_ = code, args\r
\r
\r
def _answer(result, transforms, checks, warnings, tools=None):\r
    return {"ok": True, "result": result, "tools": tools or [TOOL], "transforms": transforms, "checks": checks, "warnings": warnings}\r
\r
\r
def _clean(text, field, allow=r"[\\s\\-\\.]"):\r
    s = "" if text is None else str(text)\r
    if not s.strip():\r
        raise ProductError("empty", field=field)\r
    if len(s) > 200:\r
        raise ProductError("too_long", field=field, limit=200)\r
    c = re.sub(allow, "", s).upper()\r
    tr = [{"code": "normalised", "before": s.strip()[:60], "after": c}] if c != s.strip() else []\r
    return c, tr\r
\r
\r
# ---------------------------------------------------------------- shared: the odd/even tables of the Italian check characters\r
ODD = {**dict(zip("0123456789", [1, 0, 5, 7, 9, 13, 15, 17, 19, 21])),\r
       **dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", [1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20, 11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24, 23]))}\r
EVEN = {**{d: int(d) for d in "0123456789"}, **{ch: i for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}}\r
\r
\r
def _odd_even_char(s):\r
    """Check character of the codice fiscale and of the Italian bank CIN: odd positions (1st, 3rd, ...) through ODD,\r
    even ones through EVEN, sum modulo 26 as a letter."""\r
    total = sum(ODD[ch] if i % 2 == 0 else EVEN[ch] for i, ch in enumerate(s))\r
    return chr(ord("A") + total % 26)\r
\r
\r
# ---------------------------------------------------------------- 1. codice fiscale\r
OMO = dict(zip("LMNPQRSTUV", "0123456789"))\r
OMO_POS = [14, 13, 12, 10, 9, 7, 6]           # digit positions, in the order the Agenzia substitutes them (right to left)\r
MONTHS = dict(zip("ABCDEHLMPRST", range(1, 13)))\r
CF_RE = re.compile(r"[A-Z]{6}[0-9LMNPQRSTUV]{2}[ABCDEHLMPRST][0-9LMNPQRSTUV]{2}[A-Z][0-9LMNPQRSTUV]{3}[A-Z]")\r
\r
\r
def cf_check_char(first15):\r
    return _odd_even_char(first15)\r
\r
\r
def _letters(word):\r
    w = re.sub(r"[^A-Z]", "", _strip_accents(word).upper())\r
    cons = [c for c in w if c not in "AEIOU"]\r
    vows = [c for c in w if c in "AEIOU"]\r
    return cons, vows\r
\r
\r
def _strip_accents(s):\r
    table = str.maketrans("ÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜàáâäèéêëìíîïòóôöùúûüÇçÑñ", "AAAAEEEEIIIIOOOOUUUUaaaaeeeeiiiioooouuuuCcNn")\r
    return str(s).translate(table)\r
\r
\r
def cf_surname_code(surname):\r
    cons, vows = _letters(surname)\r
    return "".join((cons + vows + ["X"] * 3)[:3])\r
\r
\r
def cf_name_code(name):\r
    cons, vows = _letters(name)\r
    if len(cons) >= 4:\r
        return cons[0] + cons[2] + cons[3]\r
    return "".join((cons + vows + ["X"] * 3)[:3])\r
\r
\r
def task_cf(params):\r
    code, tr = _clean(params.get("code"), "code")\r
    if len(code) != 16:\r
        raise ProductError("cf_length", n=len(code))\r
    if not CF_RE.fullmatch(code):\r
        raise ProductError("cf_format")\r
    checks, warnings = [], []\r
    expected = cf_check_char(code[:15])\r
    checks.append({"code": "cf_check_char", "ok": expected == code[15], "args": {"expected": expected, "found": code[15]}})\r
    letters_at = [p for p in OMO_POS if code[p] in OMO]\r
    omocode = bool(letters_at)\r
    if omocode:\r
        in_order = letters_at == OMO_POS[:len(letters_at)]\r
        checks.append({"code": "cf_omocode_order", "ok": in_order, "args": {"n": len(letters_at)}})\r
    base = "".join(OMO.get(ch, ch) if i in OMO_POS else ch for i, ch in enumerate(code))\r
    yy, month, day = int(base[6:8]), MONTHS[base[8]], int(base[9:11])\r
    sex = "F" if day > 40 else "M"\r
    dd = day - 40 if day > 40 else day\r
    today = dt.date.today()\r
    births = []\r
    for century in (1900, 2000):\r
        try:\r
            d = dt.date(century + yy, month, dd)\r
        except ValueError:\r
            continue\r
        if d <= today:\r
            births.append(d.isoformat())\r
    checks.append({"code": "cf_birth_date", "ok": bool(births), "args": {"day": day, "month": month}})\r
    place = base[11:15]\r
    res = {"code": code, "valid": all(c["ok"] for c in checks if c["code"] != "cf_omocode_order"),\r
           "check_char_expected": expected, "omocode": omocode, "omocode_positions": len(letters_at), "base_code": base[:15] + cf_check_char(base[:15]),\r
           "sex": sex, "birth_day": dd, "birth_month": month, "birth_year_2digit": f"{yy:02d}", "birth_date_candidates": births,\r
           "place_code": place, "place_kind": "foreign_country" if place[0] == "Z" else "italian_municipality",\r
           "surname_code": code[:3], "name_code": code[3:6]}\r
    for key, fn, field in (("surname", cf_surname_code, "surname_code"), ("name", cf_name_code, "name_code")):\r
        given = (params.get(key) or "").strip()\r
        if given:\r
            mine = fn(given)\r
            checks.append({"code": f"cf_{key}_match", "ok": mine == code[:3] if key == "surname" else mine == code[3:6], "args": {"expected": mine}})\r
            res[f"{key}_given_code"] = mine\r
    if omocode:\r
        warnings.append({"code": "cf_omocode", "args": {"base": res["base_code"]}})\r
    if len(births) == 2:\r
        warnings.append({"code": "cf_century_ambiguous", "args": {"a": births[0][:4], "b": births[1][:4]}})\r
    warnings.append({"code": "cf_not_registry", "args": {}})\r
    return _answer(res, tr, checks, warnings)\r
\r
\r
# ---------------------------------------------------------------- 2. partita IVA\r
def piva_check_digit_italian(first10):\r
    """The rule as written for the partita IVA: digits in odd positions (1st, 3rd, ... 9th) added; digits in even positions\r
    (2nd ... 10th) doubled, minus 9 when the double exceeds 9, then added; check digit = (10 - total mod 10) mod 10."""\r
    total = 0\r
    for i, ch in enumerate(first10):\r
        d = int(ch)\r
        if i % 2 == 1:\r
            d *= 2\r
            d = d - 9 if d > 9 else d\r
        total += d\r
    return (10 - total % 10) % 10\r
\r
\r
def luhn_check_digit(payload):\r
    """The Luhn mod-10 rule, as usually stated: from the right of the payload, double every second digit starting with\r
    the rightmost one."""\r
    total = 0\r
    for i, ch in enumerate(reversed(payload)):\r
        d = int(ch)\r
        if i % 2 == 0:\r
            d *= 2\r
            d = d - 9 if d > 9 else d\r
        total += d\r
    return (10 - total % 10) % 10\r
\r
\r
def task_piva(params):\r
    code, tr = _clean(params.get("code"), "code")\r
    if code.startswith("IT"):\r
        tr.append({"code": "country_prefix_removed", "before": code, "after": code[2:]})\r
        code = code[2:]\r
    if not code.isdigit():\r
        raise ProductError("piva_digits")\r
    if len(code) != 11:\r
        raise ProductError("piva_length", n=len(code))\r
    expected = piva_check_digit_italian(code[:10])\r
    office = int(code[7:10])\r
    checks = [{"code": "piva_check_digit", "ok": expected == int(code[10]), "args": {"expected": expected, "found": int(code[10])}},\r
              {"code": "piva_office_code", "ok": 1 <= office <= 100 or office in (120, 121, 888, 999), "args": {"office": f"{office:03d}"}},\r
              {"code": "piva_serial", "ok": code[:7] != "0000000", "args": {}}]\r
    res = {"code": code, "valid": all(c["ok"] for c in checks), "serial": code[:7], "office_code": f"{office:03d}",\r
           "check_digit_expected": expected, "luhn_same": luhn_check_digit(code[:10]) == expected}\r
    return _answer(res, tr, checks, [{"code": "piva_not_vies", "args": {}}])\r
\r
\r
# ---------------------------------------------------------------- 3. IBAN\r
# total IBAN length per country (SWIFT IBAN registry); checked in the tests against python-stdnum and schwifty\r
IBAN_LEN = {\r
    "AD": 24, "AE": 23, "AL": 28, "AT": 20, "AZ": 28, "BA": 20, "BE": 16, "BG": 22, "BH": 22, "BI": 27, "BR": 29, "BY": 28,\r
    "CH": 21, "CR": 22, "CY": 28, "CZ": 24, "DE": 22, "DJ": 27, "DK": 18, "DO": 28, "EE": 20, "EG": 29, "ES": 24, "FI": 18,\r
    "FK": 18, "FO": 18, "FR": 27, "GB": 22, "GE": 22, "GI": 23, "GL": 18, "GR": 27, "GT": 28, "HN": 28, "HR": 21, "HU": 28,\r
    "IE": 22, "IL": 23, "IQ": 23, "IS": 26, "IT": 27, "JO": 30, "KW": 30, "KZ": 20, "LB": 28, "LC": 32, "LI": 21, "LT": 20,\r
    "LU": 20, "LV": 21, "LY": 25, "MC": 27, "MD": 24, "ME": 22, "MK": 19, "MN": 20, "MR": 27, "MT": 31, "MU": 30, "NI": 28,\r
    "NL": 18, "NO": 15, "OM": 23, "PK": 24, "PL": 28, "PS": 29, "PT": 25, "QA": 29, "RO": 24, "RS": 22, "RU": 33, "SA": 24,\r
    "SC": 31, "SD": 18, "SE": 24, "SI": 19, "SK": 24, "SM": 27, "SO": 23, "ST": 25, "SV": 28, "TL": 23, "TN": 24, "TR": 26,\r
    "UA": 29, "VA": 22, "VG": 24, "XK": 20, "YE": 30,\r
}\r
\r
\r
def iban_mod97(iban):\r
    moved = iban[4:] + iban[:4]\r
    digits = "".join(str(int(ch, 36)) for ch in moved)\r
    return int(digits) % 97\r
\r
\r
def iban_check_digits(country, bban):\r
    return f"{98 - iban_mod97(country + '00' + bban):02d}"\r
\r
\r
def it_cin(abi_cab_account):\r
    return _odd_even_char(abi_cab_account)\r
\r
\r
def task_iban(params):\r
    code, tr = _clean(params.get("code"), "code")\r
    if code.startswith("IBAN"):\r
        tr.append({"code": "iban_prefix_removed", "before": code, "after": code[4:]})\r
        code = code[4:]\r
    if not re.fullmatch(r"[A-Z0-9]+", code):\r
        raise ProductError("iban_chars")\r
    if len(code) < 5 or not code[:2].isalpha() or not code[2:4].isdigit():\r
        raise ProductError("iban_format")\r
    country = code[:2]\r
    if country not in IBAN_LEN:\r
        raise ProductError("iban_country", country=country)\r
    checks = [{"code": "iban_length", "ok": len(code) == IBAN_LEN[country], "args": {"expected": IBAN_LEN[country], "found": len(code)}}]\r
    checks.append({"code": "iban_mod97", "ok": iban_mod97(code) == 1, "args": {"expected": iban_check_digits(country, code[4:]), "found": code[2:4]}})\r
    res = {"iban": code, "printed": " ".join(code[i:i + 4] for i in range(0, len(code), 4)), "country": country,\r
           "check_digits": code[2:4], "bban": code[4:]}\r
    if country in ("IT", "SM") and len(code) == 27:\r
        bban = code[4:]\r
        res.update(cin=bban[0], abi=bban[1:6], cab=bban[6:11], account=bban[11:])\r
        ok_shape = bool(re.fullmatch(r"[A-Z]\\d{10}[A-Z0-9]{12}", bban))\r
        checks.append({"code": "it_bban_format", "ok": ok_shape, "args": {}})\r
        if ok_shape:\r
            exp = it_cin(bban[1:])\r
            checks.append({"code": "it_cin", "ok": exp == bban[0], "args": {"expected": exp, "found": bban[0]}})\r
    res["valid"] = all(c["ok"] for c in checks)\r
    return _answer(res, tr, checks, [{"code": "iban_not_account", "args": {}}])\r
\r
\r
# ---------------------------------------------------------------- 4. working days and deadlines\r
def easter(year):\r
    """Gregorian Easter Sunday (the anonymous algorithm published by Meeus, valid for every Gregorian year)."""\r
    a, b, c = year % 19, year // 100, year % 100\r
    d, e = b // 4, b % 4\r
    f = (b + 8) // 25\r
    g = (b - f + 1) // 3\r
    h = (19 * a + b - d - g + 15) % 30\r
    i, k = c // 4, c % 4\r
    ll = (32 + 2 * e + 2 * i - h - k) % 7\r
    m = (a + 11 * h + 22 * ll) // 451\r
    month = (h + ll - 7 * m + 114) // 31\r
    day = (h + ll - 7 * m + 114) % 31 + 1\r
    return dt.date(year, month, day)\r
\r
\r
FIXED = [((1, 1), "new_year"), ((1, 6), "epiphany"), ((4, 25), "liberation"), ((5, 1), "labour"), ((6, 2), "republic"),\r
         ((8, 15), "assumption"), ((11, 1), "all_saints"), ((12, 8), "immaculate"), ((12, 25), "christmas"), ((12, 26), "st_stephen")]\r
YEAR_MIN, YEAR_MAX = 2001, 2099      # 2 June has been a holiday again since 2001 (L. 336/2000)\r
\r
\r
def holidays_it(year, patron=None):\r
    """National holidays of Italy for a year (L. 260/1949 art. 2 as amended), plus an optional local patron day (month, day)."""\r
    if not YEAR_MIN <= year <= YEAR_MAX:\r
        raise ProductError("year_range", min=YEAR_MIN, max=YEAR_MAX, year=year)\r
    out = {dt.date(year, m, d): name for (m, d), name in FIXED}\r
    if year >= 2026:                                   # L. 8 ottobre 2025, n. 151\r
        out[dt.date(year, 10, 4)] = "st_francis"\r
    if year == 2011:                                   # one-off: 150 years of the unification of Italy (D.L. 22 febbraio 2011, n. 5)\r
        out[dt.date(2011, 3, 17)] = "unification_150"\r
    e = easter(year)\r
    out[e] = "easter"\r
    out[e + dt.timedelta(days=1)] = "easter_monday"\r
    if patron:\r
        try:\r
            p = dt.date(year, patron[0], patron[1])\r
        except ValueError:\r
            raise ProductError("patron_date", value=f"{patron[1]:02d}/{patron[0]:02d}") from None\r
        out.setdefault(p, "patron")\r
    return out\r
\r
\r
def _parse_date(text, field):\r
    s = "" if text is None else str(text).strip()\r
    if not s:\r
        raise ProductError("empty", field=field)\r
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):\r
        try:\r
            return dt.datetime.strptime(s, fmt).date()\r
        except ValueError:\r
            pass\r
    raise ProductError("bad_date", field=field, value=s[:30])\r
\r
\r
def _parse_patron(text):\r
    s = "" if text is None else str(text).strip()\r
    if not s:\r
        return None\r
    m = re.fullmatch(r"(\\d{1,2})[/\\-.](\\d{1,2})", s)\r
    if not m:\r
        raise ProductError("bad_patron", value=s[:20])\r
    return (int(m.group(2)), int(m.group(1)))          # typed as day/month\r
\r
\r
def _is_working(d, hol, saturday_working):\r
    if d.weekday() == 6 or (d.weekday() == 5 and not saturday_working):\r
        return False\r
    return d not in hol\r
\r
\r
def _holidays_between(a, b, patron):\r
    hol = {}\r
    for y in range(a.year, b.year + 1):\r
        hol.update(holidays_it(y, patron))\r
    return hol\r
\r
\r
def task_workdays(params):\r
    mode = params.get("mode") or "between"\r
    patron = _parse_patron(params.get("patron"))\r
    sat = bool(params.get("saturday_working"))\r
    start = _parse_date(params.get("start"), "start")\r
    checks, warnings, tr = [], [], []\r
    if mode == "between":\r
        end = _parse_date(params.get("end"), "end")\r
        if end < start:\r
            start, end = end, start\r
            tr.append({"code": "dates_swapped", "before": "", "after": ""})\r
        if (end - start).days > 3660:\r
            raise ProductError("span_too_long", limit_years=10)\r
        hol = _holidays_between(start, end, patron)\r
        days = [start + dt.timedelta(days=k) for k in range((end - start).days + 1)]\r
        working = [d for d in days if _is_working(d, hol, sat)]\r
        listed = sorted((d, n) for d, n in hol.items() if start <= d <= end)\r
        res = {"mode": mode, "start": start.isoformat(), "end": end.isoformat(), "calendar_days": len(days),\r
               "working_days": len(working), "both_ends_included": True,\r
               "weekend_days": sum(1 for d in days if d.weekday() == 6 or (d.weekday() == 5 and not sat)),\r
               "holidays_on_weekdays": [[d.isoformat(), n] for d, n in listed if d.weekday() < (6 if sat else 5)],\r
               "holidays_all": [[d.isoformat(), n] for d, n in listed]}\r
    else:\r
        n = params.get("n")\r
        try:\r
            n = int(str(n).strip())\r
        except (TypeError, ValueError):\r
            raise ProductError("bad_n", value=str(n)[:20]) from None\r
        if not 1 <= n <= 1000:\r
            raise ProductError("n_range", min=1, max=1000)\r
        hol = _holidays_between(start, start + dt.timedelta(days=n * 3 + 400), patron)\r
        d, count, skipped = start, 0, []\r
        while count < n:\r
            d += dt.timedelta(days=1)\r
            if _is_working(d, hol, sat):\r
                count += 1\r
            elif d in hol:\r
                skipped.append([d.isoformat(), hol[d]])\r
        res = {"mode": mode, "start": start.isoformat(), "n": n, "deadline": d.isoformat(), "weekday": d.weekday(),\r
               "start_day_counted": False, "holidays_skipped": skipped}\r
    res["saturday_working"] = sat\r
    res["patron"] = f"{patron[1]:02d}/{patron[0]:02d}" if patron else ""\r
    # bridge days ("ponti"): a working day between a holiday and the weekend, in the period shown\r
    a, b = dt.date.fromisoformat(res["start"]), dt.date.fromisoformat(res.get("end") or res["deadline"])\r
    hol_all = _holidays_between(a, b, patron)\r
    bridges = []\r
    if not sat:      # a bridge sits between a holiday and the weekend: Monday before a Tuesday holiday, Friday after a Thursday one\r
        for h in sorted(x for x in hol_all if a <= x <= b):\r
            for cand, wd in ((h - dt.timedelta(days=1), 0), (h + dt.timedelta(days=1), 4)):\r
                if a <= cand <= b and cand.weekday() == wd and _is_working(cand, hol_all, sat):\r
                    bridges.append(cand.isoformat())\r
    res["bridge_days"] = sorted(set(bridges))\r
    e = easter(a.year)\r
    checks.append({"code": "easter_rule", "ok": e.weekday() == 6 and dt.date(a.year, 3, 22) <= e <= dt.date(a.year, 4, 25), "args": {"date": e.isoformat()}})\r
    warnings.append({"code": "wd_rules", "args": {}})\r
    return _answer(res, tr, checks, warnings)\r
\r
\r
# ---------------------------------------------------------------- 5-8. second batch (M12, 2026-10-21)\r
# Table comparison, duplicate or similar rows, VAT reconciliation in exact decimal arithmetic, file metadata and privacy.\r
# Same contract; compared in tests/test_products2.py with independent implementations (pandas, rapidfuzz, fractions,\r
# Pillow, exifread, pypdf, python-docx, openpyxl) that are never shipped.\r
MAX_DIFF_LIST, MAX_SIMILAR_ROWS = 500, 400\r
\r
\r
def _tables():\r
    import ws_tasks                                      # here: ws_tasks imports this module at its end\r
    return ws_tasks\r
\r
\r
def dec(cell, decimal_comma=False):\r
    """A cell as an exact Decimal, or None: '1.234,50' (Italian), '1,234.50', '1234.5', '€ 12,00', '-3'. Never a float."""\r
    c = "" if cell is None else str(cell).strip().replace("−", "-").replace("€", "").replace("EUR", "").replace("\xA0", "").replace(" ", "")\r
    if not c:\r
        return None\r
    # '12.340' alone is ambiguous: twelve point three four in a table written with points, 12,340 in one written with\r
    # commas. It follows the table's convention; two or more groups ('1.234.567') or groups before a decimal comma\r
    # ('1.234,50') are thousands in any table. (FAIL-0051, 2026-10-21: '12.340' read as 12340 in a point table made the\r
    # table comparison report a price written with a trailing zero as changed - found by qa/volume_products_chdb.py)\r
    if (re.fullmatch(r"[+-]?\\d{1,3}(\\.\\d{3})+,\\d+", c) or re.fullmatch(r"[+-]?\\d{1,3}(\\.\\d{3}){2,}", c)\r
            or (decimal_comma and re.fullmatch(r"[+-]?\\d{1,3}(\\.\\d{3})+", c))\r
            or (decimal_comma and re.fullmatch(r"[+-]?\\d+,\\d+", c)) or re.fullmatch(r"[+-]?\\d+,\\d{1,2}", c)):\r
        c = c.replace(".", "").replace(",", ".")\r
    elif re.fullmatch(r"[+-]?\\d{1,3}(,\\d{3})+(\\.\\d+)?", c):\r
        c = c.replace(",", "")\r
    if not re.fullmatch(r"[+-]?(\\d+(\\.\\d*)?|\\.\\d+)", c):\r
        return None\r
    try:\r
        return Decimal(c)\r
    except InvalidOperation:\r
        return None\r
\r
\r
def _same(a, b, dca, dcb):\r
    """Two cells are equal if the text is equal, or if both are numbers with the same exact value ('1,50' and '1.5')."""\r
    if a.strip() == b.strip():\r
        return True\r
    x, y = dec(a, dca), dec(b, dcb)\r
    return x is not None and y is not None and x == y\r
\r
\r
def task_tablediff(params):\r
    wt = _tables()\r
    ta, tb = wt._read_table(params.get("a")), wt._read_table(params.get("b"))\r
    if not (ta["header"] and tb["header"]):\r
        raise ProductError("diff_header")\r
    key = str(params.get("key") or "").strip()\r
    common = [n for n in ta["names"] if n in tb["names"]]\r
    if key and key not in common:\r
        raise ProductError("diff_key_missing", key=key)\r
    key = key or (common[0] if common else "")\r
    if not key:\r
        raise ProductError("diff_no_common")\r
    def index(t, which):\r
        k = t["names"].index(key)\r
        out, dup = {}, []\r
        for r in t["body"]:\r
            if len(r) <= k:\r
                continue\r
            v = r[k].strip()\r
            if v in out:\r
                dup.append(v)\r
            out[v] = dict(zip(t["names"], r))\r
        if dup:\r
            raise ProductError("diff_key_duplicate", table=which, key=key, values=", ".join(sorted(set(dup))[:10]))\r
        return out\r
    A, B = index(ta, "A"), index(tb, "B")\r
    cols = [c for c in common if c != key]\r
    changes, unchanged = [], 0\r
    for k in A.keys() & B.keys():\r
        row = [(c, A[k].get(c, ""), B[k].get(c, "")) for c in cols if not _same(A[k].get(c, ""), B[k].get(c, ""), ta["decimal_comma"], tb["decimal_comma"])]\r
        if row:\r
            changes += [{"key": k, "column": c, "a": x, "b": y} for c, x, y in row]\r
        else:\r
            unchanged += 1\r
    order = {k: i for i, k in enumerate(list(A) + [k for k in B if k not in A])}\r
    changes.sort(key=lambda d: (order[d["key"]], cols.index(d["column"])))\r
    removed = [k for k in A if k not in B]\r
    added = [k for k in B if k not in A]\r
    changed_rows = len({d["key"] for d in changes})\r
    warnings = []\r
    if len(changes) > MAX_DIFF_LIST:\r
        warnings.append({"code": "diff_truncated", "args": {"shown": MAX_DIFF_LIST, "total": len(changes)}})\r
    for t, name in ((ta, "A"), (tb, "B")):\r
        if t["ragged"]:\r
            warnings.append({"code": "diff_ragged", "args": {"table": name, "rows": ", ".join(map(str, t["ragged"][:10]))}})\r
    res = {"key": key, "rows_a": len(A), "rows_b": len(B), "removed": removed[:MAX_DIFF_LIST], "added": added[:MAX_DIFF_LIST],\r
           "n_removed": len(removed), "n_added": len(added), "n_changed_rows": changed_rows, "n_changed_cells": len(changes), "n_unchanged": unchanged,\r
           "changes": changes[:MAX_DIFF_LIST], "columns_compared": cols,\r
           "only_in_a": [c for c in ta["names"] if c not in tb["names"]], "only_in_b": [c for c in tb["names"] if c not in ta["names"]]}\r
    checks = [{"code": "diff_identical", "ok": not (removed or added or changes), "args": {}}]\r
    return _answer(res, ta["transforms"] + tb["transforms"], checks, warnings)\r
\r
\r
def norm_cell(s):\r
    """Accents removed, case folded, punctuation dropped, spaces collapsed: 'Rossi, Mario ' == 'ROSSI MARIO'."""\r
    s = unicodedata.normalize("NFKD", str(s))\r
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).casefold()\r
    s = re.sub(r"[^\\w\\s]", " ", s)\r
    return re.sub(r"\\s+", " ", s).strip()\r
\r
\r
def levenshtein_within(a, b, k):\r
    """Levenshtein distance if it is at most k, else k + 1 (a band of width 2k + 1: fast when k is small)."""\r
    if abs(len(a) - len(b)) > k:\r
        return k + 1\r
    if len(a) > len(b):\r
        a, b = b, a\r
    big = k + 1\r
    prev = [j if j <= k else big for j in range(len(b) + 1)]\r
    for i in range(1, len(a) + 1):\r
        cur = [big] * (len(b) + 1)\r
        lo, hi = max(1, i - k), min(len(b), i + k)\r
        cur[0] = i if i <= k else big\r
        best = cur[0]\r
        for j in range(lo, hi + 1):\r
            v = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))\r
            cur[j] = v if v <= k else big\r
            best = min(best, cur[j])\r
        if best > k:\r
            return k + 1\r
        prev = cur\r
    return prev[len(b)] if prev[len(b)] <= k else k + 1\r
\r
\r
def task_dups(params):\r
    wt = _tables()\r
    t = wt._read_table(params.get("text"))\r
    thr, tr = wt.parse_number(params.get("threshold", "0.9"), "threshold")\r
    if not 0.5 <= thr <= 1:\r
        raise ProductError("dups_threshold")\r
    want = [c.strip() for c in str(params.get("columns") or "").split(",") if c.strip()]\r
    missing = [c for c in want if c not in t["names"]]\r
    if missing:\r
        raise ProductError("dups_columns", columns=", ".join(missing))\r
    idx = [t["names"].index(c) for c in want] if want else list(range(len(t["names"])))\r
    first_line = 2 if t["header"] else 1\r
    sig = [" | ".join(norm_cell(r[i]) if i < len(r) else "" for i in idx) for r in t["body"]]\r
    groups = {}\r
    for n, s in enumerate(sig):\r
        groups.setdefault(s, []).append(n + first_line)\r
    exact = [g for s, g in groups.items() if len(g) > 1 and s.replace("|", "").strip()]\r
    reps = [(g[0], s) for s, g in groups.items() if s.replace("|", "").strip()]\r
    reps.sort()\r
    similar, scanned = [], reps[:MAX_SIMILAR_ROWS]\r
    for x in range(len(scanned)):\r
        la, sa = scanned[x]\r
        for y in range(x + 1, len(scanned)):\r
            lb, sb = scanned[y]\r
            m = max(len(sa), len(sb))\r
            k = int((1 - thr) * m + 1e-9)\r
            d = levenshtein_within(sa, sb, k)\r
            if d <= k:\r
                sim = 1 - d / m if m else 1.0\r
                if sim >= thr:\r
                    similar.append({"rows": [la, lb], "similarity": round(sim, 4), "a": sa[:120], "b": sb[:120]})\r
    similar.sort(key=lambda p: (-p["similarity"], p["rows"]))\r
    warnings = []\r
    if len(reps) > MAX_SIMILAR_ROWS:\r
        warnings.append({"code": "dups_similar_limit", "args": {"limit": MAX_SIMILAR_ROWS, "rows": len(reps)}})\r
    res = {"rows": len(t["body"]), "columns": [t["names"][i] for i in idx], "threshold": thr, "exact_groups": exact,\r
           "n_exact_rows": sum(len(g) - 1 for g in exact), "similar": similar[:MAX_DIFF_LIST], "n_similar": len(similar)}\r
    checks = [{"code": "dups_none", "ok": not exact and not similar, "args": {}}]\r
    return _answer(res, t["transforms"] + ([tr] if tr else []), checks, warnings)\r
\r
\r
CENT = Decimal("0.01")\r
\r
\r
def round_cent(x):\r
    """To the cent, halves away from zero (ROUND_HALF_UP on a Decimal): 0.005 -> 0.01, -0.005 -> -0.01."""\r
    return x.quantize(CENT, rounding=ROUND_HALF_UP)\r
\r
\r
def task_vat(params):\r
    wt = _tables()\r
    t = wt._read_table(params.get("text"))\r
    names = [n.casefold() for n in t["names"]]\r
    def col(match, default):\r
        """The column whose header matches, else the positional default (if the table is that wide)."""\r
        if t["header"]:\r
            for i, n in enumerate(names):\r
                if match(n):\r
                    return i\r
        return default if default is not None and default < len(names) else None\r
    is_base = lambda n: any(w in n for w in ("imponibile", "taxable", "net", "base"))    # noqa: E731\r
    ci = col(is_base, 0)\r
    cr = col(lambda n: any(w in n for w in ("aliquota", "rate", "%")), 1)\r
    cv = col(lambda n: not is_base(n) and any(w in n for w in ("iva", "vat", "imposta", "tax")), 2)\r
    if cv in (ci, cr):\r
        cv = None\r
    first_line = 2 if t["header"] else 1\r
    lines, by_rate, bad = [], {}, []\r
    for n, r in enumerate(t["body"]):\r
        cells = [r[i].strip() if i is not None and i < len(r) else "" for i in (ci, cr, cv)]\r
        base, rate = dec(cells[0], t["decimal_comma"]), dec(cells[1].replace("%", ""), t["decimal_comma"])\r
        if base is None or rate is None or not (0 <= rate <= 100):\r
            bad.append(n + first_line)\r
            continue\r
        vat = round_cent(base * rate / 100)\r
        declared = dec(cells[2], t["decimal_comma"]) if cells[2] else None\r
        lines.append({"row": n + first_line, "taxable": str(base), "rate": str(rate), "vat": str(vat),\r
                      "declared": None if declared is None else str(declared), "difference": None if declared is None else str(declared - vat)})\r
        b = by_rate.setdefault(rate, [Decimal(0), Decimal(0)])\r
        b[0] += base\r
        b[1] += vat\r
    if not lines:\r
        raise ProductError("vat_no_lines")\r
    rates = []\r
    for rate in sorted(by_rate):\r
        base, vat_lines = by_rate[rate]\r
        vat_rate = round_cent(base * rate / 100)\r
        rates.append({"rate": str(rate), "taxable": str(base), "vat_on_total": str(vat_rate), "vat_sum_of_lines": str(vat_lines), "rounding_gap": str(vat_lines - vat_rate)})\r
    total_vat = sum((Decimal(x["vat_on_total"]) for x in rates), Decimal(0))\r
    total_taxable = sum((Decimal(x["taxable"]) for x in rates), Decimal(0))\r
    declared_total = dec(params.get("declared_vat"), t["decimal_comma"]) if str(params.get("declared_vat") or "").strip() else None\r
    if str(params.get("declared_vat") or "").strip() and declared_total is None:\r
        raise ProductError("not_a_number", field="declared_vat", value=str(params.get("declared_vat"))[:40])\r
    mism = [x for x in lines if x["difference"] not in (None, "0", "0.00") and Decimal(x["difference"]) != 0]\r
    checks = [{"code": "vat_lines", "ok": not mism, "args": {"n": len(mism)}}]\r
    if declared_total is not None:\r
        checks.append({"code": "vat_total", "ok": declared_total == total_vat, "args": {"declared": str(declared_total), "computed": str(total_vat), "difference": str(declared_total - total_vat)}})\r
    warnings = [{"code": "vat_skipped", "args": {"rows": ", ".join(map(str, bad[:10])), "n": len(bad)}}] if bad else []\r
    if any(Decimal(x["rounding_gap"]) != 0 for x in rates):\r
        warnings.append({"code": "vat_rounding_gap", "args": {}})\r
    res = {"lines": lines[:MAX_DIFF_LIST], "n_lines": len(lines), "rates": rates, "total_taxable": str(total_taxable), "total_vat": str(total_vat),\r
           "total_invoice": str(total_taxable + total_vat), "declared_vat": None if declared_total is None else str(declared_total), "mismatched_lines": len(mism)}\r
    return _answer(res, t["transforms"], checks, warnings)\r
\r
\r
# ---- file metadata and privacy: JPEG (EXIF, XMP), PNG (text chunks, eXIf), PDF (Info, XMP), Office (docProps)\r
PRIVACY = {"gps": "location", "author": "person", "artist": "person", "creator": "person", "last_modified_by": "person", "company": "person",\r
           "manager": "person", "copyright": "person", "make": "device", "model": "device", "serial": "device", "lens": "device",\r
           "software": "software", "producer": "software", "creator_tool": "software", "application": "software", "template": "software",\r
           "created": "date", "modified": "date", "taken": "date", "title": "content", "subject": "content", "keywords": "content",\r
           "description": "content", "comment": "content", "comments": "content", "tracked_changes": "content", "revision": "content"}\r
EXIF_TAGS = {0x010E: "description", 0x010F: "make", 0x0110: "model", 0x0131: "software", 0x0132: "modified", 0x013B: "artist", 0x8298: "copyright",\r
             0x9003: "taken", 0x9286: "comment", 0xA431: "serial", 0xA434: "lens", 0x9C9D: "author", 0x9C9C: "comment", 0x9C9F: "subject", 0x9C9B: "title"}\r
\r
\r
def _tiff(data):\r
    """Tags of a TIFF/EXIF block: IFD0, the Exif sub-IFD and the GPS IFD (decimal degrees and altitude)."""\r
    import struct\r
    if data[:2] not in (b"II", b"MM"):\r
        raise ProductError("meta_bad")\r
    e = "<" if data[:2] == b"II" else ">"\r
    def u16(o): return struct.unpack(e + "H", data[o:o + 2])[0]\r
    def u32(o): return struct.unpack(e + "I", data[o:o + 4])[0]\r
    sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1, 9: 4, 10: 8}\r
    def ifd(off):\r
        out = {}\r
        if not 0 < off < len(data) - 2:\r
            return out\r
        for i in range(min(u16(off), 512)):\r
            p = off + 2 + 12 * i\r
            if p + 12 > len(data):\r
                break\r
            tag, typ, cnt = u16(p), u16(p + 2), u32(p + 4)\r
            size = sizes.get(typ, 1) * cnt\r
            vo = p + 8 if size <= 4 else u32(p + 8)\r
            raw = data[vo:vo + size]\r
            if typ == 2:\r
                val = raw.split(b"\\0")[0].decode("utf-8", "replace").strip()\r
            elif typ == 3:\r
                val = [u16(vo + 2 * k) for k in range(cnt)] if size <= len(data) - vo else []\r
            elif typ in (4, 9):\r
                val = [u32(vo + 4 * k) for k in range(cnt)]\r
            elif typ in (5, 10):\r
                val = [(u32(vo + 8 * k), u32(vo + 8 * k + 4)) for k in range(cnt)]\r
            else:\r
                val = raw\r
            out[tag] = (typ, val)\r
        return out\r
    root = ifd(u32(4))\r
    found = {}\r
    def take(tags):\r
        for tag, (typ, val) in tags.items():\r
            name = EXIF_TAGS.get(tag)\r
            if not name:\r
                continue\r
            if tag in (0x9C9D, 0x9C9C, 0x9C9F, 0x9C9B) and isinstance(val, (bytes, list)):   # XP* tags: UCS-2 little-endian\r
                b = bytes(val) if isinstance(val, list) else val\r
                val = b.decode("utf-16-le", "replace").rstrip("\\0").strip()\r
            elif tag == 0x9286 and isinstance(val, bytes):                                   # UserComment: 8-byte charset id\r
                val = val[8:].decode("utf-8", "replace").rstrip("\\0").strip()\r
            if isinstance(val, str) and val:\r
                found.setdefault(name, val)\r
    take(root)\r
    if 0x8769 in root:\r
        take(ifd(root[0x8769][1][0]))\r
    if 0x8825 in root:\r
        g = ifd(root[0x8825][1][0])\r
        def deg(t):\r
            if t not in g or len(g[t][1]) != 3:\r
                return None\r
            return sum((n / d if d else 0) / 60 ** k for k, (n, d) in enumerate(g[t][1]))\r
        lat, lon = deg(2), deg(4)\r
        if lat is not None and lon is not None:\r
            if g.get(1, (2, "N"))[1] == "S":\r
                lat = -lat\r
            if g.get(3, (2, "E"))[1] == "W":\r
                lon = -lon\r
            found["gps"] = f"{lat:.6f}, {lon:.6f}"\r
            if 6 in g and g[6][1]:\r
                n, d = g[6][1][0]\r
                found["gps_altitude_m"] = f"{(n / d if d else 0):.1f}"\r
    return found\r
\r
\r
def _xmp(text):\r
    out = {}\r
    for name, pats in (("creator", [r"<dc:creator>.*?<rdf:li[^>]*>(.*?)</rdf:li>"]), ("creator_tool", [r'xmp:CreatorTool="([^"]*)"', r"<xmp:CreatorTool>(.*?)</xmp:CreatorTool>"]),\r
                       ("producer", [r'pdf:Producer="([^"]*)"', r"<pdf:Producer>(.*?)</pdf:Producer>"]), ("title", [r"<dc:title>.*?<rdf:li[^>]*>(.*?)</rdf:li>"])):\r
        for p in pats:\r
            m = re.search(p, text, re.S)\r
            if m and m.group(1).strip():\r
                out[name] = re.sub(r"\\s+", " ", m.group(1)).strip()[:300]\r
                break\r
    return out\r
\r
\r
def _pdf_string(raw):\r
    """A PDF literal or hex string as text (PDFDocEncoding treated as Latin-1; UTF-16 with a byte-order mark)."""\r
    if raw.startswith(b"<"):\r
        try:\r
            b = bytes.fromhex(re.sub(rb"[^0-9A-Fa-f]", b"", raw[1:-1]).decode())\r
        except ValueError:\r
            return ""\r
    else:\r
        b = re.sub(rb"\\\\([nrtbf()\\\\])", lambda m: {b"n": b"\\n", b"r": b"\\r", b"t": b"\\t", b"b": b"\\b", b"f": b"\\f"}.get(m.group(1), m.group(1)), raw[1:-1])\r
        b = re.sub(rb"\\\\([0-7]{1,3})", lambda m: bytes([int(m.group(1), 8) & 255]), b)\r
    if b[:2] in (b"\\xfe\\xff", b"\\xff\\xfe"):\r
        return b.decode("utf-16", "replace").strip()\r
    return b.decode("latin-1").strip()\r
\r
\r
def _pdf(data):\r
    import zlib\r
    blobs = [data]\r
    for m in re.finditer(rb"stream\\r?\\n", data):            # object streams hold the Info dictionary in newer PDFs\r
        end = data.find(b"endstream", m.end())\r
        if end < 0 or end - m.end() > 5_000_000:\r
            continue\r
        try:\r
            blobs.append(zlib.decompress(data[m.end():end]))\r
        except zlib.error:\r
            pass\r
    out = {}\r
    keys = {b"Author": "author", b"Creator": "creator_tool", b"Producer": "producer", b"Title": "title", b"Subject": "subject", b"Keywords": "keywords",\r
            b"CreationDate": "created", b"ModDate": "modified"}\r
    for b in blobs:\r
        for k, name in keys.items():\r
            if name in out:\r
                continue\r
            m = re.search(rb"/" + k + rb"\\s*(\\((?:\\\\.|[^\\\\)])*\\)|<[0-9A-Fa-f\\s]*>)", b)\r
            if m:\r
                v = _pdf_string(m.group(1))\r
                if v:\r
                    out[name] = v[:300]\r
        if b"<x:xmpmeta" in b or b"<rdf:RDF" in b:\r
            for k, v in _xmp(b.decode("utf-8", "replace")).items():\r
                out.setdefault(k, v)\r
    return out\r
\r
\r
def _office(data):\r
    import io\r
    import zipfile\r
    try:\r
        z = zipfile.ZipFile(io.BytesIO(data))\r
    except zipfile.BadZipFile:\r
        raise ProductError("meta_bad") from None\r
    names = set(z.namelist())\r
    if "[Content_Types].xml" not in names:\r
        raise ProductError("meta_unsupported")\r
    out = {}\r
    def tags(xml, pairs):\r
        for tag, name in pairs:\r
            m = re.search(rf"<{tag}(?:\\s[^>]*)?>(.*?)</{tag}>", xml, re.S)\r
            if m and m.group(1).strip():\r
                out[name] = re.sub(r"\\s+", " ", m.group(1)).strip()[:300]\r
    if "docProps/core.xml" in names:\r
        tags(z.read("docProps/core.xml").decode("utf-8", "replace"), [("dc:creator", "author"), ("cp:lastModifiedBy", "last_modified_by"), ("dc:title", "title"),\r
             ("dc:subject", "subject"), ("cp:keywords", "keywords"), ("dc:description", "description"), ("dcterms:created", "created"), ("dcterms:modified", "modified"), ("cp:revision", "revision")])\r
    if "docProps/app.xml" in names:\r
        tags(z.read("docProps/app.xml").decode("utf-8", "replace"), [("Company", "company"), ("Manager", "manager"), ("Application", "application"), ("Template", "template")])\r
    if any(n.startswith(("word/comments", "xl/comments", "ppt/comments")) for n in names):\r
        out["comments"] = "yes"\r
    if "word/document.xml" in names:\r
        doc = z.read("word/document.xml")\r
        if b"<w:ins " in doc or b"<w:del " in doc:\r
            out["tracked_changes"] = "yes"\r
    kind = "docx" if "word/document.xml" in names else "xlsx" if "xl/workbook.xml" in names else "pptx" if "ppt/presentation.xml" in names else "office"\r
    return kind, out\r
\r
\r
def task_meta(params, data):\r
    if not data:\r
        raise ProductError("empty_file")\r
    if len(data) > 100_000_000:\r
        raise ProductError("meta_too_big", limit_mb=100)\r
    if data[:2] == b"\\xff\\xd8":\r
        kind, fields, p = "jpeg", {}, 2\r
        while p + 4 <= len(data) and data[p] == 0xFF:\r
            marker, size = data[p + 1], int.from_bytes(data[p + 2:p + 4], "big")\r
            seg = data[p + 4:p + 2 + size]\r
            if marker == 0xE1 and seg.startswith(b"Exif\\0\\0"):\r
                fields.update(_tiff(seg[6:]))\r
            elif marker == 0xE1 and b"http://ns.adobe.com/xap/1.0/" in seg[:40]:\r
                for k, v in _xmp(seg.decode("utf-8", "replace")).items():\r
                    fields.setdefault(k, v)\r
            elif marker == 0xFE:\r
                fields.setdefault("comment", seg.decode("utf-8", "replace").strip()[:300])\r
            if marker == 0xDA:\r
                break\r
            p += 2 + size\r
    elif data[:8] == b"\\x89PNG\\r\\n\\x1a\\n":\r
        import zlib\r
        kind, fields, p = "png", {}, 8\r
        names = {"author": "author", "artist": "artist", "title": "title", "description": "description", "comment": "comment", "copyright": "copyright",\r
                 "software": "software", "creation time": "created", "source": "model"}\r
        while p + 8 <= len(data):\r
            n, typ = int.from_bytes(data[p:p + 4], "big"), data[p + 4:p + 8]\r
            body = data[p + 8:p + 8 + n]\r
            if typ in (b"tEXt", b"zTXt", b"iTXt"):\r
                k, _, rest = body.partition(b"\\0")\r
                if typ == b"zTXt":\r
                    try:\r
                        rest = zlib.decompress(rest[1:])\r
                    except zlib.error:\r
                        rest = b""\r
                elif typ == b"iTXt":\r
                    flag, rest = rest[0], rest[2:]\r
                    rest = rest.split(b"\\0", 2)[-1] if rest.count(b"\\0") >= 2 else rest\r
                    if flag:\r
                        try:\r
                            rest = zlib.decompress(rest)\r
                        except zlib.error:\r
                            rest = b""\r
                key = k.decode("latin-1").strip().casefold()\r
                txt = rest.decode("utf-8" if typ == b"iTXt" else "latin-1", "replace").strip()\r
                if key == "xml:com.adobe.xmp":\r
                    for kk, v in _xmp(txt).items():\r
                        fields.setdefault(kk, v)\r
                elif txt:\r
                    fields.setdefault(names.get(key, f"text_{key[:40]}"), txt[:300])\r
            elif typ == b"eXIf":\r
                fields.update(_tiff(body))\r
            if typ == b"IEND":\r
                break\r
            p += 12 + n\r
    elif data[:5] == b"%PDF-":\r
        kind, fields = "pdf", _pdf(data)\r
    elif data[:2] == b"PK":\r
        kind, fields = _office(data)\r
    else:\r
        raise ProductError("meta_unsupported")\r
    items = [{"field": k, "value": v, "category": PRIVACY.get(k.replace("gps_altitude_m", "gps"), "other")} for k, v in sorted(fields.items())]\r
    sensitive = [i for i in items if i["category"] in ("location", "person", "device")]\r
    res = {"kind": kind, "bytes": len(data), "fields": items, "n_fields": len(items), "n_sensitive": len(sensitive),\r
           "has_location": any(i["category"] == "location" for i in items)}\r
    checks = [{"code": "meta_clean", "ok": not sensitive, "args": {"n": len(sensitive)}}]\r
    warnings = [{"code": "meta_location", "args": {}}] if res["has_location"] else []\r
    return _answer(res, [], checks, warnings)\r
\r
\r
TASKS = {"p_cf": task_cf, "p_piva": task_piva, "p_iban": task_iban, "p_workdays": task_workdays,\r
         "p_tablediff": task_tablediff, "p_dups": task_dups, "p_vat": task_vat, "p_meta": task_meta}\r
`),await r.runPythonAsync(`import sys, types
_m = types.ModuleType('ws_products')
exec(_wp_src, _m.__dict__)
sys.modules['ws_products'] = _m
del _m, _wp_src
`),r.globals.set(`_ws_src`,`"""S.T.A.R. Workspace tasks: everyday jobs done by released S.T.A.R. packages, with a verification receipt.\r
\r
Runs unchanged in two places: in the visitor's browser (Pyodide, with the packages' published wheels) and on a PC\r
under pytest (tests/test_ws_tasks.py, with independent references: pyproj, numpy, zlib). Nothing here contacts the\r
network or keeps data: the input arrives as text or bytes, the answer leaves as a dictionary.\r
\r
Every task returns:\r
  ok            True when a result was produced\r
  result        the numbers, in plain units\r
  tools         [{"name", "version"}] - the S.T.A.R. packages (and standard modules) that did the work\r
  transforms    [{"code", "before", "after"}] - every change made to the input before using it\r
  checks        [{"code", "ok", "args"}] - deterministic checks and their outcome\r
  warnings      [{"code", "args"}] - things a person should look at\r
  error         {"code", "args"} when ok is False (never a Python traceback)\r
Messages are codes with arguments; the page turns them into English or Italian.\r
"""\r
from __future__ import annotations\r
\r
import csv\r
import hashlib\r
import io\r
import json\r
import math\r
import re\r
import zlib\r
\r
MAX_ROWS = 50_000\r
MAX_TEXT = 5_000_000            # characters of CSV text\r
MAX_CRC_BYTES = 1_000_000       # star_crc works bit by bit (about 4 s per MB on a laptop): the cross-check stops here\r
R_MEAN_M = 6371008.8            # IUGG mean Earth radius, for the spherical comparison\r
\r
\r
def _version(module, dist):\r
    try:\r
        from importlib.metadata import version\r
        return version(dist)\r
    except Exception:  # noqa: BLE001 - metadata may be missing when the module is imported from a source tree\r
        return getattr(module, "__version__", "?")\r
\r
\r
def _tool(module, dist):\r
    return {"name": dist, "version": _version(module, dist)}\r
\r
\r
class TaskError(Exception):\r
    def __init__(self, code, **args):\r
        super().__init__(code)\r
        self.code, self.args_ = code, args\r
\r
\r
def _answer(result, tools, transforms, checks, warnings):\r
    return {"ok": True, "result": result, "tools": tools, "transforms": transforms, "checks": checks, "warnings": warnings}\r
\r
\r
def run(task: str, params_json: str, data: bytes | None = None) -> str:\r
    """Entry point used by the page: JSON in, JSON out, never an exception."""\r
    try:\r
        params = json.loads(params_json or "{}")\r
        fn = TASKS.get(task)\r
        if fn is None:\r
            raise TaskError("unknown_task", task=task)\r
        out = fn(params, data) if task in ("fingerprint", "p_meta") else fn(params)\r
    except Exception as e:  # noqa: BLE001 - the page must always get an answer it can show\r
        if hasattr(e, "code") and hasattr(e, "args_"):      # TaskError, or ws_products.ProductError\r
            out = {"ok": False, "error": {"code": e.code, "args": e.args_}}\r
        else:\r
            out = {"ok": False, "error": {"code": "internal", "args": {"detail": f"{type(e).__name__}: {e}"[:300]}}}\r
    return json.dumps(out, ensure_ascii=False, allow_nan=False, default=str)\r
\r
\r
# ---------------------------------------------------------------- parsing what people type\r
_NUM = re.compile(r"\\d+(?:[.,]\\d+)?")\r
_SEP_OK = re.compile(r"^[\\s°'\\"′″dms.,:]*$")\r
\r
\r
def parse_number(text, what):\r
    if isinstance(text, (int, float)) and not isinstance(text, bool):\r
        if not math.isfinite(text):\r
            raise TaskError("not_a_number", field=what, value=str(text))\r
        return float(text), None\r
    s = "" if text is None else str(text).strip()          # 0 is a value, not an empty field\r
    if not s:\r
        raise TaskError("empty", field=what)\r
    t = s.replace("−", "-")                          # spaces inside are NOT removed: "1 2 3" must not become 123\r
    if re.fullmatch(r"[+-]?\\d+,\\d+", t):          # decimal comma, as written in Italy\r
        v = float(t.replace(",", "."))\r
        return v, {"code": "decimal_comma", "before": s, "after": repr(v)}\r
    try:\r
        v = float(t)\r
    except ValueError:\r
        raise TaskError("not_a_number", field=what, value=s[:40]) from None\r
    if not math.isfinite(v):\r
        raise TaskError("not_a_number", field=what, value=s[:40])\r
    return v, None\r
\r
\r
def parse_angle(text, kind):\r
    """Decimal degrees ('41.9', '41,9', '-12.5') or degrees, minutes, seconds ('41 54 10 N', '41N', '12d29m46sO')."""\r
    if isinstance(text, (int, float)) and not isinstance(text, bool):\r
        return parse_number(text, kind)\r
    s = "" if text is None else str(text).strip()          # 0 is a value, not an empty field\r
    if not s:\r
        raise TaskError("empty", field=kind)\r
    try:\r
        return parse_number(s, kind)\r
    except TaskError:\r
        pass\r
    body = s.replace("−", "-")\r
    sign = None\r
    if body[:1] in "+-":\r
        sign, body = body[0], body[1:]\r
    hemi = None\r
    last, prev = body[-1:], body[-2:-1]\r
    # a final N/S/E/W/O is a hemisphere; after a lowercase unit (10sS) the capital letter is the hemisphere\r
    if last.upper() in ("N", "S", "E", "W", "O") and (not prev.isalpha() or (last.isupper() and prev in "dms")):\r
        hemi, body = body[-1].upper(), body[:-1]\r
    nums = _NUM.findall(body)\r
    if not 1 <= len(nums) <= 3 or not _SEP_OK.match(_NUM.sub("", body)):\r
        raise TaskError("bad_angle", field=kind, value=s[:40])\r
    parts = [float(x.replace(",", ".")) for x in nums] + [0.0, 0.0]\r
    deg, mins, secs = parts[0], parts[1], parts[2]\r
    if mins >= 60 or secs >= 60 or (len(nums) > 1 and deg != int(deg)):\r
        raise TaskError("bad_angle", field=kind, value=s[:40])\r
    v = deg + mins / 60 + secs / 3600\r
    neg = sign == "-"\r
    if hemi:\r
        if kind.startswith("lat") and hemi not in "NS" or kind.startswith("lon") and hemi not in "EWO":\r
            raise TaskError("wrong_hemisphere", field=kind, value=s[:40])\r
        neg = neg != (hemi in "SWO")                        # O = Ovest, west in Italian\r
    v = -v if neg else v\r
    return v, {"code": "dms_to_decimal", "before": s, "after": f"{v:.8f}"}\r
\r
\r
def _latlon(params, a, b):\r
    lat, t1 = parse_angle(params.get(a), "lat")\r
    lon, t2 = parse_angle(params.get(b), "lon")\r
    if not -90 <= lat <= 90:\r
        raise TaskError("lat_range", value=lat)\r
    if not -180 <= lon <= 180:\r
        raise TaskError("lon_range", value=lon)\r
    return lat, lon, [t for t in (t1, t2) if t]\r
\r
\r
# ---------------------------------------------------------------- 1. distance between two places\r
def task_distance(params):\r
    import star_geodesic as geo\r
    import star_sphere as sph\r
    lat1, lon1, tr1 = _latlon(params, "lat1", "lon1")\r
    lat2, lon2, tr2 = _latlon(params, "lat2", "lon2")\r
    checks = [{"code": "coords_in_range", "ok": True, "args": {}}]\r
    warnings = []\r
    try:\r
        s12, az1, az2 = geo.inverse(lat1, lon1, lat2, lon2)\r
    except RuntimeError:\r
        raise TaskError("antipodal") from None\r
    sep = sph.separation_deg(lon1, lat1, lon2, lat2)\r
    s_sph = math.radians(sep) * R_MEAN_M\r
    if s12 == 0:\r
        warnings.append({"code": "same_point", "args": {}})\r
        checks.append({"code": "round_trip", "ok": True, "args": {"mm": 0.0}})\r
    elif s12 > 20_000_000:\r
        # star_geodesic.direct() documents a 20,000 km limit; the longest geodesic is about 20,004 km\r
        warnings.append({"code": "round_trip_skipped", "args": {"km": s12 / 1000}})\r
    else:\r
        # forward-backward check: walk the computed distance along the computed azimuth and see where we land\r
        lat_b, lon_b, _ = geo.direct(lat1, lon1, az1, s12)\r
        back = geo.inverse(lat2, lon2, lat_b, lon_b)[0]\r
        checks.append({"code": "round_trip", "ok": back < 1e-3, "args": {"mm": back * 1000}})\r
    diff = (s_sph - s12) / s12 * 100 if s12 else 0.0\r
    # the path itself, for the map: points along the geodesic (direct problem), within the package's 20,000 km limit\r
    path = [[lat1, lon1]]\r
    if 0 < s12 <= 20_000_000:\r
        for k in range(1, 64):\r
            la, lo, _ = geo.direct(lat1, lon1, az1, s12 * k / 64)\r
            path.append([la, lo])\r
    path.append([lat2, lon2])\r
    return _answer(\r
        {"distance_m": s12, "distance_km": s12 / 1000, "azimuth_start_deg": az1, "azimuth_end_deg": az2,\r
         "spherical_km": s_sph / 1000, "spherical_diff_percent": diff, "separation_deg": sep,\r
         "points": [[lat1, lon1], [lat2, lon2]], "path": path},\r
        [_tool(geo, "star-geodesic"), _tool(sph, "star-sphere")], tr1 + tr2, checks, warnings)\r
\r
\r
# ---------------------------------------------------------------- 2. coordinate formats\r
def _dms_text(fields, pos, neg):\r
    sign, d, m, s, frac = fields\r
    return f"{d}°{m:02d}'{s:02d}.{frac:03d}\\" {neg if sign == '-' else pos}"\r
\r
\r
def task_coords(params):\r
    import star_geodesic as geo\r
    import star_sexagesimal as sx\r
    import star_utm as utm\r
    lat, lon, tr = _latlon(params, "lat", "lon")\r
    checks, warnings = [{"code": "coords_in_range", "ok": True, "args": {}}], []\r
    res = {"lat": lat, "lon": lon, "lat_dms": _dms_text(sx.deg_to_dms(lat, 3), "N", "S"), "lon_dms": _dms_text(sx.deg_to_dms(lon, 3), "E", "W")}\r
    back = sx.dms_to_deg(*sx.deg_to_dms(lat, 6)[:3], sx.deg_to_dms(lat, 6)[3] + sx.deg_to_dms(lat, 6)[4] / 1e6)\r
    checks.append({"code": "dms_round_trip", "ok": abs(back - lat) < 1e-9, "args": {"deg": abs(back - lat)}})\r
    tools = [_tool(sx, "star-sexagesimal")]\r
    if -80 <= lat <= 84:\r
        zone, hemi, e, n = utm.utm_forward(lat, lon)\r
        lat_b, lon_b = utm.utm_inverse(zone, hemi, e, n)\r
        err = geo.inverse(lat, lon, lat_b, lon_b)[0]\r
        res.update({"utm_zone": zone, "utm_hemisphere": hemi, "utm_easting": e, "utm_northing": n})\r
        checks.append({"code": "utm_round_trip", "ok": err < 1e-3, "args": {"mm": err * 1000}})\r
        tools += [_tool(utm, "star-utm"), _tool(geo, "star-geodesic")]\r
        if 56 <= lat < 64 and 3 <= lon < 12 or 72 <= lat <= 84 and 0 <= lon < 42:\r
            warnings.append({"code": "utm_special_zone", "args": {"zone": zone}})\r
    else:\r
        warnings.append({"code": "utm_polar", "args": {}})\r
    return _answer(res, tools, tr, checks, warnings)\r
\r
\r
# ---------------------------------------------------------------- CSV reading shared by tasks 3 and 4\r
def _read_table(text):\r
    if not isinstance(text, str) or not text.strip():\r
        raise TaskError("empty_file")\r
    if len(text) > MAX_TEXT:\r
        raise TaskError("file_too_big", limit_mb=MAX_TEXT // 1_000_000)\r
    transforms = []\r
    if text.startswith("﻿"):\r
        text = text[1:]\r
        transforms.append({"code": "bom_removed", "before": "BOM", "after": ""})\r
    sample = text[:20000]\r
    # a binary file read as text is full of control characters: say so instead of inventing columns\r
    controls = sum(1 for ch in sample if (ord(ch) < 32 and ch not in "\\t\\r\\n") or ch == "\\ufffd")\r
    if controls > max(5, len(sample) // 100):\r
        raise TaskError("not_text")\r
    counts = {d: sample.count(d) for d in (";", "\\t", ",", "|")}          # "|" added 2026-10-19 (mandate input matrix)\r
    delim = max(counts, key=counts.get) if any(counts.values()) else ","\r
    try:\r
        # newline="" as the csv module requires, so a lone carriage return inside a cell is not an error\r
        rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=delim))\r
    except csv.Error as e:\r
        raise TaskError("bad_csv", detail=str(e)[:120]) from None\r
    rows = [r for r in rows if any(c.strip() for c in r)]\r
    if not rows:\r
        raise TaskError("empty_file")\r
    if len(rows) > MAX_ROWS:\r
        raise TaskError("too_many_rows", limit=MAX_ROWS)\r
    decimal_comma = delim != "," and any(re.fullmatch(r"\\s*[+-]?\\d+,\\d+\\s*", c) for r in rows[:200] for c in r)\r
\r
    def num(cell):\r
        c = cell.strip().replace("−", "-")\r
        if not c:\r
            return None, "missing"\r
        if decimal_comma:\r
            c2 = c.replace(".", "").replace(",", ".") if re.fullmatch(r"[+-]?\\d{1,3}(\\.\\d{3})+(,\\d+)?|[+-]?\\d+,\\d+|[+-]?\\d+", c) else c\r
        else:\r
            c2 = c.replace(",", "") if re.fullmatch(r"[+-]?\\d{1,3}(,\\d{3})+(\\.\\d+)?", c) else c\r
        try:\r
            v = float(c2)\r
        except ValueError:\r
            return None, "non_numeric"\r
        if not math.isfinite(v):\r
            return None, "non_numeric"\r
        return v, ("converted" if c2 != c else "ok")\r
    first_numeric = sum(num(c)[0] is not None for c in rows[0])\r
    header = first_numeric < max(1, len(rows[0]) // 2) and len(rows) > 1\r
    names = [c.strip() or f"col{k + 1}" for k, c in enumerate(rows[0])] if header else [f"col{k + 1}" for k in range(len(rows[0]))]\r
    body = rows[1:] if header else rows\r
    width = len(names)\r
    ragged = [k + (2 if header else 1) for k, r in enumerate(body) if len(r) != width]\r
    return {"delimiter": delim, "decimal_comma": decimal_comma, "header": header, "names": names, "body": body,\r
            "ragged": ragged, "num": num, "transforms": transforms}\r
\r
\r
def _column(tab, wanted):\r
    names = tab["names"]\r
    if wanted in (None, ""):\r
        best, best_n = None, -1\r
        for k in range(len(names)):\r
            n = sum(tab["num"](r[k])[0] is not None for r in tab["body"][:500] if k < len(r))\r
            if n > best_n:\r
                best, best_n = k, n\r
        return best\r
    if isinstance(wanted, int) or str(wanted).isdigit():\r
        k = int(wanted)\r
        if not 0 <= k < len(names):\r
            raise TaskError("no_column", name=str(wanted))\r
        return k\r
    if wanted in names:\r
        return names.index(wanted)\r
    raise TaskError("no_column", name=str(wanted)[:40])\r
\r
\r
# ---------------------------------------------------------------- 3. check and summarise a column of numbers\r
def task_column(params):\r
    import star_quantile as qn\r
    import star_stats as st\r
    tab = _read_table(params.get("text"))\r
    k = _column(tab, params.get("column"))\r
    name = tab["names"][k]\r
    values, statuses, transforms, bad = [], [], list(tab["transforms"]), []\r
    first_row = 2 if tab["header"] else 1\r
    for i, r in enumerate(tab["body"]):\r
        cell = r[k] if k < len(r) else ""\r
        v, status = tab["num"](cell)\r
        statuses.append(status)\r
        if v is None:\r
            bad.append({"row": first_row + i, "value": cell[:40], "why": status})\r
        else:\r
            values.append((first_row + i, v))\r
            if status == "converted" and sum(t["code"] == "number_format" for t in transforms) < 10:\r
                transforms.append({"code": "number_format", "before": cell.strip(), "after": repr(v)})\r
    n_conv = sum(s == "converted" for s in statuses)\r
    checks = [\r
        {"code": "columns_consistent", "ok": not tab["ragged"], "args": {"rows": tab["ragged"][:10], "count": len(tab["ragged"])}},\r
        {"code": "numeric_share", "ok": len(values) >= 0.9 * len(statuses), "args": {"numeric": len(values), "total": len(statuses)}},\r
    ]\r
    if len(values) < 2:\r
        raise TaskError("too_few_values", n=len(values), column=name[:40])\r
    xs = [v for _, v in values]\r
    med, mad = qn.median(xs), qn.mad(xs)\r
    # modified z-score (Iglewicz and Hoaglin): |x - median| / (1.4826 MAD) above 3.5 is flagged for a person to look at\r
    scale = 1.4826 * mad\r
    outliers = [{"row": r, "value": v, "score": abs(v - med) / scale} for r, v in values if scale > 0 and abs(v - med) / scale > 3.5]\r
    checks.append({"code": "outliers", "ok": not outliers, "args": {"count": len(outliers)}})\r
    res = {"column": name, "columns": tab["names"], "delimiter": tab["delimiter"], "decimal_comma": tab["decimal_comma"], "header": tab["header"],\r
           "n": len(xs), "missing": sum(s == "missing" for s in statuses), "non_numeric": sum(s == "non_numeric" for s in statuses),\r
           "converted": n_conv, "mean": st.mean(xs), "stdev": st.stdev(xs), "min": min(xs), "max": max(xs), "median": med,\r
           "q1": qn.quantile(xs, 0.25), "q3": qn.quantile(xs, 0.75), "iqr": qn.iqr(xs), "mad": mad,\r
           "bad_rows": bad[:20], "bad_total": len(bad), "outliers": sorted(outliers, key=lambda o: -o["score"])[:20], "outliers_total": len(outliers)}\r
    # a cleaned copy: the original columns plus the number read and its status, row by row\r
    out = io.StringIO()\r
    w = csv.writer(out, lineterminator="\\n")\r
    w.writerow(tab["names"] + [f"{name}_value", f"{name}_status"])\r
    flagged = {o["row"] for o in outliers}\r
    for i, r in enumerate(tab["body"]):\r
        v, status = tab["num"](r[k] if k < len(r) else "")\r
        status = "outlier" if first_row + i in flagged else status\r
        w.writerow(list(r) + (["" for _ in range(len(tab["names"]) - len(r))] if len(r) < len(tab["names"]) else []) + ["" if v is None else repr(v), status])\r
    res["cleaned_csv"] = out.getvalue()\r
    warnings = [{"code": "converted_numbers", "args": {"count": n_conv}}] if n_conv else []\r
    return _answer(res, [_tool(st, "star-stats"), _tool(qn, "star-quantile")], transforms, checks, warnings)\r
\r
\r
# ---------------------------------------------------------------- 4. straight-line fit\r
def task_linefit(params):\r
    import star_linefit as lf\r
    tab = _read_table(params.get("text"))\r
    if len(tab["names"]) < 2:\r
        raise TaskError("need_two_columns")\r
    kx = _column(tab, params.get("x") if params.get("x") not in (None, "") else 0)\r
    ky = _column(tab, params.get("y") if params.get("y") not in (None, "") else (1 if kx != 1 else 0))\r
    if kx == ky:\r
        raise TaskError("same_column")\r
    pts, skipped = [], []\r
    first_row = 2 if tab["header"] else 1\r
    for i, r in enumerate(tab["body"]):\r
        x, sx_ = tab["num"](r[kx] if kx < len(r) else "")\r
        y, sy_ = tab["num"](r[ky] if ky < len(r) else "")\r
        (pts.append((x, y)) if x is not None and y is not None else skipped.append(first_row + i))\r
    if len(pts) < 3:\r
        raise TaskError("too_few_points", n=len(pts))\r
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]\r
    if max(xs) == min(xs):\r
        raise TaskError("x_constant")\r
    slope, intercept = lf.fit(xs, ys)\r
    s_slope, s_icpt, s_res = lf.fit_errors(xs, ys)\r
    try:\r
        r = lf.correlation(xs, ys)\r
    except ValueError:\r
        r = float("nan")\r
    resid = [y - (slope * x + intercept) for x, y in pts]\r
    worst = max(range(len(pts)), key=lambda i: abs(resid[i]))\r
    checks = [{"code": "enough_points", "ok": len(pts) >= 5, "args": {"n": len(pts)}},\r
              {"code": "rows_skipped", "ok": not skipped, "args": {"count": len(skipped), "rows": skipped[:10]}}]\r
    if s_res > 0 and abs(resid[worst]) > 3 * s_res:\r
        checks.append({"code": "large_residual", "ok": False, "args": {"x": xs[worst], "y": ys[worst], "times": abs(resid[worst]) / s_res}})\r
    res = {"x_name": tab["names"][kx], "y_name": tab["names"][ky], "n": len(pts), "slope": slope, "intercept": intercept,\r
           "slope_err": s_slope, "intercept_err": s_icpt, "residual_sd": s_res, "r": None if math.isnan(r) else r,\r
           "r2": None if math.isnan(r) else r * r, "points": pts[:2000], "columns": tab["names"]}\r
    return _answer(res, [_tool(lf, "star-linefit")], list(tab["transforms"]), checks, [])\r
\r
\r
# ---------------------------------------------------------------- 5. file fingerprint\r
def _reflect32(v):\r
    out = 0\r
    for _ in range(32):\r
        out = (out << 1) | (v & 1)\r
        v >>= 1\r
    return out\r
\r
\r
def crc32_star(sc, data):\r
    """CRC-32/ISO-HDLC with star_crc, which accepts at most 64 KiB per call: blocks are chained by passing the\r
    register on (reflected back, because the algorithm is reflected). Equal to zlib.crc32 at every length (tested)."""\r
    if len(data) <= sc.MAX_BYTES:\r
        return sc.crc32(data)\r
    state = 0xFFFFFFFF\r
    for i in range(0, len(data), sc.MAX_BYTES):\r
        state = _reflect32(sc.crc(data[i:i + sc.MAX_BYTES], 32, 0x04C11DB7, state, True, True, 0))\r
    return _reflect32(state) ^ 0xFFFFFFFF\r
def task_fingerprint(params, data):\r
    import star_crc as sc\r
    if data is None or len(data) == 0:\r
        raise TaskError("empty_file")\r
    sha256 = hashlib.sha256(data).hexdigest()\r
    res = {"bytes": len(data), "sha256": sha256, "sha1": hashlib.sha1(data).hexdigest(), "md5": hashlib.md5(data).hexdigest()}\r
    checks, warnings, tools = [], [], [{"name": "hashlib, zlib (Python standard library)", "version": "-"}]\r
    c2 = zlib.crc32(data) & 0xFFFFFFFF\r
    res["crc32"] = f"{c2:08x}"\r
    if len(data) <= MAX_CRC_BYTES:\r
        c1 = crc32_star(sc, data)\r
        checks.append({"code": "crc_two_implementations", "ok": c1 == c2, "args": {"star": f"{c1:08x}", "zlib": f"{c2:08x}"}})\r
        tools.insert(0, _tool(sc, "star-crc"))\r
    else:\r
        warnings.append({"code": "crc_skipped", "args": {"limit_mb": MAX_CRC_BYTES // 1_000_000}})\r
    expected = re.sub(r"[\\s:-]", "", str(params.get("expected") or "")).lower()\r
    if expected:\r
        kind = {8: "crc32", 32: "md5", 40: "sha1", 64: "sha256"}.get(len(expected))\r
        if not kind or not re.fullmatch(r"[0-9a-f]+", expected):\r
            raise TaskError("bad_expected", length=len(expected))\r
        res["compared"] = kind\r
        res["match"] = res[kind] == expected\r
        checks.append({"code": "matches_expected", "ok": res["match"], "args": {"kind": kind}})\r
    return _answer(res, tools, [], checks, warnings)\r
\r
\r
# ---------------------------------------------------------------- 6. unit conversion\r
def task_units(params):\r
    import star_units as su\r
    v, tr = parse_number(params.get("value"), "value")\r
    a, b = str(params.get("from") or ""), str(params.get("to") or "")\r
    known = su.units()\r
    if a not in known or b not in known:\r
        raise TaskError("unknown_unit", unit=a if a not in known else b)\r
    da, db = su.dimension(a), su.dimension(b)\r
    if da != db:\r
        raise TaskError("different_dimensions", a=a, da=da, b=b, db=db)\r
    try:\r
        if da == "temperature":\r
            out = su.convert_temperature(v, a, b)\r
            back = su.convert_temperature(out, b, a)\r
        else:\r
            out = su.convert(v, a, b)\r
            back = su.convert(out, b, a)\r
    except ValueError as e:\r
        raise TaskError("unit_refused", detail=str(e)[:120]) from None\r
    rel = abs(back - v) / abs(v) if v else abs(back)\r
    checks = [{"code": "same_dimension", "ok": True, "args": {"dimension": da}},\r
              {"code": "unit_round_trip", "ok": rel < 1e-12, "args": {"rel": rel}}]\r
    res = {"value": v, "from": a, "to": b, "result": out, "dimension": da,\r
           "factor": None if da == "temperature" or v == 0 else out / v}\r
    return _answer(res, [_tool(su, "star-units")], [tr] if tr else [], checks, [])\r
\r
\r
def units_catalogue():\r
    import star_units as su\r
    out = {}\r
    for u in su.units():\r
        out.setdefault(su.dimension(u), []).append(u)\r
    return json.dumps(out)\r
\r
\r
TASKS = {"distance": task_distance, "coords": task_coords, "column": task_column, "linefit": task_linefit,\r
         "fingerprint": task_fingerprint, "units": task_units}\r
\r
# the everyday products (first batch 2026-10-20) live in ws_products.py; the page loads that module before this one.\r
# Imported without a fallback on purpose: a missing products module must fail loudly, not hide the products.\r
import ws_products  # noqa: E402\r
\r
TASKS.update(ws_products.TASKS)\r
\r
\r
# ---------------------------------------------------------------- what can be checked in this file? (MO-W05, 2026-10-20)\r
# Looks at a file or pasted text HERE, in the browser, and says what each column holds - numbers, dates, Italian tax\r
# codes, VAT numbers, IBANs, coordinates - with how many values are valid, and which Workspace tools fit. A column is\r
# called by the kind that at least 60% of its non-empty values have; tax codes, VAT numbers and IBANs are counted\r
# valid only when their check character or digits are right (the same engines as the released products).\r
DETECT_SAMPLE = 5000            # values looked at per column (declared in the result)\r
DETECT_SHARE = 0.6\r
_LAT = re.compile(r"(?i)^(lat|latitude|latitudine|lat\\.)$")\r
_LON = re.compile(r"(?i)^(lon|lng|long|longitude|longitudine|lon\\.)$")\r
_TLE1 = re.compile(r"^1 [0-9 ]{5}[A-Z ] ")\r
_TLE2 = re.compile(r"^2 [0-9 ]{5} ")\r
\r
\r
def _kind_of(cell, num):\r
    """The kinds one cell can be, and whether it is valid as that kind."""\r
    c = cell.strip()\r
    out = {}\r
    if not c:\r
        return out\r
    u = re.sub(r"[\\s\\-.]", "", c).upper()\r
    if len(u) == 16 and ws_products.CF_RE.fullmatch(u):\r
        base = "".join(ws_products.OMO.get(ch, ch) if i in ws_products.OMO_POS else ch for i, ch in enumerate(u))\r
        out["cf"] = ws_products.cf_check_char(u[:15]) == u[15] and base[9:11].isdigit()\r
    p = u[2:] if u.startswith("IT") and len(u) == 13 else u\r
    if len(p) == 11 and p.isdigit():\r
        out["piva"] = ws_products.piva_check_digit_italian(p[:10]) == int(p[10])\r
    if 15 <= len(u) <= 34 and u[:2].isalpha() and u[2:4].isdigit() and u.isalnum():\r
        out["iban"] = ws_products.IBAN_LEN.get(u[:2]) == len(u) and ws_products.iban_mod97(u) == 1\r
    try:\r
        ws_products._parse_date(c, "x")\r
        out["date"] = True\r
    except ws_products.ProductError:\r
        pass\r
    v, _st = num(c)\r
    if v is not None:\r
        out["number"] = True\r
    return out\r
\r
\r
def task_detect(params):\r
    text = params.get("text")\r
    if not isinstance(text, str) or not text.strip():\r
        raise TaskError("empty_file")\r
    lines = [ln for ln in text.splitlines() if ln.strip()]\r
    tle = sum(1 for k in range(len(lines) - 1) if _TLE1.match(lines[k]) and _TLE2.match(lines[k + 1]))\r
    if tle:\r
        res = {"kind": "tle", "rows": len(lines), "tle_sets": tle, "columns": [], "suggestions": [{"task": "fingerprint", "reason": "fp_any"}],\r
               "planned": [{"code": "tle_check"}], "sampled": False}\r
        return _answer(res, [{"name": "ws_tasks.detect (S.T.A.R. Workspace)", "version": "0.1.0"}], [],\r
                       [{"code": "detect_tle", "ok": True, "args": {"n": tle}}], [])\r
    tab = _read_table(text)\r
    names, body, num = tab["names"], tab["body"], tab["num"]\r
    cols, sampled = [], False\r
    for j, name in enumerate(names):\r
        values = [(k, r[j]) for k, r in enumerate(body) if j < len(r) and r[j].strip()]\r
        if len(values) > DETECT_SAMPLE:\r
            values, sampled = values[:DETECT_SAMPLE], True\r
        n = len(values)\r
        counts, valid, first_bad = {}, {}, {}\r
        for k, cell in values:\r
            for kind, ok in _kind_of(cell, num).items():\r
                counts[kind] = counts.get(kind, 0) + 1\r
                valid[kind] = valid.get(kind, 0) + (1 if ok else 0)\r
                if not ok and kind not in first_bad:\r
                    first_bad[kind] = {"row": k + (2 if tab["header"] else 1), "value": cell.strip()[:40]}\r
        kind = "text" if n else "empty"\r
        for k in ("cf", "iban", "piva", "date", "number"):          # the most specific kind that most values have\r
            if n and counts.get(k, 0) >= DETECT_SHARE * n:\r
                kind = k\r
                break\r
        if kind == "number" and tab["header"] and (_LAT.match(name.strip()) or _LON.match(name.strip())):\r
            kind = "lat" if _LAT.match(name.strip()) else "lon"\r
        col = {"name": name, "kind": kind, "n": n}\r
        if kind in ("cf", "piva", "iban"):\r
            col.update({"valid": valid.get(kind, 0), "invalid": counts.get(kind, 0) - valid.get(kind, 0),\r
                        "other": n - counts.get(kind, 0), "first_invalid": first_bad.get(kind),\r
                        "first_value": values[0][1].strip()[:40] if values else ""})\r
        if kind == "date":\r
            ds = sorted(ws_products._parse_date(c, "x") for _k, c in values if "date" in _kind_of(c, num))\r
            col.update({"first": ds[0].isoformat(), "last": ds[-1].isoformat()})\r
        cols.append(col)\r
    sug = []\r
    for kind, task in (("cf", "p_cf"), ("piva", "p_piva"), ("iban", "p_iban")):\r
        for c in cols:\r
            if c["kind"] == kind:\r
                example = (c["first_invalid"] or {}).get("value") or c["first_value"]\r
                sug.append({"task": task, "column": c["name"], "reason": f"{kind}_col",\r
                            "args": {"n": c["n"], "valid": c["valid"], "invalid": c["invalid"]}, "preset": {"code": example}})\r
    for c in cols:\r
        if c["kind"] == "date":\r
            sug.append({"task": "p_workdays", "column": c["name"], "reason": "date_col", "args": {"first": c["first"], "last": c["last"]},\r
                        "preset": {"mode": "between", "start": c["first"], "end": c["last"]}})\r
            break\r
    lat = next((c for c in cols if c["kind"] == "lat"), None)\r
    lon = next((c for c in cols if c["kind"] == "lon"), None)\r
    if lat and lon:\r
        j1, j2 = names.index(lat["name"]), names.index(lon["name"])\r
        pts = [(r[j1].strip(), r[j2].strip()) for r in body if max(j1, j2) < len(r) and r[j1].strip() and r[j2].strip()][:2]\r
        sug.append({"task": "coords", "column": f"{lat['name']}, {lon['name']}", "reason": "latlon_cols", "args": {"n": lat["n"]},\r
                    "preset": {"lat": pts[0][0], "lon": pts[0][1]}})\r
        if len(pts) == 2:\r
            sug.append({"task": "distance", "column": f"{lat['name']}, {lon['name']}", "reason": "latlon_two", "args": {},\r
                        "preset": {"lat1": pts[0][0], "lon1": pts[0][1], "lat2": pts[1][0], "lon2": pts[1][1]}})\r
    def row_counter(name):                     # 1, 2, 3... (or any step-1 integer run): a row number, not a measurement\r
        j = names.index(name)\r
        vals = [num(r[j])[0] for r in body if j < len(r) and r[j].strip()][:DETECT_SAMPLE]\r
        return len(vals) > 2 and all(v is not None and v == int(v) for v in vals) and all(b - a == 1 for a, b in zip(vals, vals[1:]))\r
    # measurements only: coordinates and row counters are not offered to the column and line tools\r
    numeric = [c for c in cols if c["kind"] == "number" and not row_counter(c["name"])]\r
    for c in numeric[:1]:\r
        sug.append({"task": "column", "column": c["name"], "reason": "num_col", "args": {"n": c["n"]}, "preset": {"text": "__file__", "column": c["name"]}})\r
    if len(numeric) >= 2:\r
        sug.append({"task": "linefit", "column": f"{numeric[0]['name']}, {numeric[1]['name']}", "reason": "two_num", "args": {},\r
                    "preset": {"text": "__file__", "x": numeric[0]["name"], "y": numeric[1]["name"]}})\r
    sug.append({"task": "fingerprint", "reason": "fp_any", "args": {}})\r
    planned = [{"code": "register_batch"}] if any(c["kind"] in ("cf", "piva", "iban") for c in cols) else []\r
    res = {"kind": "table", "rows": len(body), "header": tab["header"], "delimiter": tab["delimiter"], "decimal_comma": tab["decimal_comma"],\r
           "columns": cols, "suggestions": sug, "planned": planned, "sampled": sampled, "sample_limit": DETECT_SAMPLE}\r
    checks = [{"code": "detect_read", "ok": True, "args": {"rows": len(body), "cols": len(cols)}}]\r
    warnings = [{"code": "detect_sampled", "args": {"limit": DETECT_SAMPLE}}] if sampled else []\r
    return _answer(res, [{"name": "ws_tasks.detect (S.T.A.R. Workspace)", "version": "0.1.0"}], list(tab["transforms"]), checks, warnings)\r
\r
\r
TASKS["detect"] = task_detect\r
`),await r.runPythonAsync(`import sys, types
_m = types.ModuleType('ws_tasks')
exec(_ws_src, _m.__dict__)
sys.modules['ws_tasks'] = _m
del _m, _ws_src
`),r.globals.set(`_wf_src`,`"""S.T.A.R. Workspace workflow (MO-W06, 2026-10-20): several checks on the SAME table in one pass, a before/after list\r
of every value read differently, a cleaned table and one receipt (its specification was written before this code).\r
The "codes" step is the engine of product GP-027 (register cleaning). This file is sent to the browser as it is.\r
\r
Steps, each at most once, at most 4:\r
  numbers      measurement and amount columns: the number read and its status, with the column tool's reader\r
  codes        Italian tax codes, VAT numbers and IBANs: the released product engines (ws_products), row by row\r
  dates        dates in the four formats of the products: the ISO date and its status\r
  fingerprint  SHA-256 of the text given and of the cleaned table\r
A step is a name (its columns are the ones the detection gives that kind) or {"step", "columns"}.\r
\r
Nothing is corrected. A value is read, normalised (spaces removed, upper case, ISO date) and marked; a wrong check\r
character is reported, never replaced. The original columns are written back unchanged and the answer proves it by\r
reading the cleaned table again.\r
"""\r
from __future__ import annotations\r
\r
import csv\r
import hashlib\r
import io\r
\r
import ws_products as wp\r
import ws_tasks as wt\r
\r
VERSION = "0.1.0"\r
TOOL = {"name": "S.T.A.R. Workspace workflow (ws_workflow)", "version": VERSION}\r
STEPS = ("numbers", "codes", "dates", "fingerprint")\r
MAX_STEPS = 4\r
MAX_COLS = 20                    # columns per step\r
DIFF_SHOWN = 200                 # before/after lines returned; the total is always given\r
CODE_TASK = {"cf": wp.task_cf, "piva": wp.task_piva, "iban": wp.task_iban}\r
CODE_FIELD = {"cf": "code", "piva": "code", "iban": "iban"}\r
\r
\r
def _plan(params, tab, text):\r
    """The steps asked, each with its columns: given, or taken from the detection of the same text."""\r
    steps = params.get("steps")\r
    if not isinstance(steps, list) or not steps:\r
        raise wt.TaskError("wf_no_steps")\r
    if len(steps) > MAX_STEPS:\r
        raise wt.TaskError("wf_too_many_steps", limit=MAX_STEPS)\r
    asked, seen = [], set()\r
    for s in steps:                                       # the shape of the plan first, then its columns\r
        name, cols = (s, None) if isinstance(s, str) else (s.get("step") if isinstance(s, dict) else None, s.get("columns") if isinstance(s, dict) else None)\r
        if name not in STEPS:\r
            raise wt.TaskError("wf_unknown_step", step=str(name)[:30])\r
        if name in seen:\r
            raise wt.TaskError("wf_step_twice", step=name)\r
        seen.add(name)\r
        asked.append((name, cols))\r
    detected = None\r
    plan, skipped = [], []\r
    for name, cols in asked:\r
        if name != "fingerprint" and cols is None:\r
            if detected is None:\r
                detected = wt.task_detect({"text": text})["result"]["columns"]\r
            cols = _auto_columns(name, detected, tab)\r
            if not cols:                                  # ticked by default, nothing of its kind here: skipped, and said\r
                skipped.append(name)\r
                continue\r
        if name == "codes":\r
            if not isinstance(cols, dict):\r
                raise wt.TaskError("wf_bad_columns", step=name)\r
            bad = [k for k in cols.values() if k not in CODE_TASK]\r
            if bad:\r
                raise wt.TaskError("wf_code_kind", kind=str(bad[0])[:20])\r
        elif name != "fingerprint":\r
            if not isinstance(cols, list) or not all(isinstance(c, (str, int)) for c in cols):\r
                raise wt.TaskError("wf_bad_columns", step=name)\r
        if name != "fingerprint":\r
            if not cols:\r
                raise wt.TaskError("wf_no_columns", step=name)\r
            if len(cols) > MAX_COLS:\r
                raise wt.TaskError("wf_too_many_columns", step=name, limit=MAX_COLS)\r
            for c in cols:\r
                wt._column(tab, c)                        # an unknown column is an error with its name, not a crash\r
        plan.append((name, cols))\r
    if not any(name != "fingerprint" for name, _c in plan) and skipped:\r
        raise wt.TaskError("wf_no_columns", step=skipped[0])       # nothing left to check but a fingerprint\r
    return plan, skipped\r
\r
\r
def _row_counter(tab, j):\r
    """1, 2, 3...: a row number, not a measurement (the rule of the detection's suggestions)."""\r
    vals = [tab["num"](r[j])[0] for r in tab["body"] if j < len(r) and r[j].strip()][:wt.DETECT_SAMPLE]\r
    return len(vals) > 2 and all(v is not None and v == int(v) for v in vals) and all(b - a == 1 for a, b in zip(vals, vals[1:]))\r
\r
\r
def _auto_columns(step, detected, tab):\r
    if step == "codes":\r
        return {c["name"]: c["kind"] for c in detected if c["kind"] in CODE_TASK}\r
    if step == "dates":\r
        return [c["name"] for c in detected if c["kind"] == "date"]\r
    return [c["name"] for c in detected if c["kind"] == "number" and not _row_counter(tab, tab["names"].index(c["name"]))]\r
\r
\r
def _code(kind, cell):\r
    """One value through the released engine: (normalised, valid, reason). The reason is the code of the first check\r
    that failed, or of the error that stopped the engine (wrong length, letters in a VAT number...)."""\r
    try:\r
        out = CODE_TASK[kind]({"code": cell})\r
    except wp.ProductError as e:\r
        return "", "no", e.code\r
    res = out["result"]\r
    failed = next((c["code"] for c in out["checks"] if not c["ok"] and c["code"] != "cf_omocode_order"), "")\r
    return res[CODE_FIELD[kind]], "yes" if res["valid"] else "no", failed\r
\r
\r
def task_workflow(params):\r
    text = params.get("text")\r
    tab = wt._read_table(text)\r
    plan, skipped = _plan(params, tab, text)\r
    names, body = tab["names"], tab["body"]\r
    width = len(names)\r
    # every row as wide as the widest one, so the added columns stay aligned; a longer row keeps all its cells\r
    full = max([width] + [len(r) for r in body])\r
    first_row = 2 if tab["header"] else 1\r
    rows = [list(r) + [""] * (full - len(r)) for r in body]\r
    head = names + [""] * (full - width)\r
    added, extra = [], [[] for _ in rows]\r
    taken = set(names)\r
\r
    def new_col(label):\r
        out, k = label, 2\r
        while out in taken:\r
            out, k = f"{label}_{k}", k + 1\r
        taken.add(out)\r
        added.append(out)\r
        return out\r
\r
    diff, steps_out, checks, tools = [], [], [], [TOOL]\r
    for step, cols in plan:\r
        if step == "numbers":\r
            summary = []\r
            for c in cols:\r
                j = wt._column(tab, c)\r
                new_col(f"{names[j]}_value")\r
                new_col(f"{names[j]}_status")\r
                n = {"ok": 0, "converted": 0, "missing": 0, "non_numeric": 0}\r
                for i, r in enumerate(rows):\r
                    v, status = tab["num"](r[j])\r
                    n[status] += 1\r
                    extra[i] += ["" if v is None else repr(v), status]\r
                    if status == "converted":\r
                        diff.append({"row": first_row + i, "column": names[j], "before": r[j].strip(), "after": repr(v), "why": "number_format"})\r
                summary.append({"column": names[j], **n})\r
                checks.append({"code": "wf_numbers", "ok": n["non_numeric"] == 0, "args": {"column": names[j], "read": n["ok"] + n["converted"], "n": len(rows)}})\r
            steps_out.append({"step": step, "columns": summary})\r
        elif step == "codes":\r
            summary = []\r
            for c, kind in cols.items():\r
                j = wt._column(tab, c)\r
                for suffix in ("normalised", "valid", "reason"):\r
                    new_col(f"{names[j]}_{suffix}")\r
                n = {"valid": 0, "invalid": 0, "missing": 0}\r
                for i, r in enumerate(rows):\r
                    cell = r[j].strip()\r
                    if not cell:\r
                        n["missing"] += 1\r
                        extra[i] += ["", "", "missing"]\r
                        continue\r
                    norm, valid, reason = _code(kind, cell)\r
                    n["valid" if valid == "yes" else "invalid"] += 1\r
                    extra[i] += [norm, valid, reason]\r
                    if norm and norm != cell:\r
                        diff.append({"row": first_row + i, "column": names[j], "before": cell, "after": norm, "why": "normalised"})\r
                summary.append({"column": names[j], "kind": kind, **n})\r
                checks.append({"code": "wf_codes", "ok": n["invalid"] == 0, "args": {"column": names[j], "kind": kind, "valid": n["valid"], "n": n["valid"] + n["invalid"]}})\r
            steps_out.append({"step": step, "columns": summary})\r
            if wp.TOOL not in tools:\r
                tools.append(wp.TOOL)\r
        elif step == "dates":\r
            summary = []\r
            for c in cols:\r
                j = wt._column(tab, c)\r
                new_col(f"{names[j]}_iso")\r
                new_col(f"{names[j]}_status")\r
                n = {"ok": 0, "converted": 0, "invalid": 0, "missing": 0}\r
                for i, r in enumerate(rows):\r
                    cell = r[j].strip()\r
                    if not cell:\r
                        n["missing"] += 1\r
                        extra[i] += ["", "missing"]\r
                        continue\r
                    try:\r
                        iso = wp._parse_date(cell, "x").isoformat()\r
                    except wp.ProductError:\r
                        n["invalid"] += 1\r
                        extra[i] += ["", "invalid"]\r
                        continue\r
                    status = "ok" if iso == cell else "converted"\r
                    n[status] += 1\r
                    extra[i] += [iso, status]\r
                    if status == "converted":\r
                        diff.append({"row": first_row + i, "column": names[j], "before": cell, "after": iso, "why": "date_iso"})\r
                summary.append({"column": names[j], **n})\r
                checks.append({"code": "wf_dates", "ok": n["invalid"] == 0, "args": {"column": names[j], "read": n["ok"] + n["converted"], "n": n["ok"] + n["converted"] + n["invalid"]}})\r
            steps_out.append({"step": step, "columns": summary})\r
            if wp.TOOL not in tools:\r
                tools.append(wp.TOOL)\r
        else:\r
            steps_out.append({"step": step, "columns": []})\r
    out = io.StringIO()\r
    w = csv.writer(out, delimiter=tab["delimiter"], lineterminator="\\n")\r
    w.writerow(head + added)\r
    for r, e in zip(rows, extra):\r
        w.writerow(r + e)\r
    cleaned = out.getvalue()\r
    # the original columns are written back unchanged: read the cleaned table again and compare, cell by cell\r
    back = list(csv.reader(io.StringIO(cleaned, newline=""), delimiter=tab["delimiter"]))\r
    kept = back[0][:width] == names and len(back) - 1 == len(rows) and all(b[:full] == r for b, r in zip(back[1:], rows))\r
    checks.append({"code": "wf_original_kept", "ok": kept, "args": {"rows": len(rows), "columns": width}})\r
    res = {"rows": len(rows), "columns": names, "delimiter": tab["delimiter"], "header": tab["header"], "steps": steps_out,\r
           "added_columns": added, "diff": diff[:DIFF_SHOWN], "diff_total": len(diff), "cleaned_csv": cleaned}\r
    if any(s == "fingerprint" for s, _c in plan):\r
        res["input_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()\r
        res["output_sha256"] = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()\r
        tools.append({"name": "hashlib (Python standard library)", "version": "-"})\r
    transforms = list(tab["transforms"])\r
    if not tab["header"]:                                 # the cleaned table names its columns: a first row is added\r
        transforms.append({"code": "wf_header_added", "before": "", "after": ", ".join(names[:6])})\r
    transforms += [{"code": f"wf_{d['why']}", "before": d["before"][:60], "after": d["after"][:60]} for d in diff[:10]]\r
    warnings = [{"code": "wf_step_skipped", "args": {"step": s}} for s in skipped]\r
    if len(diff) > DIFF_SHOWN:\r
        warnings.append({"code": "wf_diff_cut", "args": {"shown": DIFF_SHOWN, "total": len(diff)}})\r
    if any(s == "codes" for s, _c in plan):\r
        warnings.append({"code": "wf_formal_only", "args": {}})\r
    if tab["ragged"]:\r
        warnings.append({"code": "wf_ragged", "args": {"count": len(tab["ragged"]), "rows": tab["ragged"][:10]}})\r
    return wt._answer(res, tools, transforms, checks, warnings)\r
\r
\r
wt.TASKS["workflow"] = task_workflow\r
`),await r.runPythonAsync(`import sys, types
_m = types.ModuleType('ws_workflow')
exec(_wf_src, _m.__dict__)
sys.modules['ws_workflow'] = _m
del _m, _wf_src
`),t.postMessage({kind:`ready`}),r}let i=null;t.onmessage=async a=>{let o=a.data;if(o.kind===`init`)i=o;else try{n||(n=r(i),n.catch(()=>{n=null}));let a=await n;a.globals.set(`_p`,o.params),a.globals.set(`_task`,o.task),a.globals.set(`_hasd`,o.data!==null),a.globals.set(`_d`,o.data??0);let s=o.hash&&o.data?await e(o.data):null,c=await a.runPythonAsync(`import ws_tasks
ws_tasks.run(_task, _p, bytes(_d.to_py()) if _hasd else None)`);t.postMessage({kind:`result`,id:o.id,json:c,fp:s})}catch(e){t.postMessage({kind:`failed`,id:o.id,error:String(e.message||e).slice(-4e3)})}};