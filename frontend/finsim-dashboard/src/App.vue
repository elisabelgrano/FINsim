<template>
  <div class="dashboard-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">FINsim</div>
        <div class="version">v2.1 Enterprise</div>
      </div>
      
      <div class="sidebar-section">
        <h4>VISTA OPERATIVA</h4>
        <button 
          v-for="btn in viewButtons" :key="btn.id"
          @click="view = btn.id"
          :style="getBtnStyle(view === btn.id)"
        >
          {{ btn.label }}
        </button>
      </div>

      <div class="sidebar-section" style="margin-top:24px;">
        <h4>SCENARIO ATTIVO</h4>
        <button 
          v-for="s in scenarioPills" :key="s.id"
          @click="scenario = s.id"
          :style="getBtnStyle(scenario === s.id, true)"
        >
          <span class="status-dot" :class="{ active: scenario === s.id }"></span>
          {{ s.label }}
        </button>
      </div>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div class="breadcrumb">Simulazione Base / {{ view.charAt(0).toUpperCase() + view.slice(1) }}</div>
        <div class="user-profile"></div>
      </header>

      <div class="content-area">

        <div v-if="view === 'banca'" class="dashboard-grid">
          
          <div class="panel" style="grid-column: span 12;">
            <div class="panel-header">
              <h3>Matrice Vendite e Adeguatezza</h3>
              <div class="filters"><span>Round 20</span></div>
            </div>
            <div class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Prodotto Proposto</th>
                    <th>Cluster Clienti</th>
                    <th style="text-align:right">Volume (M€)</th>
                    <th style="text-align:right">Adeguatezza</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, i) in productSales" :key="i">
                    <td style="font-weight:500; color:#E2E8F0">{{ item.name }}</td>
                    <td style="color:#8593A8">{{ item.cluster }}</td>
                    <td style="text-align:right; font-family:monospace">{{ item.volume }}</td>
                    <td style="text-align:right">
                      <div class="progress-bar-bg">
                        <div class="progress-bar-fill" :style="{ width: item.adequacy + '%', backgroundColor: item.status === 'green' ? '#1E9E63' : item.status === 'amber' ? '#E0922F' : '#D64242' }"></div>
                      </div>
                      <span style="font-size:12px; margin-left:8px; color:#8593A8">{{ item.adequacy }}%</span>
                    </td>
                    <td><span :class="['status-badge', item.status]"></span></td>
                  </tr>
                  <tr v-if="productSales.length === 0">
                    <td colspan="5" style="text-align: center; color: #8593A8; padding: 20px;">
                      Nessun dato vendite trovato per questo scenario.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="panel" style="grid-column: span 8;">
            <div class="panel-header">
              <h3>Raccolta Netta — Trend 20 round</h3>
            </div>
            <div class="chart-container"><canvas id="bRaccolta"></canvas></div>
          </div>
          
          <div class="panel" style="grid-column: span 4;">
            <div class="panel-header">
              <h3>Target Direttiva vs Attuale</h3>
            </div>
            <div class="chart-container"><canvas id="bRadar"></canvas></div>
          </div>
        </div>

        <div v-if="view === 'promotore'" class="dashboard-grid">

          <!-- ROW 1: Strategia LLM + Commissioni -->
          <div class="panel highlight-panel" style="grid-column: span 8;">
            <div class="panel-header" style="display: flex; justify-content: space-between; align-items: center;">
              <h3><span style="font-size:16px;">🧠</span> Direttiva Strategica LLM (ADAPT-1)</h3>
              <div class="scenario-indicator">
                <span class="status-dot active"></span>
                Scenario: <strong>{{ scenarioPills.find(s => s.id === scenario)?.label || scenario }}</strong>
              </div>
            </div>
            <div class="panel-body strategy-content">
              <div class="tags-container" style="display: flex; gap: 8px; margin-bottom: 4px; flex-wrap: wrap;">
                <span v-for="tag in datiPromotore.adapt.tags" :key="tag" class="strategy-tag">
                  {{ tag }}
                </span>
              </div>
              <div class="strategy-block">
                <h4>Strategia Consigliata</h4>
                <p>{{ datiPromotore.adapt.strategia_consigliata || 'Nessuna strategia generata.' }}</p>
              </div>
              <div class="strategy-block">
                <h4>Approccio Comunicativo</h4>
                <p>{{ datiPromotore.adapt.approccio_comunicativo || 'In attesa di istruzioni...' }}</p>
              </div>
            </div>
          </div>

          <div class="panel highlight-panel" style="grid-column: span 4; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; gap: 16px;">
            <div>
              <h4 style="color: #8593A8; margin-bottom: 8px; font-size: 12px; text-transform: uppercase;">Commissioni Cumulate (20 Round)</h4>
              <div style="font-size: 32px; font-weight: bold; color: #1FA463;">
                € {{ datiPromotore.adapt.commissioni_cumulate.toLocaleString('it-IT') }}
              </div>
            </div>
            <div style="width: 100%; border-top: 1px solid rgba(255,255,255,.1); padding-top: 12px;">
              <p style="font-size: 11px; color: #6b7280;">Commissione 1% | Ticket medio 100k</p>
            </div>
          </div>

          <!-- ROW 2: Next Best Actions + Allarmi Portafoglio -->
          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>📋 Next Best Action</h3></div>
            <div style="display: flex; flex-direction: column; gap: 10px;">
              <div v-for="(action, idx) in datiPromotore.next_best_actions" :key="idx" class="action-item-box">
                {{ action }}
              </div>
              <div v-if="datiPromotore.next_best_actions.length === 0" style="color: #8593A8; font-size: 13px; text-align: center; padding: 20px;">
                Nessun azione consigliata al momento.
              </div>
            </div>
          </div>

          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>🚨 Torre di Controllo Allarmi Portafoglio</h3></div>
            <div style="display: flex; flex-direction: column; gap: 12px;">
              <div class="alarm-badge" :class="{ triggered: datiPromotore.alerts.churn_risk_count > 0 }">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span>⚠️ Rischio Churn</span>
                  <span style="font-size: 18px; font-weight: bold;">{{ datiPromotore.alerts.churn_risk_count }}</span>
                </div>
                <p style="font-size: 11px; margin-top: 4px; opacity: 0.8;">Anomalie fiducia/delta rilevate</p>
              </div>
              <div class="alarm-badge" :class="{ triggered: datiPromotore.alerts.mifid_alerts_count > 0 }">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span>🔒 CONSOB/MIFID Alert</span>
                  <span style="font-size: 18px; font-weight: bold;">{{ datiPromotore.alerts.mifid_alerts_count }}</span>
                </div>
                <p style="font-size: 11px; margin-top: 4px; opacity: 0.8;">Scostamenti adeguatezza</p>
              </div>
            </div>
          </div>

          <!-- ROW 3: Confronto Performance Globale -->
          <div class="panel" style="grid-column: span 12;">
            <div class="panel-header">
              <h3>Confronto Performance: ADAPT (IA) vs FISSO (Benchmark)</h3>
            </div>
            <div class="comparison-grid">
              <div class="metric-card">
                <div class="metric-label">Tasso Conversione</div>
                <div class="metric-values">
                  <div class="adapt-value">{{ datiPromotore.adapt.tasso_conversione_pct }}% <span style="font-size:10px; color:#6b7280;">ADAPT</span></div>
                  <div class="fisso-value">{{ datiPromotore.fisso.tasso_conversione_pct }}% <span style="font-size:10px; color:#6b7280;">FISSO</span></div>
                </div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Fiducia Media Clienti</div>
                <div class="metric-values">
                  <div class="adapt-value">{{ datiPromotore.adapt.fiducia_media }}% <span style="font-size:10px; color:#6b7280;">ADAPT</span></div>
                  <div class="fisso-value">{{ datiPromotore.fisso.fiducia_media }}% <span style="font-size:10px; color:#6b7280;">FISSO</span></div>
                </div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Commissioni Cumulate</div>
                <div class="metric-values">
                  <div class="adapt-value">€ {{ datiPromotore.adapt.commissioni_cumulate.toLocaleString('it-IT') }} <span style="font-size:10px; color:#6b7280;">ADAPT</span></div>
                  <div class="fisso-value">€ {{ datiPromotore.fisso.commissioni_cumulate.toLocaleString('it-IT') }} <span style="font-size:10px; color:#6b7280;">FISSO</span></div>
                </div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Proposte Totali</div>
                <div class="metric-values">
                  <div class="adapt-value">{{ datiPromotore.adapt.proposte_totali }} <span style="font-size:10px; color:#6b7280;">ADAPT</span></div>
                  <div class="fisso-value">{{ datiPromotore.fisso.proposte_totali }} <span style="font-size:10px; color:#6b7280;">FISSO</span></div>
                </div>
              </div>
            </div>
          </div>

          <!-- ROW 4: Due tabelle affiancate -->
          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header">
              <h3>📊 Conversione per Profilo di Rischio</h3>
            </div>
            <div class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Profilo</th>
                    <th style="text-align: center;">ADAPT</th>
                    <th style="text-align: center;">FISSO</th>
                    <th style="text-align: center;">Dominanza</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in datiPromotore.risk_profile_breakdown" :key="idx">
                    <td style="font-weight: 600; color: #E2E8F0; font-size: 12px;">{{ row.profilo }}</td>
                    <td style="text-align: center; color: #1FA463; font-weight: bold; font-size: 12px;">{{ row.adapt_pct }}%</td>
                    <td style="text-align: center; color: #2E6FD6; font-weight: bold; font-size: 12px;">{{ row.fisso_pct }}%</td>
                    <td style="text-align: center;">
                      <span v-if="row.adapt_pct > row.fisso_pct" class="dom-badge adapt-dom">ADAPT</span>
                      <span v-else-if="row.fisso_pct > row.adapt_pct" class="dom-badge fisso-dom">FISSO</span>
                      <span v-else class="dom-badge" style="color: #8593A8;">Parità</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header">
              <h3>📋 Tasso di Accettazione per Prodotto</h3>
            </div>
            <div class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Prodotto</th>
                    <th style="text-align: center;">ADAPT</th>
                    <th style="text-align: center;">FISSO</th>
                    <th style="text-align: center;">Dominanza</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in datiPromotore.product_breakdown" :key="idx">
                    <td style="font-weight: 600; color: #E2E8F0; font-size: 12px;">{{ row.prodotto }}</td>
                    <td style="text-align: center; color: #1FA463; font-weight: bold; font-size: 12px;">{{ row.adapt_pct }}%</td>
                    <td style="text-align: center; color: #2E6FD6; font-weight: bold; font-size: 12px;">{{ row.fisso_pct }}%</td>
                    <td style="text-align: center;">
                      <span v-if="row.adapt_pct > row.fisso_pct" class="dom-badge adapt-dom">ADAPT</span>
                      <span v-else-if="row.fisso_pct > row.adapt_pct" class="dom-badge fisso-dom">FISSO</span>
                      <span v-else class="dom-badge" style="color: #8593A8;">Parità</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ROW 5: Grafici -->
          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>Adeguatezza Media per Round</h3></div>
            <div class="chart-container"><canvas id="pCompliance"></canvas></div>
          </div>

          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>Proposte Accettate per Round</h3></div>
            <div class="chart-container"><canvas id="pAccept"></canvas></div>
          </div>
        </div>

        <div v-if="view === 'cliente'" class="dashboard-grid">
          <div class="panel" style="grid-column: span 12;">
            <div class="panel-header">
              <h3>Heatmap Propensione al Rischio</h3>
            </div>
            <div class="heatmap-grid">
              <div v-for="(c, i) in clusters" :key="i" class="heat-cell" :style="{ backgroundColor: c.bg, color: c.fg }">
                {{ c.value }}
              </div>
            </div>
          </div>

          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>Evoluzione Fiducia</h3></div>
            <div class="chart-container"><canvas id="cFiducia"></canvas></div>
          </div>
          
          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>Allineamento Profilo vs Portafoglio</h3></div>
            <div class="chart-container"><canvas id="cRadar"></canvas></div>
          </div>
        </div>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import Chart from 'chart.js/auto';

// --- STATO ---
const view = ref('banca'); // Partiamo dalla vista banca
const scenario = ref('S0'); // Impostiamo a S0 visto che i tuoi dati su Mongo sono S0
let chartInstances = [];

// --- VARIABILI REATTIVE PER I DATI MONGODB ---
const productSales = ref([]);
const trendData = ref({ labels: [], adattivo: [], fisso: [] });
const datiPromotore = ref({
  status: 'ok',
  adapt: {
    strategia_consigliata: '',
    approccio_comunicativo: '',
    commissioni_cumulate: 0,
    tasso_conversione_pct: 0,
    fiducia_media: 0,
    proposte_totali: 0,
    tags: []
  },
  fisso: {
    commissioni_cumulate: 0,
    tasso_conversione_pct: 0,
    fiducia_media: 0,
    proposte_totali: 0
  },
  risk_profile_breakdown: [],
  product_breakdown: [],
  alerts: {
    churn_risk_count: 0,
    mifid_alerts_count: 0
  },
  next_best_actions: []
});
const datiGraficiPromotore = ref({
  labels: [],
  compliance_adapt: [],
  compliance_fisso: [],
  accettate_adapt: [],
  accettate_fisso: []
});

// --- DATI STATICI (UI Menu) ---
const viewButtons = [
  { id: 'promotore', label: 'Promotore' },
  { id: 'banca', label: 'Banca' },
  { id: 'cliente', label: 'Cliente' },
];

const scenarioPills = [
  { id: 'S0', label: 'Base' }, { id: 'S1', label: 'Espansione' }, { id: 'S2', label: 'Rialzo tassi' },
  { id: 'S3', label: 'Stress' }, { id: 'S4', label: 'Recessione' },
];

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
    // COMPLIANCE: Adeguatezza media per round (ADAPT vs FISSO)
    mkChart('pCompliance', {
      type: 'line',
      data: {
        labels: datiGraficiPromotore.value.labels.length ? datiGraficiPromotore.value.labels : Array.from({length:20}, (_,i)=>'R'+(i+1)),
        datasets: [
          {
            label: 'ADAPT (IA)',
            data: datiGraficiPromotore.value.compliance_adapt.length ? datiGraficiPromotore.value.compliance_adapt : Array.from({length:20}, ()=>Math.random()*20 + 70),
            borderColor: ADAPT,
            backgroundColor: 'rgba(23,138,87,.05)',
            fill: true,
            tension: 0.3,
            borderWidth: 2
          },
          {
            label: 'FISSO (Benchmark)',
            data: datiGraficiPromotore.value.compliance_fisso.length ? datiGraficiPromotore.value.compliance_fisso : Array.from({length:20}, ()=>80),
            borderColor: FISSO,
            borderDash: [5, 4],
            backgroundColor: 'rgba(46,111,214,.05)',
            fill: true,
            tension: 0.3,
            borderWidth: 2
          }
        ]
      },
      options: {
        ...baseCfg,
        plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } },
        scales: { y: { min: 0, max: 100 } }
      }
    });

    // ACCETTATE: Proposte accettate per round (stacked bar ADAPT vs FISSO)
    mkChart('pAccept', {
      type: 'bar',
      data: {
        labels: datiGraficiPromotore.value.labels.length ? datiGraficiPromotore.value.labels : Array.from({length:20}, (_,i)=>'R'+(i+1)),
        datasets: [
          {
            label: 'Accettate ADAPT',
            data: datiGraficiPromotore.value.accettate_adapt.length ? datiGraficiPromotore.value.accettate_adapt : Array.from({length:20}, ()=>Math.random()*10 + 5),
            backgroundColor: '#1E9E63'
          },
          {
            label: 'Accettate FISSO',
            data: datiGraficiPromotore.value.accettate_fisso.length ? datiGraficiPromotore.value.accettate_fisso : Array.from({length:20}, ()=>Math.random()*5 + 2),
            backgroundColor: '#2E6FD6'
          }
        ]
      },
      options: { ...baseCfg, indexAxis: undefined, plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } } }
    });

  } else if (view.value === 'banca') {
    
    // GRAFICO RACCOLTA ALIMENTATO DA MONGODB
    mkChart('bRaccolta', { 
      type: 'line', 
      data: { 
        labels: trendData.value.labels.length ? trendData.value.labels : Array.from({length:20}, (_,i)=>'R'+(i+1)), 
        datasets: [ 
          { data: trendData.value.adattivo.length ? trendData.value.adattivo : Array.from({length:20}, ()=>Math.random()*10 + 10), borderColor: ADAPT, tension: 0.4 }, 
          { data: trendData.value.fisso.length ? trendData.value.fisso : Array.from({length:20}, ()=>Math.random()*5 + 8), borderColor: FISSO, borderDash: [5, 4], tension: 0.4 } 
        ] 
      }, 
      options: baseCfg 
    });
    
    mkChart('bRadar', { type: 'radar', data: { labels: ['Bond Corp', 'Monetario', 'Azionario', 'Illiquidi', 'Gov Bond'], datasets: [{ label: 'Target Direttiva', data: [80, 90, 20, 10, 85], borderColor: TARGET, borderDash: [4, 4], backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0 }, { label: 'Portafoglio Attuale', data: [65, 80, 35, 15, 70], borderColor: FISSO, backgroundColor: 'rgba(46,111,214,.18)', borderWidth: 2 } ] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } }, scales: { r: { suggestedMin: 0, suggestedMax: 100 } } } });
  
  } else if (view.value === 'cliente') {
    mkChart('cFiducia', { type: 'line', data: { labels: Array.from({length:15}, (_,i)=>'R'+(i+1)), datasets: [{ data: Array.from({length:15}, ()=>Math.random()*40 + 20), borderColor: LLM, backgroundColor: 'rgba(124,58,237,.10)', fill: true, tension: 0.4 }] }, options: baseCfg });
    mkChart('cRadar', { type: 'radar', data: { labels: ['Rischio', 'Orizz.', 'Liq.', 'Rend.', 'Conosc.'], datasets: [{ data: [30, 70, 80, 45, 55], borderColor: FISSO, backgroundColor: 'rgba(46,111,214,.16)' }, { data: [35, 68, 85, 50, 55], borderColor: ADAPT, backgroundColor: 'rgba(23,138,87,.16)' }] }, options: baseCfg });
  }
};

// --- FUNZIONE PER CHIAMARE LE API (Aggiornata) ---
const fetchData = async () => {
  try {
    const currentScenario = scenario.value;

    const resTabella = await fetch(`http://10.12.7.53:8000/api/dati-banca?scenario_id=${currentScenario}`);
    if (resTabella.ok) {
      const dataTabella = await resTabella.json();
      productSales.value = dataTabella.prodotti || [];
    }

    const resTrend = await fetch(`http://10.12.7.53:8000/api/trend-banca?scenario_id=${currentScenario}`);
    if (resTrend.ok) {
      const dataTrend = await resTrend.json();
      trendData.value = dataTrend;
    }

    const resPromotore = await fetch(`http://10.12.7.53:8000/api/dati-promotore?scenario_id=${currentScenario}`);
    if (resPromotore.ok) {
      datiPromotore.value = await resPromotore.json();
    }

    const resGrafici = await fetch(`http://10.12.7.53:8000/api/dati-promotore-grafici?scenario_id=${currentScenario}`);
    if (resGrafici.ok) {
      datiGraficiPromotore.value = await resGrafici.json();
    }

  } catch (error) {
    console.error("Errore di connessione a FastAPI:", error);
  }
};

// --- LIFECYCLE HOOKS ---
onMounted(async () => {
  await fetchData();
  renderCharts();
});

// Quando cambia la vista o lo scenario, ricarica i grafici e/o i dati
watch(view, () => nextTick(() => renderCharts()));
watch(scenario, async () => {
  await fetchData(); // Se cambi scenario a sinistra, ri-pesca da Mongo!
  nextTick(() => renderCharts());
});

onBeforeUnmount(() => chartInstances.forEach(c => c.destroy()));
</script>

<style>
/* Reset base e Font */
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0B1118; color: #E2E8F0; font-size: 14px; }

/* Layout Globale */
.dashboard-layout { display: flex; height: 100vh; overflow: hidden; }

/* Sidebar */
.sidebar { width: 260px; background-color: #111A24; border-right: 1px solid #1C2B3A; padding: 24px 16px; display: flex; flex-direction: column; }
.sidebar-header { margin-bottom: 40px; }
.logo { font-size: 20px; font-weight: 700; color: #FFFFFF; letter-spacing: 0.5px; }
.version { font-size: 11px; color: #1FA463; margin-top: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
.sidebar-section h4 { font-size: 11px; color: #5C6F86; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background-color: #314457; transition: background-color 0.2s; }
.status-dot.active { background-color: #1FA463; box-shadow: 0 0 8px rgba(31,164,99,0.4); }

/* Main Content */
.main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.topbar { height: 64px; border-bottom: 1px solid #1C2B3A; display: flex; align-items: center; justify-content: space-between; padding: 0 32px; background-color: #0B1118; }
.breadcrumb { font-size: 14px; color: #8593A8; }
.user-profile { width: 32px; height: 32px; border-radius: 50%; background-color: #1FA463; border: 2px solid #111A24; }

/* Area Contenuto */
.content-area { padding: 32px; overflow-y: auto; height: calc(100vh - 64px); }
.dashboard-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 24px; }

/* Pannelli */
.panel { background-color: #111A24; border: 1px solid #1C2B3A; border-radius: 12px; padding: 20px; display: flex; flex-direction: column; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.panel-header h3 { font-size: 15px; font-weight: 600; color: #FFFFFF; }
.filters span { font-size: 12px; color: #8593A8; background: #1C2B3A; padding: 4px 10px; border-radius: 20px; }

/* Tabelle */
.table-responsive { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; text-align: left; }
.data-table th { color: #5C6F86; font-size: 12px; text-transform: uppercase; padding-bottom: 12px; border-bottom: 1px solid #1C2B3A; font-weight: 600; }
.data-table td { padding: 14px 0; border-bottom: 1px solid #1C2B3A; font-size: 13px; }
.data-table tr:last-child td { border-bottom: none; }

/* Elementi UI (Progress bar, badge, etc) */
.progress-bar-bg { background-color: #1C2B3A; height: 6px; border-radius: 3px; display: inline-block; width: 60px; overflow: hidden; vertical-align: middle; }
.progress-bar-fill { height: 100%; border-radius: 3px; }
.status-badge { display: inline-block; width: 10px; height: 10px; border-radius: 50%; }
.status-badge.green { background-color: #1FA463; box-shadow: 0 0 8px rgba(31,164,99,0.4); }
.status-badge.amber { background-color: #E0922F; box-shadow: 0 0 8px rgba(224,146,47,0.4); }
.status-badge.red { background-color: #D64242; box-shadow: 0 0 8px rgba(214,66,66,0.4); }

/* Heatmap */
.heatmap-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px; }
.heat-cell { padding: 12px; text-align: center; border-radius: 6px; font-size: 13px; font-weight: 600; border: 1px solid rgba(255,255,255,0.05); }

/* Grafici */
.chart-container { height: 260px; position: relative; width: 100%; }

/* --- NUOVE CLASSI PER IL PROMOTORE --- */
.highlight-panel {
  background: linear-gradient(145deg, #111A24 0%, #0B1118 100%);
  border: 1px solid rgba(31, 164, 99, 0.3);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.strategy-content { display: flex; flex-direction: column; gap: 16px; padding: 8px 0; }
.strategy-block h4 { color: #1FA463; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
.strategy-block p {
  color: #E2E8F0; font-size: 14px; line-height: 1.5; font-style: italic;
  border-left: 3px solid #1FA463; padding-left: 12px; background: rgba(31, 164, 99, 0.05); padding: 10px 12px; border-radius: 0 4px 4px 0;
}

/* Griglia di Confronto ADAPT vs FISSO */
.comparison-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  padding: 8px 0;
}

.metric-card {
  background: rgba(31, 164, 99, 0.08);
  border: 1px solid rgba(31, 164, 99, 0.2);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.metric-card .metric-label {
  font-size: 11px;
  color: #8593A8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
  font-weight: 600;
}

.metric-values {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.adapt-value {
  font-size: 18px;
  font-weight: 700;
  color: #1FA463;
}

.fisso-value {
  font-size: 18px;
  font-weight: 700;
  color: #2E6FD6;
}

.scenario-indicator {
  background: rgba(31, 164, 99, 0.1);
  border: 1px solid rgba(31, 164, 99, 0.3);
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  color: #1FA463;
  display: flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Nuovi stili per i componenti avanzati della vista Promotore */
.dom-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
}

.adapt-dom {
  background: rgba(31, 164, 99, 0.15);
  color: #1FA463;
}

.fisso-dom {
  background: rgba(46, 111, 214, 0.15);
  color: #2E6FD6;
}

.action-item-box {
  background: rgba(124, 58, 237, 0.08);
  border: 1px solid rgba(124, 58, 237, 0.2);
  border-radius: 6px;
  padding: 12px;
  color: #E2E8F0;
  font-size: 13px;
  line-height: 1.4;
}

.alarm-badge {
  background: rgba(31, 164, 99, 0.08);
  border: 1px solid rgba(31, 164, 99, 0.2);
  border-radius: 6px;
  padding: 14px;
  color: #E2E8F0;
  font-size: 13px;
}

.alarm-badge.triggered {
  background: rgba(214, 66, 66, 0.12);
  border: 1px solid rgba(214, 66, 66, 0.3);
  color: #F87171;
}

</style>