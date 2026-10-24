We count {desert_pop} Boston residents in pharmacy deserts. The Boston Globe reported
about {globe_pop} ({globe_date}). We did not tune our method to match.

Why the numbers differ:

- **Different rule.** The Globe counted areas where a drugstore is at least a half-mile
  away and most people do not have a car. We use the state's rule ({hpc_report}): less
  than {area_pct} of a block group's area within walking distance. That can flag a
  place where many people own cars.
- **Half-mile limit applies widely.** The state uses the half-mile limit when a block
  group has below-average car ownership or high poverty. In Boston that is
  {low_access_share} of block groups.
- **Closures since then.** Every Rite Aid in the state has closed, and so has the
  Codman Square Walgreens. Our store list removes them.
- **Different store list.** OpenStreetMap misses some independent pharmacies. Where it
  does, our desert count is too high, not too low.

Sources: Boston Globe ({globe_date}); Tufts University School of Medicine summary
({tufts_date}); Massachusetts Health Policy Commission, {hpc_report}.
