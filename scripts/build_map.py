# 분석 결과를 슬라이더가 있는 단일 HTML 지도로 만드는 스크립트.
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'

bg = (DATA / 'bg_out.geojson').read_text()
meta = (DATA / 'map_meta.json').read_text()

HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>RxGap · Boston pharmacy deserts</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
 html,body,#map{height:100%;margin:0;font:14px system-ui,sans-serif}
 .panel{position:absolute;top:10px;right:10px;z-index:1000;background:#fff;color:#111;
   padding:12px 14px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.25);width:290px}
 .panel h1{font-size:16px;margin:0 0 6px}
 .sw{display:inline-block;width:12px;height:12px;margin-right:6px;vertical-align:-1px;border:1px solid #555}
 .stat{display:flex;justify-content:space-between;margin:2px 0}
 .note{font-size:11px;color:#555;margin-top:8px;line-height:1.35}
 input[type=range]{width:100%}
</style></head><body>
<div id="map"></div>
<div class="panel" role="region" aria-label="Map controls">
 <h1>Boston pharmacy deserts</h1>
 <label for="r"><b>Walk limit: <span id="rl"></span></b></label>
 <input id="r" type="range" min="0" max="RMAX" step="1" value="0" aria-describedby="rl">
 <div class="stat"><span><span class="sw" style="background:#d7301f"></span>Desert</span><span id="n-desert"></span></div>
 <div class="stat"><span><span class="sw" style="background:#fdae61"></span>One closure from desert</span><span id="n-near-desert"></span></div>
 <div class="stat"><span><span class="sw" style="background:#a6d96a"></span>Covered</span><span id="n-covered"></span></div>
 <div class="stat"><span>&#9679; Pharmacy &nbsp; <span style="color:#d7301f">&#10006;</span> Closed</span></div>
 <div class="note" id="note"></div>
</div>
<script>
const BG = __BG__, META = __META__;
const COLORS = {'desert':'#d7301f','near-desert':'#fdae61','covered':'#a6d96a'};
const steps = [{key:'s_state', label:'State rule (1 mi, or 0.5 mi in low-access areas)'}]
  .concat(META.radii.map(r => ({key:'s_'+r, label: r + ' mile' + (r===1?'':'s') + ' for everyone'})));
const map = L.map('map').setView([42.31,-71.08], 12);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
  {attribution:'&copy; OpenStreetMap, &copy; CARTO'}).addTo(map);
let key = 's_state';
const layer = L.geoJSON(BG, {
  style: f => ({color:'#555', weight:.4, fillOpacity:.65, fillColor: COLORS[f.properties[key]]}),
  onEachFeature: (f, l) => l.bindPopup(() => {
    const p = f.properties;
    return `<b>${p.hood || 'Boston'}</b><br>Block group ${p.GEOID}<br>` +
      `Status: <b>${p[key]}</b><br>People: ${p.pop.toLocaleString()}<br>` +
      (p.age65 != null ? `Age 65+: ${p.age65}<br>` : '') +
      (p.nocar_pct != null ? `No car: ${p.nocar_pct}%<br>` : '') +
      `Limited English households: ${p.lim_eng}%<br>Low-access area: ${p.low_access ? 'yes' : 'no'}`;
  })
}).addTo(map);
META.pharmacies.forEach(p => L.circleMarker([p.lat,p.lon],
  {radius:3, color:'#1a3d7c', weight:1, fillOpacity:1}).bindTooltip(p.name || 'Pharmacy').addTo(map));
META.closed.forEach(c => L.marker([+c.lat,+c.lon], {icon: L.divIcon({className:'',
  html:'<div style="color:#d7301f;font-size:22px;font-weight:bold;text-shadow:0 0 3px #fff">&#10006;</div>',
  iconSize:[20,20], iconAnchor:[10,12]})}).bindPopup(`<b>Closed:</b> ${c.name}<br>${c.address}<br>${c.date}`).addTo(map));
function update(i){
  key = steps[i].key; document.getElementById('rl').textContent = steps[i].label;
  layer.setStyle(f => ({fillColor: COLORS[f.properties[key]]}));
  const t = {'desert':0,'near-desert':0,'covered':0}; let all = 0;
  BG.features.forEach(f => { t[f.properties[key]] += f.properties.pop; all += f.properties.pop; });
  for (const s in t) document.getElementById('n-'+s).textContent =
    t[s].toLocaleString() + ' (' + Math.round(t[s]/all*100) + '%)';
}
const slider = document.getElementById('r');
slider.addEventListener('input', e => update(+e.target.value));
update(0);
document.getElementById('note').innerHTML =
  'Desert = under 15% of the block group is within the walk limit of a pharmacy ' +
  '(Mass. Health Policy Commission, DataPoints 31). ' +
  (META.rule === 'state' ? 'Low-access = fewer cars than the state average or &gt;20% poverty (ACS 2022).'
   : '<b>Low-access uses a stand-in:</b> income below the Boston median. The Census car and poverty data is not loaded yet.') +
  ' Pharmacies from OpenStreetMap; some may be missing.';
</script></body></html>
"""

html = (HTML.replace('__BG__', bg).replace('__META__', meta)
        .replace('RMAX', str(len(json.loads(meta)['radii']))))
(ROOT / 'map.html').write_text(html)
print('wrote', ROOT / 'map.html', f'({len(html) // 1024} KB)')
