# *Plasmodium falciparum* Portal

An interactive multi-omics platform for exploring the genomic, structural, and spatial biology of the malaria parasite.

## Features
* **Genome**: Interactive chromosome browser and dynamic sequence extractor.
* **Proteome**: Searchable database for visualizing 3D protein structures in *P. falciparum*.
* **Interactome**: Egocentric protein-protein interaction networks.
* **Spatial Atlas**: Mapping of proteins directly to subcellular organelles.

## Project Structure
* `index.html`: Main landing page and portal.
* `genome.html`: Genomic annotation browser.
* `proteome.html`: Searchable structural dashboard.
* `interactome.html`: Interaction network interface.
* `spatial.html`: Subcellular localization atlas.
* `PDB_JS/`: JavaScript-wrapped protein coordinate files.
* `RENDER_OUT/`: Static 3D renders for the proteome grid.
* `GENOMIC/` & `INTERACT/`: Datasets for the browser and network tools.

## Tech Stack
* **Visualization**: D3.js (Genome), 3Dmol.js (Structures), Cytoscape.js (Networks).
* **Data Processing**: Python (UniProt API integration).
* **Deployment**: GitHub Pages.

