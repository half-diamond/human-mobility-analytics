Human Mobility Analytics

End-to-end spatio-temporal pipeline for human GPS trajectories, with offline place-name extraction using OpenStreetMap.
This project ingests the Microsoft Geolife GPS trajectories, cleans and segments trips, extracts stay points and routes, performs pattern mining (frequent motifs, hotspots, transition models), and — importantly — resolves coordinates to human-readable place names offline by processing a local OpenStreetMap extract for much faster, scalable reverse-geocoding than relying on online APIs.

Why offline reverse-geocoding?

Online APIs are convenient but slow and rate-limited for large trajectory collections. This project downloads an OSM region extract and preprocesses geometry + place attributes into a spatial index, enabling:

fast bulk lookup of POI/street/place names for millions of points,

deterministic results and reproducibility (no external API changes),

control over name-priority (e.g., prefer place=city over highway=name),

local caching and batch processing for production/analysis workflows.

Highlights

End-to-end pipeline: ingestion → cleaning → segmentation → feature extraction → pattern mining → visualization.

Offline place-name resolution: downloaded OpenStreetMap PBF → processed into spatial layers and indexed for high-throughput reverse-geocoding.

Extracts stay points, frequent routes, and time-of-day / day-of-week activity clusters.

Interactive maps (Folium) and heatmaps for spatial exploration.

Reproducible Jupyter notebooks and modular scripts.

Methods & Techniques

Preprocessing: filter noise, handle time gaps, project coordinates (EPSG:3857 / local).

Segmentation: stay-point detection (distance + dwell-time thresholds), trip splitting.

Geocoding / Naming:

download regional OSM extract (PBF), parse relevant feature layers (places, amenities, highways, buildings), and produce a condensed name-table;

build spatial index (R-tree / PostGIS / H3) and perform spatial-join or point-in-polygon queries to map GPS points to the nearest/containing named feature;

apply priority rules and local caching to resolve ambiguous matches and maximize match-quality.

Pattern discovery: DBSCAN/HDBSCAN for spatial clusters, sequence mining (PrefixSpan / n-grams) for frequent mobility motifs, first-order Markov transition matrices for simple next-location prediction.

Visualization: Folium for interactive maps, route density heatmaps, temporal activity plots.

Results (summary)

High-throughput, reproducible mapping of GPS points to place names using local OSM data.

Discovery of recurring mobility motifs, commuting corridors, and temporal hotspots.

Interactive map outputs and CSV summaries for downstream analysis.
