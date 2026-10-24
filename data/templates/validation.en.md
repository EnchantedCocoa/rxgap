We count {desert_pop} Boston residents in pharmacy deserts. The state (Health Policy
Commission) counted {hpc_pop} with pharmacy licenses from {hpc_date}. The Boston Globe
reported about {globe_pop} ({globe_date}). We did not tune our method to match either.

Why the numbers differ:

- **Closures since the state's count.** Every Rite Aid in the state has closed, and so
  have the Walgreens stores at Codman Square and Gallivan Blvd. Our store list removes
  them.
- **Different store lists.** We start from OpenStreetMap and add {added_stores} pharmacies
  it was missing (mostly health-center and grocery pharmacies), each checked on the web
  with a source link. The state uses license records, which can keep a closed store
  listed until its license runs out.
- **Same rule, same blocks as the state.** For {hpc_agree} of Boston residents, we and
  the state give the same status.
- **The Globe used a different rule.** It counted areas where a drugstore is at least a
  half-mile away and most people do not have a car. The state's rule ({hpc_report}) uses
  the share of a block group's area within reach and a half-mile limit for
  {low_access_share} of Boston block groups.

Sources: Boston Globe ({globe_date}); Massachusetts Health Policy Commission,
{hpc_report} and its public block-group dataset.
