# Implementation notes: paper → code mapping

This file maps the key concepts from the LEACH and APTEEN papers to locations in the codebase, lists current gaps, and proposes short next steps.

## Files of interest

- `router/leach/leach.py`  : LEACH implementation (cluster-head selection, `threshold()`, cluster formation, steady-state aggregation).
- `router/apteen.py`      : APTEEN prototype (periodic reports, event-driven reporting with hard/soft thresholds, per-node `_last_sample` state).
- `router/node.py`       : `Node` energy model (TX/RX amplifier models, `singlecast`, `broadcast`, `is_alive`).
- `router/router.py`     : `Router` base class, plotting utilities, `SimpleRouter` example.
- `distribution.py`      : topology generators (`power_line_naive`, `uniform_in_square`, `uniform_in_circle`).
- `compare_leach_and_apteen.py` : experiment runner, headless plotting, trials averaging, JSON output.

## How paper concepts map to code

- Cluster-head (CH) selection — `router/leach/leach.py`:
  - `threshold()` implements the probabilistic threshold used to elect CHs.
  - CH rotation protection window logic is implemented in `non_head_protection()`.

- Cluster formation / Join — `router/leach/leach.py`:
  - Members choose nearest CH and set route to the CH. Aggregation performed at CH.

- Data aggregation and steady-state — `router/leach/leach.py`:
  - `steady_state_phase()` handles member-to-CH and CH-to-sink transmissions and energy accounting.

- APTEEN periodic + event-driven behavior — `router/apteen.py`:
  - `period` parameter triggers full reports every `period` rounds.
  - `hard_threshold` and `soft_threshold` + `soft_delta` implement event reporting logic; `min_report_interval` protects from frequent reports.

- Energy model — `router/node.py`:
  - `energy_tx()` uses free-space vs multipath thresholds, `energy_rx()` subtracts RX cost.

## Known issues and gaps

- LEACH `non_head_protection` logic appears to use `r % int(1/p)` where canonical LEACH uses a fixed epoch window `1/p` to ensure each node is CH once per epoch. This can cause incorrect rotation behavior.
- APTEEN prototype: `soft_threshold` comparison uses last sample vs last reported value in code? Confirm and, if necessary, change to compare with last *reported* value as per paper.
- Tests: there are no unit tests verifying CH rotation fairness, cluster sizes, or per-round metrics (CH count, messages). Add small tests/metrics collectors.

## Recommended next steps (short list)

1. Fix LEACH rotation protection: make `non_head_protection` use a fixed epoch length `int(1/p)` instead of `r % int(1/p)` (small, high-impact).
2. Verify APTEEN soft-threshold logic: ensure soft threshold compares to last *reported* value, not last sample.
3. Add per-round metrics to runner: CH count, cluster sizes, bytes transmitted; include them in JSON output.
4. Add small unit/integration tests for CH rotation and energy accounting (use `n_sensor=10` smoke fixtures).
5. Optionally add `--verbose` flag to `compare_leach_and_apteen.py` to toggle detailed logging.

## Where to look when changing code

- To change CH rotation: edit `router/leach/leach.py` and re-run `compare_leach_and_apteen.py` smoke tests.
- To change APTEEN thresholds: edit `router/apteen.py` and run `test_apteen.py`.
- To extend runner metrics: edit `compare_leach_and_apteen.py` to collect and persist additional arrays per trial.

---

Generated: automated notes created by the code inspection run.
