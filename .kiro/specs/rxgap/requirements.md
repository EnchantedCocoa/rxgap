# Requirements Document

## Introduction

RxGap shows, for Boston, which census block groups lose walkable pharmacy access when a
store closes, who lives there, which stores the city can't afford to lose, and what each
affected official can do. Residents can draft a letter to their own representatives.

Scope: Boston only, urban distances only. Method: Massachusetts Health Policy Commission,
DataPoints 31 (Oct 2025). Distances and areas in EPSG:26986.

Status: APPROVED 2026-10-24. Requirements 1–2 already have working code
(`scripts/analyze_bg.py`, `scripts/rank.py`).

## Glossary

- **Walk limit**: 1 mile, or 0.5 mile for a low-access block group.
- **Low-access**: no-car household share above the state average, or more than 20% of
  households below poverty (ACS 2022 B25044, B17017).
- **Desert**: less than 15% of the block group's area is within the walk limit of an open pharmacy.
- **Near-desert**: not a desert, but removing one specific pharmacy makes it a desert.
- **Covered**: neither.

## Requirements

### Requirement 1: Coverage

**User Story:** As an official, I want each block group's pharmacy status, so that I can see where access is thin.

#### Acceptance Criteria
1. THE SYSTEM SHALL compute each Boston block group's covered-area share and status (desert, near-desert, covered).
2. WHEN a Census key is missing or rejected THE SYSTEM SHALL use "income below the Boston median" as the low-access rule AND say so on screen.
3. THE SYSTEM SHALL count pharmacies outside the Boston line that are within the walk limit of a Boston block group.

### Requirement 2: Can't-afford-to-lose ranking

**User Story:** As an official, I want the stores ranked by harm if they close, so that I can act before a closure.

#### Acceptance Criteria
1. FOR each pharmacy THE SYSTEM SHALL count residents of block groups that would become deserts if it closed, with 65+ and no-car household counts.
2. THE SYSTEM SHALL recompute only block groups within that pharmacy's walk limit.
3. THE SYSTEM SHALL show the top 20 with name, address and neighborhoods.
4. THE SYSTEM SHALL pass a test that the ranked residents sum to the near-desert population.

### Requirement 3: Closure simulation

**User Story:** As an official, I want to mark a store closed and see who lost access, so that I can respond the same day.

#### Acceptance Criteria
1. WHEN a store is marked closed (button, or a row in `data/manual/closures.csv`) THE SYSTEM SHALL recompute coverage within 5 seconds.
2. THE SYSTEM SHALL list newly-desert block groups with population, 65+, households without a car, and limited-English share.
3. THE SYSTEM SHALL list the three nearest remaining pharmacies per block group with walking times from a cached osmnx walking graph.

### Requirement 4: Official routing and brief

**User Story:** As a councilor or legislator, I want a one-page brief for my district, so that I know who lost access and what would fix it.

#### Acceptance Criteria
1. THE SYSTEM SHALL map each newly-desert block group to its Boston City Council district and state House and Senate districts.
2. THE SYSTEM SHALL produce one brief per affected official with the numbers from Requirement 3 and the sites from Requirement 5.
3. THE SYSTEM SHALL show letter counts by district (Requirement 7) in the brief.

### Requirement 5: Replacement siting

**User Story:** As an official, I want the best replacement sites, so that my request is specific.

#### Acceptance Criteria
1. THE SYSTEM SHALL rank the top 3 candidate sites (community health centers, MBTA rapid transit stations, `data/manual/candidate_sites.csv`) by cut-off residents brought back within the walk limit, using a coverage model in PuLP.
2. THE SYSTEM SHALL show the math behind each rank.
3. IF the optimizer is cut THE SYSTEM SHALL use the nearest health center instead.

### Requirement 6: Resident letter

**User Story:** As a resident, I want a letter to my own representatives in my language, so that I can ask for the fix.

#### Acceptance Criteria
1. WHEN a resident enters an address THE SYSTEM SHALL confirm their officials.
2. THE SYSTEM SHALL draft a short letter in Spanish or Haitian Creole (Portuguese, Chinese, Vietnamese if time allows) with an English copy.
3. THE SYSTEM SHALL require one sentence written by the resident and use the siting result as the request.
4. THE SYSTEM SHALL NOT send letters.

### Requirement 7: Letter counts

1. THE SYSTEM SHALL store letter counts by district without names or addresses.

### Requirement 8: Number integrity

1. A test SHALL fail if any number in a brief or letter differs from the analysis output.

### Requirement 9: Validation line

1. THE SYSTEM SHALL compare Boston's desert population with the Boston Globe's estimate of about 15,000 (2024) and explain the difference on screen, without tuning the method to match.

### Requirement 10: Daily check

1. `python -m rxgap.check` SHALL recompute from `closures.csv` and print a summary of block groups that changed status, so a scheduler can run it daily.

### Requirement 11: Reproducible headline

1. `scripts/verify_numbers.py` SHALL recompute the headline numbers from raw files.

### Requirement 12: Provenance

1. Every number on screen SHALL have a "how we got this" link (function or query, dataset, pull date).
