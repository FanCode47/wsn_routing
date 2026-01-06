"""
Localization strings for WSN Routing Simulation Suite
Supported languages: eng (English), pl (Polish)
"""

TRANSLATIONS = {
    "eng": {
        # Terminal messages
        "results_saved": "Results will be saved to: {}",
        "snapshot_saved": "Snapshot saved to {}",
        "topology_saved": "Topology snapshot saved to {}",
        "cluster_heads": "cluster heads: {}",
        "nodes_alive": "nodes alive: {}",
        "plot_saved": "Plot saved to {}",
        "gif_saved": "GIF saved to {}",
        "topology_gif_saved": "Topology GIF saved to {}",
        "gif_failed": "Failed to create GIF: {}",
        "topology_gif_failed": "Failed to create topology GIF: {}",
        "imageio_missing_snapshot": "SNAPSHOT_GIF=1 set but imageio is not installed; skipping GIF export.",
        "imageio_missing_topo": "TOPO_GIF=1 set but imageio is not installed; skipping GIF export.",
        
        # Plot labels
        "round": "round",
        "rounds": "Round",
        "alive_nodes": "number of alive nodes",
        "alive_nodes_title": "Alive nodes",
        "transmissions_per_round": "Transmissions per round",
        "avg_energy": "Average energy (J)",
        "total_transmissions": "Total transmissions",
        
        # Configuration names
        "leach_like": "LEACH-like",
        "teen_like": "TEEN-like",
        "conservative": "Conservative",
        "aggressive": "Aggressive",
        "balanced": "Balanced",
        "adaptive": "Adaptive per-cluster",
        
        # Progress messages
        "config_progress": "[{}/6] {} (HT={}, ST={}, TC={})...",
        "first_death": "first={}",
        "complete_death": "complete={}",
        "degradation": "degradation={}",

        # visualize_parameters specific
        "running_presets": "Running six APTEEN presets (nodes={}, area={}x{}) (until full network death)...\n",
        "saved_figure": "Saved figure: {}",
        "summary_header": "\nSummary (rounds):",
        "summary_columns": "Name                      First   Complete   Degradation   Total TX   TX/round",
        "summary_separator": "-" * 78,
        "energy_chart_help": "\nHow to read the energy chart (top right):",
        "energy_chart_x_axis": "- X axis: round; Y axis: average energy of alive nodes (J).",
        "energy_chart_slope": "- Steeper downward slope = faster energy drain = earlier deaths.",
        "energy_chart_marker": "- Dotted vertical line marks the first node death for that curve.",
        "warn_imageio": "[WARN] TOPO_GIF requested but imageio not installed; skipping GIF for {}.",
        "topology_gif_failed_viz": "Failed to create topology GIF for {}: {}",
        "apteen_title": "APTEEN parameter impact: first death vs complete death",
        "alive_title": "Alive nodes (dotted = first death)",
        "tx_title": "Transmission activity (first 1000 rounds)",
        "energy_title": "Energy (steeper = faster drain)",
        "lifetime_title": "Network lifetime: solid=to first death, faded=degradation",
        "total_tx_title": "Total transmissions over lifetime",
        "avg_tx_title": "Average transmission intensity",
        "event_label": "Event",
    },
    
    "pl": {
        # Terminal messages
        "results_saved": "Wyniki zostaną zapisane w: {}",
        "snapshot_saved": "Zrzut zapisany do {}",
        "topology_saved": "Zrzut topologii zapisany do {}",
        "cluster_heads": "głowy klastrów: {}",
        "nodes_alive": "węzły żywe: {}",
        "plot_saved": "Wykres zapisany do {}",
        "gif_saved": "GIF zapisany do {}",
        "topology_gif_saved": "GIF topologii zapisany do {}",
        "gif_failed": "Nie udało się utworzyć GIF: {}",
        "topology_gif_failed": "Nie udało się utworzyć GIF topologii: {}",
        "imageio_missing_snapshot": "SNAPSHOT_GIF=1 ustawiony, ale imageio nie jest zainstalowany; pomijanie eksportu GIF.",
        "imageio_missing_topo": "TOPO_GIF=1 ustawiony, ale imageio nie jest zainstalowany; pomijanie eksportu GIF.",
        
        # Plot labels
        "round": "runda",
        "rounds": "Runda",
        "alive_nodes": "liczba żywych węzłów",
        "alive_nodes_title": "Żywe węzły",
        "transmissions_per_round": "Transmisje na rundę",
        "avg_energy": "Średnia energia (J)",
        "total_transmissions": "Całkowite transmisje",
        
        # Configuration names
        "leach_like": "Podobny do LEACH",
        "teen_like": "Podobny do TEEN",
        "conservative": "Konserwatywny",
        "aggressive": "Agresywny",
        "balanced": "Zrównoważony",
        "adaptive": "Adaptacyjny na klaster",
        
        # Progress messages
        "config_progress": "[{}/6] {} (HT={}, ST={}, TC={})...",
        "first_death": "pierwszy={}",
        "complete_death": "kompletny={}",
        "degradation": "degradacja={}",
        
        # visualize_parameters specific
        "running_presets": "Uruchamianie sześciu presetów APTEEN (węzły={}, obszar={}x{}) (do całkowitej śmierci sieci)...\n",
        "saved_figure": "Zapisano wykres: {}",
        "summary_header": "\nPodsumowanie (rundy):",
        "summary_columns": "Nazwa                     Pierwszy  Kompletny  Degradacja   TX łącznie   TX/runda",
        "summary_separator": "-" * 85,
        "energy_chart_help": "\nJak czytać wykres energii (prawy górny):",
        "energy_chart_x_axis": "- Oś X: runda; Oś Y: średnia energia żywych węzłów (J).",
        "energy_chart_slope": "- Bardziej stromy spadek = szybszy spadek energii = wcześniejsze śmierci.",
        "energy_chart_marker": "- Przerywana pionowa linia oznacza pierwszą śmierć węzła dla tej krzywej.",
        "warn_imageio": "[OSTRZEŻENIE] TOPO_GIF wymagany, ale imageio nie zainstalowany; pomijanie GIF dla {}.",
        "topology_gif_failed_viz": "Nie udało się utworzyć GIF topologii dla {}: {}",
            "apteen_title": "Wpływ parametrów APTEEN: pierwsza śmierć vs pełna śmierć",
            "alive_title": "Żywe węzły (kropkowana = pierwsza śmierć)",
            "tx_title": "Aktywność transmisji (pierwsze 1000 rund)",
            "energy_title": "Energia (stromiej = szybszy spadek)",
            "lifetime_title": "Czas życia sieci: pełny=do pierwszej śmierci, półprzezroczysty=degradacja",
            "total_tx_title": "Łączna liczba transmisji w czasie życia",
            "avg_tx_title": "Średnia intensywność transmisji",
            "event_label": "Zdarzenie",
    }
}


def get_translation(key: str, lang: str = "eng") -> str:
    """
    Get translation for a given key and language.
    
    Args:
        key: Translation key
        lang: Language code ('eng' or 'pl')
    
    Returns:
        Translated string, or the key itself if translation not found
    """
    if lang not in TRANSLATIONS:
        lang = "eng"
    return TRANSLATIONS[lang].get(key, key)


def t(key: str, lang: str = "eng", *args, **kwargs) -> str:
    """
    Get and format translation.
    
    Args:
        key: Translation key
        lang: Language code ('eng' or 'pl')
        *args: Positional arguments for string formatting
        **kwargs: Keyword arguments for string formatting
    
    Returns:
        Formatted translated string
    """
    template = get_translation(key, lang)
    if args:
        return template.format(*args)
    elif kwargs:
        return template.format(**kwargs)
    return template
