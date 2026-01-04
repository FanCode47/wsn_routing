#!/usr/bin/env python3
"""
Run all visualization scripts in one go and save outputs to a single folder.
"""

import os
from datetime import datetime

from visualize_parameters import visualize_comparison
from test_leach import run_leach
from test_apteen import run_apteen


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("Results", f"all_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    print(f"Saving all figures to: {output_dir}")

    # APTEEN parameter sweep comparison
    visualize_comparison(output_dir=output_dir, show=False)

    # LEACH snapshots/topology/GIF (use same folder tree)
    run_leach(
        output_dir=os.path.join(output_dir, "leach"),
        snapshot_step=5,
        topo_step=5,
        snapshot_gif=True,
        topo_gif=True,
        backend="Agg",
    )

    # APTEEN snapshots/topology/GIF (use same folder tree)
    run_apteen(
        output_dir=os.path.join(output_dir, "apteen"),
        snapshot_step=5,
        topo_step=5,
        snapshot_gif=True,
        topo_gif=True,
        backend="Agg",
    )


if __name__ == "__main__":
    main()
