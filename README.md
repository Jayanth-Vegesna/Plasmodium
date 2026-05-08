# *Plasmodium falciparum* Multi-Omics Portal

An interactive platform designed to visualize genomic sequences, protein structures, cellular localization, and dynamic expression patterns in the human *Plasmodium falciparum* malaria parasite, *P. falciparum* 3D7.

---

## Interactive Features and Data Sources

### Genome Browser
* **Description**: An interactive chromosome browser and sequence extractor for navigating the 14 *Plasmodium falciparum* chromosomes.
* **Source Data**:
    * The PlasmoDB-68 GFF file was used for primary genomic annotations.
    * *var* gene IDs were identified using the NCBI annotation for *Plasmodium falciparum* 3D7.
    * *rifin* gene IDs were identified via PlasmoDB searches.
    * *stevor* gene IDs were extracted from the PlasmoDB-68 GFF annotation.

### Proteome Dashboard
* **Description**: A searchable database for visualizing 3D protein structures with associated pLDDT confidence scores.
* **Source Data**: Structural models were sourced from the AlphaFold DB for the predicted proteome.

### Transcriptome Explorer
* **Description**: Interactive time-series line charts tracking gene activity throughout the intraerythrocytic development cycle (IDC).
* **Data Content**: Transcripts Per Million (TPM) values for 7 time-points (0h, 8h, 16h, 24h, 32h, 40h, 48h) tracking Ring, Trophozoite, and Schizont stages.
* **Source Data**: Derived from the Chappell et al. (2020) DAFT-Seq dataset (DS_416070059c).

### Interactome
* **Description**: Egocentric protein-protein interaction networks designed to identify functional clusters.
* **Source Data**: Interaction data was sourced from the STRING database using the 36329.protein.links.v12.0 dataset for *Plasmodium falciparum*.

### Spatial Atlas
* **Description**: A visual mapping tool for exploring protein localization within major subcellular organelles.
* **Source Data**: Subcellular Location annotations for *Plasmodium falciparum* were sourced from UniProt.

### Gene Ontology
* **Description**: A physics-based network visualization for exploring biological processes and molecular functions.
* **Source Data**: Gene Ontology (GO) term annotations for *Plasmodium falciparum* were sourced from PlasmoDB.

---

