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
        <div style="display: flex; align-items: center; gap: 20px;">
          <div class="reportistica-buttons">
            <button @click="exportToPDF" class="report-btn pdf-btn" title="Genera report PDF completo con analisi LLM">📄 Esporta PDF</button>
            <button @click="exportToPPTX" class="report-btn pptx-btn" title="Genera presentazione PPTX con grafici e analisi">🎬 Genera PPTX</button>
          </div>
          <button @click="showHelpModal = true" class="help-btn">❓ Guida & Legenda</button>
          <div class="user-profile"></div>
        </div>
      </header>

      <div class="content-area">

        <div v-if="view === 'banca'" class="dashboard-grid">

          <div class="panel advisor-panel" style="grid-column: span 12;">
            <div class="panel-header">
              <h3>🤖 Copilota IA</h3>
            </div>
            <div class="advisor-search-box">
              <input
                v-model="searchQuery"
                @keydown="handleSearchKeydown"
                :disabled="isAdvisorLoading"
                type="text"
                placeholder="Chiedi al Copilota (es: 'Analizza il trend della compliance')..."
                class="advisor-input"
              />
            </div>
            <div class="advisor-quick-pills">
              <button
                v-for="(q, i) in quickQuestions"
                :key="i"
                @click="inviaRichiestaAdvisor(q)"
                :disabled="isAdvisorLoading"
                class="quick-pill"
              >
                {{ q }}
              </button>
            </div>
            <div v-if="isAdvisorLoading" class="advisor-loading">
              <div class="loading-spinner"></div>
              <span>Il Copilota sta analizzando i 200 round storici...</span>
            </div>
            <div v-if="aiResponseBrief && !isAdvisorLoading" class="advisor-response">
              <div class="response-brief"><strong>{{ aiResponseBrief }}</strong></div>
              <div v-if="aiResponseDetail" class="response-detail">{{ aiResponseDetail }}</div>
              <div v-if="aiResponseCharts && aiResponseCharts.length > 0" class="recommended-charts">
                <div class="charts-header">📊 Grafici Consigliati:</div>
                <div class="charts-pills">
                  <div v-for="(chart, idx) in aiResponseCharts" :key="idx" class="chart-pill">
                    <span class="chart-code">{{ chart.codice }}</span>
                    <!-- Canvas dinamico per grafici Chart.js -->
                    <div class="ai-chart-wrapper" v-if="shouldRenderChart(chart.codice)">
                      <canvas :id="'ai-chart-' + idx" style="max-height: 120px;"></canvas>
                    </div>
                    <!-- Fallback per codici non supportati -->
                    <div v-else class="chart-widget-fallback">
                      <div style="font-size: 12px; color: #8593A8; text-align: center; padding: 8px;">
                        📊 {{ chart.codice }}
                      </div>
                    </div>
                    <span class="chart-caption">{{ chart.didascalia }}</span>
                  </div>
                </div>
              </div>
              <div class="advisor-rating">
                <span class="rating-label">Utile?</span>
                <div class="stars">
                  <span v-for="star in 5" :key="star" @click="setAdvisorRating(star)" :class="['star', { active: aiRating >= star }]">★</span>
                </div>
              </div>
            </div>
          </div>

          <div class="regime-card" style="grid-column: span 12;">
            <div class="regime-header">
              <div :class="['status-led', regimeMercato.colorClass]"></div>
              <div class="regime-label">{{ regimeMercato.label }}</div>
            </div>
            <div class="regime-metrics-grid">
              <div class="metric-item">
                <div class="metric-label">TASSO BCE</div>
                <div class="metric-value">{{ regimeMercato.tassoBce }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">INDICE GEORISK</div>
                <div class="metric-value">{{ regimeMercato.tensioneGeo }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">MARKET PULSE</div>
                <div class="metric-value">{{ regimeMercato.marketSentiment }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">REGWATCH COMPLIANCE</div>
                <div class="metric-value">{{ regimeMercato.regWatch }}</div>
              </div>
            </div>
            <div class="regime-note">{{ regimeMercato.client_tip }}</div>
          </div>

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
              <h3>Raccolta Netta — Trend</h3>
            </div>
            <div class="chart-container"><canvas id="bRaccolta"></canvas></div>
            <div class="chart-static-caption">
              <strong>Come leggere:</strong> L'asse X mostra l'evoluzione su <strong>200 Round storici</strong>, l'asse Y la Raccolta Netta Cumulata in milioni di euro. La linea verde (ADAPT) riflette la strategia adattiva, la linea blu (FISSO) il benchmark fisso.
              <strong>Deduzione:</strong> Una divergenza positiva di ADAPT rispetto a FISSO indica che l'approccio personalizzato sta generando maggior valore costante sul lungo periodo. Livelli plateau suggeriscono necessità di ricalibrazione della Direttiva.
            </div>
          </div>

          <div class="panel" style="grid-column: span 4;">
            <div class="panel-header">
              <h3>Target Direttiva vs Attuale</h3>
            </div>
            <div class="chart-container"><canvas id="bRadar"></canvas></div>
            <div class="chart-static-caption">
              <strong>Come leggere:</strong> Questo grafico radar mostra 5 dimensioni strategiche (Bond Corporate, Monetario, Azionario, Illiquidi, Gov Bond). La linea grigia tratteggiata rappresenta il Target della Direttiva, la linea blu il Portafoglio Effettivo.
              <strong>Deduzione:</strong> Quando il blu è dentro il grigio, il portafoglio è allineato. Sporgenze indicano sovraesposizioni; rientranze indicano sottodimensionamenti rispetto alla strategia pianificata.
            </div>
          </div>
        </div>

        <div v-if="view === 'promotore'" class="dashboard-grid">

          <div class="panel advisor-panel" style="grid-column: span 12;">
            <div class="panel-header">
              <h3>🤖 Copilota IA</h3>
            </div>
            <div class="advisor-search-box">
              <input
                v-model="searchQuery"
                @keydown="handleSearchKeydown"
                :disabled="isAdvisorLoading"
                type="text"
                placeholder="Chiedi al Copilota (es: 'Analizza il trend della compliance')..."
                class="advisor-input"
              />
            </div>
            <div class="advisor-quick-pills">
              <button
                v-for="(q, i) in quickQuestions"
                :key="i"
                @click="inviaRichiestaAdvisor(q)"
                :disabled="isAdvisorLoading"
                class="quick-pill"
              >
                {{ q }}
              </button>
            </div>
            <div v-if="isAdvisorLoading" class="advisor-loading">
              <div class="loading-spinner"></div>
              <span>Il Copilota sta analizzando i 200 round storici...</span>
            </div>
            <div v-if="aiResponseBrief && !isAdvisorLoading" class="advisor-response">
              <div class="response-brief"><strong>{{ aiResponseBrief }}</strong></div>
              <div v-if="aiResponseDetail" class="response-detail">{{ aiResponseDetail }}</div>
              <div v-if="aiResponseCharts && aiResponseCharts.length > 0" class="recommended-charts">
                <div class="charts-header">📊 Grafici Consigliati:</div>
                <div class="charts-pills">
                  <div v-for="(chart, idx) in aiResponseCharts" :key="idx" class="chart-pill">
                    <span class="chart-code">{{ chart.codice }}</span>
                    <!-- Canvas dinamico per grafici Chart.js -->
                    <div class="ai-chart-wrapper" v-if="shouldRenderChart(chart.codice)">
                      <canvas :id="'ai-chart-' + idx" style="max-height: 120px;"></canvas>
                    </div>
                    <!-- Fallback per codici non supportati -->
                    <div v-else class="chart-widget-fallback">
                      <div style="font-size: 12px; color: #8593A8; text-align: center; padding: 8px;">
                        📊 {{ chart.codice }}
                      </div>
                    </div>
                    <span class="chart-caption">{{ chart.didascalia }}</span>
                  </div>
                </div>
              </div>
              <div class="advisor-rating">
                <span class="rating-label">Utile?</span>
                <div class="stars">
                  <span v-for="star in 5" :key="star" @click="setAdvisorRating(star)" :class="['star', { active: aiRating >= star }]">★</span>
                </div>
              </div>
            </div>
          </div>

          <div class="regime-card" style="grid-column: span 12;">
            <div class="regime-header">
              <div :class="['status-led', regimeMercato.colorClass]"></div>
              <div class="regime-label">{{ regimeMercato.label }}</div>
            </div>
            <div class="regime-metrics-grid">
              <div class="metric-item">
                <div class="metric-label">TASSO BCE</div>
                <div class="metric-value">{{ regimeMercato.tassoBce }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">INDICE GEORISK</div>
                <div class="metric-value">{{ regimeMercato.tensioneGeo }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">MARKET PULSE</div>
                <div class="metric-value">{{ regimeMercato.marketSentiment }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">REGWATCH COMPLIANCE</div>
                <div class="metric-value">{{ regimeMercato.regWatch }}</div>
              </div>
            </div>
            <div class="regime-note">{{ regimeMercato.promoter_tip }}</div>
          </div>

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
              <h4 style="color: #8593A8; margin-bottom: 8px; font-size: 12px; text-transform: uppercase;">Commissioni Cumulate</h4>
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

          <!-- ROW 2B: Heatmap Cluster Clienti -->
          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>🔥 Heatmap Cluster Clienti (AUM vs Rischio)</h3></div>
            <div class="heatmap-grid" style="grid-template-columns: repeat(5, 1fr); gap: 4px;">
              <div v-for="(c, i) in clusterHeatmap" :key="i" class="heat-cell" :style="{ backgroundColor: c.bg, color: c.fg }">
                {{ c.value }}
              </div>
            </div>
            <div style="font-size: 11px; color: #8593A8; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(31,164,99,.1);">
              <strong>Legenda:</strong> Verde = ADAPT domina | Rosso = FISSO domina | Valori = % conversione per cluster
            </div>
          </div>

          <!-- ROW 2C: Delta Performance ADAPT vs FISSO -->
          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>📊 Delta Performance (Vantaggio ADAPT)</h3></div>
            <div style="display: flex; flex-direction: column; gap: 14px;">
              <div style="background: rgba(31,164,99,.08); border-left: 3px solid #1FA463; padding: 12px; border-radius: 4px;">
                <div style="font-size: 11px; color: #8593A8; text-transform: uppercase; margin-bottom: 4px;">Commissioni</div>
                <div style="font-size: 20px; font-weight: bold; color: #1FA463;">
                  +€ {{ ((datiPromotore.adapt.commissioni_cumulate - datiPromotore.fisso.commissioni_cumulate) || 0).toLocaleString('it-IT') }}
                </div>
                <div style="font-size: 10px; color: #6b7280; margin-top: 4px;">
                  {{ Math.round(((datiPromotore.adapt.commissioni_cumulate - datiPromotore.fisso.commissioni_cumulate) / (datiPromotore.fisso.commissioni_cumulate || 1)) * 100) }}% superiore
                </div>
              </div>
              <div style="background: rgba(31,164,99,.08); border-left: 3px solid #1FA463; padding: 12px; border-radius: 4px;">
                <div style="font-size: 11px; color: #8593A8; text-transform: uppercase; margin-bottom: 4px;">Conversione</div>
                <div style="font-size: 20px; font-weight: bold; color: #1FA463;">
                  +{{ (datiPromotore.adapt.tasso_conversione_pct - datiPromotore.fisso.tasso_conversione_pct).toFixed(1) }}%
                </div>
                <div style="font-size: 10px; color: #6b7280; margin-top: 4px;">
                  ADAPT {{ datiPromotore.adapt.tasso_conversione_pct }}% vs FISSO {{ datiPromotore.fisso.tasso_conversione_pct }}%
                </div>
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
            <div class="chart-static-caption">
              <strong>Come leggere:</strong> L'asse X mostra i <strong>200 Round</strong>, l'asse Y la percentuale di adeguatezza (0-100%). La linea verde (ADAPT) rappresenta l'approccio personalizzato, la linea blu tratteggiata (FISSO) il benchmark.
              <strong>Deduzione:</strong> Se ADAPT supera FISSO, la strategia adattiva sta migliorando l'allineamento prodotto-cliente. Un trend decrescente suggerisce di rivedere la Direttiva.
            </div>
          </div>

          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>Proposte Accettate per Round</h3></div>
            <div class="chart-container"><canvas id="pAccept"></canvas></div>
            <div class="chart-static-caption">
              <strong>Come leggere:</strong> L'asse X mostra i <strong>200 Round</strong>, l'asse Y il numero di proposte accettate. Le barre verdi (ADAPT) e blu (FISSO) sono sovrapposte per un confronto immediato.
              <strong>Deduzione:</strong> Un volume ADAPT sistematicamente più alto indica maggiore efficacia della strategia personalizzata. Picchi anomali suggeriscono fattori di mercato esterni.
            </div>
          </div>
        </div>

        <div v-if="view === 'cliente'" class="dashboard-grid">

          <div class="panel advisor-panel" style="grid-column: span 12;">
            <div class="panel-header">
              <h3>🤖 Copilota IA</h3>
            </div>
            <div class="advisor-search-box">
              <input
                v-model="searchQuery"
                @keydown="handleSearchKeydown"
                :disabled="isAdvisorLoading"
                type="text"
                placeholder="Chiedi al Copilota (es: 'Analizza il trend della compliance')..."
                class="advisor-input"
              />
            </div>
            <div class="advisor-quick-pills">
              <button
                v-for="(q, i) in quickQuestions"
                :key="i"
                @click="inviaRichiestaAdvisor(q)"
                :disabled="isAdvisorLoading"
                class="quick-pill"
              >
                {{ q }}
              </button>
            </div>
            <div v-if="isAdvisorLoading" class="advisor-loading">
              <div class="loading-spinner"></div>
              <span>Il Copilota sta analizzando i 200 round storici...</span>
            </div>
            <div v-if="aiResponseBrief && !isAdvisorLoading" class="advisor-response">
              <div class="response-brief"><strong>{{ aiResponseBrief }}</strong></div>
              <div v-if="aiResponseDetail" class="response-detail">{{ aiResponseDetail }}</div>
              <div v-if="aiResponseCharts && aiResponseCharts.length > 0" class="recommended-charts">
                <div class="charts-header">📊 Grafici Consigliati:</div>
                <div class="charts-pills">
                  <div v-for="(chart, idx) in aiResponseCharts" :key="idx" class="chart-pill">
                    <span class="chart-code">{{ chart.codice }}</span>
                    <!-- Canvas dinamico per grafici Chart.js -->
                    <div class="ai-chart-wrapper" v-if="shouldRenderChart(chart.codice)">
                      <canvas :id="'ai-chart-' + idx" style="max-height: 120px;"></canvas>
                    </div>
                    <!-- Fallback per codici non supportati -->
                    <div v-else class="chart-widget-fallback">
                      <div style="font-size: 12px; color: #8593A8; text-align: center; padding: 8px;">
                        📊 {{ chart.codice }}
                      </div>
                    </div>
                    <span class="chart-caption">{{ chart.didascalia }}</span>
                  </div>
                </div>
              </div>
              <div class="advisor-rating">
                <span class="rating-label">Utile?</span>
                <div class="stars">
                  <span v-for="star in 5" :key="star" @click="setAdvisorRating(star)" :class="['star', { active: aiRating >= star }]">★</span>
                </div>
              </div>
            </div>
          </div>

          <div class="regime-card" style="grid-column: span 12;">
            <div class="regime-header">
              <div :class="['status-led', regimeMercato.colorClass]"></div>
              <div class="regime-label">{{ regimeMercato.label }}</div>
            </div>
            <div class="regime-metrics-grid">
              <div class="metric-item">
                <div class="metric-label">TASSO BCE</div>
                <div class="metric-value">{{ regimeMercato.tassoBce }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">INDICE GEORISK</div>
                <div class="metric-value">{{ regimeMercato.tensioneGeo }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">MARKET PULSE</div>
                <div class="metric-value">{{ regimeMercato.marketSentiment }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">REGWATCH COMPLIANCE</div>
                <div class="metric-value">{{ regimeMercato.regWatch }}</div>
              </div>
            </div>
            <div class="regime-note">{{ regimeMercato.client_tip }}</div>
          </div>

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
            <div class="chart-static-caption">
              <strong>Come leggere:</strong> L'asse X mostra i <strong>200 Round</strong> storici, l'asse Y la percentuale di fiducia media del cliente (0-100%). La linea viola piena con area sottostante illustra il trend macro nel tempo.
              <strong>Deduzione:</strong> Un trend macro in crescita indica comunicazione efficace e soddisfazione aumentante del cliente. Cali improvvisi segnalano perdite di confidenza dovute a mercati avversi o inadeguatezze percepite nel portafoglio.
            </div>
          </div>

          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>Allineamento Profilo vs Portafoglio</h3></div>
            <div class="chart-container"><canvas id="cRadar"></canvas></div>
            <div class="chart-static-caption">
              <strong>Come leggere:</strong> Questo grafico radar radar mostra 5 dimensioni di preferenza cliente (Rischio, Orizzonte, Liquidità, Rendimento, Conoscenza). La linea blu e la linea verde mostrano rispettivamente lo stato effettivo e quello adattivo.
              <strong>Deduzione:</strong> Quando le aree colorate coincidono, il profilo del cliente è pienamente soddisfatto. Discrepanze suggeriscono necessità di ribilanciamento o comunicazione aggiuntiva circa il razionale delle scelte di portafoglio.
            </div>
          </div>
        </div>

      </div>
    </main>

    <!-- MODAL: Guida & Legenda -->
    <div v-if="showHelpModal" class="help-modal" @click.self="showHelpModal = false">
      <div class="modal-content">
        <button @click="showHelpModal = false" class="modal-close-btn">✕</button>

        <h2 class="modal-title">📚 Guida & Legenda FINsim</h2>

        <div class="modal-section">
          <h3>🎯 Sezione 1: Come Usare la Piattaforma</h3>
          <p><strong>Selezione Scenario:</strong> Usa i pulsanti nella sidebar sinistra per passare tra S0 (Baseline), S1 (Espansione), S2 (Rialzo Tassi), S3 (Stress) e S4 (Biforcazione). Ogni scenario modella un regime macroeconomico diverso.</p>
          <p><strong>Viste Operative:</strong> Puoi passare tra tre viste analitiche:</p>
          <ul>
            <li><strong>Banca:</strong> Dati a livello di istituzione (raccolta netta, portfolio allocation, adeguatezza globale).</li>
            <li><strong>Promotore:</strong> Metriche di performance della strategia ADAPT vs FISSO (conversioni, commissioni, alert).</li>
            <li><strong>Cliente:</strong> Prospettiva del cliente: fiducia, soddisfazione, allineamento profilo.</li>
          </ul>
          <p><strong>Copilota IA:</strong> Poni domande specifiche al Copilota per ricevere analisi tattica personalizzata. Usa le "Pillole Rapide" per domande predefinite. Valuta la risposta con le 5 stelle: se voto ≤ 2, il Copilota rigenerera una risposta alternativa.</p>
        </div>

        <div class="modal-section">
          <h3>🧠 Sezione 2: Leggere i Dati — Concetti Fondamentali</h3>
          <p><strong>200 Round Storici:</strong> FINsim simula 20 round decisionali per 5 scenari (S0-S4), generando 100 interazioni cliente × strategia. Ogni round rappresenta un momento decisionale dove il promotore sceglie un approccio (ADAPT personalizzato o FISSO benchmark).</p>
          <p><strong>Swarm Intelligence (ADAPT):</strong> La strategia ADAPT usa un'IA generativa (Qwen 2.5 32B) per produrre direttive bancarie dinamiche e personalizzate per promotori (Qwen 2.5 3B), rispetto al benchmark FISSO statico. Osserva come ADAPT evolve nel tempo.</p>
          <p><strong>KPI Chiave:</strong></p>
          <ul>
            <li><strong>Tasso di Conversione:</strong> % di proposte accettate dai clienti.</li>
            <li><strong>Commissioni Cumulate:</strong> Ricavi generati (1% su volume 100k€/cliente).</li>
            <li><strong>Fiducia Media:</strong> Sentiment del cliente post-proposta (0-100%).</li>
            <li><strong>Adeguatezza:</strong> Allineamento prodotto-profilo cliente (0-100%).</li>
            <li><strong>Churn Risk / MIFID Alert:</strong> Anomalie di fiducia o adeguatezza che richiedono intervento.</li>
          </ul>
        </div>

        <div class="modal-section">
          <h3>📊 Sezione 3: Legenda Grafici</h3>
          <p><strong>Colori Standard:</strong> Verde (#1FA463) = ADAPT/Positivo, Blu (#2E6FD6) = FISSO/Benchmark, Arancione (#E0922F) = Avvertenza, Rosso (#D64242) = Critico.</p>
          <p><strong>Tipologie Grafici Comuni:</strong></p>
          <ul>
            <li><strong>Linea:</strong> Trend temporale (Round 1-20). Confronto ADAPT vs FISSO su una metrica continua.</li>
            <li><strong>Barre:</strong> Volume o conteggio per categoria. Barre sovrapposte per A/B test ADAPT vs FISSO.</li>
            <li><strong>Radar:</strong> Profilo multi-dimensionale. Area interna = obiettivo/target. Area esterna = attuale/scostamento.</li>
            <li><strong>Heatmap:</strong> Intensità di performance per cluster (asse X: Patrimonio, asse Y: Rischio). Verde = dominio ADAPT, Rosso = dominio FISSO.</li>
          </ul>
          <p><strong>Interpretazione Rapida:</strong> Se una linea sale, la metrica migliora. Se ADAPT supera FISSO, la strategia personalizzata sta vincendo. Picchi anomali suggeriscono shock di mercato; consulta il regime macroeconomico nel panel "Regime di Mercato".</p>
        </div>

        <button @click="showHelpModal = false" class="modal-close-main-btn">Chiudi Guida</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import Chart from 'chart.js/auto';
import html2pdf from 'html2pdf.js';

// --- STATO ---
const view = ref('banca'); // Partiamo dalla vista banca
const scenario = ref('S0'); // Impostiamo a S0 visto che i tuoi dati su Mongo sono S0
let chartInstances = [];
const isAdvisorLoading = ref(false);
const showHelpModal = ref(false);
const aiResponseBrief = ref('');
const aiResponseDetail = ref('');
const aiResponseCharts = ref([]);
const aiRating = ref(0);
const searchQuery = ref('');
let lastUserMessage = '';

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

const quickQuestions = [
  "Quale profilo di rischio sta soffrendo di più?",
  "Spiegami il trend della compliance per questo scenario",
  "Analizza il sentiment di mercato e l'impatto sulle commissioni",
  "Quali sono i rischi principali per la prossima finestra temporale?"
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

const clusterHeatmap = computed(() => {
  const gridSize = 20;
  const rows = 4;
  const cols = 5;
  const data = Array.from({length: gridSize}, () => Math.floor(Math.random() * 100));

  return data.map((val, idx) => {
    let bg, fg;
    if (val >= 80) { bg = '#1E9E63'; fg = '#062017'; }
    else if (val >= 65) { bg = '#7DB85A'; fg = '#10240A'; }
    else if (val >= 50) { bg = '#E0922F'; fg = '#2E1C05'; }
    else if (val >= 35) { bg = '#D9703A'; fg = '#2E1305'; }
    else { bg = '#D64242'; fg = '#FFFFFF'; }

    const row = Math.floor(idx / cols);
    const col = idx % cols;
    const cluster = `C${row+1}R${col+1}`;

    return { value: val + '%', bg, fg, cluster };
  });
});

const regimeMercato = computed(() => {
  const regimes = {
    S0: {
      label: "REGIME DI STABILITÀ (BASSA VOLATILITÀ)",
      colorClass: "status-stable",
      promoter_tip: "Posizionamento neutrale. Ottimizzazione del roll-over sui mandati esistenti.",
      client_tip: "Condizioni di mercato regolari. Il portafoglio segue l'asset allocation strategica programmata.",
      tassoBce: "2.0% (Dopo 8 tagli)",
      tensioneGeo: "78/100 (Crisi Hormuz)",
      marketSentiment: "Ansioso-Laterale",
      regWatch: "Media (MiFID Stabile)"
    },
    S1: {
      label: "ESPANSIONE ECONOMICA (SUPPORTO MONETARIO)",
      colorClass: "status-expansion",
      promoter_tip: "Aggressività misurata su equity e credito. Allungamento scadenze su tassi supportivi.",
      client_tip: "Ciclo favorevole ai mercati. Portafoglio allineato a risk-on moderato con diversificazione.",
      tassoBce: "2.50% (+50bp)",
      tensioneGeo: "78/100 (Crisi Persiste)",
      marketSentiment: "Equity -12% (Spread +80bp)",
      regWatch: "Alta (Prudenza Duration)"
    },
    S2: {
      label: "INASPRIMENTO MONETARIO (DURATION RISK)",
      colorClass: "status-warning",
      promoter_tip: "Ribilanciamento verso scadenze brevi (short-duration) e strumenti a tasso variabile.",
      client_tip: "Fase di aggiustamento dei tassi di interesse. Monitoraggio attivo della componente obbligazionaria.",
      tassoBce: "Sospeso (Incertezza)",
      tensioneGeo: "95/100 (Coinvolgimento NATO)",
      marketSentiment: "Equity -20% / Oro +25%",
      regWatch: "Allerta Straordinaria Consob"
    },
    S3: {
      label: "MARKET SHOCK (ELEVATA VOLATILITÀ)",
      colorClass: "status-critical",
      promoter_tip: "Attivazione protocolli di protezione del capitale. Monitoraggio dei livelli di massimo drawdown.",
      client_tip: "Fase di forte instabilità tecnica dei mercati. Si raccomanda stabilità emotiva e focus sul lungo termine.",
      tassoBce: "2.0% (Stabile)",
      tensioneGeo: "35/100 (Accordo USA-Iran)",
      marketSentiment: "Equity +8% (Rimbalzo Tecnico)",
      regWatch: "Nessuna Restrizione"
    },
    S4: {
      label: "CONTRAZIONE MACROECONOMICA",
      colorClass: "status-recession",
      promoter_tip: "Shift strategico su comparti difensivi, anticiclici e monetari ad alta liquidità.",
      client_tip: "Rallentamento del ciclo economico globale. Portafoglio orientato alla massima resilienza e protezione.",
      tassoBce: "2.0%",
      tensioneGeo: "78/100",
      marketSentiment: "Identico a Baseline (Cambio Direttiva)",
      regWatch: "Media (Ricalibrazione Target)"
    }
  };
  return regimes[scenario.value] || regimes.S0;
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

const handleSearchKeydown = (e) => {
  if (e.key === 'Enter' && !isAdvisorLoading.value) {
    inviaRichiestaAdvisor(searchQuery.value);
  }
};

// --- LOGICA GRAFICI ---
// --- LOGICA GRAFICI ---
const renderCharts = () => {
  chartInstances.forEach(c => c.destroy());
  chartInstances = [];

  const ADAPT = '#178A57', FISSO = '#2E6FD6', LLM = '#7C3AED', TARGET = '#8593A8';
  const baseCfg = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } };
  
  // Configurazione globale per snellire l'asse X sui 200 round
  const xAxisConfig = {
    x: {
      ticks: {
        autoSkip: false,
        callback: function(value, index, values){
          if (index === 0) return 'R1';
          if ((index + 1) % 20 === 0 && index < 199) return 'R' + (index + 1);
          if (index === 199) return 'R200';
          return '';
        },
        color: '#8593A8'
      },
      grid: { display: false }
    }
  };
  
  const mkChart = (id, config) => {
    const el = document.getElementById(id);
    if (el) chartInstances.push(new Chart(el, config));
  };

  if (view.value === 'promotore') {
    // Assicura che i labels arrivino a 200 round
    let promotoreLabels = datiGraficiPromotore.value.labels.length ? datiGraficiPromotore.value.labels : Array.from({length:200}, (_,i)=>'R'+(i+1));
    if (promotoreLabels.length < 200) {
      promotoreLabels = Array.from({length:200}, (_,i)=>promotoreLabels[i] || 'R'+(i+1));
    }

    // Estendi i dati a 200 elementi se necessario
    const extendData = (arr) => {
      if (arr.length >= 200) return arr.slice(0, 200);
      return [...arr, ...Array(200 - arr.length).fill(0)];
    };

    const complianceAdapt = extendData(datiGraficiPromotore.value.compliance_adapt);
    const complianceFisso = extendData(datiGraficiPromotore.value.compliance_fisso);
    const accettateAdapt = extendData(datiGraficiPromotore.value.accettate_adapt);
    const accettateFisso = extendData(datiGraficiPromotore.value.accettate_fisso);

    // COMPLIANCE
    mkChart('pCompliance', {
      type: 'line',
      data: {
        labels: promotoreLabels,
        datasets: [
          { label: 'ADAPT (IA)', data: complianceAdapt.length ? complianceAdapt : Array.from({length:200}, ()=>Math.random()*20 + 70), borderColor: ADAPT, backgroundColor: 'rgba(23,138,87,.05)', fill: true, tension: 0.3, borderWidth: 2 },
          { label: 'FISSO (Benchmark)', data: complianceFisso.length ? complianceFisso : Array.from({length:200}, ()=>80), borderColor: FISSO, borderDash: [5, 4], backgroundColor: 'rgba(46,111,214,.05)', fill: true, tension: 0.3, borderWidth: 2 }
        ]
      },
      options: { ...baseCfg, plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } }, scales: { x: xAxisConfig.x, y: { min: 0, max: 100 } } }
    });

    // ACCETTATE
    mkChart('pAccept', {
      type: 'bar',
      data: {
        labels: promotoreLabels,
        datasets: [
          { label: 'Accettate ADAPT', data: accettateAdapt.length ? accettateAdapt : Array.from({length:200}, ()=>Math.random()*10 + 5), backgroundColor: '#1E9E63' },
          { label: 'Accettate FISSO', data: accettateFisso.length ? accettateFisso : Array.from({length:200}, ()=>Math.random()*5 + 2), backgroundColor: '#2E6FD6' }
        ]
      },
      options: { ...baseCfg, scales: { x: xAxisConfig.x }, plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } } }
    });

  } else if (view.value === 'banca') {
    // Assicura che i labels arrivino a 200 round
    let bancaLabels = trendData.value.labels.length ? trendData.value.labels : Array.from({length:200}, (_,i)=>'R'+(i+1));
    if (bancaLabels.length < 200) {
      bancaLabels = Array.from({length:200}, (_,i)=>bancaLabels[i] || 'R'+(i+1));
    }

    const extendData = (arr) => {
      if (arr.length >= 200) return arr.slice(0, 200);
      return [...arr, ...Array(200 - arr.length).fill(0)];
    };

    const adattivo = extendData(trendData.value.adattivo);
    const fisso = extendData(trendData.value.fisso);

    // RACCOLTA
    mkChart('bRaccolta', {
      type: 'line',
      data: {
        labels: bancaLabels,
        datasets: [
          { data: adattivo.length ? adattivo : Array.from({length:200}, ()=>Math.random()*10 + 10), borderColor: ADAPT, tension: 0.4 },
          { data: fisso.length ? fisso : Array.from({length:200}, ()=>Math.random()*5 + 8), borderColor: FISSO, borderDash: [5, 4], tension: 0.4 }
        ]
      },
      options: { ...baseCfg, scales: { x: xAxisConfig.x } }
    });
    
    // RADAR BANCA (Nessun asse X limitato richiesto qui)
    mkChart('bRadar', { type: 'radar', data: { labels: ['Bond Corp', 'Monetario', 'Azionario', 'Illiquidi', 'Gov Bond'], datasets: [{ label: 'Target Direttiva', data: [80, 90, 20, 10, 85], borderColor: TARGET, borderDash: [4, 4], backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0 }, { label: 'Portafoglio Attuale', data: [65, 80, 35, 15, 70], borderColor: FISSO, backgroundColor: 'rgba(46,111,214,.18)', borderWidth: 2 } ] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } }, scales: { r: { suggestedMin: 0, suggestedMax: 100 } } } });
  
  } else if (view.value === 'cliente') {
    // FIDUCIA - già a 200 round
    const clienteLabels = Array.from({length:200}, (_,i)=>'R'+(i+1));
    mkChart('cFiducia', {
      type: 'line',
      data: {
        labels: clienteLabels,
        datasets: [{ data: Array.from({length:200}, ()=>Math.random()*40 + 20), borderColor: LLM, backgroundColor: 'rgba(124,58,237,.10)', fill: true, tension: 0.4 }]
      },
      options: { ...baseCfg, scales: { x: xAxisConfig.x } }
    });
    
    // RADAR CLIENTE
    mkChart('cRadar', { type: 'radar', data: { labels: ['Rischio', 'Orizz.', 'Liq.', 'Rend.', 'Conosc.'], datasets: [{ data: [30, 70, 80, 45, 55], borderColor: FISSO, backgroundColor: 'rgba(46,111,214,.16)' }, { data: [35, 68, 85, 50, 55], borderColor: ADAPT, backgroundColor: 'rgba(23,138,87,.16)' }] }, options: baseCfg });
  }
};

// --- FUNZIONE PER CHIAMARE LE API CON ERROR HANDLING ROBUSTO ---
const fetchWithTimeout = async (url, timeout = 5000) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);
    return res;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
};

const fetchData = async () => {
  console.log(`[FINsim] Caricamento dati per scenario: ${scenario.value}`);
  const currentScenario = scenario.value;
  const baseURL = 'http://10.12.7.53:8000';

  try {
    // 1. Fetch dati tabella banca (prodotti)
    try {
      console.log('[FINsim] Fetching /api/dati-banca...');
      const resTabella = await fetchWithTimeout(`${baseURL}/api/dati-banca?scenario_id=${currentScenario}`, 8000);
      if (resTabella.ok) {
        const dataTabella = await resTabella.json();
        productSales.value = dataTabella.prodotti || [];
        console.log(`[FINsim] ✓ Prodotti caricati: ${productSales.value.length} items`);
      } else {
        console.warn(`[FINsim] ⚠ Endpoint dati-banca returned ${resTabella.status}`);
      }
    } catch (err) {
      console.error('[FINsim] ✗ Error fetching dati-banca:', err.message);
    }

    // 2. Fetch trend banca
    try {
      console.log('[FINsim] Fetching /api/trend-banca...');
      const resTrend = await fetchWithTimeout(`${baseURL}/api/trend-banca?scenario_id=${currentScenario}`, 8000);
      if (resTrend.ok) {
        const dataTrend = await resTrend.json();
        trendData.value = dataTrend;
        console.log(`[FINsim] ✓ Trend caricato: ${dataTrend.labels?.length || 0} rounds`);
      } else {
        console.warn(`[FINsim] ⚠ Endpoint trend-banca returned ${resTrend.status}`);
      }
    } catch (err) {
      console.error('[FINsim] ✗ Error fetching trend-banca:', err.message);
    }

    // 3. Fetch dati promotore (KPI, performance)
    try {
      console.log('[FINsim] Fetching /api/dati-promotore...');
      const resPromotore = await fetchWithTimeout(`${baseURL}/api/dati-promotore?scenario_id=${currentScenario}`, 8000);
      if (resPromotore.ok) {
        const dataPromo = await resPromotore.json();
        datiPromotore.value = dataPromo;
        console.log(`[FINsim] ✓ Dati promotore caricati: ${dataPromo.adapt?.commissioni_cumulate || 0}€ ADAPT`);
      } else {
        console.warn(`[FINsim] ⚠ Endpoint dati-promotore returned ${resPromotore.status}`);
      }
    } catch (err) {
      console.error('[FINsim] ✗ Error fetching dati-promotore:', err.message);
    }

    // 4. Fetch grafici promotore
    try {
      console.log('[FINsim] Fetching /api/dati-promotore-grafici...');
      const resGrafici = await fetchWithTimeout(`${baseURL}/api/dati-promotore-grafici?scenario_id=${currentScenario}`, 8000);
      if (resGrafici.ok) {
        const dataGrafici = await resGrafici.json();
        datiGraficiPromotore.value = dataGrafici;
        console.log(`[FINsim] ✓ Dati grafici caricati: ${dataGrafici.labels?.length || 0} rounds`);
      } else {
        console.warn(`[FINsim] ⚠ Endpoint dati-promotore-grafici returned ${resGrafici.status}`);
      }
    } catch (err) {
      console.error('[FINsim] ✗ Error fetching dati-promotore-grafici:', err.message);
    }

    console.log(`[FINsim] ✓ Caricamento dati completato`);

  } catch (error) {
    console.error("[FINsim] Errore generale nel caricamento dati:", error);
  }
};

// --- FUNZIONE ADVISOR IA ---
const inviaRichiestaAdvisor = async (messaggioUtente, isRetry = false) => {
  if (!messaggioUtente.trim()) return;

  isAdvisorLoading.value = true;
  aiResponseBrief.value = '';
  aiResponseDetail.value = '';
  aiResponseCharts.value = [];
  aiRating.value = 0;
  lastUserMessage = messaggioUtente;

  try {
    let finalMessage = messaggioUtente;
    if (isRetry) {
      finalMessage = messaggioUtente + " [NOTA: L'utente ha valutato negativamente la risposta. Fornisci un'analisi completamente diversa, più chiara e focalizzati su altri aspetti strategici.]";
    }

    const payload = {
      metrics_data: {
        scenario_corrente: scenario.value,
        commissioni_cumulate_adapt: datiPromotore.value.adapt?.commissioni_cumulate || 0,
        commissioni_cumulate_fisso: datiPromotore.value.fisso?.commissioni_cumulate || 0,
        tasso_conversione_adapt_pct: datiPromotore.value.adapt?.tasso_conversione_pct || 0,
        tasso_conversione_fisso_pct: datiPromotore.value.fisso?.tasso_conversione_pct || 0,
        fiducia_media_adapt: datiPromotore.value.adapt?.fiducia_media || 0,
        fiducia_media_fisso: datiPromotore.value.fisso?.fiducia_media || 0,
        proposte_totali_adapt: datiPromotore.value.adapt?.proposte_totali || 0,
        proposte_totali_fisso: datiPromotore.value.fisso?.proposte_totali || 0,
        churn_risk_count: datiPromotore.value.alerts?.churn_risk_count || 0,
        mifid_alerts_count: datiPromotore.value.alerts?.mifid_alerts_count || 0,
        nota: "Dati aggregati di sintesi. Non includere array di clienti o log estesi."
      },
      user_message: finalMessage
    };

    const res = await fetch('http://10.12.7.53:8000/api/advisor/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      aiResponseBrief.value = data.suggerimento_breve || 'Analisi completata.';
      aiResponseDetail.value = data.dettaglio_risposta || '';
      aiResponseCharts.value = data.grafici_consigliati || [];
    } else {
      aiResponseBrief.value = 'Errore nella richiesta al Copilota. Riprovare.';
    }
  } catch (error) {
    console.error("Errore nella chiamata Advisor:", error);
    aiResponseBrief.value = 'Errore di connessione. Verificare il backend.';
  } finally {
    isAdvisorLoading.value = false;
    searchQuery.value = '';
  }
};

const setAdvisorRating = async (stars) => {
  aiRating.value = stars;
  if (stars <= 2) {
    alert('Risposta insoddisfacente. L\'IA sta rigenerando un\'analisi alternativa...');
    await inviaRichiestaAdvisor(lastUserMessage, true);
  }
};

const shouldRenderChart = (codice) => {
  return ['HEATMAP_PERFORMANCE', 'SEMAFORO_ADEGUATEZZA', 'AREA_GUADAGNI', 'WATERFALL_PATRIMONIO'].includes(codice);
};

let aiChartInstances = [];

const createAICharts = async () => {
  // Pulisci istanze precedenti
  aiChartInstances.forEach(c => {
    if (c && typeof c.destroy === 'function') {
      try { c.destroy(); } catch (e) {}
    }
  });
  aiChartInstances = [];

  await nextTick();

  aiResponseCharts.value.forEach((chart, idx) => {
    if (!shouldRenderChart(chart.codice)) return;

    const canvasId = `ai-chart-${idx}`;
    const el = document.getElementById(canvasId);
    if (!el) return;

    let config = null;

    if (chart.codice === 'HEATMAP_PERFORMANCE') {
      config = {
        type: 'bubble',
        data: {
          labels: ['Cluster 1', 'Cluster 2', 'Cluster 3', 'Cluster 4', 'Cluster 5'],
          datasets: [
            { label: 'ADAPT Win', data: [{ x: 10, y: 20, r: 8 }, { x: 30, y: 25, r: 10 }], backgroundColor: 'rgba(31,164,99,0.5)' },
            { label: 'FISSO Win', data: [{ x: 50, y: 15, r: 7 }, { x: 70, y: 30, r: 9 }], backgroundColor: 'rgba(46,111,214,0.5)' }
          ]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: true } }, scales: { x: { min: 0, max: 100 }, y: { min: 0, max: 100 } } }
      };
    } else if (chart.codice === 'SEMAFORO_ADEGUATEZZA') {
      config = {
        type: 'doughnut',
        data: {
          labels: ['Adeguato', 'Parziale', 'Inadeguato'],
          datasets: [{ data: [60, 25, 15], backgroundColor: ['#16A34A', '#D97706', '#DC2626'] }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
      };
    } else if (chart.codice === 'AREA_GUADAGNI') {
      config = {
        type: 'line',
        data: {
          labels: ['R1', 'R50', 'R100', 'R150', 'R200'],
          datasets: [{
            label: 'Cumulative Gains',
            data: [10, 45, 78, 92, 120],
            borderColor: '#1FA463',
            backgroundColor: 'rgba(31,164,99,0.2)',
            fill: true,
            tension: 0.4
          }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
      };
    } else if (chart.codice === 'WATERFALL_PATRIMONIO') {
      config = {
        type: 'bar',
        data: {
          labels: ['Initial', 'Inflows', 'Outflows', 'Final'],
          datasets: [{ label: 'AUM Change', data: [100, 50, -20, 130], backgroundColor: ['#1FA463', '#7DB85A', '#D64242', '#1FA463'] }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
      };
    }

    if (config) {
      try {
        const instance = new Chart(el, config);
        aiChartInstances.push(instance);
      } catch (e) {
        console.error(`Errore nella creazione di ${canvasId}:`, e);
      }
    }
  });
};

const exportToPDF = async () => {
  try {
    const payload = {
      metrics_data: {
        scenario_corrente: scenario.value,
        commissioni_cumulate_adapt: datiPromotore.value.adapt?.commissioni_cumulate || 0,
        commissioni_cumulate_fisso: datiPromotore.value.fisso?.commissioni_cumulate || 0,
        tasso_conversione_adapt_pct: datiPromotore.value.adapt?.tasso_conversione_pct || 0,
        tasso_conversione_fisso_pct: datiPromotore.value.fisso?.tasso_conversione_pct || 0,
        fiducia_media_adapt: datiPromotore.value.adapt?.fiducia_media || 0,
        fiducia_media_fisso: datiPromotore.value.fisso?.fiducia_media || 0,
        proposte_totali_adapt: datiPromotore.value.adapt?.proposte_totali || 0,
        proposte_totali_fisso: datiPromotore.value.fisso?.proposte_totali || 0,
        churn_risk_count: datiPromotore.value.alerts?.churn_risk_count || 0,
        mifid_alerts_count: datiPromotore.value.alerts?.mifid_alerts_count || 0,
        nota: "Esportazione PDF"
      },
      user_message: aiResponseBrief.value || ""
    };

    const res = await fetch('http://10.12.7.53:8000/api/advisor/export-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `FINsim_Report_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      alert('✅ Report PDF generato con successo!');
    } else {
      alert('❌ Errore nella generazione del PDF');
    }
  } catch (error) {
    console.error("Errore nella generazione PDF:", error);
    alert('Errore di connessione. Verificare il backend.');
  }
};

const exportToPPTX = async () => {
  try {
    const payload = {
      metrics_data: {
        scenario_corrente: scenario.value,
        commissioni_cumulate_adapt: datiPromotore.value.adapt?.commissioni_cumulate || 0,
        commissioni_cumulate_fisso: datiPromotore.value.fisso?.commissioni_cumulate || 0,
        tasso_conversione_adapt_pct: datiPromotore.value.adapt?.tasso_conversione_pct || 0,
        tasso_conversione_fisso_pct: datiPromotore.value.fisso?.tasso_conversione_pct || 0,
        fiducia_media_adapt: datiPromotore.value.adapt?.fiducia_media || 0,
        fiducia_media_fisso: datiPromotore.value.fisso?.fiducia_media || 0,
        proposte_totali_adapt: datiPromotore.value.adapt?.proposte_totali || 0,
        proposte_totali_fisso: datiPromotore.value.fisso?.proposte_totali || 0,
        churn_risk_count: datiPromotore.value.alerts?.churn_risk_count || 0,
        mifid_alerts_count: datiPromotore.value.alerts?.mifid_alerts_count || 0,
        nota: "Esportazione PPTX"
      },
      user_message: aiResponseBrief.value
    };

    const res = await fetch('http://10.12.7.53:8000/api/advisor/export-pptx', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `FINsim_Presentation_${new Date().toISOString().split('T')[0]}.pptx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      alert('✅ Presentazione PPTX generata con successo!');
    } else {
      alert('❌ Errore nella generazione della presentazione');
    }
  } catch (error) {
    console.error("Errore nella generazione PPTX:", error);
    alert('Errore di connessione. Verificare il backend.');
  }
};

// --- LIFECYCLE HOOKS ---
onMounted(async () => {
  console.log('[FINsim] 🚀 App mounted - caricamento dati iniziale...');
  console.log(`[FINsim] Scenario iniziale: ${scenario.value}`);

  await fetchData();

  console.log('[FINsim] ✓ Dati caricati, renderizzazione grafici...');
  await nextTick(() => renderCharts());

  console.log('[FINsim] ✓ Dashboard pronta!');
});

// Quando cambia la vista, ri-renderizza i grafici
watch(view, () => {
  console.log(`[FINsim] 👁️ Vista cambiata a: ${view.value}`);
  nextTick(() => renderCharts());
});

// Quando cambia lo scenario, ricarica TUTTI i dati da MongoDB
watch(scenario, async (newScenario, oldScenario) => {
  console.log(`[FINsim] 🔄 Scenario cambiato: ${oldScenario} → ${newScenario}`);
  console.log('[FINsim] 📊 Ricaricando tutti i dati da MongoDB...');

  // Reset di tutti i dati prima di fare il fetch
  productSales.value = [];
  trendData.value = { labels: [], adattivo: [], fisso: [] };
  datiPromotore.value = {
    status: 'loading',
    adapt: { strategia_consigliata: '', approccio_comunicativo: '', commissioni_cumulate: 0, tasso_conversione_pct: 0, fiducia_media: 0, proposte_totali: 0, tags: [] },
    fisso: { commissioni_cumulate: 0, tasso_conversione_pct: 0, fiducia_media: 0, proposte_totali: 0 },
    risk_profile_breakdown: [],
    product_breakdown: [],
    alerts: { churn_risk_count: 0, mifid_alerts_count: 0 },
    next_best_actions: []
  };
  datiGraficiPromotore.value = { labels: [], compliance_adapt: [], compliance_fisso: [], accettate_adapt: [], accettate_fisso: [] };

  // Fetch dati per il nuovo scenario
  await fetchData();

  // Renderizza i grafici con i nuovi dati
  await nextTick(() => renderCharts());

  console.log(`[FINsim] ✓ Dashboard aggiornata per scenario ${newScenario}`);
});

// Watch sui grafici consigliati dall'IA per renderizzarli dinamicamente
watch(aiResponseCharts, async () => {
  console.log('[FINsim] 📊 Grafici consigliati aggiornati, inizializzo Chart.js...');
  await createAICharts();
}, { deep: true });

onBeforeUnmount(() => {
  chartInstances.forEach(c => c.destroy());
  aiChartInstances.forEach(c => {
    if (c && typeof c.destroy === 'function') {
      try { c.destroy(); } catch (e) {}
    }
  });
});
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

/* Market Regime Indicator */
.regime-card {
  background-color: #111A24;
  border: 1px solid #1C2B3A;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.regime-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-led {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
  animation: pulse-led 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.status-led.status-stable {
  background-color: #16A34A;
  box-shadow: 0 0 10px rgba(22, 163, 74, 0.6);
}

.status-led.status-expansion {
  background-color: #0891B2;
  box-shadow: 0 0 10px rgba(8, 145, 178, 0.6);
}

.status-led.status-warning {
  background-color: #D97706;
  box-shadow: 0 0 10px rgba(217, 119, 6, 0.6);
}

.status-led.status-critical {
  background-color: #DC2626;
  box-shadow: 0 0 10px rgba(220, 38, 38, 0.6);
}

.status-led.status-recession {
  background-color: #1E3A8A;
  box-shadow: 0 0 10px rgba(30, 58, 138, 0.6);
}

.regime-label {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: #FFFFFF;
  flex: 1;
}

.regime-note {
  font-size: 13px;
  color: #8593A8;
  line-height: 1.5;
  font-style: italic;
  border-left: 2px solid rgba(133, 147, 168, 0.4);
  padding-left: 12px;
}

@keyframes pulse-led {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.65;
  }
}

/* Regime Metrics Grid */
.regime-metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 12px 0;
  border-top: 1px solid rgba(28, 43, 58, 0.5);
  border-bottom: 1px solid rgba(28, 43, 58, 0.5);
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metric-item .metric-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: #5C6F86;
}

.metric-item .metric-value {
  font-family: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace;
  font-size: 12px;
  font-weight: 500;
  color: #E2E8F0;
  line-height: 1.4;
}

/* Advisor Panel */
.advisor-panel {
  padding: 16px;
}

.advisor-search-box {
  margin-bottom: 12px;
}

.advisor-input {
  width: 100%;
  padding: 10px 12px;
  background-color: #0B1118;
  border: 1px solid #1C2B3A;
  border-radius: 6px;
  color: #E2E8F0;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.advisor-input::placeholder {
  color: #5C6F86;
}

.advisor-input:focus {
  border-color: #1FA463;
}

.advisor-input:disabled {
  background-color: #0B1118;
  opacity: 0.6;
  cursor: not-allowed;
}

.advisor-quick-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.quick-pill {
  padding: 6px 12px;
  background-color: rgba(31, 164, 99, 0.1);
  border: 1px solid rgba(31, 164, 99, 0.2);
  border-radius: 20px;
  color: #8593A8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.quick-pill:hover:not(:disabled) {
  background-color: rgba(31, 164, 99, 0.15);
  border-color: rgba(31, 164, 99, 0.3);
  color: #1FA463;
}

.quick-pill:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.advisor-loading {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(31, 164, 99, 0.05);
  border-left: 3px solid #1FA463;
  border-radius: 4px;
  color: #1FA463;
  font-size: 13px;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(31, 164, 99, 0.3);
  border-top: 2px solid #1FA463;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.advisor-response {
  padding: 12px;
  background: rgba(31, 164, 99, 0.08);
  border-left: 3px solid #1FA463;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.response-brief {
  color: #E2E8F0;
  font-size: 13px;
  line-height: 1.5;
  font-weight: 500;
}

.response-detail {
  color: #8593A8;
  font-size: 12px;
  line-height: 1.5;
  padding-top: 8px;
  border-top: 1px solid rgba(31, 164, 99, 0.1);
}

/* Didascalie Fisse ai Grafici */
.chart-static-caption {
  font-size: 12px;
  color: #8593A8;
  line-height: 1.6;
  margin-top: 12px;
  padding: 8px 10px;
  background: rgba(31, 164, 99, 0.05);
  border-left: 2px solid #1FA463;
  border-radius: 2px;
}

.chart-static-caption strong {
  color: #1FA463;
  font-weight: 600;
}

/* Grafici Consigliati dall'IA */
.recommended-charts {
  padding-top: 12px;
  border-top: 1px solid rgba(31, 164, 99, 0.1);
  margin-top: 12px;
}

.charts-header {
  font-size: 12px;
  font-weight: 600;
  color: #1FA463;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.charts-pills {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chart-pill {
  background: rgba(31, 164, 99, 0.08);
  border: 1px solid rgba(31, 164, 99, 0.2);
  border-radius: 4px;
  padding: 8px;
  font-size: 11px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chart-code {
  font-weight: 600;
  color: #1FA463;
  font-family: 'JetBrains Mono', monospace;
}

.chart-caption {
  color: #C7D5E6;
  font-size: 11px;
  line-height: 1.4;
  font-style: italic;
}

/* Rating a 5 Stelle */
.advisor-rating {
  padding-top: 12px;
  border-top: 1px solid rgba(31, 164, 99, 0.1);
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.rating-label {
  font-size: 12px;
  color: #8593A8;
  font-weight: 600;
}

.stars {
  display: flex;
  gap: 4px;
}

.star {
  font-size: 18px;
  color: #5C6F86;
  cursor: pointer;
  transition: all 0.2s;
}

.star:hover {
  color: #FFD700;
  transform: scale(1.2);
}

.star.active {
  color: #FFD700;
}

/* Pulsante Guida nella Topbar */
.help-btn {
  background: rgba(31, 164, 99, 0.1);
  border: 1px solid rgba(31, 164, 99, 0.2);
  border-radius: 6px;
  color: #1FA463;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  white-space: nowrap;
}

.help-btn:hover {
  background: rgba(31, 164, 99, 0.15);
  border-color: rgba(31, 164, 99, 0.3);
}

/* Modal Overlay */
.help-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.modal-content {
  background: #111A24;
  border: 1px solid #1C2B3A;
  border-radius: 12px;
  padding: 32px;
  max-width: 700px;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
}

.modal-close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: none;
  border: none;
  color: #8593A8;
  font-size: 20px;
  cursor: pointer;
  transition: color 0.2s;
}

.modal-close-btn:hover {
  color: #FFFFFF;
}

.modal-title {
  color: #FFFFFF;
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 24px;
  letter-spacing: 0.5px;
}

.modal-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(28, 43, 58, 0.5);
}

.modal-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.modal-section h3 {
  color: #1FA463;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 12px;
}

.modal-section p {
  color: #C7D5E6;
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 10px;
}

.modal-section ul {
  list-style-position: inside;
  margin-left: 12px;
}

.modal-section li {
  color: #C7D5E6;
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 6px;
}

.modal-section strong {
  color: #E2E8F0;
  font-weight: 600;
}

.modal-close-main-btn {
  width: 100%;
  background: #1FA463;
  border: none;
  color: #000000;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 16px;
  font-family: inherit;
}

.modal-close-main-btn:hover {
  background: #16A34A;
  transform: translateY(-1px);
}

/* Pulsanti di Esportazione */
.export-buttons {
  padding-top: 12px;
  border-top: 1px solid rgba(31, 164, 99, 0.1);
  margin-top: 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.export-btn {
  flex: 1;
  min-width: 120px;
  background: rgba(31, 164, 99, 0.12);
  border: 1px solid rgba(31, 164, 99, 0.25);
  border-radius: 6px;
  color: #1FA463;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.export-btn:hover {
  background: rgba(31, 164, 99, 0.2);
  border-color: rgba(31, 164, 99, 0.4);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(31, 164, 99, 0.2);
}

.export-btn:active {
  transform: translateY(0);
}

.export-btn.pdf-btn {
  background: rgba(31, 164, 99, 0.12);
  color: #1FA463;
}

.export-btn.pptx-btn {
  background: rgba(255, 213, 0, 0.1);
  border-color: rgba(255, 213, 0, 0.25);
  color: #FFD700;
}

.export-btn.pptx-btn:hover {
  background: rgba(255, 213, 0, 0.15);
  border-color: rgba(255, 213, 0, 0.4);
  box-shadow: 0 4px 12px rgba(255, 213, 0, 0.2);
}

/* Widget Visivi per Grafici Consigliati IA */
.ai-chart-wrapper {
  background: rgba(31, 164, 99, 0.05);
  border: 1px solid rgba(31, 164, 99, 0.2);
  border-radius: 4px;
  padding: 8px;
  margin: 8px 0;
  min-height: 140px;
  max-height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-widget-fallback {
  background: rgba(133, 147, 168, 0.1);
  border: 1px dashed rgba(133, 147, 168, 0.3);
  border-radius: 4px;
  padding: 12px;
  margin: 8px 0;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8593A8;
}

/* Pulsanti Reportistica nella Topbar */
.reportistica-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.report-btn {
  background: rgba(31, 164, 99, 0.12);
  border: 1px solid rgba(31, 164, 99, 0.25);
  border-radius: 6px;
  color: #1FA463;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.report-btn:hover {
  background: rgba(31, 164, 99, 0.2);
  border-color: rgba(31, 164, 99, 0.4);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(31, 164, 99, 0.2);
}

.report-btn:active {
  transform: translateY(0);
}

.report-btn.pdf-btn {
  background: rgba(31, 164, 99, 0.12);
  color: #1FA463;
}

.report-btn.pptx-btn {
  background: rgba(255, 213, 0, 0.1);
  border-color: rgba(255, 213, 0, 0.25);
  color: #FFD700;
}

.report-btn.pptx-btn:hover {
  background: rgba(255, 213, 0, 0.15);
  border-color: rgba(255, 213, 0, 0.4);
  box-shadow: 0 4px 12px rgba(255, 213, 0, 0.2);
}

</style>