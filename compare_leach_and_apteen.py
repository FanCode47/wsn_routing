import os
from datetime import datetime

import matplotlib.pyplot as plt

from distribution import *
from router import APTEEN, LEACH


def run_compare(output_dir: str | None = None, backend: str = "Agg"):
    """Compare LEACH vs APTEEN lifetimes and save plot to output_dir."""
    plt.switch_backend(backend)

    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"Results/run_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Results will be saved to: {output_dir}")

    main(output_dir=output_dir)


def main(output_dir: str | None = None):
    sink = (0, 0)
    # distribution = uniform_in_square(150, 100, sink, "left-bottem")
    # distribution = power_line_naive(4, 375, 0, 0, 25, 40, sink)
    distribution = uniform_in_circle(200, 100, sink)
    n_cluster = 6

    nodes_leach = simple_loader(sink, distribution)
    leach = LEACH(*nodes_leach, n_cluster=n_cluster)
    nodes_apteen = simple_loader(sink, distribution)
    apteen = APTEEN(*nodes_apteen, n_cluster=n_cluster)

    leach.initialize()
    alive_leach = []
    while (n := len(leach.alive_non_sinks)) > 0:
        alive_leach.append(n)
        leach.execute()

    apteen.initialize()
    alive_apteen = []
    while (n := len(apteen.alive_non_sinks)) > 0:
        alive_apteen.append(n)
        apteen.execute()

    try:
        plt.style.use(["science", "ieee", "grid"])
    except OSError:
        plt.style.use('default')
        plt.rcParams['axes.grid'] = True
    
    fig, ax = plt.subplots()
    ax.plot(list(range(len(alive_leach))), alive_leach, label="LEACH")
    ax.plot(list(range(len(alive_apteen))), alive_apteen, label="APTEEN")

    ax.legend(title="protocols")
    ax.set(xlabel="Round")
    ax.set(ylabel="Number of nodes alive")
    ax.autoscale()

    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"Results/run_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    plot_path = f"{output_dir}/compare_leach_apteen.png"
    fig.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {plot_path}")


if __name__ == "__main__":
    run_compare()
