import os
import glob
import urllib.request
import urllib.parse
import csv
import io
import json

# ==========================================
# 1. DIRECTORIES & FILES
# ==========================================
image_dir = "RENDER_OUT"
js_dir = "PDB_JS"
output_html = "spatial.html"
mapping_file = os.path.join("GENOMIC", "mapping.tsv")

if not os.path.exists(image_dir) or not os.path.exists(js_dir):
    print("Error: Could not find RENDER_OUT or PDB_JS folders. Ensure they are in this directory.")
    exit(1)

# ==========================================
# 2. LOAD PLASMODB MAPPINGS FROM TSV
# ==========================================
print("Loading PlasmoDB mappings from local TSV...")
uniprot_to_plasmodb = {}

if os.path.exists(mapping_file):
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    uid = parts[0].strip()
                    pid = parts[1].strip()
                    uniprot_to_plasmodb[uid] = pid
        print(f"Loaded {len(uniprot_to_plasmodb)} mappings from {mapping_file}.")
    except Exception as e:
        print(f"Error reading {mapping_file}: {e}")
else:
    print(f"Warning: Mapping file not found at '{mapping_file}'. PlasmoDB IDs will not be mapped.")

# ==========================================
# 3. FETCH SPATIAL DATA FROM UNIPROT
# ==========================================
print("Fetching Spatial Metadata from UniProt...")
params = urllib.parse.urlencode({
    "query": "proteome:UP000001450",
    "format": "tsv",
    "fields": "accession,protein_name,cc_subcellular_location" 
})
url = f"https://rest.uniprot.org/uniprotkb/stream?{params}"

def map_location(loc_string):
    loc_str = loc_string.lower()
    if not loc_str: return 'Unknown / Uncharacterized'
    if 'rhoptry' in loc_str or 'microneme' in loc_str or 'apical' in loc_str: return 'Rhoptries & Micronemes'
    if 'apicoplast' in loc_str or 'plastid' in loc_str: return 'Apicoplast'
    if 'mitochondrion' in loc_str: return 'Mitochondrion'
    if 'nucleus' in loc_str: return 'Nucleus'
    if 'food vacuole' in loc_str: return 'Food Vacuole'
    if 'cytoplasm' in loc_str: return 'Cytoplasm'
    if 'membrane' in loc_str or 'surface' in loc_str or 'host' in loc_str: return 'Surface Membrane'
    return 'Unknown / Uncharacterized'

metadata = {}
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Python'})
    with urllib.request.urlopen(req) as response:
        tsv_data = response.read().decode('utf-8')
        reader = csv.reader(io.StringIO(tsv_data), delimiter='\t')
        next(reader) 
        for row in reader:
            if len(row) >= 3:
                acc = row[0]
                name = row[1].split(' (EC')[0].split(' [')[0].strip()
                loc_str = row[2]
                mapped_loc = map_location(loc_str)
                plasmodb_id = uniprot_to_plasmodb.get(acc, "")
                
                metadata[acc] = {
                    "name": name, 
                    "location": mapped_loc,
                    "plasmodb": plasmodb_id
                }
    print("Metadata fetched successfully!")
except Exception as e:
    print(f"Warning: Could not fetch metadata ({e}).")

# ==========================================
# 4. MAP & CONVERT PDB/JS FILES
# ==========================================
print("Mapping available structures...")
pdb_map = {}

pdb_files = glob.glob(os.path.join(js_dir, "*.pdb"))
for p in pdb_files:
    basename = os.path.basename(p)
    uid = basename.split('-')[1] if '-' in basename else basename.split('.')[0]
    
    with open(p, 'r', encoding='utf-8') as f:
        pdb_text = f.read()
    
    escaped_text = pdb_text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    js_content = f"window.receivePDBData('{uid}', `{escaped_text}`);"
    
    js_filepath = os.path.join(js_dir, f"{uid}.js")
    with open(js_filepath, 'w', encoding='utf-8') as js_file:
        js_file.write(js_content)

js_files = glob.glob(os.path.join(js_dir, "*.js"))
for j in js_files:
    uid = os.path.basename(j).replace(".js", "")
    pdb_map[uid] = True

print(f"Found {len(pdb_map)} ready-to-use 3D structures.")

# ==========================================
# 5. BUILD THE DASHBOARD DATA
# ==========================================
print("Building HTML...")
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
            meta = metadata.get(uid, {})
            p_name = meta.get("name", "Unknown Protein")
            p_loc = meta.get("location", "Unknown / Uncharacterized")
            p_plasmodb = meta.get("plasmodb", uniprot_to_plasmodb.get(uid, ""))
            
            data.append({
                "id": uid, 
                "score": score, 
                "file": f"{image_dir}/{filename}", 
                "name": p_name,
                "location": p_loc,
                "plasmodb": p_plasmodb,
                "js_file": f"{js_dir}/{uid}.js"
            })

data.sort(key=lambda x: x['score'], reverse=True)
json_data_string = json.dumps(data)

# ==========================================
# 6. GENERATE HTML FILE
# ==========================================
# Using standard string replacement to avoid conflicting with CSS/JS curly braces

html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <title>P. falciparum Spatial Atlas</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.0.1/3Dmol-min.js"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #e0e0e0; padding: 20px; margin: 0; }
        
        .header-section { display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; align-items: stretch; }
        .controls { flex: 1; min-width: 300px; background: #1e1e1e; padding: 20px; border-radius: 8px; border: 1px solid #333; display: flex; flex-direction: column; justify-content: space-between; }
        .title-area h1 { margin: 0 0 5px 0; color: #ffffff; }
        .title-area p { margin: 0 0 15px 0; color: #888; font-size: 0.95em; line-height: 1.5; }
        
        .back-btn { display: inline-block; background: #2a2a2a; color: #aaa; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-size: 0.9em; margin-bottom: 15px; border: 1px solid #444; transition: all 0.2s; font-weight: bold; align-self: flex-start; }
        .back-btn:hover { background: #333; color: #fff; border-color: #64b5f6; }
        
        .map-container { flex: 1.5; min-width: 400px; background: #151515; border-radius: 8px; border: 1px solid #333; padding: 10px; display: flex; justify-content: center; align-items: center; position: relative; overflow: hidden; }
        
        svg { width: 100%; height: 100%; display: block; }
        
        .organelle-bg { cursor: pointer; transition: fill 0.3s; }
        .organelle-bg:hover { fill: rgba(255,255,255,0.03); }
        svg.filtering .organelle-bg.active { fill: rgba(255,255,255,0.08); stroke: #555; stroke-width: 1; stroke-dasharray: 4,4; }
        
        .organelle { cursor: pointer; transition: all 0.3s ease; }
        .organelle:hover { filter: brightness(1.4); drop-shadow(0 0 8px rgba(255,255,255,0.4)); }
        
        svg.filtering .organelle { opacity: 0.15; }
        svg.filtering .organelle.active { opacity: 1; filter: drop-shadow(0px 0px 12px rgba(255,255,255,0.5)); stroke: #fff; stroke-width: 2px; }
        
        .svg-label { fill: #ffffff; font-size: 18px; font-weight: bold; font-family: sans-serif; pointer-events: none; transition: fill 0.3s; }
        .leader-line { fill: none; stroke: #aaaaaa; stroke-width: 2; stroke-dasharray: 4,4; pointer-events: none; transition: stroke 0.3s; }
        
        svg.filtering .organelle.active ~ .leader-line,
        svg.filtering .organelle.active ~ .svg-label { fill: #64b5f6; stroke: #64b5f6; }

        .reset-filter { margin-top: 15px; padding: 12px; width: 100%; background: #2a2a2a; color: #fff; border: 1px solid #444; border-radius: 6px; cursor: pointer; display: none; font-weight: bold; transition: 0.2s; }
        .reset-filter:hover { background: #333; border-color: #64b5f6; }

        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; }
        .card { background: #1e1e1e; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #333; cursor: pointer; transition: transform 0.2s, border-color 0.2s; position: relative; content-visibility: auto; contain-intrinsic-size: 250px 320px; }
        .card:hover { transform: translateY(-5px); border-color: #64b5f6; }
        .card img { width: 100%; height: auto; border-radius: 6px; background: #2a2a2a; margin-bottom: 10px; min-height: 180px; display: block; }
        
        .id { font-weight: bold; display: block; color: #ffffff; font-size: 1.1em; }
        .plasmodb-id { font-size: 0.85em; color: #64b5f6; margin-top: 4px; display: block; font-weight: bold; font-family: monospace; letter-spacing: 0.5px; }
        .name { display: block; color: #aaa; font-size: 0.85em; margin-top: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        
        .loc-badge { display: inline-block; padding: 5px 12px; border-radius: 15px; font-size: 0.75em; font-weight: bold; margin-top: 10px; color: #fff; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); }

        #modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 1000; justify-content: center; align-items: center; }
        .modal-content { background: #1e1e1e; padding: 20px; border-radius: 12px; width: 80%; max-width: 900px; height: 80%; display: flex; flex-direction: column; position: relative; border: 1px solid #444; }
        .modal-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 15px; padding-right: 40px; }
        .modal-title { margin: 0; color: #fff; font-size: 1.5em; }
        .modal-meta-container { margin-top: 8px; font-size: 0.95em; display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
        .close-btn { position: absolute; top: 15px; right: 20px; background: none; border: none; color: #aaa; font-size: 2em; cursor: pointer; line-height: 1; padding: 5px; transition: color 0.2s; z-index: 10; }
        .close-btn:hover { color: #fff; }
        #viewer_div { flex-grow: 1; background: #121212; border-radius: 8px; position: relative; margin-top: 10px; }
        
        #sentinel { height: 50px; width: 100%; margin-top: 20px; }

        @media (max-width: 768px) {
            .header-section { flex-direction: column; }
            .map-container { min-width: 100%; height: 400px; }
            .modal-content { width: 95%; height: 95%; padding: 15px; padding-top: 50px; }
            .close-btn { top: 10px; right: 10px; font-size: 2.2em; background: #333; border: 1px solid #555; border-radius: 8px; padding: 2px 15px 6px 15px; color: #fff; z-index: 1001; }
        }
    </style>
</head>
<body>

    <div class="header-section">
        <div class="controls">
            <div class="title-area">
                <a href="index.html" class="back-btn">&larr; Back to Dashboard</a>
                <h1>Spatial Cell Atlas</h1>
                <p>Click on an organelle within the parasite diagram to instantly filter the structural database by subcellular localization. Click the empty background for uncharacterized proteins.</p>
            </div>
            
            <div>
                <h2 id="current-view" style="color: #64b5f6; margin-top: 20px; margin-bottom: 5px;">Showing: All Proteins</h2>
                <p id="hit-counter" style="color: #aaa; font-weight: bold; margin-top: 0;">Loading Structures...</p>
                <button id="reset-btn" class="reset-filter" onclick="resetFilter()">View All Proteins</button>
            </div>
        </div>
        
        <div class="map-container">
            <svg id="parasite-svg" viewBox="-250 0 1100 750" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
                
                <defs>
                    <radialGradient id="cyto-grad" cx="50%" cy="50%" r="50%">
                        <stop offset="20%" stop-color="#2a4365"/>
                        <stop offset="100%" stop-color="#0f172a"/>
                    </radialGradient>
                    <radialGradient id="nuc-grad" cx="50%" cy="50%" r="50%">
                        <stop offset="30%" stop-color="#d288ed"/>
                        <stop offset="100%" stop-color="#8e44ad"/>
                    </radialGradient>
                    <radialGradient id="vac-grad" cx="40%" cy="40%" r="50%">
                        <stop offset="0%" stop-color="#facc15"/>
                        <stop offset="100%" stop-color="#d97706"/>
                    </radialGradient>
                </defs>

                <rect x="-250" y="0" width="1100" height="750" fill="transparent" class="organelle-bg" onclick="filterByLocation('Unknown / Uncharacterized')" id="bg-catcher" rx="10"/>
                <text x="300" y="730" fill="#777" font-size="16" text-anchor="middle" pointer-events="none" font-style="italic">Click outside the cell for Unknown / Uncharacterized Proteins</text>

                <g class="organelle" onclick="filterByLocation('Cytoplasm')" data-loc="Cytoplasm" data-loc2="Surface Membrane">
                    <path d="M 300,50 C 150,150 100,400 150,550 C 200,680 400,680 450,550 C 500,400 450,150 300,50 Z" fill="url(#cyto-grad)" stroke="#fb923c" stroke-width="6"/>
                </g>
                <polyline points="135,460 -10,460" class="leader-line" />
                <text x="-20" y="465" class="svg-label" text-anchor="end">Cytoplasm & Surface</text>

                <g class="organelle" onclick="filterByLocation('Rhoptries & Micronemes')" data-loc="Rhoptries & Micronemes">
                    <path d="M 285,70 C 250,130 260,180 285,180 C 300,180 300,130 285,70 Z" fill="#60a5fa" stroke="#2563eb" stroke-width="2"/>
                    <path d="M 315,70 C 300,130 300,180 315,180 C 340,180 350,130 315,70 Z" fill="#60a5fa" stroke="#2563eb" stroke-width="2"/>
                    <circle cx="260" cy="110" r="6" fill="#93c5fd"/>
                    <circle cx="245" cy="140" r="6" fill="#93c5fd"/>
                    <circle cx="340" cy="110" r="6" fill="#93c5fd"/>
                    <circle cx="355" cy="140" r="6" fill="#93c5fd"/>
                </g>
                <polyline points="330,130 620,130" class="leader-line" />
                <text x="630" y="135" class="svg-label" text-anchor="start">Apical Complex</text>

                <g class="organelle" onclick="filterByLocation('Apicoplast')" data-loc="Apicoplast">
                    <path d="M 190,190 C 130,260 160,360 200,360 C 220,360 210,260 190,190 Z" fill="#4ade80" stroke="#166534" stroke-width="3"/>
                </g>
                <polyline points="160,280 -10,280" class="leader-line" />
                <text x="-20" y="285" class="svg-label" text-anchor="end">Apicoplast</text>

                <g class="organelle" onclick="filterByLocation('Food Vacuole')" data-loc="Food Vacuole">
                    <circle cx="300" cy="300" r="55" fill="url(#vac-grad)" stroke="#b45309" stroke-width="3"/>
                    <polygon points="280,290 295,280 305,295 285,300" fill="#451a03"/>
                    <polygon points="310,300 325,290 320,315" fill="#451a03"/>
                    <polygon points="290,320 305,310 310,330 295,335" fill="#451a03"/>
                </g>
                <polyline points="355,300 620,300" class="leader-line" />
                <text x="630" y="305" class="svg-label" text-anchor="start">Food Vacuole</text>

                <g class="organelle" onclick="filterByLocation('Mitochondrion')" data-loc="Mitochondrion">
                    <path d="M 380,220 C 430,250 420,360 430,430" fill="none" stroke="#ff6b6b" stroke-width="26" stroke-linecap="round"/>
                </g>
                <polyline points="430,330 620,330" class="leader-line" />
                <text x="630" y="335" class="svg-label" text-anchor="start">Mitochondrion</text>

                <g class="organelle" onclick="filterByLocation('Nucleus')" data-loc="Nucleus">
                    <ellipse cx="300" cy="490" rx="120" ry="85" fill="url(#nuc-grad)" stroke="#581c87" stroke-width="4"/>
                </g>
                <polyline points="420,490 620,490" class="leader-line" />
                <text x="630" y="495" class="svg-label" text-anchor="start">Nucleus</text>

            </svg>
        </div>
    </div>
    
    <div class="grid" id="proteinGrid"></div>
    <div id="sentinel"></div>

    <div id="modal">
        <div class="modal-content">
            <button class="close-btn" onclick="closeViewer()">&times;</button>
            <div class="modal-header">
                <div>
                    <h2 class="modal-title" id="modal-title">Protein ID</h2>
                    <div class="modal-meta-container" id="modal-meta"></div>
                    <div id="status" style="color: #64b5f6; font-weight: bold; margin-top: 10px;"></div>
                </div>
            </div>
            <div id="viewer_div"></div>
        </div>
    </div>

    <script>
        const allData = __JSON_DATA_HERE__; 
        
        let filteredData = [...allData];
        let currentIndex = 0;
        const CHUNK_SIZE = 50;

        document.getElementById('hit-counter').innerText = allData.length + " Structures Available";

        function renderChunk() {
            const chunk = filteredData.slice(currentIndex, currentIndex + CHUNK_SIZE);
            if (chunk.length === 0) return;

            let html = "";
            chunk.forEach(item => {
                let safeName = item.name.replace(/'/g, "\\'");
                
                let locColor = "#666";
                if(item.location === "Cytoplasm") locColor = "#fb923c";
                else if(item.location === "Rhoptries & Micronemes") locColor = "#60a5fa";
                else if(item.location === "Apicoplast") locColor = "#4ade80";
                else if(item.location === "Food Vacuole") locColor = "#facc15";
                else if(item.location === "Mitochondrion") locColor = "#ff6b6b";
                else if(item.location === "Nucleus") locColor = "#d288ed";
                else if(item.location === "Surface Membrane") locColor = "#00e5ff";

                let plasmoText = item.plasmodb ? `<span class="plasmodb-id">${item.plasmodb}</span>` : "";
                let passPlasmodb = item.plasmodb || "";
                
                html += `
                <div class="card" onclick="openViewer('${item.js_file}', '${item.id}', '${safeName}', '${item.location}', '${passPlasmodb}')">
                    <img loading="lazy" decoding="async" src="${item.file}" onerror="this.onerror=null; this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'100%\\' height=\\'100%\\'><rect width=\\'100%\\' height=\\'100%\\' fill=\\'#333\\'/><text x=\\'50%\\' y=\\'50%\\' fill=\\'#888\\' font-family=\\'sans-serif\\' font-size=\\'14\\' text-anchor=\\'middle\\' dominant-baseline=\\'middle\\'>Render Failed</text></svg>';">
                    <span class="id">${item.id}</span>
                    ${plasmoText}
                    <span class="name" title="${item.name}">${item.name}</span>
                    <span class="loc-badge" style="background:${locColor}">${item.location}</span>
                </div>`;
            });

            document.getElementById('proteinGrid').insertAdjacentHTML('beforeend', html);
            currentIndex += CHUNK_SIZE;
        }

        function filterByLocation(loc) {
            document.getElementById('parasite-svg').classList.add('filtering');
            document.querySelectorAll('.organelle, .organelle-bg').forEach(el => el.classList.remove('active'));
            
            let clickedEl = Array.from(document.querySelectorAll('.organelle, .organelle-bg')).find(el => el.getAttribute('data-loc') === loc || (loc === 'Unknown / Uncharacterized' && el.id === 'bg-catcher'));
            if(clickedEl) clickedEl.classList.add('active');

            document.getElementById('reset-btn').style.display = 'block';
            document.getElementById('current-view').innerText = "Showing: " + loc;

            filteredData = allData.filter(d => d.location === loc || (clickedEl && clickedEl.getAttribute('data-loc2') === d.location));
            
            document.getElementById('hit-counter').innerText = filteredData.length + " Structures Available";
            
            document.getElementById('proteinGrid').innerHTML = "";
            currentIndex = 0;
            renderChunk();
        }

        function resetFilter() {
            document.getElementById('parasite-svg').classList.remove('filtering');
            document.querySelectorAll('.organelle, .organelle-bg').forEach(el => el.classList.remove('active'));
            document.getElementById('reset-btn').style.display = 'none';
            document.getElementById('current-view').innerText = "Showing: All Proteins";
            document.getElementById('hit-counter').innerText = allData.length + " Structures Available";
            
            filteredData = [...allData];
            document.getElementById('proteinGrid').innerHTML = "";
            currentIndex = 0;
            renderChunk();
        }

        let viewer = null;

        function openViewer(jsPath, uniprotId, proteinName, location, plasmodbId) {
            document.getElementById('modal').style.display = 'flex';
            
            let displayTitle = uniprotId + " - " + proteinName;
            if(plasmodbId && plasmodbId !== "undefined") displayTitle = uniprotId + " (" + plasmodbId + ") - " + proteinName;
            document.getElementById('modal-title').innerText = displayTitle;
            
            let extraLinks = "";
            if (plasmodbId && plasmodbId !== "undefined") {
                extraLinks += `
                    <span style="margin: 0 5px; color: #555;">|</span>
                    <a href="https://plasmodb.org/plasmo/app/record/gene/${plasmodbId}" target="_blank" style="color: #64b5f6; text-decoration: none;">🔗 View on PlasmoDB</a>
                `;
            }
            
            let searchId = (plasmodbId && plasmodbId !== "undefined") ? plasmodbId : uniprotId;
            extraLinks += `
                <span style="margin: 0 10px; color: #555;">|</span>
                <a href="genome.html?search=${searchId}" target="_blank" style="display: inline-block; background: #64b5f6; color: #121212; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 0.9em; box-shadow: 0 2px 4px rgba(0,0,0,0.3); transition: 0.2s;">🧬 View in Genome Browser</a>
            `;

            document.getElementById('modal-meta').innerHTML = `
                <span style="color: #aaa; font-weight: bold;">Location: ${location}</span>
                <span style="margin: 0 5px; color: #555;">|</span>
                <a href="https://www.uniprot.org/uniprotkb/${uniprotId}/entry" target="_blank" style="color: #64b5f6; text-decoration: none;">🔗 View on UniProt</a>
                ${extraLinks}
            `;

            document.getElementById('status').innerText = "Loading structure data...";

            if (!viewer) {
                viewer = $3Dmol.createViewer(document.getElementById('viewer_div'), { backgroundColor: '#121212' });
            } else {
                viewer.clear();
            }

            let script = document.createElement('script');
            script.src = jsPath;
            script.id = 'temp-pdb-script';
            if(document.getElementById('temp-pdb-script')) document.getElementById('temp-pdb-script').remove();
            document.body.appendChild(script);
        }

        window.receivePDBData = function(uid, pdbData) {
            document.getElementById('status').innerText = "";
            viewer.addModel(pdbData, "pdb");
            let colorAlphaFold = (atom) => {
                if(atom.b > 90) return '#0053d6'; 
                if(atom.b > 70) return '#65cbf3'; 
                if(atom.b > 50) return '#ffdb13'; 
                return '#ff7d45'; 
            };
            viewer.setStyle({}, {cartoon: {colorfunc: colorAlphaFold}});
            viewer.zoomTo();
            viewer.render();
        };

        function closeViewer() {
            document.getElementById('modal').style.display = 'none';
            if (viewer) viewer.clear();
        }
        
        const observer = new IntersectionObserver(entries => {
            if(entries[0].isIntersecting) {
                renderChunk();
            }
        }, { rootMargin: "300px" }); 

        window.addEventListener('DOMContentLoaded', () => {
            renderChunk();
            observer.observe(document.getElementById('sentinel'));
        });
    </script>
</body>
</html>
"""

html_content = html_template.replace("__JSON_DATA_HERE__", json_data_string)

with open(output_html, "w", encoding='utf-8') as f:
    f.write(html_content)

print(f"Spatial Atlas created successfully at: {output_html}")
