import os
import glob
import urllib.request
import csv
import io
import json

string_file = "36329.protein.links.v12.0.txt"
js_dir = "PDB_JS" 
output_js = "network_data.js"

# Known drug targets in the hemoglobin digestion/vacuole pathway
# PfCRT (Q8ILE5), PfMDR1 (P13568), Plasmepsin II (P20710), Plasmepsin IV (Q7K6A5), etc.
drug_target_uids = {
    'Q8ILE5', 'P13568', 'P20710', 'Q7K6A5', 'P04924', 'Q8I0W8'
}

if not os.path.exists(string_file):
    print(f"Error: {string_file} not found.")
    exit(1)

print("1. Scanning local 3D structures...")
available_uids = [os.path.basename(f).replace('.js', '') for f in glob.glob(os.path.join(js_dir, "*.js"))]
available_set = set(available_uids)

print("2. Fetching Protein Metadata from UniProt...")
url = "https://rest.uniprot.org/uniprotkb/stream?query=proteome:UP000001450&format=tsv&fields=accession,gene_names,protein_name"
req = urllib.request.Request(url, headers={'User-Agent': 'Python'})

uniprot_to_name = {}
pathway_keywords = ['plasmepsin', 'falcipain', 'falcilysin', 'heme detoxification', 'pfcrt', 'pfmdr1']
target_pathway_uids = set()

try:
    with urllib.request.urlopen(req) as response:
        reader = csv.reader(io.StringIO(response.read().decode('utf-8')), delimiter='\t')
        next(reader) 
        for row in reader:
            acc, genes, name = row[0], row[1].lower(), row[2].lower()
            uniprot_to_name[acc] = row[2].split(' (EC')[0].strip()
            if any(k in genes or k in name for k in pathway_keywords):
                target_pathway_uids.add(acc)
except Exception:
    print("UniProt fetch failed; proceeding with IDs.")

print("3. Building Drug-Target Aware Network...")
nodes = {}
edges = []
confidence_threshold = 400 

with open(string_file, 'r') as f:
    next(f)
    for line in f:
        p1, p2, score = line.strip().split()
        u1, u2 = p1.replace("36329.", ""), p2.replace("36329.", "")
        
        if int(score) < confidence_threshold: continue
        if u1 not in target_pathway_uids and u2 not in target_pathway_uids: continue

        if u1 in available_set and u2 in available_set:
            for u in [u1, u2]:
                if u not in nodes:
                    nodes[u] = {
                        "data": {
                            "id": u, 
                            "name": uniprot_to_name.get(u, u), 
                            "gene": u,
                            "is_drug_target": "true" if u in drug_target_uids else "false"
                        }
                    }
            edges.append({"data": {"source": u1, "target": u2, "weight": int(score)}})

with open(output_js, "w") as f:
    f.write("window.NetworkData = " + json.dumps(list(nodes.values()) + edges) + ";")
print(f"Success! Network with {len(nodes)} nodes created.")
