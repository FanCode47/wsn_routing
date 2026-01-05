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
from router import APTEEN


def parse_args():
    parser = argparse.ArgumentParser(description="Run APTEEN simulation with snapshot/topology outputs")
    parser.add_argument("--nodes", type=int, default=100, help="Number of sensor nodes (default: 100)")
    parser.add_argument("--area", type=float, default=100.0, help="Square area side length for node placement (default: 100.0)")
    parser.add_argument("--max-rounds", type=int, default=None, help="Maximum rounds to run (None = run until all nodes die)")
    parser.add_argument("--output-dir", type=str, default=None, help="Output folder (if not specified, auto-generates Results/run_YYYYMMDD_HHMMSS)")
    parser.add_argument("--snapshot-step", type=int, default=None, help="Save alive-nodes plot every N rounds (0 disables; default from env SNAPSHOT_STEP)")
    parser.add_argument("--topo-step", type=int, default=None, help="Save topology every N rounds (0 disables; default from env TOPO_STEP)")
    parser.add_argument("--snapshot-gif", dest="snapshot_gif", action="store_true", help="Create GIF from alive-nodes snapshots")
    parser.add_argument("--no-snapshot-gif", dest="snapshot_gif", action="store_false", help="Disable GIF from alive-nodes snapshots")
    parser.add_argument("--topo-gif", dest="topo_gif", action="store_true", help="Create GIF from topology snapshots")
    parser.add_argument("--no-topo-gif", dest="topo_gif", action="store_false", help="Disable GIF from topology snapshots")
    parser.add_argument("--backend", type=str, default=None, help="Matplotlib backend (default: Agg)")
    parser.set_defaults(snapshot_gif=None, topo_gif=None)
    return parser.parse_args()


def run_apteen(
    nodes: int = 100,
    area: float = 100.0,
    max_rounds: int | None = None,
    output_dir: str | None = None,
    snapshot_step: int | None = None,
    topo_step: int | None = None,
    snapshot_gif: bool | None = None,
    topo_gif: bool | None = None,
    backend: str | None = None,
):
    """Run APTEEN test with optional snapshot/topology/GIF generation."""
    plt.switch_backend(backend or "Agg")

    env_snapshot_step = int(os.environ.get("SNAPSHOT_STEP", "10"))
    env_topo_step = int(os.environ.get("TOPO_STEP", "10"))
    env_snapshot_gif = os.environ.get("SNAPSHOT_GIF", "1") == "1"
    env_topo_gif = os.environ.get("TOPO_GIF", "1") == "1"

    snapshot_step = env_snapshot_step if snapshot_step is None else snapshot_step
    topo_step = env_topo_step if topo_step is None else topo_step
    snapshot_gif = env_snapshot_gif if snapshot_gif is None else snapshot_gif
    topo_gif = env_topo_gif if topo_gif is None else topo_gif

    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"Results/run_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    snapshots_dir = os.path.join(output_dir, "snapshots")
    topology_dir = os.path.join(output_dir, "topology")
    os.makedirs(snapshots_dir, exist_ok=True)
    os.makedirs(topology_dir, exist_ok=True)
    print(f"Results will be saved to: {output_dir}")

    sink = (0, 0)
    sensor_nodes = simple_loader(
        sink,
        uniform_in_square(area, nodes, sink)
    )

    apteen = APTEEN(*sensor_nodes, n_cluster=5)
    apteen.initialize()
    initial_nodes = len(apteen.alive_non_sinks)
    # Guarantee at least one frame when a positive step is requested
    effective_snapshot_step = 0 if snapshot_step <= 0 else max(1, min(snapshot_step, initial_nodes))
    effective_topo_step = 0 if topo_step <= 0 else max(1, min(topo_step, initial_nodes))
    n_alive = []
    snapshot_paths = []
    topo_paths = []
    while len(apteen.alive_non_sinks) > 0 and (max_rounds is None or len(n_alive) < max_rounds):
        apteen.execute()
        n = len(apteen.alive_non_sinks)
        n_alive.append(n)

        round_idx = len(n_alive)
        if effective_snapshot_step > 0 and round_idx % effective_snapshot_step == 0:
            fig, ax = plt.subplots()
            rounds = list(range(len(n_alive)))
            ax.plot(rounds, n_alive)
            if rounds:
                x_end = rounds[-1] + (rounds[-1] - rounds[0]) / 5 if len(rounds) > 1 else rounds[0] + 1
                ax.set_xlim([rounds[0], x_end])
                ax.set_ylim([0, max(n_alive) + 5])
            ax.set_xlabel("round")
            ax.set_ylabel("number of alive nodes")
            snap_path = f"{snapshots_dir}/test_apteen_step_{round_idx}.png"
            fig.savefig(snap_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            print(f"Snapshot saved to {snap_path}")
            snapshot_paths.append(snap_path)

        if effective_topo_step > 0 and round_idx % effective_topo_step == 0:
            topo_path = f"{topology_dir}/topology_apteen_{round_idx}.png"
            apteen.plot(save_path=topo_path, show=False)
            plt.close(apteen.plotter.fig)
            print(f"Topology snapshot saved to {topo_path}")
            topo_paths.append(topo_path)

        print(f"cluster heads: {len(apteen.clusters)}")
        print(f"nodes alive: {n}")
    print("")
    rounds = list(range(len(n_alive)))
    fig, ax = plt.subplots()
    ax.plot(rounds, n_alive)
    if rounds:
        x_end = rounds[-1] + (rounds[-1] - rounds[0]) / 5 if len(rounds) > 1 else rounds[0] + 1
        ax.set_xlim([rounds[0], x_end])
        ax.set_ylim([0, max(n_alive) + 5])
    ax.set_xlabel("round")
    ax.set_ylabel("number of alive nodes")
    plot_path = f"{output_dir}/test_apteen.png"
    fig.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved to {plot_path}")

    if snapshot_gif and snapshot_paths:
        if imageio is None:
            print("SNAPSHOT_GIF=1 set but imageio is not installed; skipping GIF export.")
        else:
            gif_path = f"{output_dir}/test_apteen.gif"
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
                print(f"GIF saved to {gif_path}")
            except Exception as exc:
                print(f"Failed to create GIF: {exc}")

    if topo_gif and topo_paths:
        if imageio is None:
            print("TOPO_GIF=1 set but imageio is not installed; skipping GIF export.")
        else:
            gif_path = f"{output_dir}/topology_apteen.gif"
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
                print(f"Failed to create topology GIF: {exc}")


if __name__ == "__main__":
    args = parse_args()
    run_apteen(
        nodes=args.nodes,
        area=args.area,
        max_rounds=args.max_rounds,
        output_dir=args.output_dir,
        snapshot_step=args.snapshot_step,
        topo_step=args.topo_step,
        snapshot_gif=args.snapshot_gif,
        topo_gif=args.topo_gif,
        backend=args.backend,
    )
