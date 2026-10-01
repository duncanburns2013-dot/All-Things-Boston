#!/usr/bin/env python3
"""
update_311_data.py

Builds data/311-latest.json from Boston's 311 open data (data.boston.gov CKAN).

Why this is not a one-resource fetch
------------------------------------
Boston moved 311 to a new backend (Creatio/Cartegraph) in October 2025. The open
data did NOT cut over — it SPLIT. As of this writing both of these are live and
were last modified the same day:

    311 Service Requests - 2026        (legacy schema)   last_modified 2026-07-30
    311 Service Requests - NEW SYSTEM  (new schema)      last_modified 2026-07-30

Cases land in one or the other by service type. So any figure covering late 2025
onward has to UNION both, and the two use different column names for the same
concepts:

    concept        legacy              new system
    ------------   -----------------   -----------------
    case id        case_enquiry_id     case_id
    opened         open_dt             open_date
    closed         closed_dt           close_date
    category       type                case_topic
    neighborhood   neighborhood        neighborhood

Pointing an updater at the obvious resource would silently under-count everything
after October 2025 and still report success. That is the failure mode this script
exists to avoid, so it:

  * discovers resources by NAME at runtime rather than hardcoding UUIDs (Boston
    adds a new per-year resource every January),
  * introspects each resource's fields and maps them, rather than assuming a
    schema,
  * records in the output exactly which resources fed each number, and
  * treats a zero-row answer as a failure to report, not a success.
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen, Request

BASE = "https://data.boston.gov/api/3/action"
DATASET = "311-service-requests"
UA = "All-Things-Boston/1.0 (+https://github.com/duncanburns2013-dot/All-Things-Boston)"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "311-latest.json")

FIRST_YEAR = 2019          # the tab's annual chart starts here
STALE_DAYS = 30            # "unresolved >30 days"

# The two schemas do not share a neighborhood vocabulary. Legacy uses Boston's
# combined planning labels; NEW SYSTEM uses atomic ones. Merging on the raw
# string therefore splits one place across several rows — South Boston came out
# as three separate entries (7,792 + 2,574 + 261) and Allston/Brighton as three
# more, while Dorchester happened to match in both and looked fine.
#
# Fold the atomic names into the combined labels, which is what the dashboard
# and Boston's own neighborhood reporting use. Anything unmapped is reported.
CANONICAL = {
    "South Boston": "South Boston / South Boston Waterfront",
    "South Boston Waterfront": "South Boston / South Boston Waterfront",
    "Allston": "Allston / Brighton",
    "Brighton": "Allston / Brighton",
    "Downtown": "Downtown / Financial District",
    "Financial District": "Downtown / Financial District",
    "Fenway": "Fenway / Kenmore / Audubon Circle / Longwood",
    "Kenmore": "Fenway / Kenmore / Audubon Circle / Longwood",
    "Audubon Circle": "Fenway / Kenmore / Audubon Circle / Longwood",
    "Longwood": "Fenway / Kenmore / Audubon Circle / Longwood",
    "Mattapan": "Greater Mattapan",
}

# Not a neighborhood — the unassigned/citywide bucket. Kept in the output under
# its own key so the total still reconciles, but flagged so it is never charted
# as if it were a place.
CATCHALL = {"Boston"}


def canonical_neighborhood(name):
    return CANONICAL.get(name, name)

warnings = []


def warn(msg):
    warnings.append(msg)
    print(f"::warning::{msg}" if os.environ.get("GITHUB_ACTIONS") else f"WARNING: {msg}")


# data.boston.gov sits behind a WAF that throttles bursts. The first run of this
# script fired ~30 datastore_search_sql calls in 18 seconds and got HTTP 403
# partway through — after the annual counts had succeeded, so the failure landed
# on the detail aggregates rather than anywhere obvious. Pace the calls and back
# off rather than hammering it.
MIN_INTERVAL = 1.2      # seconds between requests
MAX_RETRIES = 5
_last_call = [0.0]


def api(path):
    delay = 3.0
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        wait = MIN_INTERVAL - (time.monotonic() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.monotonic()
        req = Request(f"{BASE}/{path}",
                      headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urlopen(req, timeout=120) as r:
                payload = json.loads(r.read())
            if not payload.get("success"):
                raise RuntimeError(f"CKAN returned success=false for {path[:80]}")
            return payload["result"]
        except HTTPError as e:
            last_err = e
            # 403 here is throttling, not authorisation — the same URL succeeds
            # when paced. Retry those alongside 429/5xx; fail fast on anything else.
            if e.code not in (403, 429, 500, 502, 503, 504):
                raise
        except (URLError, TimeoutError) as e:
            last_err = e
        if attempt < MAX_RETRIES:
            print(f"    retry {attempt}/{MAX_RETRIES - 1} after {delay:.0f}s ({last_err})")
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"gave up after {MAX_RETRIES} attempts: {last_err}")


def sql(query):
    return api(f"datastore_search_sql?sql={quote(query)}")["records"]


def guard(label, fn, default):
    """Run an aggregate; downgrade any failure to a warning instead of killing the run."""
    try:
        return fn()
    except Exception as e:
        warn(f"{label}: {e}")
        return default


# ---------------------------------------------------------------- discovery

def discover():
    """
    Return [{name, id, kind, year}] for every datastore-active 311 resource.

    kind is 'legacy' or 'new'; year is the calendar year for per-year legacy
    resources and None for NEW SYSTEM (which is a rolling table, not a year).
    """
    pkg = api(f"package_show?id={DATASET}")
    out = []
    for r in pkg.get("resources", []):
        if not r.get("datastore_active"):
            continue
        name = (r.get("name") or "").strip()
        if "311" not in name.upper():
            continue
        if "NEW SYSTEM" in name.upper():
            out.append({"name": name, "id": r["id"], "kind": "new", "year": None,
                        "last_modified": r.get("last_modified")})
            continue
        m = re.search(r"(20\d{2})\s*$", name)
        if m:
            out.append({"name": name, "id": r["id"], "kind": "legacy",
                        "year": int(m.group(1)), "last_modified": r.get("last_modified")})
    if not out:
        raise RuntimeError("no datastore-active 311 resources found")
    return out


def fields_of(resource_id):
    res = api(f"datastore_search?resource_id={resource_id}&limit=0")
    return {f["id"] for f in res.get("fields", [])}


def map_columns(available):
    """Resolve concept -> actual column name, tolerating either schema."""
    def pick(*candidates):
        for c in candidates:
            if c in available:
                return c
        return None
    cols = {
        "opened": pick("open_dt", "open_date"),
        "closed": pick("closed_dt", "close_date"),
        "category": pick("type", "case_topic", "service_name"),
        "neighborhood": pick("neighborhood"),
        "status": pick("case_status"),
    }
    return cols


# ---------------------------------------------------------------- aggregates

def count_for_year(res, cols, year):
    """Row count for a calendar year within one resource."""
    o = cols["opened"]
    if not o:
        return 0
    rows = sql(f'SELECT COUNT(*) AS n FROM "{res["id"]}" '
               f'WHERE "{o}" >= \'{year}-01-01\' AND "{o}" < \'{year + 1}-01-01\'')
    return int(rows[0]["n"]) if rows else 0


def by_neighborhood(res, cols, year):
    """
    {neighborhood: {n, avg_days}} for one resource/year.

    Split deliberately into two queries. The combined form —
    COUNT(*) plus AVG(EXTRACT(EPOCH FROM (closed::timestamp - opened::timestamp)))
    in one GROUP BY — was rejected with HTTP 403 on every retry, while the plain
    grouped count succeeds reliably (the schema probe ran exactly that against
    the same resource). So the WAF is pricing the query, not throttling the
    caller: retrying an expensive statement just fails five times more slowly.

    The counts are the figures the tab actually leads with, so they run alone and
    are kept even when the resolution-time average is refused.
    """
    o, c, nb = cols["opened"], cols["closed"], cols["neighborhood"]
    if not (o and nb):
        return {}

    window = f'"{o}" >= \'{year}-01-01\' AND "{o}" < \'{year + 1}-01-01\''
    rows = sql(f'SELECT "{nb}" AS nb, COUNT(*) AS n FROM "{res["id"]}" '
               f'WHERE {window} GROUP BY "{nb}"')
    out = {}
    for r in rows:
        nbname = (r.get("nb") or "").strip()
        if nbname:
            out[nbname] = {"n": int(r["n"]), "avg_days": None}

    if not c:
        return out

    # Resolution time is a bonus, not a blocker.
    #
    # EXTRACT(EPOCH FROM (ts - ts)) is refused with 403 however it is paced, so
    # subtract dates instead: in Postgres date - date yields an integer number of
    # days directly, which is the unit wanted anyway and costs far less than
    # building and decomposing an interval.
    def _avg():
        return sql(
            f'SELECT "{nb}" AS nb, AVG("{c}"::date - "{o}"::date) AS avg_days '
            f'FROM "{res["id"]}" WHERE {window} AND "{c}" IS NOT NULL GROUP BY "{nb}"')

    for r in guard(f"avg_resolution[{res['name']}]", _avg, []):
        nbname = (r.get("nb") or "").strip()
        if nbname in out and r.get("avg_days") is not None:
            out[nbname]["avg_days"] = float(r["avg_days"])
    return out


def by_category(res, cols, year, limit=25):
    o, cat = cols["opened"], cols["category"]
    if not (o and cat):
        return {}
    rows = sql(f'SELECT "{cat}" AS c, COUNT(*) AS n FROM "{res["id"]}" '
               f'WHERE "{o}" >= \'{year}-01-01\' AND "{o}" < \'{year + 1}-01-01\' '
               f'GROUP BY "{cat}" ORDER BY n DESC LIMIT {limit}')
    return {(r.get("c") or "Unknown").strip(): int(r["n"]) for r in rows}


def rodent_count(res, cols, year):
    o, cat = cols["opened"], cols["category"]
    if not (o and cat):
        return 0
    rows = sql(f'SELECT COUNT(*) AS n FROM "{res["id"]}" '
               f'WHERE "{o}" >= \'{year}-01-01\' AND "{o}" < \'{year + 1}-01-01\' '
               f"AND \"{cat}\" ILIKE '%rodent%'")
    return int(rows[0]["n"]) if rows else 0


def unresolved_over_30d(res, cols, year, limit=15):
    """
    Open cases older than STALE_DAYS, by category.

    Uses a plain date comparison rather than EXTRACT(EPOCH FROM ...) arithmetic.
    The arithmetic form was refused with 403 on every retry (see by_neighborhood);
    comparing the open date against a fixed cutoff is the same question asked
    cheaply, and it reads more directly besides: still open, opened long enough
    ago to be overdue.
    """
    o, c, cat = cols["opened"], cols["closed"], cols["category"]
    if not (o and c and cat):
        return {}
    cutoff = (datetime.now(timezone.utc) - timedelta(days=STALE_DAYS)).strftime("%Y-%m-%d")
    rows = sql(
        f'SELECT "{cat}" AS c, COUNT(*) AS n FROM "{res["id"]}" '
        f'WHERE "{o}" >= \'{year}-01-01\' AND "{o}" < \'{year + 1}-01-01\' '
        f'AND "{c}" IS NULL AND "{o}" < \'{cutoff}\' '
        f'GROUP BY "{cat}" ORDER BY n DESC LIMIT {limit}')
    return {(r.get("c") or "Unknown").strip(): int(r["n"]) for r in rows}


def merge_neighborhoods(parts):
    """
    Union per-resource neighborhood dicts onto canonical names, re-weighting the
    average by count.

    Both steps matter. Canonicalising first stops one place being counted as
    several; weighting by count stops a mean-of-means — averaging a 7,792-case
    resource against a 261-case one as equals would be simply wrong.
    """
    out = {}
    for part in parts:
        for raw, v in part.items():
            nb = canonical_neighborhood(raw)
            cur = out.setdefault(nb, {"n": 0, "_days_sum": 0.0, "_days_n": 0,
                                      "_raw": set()})
            cur["n"] += v["n"]
            cur["_raw"].add(raw)
            if v["avg_days"] is not None:
                cur["_days_sum"] += v["avg_days"] * v["n"]
                cur["_days_n"] += v["n"]
    for nb, v in out.items():
        v["avg_days"] = round(v["_days_sum"] / v["_days_n"], 2) if v["_days_n"] else None
        v["source_labels"] = sorted(v.pop("_raw"))
        v["is_catchall"] = nb in CATCHALL
        del v["_days_sum"], v["_days_n"]
    return out


def merge_counts(parts):
    out = {}
    for part in parts:
        for k, n in part.items():
            out[k] = out.get(k, 0) + n
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


# ---------------------------------------------------------------- main

def main():
    print("Discovering 311 resources...")
    resources = discover()
    for r in resources:
        print(f"  {r['kind']:6s} {str(r['year']):5s} {r['name'][:44]:46s} {r['id']}")

    # Resolve each resource's column names once.
    for r in resources:
        try:
            r["cols"] = map_columns(fields_of(r["id"]))
        except Exception as e:
            warn(f"{r['name']}: schema introspection failed ({e}); skipping")
            r["cols"] = None
    resources = [r for r in resources if r["cols"]]

    new_sys = [r for r in resources if r["kind"] == "new"]
    legacy = {r["year"]: r for r in resources if r["kind"] == "legacy"}
    this_year = datetime.now(timezone.utc).year
    years = [y for y in range(FIRST_YEAR, this_year + 1)]

    # Which resources cover a given calendar year: the per-year legacy resource
    # plus NEW SYSTEM for any year it overlaps (it began Oct 2025 and is rolling).
    def sources_for(year):
        srcs = []
        if year in legacy:
            srcs.append(legacy[year])
        if year >= 2025:
            srcs.extend(new_sys)
        return srcs

    annual = {}
    provenance = {}
    for y in years:
        srcs = sources_for(y)
        if not srcs:
            warn(f"no resource covers {y}")
            continue
        per = {}
        for r in srcs:
            try:
                per[r["name"]] = count_for_year(r, r["cols"], y)
            except Exception as e:
                warn(f"{r['name']} {y}: count failed ({e})")
                per[r["name"]] = None
        got = [v for v in per.values() if v is not None]
        annual[str(y)] = sum(got) if got else None
        provenance[str(y)] = per
        if annual[str(y)] == 0:
            warn(f"{y} totalled 0 rows across {len(srcs)} resource(s)")
        print(f"  {y}: {annual[str(y)]}  {per}")

    # Detail views for the latest year and the two complete years before it.
    # The tab's charts are per-year, and a single year cannot answer whether a
    # figure on it is stale or was measuring something different all along —
    # comparing this year's partial total against a prior full year proves
    # nothing either way.
    populated = sorted(int(y) for y, v in annual.items() if v)
    detail_years = populated[-3:] if populated else [this_year]
    detail_year = detail_years[-1]
    print(f"\nDetail years: {detail_years}")

    details = {}
    for dy in detail_years:
        dsrcs = sources_for(dy)
        print(f"  detail {dy} from {[r['name'] for r in dsrcs]}")
        details[str(dy)] = {
            "by_neighborhood": merge_neighborhoods([
                guard(f"by_neighborhood[{dy}][{r['name']}]",
                      lambda r=r, dy=dy: by_neighborhood(r, r["cols"], dy), {})
                for r in dsrcs]),
            "top_categories": merge_counts([
                guard(f"by_category[{dy}][{r['name']}]",
                      lambda r=r, dy=dy: by_category(r, r["cols"], dy), {})
                for r in dsrcs]),
            "unresolved_over_30d_by_type": merge_counts([
                guard(f"unresolved[{dy}][{r['name']}]",
                      lambda r=r, dy=dy: unresolved_over_30d(r, r["cols"], dy), {})
                for r in dsrcs]),
        }

    # Top-level keys stay pointed at the newest year so existing consumers keep
    # working; the per-year breakdown lives under `details`. Read them back
    # rather than re-running the same queries a second time.
    latest = details[str(detail_year)]
    nb = latest["by_neighborhood"]
    cats = latest["top_categories"]
    stale = latest["unresolved_over_30d_by_type"]

    rodents = {}
    for y in years:
        srcs = sources_for(y)
        got = guard(f"rodent[{y}]",
                    lambda srcs=srcs, y=y: sum(rodent_count(r, r["cols"], y) for r in srcs),
                    None)
        if got is not None:
            rodents[str(y)] = got

    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "data.boston.gov CKAN — 311 Service Requests",
        "dataset_url": f"https://data.boston.gov/dataset/{DATASET}",
        "note": ("Boston split 311 across a legacy per-year resource and a "
                 "differently-structured NEW SYSTEM resource when the backend "
                 "changed in Oct 2025. Years from 2025 union both."),
        "detail_year": detail_year,
        "detail_years": [str(y) for y in detail_years],
        "details": details,
        "resources_used": [
            {"name": r["name"], "id": r["id"], "kind": r["kind"],
             "year": r["year"], "last_modified": r["last_modified"],
             "columns": r["cols"]}
            for r in resources
        ],
        "annual_totals": annual,
        "annual_provenance": provenance,
        "by_neighborhood": nb,
        "top_categories": dict(list(cats.items())[:25]),
        "rodent_by_year": rodents,
        "unresolved_over_30d_by_type": stale,
        "warnings": warnings,
    }

    # A run that lost the detail views to throttling is not a usable snapshot.
    # Keep the previous one rather than publishing a hollowed-out file — but say
    # so in the output, so a persistent failure is visible instead of absorbed.
    if not nb and not cats:
        prev = None
        try:
            with open(OUT, encoding="utf-8") as f:
                prev = json.load(f)
        except (OSError, ValueError):
            pass
        if prev and prev.get("by_neighborhood"):
            warn("detail aggregates all failed — preserving previous snapshot")
            prev["preserved_from_cache"] = True
            prev["last_attempted_at"] = payload["fetched_at"]
            prev["annual_totals"] = annual          # counts did succeed; keep them fresh
            prev["annual_provenance"] = provenance
            prev["warnings"] = warnings
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump(prev, f, indent=2)
            # Stamp from the preserved payload too. The annual totals above ARE
            # fresh, and the Total Requests KPI reads them, so returning here
            # would leave the page quoting a count the file no longer holds.
            stamp_page(prev)
            print(f"\nPreserved previous snapshot in {OUT} (annual totals refreshed)")
            return 0
        warn("detail aggregates all failed and no previous snapshot exists")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    stamp_page(payload)
    print(f"\nWrote {OUT}")
    print(f"  {len(nb)} neighborhoods, {len(cats)} categories, {len(warnings)} warning(s)")
    return 0



# ---------------------------------------------------------------------------
# index.html
# ---------------------------------------------------------------------------
# This script wrote data/311-latest.json and nothing wrote the page, so the 311
# tab was hand-typed and every figure on it had drifted. Checked 2026-10-01
# against the file this script produces:
#
#   published                          actual
#   "3-4x longer" for 4 neighbourhoods  0.91x -- they are very slightly FASTER
#   "Mattapan 11.2 days"                Greater Mattapan 4.12 days
#   "Back Bay 3.1 days"                 3.37 days
#   "3.6x service speed disparity"      0.91x
#   "Dorchester alone = 25%"            14.6% of requests mapped to a nbhd
#   "138K total requests"               241,676 (Jan-Sep 2026)
#   "+62% rodent since 2019"            +98%
#   "14% unresolved >30 days"           22.1%
#
# The headline was not merely stale, it was REVERSED: the four neighbourhoods
# said to wait three to four times longer for 311 service do not wait longer at
# all. A page that argues a service-equity gap from the city's own data has to
# follow that data when it says otherwise.
#
# Anchors that fail to match abort rather than publishing a half-updated page.
HTML = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "index.html")

# the four neighbourhoods the page names; "Mattapan" is "Greater Mattapan" in
# the SOS-side vocabulary this script canonicalises to
HIGH = ["Dorchester", "Roxbury", "Greater Mattapan", "Jamaica Plain"]
MIN_N = 1000          # below this an average is too volatile to rank on


def stamp_page(payload):
    import re as _re
    bn = {n: v for n, v in payload["by_neighborhood"].items()
          if not v.get("is_catchall") and v.get("avg_days") is not None}
    if len(bn) < 10:
        print("  page: too few neighbourhoods to stamp safely - left alone")
        return
    total = sum(v["n"] for v in bn.values())
    hi = [bn[n] for n in HIGH if n in bn]
    lo = [v for n, v in bn.items() if n not in HIGH]
    if not hi or not lo:
        print("  page: cannot identify the named neighbourhoods - left alone")
        return
    hw = sum(v["avg_days"] * v["n"] for v in hi) / sum(v["n"] for v in hi)
    lw = sum(v["avg_days"] * v["n"] for v in lo) / sum(v["n"] for v in lo)
    ratio = hw / lw

    big = {n: v for n, v in bn.items() if v["n"] >= MIN_N}
    slowest = sorted(big.items(), key=lambda kv: -kv[1]["avg_days"])[:3]
    dor = bn.get("Dorchester", {"n": 0})
    rod = payload.get("rodent_by_year", {})
    ry = sorted(rod)
    rod_pct = ((rod[ry[-1]] / rod[ry[0]] - 1) * 100) if len(ry) >= 2 else None
    year = payload.get("detail_year", "")

    # THREE different totals live in this payload and they are not interchangeable:
    #   232,203  the 23 real neighbourhoods          <- share/ratio denominator
    #   240,638  + a "Boston" catch-all of 8,435 the city never assigned
    #   241,676  + 1,038 with no neighbourhood field <- the actual request count
    # "Total Requests" has to be the last of those. The first run of this stamper
    # published 232,203 under that label, understating the year by 9,473 requests
    # and inviting a comparison against the full-year 306,756 in 2024.
    grand = payload.get("annual_totals", {}).get(str(year)) or total
    catchall = sum(v["n"] for n, v in payload["by_neighborhood"].items()
                   if v.get("is_catchall"))

    # Partial year: the 2026 figure is Jan-Sep, against 280K-307K for full years.
    # Labelling it plain "2026" reads as a 21% collapse in 311 volume that is
    # really just a short year -- the same trap as calling semi-annual lobbying
    # filings "this year".
    fetched = str(payload.get("fetched_at", ""))
    partial = fetched[:4] == str(year)
    months = {"01": "January", "02": "February", "03": "March", "04": "April",
              "05": "May", "06": "June", "07": "July", "08": "August",
              "09": "September", "10": "October", "11": "November",
              "12": "December"}.get(fetched[5:7], "")
    span = f"{year} YTD" if partial else str(year)
    span_long = (f"January–{months} {year}" if partial and months
                 else str(year))

    uns = payload.get("unresolved_over_30d_by_type", {})
    # by TYPE, not by neighbourhood, so these counts span the catch-all and the
    # unmapped records too -- the denominator is every request, not just the
    # neighbourhood-attributed ones.
    uns_pct = sum(uns.values()) / grand * 100 if uns and grand else None

    faster = "slightly faster" if ratio < 1 else "slightly slower"
    slow_txt = ", ".join(f"{n} ({v['avg_days']:.1f}d)" for n, v in slowest)
    dor_pct = dor["n"] / total * 100
    callout = (
        f'<div class="co red"><strong>What the 311 data actually shows:</strong> the four '
        f'neighbourhoods absorbing 80% of Boston\u2019s shootings do <strong>not</strong> wait '
        f'longer for 311 service. Weighted by request volume they average '
        f'<strong>{hw:.1f} days</strong> to resolution against <strong>{lw:.1f}</strong> for the '
        f'rest of the city \u2014 {faster}. The slowest resolutions are in {slow_txt}, none of '
        f'which are in that group. Dorchester files the most requests of any neighbourhood '
        f'({dor_pct:.1f}% of those mapped to one) because it is the largest, not because it is '
        f'underserved. Caveats: this averages requests that were <em>closed</em>, and the open '
        f'dataset does not break unresolved requests out by neighbourhood; of '
        f'{grand:,} requests, {catchall:,} carry only a city-wide “Boston” label and '
        f'are excluded from the neighbourhood figures. '
        f'Source: data.boston.gov 311 open dataset, {span_long}.</div>')

    subs = [
        ("equity callout",
         r'<div class="co red"><strong>(?:Service Equity Gap|What the 311 data actually shows):</strong>.*?</div>',
         lambda m: callout),
        ("total-requests KPI",
         r'(<div class="kpi red"><div class="v">)[\d.]+K(</div><div class="lb">Total Requests<br>)[^<]*',
         lambda m: f'{m.group(1)}{grand/1000:.0f}K{m.group(2)}{span}'),
        # Every anchor below has to match this stamper's OWN output as well as
        # the original hand-written markup, or the second run aborts on a page
        # it wrote itself. That is exactly what happened the first time: the
        # label became "Gtr Mattapan" and the anchor still wanted "Mattapan".
        ("Mattapan KPI",
         r'<div class="kpi red"><div class="v">[\d.]+d</div>'
         r'<div class="lb">(?:Gtr )?Mattapan Avg<br>Resolution</div></div>',
         lambda m: f'<div class="kpi red"><div class="v">{bn["Greater Mattapan"]["avg_days"]:.1f}d</div>'
                   f'<div class="lb">Gtr Mattapan Avg<br>Resolution</div></div>'),
        ("Back Bay KPI",
         r'(<div class="kpi green"><div class="v">)[\d.]+d(</div><div class="lb">Back Bay Avg)',
         lambda m: f'{m.group(1)}{bn["Back Bay"]["avg_days"]:.1f}d{m.group(2)}'),
        ("disparity KPI",
         r'<div class="kpi amber"><div class="v">[\d.]+\u00d7</div>'
         r'<div class="lb">(?:Service Speed<br>Disparity|Those 4 vs<br>the Rest)'
         r'</div></div>',
         lambda m: f'<div class="kpi amber"><div class="v">{ratio:.2f}\u00d7</div>'
                   f'<div class="lb">Those 4 vs<br>the Rest</div></div>'),
        ("s1 subtitle",
         r'(<h3>311 Complaints by Neighborhood )\([^)]*\)(</h3><p class="cs">)[^<]*',
         lambda m: f'{m.group(1)}({span}, thousands){m.group(2)}'
                   f'Red = the 4 neighbourhoods named above. Dorchester = '
                   f'{dor_pct:.1f}% of the {total:,} requests mapped to a neighbourhood.'),
        ("s4 subtitle",
         r'(<h3>Average 311 Resolution Time by Neighborhood \(Days\)</h3><p class="cs">)[^<]*',
         lambda m: f'{m.group(1)}Sorted slowest to fastest. Red = the 4 neighbourhoods '
                   f'with 80% of shootings \u2014 they are not the slowest.'),
    ]
    if rod_pct is not None:
        subs.append(("rodent KPI",
                     r'(<div class="kpi purple"><div class="v">)[+\-][\d.]+%(</div><div class="lb">Rodent Complaints<br>)[^<]*',
                     lambda m: f'{m.group(1)}{rod_pct:+.0f}%{m.group(2)}Since {ry[0]}'))
    if uns_pct is not None:
        # anchored on its own label: an unanchored "first kpi orange with a
        # percentage" matched the EDUCATION tab's Grad Rate and rewrote 79.7% to
        # 23% on the first run of this stamper.
        subs.append(("unresolved KPI",
                     r'(<div class="kpi orange"><div class="v">)[\d.]+%'
                     r'(</div><div class="lb">Unresolved<br>)',
                     lambda m: f'{m.group(1)}{uns_pct:.0f}%{m.group(2)}'))

    # chart s1: hardcoded thousands, drifted (Dorchester 35.0K vs a real 34.0K,
    # Roxbury 16.2K vs 21.0K)
    top = sorted(bn.items(), key=lambda kv: -kv[1]["n"])[:11]
    other = total - sum(v["n"] for _, v in top)
    labels = [n.split(" / ")[0] for n, _ in top] + ["Other"]
    vals = [round(v["n"] / 1000, 1) for _, v in top] + [round(other / 1000, 1)]
    subs.append(("s1 chart data",
                 r"(sc\('s1',\{type:'bar',data:\{labels:)\[[^\]]*\](,datasets:\[\{data:)\[[^\]]*\]",
                 lambda m: m.group(1) + json.dumps(labels) + m.group(2) + json.dumps(vals)))
    # The colour callback carried its OWN copy of the label list and looked the
    # bar up by index. Replacing only the chart's labels left that copy stale and
    # the red bars pointing at the wrong neighbourhoods. Keyed off the label
    # itself now, so there is nothing left to drift.
    short_high = [n.split(" / ")[0] for n in HIGH]
    subs.append(("s1 colour callback",
                 r"backgroundColor:function\(c\)\{(?:var n=\[[^\]]*\];)?return ?\[[^\]]*\]"
                 r"\.indexOf\((?:n\[c\.dataIndex\]|c\.chart\.data\.labels\[c\.dataIndex\])\)"
                 r">=0\?C\.r:C\.b\}",
                 lambda m: "backgroundColor:function(c){return "
                           + json.dumps(short_high)
                           + ".indexOf(c.chart.data.labels[c.dataIndex])>=0?C.r:C.b}"))

    with open(HTML, encoding="utf-8") as f:
        html = f.read()
    before = html
    for label, pat, repl in subs:
        html, n = _re.subn(pat, repl, html, count=1, flags=_re.S)
        if n != 1:
            sys.exit(f"index.html: anchor for '{label}' did not match - "
                     f"refusing to publish a half-updated page")
    if html == before:
        print("  page: already current")
        return
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  page: 311 tab stamped ({grand:,} requests, {ratio:.2f}x, "
          f"Dorchester {dor_pct:.1f}%)")


if __name__ == "__main__":
    sys.exit(main())
