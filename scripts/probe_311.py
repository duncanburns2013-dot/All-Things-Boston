#!/usr/bin/env python3
"""
Throwaway probe: confirm a CI runner can reach data.boston.gov's CKAN API and
report what the 311 dataset actually exposes.

Run once from Actions, read the log, then delete this file. Nothing depends on it.
"""
import json
import sys
from urllib.request import urlopen, Request
from urllib.parse import quote

BASE = "https://data.boston.gov/api/3/action"
UA = "All-Things-Boston/1.0 (+https://github.com/duncanburns2013-dot/All-Things-Boston)"


def get(url):
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main():
    print("=" * 70)
    print("1. package_show — what resources exist?")
    print("=" * 70)
    try:
        pkg = get(f"{BASE}/package_show?id=311-service-requests")["result"]
    except Exception as e:
        print(f"FAILED to reach CKAN: {e}")
        return 1

    print(f"title            : {pkg.get('title')}")
    print(f"metadata_modified: {pkg.get('metadata_modified')}")
    print(f"num_resources    : {pkg.get('num_resources')}")
    print()
    live = []
    for r in pkg.get("resources", []):
        ds = r.get("datastore_active")
        print(f"  {str(r.get('name'))[:46]:48s} fmt={str(r.get('format')):5s} "
              f"datastore={str(ds):5s} id={r.get('id')}")
        print(f"      last_modified={r.get('last_modified')}  created={r.get('created')}")
        if ds:
            live.append(r)

    if not live:
        print("\nNo datastore-active resources — SQL endpoint unavailable.")
        return 0

    newest = live[0]
    print()
    print("=" * 70)
    print(f"2. schema of newest datastore resource: {newest.get('name')}")
    print("=" * 70)
    rid = newest["id"]
    try:
        sample = get(f"{BASE}/datastore_search?resource_id={rid}&limit=1")["result"]
        print(f"total rows: {sample.get('total'):,}")
        print("fields:")
        for f in sample.get("fields", []):
            print(f"   {f.get('id'):34s} {f.get('type')}")
        if sample.get("records"):
            print("\nsample record:")
            for k, v in list(sample["records"][0].items())[:30]:
                print(f"   {k:34s} = {str(v)[:60]}")
    except Exception as e:
        print(f"datastore_search failed: {e}")

    print()
    print("=" * 70)
    print("3. can we aggregate server-side? (counts by neighborhood)")
    print("=" * 70)
    sql = (f'SELECT "neighborhood", COUNT(*) AS n '
           f'FROM "{rid}" GROUP BY "neighborhood" ORDER BY n DESC LIMIT 12')
    try:
        rows = get(f"{BASE}/datastore_search_sql?sql={quote(sql)}")["result"]["records"]
        for r in rows:
            print(f"   {str(r.get('neighborhood'))[:38]:40s} {r.get('n')}")
        print("\n-> datastore_search_sql works; aggregation can happen server-side.")
    except Exception as e:
        print(f"datastore_search_sql failed: {e}")
        print("-> would need to page the CSV instead.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
