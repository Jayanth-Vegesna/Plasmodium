import os
import glob
import urllib.request
import urllib.parse
import csv
import io

# Ensure environment variables are set
image_dir = os.environ.get("RENDER_OUT_DIR")
pdb_dir = os.environ.get("AF_RAW_DIR")

if not image_dir or not pdb_dir:
    print("Error: RENDER_OUT_DIR and AF_RAW_DIR environment variables must be set.")
    exit(1)

base_dir = os.path.dirname(image_dir)
output_html = os.path.join(base_dir, "index.html")

js_dir = os.path.join(base_dir, "PDB_JS")
os.makedirs(js_dir, exist_ok=True)

rel_image_dir = os.path.relpath(image_dir, base_dir)
rel_js_dir = os.path.relpath(js_dir, base_dir)

print("Fetching metadata from UniProt...")
params = urllib.parse.urlencode({
    "query": "proteome:UP000001450",
    "format": "tsv",
    "fields": "accession,protein_name" 
})
url = f"https://rest.uniprot.org/uniprotkb/stream?{params}"

metadata = {}
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Python'})
    with urllib.request.urlopen(req) as response:
        tsv_data = response.read().decode('utf-8')
        reader = csv.reader(io.StringIO(tsv_data), delimiter='\t')
        next(reader) 
        for row in reader:
            if len(row) >= 2:
                acc = row[0]
                name = row[1].split(' (EC')[0].split(' [')[0].strip()
                metadata[acc] = {"name": name}
    print("Metadata fetched successfully!")
except Exception as e:
    print(f"Warning: Could not fetch metadata ({e}).")

print("Converting local PDB files to JS wrappers (Bypassing Browser Security)...")
pdb_files = glob.glob(os.path.join(pdb_dir, "*.pdb"))
pdb_map = {}

for p in pdb_files:
    basename = os.path.basename(p)
    uid = basename.split('-')[1]
    
    with open(p, 'r', encoding='utf-8') as f:
        pdb_text = f.read()
    
    escaped_text = pdb_text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    js_content = f"window.receivePDBData('{uid}', `{escaped_text}`);"
    
    js_filename = f"{uid}.js"
    js_filepath = os.path.join(js_dir, js_filename)
    with open(js_filepath, 'w', encoding='utf-8') as js_file:
        js_file.write(js_content)
        
    pdb_map[uid] = True

print("Building hyper-optimized dashboard HTML...")
files = glob.glob(os.path.join(image_dir, "*.png"))
data = []

for f in files:
    filename = os.path.basename(f)
    name_part = filename.replace(".png", "")
    parts = name_part.split("_")
    
    if len(parts) == 2:
        uid = parts[0]
        try:
            score = float(parts[1])
        except ValueError:
            continue
        
        if uid in pdb_map:
            p_name = metadata.get(uid, {}).get("name", "Unknown Protein")
            data.append({
                "id": uid, 
                "score": score, 
                "file": f"{rel_image_dir}/{filename}", 
                "name": p_name,
                "js_file": f"{rel_js_dir}/{uid}.js"
            })

data.sort(key=lambda x: x['score'], reverse=True)

total_proteins = len(data)
if total_proteins > 0:
    avg_plddt = sum(item['score'] for item in data) / total_proteins
    high_conf = sum(1 for item in data if item['score'] >= 70)
else:
    avg_plddt = 0
    high_conf = 0

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>P. falciparum Proteome</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.0.1/3Dmol-min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #e0e0e0; padding: 20px; margin: 0; }}
        .controls {{ position: sticky; top: 0; background: #1e1e1e; padding: 20px; z-index: 100; box-shadow: 0 4px 10px rgba(0,0,0,0.5); border-radius: 8px; margin-bottom: 20px; border: 1px solid #333; }}
        .header-flex {{ display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 20px; }}
        .title-area h1 {{ margin: 0 0 5px 0; color: #ffffff; }}
        .title-area h3 {{ margin: 0 0 15px 0; color: #888; font-weight: normal; }}
        .stats-container {{ display: flex; gap: 15px; background: #2a2a2a; padding: 15px; border-radius: 8px; border: 1px solid #444; }}
        .stat-box {{ display: flex; flex-direction: column; align-items: center; min-width: 120px; }}
        .stat-value {{ font-size: 1.4em; font-weight: bold; color: #64b5f6; }}
        .stat-label {{ font-size: 0.85em; color: #aaa; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }}
        
        /* Grid Optimization */
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; }}
        
        /* High-Performance Card Styling */
        .card {{ 
            background: #1e1e1e; 
            padding: 15px; 
            border-radius: 10px; 
            text-align: center; 
            border: 1px solid #333; 
            cursor: pointer; 
            position: relative;
            
            /* The Magic Performance Fixes */
            content-visibility: auto;
            contain-intrinsic-size: 250px 320px; /* Prevents scrollbar jumping */
            transition: transform 0.2s, border-color 0.2s; /* Strict targeting, no 'all' */
            will-change: transform; /* Hints the GPU */
        }}
        
        /* Removed heavy box-shadows on hover to save GPU */
        .card:hover {{ transform: translateY(-5px); border-color: #64b5f6; }}
        .card img {{ width: 100%; height: auto; border-radius: 6px; background: #2a2a2a; margin-bottom: 10px; min-height: 180px; display: block; }}

        .id {{ font-weight: bold; display: block; color: #ffffff; font-size: 1.1em; }}
        .name {{ display: block; color: #aaa; font-size: 0.85em; margin-top: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .score {{ font-size: 0.95em; font-weight: bold; margin-top: 10px; display: block; }}
        .high {{ color: #4caf50; }}
        .medium {{ color: #ffeb3b; }}
        .low {{ color: #ff9800; }}
        input[type="text"] {{ padding: 10px; width: 100%; max-width: 400px; border: 1px solid #444; border-radius: 6px; background: #2a2a2a; color: #fff; font-size: 1em; box-sizing: border-box; }}
        
        /* Modal Styles */
        #modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 1000; justify-content: center; align-items: center; }}
        .modal-content {{ background: #1e1e1e; padding: 20px; border-radius: 12px; width: 80%; max-width: 900px; height: 80%; display: flex; flex-direction: column; position: relative; border: 1px solid #444; }}
        .modal-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 15px; }}
        .modal-title {{ margin: 0; color: #fff; font-size: 1.5em; }}
        .modal-meta-container {{ margin-top: 8px; font-size: 0.95em; }}
        .close-btn {{ background: none; border: none; color: #aaa; font-size: 2em; cursor: pointer; line-height: 1; padding: 0 10px; }}
        .close-btn:hover {{ color: #fff; }}
        #viewer_div {{ flex-grow: 1; background: #121212; border-radius: 8px; position: relative; margin-top: 10px; }}
        
        .loading-text {{ color: #64b5f6; font-weight: bold; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="controls">
        <div class="header-flex">
            <div class="title-area">
                <h1><i>Plasmodium falciparum</i> Proteome</h1>
                <h3>By Jayanth Vegesna</h3>
                <input type="text" id="search" placeholder="Search by UniProt ID or Name..." onkeyup="filterCards()">
            </div>
            <div class="stats-container">
                <div class="stat-box">
                    <span class="stat-value">{total_proteins}</span>
                    <span class="stat-label">Total Proteins</span>
                </div>
                <div class="stat-box">
                    <span class="stat-value">{avg_plddt:.2f}</span>
                    <span class="stat-label">Average pLDDT</span>
                </div>
                <div class="stat-box">
                    <span class="stat-value">{high_conf}</span>
                    <span class="stat-label">High Conf (>70)</span>
                </div>
            </div>
        </div>
    </div>
    
    <div class="grid" id="proteinGrid">
        {" ".join([f'''
        <div class="card" data-search="{item['id']} {item['name'].upper()}" onclick="openViewer('{item['js_file']}', '{item['id']}', '{item['name'].replace("'", "\\'")}', {item['score']})">
            <img loading="lazy" decoding="async" src="{item['file']}" alt="{item['id']}" onerror="this.onerror=null; this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'100%\\' height=\\'100%\\'><rect width=\\'100%\\' height=\\'100%\\' fill=\\'#333\\'/><text x=\\'50%\\' y=\\'50%\\' fill=\\'#888\\' font-family=\\'sans-serif\\' font-size=\\'14\\' text-anchor=\\'middle\\' dominant-baseline=\\'middle\\'>Render Failed</text></svg>';">
            <span class="id">{item['id']}</span>
            <span class="name" title="{item['name']}">{item['name']}</span>
            <span class="score {'high' if item['score'] >= 70 else 'medium' if item['score'] >= 50 else 'low'}">
                pLDDT: {item['score']}
            </span>
        </div>''' for item in data])}
    </div>

    <div id="modal">
        <div class="modal-content">
            <div class="modal-header">
                <div>
                    <h2 class="modal-title" id="modal-title">Protein ID</h2>
                    <div class="modal-meta-container" id="modal-meta"></div>
                    <div id="status" class="loading-text"></div>
                </div>
                <button class="close-btn" onclick="closeViewer()">&times;</button>
            </div>
            <div id="viewer_div"></div>
        </div>
    </div>

    <script>
        let viewer = null;

        function filterCards() {{
            let input = document.getElementById('search').value.toUpperCase();
            let cards = document.getElementsByClassName('card');
            for (let i = 0; i < cards.length; i++) {{
                let searchData = cards[i].getAttribute('data-search');
                cards[i].style.display = searchData.includes(input) ? "" : "none";
            }}
        }}

        function openViewer(jsPath, uniprotId, proteinName, plddtScore) {{
            document.getElementById('modal').style.display = 'flex';
            document.getElementById('modal-title').innerText = uniprotId + " - " + proteinName;
            
            let quality = "Very Low (Disordered)";
            let scoreColor = "#ff9800"; 
            
            if (plddtScore >= 90) {{
                quality = "Very High";
                scoreColor = "#4caf50"; 
            }} else if (plddtScore >= 70) {{
                quality = "Confident";
                scoreColor = "#65cbf3"; 
            }} else if (plddtScore >= 50) {{
                quality = "Low";
                scoreColor = "#ffdb13"; 
            }}

            document.getElementById('modal-meta').innerHTML = `
                <span style="color: ${{scoreColor}}; font-weight: bold;">Average pLDDT: ${{plddtScore}} (${{quality}})</span>
                <span style="margin: 0 10px; color: #555;">|</span>
                <a href="https://www.uniprot.org/uniprotkb/${{uniprotId}}/entry" target="_blank" style="color: #64b5f6; text-decoration: none;">🔗 View on UniProt</a>
            `;

            document.getElementById('status').innerText = "Loading structure data...";

            if (!viewer) {{
                let element = document.getElementById('viewer_div');
                let config = {{ backgroundColor: '#121212' }};
                viewer = $3Dmol.createViewer(element, config);
            }} else {{
                viewer.clear();
            }}

            let script = document.createElement('script');
            script.src = jsPath;
            script.id = 'temp-pdb-script';
            
            let oldScript = document.getElementById('temp-pdb-script');
            if(oldScript) oldScript.remove();
            
            document.body.appendChild(script);
        }}

        window.receivePDBData = function(uid, pdbData) {{
            document.getElementById('status').innerText = "";
            viewer.addModel(pdbData, "pdb");
            
            let colorAlphaFold = function(atom) {{
                if(atom.b > 90) return '#0053d6'; 
                if(atom.b > 70) return '#65cbf3'; 
                if(atom.b > 50) return '#ffdb13'; 
                return '#ff7d45'; 
            }};
            
            viewer.setStyle({{}}, {{cartoon: {{colorfunc: colorAlphaFold}}}});
            viewer.zoomTo();
            viewer.render();
        }};

        function closeViewer() {{
            document.getElementById('modal').style.display = 'none';
            if (viewer) viewer.clear();
        }}
    </script>
</body>
</html>
"""

with open(output_html, "w", encoding='utf-8') as f:
    f.write(html_content)

print(f"Hyper-Optimized Dashboard created successfully at: {output_html}")
