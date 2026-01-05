"""
APTEEN parameter impact visualization.

Shows for each configuration:
- Time to FIRST node death.
- Time to COMPLETE network death.
- Degradation period (complete - first).

Charts:
Top row: alive nodes (with first-death marker), transmissions (first 1000 rounds), energy.
Bottom row: stacked lifetime bars (first death + degradation), total transmissions, average transmissions per round.
"""

import argparse
import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
try:
    import imageio.v2 as imageio
except ImportError:
    imageio = None
try:
    from PIL import Image
except ImportError:
    Image = None
from router import APTEEN
from distribution import simple_loader, uniform_in_square


def slugify(name: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in name)
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe.strip("_") or "config"


# -------------------- simulation helpers --------------------
def create_data_generator(base_event_round=10):
    """Synthetic sensor generator with a step event after base_event_round."""
    def generator(node, round_id):
        base = 30.0 + (node.position[0] + node.position[1]) / 10
        event = 30.0 if round_id >= base_event_round else 0.0
        noise = np.random.normal(0, 3)
        return max(0.0, base + event + noise)

    return generator


def run_simulation(
    config_name,
    hard_threshold,
    soft_threshold,
    count_time,
    per_cluster_params=None,
    n_sensor=30,
    area_size=100.0,
    sink=(0.0, 0.0),
    topology_dir: str | None = None,
    topo_step: int = 0,
    topo_gif: bool = False,
    config_tag: str | None = None,
):
    """Run one simulation until all nodes die; track first and complete death rounds, optionally saving topology snapshots/GIF."""
    np.random.seed(42)
    nodes = simple_loader(sink, uniform_in_square(area_size, n_sensor, sink))
    initial_node_count = len(nodes[1])

    apteen = APTEEN(
        *nodes,
        n_cluster=5,
        hard_threshold=hard_threshold,
        soft_threshold=soft_threshold,
        count_time=count_time,
        data_generator=create_data_generator(base_event_round=15),
    )

    apteen.initialize()

    effective_topo_step = 0
    if topo_gif and topo_step <= 0:
        effective_topo_step = 1
    elif topo_step > 0:
        effective_topo_step = max(1, topo_step)

    topo_paths = []
    topo_prefix = config_tag or slugify(config_name)
    if topology_dir and effective_topo_step > 0:
        os.makedirs(topology_dir, exist_ok=True)
        init_path = os.path.join(topology_dir, f"{topo_prefix}_topology_{0:04d}.png")
        apteen.plot(show=False)
        # Override axis bounds to match requested area_size
        half_area = area_size / 2
        apteen.plotter.set_bound(sink[0] - half_area, sink[1] - half_area, sink[0] + half_area, sink[1] + half_area)
        apteen.plotter.fig.savefig(init_path, dpi=150, bbox_inches='tight')
        plt.close(apteen.plotter.fig)
        topo_paths.append(init_path)

    # Optional per-cluster parameters
    if per_cluster_params:
        apteen.set_up_phase()
        cluster_heads = [h for h in apteen.get_cluster_heads() if h != apteen.sink]
        for i, (ht, st, tc) in enumerate(per_cluster_params):
            if i < len(cluster_heads):
                apteen.set_cluster_parameters(cluster_heads[i], ht, st, tc)

    metrics = {"rounds": [], "alive": [], "transmissions": [], "energy": []}

    round_num = 0
    first_death_round = None

    # Run until all non-sink nodes die
    while len(apteen.alive_non_sinks) > 0:
        if first_death_round is None and len(apteen.alive_non_sinks) < initial_node_count:
            first_death_round = round_num

        apteen.execute()

        transmissions = sum(
            1
            for node in apteen.alive_non_sinks
            if node in apteen.last_transmission and apteen.rounds_since_transmission[node] == 0
        )
        avg_energy = (
            np.mean([n.energy for n in apteen.alive_non_sinks]) if apteen.alive_non_sinks else 0.0
        )

        metrics["rounds"].append(round_num)
        metrics["alive"].append(len(apteen.alive_non_sinks))
        metrics["transmissions"].append(transmissions)
        metrics["energy"].append(avg_energy)

        if topology_dir and effective_topo_step > 0 and round_num % effective_topo_step == 0:
            topo_path = os.path.join(topology_dir, f"{topo_prefix}_topology_{round_num:04d}.png")
            apteen.plot(show=False)
            # Override axis bounds to match requested area_size
            half_area = area_size / 2
            apteen.plotter.set_bound(sink[0] - half_area, sink[1] - half_area, sink[0] + half_area, sink[1] + half_area)
            apteen.plotter.fig.savefig(topo_path, dpi=150, bbox_inches='tight')
            plt.close(apteen.plotter.fig)
            topo_paths.append(topo_path)

        round_num += 1

    if first_death_round is None:
        first_death_round = round_num - 1

    complete_death_round = round_num

    if topo_gif and topo_paths:
        if imageio is None:
            print(f"[WARN] TOPO_GIF requested but imageio not installed; skipping GIF for {config_name}.")
        else:
            gif_path = os.path.join(topology_dir or ".", f"{topo_prefix}_topology.gif")
            try:
                frames = []
                target_size = None
                for p in topo_paths:
                    arr = imageio.imread(p)
                    if arr.ndim == 2:
                        arr = np.stack([arr] * 3, axis=-1)
                    if arr.shape[2] == 3:
                        alpha = 255 * np.ones_like(arr[..., :1])
                        arr = np.concatenate([arr, alpha], axis=-1)
                    if target_size is None:
                        target_size = arr.shape[:2]
                    elif arr.shape[:2] != target_size and Image is not None:
                        arr = np.array(Image.fromarray(arr).resize((target_size[1], target_size[0])))
                        if arr.ndim == 2:
                            arr = np.stack([arr] * 3, axis=-1)
                        if arr.shape[2] == 3:
                            alpha = 255 * np.ones_like(arr[..., :1])
                            arr = np.concatenate([arr, alpha], axis=-1)
                    frames.append(arr)
                imageio.mimsave(gif_path, frames, duration=0.2)
                print(f"Topology GIF saved to {gif_path}")
            except Exception as exc:
                print(f"Failed to create topology GIF for {config_name}: {exc}")

    return metrics, first_death_round, complete_death_round, topo_paths


# -------------------- visualization --------------------
def visualize_comparison(
    n_sensor=30,
    area_size=100.0,
    sink=(0.0, 0.0),
    output_dir: str | None = None,
    show: bool = True,
    topo_step: int = 0,
    topo_gif: bool = False,
    backend: str | None = None,
):
    """Run six presets and plot comparison in English without emojis; optionally save topology snapshots/GIFs per preset."""

    if not show:
        plt.switch_backend(backend or "Agg")

    print(
        f"Running six APTEEN presets (nodes={n_sensor}, area={area_size}x{area_size})"
        " (until full network death)...\n"
    )

    topo_root = None
    if topo_step > 0 or topo_gif:
        base_dir = output_dir if output_dir else "."
        topo_root = os.path.join(base_dir, "topology")
        os.makedirs(topo_root, exist_ok=True)

    def run_config(label, hard, soft, tc, per_cluster_params=None, color="blue"):
        config_tag = slugify(label)
        config_topo_dir = os.path.join(topo_root, config_tag) if topo_root else None
        metrics, first, total, topo_paths = run_simulation(
            label,
            hard,
            soft,
            tc,
            per_cluster_params=per_cluster_params,
            n_sensor=n_sensor,
            area_size=area_size,
            sink=sink,
            topology_dir=config_topo_dir,
            topo_step=topo_step,
            topo_gif=topo_gif,
            config_tag=config_tag,
        )
        return (label, metrics, first, total, color, topo_paths)

    print("[1/6] LEACH-like (HT=0.1, ST=0.1, TC=1)...")
    m1 = run_config("LEACH-like", 0.1, 0.1, 1, color="orange")
    print(f"      first={m1[2]}, complete={m1[3]}, degradation={m1[3] - m1[2]}")

    print("[2/6] TEEN-like (HT=50, ST=3, TC=1000)...")
    m2 = run_config("TEEN-like", 50.0, 3.0, 1000, color="brown")
    print(f"      first={m2[2]}, complete={m2[3]}, degradation={m2[3] - m2[2]}")

    print("[3/6] Conservative (HT=70, ST=5, TC=20)...")
    m3 = run_config("Conservative", 70.0, 5.0, 20, color="blue")
    print(f"      first={m3[2]}, complete={m3[3]}, degradation={m3[3] - m3[2]}")

    print("[4/6] Aggressive (HT=40, ST=1, TC=5)...")
    m4 = run_config("Aggressive", 40.0, 1.0, 5, color="red")
    print(f"      first={m4[2]}, complete={m4[3]}, degradation={m4[3] - m4[2]}")

    print("[5/6] Balanced (HT=50, ST=2, TC=10)...")
    m5 = run_config("Balanced", 50.0, 2.0, 10, color="green")
    print(f"      first={m5[2]}, complete={m5[3]}, degradation={m5[3] - m5[2]}")

    print("[6/6] Adaptive per-cluster...")
    m6 = run_config(
        "Adaptive",
        50.0,
        2.0,
        10,
        per_cluster_params=[
            (40.0, 1.0, 5),
            (70.0, 5.0, 20),
            (50.0, 2.0, 10),
            (60.0, 3.0, 15),
            (45.0, 1.5, 8),
        ],
        color="purple",
    )
    print(f"      first={m6[2]}, complete={m6[3]}, degradation={m6[3] - m6[2]}\n")

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle("APTEEN parameter impact: first death vs complete death", fontsize=14, fontweight="bold")

    configs = [
        ("LEACH-like (0.1/0.1/1)", m1[1], m1[2], m1[3], m1[4]),
        ("TEEN-like (50/3/1000)", m2[1], m2[2], m2[3], m2[4]),
        ("Conservative (70/5/20)", m3[1], m3[2], m3[3], m3[4]),
        ("Aggressive (40/1/5)", m4[1], m4[2], m4[3], m4[4]),
        ("Balanced (50/2/10)", m5[1], m5[2], m5[3], m5[4]),
        ("Adaptive per-cluster", m6[1], m6[2], m6[3], m6[4]),
    ]

    # 1) Alive nodes with first-death markers
    ax = axes[0, 0]
    for name, metrics, first, total, color in configs:
        ax.plot(metrics["rounds"], metrics["alive"], label=name, linewidth=2.0, color=color, alpha=0.85)
        ax.axvline(x=first, color=color, linestyle=":", alpha=0.5, linewidth=2)
    ax.set_xlabel("Round", fontweight="bold")
    ax.set_ylabel("Alive nodes", fontweight="bold")
    ax.set_title("Alive nodes (dotted = first death)", fontweight="bold")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(True, alpha=0.3)

    # 2) Transmissions (first 1000 rounds for readability)
    ax = axes[0, 1]
    for name, metrics, first, total, color in configs:
        limit = min(1000, len(metrics["rounds"]))
        ax.plot(metrics["rounds"][:limit], metrics["transmissions"][:limit], label=name, linewidth=1.6, color=color, alpha=0.7)
    ax.set_xlabel("Round", fontweight="bold")
    ax.set_ylabel("Transmissions per round", fontweight="bold")
    ax.set_title("Transmission activity (first 1000 rounds)", fontweight="bold")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(True, alpha=0.3)
    ax.axvline(x=15, color="black", linestyle="--", alpha=0.25, linewidth=1)
    ax.text(16, ax.get_ylim()[1] * 0.92, "Event", fontsize=8, color="black")

    # 3) Energy consumption with first-death markers
    ax = axes[0, 2]
    for name, metrics, first, total, color in configs:
        ax.plot(metrics["rounds"], metrics["energy"], label=name, linewidth=2.0, color=color, alpha=0.85)
        if first < len(metrics["energy"]):
            ax.axvline(x=first, color=color, linestyle=":", alpha=0.5, linewidth=2)
    ax.set_xlabel("Round", fontweight="bold")
    ax.set_ylabel("Average energy (J)", fontweight="bold")
    ax.set_title("Energy (steeper = faster drain)", fontweight="bold")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(True, alpha=0.3)

    # 4) Stacked bar: first death + degradation (complete = darker + faded)
    ax = axes[1, 0]
    names_short = [n for n, _, _, _, _ in configs]
    firsts = [f for _, _, f, _, _ in configs]
    totals = [t for _, _, _, t, _ in configs]
    colors = [c for _, _, _, _, c in configs]

    bars_first = ax.barh(range(len(names_short)), firsts, color=colors, alpha=0.85, label="First death")
    bars_deg = ax.barh(
        range(len(names_short)),
        [t - f for f, t in zip(firsts, totals)],
        left=firsts,
        color=colors,
        alpha=0.35,
        label="Degradation",
    )

    ax.set_yticks(range(len(names_short)))
    ax.set_yticklabels(names_short, fontsize=9)
    ax.set_xlabel("Rounds", fontweight="bold")
    ax.set_title("Network lifetime: solid=to first death, faded=degradation", fontweight="bold")
    ax.grid(True, alpha=0.3, axis="x")
    ax.legend(fontsize=8, loc="lower right")

    for bar_f, bar_d, first, total in zip(bars_first, bars_deg, firsts, totals):
        ax.text(first * 0.02, bar_f.get_y() + bar_f.get_height() / 2, f"{first}", va="center", ha="left", fontsize=8)
        ax.text(total + max(totals) * 0.01, bar_d.get_y() + bar_d.get_height() / 2, f"{total}", va="center", ha="left", fontsize=8)

    # 5) Total transmissions (per configuration)
    ax = axes[1, 1]
    total_tx = [sum(m["transmissions"]) for _, m, _, _, _ in configs]
    bars = ax.bar(range(len(names_short)), total_tx, color=colors, alpha=0.75)
    ax.set_xticks(range(len(names_short)))
    ax.set_xticklabels(names_short, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Total transmissions", fontweight="bold")
    ax.set_title("Total transmissions over lifetime", fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")
    for bar, val in zip(bars, total_tx):
        ax.text(bar.get_x() + bar.get_width() / 2, val, str(int(val)), ha="center", va="bottom", fontsize=8)

    # 6) Average transmissions per round
    ax = axes[1, 2]
    avg_tx = [sum(m["transmissions"]) / t if t else 0.0 for _, m, _, t, _ in configs]
    bars = ax.bar(range(len(names_short)), avg_tx, color=colors, alpha=0.75)
    ax.set_xticks(range(len(names_short)))
    ax.set_xticklabels(names_short, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Transmissions per round", fontweight="bold")
    ax.set_title("Average transmission intensity", fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")
    for bar, val in zip(bars, avg_tx):
        ax.text(bar.get_x() + bar.get_width() / 2, val, f"{val:.2f}", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        save_path = os.path.join(output_dir, "apteen_parameters_comparison.png")
    else:
        save_path = "apteen_parameters_comparison.png"

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"Saved figure: {save_path}")

    if show:
        plt.show()

    # Textual summary
    print("\nSummary (rounds):")
    print("Name                      First   Complete   Degradation   Total TX   TX/round")
    print("-" * 78)
    for name, metrics, first, total, _ in configs:
        total_tx_sum = sum(metrics["transmissions"])
        tx_per_round = total_tx_sum / total if total else 0.0
        print(f"{name:25s} {first:6d} {total:10d} {total - first:12d} {total_tx_sum:10d} {tx_per_round:9.2f}")

    print("\nHow to read the energy chart (top right):")
    print("- X axis: round; Y axis: average energy of alive nodes (J).")
    print("- Steeper downward slope = faster energy drain = earlier deaths.")
    print("- Dotted vertical line marks the first node death for that curve.")


# -------------------- entry point --------------------
def main():
    parser = argparse.ArgumentParser(description="APTEEN visualization")
    parser.add_argument(
        "--nodes",
        type=int,
        default=30,
        help="Number of sensor nodes (default: 30)",
    )
    parser.add_argument(
        "--area",
        type=float,
        default=100.0,
        help="Square area side length for node placement (default: 100.0)",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=None,
        help="Maximum rounds per simulation (None = run until all nodes die)",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default="Results/params_run",
        help="Output directory for figures (date suffix auto-appended)",
    )
    parser.add_argument("--no-show", action="store_true", help="Skip showing the plot window")
    parser.add_argument("--show", action="store_false", dest="no_show", help="Show the plot window")
    parser.add_argument("--topo-step", type=int, default=int(os.environ.get("TOPO_STEP", "50")), help="Save topology snapshots every N rounds (0=disabled, default: 50)")
    parser.add_argument("--topo-gif", dest="topo_gif", action="store_true", help="Export topology GIF per preset (implies snapshots)")
    parser.add_argument("--no-topo-gif", dest="topo_gif", action="store_false", help="Disable topology GIF export")
    parser.add_argument("--backend", type=str, default=None, help="Matplotlib backend (default: Agg)")
    parser.set_defaults(no_show=True, topo_gif=os.environ.get("TOPO_GIF", "1") == "1")
    args = parser.parse_args()

    final_outdir = None
    if args.outdir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_outdir = f"{args.outdir}_{timestamp}"

    visualize_comparison(
        n_sensor=args.nodes,
        area_size=args.area,
        output_dir=final_outdir,
        show=not args.no_show,
        topo_step=args.topo_step,
        topo_gif=args.topo_gif,
        backend=args.backend,
    )


if __name__ == "__main__":
    main()
