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
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import urlopen, Request

BASE = "https://data.boston.gov/api/3/action"
DATASET = "311-service-requests"
UA = "All-Things-Boston/1.0 (+https://github.com/duncanburns2013-dot/All-Things-Boston)"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "311-latest.json")

FIRST_YEAR = 2019          # the tab's annual chart starts here
STALE_DAYS = 30            # "unresolved >30 days"

warnings = []


def warn(msg):
    warnings.append(msg)
    print(f"::warning::{msg}" if os.environ.get("GITHUB_ACTIONS") else f"WARNING: {msg}")


def api(path):
    req = Request(f"{BASE}/{path}", headers={"User-Agent": UA, "Accept": "application/json"})
    with urlopen(req, timeout=120) as r:
        payload = json.loads(r.read())
    if not payload.get("success"):
        raise RuntimeError(f"CKAN returned success=false for {path[:80]}")
    return payload["result"]


def sql(query):
    return api(f"datastore_search_sql?sql={quote(query)}")["records"]


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
    """{neighborhood: {n, avg_days}} for one resource/year."""
    o, c, nb = cols["opened"], cols["closed"], cols["neighborhood"]
    if not (o and nb):
        return {}
    avg = (f'AVG(EXTRACT(EPOCH FROM ("{c}"::timestamp - "{o}"::timestamp))/86400.0)'
           if c else "NULL")
    rows = sql(
        f'SELECT "{nb}" AS nb, COUNT(*) AS n, {avg} AS avg_days '
        f'FROM "{res["id"]}" '
        f'WHERE "{o}" >= \'{year}-01-01\' AND "{o}" < \'{year + 1}-01-01\' '
        f'GROUP BY "{nb}"')
    out = {}
    for r in rows:
        nbname = (r.get("nb") or "").strip()
        if not nbname:
            continue
        out[nbname] = {"n": int(r["n"]),
                       "avg_days": float(r["avg_days"]) if r.get("avg_days") else None}
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
    o, c, cat = cols["opened"], cols["closed"], cols["category"]
    if not (o and c and cat):
        return {}
    rows = sql(
        f'SELECT "{cat}" AS c, COUNT(*) AS n FROM "{res["id"]}" '
        f'WHERE "{o}" >= \'{year}-01-01\' AND "{o}" < \'{year + 1}-01-01\' '
        f'AND ("{c}" IS NULL OR '
        f'     EXTRACT(EPOCH FROM ("{c}"::timestamp - "{o}"::timestamp))/86400.0 > {STALE_DAYS}) '
        f'GROUP BY "{cat}" ORDER BY n DESC LIMIT {limit}')
    return {(r.get("c") or "Unknown").strip(): int(r["n"]) for r in rows}


def merge_neighborhoods(parts):
    """Union per-resource neighborhood dicts, re-weighting the average by count."""
    out = {}
    for part in parts:
        for nb, v in part.items():
            cur = out.setdefault(nb, {"n": 0, "_days_sum": 0.0, "_days_n": 0})
            cur["n"] += v["n"]
            if v["avg_days"] is not None:
                cur["_days_sum"] += v["avg_days"] * v["n"]
                cur["_days_n"] += v["n"]
    for nb, v in out.items():
        v["avg_days"] = round(v["_days_sum"] / v["_days_n"], 2) if v["_days_n"] else None
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

    # Latest year with data drives the detail views.
    detail_year = max((int(y) for y, v in annual.items() if v), default=this_year)
    print(f"\nDetail year: {detail_year}")
    dsrcs = sources_for(detail_year)

    nb = merge_neighborhoods([by_neighborhood(r, r["cols"], detail_year) for r in dsrcs])
    cats = merge_counts([by_category(r, r["cols"], detail_year) for r in dsrcs])
    stale = merge_counts([unresolved_over_30d(r, r["cols"], detail_year) for r in dsrcs])

    rodents = {}
    for y in years:
        srcs = sources_for(y)
        try:
            rodents[str(y)] = sum(rodent_count(r, r["cols"], y) for r in srcs)
        except Exception as e:
            warn(f"rodent {y}: {e}")

    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "data.boston.gov CKAN — 311 Service Requests",
        "dataset_url": f"https://data.boston.gov/dataset/{DATASET}",
        "note": ("Boston split 311 across a legacy per-year resource and a "
                 "differently-structured NEW SYSTEM resource when the backend "
                 "changed in Oct 2025. Years from 2025 union both."),
        "detail_year": detail_year,
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

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\nWrote {OUT}")
    print(f"  {len(nb)} neighborhoods, {len(cats)} categories, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
