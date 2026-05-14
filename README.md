# All Things Boston

City government accountability dashboard — 8 tabs, 36 interactive charts, all sourced from official government data.

**Live Site:** https://duncanburns2013-dot.github.io/All-Things-Boston/

---

## 📊 Dashboard Tabs

| Tab | Charts | Topic | Sources |
|-----|--------|-------|---------|
| Budget | 5 | Veterans vs DEI/equity spending FY2019–FY2025 | City of Boston ACFRs |
| DEI Breakdown | 3 | All 14+ new departments created under Wu | City of Boston ACFRs |
| Payroll | 4 | Employee headcount & earnings by department | data.boston.gov Employee Earnings |
| Crime | 8 | Neighborhood concentration, demographics, FBI data | FBI UCR, BPD, Mass.gov EOPSS, Vera |
| Education | 6 | BPS MCAS performance, achievement gaps | DESE/MCAS 2025 |
| ICE | 4 | Boston AOR arrests, operations, demographics | ICE ERO, UC Berkeley, Globe |
| Commercial RE | 6 | Office vacancy, CMBS, distressed sales, tax shift | C&W, Trepp, Colliers, Boston Assessing |
| Housing | — | Boston residential (placeholder, links to Data Hub) | Warren Group, MLS PIN |

## Key Findings

### Budget
Veterans Services flatlined at $2.5M–$3.3M since FY2019 while combined DEI/equity departments went from $548K to $22.3M — a **40× increase**. Every year Veterans is budgeted ~$4.7M then slashed nearly in half. The Office of Workforce Development alone ($6.5M in FY25) is roughly double Veterans' entire budget. The Office of New Bostonians grew 785% ($412K → $3.6M).

### Payroll
DEI-adjacent headcount went from **46 employees to 429** (CY2019→CY2025) while Boston Police **lost 177 officers** (3,271→3,094). Veterans stuck at 12–17 employees the entire time. BPS Inclusion positions alone (220 staff, $19.8M payroll) cost more than 6× the Veterans department. Total city payroll grew from $1.80B to $2.46B (+37%).

### Crime
**80% of all Boston shootings (2018–2025) are concentrated in just 4 neighborhoods** — Dorchester, Roxbury, Mattapan, and Jamaica Plain. 80% of victims are Black. Massachusetts is #2 safest state for homicide (1.9/100K). Boston accounts for 19% of state violent crime with only 9% of population. 2025 saw 31 homicides (up 36% from historic 2024 low of 24, but still second-lowest in two decades). Shootings down 30% from 5-year average.

### Education
BPS earned **0 out of 12** achievement points at the high school level — every subject declined. Trails the state by 11–20 percentage points across every MCAS subject. 26.3% chronic absenteeism in K-8. Graduation rate fell to 79.7%. Spending ~$27K per pupil.

### ICE
5,100+ administrative arrests in Boston AOR (Jan–Oct 2025), roughly **3× year-over-year** increase despite sanctuary city policies. Operation Patriot 2.0 alone accounted for 1,400+ arrests in September. Brazil is the top nationality at ~25% of arrests.

### Commercial RE
Boston office vacancy hit **18.2%** (up from <8% pre-COVID). Distressed sales closing at 31–62% discounts from prior values. Commercial property assessments **declined for the first time in FY2026** (−$800M), shifting tax burden to residential homeowners. CMBS office delinquency at 11.3% — far above every other property type. New leasing activity up 72% in 2025 but not enough to reverse the trend.

## The Through Line

Each tab tells its own story. Together they ask a harder question: the city spends $22M on equity offices and $34M in DEI payroll while Veterans gets $1.2M and police lose 177 officers. 80% of gun violence is packed into 4 predominantly non-white neighborhoods — the same communities these equity departments claim to serve. BPS is failing across every metric despite $27K per pupil. Office buildings are losing 60% of their value, which will crush the tax base and push costs onto homeowners. And ICE is making 5,100 arrests despite sanctuary city policies.

**Priorities vs. outcomes.**

## Data Sources

| Source | What | URL |
|--------|------|-----|
| City of Boston ACFRs | Budget expenditures FY2019–FY2025 | boston.gov |
| data.boston.gov | Employee earnings reports CY2019–CY2025 | data.boston.gov |
| FBI Crime Data Explorer | UCR/NIBRS crime statistics | cde.ucr.cjis.gov |
| Mass.gov EOPSS | State crime press releases | mass.gov |
| Boston Police Dept | Weekly crime stats, shooting data | police.boston.gov |
| Vera Institute | Neighborhood shooting concentration | vera.org |
| MA DESE | MCAS results, accountability | profiles.doe.mass.edu |
| ICE ERO Boston | Administrative arrest statistics | ice.gov |
| UC Berkeley | Deportation Data Project | law.berkeley.edu |
| Cushman & Wakefield | Office vacancy, MarketBeat | cushmanwakefield.com |
| Trepp | CMBS delinquency data | trepp.com |
| Boston Assessing Dept | Property assessment data FY2016–FY2026 | boston.gov/assessing |
| Warren Group / MLS PIN | Residential housing data | thewarrengroup.com |

## Repository Structure

```
All-Things-Boston/
├── index.html              ← Main 8-tab dashboard (36 charts)
├── education-boston.html    ← Full 7-tab BPS deep dive
├── data/                   ← Static chart images, CSVs
├── README.md
```

## Related

- [Massachusetts Data Hub](https://duncanburns2013-dot.github.io/Massachusetts-Data-Hub/) — Statewide dashboards (housing, immigration, education, affordability, energy, commercial RE)
- [BPS Education Deep Dive](https://duncanburns2013-dot.github.io/All-Things-Boston/education-boston.html) — Full 7-tab BPS analysis with 20+ charts

## Deployment

GitHub Pages: Settings → Pages → Deploy from branch: **main** / **root**

---

*Data compiled May 2026 · All data from official government sources*
