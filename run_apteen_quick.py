from distribution import *
from router import APTEEN


def run():
    sink = (0, 0)
    # small test network
    nodes = simple_loader(
        sink,
        uniform_in_square(100, 10, sink)
    )
    apteen = APTEEN(*nodes, n_cluster=3, period=5, event_prob=0.05)
    # enable thresholds for demonstration
    apteen.hard_threshold = 0.92
    apteen.soft_threshold = 0.8
    apteen.soft_delta = 0.12
    apteen.min_report_interval = 2
    apteen.initialize()
    r = 0
    while True:
        r += 1
        apteen.execute()
        n = len(apteen.alive_non_sinks)
        print(f"round {r}: alive_non_sinks = {n}, clusters = {len(apteen.clusters)}")
        if n == 0:
            break


if __name__ == '__main__':
    run()
