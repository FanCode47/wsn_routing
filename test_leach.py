import argparse
import matplotlib.pyplot as plt
import os
from datetime import datetime
import numpy as np

try:
    import imageio.v2 as imageio
except ImportError:  # optional dependency
    imageio = None

try:
    from PIL import Image
except ImportError:
    Image = None

from distribution import *
from router import LEACH
from locale_pl import t


def parse_args():
    parser = argparse.ArgumentParser(description="Run LEACH simulation with snapshot/topology outputs")
    parser.add_argument("--nodes", type=int, default=100, help="Number of sensor nodes (default: 100)")
    parser.add_argument("--area", type=float, default=200.0, help="Square area side length for node placement (default: 200.0)")
    parser.add_argument("--width", type=float, default=None, help="Area width (overrides --area if specified)")
    parser.add_argument("--height", type=float, default=None, help="Area height (overrides --area if specified)")
    parser.add_argument("--initial-energy", type=float, default=0.5, help="Initial energy per node in Joules (default: 0.5)")
    parser.add_argument("--max-rounds", type=int, default=None, help="Maximum rounds to run (None = run until all nodes die)")
    parser.add_argument("--output-dir", type=str, default=None, help="Output folder (if not specified, auto-generates Results/run_YYYYMMDD_HHMMSS)")
    parser.add_argument("--snapshot-step", type=int, default=int(os.environ.get("SNAPSHOT_STEP", "10")), help="Save alive-nodes plot every N rounds (0 disables, default: 10)")
    parser.add_argument("--topo-step", type=int, default=int(os.environ.get("TOPO_STEP", "10")), help="Save topology every N rounds (0 disables, default: 10)")
    parser.add_argument("--snapshot-gif", dest="snapshot_gif", action="store_true", help="Create GIF from alive-nodes snapshots")
    parser.add_argument("--no-snapshot-gif", dest="snapshot_gif", action="store_false", help="Disable GIF from alive-nodes snapshots")
    parser.add_argument("--topo-gif", dest="topo_gif", action="store_true", help="Create GIF from topology snapshots")
    parser.add_argument("--no-topo-gif", dest="topo_gif", action="store_false", help="Disable GIF from topology snapshots")
    parser.add_argument("--backend", type=str, default=None, help="Matplotlib backend (default: Agg)")
    parser.add_argument("--show", action="store_true", help="Show plots interactively during simulation")
    parser.add_argument("--language", type=str, default="eng", choices=["eng", "pl"], help="Interface language (default: eng)")
    parser.set_defaults(snapshot_gif=None, topo_gif=None)
    return parser.parse_args()


def run_leach(
    args,
    backend: str | None = None,
    show: bool = False,
):
    """Run LEACH test with optional snapshot/topology/GIF generation"""
    # Apply environment variable defaults for GIF generation
    env_snapshot_gif = os.environ.get("SNAPSHOT_GIF", "1") == "1"
    env_topo_gif = os.environ.get("TOPO_GIF", "1") == "1"
    
    # Use environment defaults if command-line args are None
    if args.snapshot_gif is None:
        args.snapshot_gif = env_snapshot_gif
    if args.topo_gif is None:
        args.topo_gif = env_topo_gif
    
    # Don't show windows, save to files instead
    plt.switch_backend(backend or 'Agg')

    # Create results folder with timestamp
    if args.output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = f"Results/run_{timestamp}"
    else:
        results_dir = args.output_dir
    os.makedirs(results_dir, exist_ok=True)
    print(t("results_saved", args.language, results_dir))

    snapshots_dir = os.path.join(results_dir, "snapshots")
    topology_dir = os.path.join(results_dir, "topology")
    os.makedirs(snapshots_dir, exist_ok=True)
    os.makedirs(topology_dir, exist_ok=True)

    # Determine area dimensions
    if args.width is not None and args.height is not None:
        from distribution import uniform_in_rectangle
        area_width, area_height = args.width, args.height
        distribution = uniform_in_rectangle(area_width, area_height, args.nodes, (0, 0), "left-bottem")
    else:
        from distribution import uniform_in_square
        area_width = area_height = args.area
        distribution = uniform_in_square(args.area, args.nodes, (0, 0), "left-bottem")
    
    # Set initial energy if specified
    from router import Node
    if args.initial_energy != 0.5:
        Node.default_energy_max = args.initial_energy

    sink = (0, 0)
    nodes = simple_loader(sink, distribution)

    # leach = LEACH(*nodes_on_power_line_naive(), n_cluster=5)
    leach = LEACH(*nodes, n_cluster=6)
    leach.initialize()
    initial_nodes = len(leach.alive_non_sinks)
    # Guarantee at least one frame when a positive step is requested
    snapshot_step = 0 if args.snapshot_step <= 0 else max(1, min(args.snapshot_step, initial_nodes))
    topo_step = 0 if args.topo_step <= 0 else max(1, min(args.topo_step, initial_nodes))
    n_alive = []
    snapshot_paths = []
    topo_paths = []
    while len(leach.alive_non_sinks) > 0 and (args.max_rounds is None or len(n_alive) < args.max_rounds):
        leach.execute()
        n = len(leach.alive_non_sinks)
        n_alive.append(n)

        round_idx = len(n_alive)
        if snapshot_step > 0 and round_idx % snapshot_step == 0:
            fig, ax = plt.subplots()
            rounds = list(range(len(n_alive)))
            ax.plot(rounds, n_alive)
            if rounds:
                x_end = rounds[-1] + (rounds[-1] - rounds[0]) / 5 if len(rounds) > 1 else rounds[0] + 1
                ax.set_xlim([rounds[0], x_end])
                ax.set_ylim([0, max(n_alive) + 5])
            ax.set_xlabel(t("round", args.language))
            ax.set_ylabel(t("alive_nodes", args.language))
            snap_path = f"{snapshots_dir}/test_leach_step_{round_idx}.png"
            fig.savefig(snap_path, dpi=300, bbox_inches='tight')
            if show:
                plt.show(block=False)
                plt.pause(0.1)
            plt.close(fig)
            print(t("snapshot_saved", args.language, snap_path))
            snapshot_paths.append(snap_path)

        if topo_step > 0 and round_idx % topo_step == 0:
            topo_path = f"{topology_dir}/topology_leach_{round_idx}.png"
            leach.plot(save_path=topo_path, show=show)
            if not show:
                plt.close(leach.plotter.fig)
            else:
                plt.pause(0.1)
            print(t("topology_saved", args.language, topo_path))
            topo_paths.append(topo_path)

        print(t("cluster_heads", args.language, len(leach.clusters)))
        print(t("nodes_alive", args.language, n))
    print("")
    rounds = list(range(len(n_alive)))
    fig, ax = plt.subplots()
    ax.plot(rounds, n_alive)
    if rounds:
        x_end = rounds[-1] + (rounds[-1] - rounds[0]) / 5 if len(rounds) > 1 else rounds[0] + 1
        ax.set_xlim([rounds[0], x_end])
        ax.set_ylim([0, max(n_alive) + 5])
    ax.set_xlabel(t("round", args.language))
    ax.set_ylabel(t("alive_nodes", args.language))
    plot_path = f"{results_dir}/test_leach.png"
    fig.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(t("plot_saved", args.language, plot_path))

    if args.snapshot_gif and snapshot_paths:
        if imageio is None:
            print("SNAPSHOT_GIF=1 set but imageio is not installed; skipping GIF export.")
        else:
            gif_path = f"{results_dir}/test_leach.gif"
            try:
                frames = []
                target_size = None
                for p in snapshot_paths:
                    arr = imageio.imread(p)
                    if arr.ndim == 2:  # grayscale
                        arr = np.stack([arr] * 3, axis=-1)
                    if arr.shape[2] == 3:  # no alpha
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
                print(t("gif_saved", args.language, gif_path))
            except Exception as exc:
                print(t("gif_failed", args.language, exc))

    if args.topo_gif and topo_paths:
        if imageio is None:
            print(t("imageio_missing_topo", args.language))
        else:
            gif_path = f"{results_dir}/topology_leach.gif"
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
                print(t("topology_gif_saved", args.language, gif_path))
            except Exception as exc:
                print(t("topology_gif_failed", args.language, exc))


if __name__ == "__main__":
    args = parse_args()
    run_leach(
        args,
        backend=args.backend,
        show=args.show,
    )
