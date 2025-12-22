<<<<<<< HEAD

import pandas as pd
import json

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

ARCHIVO_2017 = "BACI_HS17_Y2017_V202501.csv"
ARCHIVO_2023 = "BACI_HS17_Y2023_V202501.csv"
ARCHIVO_PAISES = "country_codes_V202501.csv"
ARCHIVO_PRODUCTOS = "product_codes_HS17_V202501.csv"

CODIGO_PAIS = 320
NOMBRE_PAIS = "Guatemala"
TOP_PRODUCTOS = 10
TOP_DESTINOS = 3

# =============================================================================
# CARGAR DATOS
# =============================================================================

print("Cargando datos...")
trade_2017 = pd.read_csv(ARCHIVO_2017)
trade_2023 = pd.read_csv(ARCHIVO_2023)
countries = pd.read_csv(ARCHIVO_PAISES)
products = pd.read_csv(ARCHIVO_PRODUCTOS)
print(f"2017: {len(trade_2017):,} filas")
print(f"2023: {len(trade_2023):,} filas")

# =============================================================================
# FILTRAR PAÍS
# =============================================================================

pais_2017 = trade_2017[trade_2017['i'] == CODIGO_PAIS]
pais_2023 = trade_2023[trade_2023['i'] == CODIGO_PAIS]

total_2017 = float(pais_2017['v'].sum())
total_2023 = float(pais_2023['v'].sum())

print(f"{NOMBRE_PAIS} 2017: ${total_2017/1000000:.2f}B")
print(f"{NOMBRE_PAIS} 2023: ${total_2023/1000000:.2f}B")

# =============================================================================
# CREAR GRAFO
# =============================================================================

productos_2017 = pais_2017.groupby('k')['v'].sum()
productos_2023 = pais_2023.groupby('k')['v'].sum()
destinos_2017 = pais_2017.groupby('j')['v'].sum()
destinos_2023 = pais_2023.groupby('j')['v'].sum()

top_productos = productos_2023.sort_values(ascending=False).head(TOP_PRODUCTOS).index.tolist()
data_2023 = pais_2023[pais_2023['k'].isin(top_productos)]

def get_producto(codigo):
    r = products[products['code'] == codigo]['description'].values
    return r[0][:28] if len(r) > 0 else str(codigo)

def get_pais(codigo):
    r = countries[countries['country_code'] == codigo]['country_name'].values
    return r[0] if len(r) > 0 else str(codigo)

def cambio(v17, v23):
    if v17 > 0:
        return ((v23/v17)-1)*100
    return 100 if v23 > 0 else 0

nodes = [{
    "id": NOMBRE_PAIS, "group": 1,
    "v2017": total_2017, "v2023": total_2023,
    "cambio": cambio(total_2017, total_2023)
}]
links = []
destinos_agregados = set()

for prod in top_productos:
    nombre = get_producto(prod)
    v17 = float(productos_2017.get(prod, 0))
    v23 = float(productos_2023.get(prod, 0))
    
    nodes.append({"id": nombre, "group": 2, "v2017": v17, "v2023": v23, "cambio": cambio(v17, v23)})
    links.append({"source": NOMBRE_PAIS, "target": nombre, "v2017": v17, "v2023": v23})
    
    dest_prod = data_2023[data_2023['k'] == prod].groupby('j')['v'].sum().sort_values(ascending=False).head(TOP_DESTINOS)
    
    for dest_code, val_23 in dest_prod.items():
        dest_nombre = get_pais(dest_code)
        
        if dest_nombre not in destinos_agregados:
            d17 = float(destinos_2017.get(dest_code, 0))
            d23 = float(destinos_2023.get(dest_code, 0))
            nodes.append({"id": dest_nombre, "group": 3, "v2017": d17, "v2023": d23, "cambio": cambio(d17, d23)})
            destinos_agregados.add(dest_nombre)
        
        l17 = float(pais_2017[(pais_2017['k']==prod) & (pais_2017['j']==dest_code)]['v'].sum())
        links.append({"source": nombre, "target": dest_nombre, "v2017": l17, "v2023": float(val_23)})

graph_data = {"nodes": nodes, "links": links}
print(f"Nodos: {len(nodes)}, Enlaces: {len(links)}")

# =============================================================================
# GENERAR HTML
# =============================================================================

html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>''' + NOMBRE_PAIS + ''': Comercio 2017-2023</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0f1a; min-height: 100vh; color: #e2e8f0; overflow: hidden; }
        .header { position: fixed; top: 0; left: 0; right: 0; padding: 20px 40px; background: linear-gradient(180deg, rgba(10,15,26,1) 0%, rgba(10,15,26,0) 100%); z-index: 100; display: flex; justify-content: space-between; align-items: center; }
        h1 { font-size: 32px; background: linear-gradient(90deg, #f97316, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { color: #64748b; font-size: 14px; }
        .toggle-container { background: #1e293b; border-radius: 16px; padding: 8px; display: flex; gap: 8px; }
        .toggle-btn { padding: 16px 40px; border: none; border-radius: 12px; font-size: 24px; font-weight: 800; cursor: pointer; transition: all 0.4s; background: transparent; color: #64748b; }
        .toggle-btn.active-2017 { background: linear-gradient(135deg, #f97316, #ea580c); color: white; box-shadow: 0 8px 30px rgba(249, 115, 22, 0.5); }
        .toggle-btn.active-2023 { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; box-shadow: 0 8px 30px rgba(59, 130, 246, 0.5); }
        .total-display { text-align: right; }
        .total-label { font-size: 14px; color: #64748b; }
        .total-value { font-size: 48px; font-weight: 800; }
        .info-panel { position: fixed; bottom: 30px; left: 30px; background: rgba(15, 23, 42, 0.95); border-radius: 20px; padding: 30px; border: 2px solid #334155; min-width: 400px; z-index: 100; display: none; }
        .info-panel.active { display: block; }
        .info-panel h3 { font-size: 28px; margin-bottom: 10px; }
        .info-type { font-size: 16px; color: #64748b; margin-bottom: 20px; }
        .info-comparison { display: flex; gap: 30px; align-items: center; }
        .info-year { text-align: center; }
        .info-year-label { font-size: 18px; color: #64748b; margin-bottom: 5px; }
        .info-year-value { font-size: 36px; font-weight: 700; }
        .info-arrow { font-size: 32px; color: #64748b; }
        .info-change { font-size: 42px; font-weight: 800; padding: 15px 25px; border-radius: 12px; }
        .positive { color: #22c55e; background: rgba(34, 197, 94, 0.15); }
        .negative { color: #ef4444; background: rgba(239, 68, 68, 0.15); }
        .legend { position: fixed; bottom: 30px; right: 30px; background: rgba(15, 23, 42, 0.9); border-radius: 16px; padding: 25px; z-index: 100; }
        .legend-title { font-size: 14px; color: #64748b; margin-bottom: 15px; text-transform: uppercase; }
        .legend-item { display: flex; align-items: center; gap: 15px; margin-bottom: 12px; font-size: 18px; }
        .legend-dot { width: 24px; height: 24px; border-radius: 50%; }
        svg { width: 100vw; height: 100vh; }
        .node { cursor: pointer; }
        .node circle { stroke: #0a0f1a; stroke-width: 4px; transition: all 0.5s; }
        .node:hover circle { stroke: #fff; stroke-width: 6px; filter: brightness(1.3); }
        .node.selected circle { stroke: #fbbf24; stroke-width: 6px; }
        .node .label-name { font-size: 18px; fill: #fff; font-weight: 600; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }
        .node .label-change { font-size: 20px; font-weight: 800; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }
        .link { fill: none; stroke-linecap: round; }
        .instructions { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); font-size: 14px; color: #64748b; background: rgba(15, 23, 42, 0.9); padding: 12px 24px; border-radius: 30px; z-index: 100; }
    </style>
</head>
<body>
<div class="header">
    <div><h1>🌐 ''' + NOMBRE_PAIS + ''': Evolución del Comercio</h1><p class="subtitle">Entity Graph 2017 → 2023 | Datos: BACI-CEPII</p></div>
    <div class="toggle-container">
        <button class="toggle-btn active-2017" id="btn2017" onclick="setYear(2017)">2017</button>
        <button class="toggle-btn" id="btn2023" onclick="setYear(2023)">2023</button>
    </div>
    <div class="total-display"><div class="total-label">EXPORTACIONES TOTALES</div><div class="total-value" id="totalValue" style="color:#f97316"></div></div>
</div>
<div class="info-panel" id="infoPanel">
    <h3 id="infoName"></h3><div class="info-type" id="infoType"></div>
    <div class="info-comparison">
        <div class="info-year"><div class="info-year-label">2017</div><div class="info-year-value" id="info2017" style="color:#f97316"></div></div>
        <div class="info-arrow">→</div>
        <div class="info-year"><div class="info-year-label">2023</div><div class="info-year-value" id="info2023" style="color:#3b82f6"></div></div>
        <div class="info-change" id="infoChange"></div>
    </div>
</div>
<div class="legend">
    <div class="legend-title">Leyenda</div>
    <div class="legend-item"><div class="legend-dot" id="leg1"></div> <span>''' + NOMBRE_PAIS + '''</span></div>
    <div class="legend-item"><div class="legend-dot" id="leg2"></div> <span>Productos</span></div>
    <div class="legend-item"><div class="legend-dot" id="leg3"></div> <span>Destinos</span></div>
</div>
<div class="instructions">🖱️ Arrastra nodos · Scroll = zoom · Click = ver cambio</div>
<svg id="graph"></svg>
<script>
const graphData = ''' + json.dumps(graph_data) + ''';
const total2017 = ''' + str(total_2017) + ''';
const total2023 = ''' + str(total_2023) + ''';
let currentYear = 2017;
const colors2017 = {1: "#f97316", 2: "#fb923c", 3: "#fcd34d", link: "#f97316"};
const colors2023 = {1: "#3b82f6", 2: "#60a5fa", 3: "#93c5fd", link: "#3b82f6"};
function formatValue(v) { if (v >= 1000000) return "$" + (v / 1000000).toFixed(2) + "B"; if (v >= 1000) return "$" + (v / 1000).toFixed(0) + "M"; return "$" + v.toFixed(0) + "K"; }
function formatChange(c) { return (c >= 0 ? "+" : "") + c.toFixed(0) + "%"; }
document.getElementById("totalValue").textContent = formatValue(total2017);
const width = window.innerWidth, height = window.innerHeight;
const svg = d3.select("#graph"), g = svg.append("g");
svg.call(d3.zoom().scaleExtent([0.2, 4]).on("zoom", (e) => g.attr("transform", e.transform)));
const nodeScale = d3.scaleSqrt().domain([50000, Math.max(total2017, total2023)]).range([30, 120]);
const linkScale = d3.scaleLinear().domain([10000, 1100000]).range([3, 20]);
const link = g.append("g").selectAll("line").data(graphData.links).join("line").attr("class", "link").attr("stroke", colors2017.link).attr("stroke-width", d => linkScale(d.v2017)).attr("stroke-opacity", 0.35);
const node = g.append("g").selectAll("g").data(graphData.nodes).join("g").attr("class", "node");
node.append("circle").attr("r", d => nodeScale(d.v2017)).attr("fill", d => colors2017[d.group]);
node.append("text").attr("class", "label-name").text(d => d.id.length > 22 ? d.id.slice(0, 20) + "…" : d.id).attr("x", d => nodeScale(d.v2017) + 12).attr("y", -8);
node.append("text").attr("class", "label-change").text(d => formatChange(d.cambio)).attr("x", d => nodeScale(d.v2017) + 12).attr("y", 18).attr("fill", d => d.cambio >= 0 ? "#22c55e" : "#ef4444");
const simulation = d3.forceSimulation(graphData.nodes).force("link", d3.forceLink(graphData.links).id(d => d.id).distance(220).strength(0.5)).force("charge", d3.forceManyBody().strength(-1500)).force("center", d3.forceCenter(width / 2, height / 2)).force("collision", d3.forceCollide().radius(d => nodeScale(Math.max(d.v2017, d.v2023)) + 50));
node.call(d3.drag().on("start", (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }).on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; }).on("end", (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));
simulation.on("tick", () => { link.attr("x1", d => d.source.x).attr("y1", d => d.source.y).attr("x2", d => d.target.x).attr("y2", d => d.target.y); node.attr("transform", d => "translate(" + d.x + "," + d.y + ")"); });
node.on("mouseenter", function(e, d) { link.attr("stroke-opacity", l => (l.source.id === d.id || l.target.id === d.id) ? 0.8 : 0.05); node.select("circle").attr("opacity", n => { if (n.id === d.id) return 1; return graphData.links.some(l => (l.source.id === d.id && l.target.id === n.id) || (l.target.id === d.id && l.source.id === n.id)) ? 1 : 0.1; }); node.selectAll("text").attr("opacity", function() { const n = d3.select(this.parentNode).datum(); if (n.id === d.id) return 1; return graphData.links.some(l => (l.source.id === d.id && l.target.id === n.id) || (l.target.id === d.id && l.source.id === n.id)) ? 1 : 0.1; }); });
node.on("mouseleave", function() { link.attr("stroke-opacity", 0.35); node.select("circle").attr("opacity", 1); node.selectAll("text").attr("opacity", 1); });
node.on("click", function(e, d) { e.stopPropagation(); node.classed("selected", false); d3.select(this).classed("selected", true); document.getElementById("infoPanel").classList.add("active"); const types = {1: "País exportador", 2: "Producto", 3: "Destino"}; document.getElementById("infoName").textContent = d.id; document.getElementById("infoName").style.color = currentYear === 2017 ? colors2017[d.group] : colors2023[d.group]; document.getElementById("infoType").textContent = types[d.group]; document.getElementById("info2017").textContent = formatValue(d.v2017); document.getElementById("info2023").textContent = formatValue(d.v2023); const el = document.getElementById("infoChange"); el.textContent = formatChange(d.cambio); el.className = "info-change " + (d.cambio >= 0 ? "positive" : "negative"); });
svg.on("click", () => { node.classed("selected", false); document.getElementById("infoPanel").classList.remove("active"); });
function setYear(year) { currentYear = year; const colors = year === 2017 ? colors2017 : colors2023; document.getElementById("btn2017").className = "toggle-btn" + (year === 2017 ? " active-2017" : ""); document.getElementById("btn2023").className = "toggle-btn" + (year === 2023 ? " active-2023" : ""); document.getElementById("leg1").style.background = colors[1]; document.getElementById("leg2").style.background = colors[2]; document.getElementById("leg3").style.background = colors[3]; document.getElementById("totalValue").textContent = formatValue(year === 2017 ? total2017 : total2023); document.getElementById("totalValue").style.color = colors[1]; node.select("circle").transition().duration(800).attr("r", d => nodeScale(year === 2017 ? d.v2017 : d.v2023)).attr("fill", d => colors[d.group]); node.select(".label-name").transition().duration(800).attr("x", d => nodeScale(year === 2017 ? d.v2017 : d.v2023) + 12); node.select(".label-change").transition().duration(800).attr("x", d => nodeScale(year === 2017 ? d.v2017 : d.v2023) + 12); link.transition().duration(800).attr("stroke", colors.link).attr("stroke-width", d => linkScale(year === 2017 ? d.v2017 : d.v2023)); simulation.force("collision").radius(d => nodeScale(year === 2017 ? d.v2017 : d.v2023) + 50); simulation.alpha(0.5).restart(); }
document.getElementById("leg1").style.background = colors2017[1]; document.getElementById("leg2").style.background = colors2017[2]; document.getElementById("leg3").style.background = colors2017[3];
</script>
</body>
</html>'''

with open("entity_graph_" + NOMBRE_PAIS.lower() + ".html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✓ Archivo generado: entity_graph_{NOMBRE_PAIS.lower()}.html")
=======

import pandas as pd
import json

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

ARCHIVO_2017 = "BACI_HS17_Y2017_V202501.csv"
ARCHIVO_2023 = "BACI_HS17_Y2023_V202501.csv"
ARCHIVO_PAISES = "country_codes_V202501.csv"
ARCHIVO_PRODUCTOS = "product_codes_HS17_V202501.csv"

CODIGO_PAIS = 320
NOMBRE_PAIS = "Guatemala"
TOP_PRODUCTOS = 10
TOP_DESTINOS = 3

# =============================================================================
# CARGAR DATOS
# =============================================================================

print("Cargando datos...")
trade_2017 = pd.read_csv(ARCHIVO_2017)
trade_2023 = pd.read_csv(ARCHIVO_2023)
countries = pd.read_csv(ARCHIVO_PAISES)
products = pd.read_csv(ARCHIVO_PRODUCTOS)
print(f"2017: {len(trade_2017):,} filas")
print(f"2023: {len(trade_2023):,} filas")

# =============================================================================
# FILTRAR PAÍS
# =============================================================================

pais_2017 = trade_2017[trade_2017['i'] == CODIGO_PAIS]
pais_2023 = trade_2023[trade_2023['i'] == CODIGO_PAIS]

total_2017 = float(pais_2017['v'].sum())
total_2023 = float(pais_2023['v'].sum())

print(f"{NOMBRE_PAIS} 2017: ${total_2017/1000000:.2f}B")
print(f"{NOMBRE_PAIS} 2023: ${total_2023/1000000:.2f}B")

# =============================================================================
# CREAR GRAFO
# =============================================================================

productos_2017 = pais_2017.groupby('k')['v'].sum()
productos_2023 = pais_2023.groupby('k')['v'].sum()
destinos_2017 = pais_2017.groupby('j')['v'].sum()
destinos_2023 = pais_2023.groupby('j')['v'].sum()

top_productos = productos_2023.sort_values(ascending=False).head(TOP_PRODUCTOS).index.tolist()
data_2023 = pais_2023[pais_2023['k'].isin(top_productos)]

def get_producto(codigo):
    r = products[products['code'] == codigo]['description'].values
    return r[0][:28] if len(r) > 0 else str(codigo)

def get_pais(codigo):
    r = countries[countries['country_code'] == codigo]['country_name'].values
    return r[0] if len(r) > 0 else str(codigo)

def cambio(v17, v23):
    if v17 > 0:
        return ((v23/v17)-1)*100
    return 100 if v23 > 0 else 0

nodes = [{
    "id": NOMBRE_PAIS, "group": 1,
    "v2017": total_2017, "v2023": total_2023,
    "cambio": cambio(total_2017, total_2023)
}]
links = []
destinos_agregados = set()

for prod in top_productos:
    nombre = get_producto(prod)
    v17 = float(productos_2017.get(prod, 0))
    v23 = float(productos_2023.get(prod, 0))
    
    nodes.append({"id": nombre, "group": 2, "v2017": v17, "v2023": v23, "cambio": cambio(v17, v23)})
    links.append({"source": NOMBRE_PAIS, "target": nombre, "v2017": v17, "v2023": v23})
    
    dest_prod = data_2023[data_2023['k'] == prod].groupby('j')['v'].sum().sort_values(ascending=False).head(TOP_DESTINOS)
    
    for dest_code, val_23 in dest_prod.items():
        dest_nombre = get_pais(dest_code)
        
        if dest_nombre not in destinos_agregados:
            d17 = float(destinos_2017.get(dest_code, 0))
            d23 = float(destinos_2023.get(dest_code, 0))
            nodes.append({"id": dest_nombre, "group": 3, "v2017": d17, "v2023": d23, "cambio": cambio(d17, d23)})
            destinos_agregados.add(dest_nombre)
        
        l17 = float(pais_2017[(pais_2017['k']==prod) & (pais_2017['j']==dest_code)]['v'].sum())
        links.append({"source": nombre, "target": dest_nombre, "v2017": l17, "v2023": float(val_23)})

graph_data = {"nodes": nodes, "links": links}
print(f"Nodos: {len(nodes)}, Enlaces: {len(links)}")

# =============================================================================
# GENERAR HTML
# =============================================================================

html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>''' + NOMBRE_PAIS + ''': Comercio 2017-2023</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0f1a; min-height: 100vh; color: #e2e8f0; overflow: hidden; }
        .header { position: fixed; top: 0; left: 0; right: 0; padding: 20px 40px; background: linear-gradient(180deg, rgba(10,15,26,1) 0%, rgba(10,15,26,0) 100%); z-index: 100; display: flex; justify-content: space-between; align-items: center; }
        h1 { font-size: 32px; background: linear-gradient(90deg, #f97316, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { color: #64748b; font-size: 14px; }
        .toggle-container { background: #1e293b; border-radius: 16px; padding: 8px; display: flex; gap: 8px; }
        .toggle-btn { padding: 16px 40px; border: none; border-radius: 12px; font-size: 24px; font-weight: 800; cursor: pointer; transition: all 0.4s; background: transparent; color: #64748b; }
        .toggle-btn.active-2017 { background: linear-gradient(135deg, #f97316, #ea580c); color: white; box-shadow: 0 8px 30px rgba(249, 115, 22, 0.5); }
        .toggle-btn.active-2023 { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; box-shadow: 0 8px 30px rgba(59, 130, 246, 0.5); }
        .total-display { text-align: right; }
        .total-label { font-size: 14px; color: #64748b; }
        .total-value { font-size: 48px; font-weight: 800; }
        .info-panel { position: fixed; bottom: 30px; left: 30px; background: rgba(15, 23, 42, 0.95); border-radius: 20px; padding: 30px; border: 2px solid #334155; min-width: 400px; z-index: 100; display: none; }
        .info-panel.active { display: block; }
        .info-panel h3 { font-size: 28px; margin-bottom: 10px; }
        .info-type { font-size: 16px; color: #64748b; margin-bottom: 20px; }
        .info-comparison { display: flex; gap: 30px; align-items: center; }
        .info-year { text-align: center; }
        .info-year-label { font-size: 18px; color: #64748b; margin-bottom: 5px; }
        .info-year-value { font-size: 36px; font-weight: 700; }
        .info-arrow { font-size: 32px; color: #64748b; }
        .info-change { font-size: 42px; font-weight: 800; padding: 15px 25px; border-radius: 12px; }
        .positive { color: #22c55e; background: rgba(34, 197, 94, 0.15); }
        .negative { color: #ef4444; background: rgba(239, 68, 68, 0.15); }
        .legend { position: fixed; bottom: 30px; right: 30px; background: rgba(15, 23, 42, 0.9); border-radius: 16px; padding: 25px; z-index: 100; }
        .legend-title { font-size: 14px; color: #64748b; margin-bottom: 15px; text-transform: uppercase; }
        .legend-item { display: flex; align-items: center; gap: 15px; margin-bottom: 12px; font-size: 18px; }
        .legend-dot { width: 24px; height: 24px; border-radius: 50%; }
        svg { width: 100vw; height: 100vh; }
        .node { cursor: pointer; }
        .node circle { stroke: #0a0f1a; stroke-width: 4px; transition: all 0.5s; }
        .node:hover circle { stroke: #fff; stroke-width: 6px; filter: brightness(1.3); }
        .node.selected circle { stroke: #fbbf24; stroke-width: 6px; }
        .node .label-name { font-size: 18px; fill: #fff; font-weight: 600; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }
        .node .label-change { font-size: 20px; font-weight: 800; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }
        .link { fill: none; stroke-linecap: round; }
        .instructions { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); font-size: 14px; color: #64748b; background: rgba(15, 23, 42, 0.9); padding: 12px 24px; border-radius: 30px; z-index: 100; }
    </style>
</head>
<body>
<div class="header">
    <div><h1>🌐 ''' + NOMBRE_PAIS + ''': Evolución del Comercio</h1><p class="subtitle">Entity Graph 2017 → 2023 | Datos: BACI-CEPII</p></div>
    <div class="toggle-container">
        <button class="toggle-btn active-2017" id="btn2017" onclick="setYear(2017)">2017</button>
        <button class="toggle-btn" id="btn2023" onclick="setYear(2023)">2023</button>
    </div>
    <div class="total-display"><div class="total-label">EXPORTACIONES TOTALES</div><div class="total-value" id="totalValue" style="color:#f97316"></div></div>
</div>
<div class="info-panel" id="infoPanel">
    <h3 id="infoName"></h3><div class="info-type" id="infoType"></div>
    <div class="info-comparison">
        <div class="info-year"><div class="info-year-label">2017</div><div class="info-year-value" id="info2017" style="color:#f97316"></div></div>
        <div class="info-arrow">→</div>
        <div class="info-year"><div class="info-year-label">2023</div><div class="info-year-value" id="info2023" style="color:#3b82f6"></div></div>
        <div class="info-change" id="infoChange"></div>
    </div>
</div>
<div class="legend">
    <div class="legend-title">Leyenda</div>
    <div class="legend-item"><div class="legend-dot" id="leg1"></div> <span>''' + NOMBRE_PAIS + '''</span></div>
    <div class="legend-item"><div class="legend-dot" id="leg2"></div> <span>Productos</span></div>
    <div class="legend-item"><div class="legend-dot" id="leg3"></div> <span>Destinos</span></div>
</div>
<div class="instructions">🖱️ Arrastra nodos · Scroll = zoom · Click = ver cambio</div>
<svg id="graph"></svg>
<script>
const graphData = ''' + json.dumps(graph_data) + ''';
const total2017 = ''' + str(total_2017) + ''';
const total2023 = ''' + str(total_2023) + ''';
let currentYear = 2017;
const colors2017 = {1: "#f97316", 2: "#fb923c", 3: "#fcd34d", link: "#f97316"};
const colors2023 = {1: "#3b82f6", 2: "#60a5fa", 3: "#93c5fd", link: "#3b82f6"};
function formatValue(v) { if (v >= 1000000) return "$" + (v / 1000000).toFixed(2) + "B"; if (v >= 1000) return "$" + (v / 1000).toFixed(0) + "M"; return "$" + v.toFixed(0) + "K"; }
function formatChange(c) { return (c >= 0 ? "+" : "") + c.toFixed(0) + "%"; }
document.getElementById("totalValue").textContent = formatValue(total2017);
const width = window.innerWidth, height = window.innerHeight;
const svg = d3.select("#graph"), g = svg.append("g");
svg.call(d3.zoom().scaleExtent([0.2, 4]).on("zoom", (e) => g.attr("transform", e.transform)));
const nodeScale = d3.scaleSqrt().domain([50000, Math.max(total2017, total2023)]).range([30, 120]);
const linkScale = d3.scaleLinear().domain([10000, 1100000]).range([3, 20]);
const link = g.append("g").selectAll("line").data(graphData.links).join("line").attr("class", "link").attr("stroke", colors2017.link).attr("stroke-width", d => linkScale(d.v2017)).attr("stroke-opacity", 0.35);
const node = g.append("g").selectAll("g").data(graphData.nodes).join("g").attr("class", "node");
node.append("circle").attr("r", d => nodeScale(d.v2017)).attr("fill", d => colors2017[d.group]);
node.append("text").attr("class", "label-name").text(d => d.id.length > 22 ? d.id.slice(0, 20) + "…" : d.id).attr("x", d => nodeScale(d.v2017) + 12).attr("y", -8);
node.append("text").attr("class", "label-change").text(d => formatChange(d.cambio)).attr("x", d => nodeScale(d.v2017) + 12).attr("y", 18).attr("fill", d => d.cambio >= 0 ? "#22c55e" : "#ef4444");
const simulation = d3.forceSimulation(graphData.nodes).force("link", d3.forceLink(graphData.links).id(d => d.id).distance(220).strength(0.5)).force("charge", d3.forceManyBody().strength(-1500)).force("center", d3.forceCenter(width / 2, height / 2)).force("collision", d3.forceCollide().radius(d => nodeScale(Math.max(d.v2017, d.v2023)) + 50));
node.call(d3.drag().on("start", (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }).on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; }).on("end", (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));
simulation.on("tick", () => { link.attr("x1", d => d.source.x).attr("y1", d => d.source.y).attr("x2", d => d.target.x).attr("y2", d => d.target.y); node.attr("transform", d => "translate(" + d.x + "," + d.y + ")"); });
node.on("mouseenter", function(e, d) { link.attr("stroke-opacity", l => (l.source.id === d.id || l.target.id === d.id) ? 0.8 : 0.05); node.select("circle").attr("opacity", n => { if (n.id === d.id) return 1; return graphData.links.some(l => (l.source.id === d.id && l.target.id === n.id) || (l.target.id === d.id && l.source.id === n.id)) ? 1 : 0.1; }); node.selectAll("text").attr("opacity", function() { const n = d3.select(this.parentNode).datum(); if (n.id === d.id) return 1; return graphData.links.some(l => (l.source.id === d.id && l.target.id === n.id) || (l.target.id === d.id && l.source.id === n.id)) ? 1 : 0.1; }); });
node.on("mouseleave", function() { link.attr("stroke-opacity", 0.35); node.select("circle").attr("opacity", 1); node.selectAll("text").attr("opacity", 1); });
node.on("click", function(e, d) { e.stopPropagation(); node.classed("selected", false); d3.select(this).classed("selected", true); document.getElementById("infoPanel").classList.add("active"); const types = {1: "País exportador", 2: "Producto", 3: "Destino"}; document.getElementById("infoName").textContent = d.id; document.getElementById("infoName").style.color = currentYear === 2017 ? colors2017[d.group] : colors2023[d.group]; document.getElementById("infoType").textContent = types[d.group]; document.getElementById("info2017").textContent = formatValue(d.v2017); document.getElementById("info2023").textContent = formatValue(d.v2023); const el = document.getElementById("infoChange"); el.textContent = formatChange(d.cambio); el.className = "info-change " + (d.cambio >= 0 ? "positive" : "negative"); });
svg.on("click", () => { node.classed("selected", false); document.getElementById("infoPanel").classList.remove("active"); });
function setYear(year) { currentYear = year; const colors = year === 2017 ? colors2017 : colors2023; document.getElementById("btn2017").className = "toggle-btn" + (year === 2017 ? " active-2017" : ""); document.getElementById("btn2023").className = "toggle-btn" + (year === 2023 ? " active-2023" : ""); document.getElementById("leg1").style.background = colors[1]; document.getElementById("leg2").style.background = colors[2]; document.getElementById("leg3").style.background = colors[3]; document.getElementById("totalValue").textContent = formatValue(year === 2017 ? total2017 : total2023); document.getElementById("totalValue").style.color = colors[1]; node.select("circle").transition().duration(800).attr("r", d => nodeScale(year === 2017 ? d.v2017 : d.v2023)).attr("fill", d => colors[d.group]); node.select(".label-name").transition().duration(800).attr("x", d => nodeScale(year === 2017 ? d.v2017 : d.v2023) + 12); node.select(".label-change").transition().duration(800).attr("x", d => nodeScale(year === 2017 ? d.v2017 : d.v2023) + 12); link.transition().duration(800).attr("stroke", colors.link).attr("stroke-width", d => linkScale(year === 2017 ? d.v2017 : d.v2023)); simulation.force("collision").radius(d => nodeScale(year === 2017 ? d.v2017 : d.v2023) + 50); simulation.alpha(0.5).restart(); }
document.getElementById("leg1").style.background = colors2017[1]; document.getElementById("leg2").style.background = colors2017[2]; document.getElementById("leg3").style.background = colors2017[3];
</script>
</body>
</html>'''

with open("entity_graph_" + NOMBRE_PAIS.lower() + ".html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✓ Archivo generado: entity_graph_{NOMBRE_PAIS.lower()}.html")
>>>>>>> ceb3c3fc465e34d871a27c49463217a2015eebca
