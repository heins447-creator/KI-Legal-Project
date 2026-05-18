"""Patch ui03_1 HTML template: add decision buttons and badge-ki"""
import re

path = r'I:\KI_Legal_Project\Scripts\python_runner\ui03_1_anwalts_dreiansicht.py'
with open(path, encoding='utf-8') as f:
    content = f.read()

# --- PATCH 1: Add badge-ki after hinweis-keine-rechtsberatung div ---
old_badge = 'Keine Rechtsberatung – kein verbindliches Ergebnis – keine Beweiswuerdigung</div>'
new_badge = 'Keine Rechtsberatung – kein verbindliches Ergebnis – keine Beweiswuerdigung</div>\n  <span class="badge-ki">KI-generiert</span>'
count = content.count(old_badge)
print(f"Badge occurrences: {count}")
content = content.replace(old_badge, new_badge, 1)

# --- PATCH 2: Add decision-row between AGENTENAUFTRAEGE and AKTIONEN sections ---
old_section = '</section>\n\n<!-- ═══ AKTIONEN ═══ -->'
new_section = '''</section>

<!-- ═══ ENTSCHEIDUNG ═══ -->
<section class="panel entscheidung-panel">
  <h2>Entscheidung</h2>
  <div class="decision-row">
    <button class="btn-accept" onclick="entscheidungTreffen('accept')">&#10004; Annehmen</button>
    <button class="btn-reject" onclick="entscheidungTreffen('reject')">&#10008; Ablehnen</button>
    <button class="btn-hold" onclick="entscheidungTreffen('hold')">&#9881; Zurueckstellen</button>
  </div>
  <div id="entscheidung-status" style="display:none; margin-top:12px; padding:10px; border-radius:8px; font-weight:600;"></div>
</section>

<!-- ═══ AKTIONEN ═══ -->'''
count2 = content.count(old_section)
print(f"AKTIONEN section occurrences: {count2}")
content = content.replace(old_section, new_section, 1)

# --- PATCH 3: Add entscheidungTreffen JS function ---
# Insert before the downloadArbeitsstand function
old_js = "function downloadArbeitsstand() {"
new_js = '''function entscheidungTreffen(typ) {
  const labels = {'accept': 'Angenommen (✔)', 'reject': 'Abgelehnt (✘)', 'hold': 'Zurueckgestellt (⚙)'};
  const statusEl = document.getElementById('entscheidung-status');
  statusEl.style.display = 'block';
  statusEl.textContent = 'Entscheidung: ' + labels[typ] + ' – ' + new Date().toLocaleString();
  if (typ === 'accept') { statusEl.style.background = 'var(--ok-bg)'; statusEl.style.color = 'var(--ok)'; }
  else if (typ === 'reject') { statusEl.style.background = 'var(--danger-bg)'; statusEl.style.color = 'var(--danger-text)'; }
  else { statusEl.style.background = 'var(--hold-bg)'; statusEl.style.color = 'var(--hold-text)'; }

  // In Arbeitsstand-Download integrierbar
  window.__entscheidung = {typ: typ, zeit: new Date().toISOString()};
}

function downloadArbeitsstand() {'''
count3 = content.count(old_js)
print(f"downloadArbeitsstand occurrences: {count3}")
content = content.replace(old_js, new_js, 1)

# --- PATCH 4: Add entscheidung to downloadArbeitsstand ---
old_entry = "notizen: {"
new_entry = '''entscheidung: window.__entscheidung || null,
    notizen: {'''
count4 = content.count(old_entry)
print(f"notizen occurrences: {count4}")
content = content.replace(old_entry, new_entry, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'All patches applied. New length: {len(content)}')
