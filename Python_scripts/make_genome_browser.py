import os
import json

gff_file = "custom.gff" 
fasta_file = "genome.fasta" 
output_js = "genome_data.js"

if not os.path.exists(gff_file) or not os.path.exists(fasta_file):
    print("Error: Ensure BOTH custom.gff and genome.fasta are in this folder.")
    exit(1)

print("1. Loading FASTA sequences...")
fasta_data = {}
curr_chrom = ""
with open(fasta_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith(">"):
            curr_chrom = line[1:].split()[0] 
            fasta_data[curr_chrom] = []
        else:
            fasta_data[curr_chrom].append(line)

for chrom in fasta_data:
    fasta_data[chrom] = "".join(fasta_data[chrom]).upper()

print("2. Parsing GFF and extracting gene sequences...")
genome_data = {}
max_lengths = {}
allowed_features = {
    "CDS", "five_prime_UTR", "three_prime_UTR", 
    "intron", "ncRNA", "pseudogene", "rRNA", "tRNA"
}

with open(gff_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith("#"): continue
        parts = line.strip().split('\t')
        if len(parts) < 9: continue
            
        chrom = parts[0]
        feature_type = parts[2]
        
        if feature_type in allowed_features:
            start = int(parts[3])
            end = int(parts[4])
            strand = parts[6]
            
            chrom_seq = fasta_data.get(chrom, "")
            seq_snippet = chrom_seq[start-1:end] if chrom_seq else ""
            
            attrs = {k: v for k, v in (attr.split('=', 1) for attr in parts[8].split(';') if '=' in attr)}
            name = attrs.get("gene_id", attrs.get("Parent", attrs.get("ID", "Unknown")))
            
            if chrom not in genome_data:
                genome_data[chrom] = []
                max_lengths[chrom] = 0
                
            genome_data[chrom].append({
                "name": name,
                "type": feature_type,
                "start": start,
                "end": end,
                "strand": strand,
                "seq": seq_snippet 
            })
            
            if end > max_lengths[chrom]:
                max_lengths[chrom] = end

print("Wrapping data for offline browser access...")
js_content = f"""
window.GenomeData = {json.dumps(genome_data)};
window.ChromosomeLengths = {json.dumps(max_lengths)};
"""

with open(output_js, 'w', encoding='utf-8') as f:
    f.write(js_content)

print("Done! Open genome.html")
