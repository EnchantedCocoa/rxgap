We count {desert_pop} residents in pharmacy deserts. The state (Health Policy
Commission) counted {hpc_pop} with pharmacy licenses from {hpc_date}. We did not tune our
method to match.

Why the numbers differ:

- **Different store lists.** The state uses pharmacy license records. We use every
  pharmacy we could find in OpenStreetMap and the federal NPI list, each checked on the web
  for being open today, with a source link. Licenses can keep a closed store listed until
  they run out; our web checks can miss a store with no web presence.
- **Closures since the state's count.** Every Rite Aid in the state has closed since then.
- **Same rule, same blocks as the state.** For {hpc_agree} of residents, we and the
  state give the same status.

Sources: Massachusetts Health Policy Commission, {hpc_report} and its public block-group
dataset.
