import os
import glob
import numpy as np
from chimerax.core.commands import run

# Ensure variables are pulled from your shell
input_dir = os.environ.get("AF_RAW_DIR")
output_dir = os.environ.get("RENDER_OUT_DIR")

if not input_dir or not output_dir:
    print("Error: Environment variables AF_RAW_DIR and RENDER_OUT_DIR must be set.")
    exit(1)

# --- NEW RESUME LOGIC ---
# 1. Find all PNG files already in the output folder
existing_pngs = glob.glob(os.path.join(output_dir, "*.png"))

# 2. Extract UniProt IDs from the filenames (e.g., "C0H4W4_59.78.png" -> "C0H4W4")
completed_ids = set()
for png in existing_pngs:
    basename = os.path.basename(png)
    uid = basename.split('_')[0]
    completed_ids.add(uid)

print(f"Found {len(completed_ids)} already processed structures. Resuming...")
# ------------------------

# Get all PDB files
structure_files = glob.glob(os.path.join(input_dir, "*.pdb"))
print(f"Remaining structures to process: {len(structure_files) - len(completed_ids)}")

for filepath in structure_files:
    filename = os.path.basename(filepath)
    uniprot_id = filename.split('-')[1] 
    
    # --- SKIP ALREADY RENDERED FILES ---
    if uniprot_id in completed_ids:
        continue
    # -----------------------------------
    
    # 1. Load
    run(session, f"open {filepath}")
    
    # 2. Calculate pLDDT
    model = session.models.list()[0]
    avg_plddt = np.mean(model.atoms.bfactors)
    
    # 3. Style
    run(session, "view orient")
    run(session, "color bfactor palette alphafold")
    run(session, "lighting soft")
    run(session, "graphics silhouettes true")
    
    # 4. Save (UniprotID_pLDDT.png)
    output_name = f"{uniprot_id}_{avg_plddt:.2f}.png"
    output_path = os.path.join(output_dir, output_name)
    run(session, f"save {output_path} width 500 height 500 transparentBackground true")
    
    # 5. Cleanup
    run(session, "close session")

print("All structures rendered successfully!")
