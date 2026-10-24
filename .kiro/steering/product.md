---
inclusion: always
---
# RxGap

When a pharmacy closes in Boston, RxGap shows which block groups just lost walkable
access and who lives there (65+, no car, limited English); ranks the pharmacies the
city can't afford to lose; gives each affected council member and state legislator a
one-page brief with the best replacement sites; and helps residents write to their
own representatives.

Pitch: when a neighborhood's pharmacy closes, people stop taking their heart medicine.

Users: city councilors and state legislators, community health centers, MassHealth
plan care teams, residents.
Hackathon challenge: Civic action, V2 ("who an alert misses") and community readiness.
MIT libraries to use: osmnx, rapidfuzz, duckdb, folium, pulp.

## Method (cite on screen)
Massachusetts Health Policy Commission, DataPoints 31 (Oct 2025).
- A block group is a **desert** when less than 15% of its area is within the walk
  limit of a pharmacy.
- Walk limit: 1 mile; 0.5 mile for **low-access** block groups (no-car share above the
  Boston average, or more than 20% of households below poverty).
- **Near-desert**: covered, but losing one specific pharmacy makes it a desert.
- Scope today: Boston only, urban distances only. Suburban 2 mi / rural are out.

## Rules
- Every number in a brief or letter is inserted by code. Model-written text comes from
  fixed templates and never types a number.
- The app never sends anything on a resident's behalf. It says it is an AI tool built
  at Hackachusetts, not the City of Boston.
- Every number on screen has a "how we got this" link (function, dataset, pull date).
- Don't tune the method to hit the Boston Globe's ~15,000 estimate. Explain the gap.
- OpenStreetMap pharmacies are a floor, not the truth. Show the source label.
