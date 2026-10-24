# Context notes

## Decisions
- Use block groups + the HPC 15%-area rule, not a grid. A flat-mile grid over 5
  counties flagged most of the inner city as desert and was thrown away.
- Pull pharmacies from the 5 counties around Boston so stores just across the city
  line (Brookline, Cambridge, Quincy) count toward Boston coverage.
- "Below-average vehicle ownership" read as: no-car household share above the Boston
  average (B25044). Poverty: B17017 below-poverty households / total > 20%.
- Closed stores are removed if an OSM pharmacy sits within 60 m of the closure point.
  Codman Square Walgreens was still in OSM and was removed. Morton St and Gallivan Blvd
  Walgreens were already absent.
- Ranking counts a block group under a store only if it goes from not-desert to desert
  when that one store closes. Each near-desert block group has exactly one such store,
  so the ranking sums to the near-desert population (tested).
- Census keys need a minute to activate; the first call returned an HTML page.

## Numbers (2026-10-24, state rule, Codman closed)
- Desert 132,087 (23.1%), near-desert 158,214 (27.7%), covered 280,891 (49.2%).
- 1 mile for everyone: 44,432 in deserts. Globe 2024: ~15,000. Gap not yet explained.
- 19 of 270 stores carry all near-desert residents. Top: CVS 42.3088,-71.0818 (24,080).

## Open
- Why we're far above the Globe: likely the 0.5 mi low-access rule (271 of 462 block
  groups qualify), OSM gaps, and newer closures. Write this before tuning anything.
