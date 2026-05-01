# *Plasmodium falciparum* Systems Biology Portal[cite: 5]

An interactive multi-omics platform for exploring the genomic, structural, and spatial biology of the malaria parasite.[cite: 5]

## Features
* **Genome**: Interactive chromosome browser and dynamic sequence extractor.[cite: 4]
* **Proteome**: Searchable database for visualizing 3D protein structures in *P. falciparum*.[cite: 6]
* **Interactome**: Egocentric protein-protein interaction networks.
* **Spatial Atlas**: Mapping of proteins directly to subcellular organelles.

## Project Structure[cite: 5]
* `index.html`: Main landing page and portal.[cite: 5]
* `genome.html`: Genomic annotation browser.[cite: 4]
* `proteome.html`: Searchable structural dashboard.[cite: 6]
* `interactome.html`: Interaction network interface.
* `spatial.html`: Subcellular localization atlas.
* `PDB_JS/`: JavaScript-wrapped protein coordinate files.[cite: 6]
* `RENDER_OUT/`: Static 3D renders for the proteome grid.[cite: 6]
* `GENOMIC/` & `INTERACT/`: Datasets for the browser and network tools.[cite: 5]

## Tech Stack
* **Visualization**: D3.js (Genome), 3Dmol.js (Structures), Cytoscape.js (Networks).[cite: 4, 6]
* **Data Processing**: Python (UniProt API integration).
* **Deployment**: GitHub Pages.

---
**Developed by Jayanth Vegesna**
