import os
import time
import json
import argparse
from pathlib import Path

# Decide backend before importing pyplot
def select_backend(mode: str | None = None):
    import matplotlib
    if mode is None or mode == "auto":
        # if no DISPLAY, force Agg
        if os.environ.get("DISPLAY") is None:
            matplotlib.use("Agg")
    elif mode in ("agg", "headless"):
        matplotlib.use("Agg")
    # else leave default (interactive) - user's environment decides


def main():
    parser = argparse.ArgumentParser(description="Compare LEACH and APTEEN (headless-friendly)")
    parser.add_argument("--backend", choices=["auto", "agg", "interactive"], default="auto",
                        help="matplotlib backend selection; 'auto' forces Agg when DISPLAY is missing")
    parser.add_argument("--outdir", default="results", help="directory to store outputs (png/json)")
    parser.add_argument("--n-sensor", type=int, default=100, help="number of sensors to generate (for quick tests)")
    parser.add_argument("--trials", type=int, default=3, help="number of independent trials to run and average")
    parser.add_argument("--seed-start", type=int, default=0, help="start seed (seeds will be seed-start .. seed-start+trials-1)")
    parser.add_argument("--save-runs", action="store_true", help="save per-trial JSON files in outdir/runs/")
    args = parser.parse_args()

    select_backend(args.backend)

    import matplotlib.pyplot as plt

    from distribution import simple_loader, uniform_in_circle
    from router import APTEEN, LEACH

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    sink = (0, 0)
    distribution = uniform_in_circle(200, args.n_sensor, sink)
    n_cluster = 6

    nodes_leach = simple_loader(sink, distribution)
    leach = LEACH(*nodes_leach, n_cluster=n_cluster)
    nodes_apteen = simple_loader(sink, distribution)
    apteen = APTEEN(*nodes_apteen, n_cluster=n_cluster)

    # Run trials
    trials = max(1, int(args.trials))
    seed_start = int(args.seed_start)
    per_run = {
        "leach": [],
        "apteen": [],
    }
    # metrics: per-round arrays collected for each trial
    per_run_metrics = {
        "leach": {
            "ch_count": [],
            "avg_cluster_size": [],
            "total_energy": [],
        },
        "apteen": {
            "ch_count": [],
            "avg_cluster_size": [],
            "total_energy": [],
        },
    }
    durations = []

    import random as pyrandom
    import numpy as _np

    for t in range(trials):
        seed = seed_start + t
        pyrandom.seed(seed)
        _np.random.seed(seed)

        # generate fresh distributions/nodes per trial
        distribution = uniform_in_circle(200, args.n_sensor, sink)

        nodes_leach = simple_loader(sink, distribution)
        leach = LEACH(*nodes_leach, n_cluster=n_cluster)
        nodes_apteen = simple_loader(sink, distribution)
        apteen = APTEEN(*nodes_apteen, n_cluster=n_cluster)

        t0 = time.time()

        # run LEACH
        leach.initialize()
        alive_leach = []
        leach_ch = []
        leach_cluster_size = []
        leach_energy = []
        while (n := len(leach.alive_non_sinks)) > 0:
            alive_leach.append(n)
            leach.execute()
            # collect metrics for this round
            heads = list(leach.get_cluster_heads())
            ch_count = len(heads)
            member_counts = [len(list(leach.get_cluster_members(h))) for h in heads] if ch_count > 0 else []
            avg_size = float(sum(member_counts) / len(member_counts)) if member_counts else 0.0
            total_energy = sum(node.energy for node in leach.non_sinks)
            leach_ch.append(ch_count)
            leach_cluster_size.append(avg_size)
            leach_energy.append(total_energy)

        # run APTEEN
        apteen.initialize()
        alive_apteen = []
        apteen_ch = []
        apteen_cluster_size = []
        apteen_energy = []
        while (n := len(apteen.alive_non_sinks)) > 0:
            alive_apteen.append(n)
            apteen.execute()
            heads = list(apteen.get_cluster_heads())
            ch_count = len(heads)
            member_counts = [len(list(apteen.get_cluster_members(h))) for h in heads] if ch_count > 0 else []
            avg_size = float(sum(member_counts) / len(member_counts)) if member_counts else 0.0
            total_energy = sum(node.energy for node in apteen.non_sinks)
            apteen_ch.append(ch_count)
            apteen_cluster_size.append(avg_size)
            apteen_energy.append(total_energy)

        dt = time.time() - t0
        durations.append(dt)

        per_run["leach"].append(alive_leach)
        per_run["apteen"].append(alive_apteen)
        per_run_metrics["leach"]["ch_count"].append(leach_ch)
        per_run_metrics["leach"]["avg_cluster_size"].append(leach_cluster_size)
        per_run_metrics["leach"]["total_energy"].append(leach_energy)
        per_run_metrics["apteen"]["ch_count"].append(apteen_ch)
        per_run_metrics["apteen"]["avg_cluster_size"].append(apteen_cluster_size)
        per_run_metrics["apteen"]["total_energy"].append(apteen_energy)

        if args.save_runs:
            run_dir = outdir / "runs"
            run_dir.mkdir(parents=True, exist_ok=True)
            run_json = run_dir / f"run_{t}_results.json"
            with open(run_json, "w") as f:
                json.dump({
                    "seed": seed,
                    "alive_leach": alive_leach,
                    "alive_apteen": alive_apteen,
                    "duration_s": dt,
                }, f)

        print(f"trial {t+1}/{trials} seed={seed}: LEACH rounds={len(alive_leach)}, APTEEN rounds={len(alive_apteen)}, dt={dt:.2f}s")

    # aggregate results: pad sequences to max length and compute mean/std
    import numpy as np

    def pad_and_stack(list_of_lists):
        max_len = max(len(x) for x in list_of_lists)
        arr = np.zeros((len(list_of_lists), max_len), dtype=float)
        for i, x in enumerate(list_of_lists):
            arr[i, :len(x)] = x
        return arr

    leach_stack = pad_and_stack(per_run["leach"])
    apteen_stack = pad_and_stack(per_run["apteen"])

    leach_mean = leach_stack.mean(axis=0).tolist()
    leach_std = leach_stack.std(axis=0).tolist()
    apteen_mean = apteen_stack.mean(axis=0).tolist()
    apteen_std = apteen_stack.std(axis=0).tolist()

    # aggregate metrics (ch_count, avg_cluster_size, total_energy)
    def agg_metric(metric_name: str, proto: str):
        stack = pad_and_stack(per_run_metrics[proto][metric_name])
        return stack.mean(axis=0).tolist(), stack.std(axis=0).tolist()

    leach_ch_mean, leach_ch_std = agg_metric("ch_count", "leach")
    leach_cluster_size_mean, leach_cluster_size_std = agg_metric("avg_cluster_size", "leach")
    leach_energy_mean, leach_energy_std = agg_metric("total_energy", "leach")

    apteen_ch_mean, apteen_ch_std = agg_metric("ch_count", "apteen")
    apteen_cluster_size_mean, apteen_cluster_size_std = agg_metric("avg_cluster_size", "apteen")
    apteen_energy_mean, apteen_energy_std = agg_metric("total_energy", "apteen")

    duration = sum(durations)

    # Plot aggregated mean +- std
    styles = ["science", "ieee", "grid"]
    avail = plt.style.available
    use_styles = [s for s in styles if s in avail]
    if not use_styles:
        use_styles = ["default"]

    with plt.style.context(use_styles):
        fig, ax = plt.subplots()
        x_leach = list(range(len(leach_mean)))
        x_apteen = list(range(len(apteen_mean)))
        ax.plot(x_leach, leach_mean, label="LEACH mean")
        ax.fill_between(x_leach, np.array(leach_mean) - np.array(leach_std), np.array(leach_mean) + np.array(leach_std), alpha=0.2)
        ax.plot(x_apteen, apteen_mean, label="APTEEN mean")
        ax.fill_between(x_apteen, np.array(apteen_mean) - np.array(apteen_std), np.array(apteen_mean) + np.array(apteen_std), alpha=0.2)
        ax.legend(title="protocols")
        ax.set(xlabel="Round")
        ax.set(ylabel="Number of nodes alive")
        ax.autoscale()
        png_path = outdir / "alive_nodes_compare_mean.png"
        fig.savefig(str(png_path), dpi=200)

    # Structured JSON log
    result = {
        "timestamp": time.time(),
        "duration_s": duration,
        "n_sensors": args.n_sensor,
        "n_cluster": n_cluster,
        "trials": trials,
        "seed_start": seed_start,
        "leach_mean": leach_mean,
        "leach_std": leach_std,
        "apteen_mean": apteen_mean,
        "apteen_std": apteen_std,
        "leach_ch_mean": leach_ch_mean,
        "leach_ch_std": leach_ch_std,
        "leach_cluster_size_mean": leach_cluster_size_mean,
        "leach_cluster_size_std": leach_cluster_size_std,
        "leach_energy_mean": leach_energy_mean,
        "leach_energy_std": leach_energy_std,
        "apteen_ch_mean": apteen_ch_mean,
        "apteen_ch_std": apteen_ch_std,
        "apteen_cluster_size_mean": apteen_cluster_size_mean,
        "apteen_cluster_size_std": apteen_cluster_size_std,
        "apteen_energy_mean": apteen_energy_mean,
        "apteen_energy_std": apteen_energy_std,
        "backend": plt.get_backend(),
    }
    json_path = outdir / "compare_results_aggregated.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)

    # Minimal console output
    print(f"Saved aggregated plot: {png_path}")
    print(f"Saved aggregated JSON results: {json_path}")
    print(f"Total runtime for all trials: {duration:.1f}s")


if __name__ == "__main__":
    main()
