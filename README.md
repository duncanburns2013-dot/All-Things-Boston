# All Things Boston

City government accountability dashboard — 8 tabs, 36 interactive charts, all sourced from official government data. Every department name and dollar amount verified page-by-page against the city's own ACFRs.

**Live Site:** https://duncanburns2013-dot.github.io/All-Things-Boston/

---

## 📊 Dashboard Tabs

| Tab | Charts | Topic | Sources |
|-----|--------|-------|---------|
| Budget | 5 | Veterans vs DEI/equity spending FY2019–FY2025 | City of Boston ACFRs |
| DEI Breakdown | 3 | All 14+ departments, two-tier categorization | City of Boston ACFRs |
| Payroll | 4 + interactive | Employee headcount & earnings by department | data.boston.gov |
| Crime | 8 | Neighborhood concentration, demographics, FBI data | FBI UCR, BPD, EOPSS |
| Education | 6 | BPS MCAS performance, achievement gaps, graduation | DESE/MCAS 2025 |
| ICE | 4 | Boston AOR arrests, operations, demographics | ICE ERO, UC Berkeley |
| Commercial RE | 6 | Office vacancy, CMBS, distressed sales, tax shift | C&W, Trepp, Colliers |
| Housing | — | Placeholder (links to MA Data Hub) | Warren Group, MLS PIN |

## Key Findings

### Budget — $548K → $28.5M (52× increase)
Veterans Services Department flatlined at $2.5M–$3.3M since FY2019 while combined DEI/equity departments went from $548K to **$28.5M** — a **52× increase**. Every year Veterans is budgeted ~$4.7M then slashed nearly in half before a dollar is spent. The city's total budget grew 41% over the same period ($3.35B → $4.74B).

### DEI Departments — Two-Tier Methodology
Departments are presented in two tiers, using exact names from the ACFR expenditure schedules:

**Tier 1 — Equity & Identity Offices ($14.3M in FY2025):** Office of Equity, Fair Housing & Equity (formerly Office of Civil Rights), Language & Community Access, Participatory Budgeting, Black Male Advancement, Office of Food Justice, LGBTQ+ Advancement, Supplier Diversity, Women's Commission. Departments with no operational service-delivery mission beyond equity/identity advocacy.

**Tier 2 — Equity-Adjacent / Operational ($14.1M in FY2025):** Police Accountability & Transparancy [sic — ACFR spelling], Office of Workforce Development, Office of Eco Opp & Inclusion. Departments with explicit equity framing but also perform operational functions (job training, civilian police oversight, economic development).

Combined: **$28.5M** in FY2025. Both subtotals are shown independently so readers can evaluate each tier on its own merits.

### Payroll — 46 → 429 employees
DEI-adjacent headcount went from **46 employees to 429** (CY2019→CY2025) while Boston Police **lost 177 officers** (3,271→3,094). Veterans stuck at 12–17 employees the entire time. BPS "Inclusion" positions alone (220 staff, $19.8M payroll) exceed the entire Veterans department by 6×. Total city payroll grew from $1.80B to $2.46B (+37%).

### Crime — 80% of shootings in 4 neighborhoods
**80% of all Boston shootings (2018–2025) are concentrated in just 4 neighborhoods** — Dorchester, Roxbury, Mattapan, and Jamaica Plain. 80% of victims are Black. Massachusetts is #2 safest state for homicide (1.9/100K). Boston accounts for 19% of state violent crime with only 9% of population. 2025: 31 homicides (up 36% from historic 2024 low of 24). Shootings down 30% from 5-year average.

### Education — 0/12 achievement points
BPS earned **0 out of 12** achievement points at the high school level — every subject declined. Trails the state by 11–20 percentage points across every MCAS subject. 26.3% chronic absenteeism in K-8. Graduation rate fell to 79.7%. Spending ~$27K per pupil.

### ICE — 5,100+ arrests despite sanctuary city
5,100+ administrative arrests in Boston AOR (Jan–Oct 2025), roughly **3× year-over-year** increase despite sanctuary city policies. Operation Patriot 2.0: 1,400+ arrests in September alone. Brazil is the top nationality (~25%).

### Commercial RE — 18.2% vacancy, 31–62% distressed discounts
Boston office vacancy hit **18.2%** (from <8% pre-COVID). Distressed sales closing at 31–62% discounts. Commercial property assessments **declined for the first time in FY2026** (−$800M), shifting tax burden to residential homeowners. CMBS office delinquency at 11.3%.

## Methodology & Data Integrity

- All ACFR department names are **verbatim** from the Schedule of Expenditures Compared to Budget (Budgetary Basis), including the city's own "Transparancy" misspelling
- All dollar amounts are **actual expenditures** (not budgeted, not appropriated — what was spent)
- FY2019 figures are sourced from prior-year comparative columns in the FY2020 ACFR
- "—" in tables means the department did not exist or had zero General Fund expenditure that year
- Office of New Bostonians is tracked separately and not included in DEI totals
- Payroll data is from official City of Boston Employee Earnings Reports published on data.boston.gov

## Data Sources

| Source | What | Access |
|--------|------|--------|
| City of Boston ACFRs | Budget expenditures FY2019–FY2025 | boston.gov |
| data.boston.gov | Employee earnings reports CY2019–CY2025 | data.boston.gov |
| FBI Crime Data Explorer | UCR/NIBRS crime statistics | cde.ucr.cjis.gov |
| Mass.gov EOPSS | State crime press releases | mass.gov |
| Boston Police Dept | Crime stats, shooting data by neighborhood | police.boston.gov |
| MA DESE | MCAS results, accountability | profiles.doe.mass.edu |
| ICE ERO Boston | Administrative arrest statistics | ice.gov |
| UC Berkeley | Deportation Data Project | law.berkeley.edu |
| Cushman & Wakefield | Office vacancy, MarketBeat | cushmanwakefield.com |
| Trepp | CMBS delinquency data | trepp.com |
| Boston Assessing Dept | Property assessment FY2016–FY2026 | boston.gov/assessing |

## Repository Structure

```
All-Things-Boston/
├── index.html                      ← Main 8-tab dashboard (36 charts)
├── boston-payroll-interactive.html  ← Interactive dot visualization (embedded in Payroll tab)
├── education-boston.html            ← Full 7-tab BPS deep dive (20+ charts)
├── data/                           ← Static chart images, source CSVs
├── README.md
```

## Related

- [Massachusetts Data Hub](https://duncanburns2013-dot.github.io/Massachusetts-Data-Hub/) — Statewide dashboards
- [BPS Education Deep Dive](https://duncanburns2013-dot.github.io/All-Things-Boston/education-boston.html) — Full 7-tab BPS analysis

## Deployment

GitHub Pages: Settings → Pages → Deploy from branch: **main** / **root**

---

*Data compiled May 2026 · All data from official government sources · Corrections applied May 14, 2026 after page-by-page ACFR verification*
