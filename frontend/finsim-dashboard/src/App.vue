<template>
  <div style="display:flex;min-height:100vh;background:#EEF2F7;font-family:'IBM Plex Sans',system-ui,sans-serif;color:#0E1B2E;">

    <aside style="width:200px;flex:none;background:#0E2238;color:#C7D5E6;display:flex;flex-direction:column;padding:18px 0 16px;position:sticky;top:0;height:100vh;">
      <div style="display:flex;align-items:center;gap:10px;padding:0 18px 22px;">
        <span style="width:28px;height:28px;border-radius:6px;display:grid;place-items:center;background:#1FA463;color:#06231A;font-weight:600;font-size:16px;">F</span>
        <span style="font-size:17px;letter-spacing:.02em;color:#F2F6FB;">FIN<b style="color:#1FA463;font-weight:600;">sim</b></span>
      </div>

      <div style="padding:0 12px;margin-bottom:20px;">
        <p style="margin:0 0 6px;padding:0 8px;font-size:10px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#5E748F;">Vista</p>
        <button v-for="v in viewButtons" :key="v.id" @click="view = v.id" :style="getBtnStyle(view === v.id)">
          {{ v.label }}
        </button>
      </div>

      <div style="padding:0 12px;margin-bottom:20px;">
        <p style="margin:0 0 6px;padding:0 8px;font-size:10px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#5E748F;">Scenario</p>
        <button v-for="s in scenarioPills" :key="s.id" @click="scenario = s.id" :style="getBtnStyle(scenario === s.id, true)">
          <span :style="{ fontSize: '10px', width: '20px', color: scenario === s.id ? '#FFFFFF' : '#1FA463', fontWeight: 'bold' }">{{ s.id }}</span>
          <span>{{ s.label }}</span>
        </button>
      </div>

      <div style="margin-top:auto;padding:14px 18px 0;font-size:11px;color:#5E748F;display:flex;align-items:center;gap:7px;">
        <span style="width:7px;height:7px;border-radius:999px;background:#1FA463;box-shadow:0 0 0 3px rgba(31,164,99,.2);"></span>
        Motore agenti attivo
      </div>
    </aside>

    <div style="flex:1;min-width:0;display:flex;flex-direction:column;">

      <header style="height:56px;flex:none;position:sticky;top:0;z-index:10;display:flex;align-items:center;gap:20px;padding:0 22px;background:#fff;border-bottom:1px solid #DCE3ED;">
        <div style="flex:1;max-width:420px;display:flex;align-items:center;gap:8px;height:36px;padding:0 11px;background:#F7F9FC;border:1px solid #DCE3ED;border-radius:6px;">
          <span style="color:#8593A8;font-size:16px;">⌕</span>
          <span style="flex:1;font-size:13px;color:#8593A8;">Chiedi a FINsim — «perché S2 ha tanti rifiuti?»</span>
        </div>
        <div style="margin-left:auto;display:flex;align-items:center;gap:18px;">
          <span style="font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#8593A8;">Meteo finanziario</span>
          <div style="display:flex;flex-direction:column;line-height:1.15;"><span style="font-size:10px;color:#8593A8;">Tasso BCE</span><b style="font-size:13px;font-weight:500;">3.25%</b></div>
          <div style="width:1px;height:24px;background:#DCE3ED;"></div>
          <div style="display:flex;flex-direction:column;line-height:1.15;"><span style="font-size:10px;color:#8593A8;">Direttiva</span><b style="font-size:13px;font-weight:500;color:#2E6FD6;">Difensiva</b></div>
        </div>
      </header>

      <main style="flex:1;padding:20px 22px 40px;display:flex;flex-direction:column;gap:16px;">

        <div v-if="view === 'promotore'" style="display:flex;flex-direction:column;gap:16px;">
          <div style="display:flex;gap:16px;background:#fff;border:1px solid #DCE3ED;border-left:4px solid #178A57;border-radius:10px;padding:18px 20px;box-shadow:0 1px 2px rgba(13,30,55,.06);">
            <div style="flex:1;min-width:0;">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;flex-wrap:wrap;">
                <span style="font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#178A57;">Consiglio strategia · ADAPT</span>
                <span style="font-size:10px;color:#8593A8;">{{ currentAdvice.scenarioTag }}</span>
              </div>
              <div style="font-size:16px;font-weight:600;color:#0E1B2E;line-height:1.35;margin-bottom:6px;">{{ currentAdvice.title }}</div>
              <div style="font-size:13px;color:#4A5A72;line-height:1.5;max-width:760px;">{{ currentAdvice.body }}</div>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;">
            <div style="position:relative;background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px 14px;overflow:hidden;box-shadow:0 1px 2px rgba(13,30,55,.06);"><div style="position:absolute;inset:0 0 auto 0;height:3px;background:#178A57;"></div><div style="font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:#8593A8;margin-bottom:10px;">Adeguatezza media</div><div style="display:flex;align-items:baseline;gap:3px;"><span style="font-size:36px;font-weight:500;line-height:1;letter-spacing:-.02em;">80</span><span style="font-size:16px;color:#4A5A72;">%</span></div></div>
            <div style="position:relative;background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px 14px;overflow:hidden;box-shadow:0 1px 2px rgba(13,30,55,.06);"><div style="position:absolute;inset:0 0 auto 0;height:3px;background:#2E6FD6;"></div><div style="font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:#8593A8;margin-bottom:10px;">Benchmark FISSO</div><div style="display:flex;align-items:baseline;gap:3px;"><span style="font-size:36px;font-weight:500;line-height:1;letter-spacing:-.02em;">71</span><span style="font-size:16px;color:#4A5A72;">%</span></div></div>
            <div style="position:relative;background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px 14px;overflow:hidden;box-shadow:0 1px 2px rgba(13,30,55,.06);"><div style="position:absolute;inset:0 0 auto 0;height:3px;background:#178A57;"></div><div style="font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:#8593A8;margin-bottom:10px;">Acceptance rate</div><div style="display:flex;align-items:baseline;gap:3px;"><span style="font-size:36px;font-weight:500;line-height:1;letter-spacing:-.02em;">80</span><span style="font-size:16px;color:#4A5A72;">%</span></div></div>
            <div style="position:relative;background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px 14px;overflow:hidden;box-shadow:0 1px 2px rgba(13,30,55,.06);"><div style="position:absolute;inset:0 0 auto 0;height:3px;background:#14375E;"></div><div style="font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:#8593A8;margin-bottom:10px;">Vantaggio AI</div><div style="display:flex;align-items:baseline;gap:3px;"><span style="font-size:36px;font-weight:500;line-height:1;letter-spacing:-.02em;color:#178A57;">+9</span><span style="font-size:16px;color:#4A5A72;">pt</span></div></div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
            <div style="background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px;box-shadow:0 1px 2px rgba(13,30,55,.06);">
              <div style="font-size:13px;font-weight:600;margin-bottom:2px;">Compliance — 20 round</div>
              <div style="position:relative;height:170px;"><canvas id="pCompliance"></canvas></div>
            </div>
            <div style="background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px;box-shadow:0 1px 2px rgba(13,30,55,.06);">
              <div style="font-size:13px;font-weight:600;margin-bottom:2px;">Accettazioni per scenario</div>
              <div style="position:relative;height:170px;"><canvas id="pAccept"></canvas></div>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1.25fr;gap:16px;">
            <div style="background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px;box-shadow:0 1px 2px rgba(13,30,55,.06);">
              <div style="font-size:13px;font-weight:600;margin-bottom:2px;">ADAPT vs FISSO per scenario</div>
              <div style="position:relative;height:190px;"><canvas id="pAdaptFisso"></canvas></div>
            </div>
            <div style="background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px;box-shadow:0 1px 2px rgba(13,30,55,.06);">
              <div style="font-size:13px;font-weight:600;margin-bottom:10px;">Heatmap cluster clienti</div>
              <div style="display:grid;gap:5px;grid-template-columns:repeat(5,1fr);">
                <div v-for="(c, i) in clusters" :key="i" :style="{ aspectRatio:'1.5', borderRadius:'5px', display:'flex', alignItems:'center', justifyContent:'center', fontSize:'13px', fontWeight:'500', background: c.bg, color: c.fg }">
                  {{ c.value }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="view === 'banca'" style="display:flex;flex-direction:column;gap:16px;">
          
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;">
            <div style="position:relative;background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px 14px;overflow:hidden;box-shadow:0 1px 2px rgba(13,30,55,.06);"><div style="position:absolute;inset:0 0 auto 0;height:3px;background:#178A57;"></div><div style="font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:#8593A8;margin-bottom:10px;">Premio personalizzazione</div><div style="font-size:32px;font-weight:500;line-height:1;color:#178A57;">+€2.4M</div><div style="margin-top:10px;font-size:11px;color:#4A5A72;">vs scenario fisso</div></div>
            <div style="position:relative;background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px 14px;overflow:hidden;box-shadow:0 1px 2px rgba(13,30,55,.06);"><div style="position:absolute;inset:0 0 auto 0;height:3px;background:#14375E;"></div><div style="font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:#8593A8;margin-bottom:10px;">Raccolta netta ADAPT</div><div style="font-size:32px;font-weight:500;line-height:1;">€18.7M</div><div style="margin-top:10px;font-size:11px;color:#4A5A72;">Fisso: €16.3M</div></div>
            <div style="position:relative;background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px 14px;overflow:hidden;box-shadow:0 1px 2px rgba(13,30,55,.06);"><div style="position:absolute;inset:0 0 auto 0;height:3px;background:#178A57;"></div><div style="font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:#8593A8;margin-bottom:10px;">Conv. rate ADAPT</div><div style="display:flex;align-items:baseline;gap:3px;"><span style="font-size:32px;font-weight:500;line-height:1;color:#178A57;">68</span><span style="font-size:15px;color:#4A5A72;">%</span></div><div style="margin-top:10px;font-size:11px;color:#4A5A72;">Fisso: 54%</div></div>
            <div style="position:relative;background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px 14px;overflow:hidden;box-shadow:0 1px 2px rgba(13,30,55,.06);"><div style="position:absolute;inset:0 0 auto 0;height:3px;background:#E0922F;"></div><div style="font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:#8593A8;margin-bottom:10px;">Aderenza direttiva</div><div style="display:flex;align-items:baseline;gap:3px;"><span style="font-size:32px;font-weight:500;line-height:1;color:#9a6209;">82</span><span style="font-size:15px;color:#4A5A72;">%</span></div><div style="margin-top:10px;font-size:11px;color:#4A5A72;">Obiettivo raggiunto</div></div>
          </div>

          <div style="display:grid;grid-template-columns:1.3fr 1fr;gap:16px;">
             <div style="background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px;box-shadow:0 1px 2px rgba(13,30,55,.06);">
              <div style="font-size:13px;font-weight:600;margin-bottom:2px;">Raccolta Netta — Trend 20 round</div>
              <div style="font-size:11px;color:#8593A8;margin-bottom:10px;">A/B comparativo · Adattivo vs Fisso</div>
              <div style="position:relative;height:220px;"><canvas id="bRaccolta"></canvas></div>
            </div>
            
            <div style="background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px;box-shadow:0 1px 2px rgba(13,30,55,.06);">
              <div style="font-size:13px;font-weight:600;margin-bottom:2px;">Aderenza alla Direttiva (Difensiva)</div>
              <div style="font-size:11px;color:#8593A8;margin-bottom:10px;">Portafoglio attuale vs Target direttiva</div>
              <div style="position:relative;height:220px;"><canvas id="bRadar"></canvas></div>
            </div>
          </div>

          <div style="background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px;box-shadow:0 1px 2px rgba(13,30,55,.06);">
            <div style="font-size:13px;font-weight:600;margin-bottom:2px;">Matrice Vendite e Adeguatezza</div>
            <div style="font-size:11px;color:#8593A8;margin-bottom:14px;">Cosa stiamo vendendo, a chi, e con quale grado di compliance normativa.</div>
            
            <table style="width:100%;text-align:left;border-collapse:collapse;font-size:13px;">
              <thead>
                <tr style="border-bottom:2px solid #EEF2F7;color:#8593A8;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;">
                  <th style="padding:10px 8px;font-weight:600;">Prodotto</th>
                  <th style="padding:10px 8px;font-weight:600;">Cluster Principale</th>
                  <th style="padding:10px 8px;font-weight:600;">Volume Raccolto</th>
                  <th style="padding:10px 8px;font-weight:600;text-align:center;">Adeguatezza (Semaforo)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(p, index) in productSales" :key="index" style="border-bottom:1px solid #EEF2F7;">
                  <td style="padding:12px 8px;font-weight:500;color:#0E1B2E;">{{ p.name }}</td>
                  <td style="padding:12px 8px;">
                    <span style="background:#F7F9FC;border:1px solid #DCE3ED;padding:4px 8px;border-radius:6px;font-size:12px;color:#4A5A72;">{{ p.cluster }}</span>
                  </td>
                  <td style="padding:12px 8px;font-weight:600;color:#2E6FD6;">€ {{ p.volume }} M</td>
                  <td style="padding:12px 8px;text-align:center;">
                    <div style="display:flex;align-items:center;justify-content:center;gap:6px;">
                      <span :style="{ 
                        width: '10px', height: '10px', borderRadius: '50%', 
                        background: p.status === 'green' ? '#178A57' : (p.status === 'amber' ? '#E0922F' : '#D64242'),
                        boxShadow: `0 0 0 3px ${p.status === 'green' ? 'rgba(23,138,87,.2)' : (p.status === 'amber' ? 'rgba(224,146,47,.2)' : 'rgba(214,66,66,.2)')}`
                      }"></span>
                      <span style="font-weight:500;width:35px;text-align:right;" :style="{ color: p.status === 'green' ? '#178A57' : (p.status === 'amber' ? '#E0922F' : '#D64242') }">
                        {{ p.adequacy }}%
                      </span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="view === 'cliente'" style="display:flex;flex-direction:column;gap:16px;">
          <div style="display:grid;grid-template-columns:1.25fr 1fr;gap:16px;">
            <div style="background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px;box-shadow:0 1px 2px rgba(13,30,55,.06);">
              <div style="font-size:13px;font-weight:600;margin-bottom:2px;">Traiettoria fiducia — Cliente #4812</div>
              <div style="font-size:11px;color:#8593A8;margin-bottom:10px;">15 round</div>
              <div style="position:relative;height:180px;"><canvas id="cFiducia"></canvas></div>
            </div>
            <div style="background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px;box-shadow:0 1px 2px rgba(13,30,55,.06);">
              <div style="font-size:13px;font-weight:600;margin-bottom:2px;">Profilo vs proposta</div>
              <div style="font-size:11px;color:#8593A8;margin-bottom:10px;">Radar · idoneità</div>
              <div style="position:relative;height:180px;"><canvas id="cRadar"></canvas></div>
            </div>
          </div>
           <div style="background:#fff;border:1px solid #DCE3ED;border-radius:10px;padding:16px 18px;box-shadow:0 1px 2px rgba(13,30,55,.06);">
            <div style="font-size:13px;font-weight:600;margin-bottom:14px;">Macchina della verità — Ragionamento LLM</div>
            <div style="display:flex;align-items:stretch;gap:10px;flex-wrap:wrap;">
              <div style="flex:1;min-width:200px;background:#F7F9FC;border-left:3px solid #7C3AED;padding:12px 14px;">
                <div style="font-size:9px;font-weight:600;color:#7C3AED;margin-bottom:5px;">Ragionamento LLM</div>
                <div style="font-size:12px;color:#0E1B2E;">Tensione alta (72/100) → riduco esposizione azionaria.</div>
              </div>
              <div style="flex:1;min-width:200px;background:#F7F9FC;border-left:3px solid #0284C7;padding:12px 14px;">
                <div style="font-size:9px;font-weight:600;color:#0284C7;margin-bottom:5px;">Proposta individuale</div>
                <div style="font-size:12px;color:#0E1B2E;">BTP 5Y (60%) + Fondo Monetario (30%) + liquidità (10%).</div>
              </div>
              <div style="flex:1;min-width:200px;background:#F7F9FC;border-left:3px solid #1E9E63;padding:12px 14px;">
                <div style="font-size:9px;font-weight:600;color:#1E9E63;margin-bottom:5px;">Risposta cliente</div>
                <div style="font-size:12px;color:#0E1B2E;">Accettazione con riserva. Fiducia misurata +12 punti.</div>
              </div>
            </div>
          </div>
        </div>

      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import Chart from 'chart.js/auto';

// --- STATO ---
const view = ref('banca'); // Impostato su 'banca' di default per mostrarti subito le novità
const scenario = ref('S2');
let chartInstances = [];

// --- DATI STATICI (Mock) ---
const viewButtons = [
  { id: 'promotore', label: 'Promotore' },
  { id: 'banca', label: 'Banca' },
  { id: 'cliente', label: 'Cliente' },
];

const scenarioPills = [
  { id: 'S0', label: 'Base' }, { id: 'S1', label: 'Espansione' }, { id: 'S2', label: 'Rialzo tassi' },
  { id: 'S3', label: 'Stress' }, { id: 'S4', label: 'Recessione' },
];

const adviceMap = {
  S0: { title: 'Mantieni l\'allocazione corrente', body: 'In scenario base la personalizzazione ADAPT genera un vantaggio marginale.' },
  S1: { title: 'Aumenta l\'esposizione equity nei cluster dinamici', body: 'Con sentiment positivo e tassi stabili, i profili dinamici tollerano maggiore equity.' },
  S2: { title: 'Privilegia BTP e monetario', body: 'Con tensione a 72/100 e rialzo tassi, i profili a basso rischio mostrano forte avversione.' },
  S3: { title: 'Attiva modalità difensiva', body: 'Scenario di stress: i cluster con duration elevata sono i più vulnerabili.' },
  S4: { title: 'Massima protezione', body: 'In recessione il benchmark FISSO subisce churn elevato. ADAPT consiglia rotazione su liquidità.' },
};

// Nuovo Mock per Tabella Vendite e Semaforo Adeguatezza
const productSales = [
  { name: 'Fondo Monetario Euro', cluster: 'Conservativi (Lvl 1)', volume: '5.2', adequacy: 95, status: 'green' },
  { name: 'BTP 5Y - Nuova Emissione', cluster: 'Conservativi (Lvl 1-2)', volume: '8.4', adequacy: 88, status: 'green' },
  { name: 'ETF Azionario Globale', cluster: 'Dinamici (Lvl 4-5)', volume: '3.1', adequacy: 62, status: 'amber' },
  { name: 'Bond Corporate High Yield', cluster: 'Bilanciati (Lvl 3)', volume: '1.5', adequacy: 38, status: 'red' },
  { name: 'Polizza Ramo I', cluster: 'Affluent (Lvl 1-3)', volume: '4.8', adequacy: 91, status: 'green' }
];

// --- COMPUTED PROPERTIES ---
const currentAdvice = computed(() => {
  return { ...adviceMap[scenario.value], scenarioTag: `${scenario.value} · ${scenarioPills.find(s => s.id === scenario.value).label}` };
});

const clusters = computed(() => {
  const vals = [88, 82, 75, 70, 65, 91, 85, 79, 73, 68, 78, 72, 66, 58, 48, 62, 54, 44, 32, 22];
  return vals.map(v => {
    let bg = '#D64242', fg = '#FFFFFF';
    if (v >= 85) { bg = '#1E9E63'; fg = '#062017'; }
    else if (v >= 70) { bg = '#7DB85A'; fg = '#10240A'; }
    else if (v >= 55) { bg = '#E0922F'; fg = '#2E1C05'; }
    else if (v >= 42) { bg = '#D9703A'; fg = '#2E1305'; }
    return { value: v + '%', bg, fg };
  });
});

// --- METODI ---
const getBtnStyle = (isActive, isScenario = false) => ({
  display: 'flex', alignItems: 'center', gap: isScenario ? '8px' : '0', width: '100%', 
  padding: isScenario ? '7px 8px' : '8px 8px', marginBottom: '1px',
  border: 0, cursor: 'pointer', borderRadius: '6px', fontFamily: 'inherit', 
  fontSize: isScenario ? '12px' : '13px', textAlign: 'left',
  background: isActive ? 'rgba(31,164,99,.14)' : 'transparent', 
  color: isActive ? '#FFFFFF' : '#C7D5E6',
  boxShadow: isActive ? 'inset 2px 0 0 #1FA463' : 'none'
});

// --- LOGICA GRAFICI ---
const renderCharts = () => {
  chartInstances.forEach(c => c.destroy());
  chartInstances = [];

  const ADAPT = '#178A57', FISSO = '#2E6FD6', LLM = '#7C3AED', TARGET = '#8593A8';
  const baseCfg = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } };
  
  const mkChart = (id, config) => {
    const el = document.getElementById(id);
    if (el) chartInstances.push(new Chart(el, config));
  };

  if (view.value === 'promotore') {
    mkChart('pCompliance', { type: 'line', data: { labels: Array.from({length:20}, (_,i)=>'R'+(i+1)), datasets: [ { data: Array.from({length:20}, ()=>Math.random()*20 + 70), borderColor: ADAPT, tension: 0.3 }, { data: Array.from({length:20}, ()=>80), borderColor: FISSO, borderDash: [5, 4], tension: 0.3 } ] }, options: baseCfg });
    mkChart('pAccept', { type: 'bar', data: { labels: ['S0', 'S1', 'S2', 'S3', 'S4'], datasets: [ { data: [16, 18, 12, 15, 16], backgroundColor: '#1E9E63' }, { data: [3, 1, 8, 5, 4], backgroundColor: '#D64242' } ] }, options: baseCfg });
    mkChart('pAdaptFisso', { type: 'bar', data: { labels: ['S0', 'S1', 'S2', 'S3', 'S4'], datasets: [ { data: [79, 80, 84, 84, 72], backgroundColor: '#1E9E63' }, { data: [80, 78, 71, 67, 70], backgroundColor: FISSO } ] }, options: baseCfg });
  
  } else if (view.value === 'banca') {
    mkChart('bRaccolta', { type: 'line', data: { labels: Array.from({length:20}, (_,i)=>'R'+(i+1)), datasets: [ { data: Array.from({length:20}, ()=>Math.random()*10 + 10), borderColor: ADAPT, tension: 0.4 }, { data: Array.from({length:20}, ()=>Math.random()*5 + 8), borderColor: FISSO, borderDash: [5, 4], tension: 0.4 } ] }, options: baseCfg });
    
    // RADAR CHART AGGIORNATO CON 2 DATASET (Target Direttiva vs Attuale)
    mkChart('bRadar', { 
      type: 'radar', 
      data: { 
        labels: ['Bond Corp', 'Monetario', 'Azionario', 'Illiquidi', 'Gov Bond'], 
        datasets: [
          { label: 'Target Direttiva', data: [80, 90, 20, 10, 85], borderColor: TARGET, borderDash: [4, 4], backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0 },
          { label: 'Portafoglio Attuale', data: [65, 80, 35, 15, 70], borderColor: FISSO, backgroundColor: 'rgba(46,111,214,.18)', borderWidth: 2 }
        ] 
      }, 
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } },
        scales: { r: { suggestedMin: 0, suggestedMax: 100 } }
      } 
    });
  
  } else if (view.value === 'cliente') {
    mkChart('cFiducia', { type: 'line', data: { labels: Array.from({length:15}, (_,i)=>'R'+(i+1)), datasets: [{ data: Array.from({length:15}, ()=>Math.random()*40 + 20), borderColor: LLM, backgroundColor: 'rgba(124,58,237,.10)', fill: true, tension: 0.4 }] }, options: baseCfg });
    mkChart('cRadar', { type: 'radar', data: { labels: ['Rischio', 'Orizz.', 'Liq.', 'Rend.', 'Conosc.'], datasets: [{ data: [30, 70, 80, 45, 55], borderColor: FISSO, backgroundColor: 'rgba(46,111,214,.16)' }, { data: [35, 68, 85, 50, 55], borderColor: ADAPT, backgroundColor: 'rgba(23,138,87,.16)' }] }, options: baseCfg });
  }
};

// --- LIFECYCLE HOOKS ---
onMounted(() => renderCharts());
watch([view, scenario], () => nextTick(() => renderCharts()));
onBeforeUnmount(() => chartInstances.forEach(c => c.destroy()));
</script>

<style>
/* CSS Resets inclusi direttamente per matching 1:1 col mockup */
</style>