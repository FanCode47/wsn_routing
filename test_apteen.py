import matplotlib.pyplot as plt

from distribution import *
from router import APTEEN


def test_apteen():
    sink = (0, 0)
    # reduce sensors for a quick debug run and set progress interval
    progress_interval = 5
    nodes = simple_loader(
        sink,
        uniform_in_square(100, 20, sink)
    )

    # apteen = LEACH(*nodes_on_power_line_naive(), n_cluster=5)
    apteen = APTEEN(*nodes, n_cluster=5)
    apteen.initialize()
    n_alive = []
    while len(apteen.alive_non_sinks) > 0:
        apteen.execute()
        n = len(apteen.alive_non_sinks)
        n_alive.append(n)
        # print progress every N rounds
        if len(n_alive) % progress_interval == 0:
            print(f"round {len(n_alive)}: alive_non_sinks = {n}")

        # print(
        #     {apteen.index(head): [apteen.index(n) for n in members] for head, members in apteen.clusters.items()}
        # )
        # print(f"cluster heads: {len(apteen.clusters)}")
        # print(f"nodes alive: {n}")
        # print(apteen.route)
        apteen.plot()
    print("")
    rounds = list(range(len(n_alive)))
    plt.plot(rounds, n_alive)
    plt.xlim([rounds[0], rounds[-1] + (rounds[-1] - rounds[0]) / 5])
    plt.ylim([0, max(n_alive) + 5])
    plt.xlabel("round")
    plt.ylabel("number of alive nodes")
    # In headless environments (Agg) calling plt.show() issues a
    # UserWarning because FigureCanvasAgg is non-interactive. Save the
    # figure to a file when running with Agg; otherwise show interactively.
    import matplotlib
    if matplotlib.get_backend().lower() == "agg":
        plt.savefig("apteen_alive_nodes.png", dpi=200)
    else:
        plt.show()


if __name__ == "__main__":
    test_apteen()
