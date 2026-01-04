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


def parse_args():
    parser = argparse.ArgumentParser(description="Run LEACH simulation with snapshot/topology outputs")
    parser.add_argument("--snapshot-step", type=int, default=int(os.environ.get("SNAPSHOT_STEP", "0")), help="Save alive-nodes plot every N rounds (0 disables)")
    parser.add_argument("--topo-step", type=int, default=int(os.environ.get("TOPO_STEP", "0")), help="Save topology every N rounds (0 disables)")
    parser.add_argument("--snapshot-gif", action="store_true", default=os.environ.get("SNAPSHOT_GIF", "0") == "1", help="Create GIF from alive-nodes snapshots")
    parser.add_argument("--topo-gif", action="store_true", default=os.environ.get("TOPO_GIF", "0") == "1", help="Create GIF from topology snapshots")
    return parser.parse_args()


def test_leach(args):
    # Don't show windows, save to files instead
    plt.switch_backend('Agg')

    # Create results folder with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"Results/run_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    print(f"Results will be saved to: {results_dir}")

    snapshots_dir = os.path.join(results_dir, "snapshots")
    topology_dir = os.path.join(results_dir, "topology")
    os.makedirs(snapshots_dir, exist_ok=True)
    os.makedirs(topology_dir, exist_ok=True)

    sink = (0, 0)
    nodes = simple_loader(
        sink,
        uniform_in_square(200, 100, sink, "left-bottem")
    )

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
    while len(leach.alive_non_sinks) > 0:
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
            ax.set_xlabel("round")
            ax.set_ylabel("number of alive nodes")
            snap_path = f"{snapshots_dir}/test_leach_step_{round_idx}.png"
            fig.savefig(snap_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            print(f"Snapshot saved to {snap_path}")
            snapshot_paths.append(snap_path)

        if topo_step > 0 and round_idx % topo_step == 0:
            topo_path = f"{topology_dir}/topology_leach_{round_idx}.png"
            leach.plot(save_path=topo_path, show=False)
            # close figure created inside Router.plot
            plt.close(leach.plotter.fig)
            print(f"Topology snapshot saved to {topo_path}")
            topo_paths.append(topo_path)

        # print(
        #     {leach.index(head): [leach.index(n) for n in members] for head, members in leach.clusters.items()}
        # )
        print(f"cluster heads: {len(leach.clusters)}")
        print(f"nodes alive: {n}")
        # print(leach.route)
        # leach.plot()
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
    plot_path = f"{results_dir}/test_leach.png"
    fig.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved to {plot_path}")

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
                print(f"GIF saved to {gif_path}")
            except Exception as exc:
                print(f"Failed to create GIF: {exc}")

    if args.topo_gif and topo_paths:
        if imageio is None:
            print("TOPO_GIF=1 set but imageio is not installed; skipping GIF export.")
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
                print(f"Topology GIF saved to {gif_path}")
            except Exception as exc:
                print(f"Failed to create topology GIF: {exc}")


if __name__ == "__main__":
    args = parse_args()
    test_leach(args)
