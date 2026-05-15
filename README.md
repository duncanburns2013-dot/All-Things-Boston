# All Things Boston

City government accountability dashboard — **10 tabs, 50+ interactive charts**, all sourced from official government data.

**Live:** https://duncanburns2013-dot.github.io/All-Things-Boston/

---

## 📊 Dashboard Tabs

| Tab | Charts | Topic | Key Source(s) |
|-----|--------|-------|---------------|
| Budget | 5 | Veterans vs. DEI/equity spending FY2019–FY2025 | City of Boston ACFRs |
| DEI Breakdown | 3 | All 14 departments created/expanded under Wu | City of Boston ACFRs |
| Payroll | 4 | Headcount & earnings by department CY2019–CY2025 | data.boston.gov Employee Earnings |
| Crime | 8 | Shooting geography, demographics, FBI rates | FBI UCR, BPD, Mass.gov EOPSS |
| Education | 6 | BPS MCAS, achievement gaps, absenteeism | DESE/MCAS 2025 |
| ICE | 4 | Boston AOR arrests, operations, nationalities | ICE ERO, UC Berkeley, Globe |
| Commercial RE | 14 | 7-section deep-dive: vacancy → CMBS → tax impact | C&W, Trepp, Colliers, Boston Assessing, MLS PIN |
| Housing | 6 | Residential sale prices, rent, inventory 2018–2026 | MLS PIN |
| 311 Services | 7 | Service equity gap by neighborhood | data.boston.gov 311 open dataset |
| Pension/OPEB | 6 | Funded ratio, unfunded liability, peer comparison | Boston Retirement System, ACFRs |

---

## Key Findings

### Budget
Veterans Services flatlined at **$2.5M–$3.3M** since FY2019 while combined DEI/equity departments went from $548K to **$28.5M** — a **52× increase**. Every year Veterans is budgeted ~$4.7M then slashed nearly in half before spending occurs. The Office of New Bostonians grew 785% ($412K → $3.6M). All figures are General Fund actual expenditures verified page-by-page from ACFRs.

### DEI Breakdown
14+ new departments created or expanded under Wu, organized into Tier 1 (identity/equity offices with no service-delivery mission) and Tier 2 (equity-adjacent with operational functions). The Office of Workforce Development and Office of Economic Opportunity & Inclusion each debuted at $6.5M in FY2025 — two new departments, one year, $13M combined. All department names and dollar amounts are verbatim from ACFR expenditure schedules.

### Payroll
DEI-adjacent headcount: **46 → 429 employees** (CY2019→CY2025). Boston Police **lost 177 officers** (3,271→3,094) over the same period. Veterans department stuck at 12–17 staff throughout. BPS Inclusion positions alone (220 staff, $19.8M) cost more than 6× the entire Veterans department.

### Crime
**80% of all Boston shootings concentrated in 4 neighborhoods** — Dorchester, Roxbury, Mattapan, Jamaica Plain. 80% of homicide victims are Black. Massachusetts is the #2 safest state for homicide nationally (1.9/100K). Boston accounts for 19% of state violent crime with only 9% of state population. Robbery rate is 3.4× the national average; homicide is below national average. 2025 homicides: 31 (+36% from historic 2024 low of 24, still second-lowest in two decades).

### Education
BPS earned **0 of 12 achievement points** at the high school level — every subject declined. Trails the state by 11–20 percentage points across every MCAS subject. 26.3% chronic absenteeism in K-8. Graduation rate fell to 79.7%. Spending ~$27K per pupil, among the highest in the country.

### ICE
5,100+ administrative arrests in Boston AOR (Jan–Oct 2025), roughly 3× year-over-year despite sanctuary city policies. Operation Patriot (May 2025): 1,461 arrests. Operation Patriot 2.0 (Sep 2025): 1,400+. Top nationality: Brazil (~25%).

### Commercial Real Estate *(7-section deep-dive)*
Office vacancy hit **18.5% in Q1 2026** (from <8% pre-COVID) — a 147% increase. After two quarters of stabilization in H2 2025, vacancy ticked back up 30 bps QoQ. Distressed sales closing at 31–62% discounts from prior value. CMBS office delinquency at **11.01%** — historic high. Commercial property assessments declined **−0.6% in FY2026**, first drop in a decade, shifting tax burden to residential homeowners. MLS PIN commercial supply: 67.6 months (balanced = 6–9 months). Bank CRE lending down 58% vs. pre-pandemic.

### Housing
Boston residential average single-family price up 55% since 2018 ($813K → $1.26M) but volume down 19%. Condo months supply hit **5.58** — approaching balanced market (6.0) for the first time since 2019. Average rent $3,781/month, up 29% since 2018. Condo inventory nearly doubled since 2022.

### 311 Services *(new)*
The same 4 neighborhoods absorbing 80% of Boston's shootings also wait **3–4× longer** for basic 311 services. Mattapan average resolution time: 11.2 days. Back Bay: 3.1 days. Rodent complaints up 62% since 2019. 31% of graffiti requests and 28% of streetlight requests sit unresolved past 30 days. The city spends $28.5M on equity offices while service delivery to minority neighborhoods is measurably slower — sourced from data.boston.gov 311 open dataset.

### Pension/OPEB *(new)*
Boston Retirement System is **85.8% funded** (FY2025) — better than Chicago (48.5%), Philadelphia (47.3%), and NYC (71.2%). But the unfunded pension liability is still **$1.3B**, and OPEB (retiree health benefits) carries a **$2.1B actuarial liability with zero trust assets** — pure pay-as-you-go. Combined shortfall: **$3.4 billion** — 119× the DEI budget, 1,030× the Veterans budget. Annual pension payment alone ($484M) exceeds 10% of the total city budget.

---

## Data Sources

| Dataset | Publisher | Update Frequency |
|---------|-----------|-----------------|
| Annual Comprehensive Financial Reports | City of Boston | Annually |
| Employee Earnings Report | data.boston.gov | Annually |
| 311 Service Requests | data.boston.gov | Daily (open dataset) |
| Boston Retirement System Actuarial Valuations | Boston Retirement Board | Annually |
| FBI Uniform Crime Report / UCR | FBI Crime Data Explorer | Annually |
| MCAS Results | MA DESE | Annually |
| ICE ERO Enforcement Data | ICE / UC Berkeley | Monthly |
| Office Market Reports | Cushman & Wakefield, Colliers, Newmark | Quarterly |
| CMBS Delinquency | Trepp | Monthly |
| Property Assessments | Boston Assessing Dept | Annually |
| Residential Market Review | MLS PIN | Monthly |

---

## Methodology Notes

- **Budget figures** are General Fund *actual expenditures* on a budgetary basis, not appropriations. Source: Schedule of Expenditures Compared to Budget in each ACFR.
- **DEI tier definitions**: Tier 1 = departments whose primary stated mission is equity/identity with no independent service-delivery function. Tier 2 = departments with operational missions but explicit equity framing. All department names copied verbatim from ACFR expenditure schedules.
- **311 resolution times** are calendar days from ticket open to ticket closed, as recorded in the open dataset. Neighborhood assignment uses BPD neighborhood boundaries.
- **Pension funded ratio** uses the actuarial (smoothed) asset value per Boston Retirement System annual valuations. Assumed return: 7.0%.
- **OPEB liability** per GASB 75 actuarial basis. No OPEB trust fund has been established as of FY2025.
- **CRE vacancy** figures vary by brokerage due to differing definitions of "availability" vs. "vacancy" and submarket boundaries.

---

## Related Dashboards

| Dashboard | Topic |
|-----------|-------|
| [Massachusetts Data Hub](https://duncanburns2013-dot.github.io/Massachusetts-Data-Hub/) | Energy costs, pension, healthcare, employment — statewide |
| [commercial-re-dashboard.html](commercial-re-dashboard.html) | Standalone CRE deep-dive (also embedded in Commercial RE tab) |

---

*Data compiled May 2026 · All figures from official government sources · See individual chart source notes for specific citations*
