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

      <div class="sidebar-section" style="margin-top:24px; flex: 1; display: flex; flex-direction: column;">
        <h4>📋 CRONOLOGIA CONVERSAZIONI</h4>
        <div class="conversation-history-scroll">
          <div v-if="conversationHistory.length === 0" style="color: #6B7280; font-size: 12px; text-align: center; padding: 12px;">
            Nessuna domanda ancora...
          </div>
          <div v-for="conv in conversationHistory" :key="conv.id" class="history-item" @click="ripristinaConversazione(conv)">
            <div class="history-time">{{ conv.timestamp }}</div>
            <div class="history-question">{{ conv.question }}</div>
            <div class="history-brief">{{ conv.brief }}</div>
          </div>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div class="breadcrumb">Simulazione Base / {{ view.charAt(0).toUpperCase() + view.slice(1) }}</div>
        <div style="display: flex; align-items: center; gap: 20px;">
          <div class="reportistica-buttons">
            <button @click="exportToPDF" class="report-btn pdf-btn" title="Genera report PDF completo con analisi IA">📄 Esporta PDF</button>
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
              <h3>🤖 Assistente di Analisi Strategica</h3>
            </div>
            <div class="advisor-search-box">
              <input
                v-model="searchQuery"
                @keydown="handleSearchKeydown"
                :disabled="isAdvisorLoading"
                type="text"
                placeholder="Poni una domanda all'Assistente (es: 'Analizza il trend della compliance')..."
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
              <span>L'Assistente sta analizzando i 200 round storici...</span>
            </div>
            <div v-if="aiResponseBrief && !isAdvisorLoading" class="advisor-response">
              <div class="response-brief"><strong>{{ aiResponseBrief }}</strong></div>
              <div v-if="aiResponseDetail" class="response-detail">{{ aiResponseDetail }}</div>
              <div v-if="aiResponseCharts && aiResponseCharts.length > 0" class="recommended-charts">
                <div class="charts-header">📊 Grafici Consigliati:</div>
                <div class="charts-pills">
                  <div v-for="(chart, idx) in aiResponseCharts" :key="idx" class="chart-pill">
                    <span class="chart-code">{{ nomiGrafici[chart.codice] || chart.codice }}</span>
                    <!-- FINSIM-MOD: Dynamic Plotly rendering for all mapped chart codes -->
                    <div v-if="chartCodeToEndpoint[chart.codice]"
                         :id="'plotly-ai-' + idx"
                         @click="apriSpiegazioneGrafico('plotly-ai-' + idx, nomiGrafici[chart.codice] || chart.codice)"
                         style="height: 350px; margin: 8px 0; background: rgba(0,0,0,0.02); border-radius: 4px; cursor:pointer;">
                    </div>
                    <!-- Fallback for unsupported chart codes -->
                    <div v-else class="chart-widget-fallback">
                      <div style="font-size: 12px; color: #8593A8; text-align: center; padding: 12px;">
                        📊 Grafico '{{ chart.codice }}' non ancora mappato.<br/>
                        <span style="font-size: 11px; color: #6B7280;">Controlla la console per i dettagli.</span>
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
            <div class="chart-container" @click="apriSpiegazioneGrafico('bRaccolta', 'Raccolta Netta — Trend')" style="cursor:pointer;"><canvas id="bRaccolta"></canvas></div>
            <div class="chart-static-caption">
              <strong>Come leggere:</strong> L'asse X mostra l'evoluzione su <strong>200 Tentativi di Proposta</strong>, l'asse Y la Raccolta Netta Cumulata in milioni di euro. La linea verde (Consulenza IA Adattiva) riflette la strategia personalizzata, la linea blu (Strategia Standard) il benchmark statico.
              <strong>Deduzione:</strong> Una divergenza positiva della Consulenza IA Adattiva rispetto alla Strategia Standard indica che l'approccio personalizzato sta generando maggior valore costante sul lungo periodo. Livelli plateau suggeriscono necessità di ricalibrazione della Direttiva.
            </div>
          </div>

          <div class="panel" style="grid-column: span 4;">
            <div class="panel-header">
              <h3>🎯 Performance Strategica Banca</h3>
            </div>
            
          <div id="plotly-spider-banca" @click="apriSpiegazioneGrafico('plotly-spider-banca', 'Performance Strategica Banca')" style="height: 320px; width: 100%; cursor:pointer;"></div>
          <div class="chart-static-caption">
            <strong>Come leggere:</strong> Il radar mostra 5 dimensioni chiave per la banca: Compliance (adeguatezza proposte), Raccolta (tasso conversione), Fiducia Cliente (sentiment post-proposta), Aderenza Direttiva (quanto ADAPT segue la strategia FISSO), Redditività (commissioni generate). La linea <strong style="color:#1FA463">verde</strong> è ADAPT, la linea <strong style="color:#8593A8">grigia tratteggiata</strong> è il target bancario.
            <strong>Deduzione:</strong> Dimensioni sotto il target (grigio) indicano aree di miglioramento prioritarie. Aderenza Direttiva bassa significa che ADAPT si discosta significativamente dalla strategia canonica.
          </div>
          </div>

          <!-- PLOTLY ADVANCED CHARTS -->
          <div class="panel" style="grid-column: span 12;">
            <div class="panel-header">
              <h3>📊 Visualizzazioni Avanzate</h3>
            </div>
          </div>

          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>Mappa di Valore (Patrimonio Gestito vs Profilo Rischio)</h3></div>
            <div @click="apriSpiegazioneGrafico('heatmap-banca', 'Mappa di Valore')" style="display: grid; grid-template-columns: 120px repeat(5, 1fr); gap: 4px; align-items: center; cursor:pointer;">
              <div></div>
              <div v-for="col in ['Patrimonio Basso', 'Medio-Basso', 'Medio', 'Medio-Alto', 'Alto Patrimonio']" :key="col"
                  style="text-align:center; font-size:11px; color:#8593A8; font-weight:600; padding:4px; text-transform:uppercase; letter-spacing:0.5px">
                {{ col }}
              </div>
              <template v-for="(row, rowIdx) in heatmapBanca" :key="rowIdx">
                <div style="font-size:11px; color:#8593A8; font-weight:600; text-align:right; padding-right:8px; text-transform:uppercase; letter-spacing:0.5px">
                  {{ row.label }}
                </div>
                <div v-for="(cell, colIdx) in row.cells" :key="colIdx"
                    class="heat-cell" :style="{ backgroundColor: cell.bg, color: cell.fg }">
                  {{ cell.value }}
                </div>
              </template>
            </div>
            <p class="chart-caption">La scala cromatica mostra il differenziale di conversione tra le due strategie. <strong style="color:#059669">Verde</strong> = Consulenza Adattiva converte meglio. <strong style="color:#e11d48">Rosso</strong> = Strategia Standard più efficace.</p>
          </div>

          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>Analisi Contribuzione Patrimonio Gestito</h3></div>
            <div id="plotly-waterfall" @click="apriSpiegazioneGrafico('plotly-waterfall', 'Analisi Contribuzione Patrimonio')" style="min-height: 400px; width: 100%; background: rgba(0,0,0,0.02); border-radius: 4px; cursor:pointer;"></div>
            <p class="chart-caption">Grafico a cascata che mostra la scomposizione del patrimonio finale: partendo da Patrimonio Gestito iniziale, passando per nuova raccolta, effetto mercato, e abbandoni clienti, fino al patrimonio finale gestito.</p>
          </div>

          <div class="panel" style="grid-column: span 12;">
            <div class="panel-header"><h3>Evoluzione Performance Cumulata (200 Tentativi di Proposta)</h3></div>
            <div id="plotly-lines" @click="apriSpiegazioneGrafico('plotly-lines', 'Evoluzione Performance Cumulata')" style="min-height: 400px; width: 100%; background: rgba(0,0,0,0.02); border-radius: 4px; cursor:pointer;"></div>
            <p class="chart-caption">Confronto delle linee di performance cumulate tra Consulenza IA Dinamica e Strategia Standard su tutti i 200 tentativi di proposta. Le divergenze evidenziano i vantaggi strategici dell'approccio personalizzato.</p>
          </div>
        </div>

        <div v-if="view === 'promotore'" class="dashboard-grid">

          <div class="panel advisor-panel" style="grid-column: span 12;">
            <div class="panel-header">
              <h3>🤖 Assistente di Analisi Strategica</h3>
            </div>
            <div class="advisor-search-box">
              <input
                v-model="searchQuery"
                @keydown="handleSearchKeydown"
                :disabled="isAdvisorLoading"
                type="text"
                placeholder="Poni una domanda all'Assistente (es: 'Analizza il trend della compliance')..."
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
              <span>L'Assistente sta analizzando i 200 round storici...</span>
            </div>
            <div v-if="aiResponseBrief && !isAdvisorLoading" class="advisor-response">
              <div class="response-brief"><strong>{{ aiResponseBrief }}</strong></div>
              <div v-if="aiResponseDetail" class="response-detail">{{ aiResponseDetail }}</div>
              <div v-if="aiResponseCharts && aiResponseCharts.length > 0" class="recommended-charts">
                <div class="charts-header">📊 Grafici Consigliati:</div>
                <div class="charts-pills">
                  <div v-for="(chart, idx) in aiResponseCharts" :key="idx" class="chart-pill">
                    <span class="chart-code">{{ nomiGrafici[chart.codice] || chart.codice }}</span>
                    <!-- FINSIM-MOD: Dynamic Plotly rendering for all mapped chart codes -->
                    <div v-if="chartCodeToEndpoint[chart.codice]"
                         :id="'plotly-ai-' + idx"
                         @click="apriSpiegazioneGrafico('plotly-ai-' + idx, nomiGrafici[chart.codice] || chart.codice)"
                         style="height: 350px; margin: 8px 0; background: rgba(0,0,0,0.02); border-radius: 4px; cursor:pointer;">
                    </div>
                    <!-- Fallback for unsupported chart codes -->
                    <div v-else class="chart-widget-fallback">
                      <div style="font-size: 12px; color: #8593A8; text-align: center; padding: 12px;">
                        📊 Grafico '{{ chart.codice }}' non ancora mappato.<br/>
                        <span style="font-size: 11px; color: #6B7280;">Controlla la console per i dettagli.</span>
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

          <!-- ROW 1: Strategia IA Adattiva + Commissioni -->
          <div class="panel highlight-panel" style="grid-column: span 8;">
            <div class="panel-header" style="display: flex; justify-content: space-between; align-items: center;">
              <h3><span style="font-size:16px;">🧠</span> Direttiva Strategica IA (Consulenza Adattiva)</h3>
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
              <div v-for="(action, idx) in nextBestActionsTradotte" :key="idx" class="action-item-box">
                {{ action }}
              </div>
              <div v-if="nextBestActionsTradotte.length === 0" style="color: #8593A8; font-size: 13px; text-align: center; padding: 20px;">
                Nessun azione consigliata al momento.
              </div>
            </div>
          </div>

          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>🚨 Torre di Controllo Allarmi Portafoglio</h3></div>
            <div style="display: flex; flex-direction: column; gap: 12px;">
              <div class="alarm-badge" :class="{ triggered: datiPromotore.alerts.churn_risk_count > 0 }">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span>⚠️ Rischio Abbandono</span>
                  <span style="font-size: 18px; font-weight: bold;">{{ datiPromotore.alerts.churn_risk_count }}</span>
                </div>
                <p style="font-size: 11px; margin-top: 4px; opacity: 0.8;">Anomalie fiducia/delta rilevate</p>
              </div>
              <div class="alarm-badge" :class="{ triggered: datiPromotore.alerts.mifid_alerts_count > 0 }">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span>🔒 Allerta Conformità Normativa</span>
                  <span style="font-size: 18px; font-weight: bold;">{{ datiPromotore.alerts.mifid_alerts_count }}</span>
                </div>
                <p style="font-size: 11px; margin-top: 4px; opacity: 0.8;">Scostamenti adeguatezza</p>
              </div>
            </div>
          </div>

          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>🔥 Mappa di Valore (Patrimonio Gestito vs Profilo Rischio)</h3></div>
            <div @click="apriSpiegazioneGrafico('heatmap-promotore', 'Mappa di Valore Promotore')" style="display: grid; grid-template-columns: 120px repeat(5, 1fr); gap: 4px; align-items: center; cursor:pointer;">              <div></div>
              <div v-for="col in ['Patrimonio Basso', 'Medio-Basso', 'Medio', 'Medio-Alto', 'Alto Patrimonio']" :key="col"
                  style="text-align:center; font-size:11px; color:#8593A8; font-weight:600; padding:4px; text-transform:uppercase; letter-spacing:0.5px">
                {{ col }}
              </div>
              <template v-for="(row, rowIdx) in heatmapBanca" :key="rowIdx">
                <div style="font-size:11px; color:#8593A8; font-weight:600; text-align:right; padding-right:8px; text-transform:uppercase; letter-spacing:0.5px">
                  {{ row.label }}
                </div>
                <div v-for="(cell, colIdx) in row.cells" :key="colIdx"
                    class="heat-cell" :style="{ backgroundColor: cell.bg, color: cell.fg }">
                  {{ cell.value }}
                </div>
              </template>
            </div>
            <p class="chart-caption">La scala cromatica mostra il differenziale di conversione tra le due strategie. <strong style="color:#059669">Verde</strong> = Consulenza Adattiva converte meglio. <strong style="color:#e11d48">Rosso</strong> = Strategia Standard più efficace.</p>
          </div>

          <!-- ROW 2C: Delta Performance Consulenza Adattiva vs Strategia Standard -->
          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>📊 Delta Performance (Vantaggio Consulenza Adattiva)</h3></div>
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
                  Consulenza Adattiva {{ datiPromotore.adapt.tasso_conversione_pct }}% vs Strategia Standard {{ datiPromotore.fisso.tasso_conversione_pct }}%
                </div>
              </div>
            </div>
          </div>

          <!-- ROW 3: Curva di Sopravvivenza Clienti (Kaplan-Meier) -->
          <div class="panel" style="grid-column: span 12;">
            <div class="panel-header"><h3>📈 Curva di Sopravvivenza Clienti (Kaplan-Meier)</h3></div>
            <div id="plotly-sopravvivenza" @click="apriSpiegazioneGrafico('plotly-sopravvivenza', 'Curva di Sopravvivenza Clienti')" style="width: 100%; height: 400px; min-height: 400px; background: rgba(0,0,0,0.02); border-radius: 4px; cursor:pointer;"></div>
            <p class="chart-caption">Curva di retention che mostra il tasso di sopravvivenza dei clienti nel tempo, comparando la Consulenza IA Dinamica (verde) vs Strategia Standard (rosso). I "scalini" rappresentano i momenti in cui i clienti abbandonano il portafoglio.</p>
          </div>

          <!-- ROW 3B: Andamento Ricavi Cumulati-->
          <div class="panel" style="grid-column: span 12;">
            <div class="panel-header"><h3>💰 Andamento Ricavi Cumulati (200 Proposte)</h3></div>
            <div id="plotly-guadagni" @click="apriSpiegazioneGrafico('plotly-guadagni', 'Andamento Ricavi Cumulati')" style="width: 100%; height: 400px; min-height: 400px; background: rgba(0,0,0,0.02); border-radius: 4px; cursor:pointer;"></div>
            <p class="chart-caption">Andamento dei ricavi cumulati generati dalla Consulenza IA Adattiva (verde) vs Strategia Standard (rosso) su 200 proposte commerciali. La divergenza tra le due curve indica il vantaggio economico dell'approccio personalizzato.</p>
          </div>

          <!-- ROW 4: Confronto Performance Globale -->
          <div class="panel" style="grid-column: span 12;">
            <div class="panel-header">
              <h3>Confronto Performance: Consulenza IA Dinamica vs Strategia Standard</h3>
            </div>
            <div class="comparison-grid">
              <div class="metric-card">
                <div class="metric-label">Tasso Conversione</div>
                <div class="metric-values">
                  <div class="adapt-value">{{ datiPromotore.adapt.tasso_conversione_pct }}% <span style="font-size:10px; color:#6b7280;">Consulenza Adattiva</span></div>
                  <div class="fisso-value">{{ datiPromotore.fisso.tasso_conversione_pct }}% <span style="font-size:10px; color:#6b7280;">Strategia Standard</span></div>
                </div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Fiducia Media Clienti</div>
                <div class="metric-values">
                  <div class="adapt-value">{{ datiPromotore.adapt.fiducia_media }}% <span style="font-size:10px; color:#6b7280;">Consulenza Adattiva</span></div>
                  <div class="fisso-value">{{ datiPromotore.fisso.fiducia_media }}% <span style="font-size:10px; color:#6b7280;">Strategia Standard</span></div>
                </div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Commissioni Cumulate</div>
                <div class="metric-values">
                  <div class="adapt-value">€ {{ datiPromotore.adapt.commissioni_cumulate.toLocaleString('it-IT') }} <span style="font-size:10px; color:#6b7280;">Consulenza Adattiva</span></div>
                  <div class="fisso-value">€ {{ datiPromotore.fisso.commissioni_cumulate.toLocaleString('it-IT') }} <span style="font-size:10px; color:#6b7280;">Strategia Standard</span></div>
                </div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Proposte Totali</div>
                <div class="metric-values">
                  <div class="adapt-value">{{ datiPromotore.adapt.proposte_totali }} <span style="font-size:10px; color:#6b7280;">Consulenza Adattiva</span></div>
                  <div class="fisso-value">{{ datiPromotore.fisso.proposte_totali }} <span style="font-size:10px; color:#6b7280;">Strategia Standard</span></div>
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
                    <th style="text-align: center;">Consulenza Adattiva</th>
                    <th style="text-align: center;">Strategia Standard</th>
                    <th style="text-align: center;">Dominanza</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in datiPromotore.risk_profile_breakdown" :key="idx">
                    <td style="font-weight: 600; color: #E2E8F0; font-size: 12px;">{{ row.profilo }}</td>
                    <td style="text-align: center; color: #1FA463; font-weight: bold; font-size: 12px;">{{ row.adapt_pct }}%</td>
                    <td style="text-align: center; color: #2E6FD6; font-weight: bold; font-size: 12px;">{{ row.fisso_pct }}%</td>
                    <td style="text-align: center;">
                      <span v-if="row.adapt_pct > row.fisso_pct" class="dom-badge adapt-dom">Consulenza Adattiva</span>
                      <span v-else-if="row.fisso_pct > row.adapt_pct" class="dom-badge fisso-dom">Strategia Standard</span>
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
                    <th style="text-align: center;">Consulenza Adattiva</th>
                    <th style="text-align: center;">Strategia Standard</th>
                    <th style="text-align: center;">Dominanza</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in datiPromotore.product_breakdown" :key="idx">
                    <td style="font-weight: 600; color: #E2E8F0; font-size: 12px;">{{ row.prodotto }}</td>
                    <td style="text-align: center; color: #1FA463; font-weight: bold; font-size: 12px;">{{ row.adapt_pct }}%</td>
                    <td style="text-align: center; color: #2E6FD6; font-weight: bold; font-size: 12px;">{{ row.fisso_pct }}%</td>
                    <td style="text-align: center;">
                      <span v-if="row.adapt_pct > row.fisso_pct" class="dom-badge adapt-dom">Consulenza Adattiva</span>
                      <span v-else-if="row.fisso_pct > row.adapt_pct" class="dom-badge fisso-dom">Strategia Standard</span>
                      <span v-else class="dom-badge" style="color: #8593A8;">Parità</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ROW 5: Grafici -->
          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>Conformità per Interazione Commerciale</h3></div>
            <div class="chart-container" @click="apriSpiegazioneGrafico('pCompliance', 'Conformità per Interazione Commerciale')" style="cursor:pointer;"><canvas id="pCompliance"></canvas></div>
            <div class="chart-static-caption">
              <strong>Come leggere:</strong> L'asse X mostra i <strong>200 Tentativi di Proposta</strong>, l'asse Y la percentuale di conformità (0-100%). La linea verde (Consulenza Adattiva) rappresenta l'approccio personalizzato, la linea blu tratteggiata (Strategia Standard) il benchmark.
              <strong>Deduzione:</strong> Se la Consulenza Adattiva supera la Strategia Standard, l'approccio personalizzato sta migliorando l'allineamento prodotto-cliente. Un trend decrescente suggerisce di rivedere la Direttiva.
            </div>
          </div>

          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>Proposte Accettate per Fase Commerciale</h3></div>
            <div class="chart-container" @click="apriSpiegazioneGrafico('pAccept', 'Proposte Accettate per Fase Commerciale')" style="cursor:pointer;"><canvas id="pAccept"></canvas></div>
            <div class="chart-static-caption">
              <strong>Come leggere:</strong> L'asse X mostra i <strong>10 Blocchi di Tentativi di Proposta</strong> (20 proposte per blocco), l'asse Y il numero cumulato di proposte accettate. Le barre verdi (Consulenza Adattiva) e blu (Strategia Standard) sono sovrapposte per un confronto immediato.
              <strong>Deduzione:</strong> Un volume della Consulenza Adattiva sistematicamente più alto indica maggiore efficacia della strategia personalizzata. Picchi anomali suggeriscono fattori di mercato esterni.
            </div>
          </div>
        </div>

        <div v-if="view === 'cliente'" class="dashboard-grid">

          <div class="panel advisor-panel" style="grid-column: span 12;">
            <div class="panel-header">
              <h3>🤖 Assistente di Analisi Strategica</h3>
            </div>
            <div class="advisor-search-box">
              <input
                v-model="searchQuery"
                @keydown="handleSearchKeydown"
                :disabled="isAdvisorLoading"
                type="text"
                placeholder="Poni una domanda all'Assistente (es: 'Analizza il trend della compliance')..."
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
              <span>L'Assistente sta analizzando i 200 round storici...</span>
            </div>
            <div v-if="aiResponseBrief && !isAdvisorLoading" class="advisor-response">
              <div class="response-brief"><strong>{{ aiResponseBrief }}</strong></div>
              <div v-if="aiResponseDetail" class="response-detail">{{ aiResponseDetail }}</div>
              <div v-if="aiResponseCharts && aiResponseCharts.length > 0" class="recommended-charts">
                <div class="charts-header">📊 Grafici Consigliati:</div>
                <div class="charts-pills">
                  <div v-for="(chart, idx) in aiResponseCharts" :key="idx" class="chart-pill">
                    <span class="chart-code">{{ nomiGrafici[chart.codice] || chart.codice }}</span>
                    <!-- FINSIM-MOD: Dynamic Plotly rendering for all mapped chart codes -->
                    <div v-if="chartCodeToEndpoint[chart.codice]"
                         :id="'plotly-ai-' + idx"
                         @click="apriSpiegazioneGrafico('plotly-ai-' + idx, nomiGrafici[chart.codice] || chart.codice)"
                         style="height: 350px; margin: 8px 0; background: rgba(0,0,0,0.02); border-radius: 4px; cursor:pointer;">
                    </div>
                    <!-- Fallback for unsupported chart codes -->
                    <div v-else class="chart-widget-fallback">
                      <div style="font-size: 12px; color: #8593A8; text-align: center; padding: 12px;">
                        📊 Grafico '{{ chart.codice }}' non ancora mappato.<br/>
                        <span style="font-size: 11px; color: #6B7280;">Controlla la console per i dettagli.</span>
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

          <!-- FINSIM-MOD: Client Intelligence KPI & Risk Profile Distribution -->
          <div class="panel" style="grid-column: span 12;">
            <div class="panel-header">
              <h3>📊 Intelligence Cliente — KPI Medi & Distribuzione Portafoglio</h3>
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;">
              <div class="metric-card">
                <div class="metric-label">Fiducia Media (ADAPT)</div>
                <div class="adapt-value" style="font-size:28px;">{{ datiPromotore.adapt.fiducia_media }}%</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Fiducia Media (FISSO)</div>
                <div class="fisso-value" style="font-size:28px;">{{ datiPromotore.fisso.fiducia_media }}%</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Tasso Accettazione (ADAPT)</div>
                <div class="adapt-value" style="font-size:28px;">{{ datiPromotore.adapt.tasso_conversione_pct }}%</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Tasso Accettazione (FISSO)</div>
                <div class="fisso-value" style="font-size:28px;">{{ datiPromotore.fisso.tasso_conversione_pct }}%</div>
              </div>
            </div>
            <div class="panel-header" style="margin-top: 8px;">
              <h3>Distribuzione Clienti per Profilo di Rischio</h3>
            </div>
            <div class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Profilo di Rischio</th>
                    <th style="text-align:center">Accettazione ADAPT</th>
                    <th style="text-align:center">Accettazione FISSO</th>
                    <th style="text-align:center">Dominanza</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in datiPromotore.risk_profile_breakdown" :key="idx">
                    <td style="font-weight:600; color:#E2E8F0">{{ row.profilo }}</td>
                    <td style="text-align:center; color:#1FA463; font-weight:bold">{{ row.adapt_pct }}%</td>
                    <td style="text-align:center; color:#2E6FD6; font-weight:bold">{{ row.fisso_pct }}%</td>
                    <td style="text-align:center">
                      <span v-if="row.adapt_pct > row.fisso_pct" class="dom-badge adapt-dom">ADAPT</span>
                      <span v-else-if="row.fisso_pct > row.adapt_pct" class="dom-badge fisso-dom">FISSO</span>
                      <span v-else class="dom-badge" style="color:#8593A8">Parità</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- FINSIM-MOD: Radar Chart Panel - Full Width -->
          <div class="panel" style="grid-column: span 12; padding: 24px;">
            <div style="display: grid; grid-template-columns: 1fr;">
              <!-- Radar Chart Full Width -->
              <div style="background: rgba(31, 164, 99, 0.08); border: 1px solid rgba(31, 164, 99, 0.2); border-radius: 8px; padding: 24px;">
                <h4 style="color: #1FA463; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">Radar: Sentiment Client</h4>
                <div id="spider-sentiment-clienti" @click="apriSpiegazioneGrafico('spider-sentiment-clienti', 'Sentiment Clienti')" style="height: 520px; width: 100%; cursor:pointer;"></div>
                <div class="chart-static-caption" style="margin-top: 12px;">
                  <strong>Come leggere:</strong> Il radar mostra 5 dimensioni del sentiment cliente: Fiducia Percepita, Soddisfazione Proposta, Resilienza al Churn, Stabilità Comportamentale.
                  <strong>Deduzione:</strong> Dimensioni dove la Consulenza Adattiva supera la Strategia Standard indicano aree dove la personalizzazione sta costruendo maggior fiducia. Dimensioni rientranti indicano aree critiche da migliorare.
                </div>
              </div>
            </div>
          </div>

          <!-- FINSIM-MOD: Heatmap Propensione al Rischio - Leggibile con Assi -->
          <div class="panel" style="grid-column: span 12;">
            <div class="panel-header">
              <h3>🗺️ Heatmap Propensione al Rischio per Cluster</h3>
            </div>
            <div @click="apriSpiegazioneGrafico('heatmap-promotore', 'Mappa di Valore Promotore')" style="display: grid; grid-template-columns: 120px repeat(5, 1fr); gap: 4px; align-items: center; cursor:pointer;">
              <!-- Header colonne -->
              <div></div>
              <div v-for="col in ['Basso Patrimonio', 'Medio-Basso', 'Medio', 'Medio-Alto', 'Alto Patrimonio']" :key="col"
                   style="text-align:center; font-size:11px; color:#8593A8; font-weight:600; padding:4px; text-transform:uppercase; letter-spacing:0.5px">
                {{ col }}
              </div>
              <!-- Righe con label -->
              <template v-for="(row, rowIdx) in heatmapReale" :key="rowIdx">
                <div style="font-size:11px; color:#8593A8; font-weight:600; text-align:right; padding-right:8px; text-transform:uppercase; letter-spacing:0.5px">
                  {{ row.label }}
                </div>
                <div v-for="(cell, colIdx) in row.cells" :key="colIdx"
                     class="heat-cell" :style="{ backgroundColor: cell.bg, color: cell.fg }">
                  {{ cell.value }}
                </div>
              </template>
            </div>
            <div class="chart-static-caption" style="margin-top:16px;">
              <strong>Come leggere:</strong> Ogni cella mostra la propensione al rischio media dei clienti in quel cluster (Profilo Rischio × Patrimonio).
              <strong style="color:#1E9E63">Verde</strong> = alta propensione,
              <strong style="color:#E0922F">Arancione</strong> = media,
              <strong style="color:#D64242">Rosso</strong> = bassa propensione o cluster critico.
              <strong>Deduzione:</strong> Le celle rosse indicano cluster dove la proposta standard fallisce — priorità per la Consulenza IA Adattiva.
            </div>
          </div>

          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>Evoluzione Fiducia</h3></div>
            <div class="chart-container" @click="apriSpiegazioneGrafico('cFiducia', 'Evoluzione Fiducia')" style="cursor:pointer;"><canvas id="cFiducia"></canvas></div>
            <div class="chart-static-caption">
              <strong>Come leggere:</strong> L'asse X mostra i <strong>200 Tentativi di Proposta</strong>, l'asse Y la percentuale di fiducia media (0-100%). La curva è una <strong>media mobile a 15 periodi</strong> che elimina il rumore e mostra il trend reale.
              <strong>Deduzione:</strong> Un trend in crescita indica comunicazione efficace. Cali sostenuti segnalano perdita di fiducia che richiede intervento sulla strategia comunicativa.
            </div>
          </div>

          <div class="panel" style="grid-column: span 6;">
            <div class="panel-header"><h3>Allineamento Profilo vs Portafoglio</h3></div>
            <div class="chart-container" @click="apriSpiegazioneGrafico('cRadar', 'Allineamento Profilo vs Portafoglio')" style="height: 320px; cursor:pointer;"><canvas id="cRadar"></canvas></div>
            <div class="chart-static-caption">
              <strong>Come leggere:</strong> Il radar mostra 3 dimensioni con dati reali di simulazione: Profilo Rischio, Fiducia Cliente, Adeguatezza Proposta. La linea <strong style="color:#2E6FD6">blu</strong> è il profilo/soglia di riferimento, la linea <strong style="color:#178A57">verde</strong>è il portafoglio effettivo assegnato.
              <strong>Deduzione:</strong> Quando le aree coincidono il profilo è rispettato. Discrepanze indicano necessità di ribilanciamento o comunicazione aggiuntiva al cliente sul razionale delle scelte.
            </div>
          </div>

          <div class="panel" style="grid-column: span 12;">
            <div class="panel-header"><h3>📊 Soddisfazione per Tipologia Prodotto</h3></div>
            <div id="plotly-bar-prodotti" @click="apriSpiegazioneGrafico('plotly-bar-prodotti', 'Soddisfazione per Tipologia Prodotto')" style="height: 400px; width: 100%; background: rgba(0,0,0,0.02); border-radius: 4px; cursor:pointer;"></div>
            <p class="chart-caption">Analisi della soddisfazione dei clienti per ogni tipologia di prodotto proposto. Confronto tra Consulenza IA Adattiva e Strategia Standard.</p>
          </div>
        </div>

        <div v-if="view === 'evoluzione'" class="dashboard-grid">

          <div class="panel" style="grid-column: span 12;">
            <div class="panel-header">
              <h3>🔍 Evoluzione Strategica per Segmento di Clientela</h3>
            </div>
            <p style="color: #8593A8; font-size: 13px; margin-bottom: 16px;">
              Seleziona un segmento di clientela per analizzare come il promotore adatta la propria strategia nel corso dei tentativi di proposta, in risposta al feedback ricevuto.
            </p>
            <div style="display: flex; gap: 16px; margin-bottom: 16px; flex-wrap: wrap;">
              <div style="flex: 1; min-width: 200px;">
                <label style="font-size: 11px; color: #8593A8; text-transform: uppercase; display: block; margin-bottom: 6px;">Profilo di Rischio</label>
                <select v-model.number="clusterRiskIdx" @change="caricaEvoluzioneCluster" class="advisor-input" style="cursor: pointer;">
                  <option v-for="(label, idx) in profiliRischioLabels" :key="idx" :value="idx">{{ label }}</option>
                </select>
              </div>
              <div style="flex: 1; min-width: 200px;">
                <label style="font-size: 11px; color: #8593A8; text-transform: uppercase; display: block; margin-bottom: 6px;">Livello Patrimoniale</label>
                <select v-model.number="clusterWealthIdx" @change="caricaEvoluzioneCluster" class="advisor-input" style="cursor: pointer;">
                  <option v-for="(label, idx) in profiliPatrimonioLabels" :key="idx" :value="idx">{{ label }}</option>
                </select>
              </div>
            </div>

            <div v-if="isLoadingClusterEvolution" class="advisor-loading">
              <div class="loading-spinner"></div>
              <span>Analisi dell'evoluzione strategica in corso...</span>
            </div>

            <div v-else-if="clusterEvolutionData.rounds && clusterEvolutionData.rounds.length > 0 && clusterPromotoreType === 'Strategia Standard'" style="text-align: center; padding: 40px 20px; background: rgba(46,111,214,0.05); border-radius: 8px; border: 1px solid rgba(46,111,214,0.15);">
              <div style="font-size: 32px; margin-bottom: 12px;">📌</div>
              <h4 style="color: #2E6FD6; margin-bottom: 8px;">{{ clusterEvolutionData.cluster_label }} — Gestito dalla Strategia Standard</h4>
              <p style="color: #8593A8; font-size: 13px; max-width: 480px; margin: 0 auto 20px;">
                Questo segmento di clientela segue un approccio fisso e predefinito, che non si adatta nel tempo in risposta al feedback dei clienti. Non c'è quindi un'evoluzione strategica da analizzare per questo profilo.
              </p>
              <button @click="clusterRiskIdx = 2; caricaEvoluzioneCluster()" class="quick-pill" style="display: inline-block; padding: 10px 20px;">
                Prova "Basso Rischio" — gestito dalla Consulenza Adattiva
              </button>
            </div>

            <div v-else-if="clusterEvolutionData.rounds && clusterEvolutionData.rounds.length > 0">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h4 style="color: #1FA463;">{{ clusterEvolutionData.cluster_label }}</h4>
                <span style="font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 10px;"
                      :style="{ background: clusterPromotoreType === 'Consulenza Adattiva' ? 'rgba(31,164,99,0.15)' : 'rgba(46,111,214,0.15)', color: clusterPromotoreType === 'Consulenza Adattiva' ? '#1FA463' : '#2E6FD6' }">
                    Gestito da: {{ clusterPromotoreType }}
                </span>
              </div>

              <div class="advisor-response" style="margin-bottom: 20px;">
                <div class="response-brief" style="margin-bottom: 4px;">📊 Analisi del cambiamento di approccio</div>
                <div class="response-detail">{{ clusterAnalisiLLM }}</div>
              </div>

              <div id="plotly-cluster-evolution" @click="apriSpiegazioneGrafico('plotly-cluster-evolution', 'Evoluzione Strategica per Cluster')" style="width: 100%; height: 400px; margin-bottom: 8px; background: rgba(0,0,0,0.02); border-radius: 4px; cursor:pointer;"></div>
              <div class="chart-static-caption" style="margin-bottom: 24px;">
                <strong>Come leggere:</strong> Ogni pallino rappresenta un momento in cui il promotore ha cambiato approccio strategico. Il <strong>colore</strong> indica la categoria (🔴 Aggressiva, 🔵 Conservativa, 🟠 Informativa, 🟢 Relazionale). L'<strong>asse Y</strong> mostra la fiducia del cliente in quel momento (0-100%). La <strong>linea tratteggiata blu</strong> mostra l'adeguatezza della proposta.
                <strong>Deduzione:</strong> Pallini in salita indicano che il cambio di approccio ha migliorato la fiducia. Pallini in discesa indicano che la strategia non ha funzionato e il promotore ha dovuto cambiare rotta.
              </div>
              <div id="plotly-cumulativa-categoria" @click="apriSpiegazioneGrafico('plotly-cumulativa-categoria', 'Utilizzo Cumulativo delle Categorie di Approccio')" style="width: 100%; height: 320px; margin-bottom: 8px; background: rgba(0,0,0,0.02); border-radius: 4px; cursor:pointer;"></div>
              <div class="chart-static-caption" style="margin-bottom: 24px;">
                <strong>Come leggere:</strong> Le linee mostrano quante volte ciascuna categoria di approccio è stata usata cumulativamente nel corso dei 200 round. Una linea che sale rapidamente indica un approccio dominante.
                <strong>Deduzione:</strong> Se la categoria Relazionale (verde) domina nel lungo periodo, il promotore ha imparato che costruire fiducia è più efficace che spingere prodotti aggressivamente.
              </div>

              <div style="display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap;">
                <div v-for="(colore, catName) in categoriaColori" :key="catName" v-show="catName !== 'Non classificato'" style="display: flex; align-items: center; gap: 6px;">
                  <span :style="{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: colore, display: 'inline-block' }"></span>
                  <span style="font-size: 12px; color: #C7D5E6;">{{ catName }}</span>
                </div>
              </div>

                <h4 style="color: #C7D5E6; margin-bottom: 12px; font-size: 13px;">Momenti di cambio strategia ({{ eventiTransizione.length }} su 200 round totali)</h4>              <div style="display: flex; flex-direction: column; gap: 10px; max-height: 500px; overflow-y: auto;">
                <div v-for="(evento, idx) in eventiTransizione" :key="idx"
                     style="display: flex; gap: 12px; padding: 12px; border-radius: 6px; background: rgba(31,164,99,0.05);"
                     :style="{ borderLeft: '3px solid ' + (categoriaColori[evento.categoria_approccio] || '#8593A8') }">
                  <div style="min-width: 70px; font-size: 12px; color: #8593A8; font-weight: 600;">
                    Round {{ evento.round }}
                  </div>
                  <div style="flex: 1;">
                    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 4px; flex-wrap: wrap;">
                      <span style="font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 10px; color: white;"
                            :style="{ background: categoriaColori[evento.categoria_approccio] || '#8593A8' }">
                        {{ evento.categoria_approccio }}
                      </span>
                      <span style="font-size: 11px; color: #8593A8;">{{ evento.prodotto_suggerito }}</span>
                      <span :style="{ color: evento.accettato ? '#1FA463' : '#e11d48', fontSize: '11px', fontWeight: '600' }">
                        {{ evento.accettato ? '✓ Accettato' : '✗ Rifiutato' }}
                      </span>
                    </div>
                    <p style="font-size: 13px; color: #E2E8F0; margin-bottom: 4px;">{{ evento.llm_strategy }}</p>
                    <p style="font-size: 12px; color: #8593A8; font-style: italic;">{{ evento.approccio_comunicativo }}</p>
                    <div style="display: flex; gap: 16px; margin-top: 6px; font-size: 11px; color: #8593A8;">
                      <span>Adeguatezza: <strong style="color: #C7D5E6;">{{ (evento.adeguatezza_score * 100).toFixed(0) }}%</strong></span>
                      <span>Δ Fiducia: <strong :style="{ color: evento.delta_fiducia_medio >= 0 ? '#1FA463' : '#e11d48' }">{{ evento.delta_fiducia_medio >= 0 ? '+' : '' }}{{ (evento.delta_fiducia_medio * 100).toFixed(1) }}%</strong></span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-else style="text-align: center; color: #8593A8; padding: 40px;">
              Nessun dato disponibile per questo segmento di clientela in questo scenario.
            </div>
          </div>
        </div>

      </div>
    </main>

    <!-- MODAL: Guida & Legenda -->
    <div v-if="showHelpModal" class="help-modal" @click.self="showHelpModal = false">
      <div class="modal-content">
        <button @click="showHelpModal = false" class="modal-close-btn">✕</button>

        <h2 class="modal-title">📚 Guida alla Dashboard FINsim</h2>

        <div class="modal-section">
          <h3>🎯 Come navigare la dashboard</h3>
          <p><strong>Viste operative:</strong> Usa i pulsanti nella sidebar sinistra per passare tra quattro prospettive di analisi:</p>
          <ul>
            <li><strong>Banca:</strong> Visione consolidata delle performance commerciali, raccolta netta e adeguatezza del portafoglio a livello istituzionale.</li>
            <li><strong>Promotore:</strong> Metriche di performance della Consulenza Adattiva rispetto alla Strategia Standard — conversioni, commissioni, conformità normativa.</li>
            <li><strong>Cliente:</strong> Prospettiva del cliente finale — fiducia, soddisfazione, allineamento tra profilo di rischio e portafoglio assegnato.</li>
            <li><strong>Evoluzione Cliente:</strong> Analisi dinamica di come un promotore adatta la propria strategia nel tempo in risposta al feedback ricevuto (fiducia e adeguatezza). Mostra solo i momenti critici dove cambia l'approccio strategico.</li>
          </ul>
          <p><strong>Scenari di mercato:</strong> Seleziona uno dei cinque scenari macroeconomici per vedere come cambiano le performance in contesti diversi:</p>
          <ul>
            <li><strong>Base:</strong> Mercato stabile, bassa volatilità, condizioni neutrali.</li>
            <li><strong>Espansione:</strong> Ciclo favorevole, opportunità di crescita.</li>
            <li><strong>Rialzo tassi:</strong> Pressione sui prodotti obbligazionari, duration risk.</li>
            <li><strong>Stress:</strong> Alta volatilità, shock di mercato.</li>
            <li><strong>Recessione:</strong> Contrazione economica, approccio difensivo.</li>
          </ul>
        </div>

        <div class="modal-section">
          <h3>🤖 Assistente di Analisi Strategica</h3>
          <p>L'assistente analizza i dati della simulazione e risponde a domande specifiche in linguaggio da consulente finanziario. Per ogni risposta suggerisce automaticamente i grafici più rilevanti.</p>
          <p><strong>Come usarlo:</strong> Scrivi una domanda nel campo di testo oppure clicca su una delle pillole rapide predefinite. Dopo la risposta, valuta l'utilità con le stelle — se la risposta è insufficiente (1-2 stelle), l'assistente rigenera automaticamente un'analisi alternativa.</p>
          <p><strong>Esempi di domande utili:</strong></p>
          <ul>
            <li>"Quale profilo di clientela sta soffrendo di più in questo scenario?"</li>
            <li>"Analizza il trend della conformità normativa"</li>
            <li>"Dove stiamo perdendo clienti e perché?"</li>
            <li>"Confronta le commissioni generate nei diversi scenari"</li>
          </ul>
        </div>

        <div class="modal-section">
          <h3>🔄 Evoluzione Cliente — Come analizzare l'adattamento strategico</h3>
          <p><strong>Cosa vedi:</strong> Questa vista mostra come un promotore adatta dinamicamente il proprio approccio verso un segmento specifico di clientela nel corso della simulazione, evidenziando i momenti critici dove cambia strategia in risposta al feedback ricevuto.</p>
          <p><strong>Come usarla:</strong></p>
          <ol style="margin-left: 16px;">
            <li>Seleziona un <strong>Profilo di Rischio</strong> (es. "Basso Rischio") e un <strong>Livello Patrimoniale</strong> (es. "Basso Patrimonio")</li>
            <li>Leggi l'<strong>Analisi LLM</strong> in alto: spiega il pattern osservato e collega i cambi di strategia ai feedback ricevuti</li>
            <li>Osserva il <strong>Grafico Plotly</strong>: mostra l'evoluzione di Fiducia (linea verde) e Adeguatezza (linea blu tratteggiata) nel tempo
              <ul style="margin-left: 12px; margin-top: 4px;">
                <li>I <strong>marker colorati</strong> sulla linea di fiducia indicano la categoria di approccio usata in quel round</li>
                <li>Quando il colore cambia, il promotore ha cambiato strategia in risposta al feedback precedente</li>
              </ul>
            </li>
            <li>Leggi la <strong>Cronologia</strong> qui sotto: mostra SOLO i round dove avviene un cambio strategico (es. "3 su 20 round totali")
              <ul style="margin-left: 12px; margin-top: 4px;">
                <li><strong style="color:#e11d48">Rosso</strong> = Approccio Aggressivo (spinge su prodotti a rischio/rendimento alto)</li>
                <li><strong style="color:#2E6FD6">Blu</strong> = Approccio Conservativo (privilegi sicurezza e liquidità)</li>
                <li><strong style="color:#f59e0b">Arancione</strong> = Approccio Informativo (focus su trasparenza e educazione)</li>
                <li><strong style="color:#1FA463">Verde</strong> = Approccio Relazionale (focus su fiducia e rassicurazione)</li>
              </ul>
            </li>
          </ol>
          <p><strong>Cosa dedurre:</strong> Se vedi molte transizioni fra categorie diverse, il promotore sta reagendo dinamicamente al feedback. Se vedi un solo colore, la strategia è rimasta stabile. Confronta questo con l'Analisi LLM per capire il "perché" dietro i cambi osservati.</p>
        </div>

        <div class="modal-section">
          <h3>📊 Grafici interattivi e Schemi colore</h3>
          <p><strong>Spiegazione al click:</strong> Clicca su qualsiasi grafico per ricevere una spiegazione generata dall'assistente su come leggere il grafico e cosa indicano i dati nel contesto dello scenario attivo.</p>
          <p><strong>Come leggere i colori — Scheme standard:</strong></p>
          <ul>
            <li><strong style="color:#1FA463">Verde</strong> — Consulenza Adattiva / valore positivo / adeguatezza alta / Approccio Relazionale</li>
            <li><strong style="color:#2E6FD6">Blu</strong> — Strategia Standard / valore di riferimento / Approccio Conservativo</li>
            <li><strong style="color:#E0922F">Arancione</strong> — Situazione di attenzione / adeguatezza parziale / Approccio Informativo</li>
            <li><strong style="color:#D64242">Rosso</strong> — Situazione critica / adeguatezza bassa / valore negativo / Approccio Aggressivo</li>
          </ul>
          <p><strong>Categorie di approccio strategico (vista Evoluzione Cliente):</strong></p>
          <ul>
            <li><strong style="color:#e11d48">Aggressivo (Rosso)</strong> — Il promotore spinge su prodotti a rischio/rendimento alto, incrementa l'esposizione clienti</li>
            <li><strong style="color:#2E6FD6">Conservativo (Blu)</strong> — Il promotore privilegia sicurezza, liquidità e protezione del capitale</li>
            <li><strong style="color:#f59e0b">Informativo (Arancione)</strong> — Il promotore focalizza su trasparenza, educazione finanziaria e dati</li>
            <li><strong style="color:#1FA463">Relazionale (Verde)</strong> — Il promotore focalizza su fiducia, rassicurazione e ascolto del cliente</li>
          </ul>
          <p><strong>Heatmap (viste Banca e Cliente):</strong> I colori indicano il differenziale di conversione tra le due strategie. Verde = la Consulenza Adattiva converte meglio in quel segmento. Rosso = la Strategia Standard è più efficace. Il numero indica la differenza percentuale.</p>
        </div>

        <div class="modal-section">
          <h3>🔍 Vista Evoluzione Cliente</h3>
          <p>Questa vista permette di analizzare in dettaglio come il promotore della Consulenza Adattiva modifica il proprio stile di approccio verso un segmento specifico di clientela nel corso della simulazione.</p>
          <p><strong>Come usarla:</strong> Seleziona un Profilo di Rischio e un Livello Patrimoniale per identificare il segmento di clientela da analizzare. Nota che ogni segmento è gestito esclusivamente da un solo tipo di promotore — se il segmento è gestito dalla Strategia Standard, non sarà disponibile un'analisi di evoluzione poiché questo approccio non si adatta nel tempo.</p>
          <p><strong>Categorie di approccio:</strong></p>
          <ul>
            <li><strong style="color:#e11d48">Aggressiva</strong> — il promotore privilegia prodotti a rischio e rendimento elevato</li>
            <li><strong style="color:#2E6FD6">Conservativa</strong> — focus su sicurezza, liquidità e protezione del capitale</li>
            <li><strong style="color:#f59e0b">Informativa</strong> — comunicazione basata su trasparenza ed educazione finanziaria</li>
            <li><strong style="color:#1FA463">Relazionale</strong> — enfasi su fiducia, rassicurazione e ascolto del cliente</li>
          </ul>
          <p>Il grafico ad area cumulativa mostra quale stile diventa progressivamente dominante nel tempo, mentre l'analisi generata dall'assistente spiega perché il promotore potrebbe aver cambiato approccio in determinati momenti, collegando le transizioni ai livelli di fiducia e adeguatezza osservati.</p>
        </div>

        <div class="modal-section">
          <h3>📄 Esportazione report</h3>
          <p><strong>PDF:</strong> Genera un report completo con analisi esecutiva scritta dall'assistente, tabella KPI e grafici principali. Ideale per la condivisione con il management.</p>
          <p><strong>PPTX:</strong> Genera una presentazione pronta da proiettare, con slide che combinano grafici e analisi testuali. Struttura ottimizzata per presentazioni al board.</p>
          <p>Entrambi i documenti riflettono lo scenario e i dati attualmente selezionati nella dashboard.</p>
        </div>

        <div class="modal-section">
          <h3>📈 Indicatori chiave</h3>
          <ul>
            <li><strong>Tasso di accettazione:</strong> Percentuale di proposte commerciali accettate dal cliente sul totale formulate.</li>
            <li><strong>Commissioni cumulate:</strong> Ricavi totali generati — calcolati all'1% sul volume medio di 100.000€ per cliente.</li>
            <li><strong>Fiducia media:</strong> Livello di soddisfazione e confidenza del cliente dopo ogni proposta (scala 0-100%).</li>
            <li><strong>Conformità normativa:</strong> Grado di adeguatezza del prodotto proposto rispetto al profilo di rischio del cliente (scala 0-100%). Valori sotto il 70% richiedono attenzione.</li>
            <li><strong>Rischio abbandono:</strong> Numero di clienti con segnali di insoddisfazione che potrebbero lasciare il portafoglio.</li>
            <li><strong>Segnalazioni di non conformità:</strong> Proposte che presentano scostamenti rispetto ai requisiti normativi di adeguatezza.</li>
          </ul>
        </div>

        <button @click="showHelpModal = false" class="modal-close-main-btn">Chiudi Guida</button>
      </div>
    </div>

    <!-- FINSIM-MOD: MODAL SPIEGAZIONE GRAFICO -->
    <div v-if="showChartModal" class="chart-explain-modal" @click.self="showChartModal = false">
      <div class="chart-explain-content">
        <div class="chart-explain-header">
          <h3>📊 {{ chartModalTitle }}</h3>
          <button @click="showChartModal = false" class="modal-close-btn">✕</button>
        </div>
        <div v-if="chartModalLoading" class="advisor-loading">
          <div class="loading-spinner"></div>
          <span>Analisi del grafico in corso...</span>
        </div>
        <div v-else class="chart-explain-body">
          <p>{{ chartModalSpiegazione }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import Chart from 'chart.js/auto';
import html2pdf from 'html2pdf.js';

// Carica Plotly dinamicamente via CDN
const loadPlotly = async () => {
  if (window.Plotly) return;
  const script = document.createElement('script');
  script.src = 'https://cdn.plot.ly/plotly-2.35.2.min.js';
  document.head.appendChild(script);
  return new Promise(resolve => {
    script.onload = () => resolve();
  });
};

// --- STATO ---
const view = ref('banca'); // Partiamo dalla vista banca
const scenario = ref('S0_fix12');
let chartInstances = [];
const isAdvisorLoading = ref(false);
const showHelpModal = ref(false);
const aiResponseBrief = ref('');
const aiResponseDetail = ref('');
const aiResponseCharts = ref([]);
const aiRating = ref(0);
const searchQuery = ref('');
let lastUserMessage = '';
const conversationHistory = ref([]);

// FINSIM-MOD: Chart Explanation Modal
const showChartModal = ref(false);
const chartModalTitle = ref('');
const chartModalSpiegazione = ref('');
const chartModalLoading = ref(false);

// --- VARIABILI REATTIVE PER I DATI MONGODB ---
const productSales = ref([]);
const trendData = ref({ labels: [], adattivo: [], fisso: [] });
const datiCliente = ref({
  labels: [],
  fiducia_adapt: [],
  fiducia_fisso: [],
  profilo_dichiarato: [],
  portafoglio_assegnato: [],
  profilo_labels: [],
  risk_matrice: [],
  risk_profili: [],
  risk_patrimoni: []
});
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

// FINSIM-MOD: Heatmap Propensione Rischio - Data-driven
const heatmapReale = ref([]);
const heatmapBanca = ref([]);

// FINSIM-MOD: Cluster Evolution View
const clusterRiskIdx = ref(0);
const clusterWealthIdx = ref(0);
const clusterEvolutionData = ref({ rounds: [], cluster_label: '' });
const clusterTransizioni = ref([]);
const clusterAnalisiLLM = ref('');
const clusterPromotoreType = ref('');
const isLoadingClusterEvolution = ref(false);

const profiliRischioLabels = ['Alto Rischio', 'Medio Rischio', 'Basso Rischio', 'Conservativo'];
const profiliPatrimonioLabels = ['Basso Patrimonio (50k-150k)', 'Medio-Basso (150k-300k)', 'Medio (300k-500k)', 'Medio-Alto (500k-750k)', 'Alto Patrimonio (750k+)'];
const profiliPatrimonioLabelsBreve = ['Basso Patrimonio', 'Medio-Basso', 'Medio', 'Medio-Alto', 'Alto Patrimonio'];

const categoriaColori = {
  'Aggressiva': '#e11d48',
  'Conservativa': '#2E6FD6',
  'Informativa': '#f59e0b',
  'Relazionale': '#1FA463',
  'Non classificato': '#8593A8'
};

// FINSIM-MOD: Filtra gli eventi di transizione dalla cronologia
const eventiTransizione = computed(() => {
  const rounds = clusterEvolutionData.value.rounds || [];
  if (rounds.length === 0) return [];

  const risultato = [rounds[0]];

  for (let i = 1; i < rounds.length; i++) {
    if (rounds[i].categoria_approccio !== rounds[i-1].categoria_approccio) {
      risultato.push(rounds[i]);
    }
  }

  return risultato;
});

const timelineBande = computed(() => {
  const rounds = clusterEvolutionData.value.rounds || [];
  if (rounds.length === 0) return [];

  const bande = [];
  let bandaAttuale = null;

  rounds.forEach((evento) => {
    const cat = evento.categoria_approccio;
    if (!bandaAttuale || bandaAttuale.categoria !== cat) {
      if (bandaAttuale) bande.push(bandaAttuale);
      bandaAttuale = { categoria: cat, roundInizio: evento.round, roundFine: evento.round };
    } else {
      bandaAttuale.roundFine = evento.round;
    }
  });
  if (bandaAttuale) bande.push(bandaAttuale);

  return bande;
});

const cumulativaCategoria = computed(() => {
  const rounds = clusterEvolutionData.value.rounds || [];
  if (rounds.length === 0) return { labels: [], serie: {} };

  const categorie = ['Aggressiva', 'Conservativa', 'Informativa', 'Relazionale'];
  const contatori = { Aggressiva: 0, Conservativa: 0, Informativa: 0, Relazionale: 0 };
  const serie = { Aggressiva: [], Conservativa: [], Informativa: [], Relazionale: [] };
  const labels = [];

  rounds.forEach((evento) => {
    const cat = evento.categoria_approccio;
    if (categorie.includes(cat)) {
      contatori[cat]++;
    }
    labels.push(evento.round);
    categorie.forEach(c => serie[c].push(contatori[c]));
  });

  return { labels, serie };
});

// --- DATI STATICI (UI Menu) ---
const viewButtons = [
  { id: 'promotore', label: 'Promotore' },
  { id: 'banca', label: 'Banca' },
  { id: 'cliente', label: 'Cliente' },
  { id: 'evoluzione', label: 'Evoluzione Cliente' },
];

const scenarioPills = [
  //{ id: 'S0', label: 'Base' },
  // { id: 'S1', label: 'Espansione' },
  // { id: 'S2', label: 'Rialzo tassi' },
  // { id: 'S3', label: 'Stress' },
  // { id: 'S4', label: 'Recessione' },
  { id: 'S0_fix12', label: 'Base' },
  { id: 'S1_fix12', label: 'Espansione' },
  { id: 'S2_fix12', label: 'Rialzo tassi' },
  { id: 'S3_fix12', label: 'Opportunità' },
  { id: 'S4_fix12', label: 'Biforcazione' },
];

const domandePredefiniteStandard = [
  "Quale profilo di rischio sta soffrendo di più?",
  "Spiegami il trend della compliance per questo scenario",
  "Analizza il sentiment di mercato e l'impatto sulle commissioni",
  "Quali sono i rischi principali per la prossima finestra temporale?"
];

const domandePredefiniteCliente = [
  'Quale cluster manifesta il punto di minimo nella fiducia?',
  'Come possiamo manipolare le direttive per neutralizzare le 1237 Anomalie di Conformità (MiFID)?',
  'Analizza i punti di massimo della stabilità psicologica sulla Consulenza Adattiva',
  'Che tipo di correzione strategica serve per il cluster a rischio Churn?'
];

const quickQuestions = computed(() => {
  return view.value === 'cliente' ? domandePredefiniteCliente : domandePredefiniteStandard;
});

// FINSIM-MOD: Chart code to Italian name mapping (STEP 3 - Dynamic Integration)
const nomiGrafici = {
  'TREND_COMPLIANCE': 'Trend di Conformità Normativa (Anomalie MiFID)',
  'SEMAFORO_ADEGUATEZZA': 'Stato Adeguatezza Proposte (Semaforo)',
  'SANKEY_FLUSSI': 'Analisi di Sopravvivenza Clienti (Kaplan-Meier)',
  'HEATMAP_PERFORMANCE': 'Mappa del Vantaggio Strategico',
  'ANDAMENTO_GUADAGNI': 'Evoluzione Ricavi Cumulati',
  'BAR_PRODOTTI': 'Soddisfazione per Tipologia Prodotto',
  'INTERESSE_COMPOSTO': 'Proiezione Interesse Composto',
  'ACCETTAZIONI_SCENARI': 'Proposte Accettate vs Rifiutate',
  'LINEE_COMPARATIVE': 'Trend Raccolta nei 200 Round',
  'WATERFALL_PATRIMONIO': 'Scomposizione AUM (Variazioni)',
  'AREA_GUADAGNI': 'Andamento Ricavi nei 200 Round',
  'SPIDER_SENTIMENT': 'Radar Matrix: Sentiment & Psicologia del Portafoglio'
};

// FINSIM-MOD: Chart code to API endpoint mapping
const chartCodeToEndpoint = {
  'TREND_COMPLIANCE': '/api/charts/compliance',
  'SEMAFORO_ADEGUATEZZA': '/api/charts/semaforo',
  'SANKEY_FLUSSI': '/api/charts/sopravvivenza',
  'HEATMAP_PERFORMANCE': '/api/charts/heatmap',
  'ANDAMENTO_GUADAGNI': '/api/charts/guadagni',
  'AREA_GUADAGNI': '/api/charts/guadagni',
  'BAR_PRODOTTI': '/api/charts/prodotti',
  'INTERESSE_COMPOSTO': '/api/charts/interesse-composto',
  'ACCETTAZIONI_SCENARI': '/api/charts/accettazioni',
  'LINEE_COMPARATIVE': '/api/charts/linee-comparative',
  'WATERFALL_PATRIMONIO': '/api/charts/waterfall',
  'SPIDER_SENTIMENT': '/api/charts/client-sentiment'
};

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

const nextBestActionsTradotte = computed(() => {
  const traduzioni = {
    'Alert CONSOB/MIFID': 'Avvertenza Normativa',
    'Rischio churn': 'Rischio Abbandono',
    'ADAPT': 'Consulenza IA Dinamica',
    'FISSO': 'Strategia Standard',
    'Alert MIFID': 'Avvertenza Normativa',
    'Churn Risk': 'Rischio Abbandono',
    'Compliance Alert': 'Avvertenza Normativa'
  };

  return (datiPromotore.value.next_best_actions || []).map(action => {
    let translated = action;
    for (const [old, neu] of Object.entries(traduzioni)) {
      translated = translated.replace(new RegExp(old, 'g'), neu);
    }
    return translated;
  });
});

// FINSIM-MOD: Heatmap Propensione al Rischio con Assi Leggibili (data-driven)
const heatmapConAssi = computed(() => {
  // Usa dati reali da MongoDB se disponibili, fallback a valori statici
  const righe = datiCliente.value.risk_profili.length ? datiCliente.value.risk_profili : ['Alto Rischio', 'Medio Rischio', 'Basso Rischio', 'Conservativo'];
  const valori = datiCliente.value.risk_matrice.length ? datiCliente.value.risk_matrice : [
    [88, 82, 75, 70, 65],
    [91, 85, 79, 73, 68],
    [78, 72, 66, 58, 48],
    [62, 54, 44, 32, 22]
  ];

  return righe.map((label, i) => ({
    label,
    cells: (valori[i] || []).map(v => {
      let bg = '#D64242', fg = '#FFFFFF';
      if (v >= 85) { bg = '#1E9E63'; fg = '#062017'; }
      else if (v >= 70) { bg = '#7DB85A'; fg = '#10240A'; }
      else if (v >= 55) { bg = '#E0922F'; fg = '#2E1C05'; }
      else if (v >= 42) { bg = '#D9703A'; fg = '#2E1305'; }
      return { value: v + '%', bg, fg };
    })
  }));
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
  
  // Configurazione globale per snellire l'asse X sui 200 round (Tentativi di Proposta)
  const xAxisConfig = {
    x: {
      ticks: {
        autoSkip: false,
        callback: function(value, index, values){
          if (index === 0) return 'Prop. 1';
          if ((index + 1) % 40 === 0 && index < 199) return 'Prop. ' + (index + 1);
          if (index === 199) return 'Prop. 200';
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
    // Helper: Media mobile dinamica con finestra stretta per mantenere trend chiari
    const movingAverage = (arr, windowSize = 10) => arr.map((val, idx, list) => {
      const start = Math.max(0, idx - windowSize + 1);
      const subset = list.slice(start, idx + 1);
      return subset.reduce((a, b) => a + b, 0) / subset.length;
    });

    // Helper: Aggregazione in blocchi
    const aggregateInBlocks = (arr, blockSize = 20) => {
      const blocks = [];
      for (let i = 0; i < arr.length; i += blockSize) {
        const block = arr.slice(i, i + blockSize);
        blocks.push(block.reduce((a, b) => a + b, 0));
      }
      return blocks;
    };

    // Assicura che i labels arrivino a 200 proposte
    let promotoreLabels = datiGraficiPromotore.value.labels.length ? datiGraficiPromotore.value.labels : Array.from({length:200}, (_,i)=>'Prop. '+(i+1));
    if (promotoreLabels.length < 200) {
      promotoreLabels = Array.from({length:200}, (_,i)=>promotoreLabels[i] || 'Prop. '+(i+1));
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

    // COMPLIANCE - con media mobile dinamica (windowSize=10) e zoom verticale
    // Fallback: zeri, non dati sintetici
    const complianceAdaptSmoothed = movingAverage(complianceAdapt.length ? complianceAdapt : Array.from({length:200}, ()=>0));
    const complianceFissoSmoothed = movingAverage(complianceFisso.length ? complianceFisso : Array.from({length:200}, ()=>0));

    // Configurazione asse X ogni 20 proposte
    const complianceXConfig = {
      ...xAxisConfig.x,
      ticks: {
        autoSkip: false,
        callback: (val, index) => (index === 0) ? 'Prop. 1' : ((index + 1) % 20 === 0) ? 'Prop. ' + (index + 1) : (index === 199) ? 'Prop. 200' : '',
        color: '#8593A8'
      }
    };

    mkChart('pCompliance', {
      type: 'line',
      data: {
        labels: promotoreLabels,
        datasets: [
          { label: 'Consulenza IA Adattiva', data: complianceAdaptSmoothed, borderColor: ADAPT, backgroundColor: 'rgba(23,138,87,.05)', fill: true, tension: 0.4, borderWidth: 2.5, pointRadius: 0 },
          { label: 'Strategia Standard (Benchmark)', data: complianceFissoSmoothed, borderColor: FISSO, borderDash: [5, 4], backgroundColor: 'rgba(46,111,214,.05)', fill: true, tension: 0.4, borderWidth: 2.5, pointRadius: 0 }
        ]
      },
      options: {
        ...baseCfg,
        plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } },
        scales: {
          x: complianceXConfig,
          y: { suggestedMin: 40, suggestedMax: 95 }  // Zoom verticale dinamico
        }
      }
    });

    // ACCETTATE - aggregato in 10 blocchi da 20
    // Fallback: zeri, non dati sintetici
    const blockLabels = ['Prop. 1-20', 'Prop. 21-40', 'Prop. 41-60', 'Prop. 61-80', 'Prop. 81-100', 'Prop. 101-120', 'Prop. 121-140', 'Prop. 141-160', 'Prop. 161-180', 'Prop. 181-200'];
    const accettateAdaptAgg = aggregateInBlocks(accettateAdapt.length ? accettateAdapt : Array.from({length:200}, ()=>0));
    const accettateFissoAgg = aggregateInBlocks(accettateFisso.length ? accettateFisso : Array.from({length:200}, ()=>0));

    mkChart('pAccept', {
      type: 'bar',
      data: {
        labels: blockLabels,
        datasets: [
          { label: 'Accettate Consulenza Adattiva', data: accettateAdaptAgg, backgroundColor: '#1E9E63' },
          { label: 'Accettate Strategia Standard', data: accettateFissoAgg, backgroundColor: '#2E6FD6' }
        ]
      },
      options: { ...baseCfg, scales: { x: { ticks: { color: '#8593A8' }, grid: { display: false } } }, plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } } }
    });

  } else if (view.value === 'banca') {
    // Assicura che i labels arrivino a 200 proposte
    let bancaLabels = trendData.value.labels.length ? trendData.value.labels : Array.from({length:200}, (_,i)=>'Prop. '+(i+1));
    if (bancaLabels.length < 200) {
      bancaLabels = Array.from({length:200}, (_,i)=>bancaLabels[i] || 'Prop. '+(i+1));
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
    
    // RADAR BANCA - Data-driven da MongoDB
    (async () => {
      let radarTarget = [80, 90, 20, 10, 85];
      let radarAttuale = [0, 0, 0, 0, 0];

      try {
        const rr = await fetch(`http://10.12.7.53:8000/api/charts/radar-banca-direttiva?scenario_id=${scenario.value}`);
        if (rr.ok) {
          const rd = await rr.json();
          radarTarget = rd.target || radarTarget;
          radarAttuale = rd.attuale || radarAttuale;
          console.log('[bRadar] Dati caricati da API');
        }
      } catch (err) {
        console.warn('[bRadar] Errore fetch API, fallback a dati statici:', err.message);
      }

      mkChart('bRadar', {
        type: 'radar',
        data: {
          labels: ['Bond Corp', 'Monetario', 'Azionario', 'Illiquidi', 'Gov Bond'],
          datasets: [
            { label: 'Target Direttiva', data: radarTarget, borderColor: TARGET, borderDash: [4, 4], backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0 },
            { label: 'Portafoglio Attuale', data: radarAttuale, borderColor: FISSO, backgroundColor: 'rgba(46,111,214,.18)', borderWidth: 2 }
          ]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } }, scales: { r: { suggestedMin: 0, suggestedMax: 100 } } }
      });
    })();
  
  } else if (view.value === 'cliente') {
    // FINSIM-MOD: FIDUCIA - Data-driven da MongoDB via API
    (async () => {
      let fiduciaAdapt = [], fiduciaFisso = [], fiduciaLabels = [];

      try {
        const res = await fetch(`http://10.12.7.53:8000/api/charts/fiducia-evolution?scenario_id=${scenario.value}`);
        if (res.ok) {
          const data = await res.json();
          fiduciaAdapt = data.fiducia_adapt || [];
          fiduciaFisso = data.fiducia_fisso || [];
          fiduciaLabels = data.labels || [];
          console.log('[cFiducia] Dati caricati da API:', { adapt: fiduciaAdapt.length, fisso: fiduciaFisso.length });
        }
      } catch (err) {
        console.warn('[cFiducia] Errore fetch API, fallback a dati statici:', err.message);
      }

      // Fallback se vuoti
      if (!fiduciaAdapt.length) fiduciaAdapt = Array.from({length: 200}, () => 50);
      if (!fiduciaFisso.length) fiduciaFisso = Array.from({length: 200}, () => 55);
      if (!fiduciaLabels.length) fiduciaLabels = Array.from({length: fiduciaAdapt.length}, (_, i) => `P${i + 1}`);

      // Media mobile a 15 periodi
      const smoothingWindow = (arr) => arr.map((_, idx, list) => {
        const window = list.slice(Math.max(0, idx - 14), idx + 1);
        return window.reduce((a, b) => a + b, 0) / window.length;
      });

      const fiduciaAdaptSmoothed = smoothingWindow(fiduciaAdapt);
      const fiduciaFissoSmoothed = smoothingWindow(fiduciaFisso);

      mkChart('cFiducia', {
        type: 'line',
        data: {
          labels: fiduciaLabels,
          datasets: [
            {
              label: 'Fiducia Consulenza Adattiva',
              data: fiduciaAdaptSmoothed,
              borderColor: ADAPT,
              backgroundColor: 'rgba(23,138,87,0.1)',
              fill: true,
              tension: 0.4,
              borderWidth: 2.5,
              pointRadius: 0
            },
            {
              label: 'Fiducia Strategia Standard',
              data: fiduciaFissoSmoothed,
              borderColor: FISSO,
              backgroundColor: 'rgba(46,111,214,0.1)',
              fill: true,
              tension: 0.4,
              borderWidth: 2.5,
              borderDash: [5, 4],
              pointRadius: 0
            }
          ]
        },
        options: {
          ...baseCfg,
          plugins: {
            legend: { display: true, position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } }
          },
          scales: {
            x: {
              ticks: {
                autoSkip: false,
                callback: (val, index) => (index === 0) ? 'P1' : ((index + 1) % 40 === 0) ? `P${index + 1}` : (index === fiduciaAdapt.length - 1) ? `P${index + 1}` : '',
                color: '#8593A8'
              },
              grid: { display: false }
            },
            y: {
              suggestedMin: 0,
              suggestedMax: 100,
              ticks: { color: '#8593A8', callback: val => val + '%' }
            }
          }
        }
      });
    })();

    // RADAR CLIENTE - Profilo vs Portafoglio - Data-driven da MongoDB
    (async () => {
      let profiloLabels = ['Profilo Rischio', 'Fiducia Cliente', 'Adeguatezza Proposta'];
      let profiloDichiarato = [35, 70, 75];
      let portagifolioAssegnato = [40, 58, 48];

      try {
        const res = await fetch(`http://10.12.7.53:8000/api/charts/profilo-portafoglio?scenario_id=${scenario.value}`);
        if (res.ok) {
          const data = await res.json();
          profiloLabels = data.labels || profiloLabels;
          profiloDichiarato = data.profilo_dichiarato || profiloDichiarato;
          portagifolioAssegnato = data.portafoglio_assegnato || portagifolioAssegnato;
          console.log('[cRadar] Dati caricati da API');
        }
      } catch (err) {
        console.warn('[cRadar] Errore fetch API, fallback a dati statici:', err.message);
      }

      mkChart('cRadar', {
        type: 'radar',
        data: {
          labels: profiloLabels,
          datasets: [
            {
              label: 'Profilo Dichiarato',
              data: profiloDichiarato,
              borderColor: FISSO,
              backgroundColor: 'rgba(46,111,214,.16)',
              borderDash: [4, 4],
              borderWidth: 2,
              pointRadius: 0
            },
            {
              label: 'Portafoglio Assegnato',
              data: portagifolioAssegnato,
              borderColor: ADAPT,
              backgroundColor: 'rgba(23,138,87,.16)',
              borderWidth: 2,
              pointRadius: 0
            }
          ]
        },
        options: {
          ...baseCfg,
          plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } },
          scales: { r: { suggestedMin: 0, suggestedMax: 100 } }
        }
      });
    })();
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

    // 5. Fetch dati cliente (fiducia evolution, profilo, risk heatmap)
    try {
      console.log('[FINsim] Fetching /api/charts/fiducia-evolution...');
      const resFiducia = await fetchWithTimeout(`${baseURL}/api/charts/fiducia-evolution?scenario_id=${currentScenario}`, 8000);
      if (resFiducia.ok) {
        const dataFiducia = await resFiducia.json();
        datiCliente.value.labels = dataFiducia.labels || [];
        datiCliente.value.fiducia_adapt = dataFiducia.fiducia_adapt || [];
        datiCliente.value.fiducia_fisso = dataFiducia.fiducia_fisso || [];
        console.log(`[FINsim] ✓ Fiducia evolution caricata: ${dataFiducia.labels?.length || 0} rounds`);
      } else {
        console.warn(`[FINsim] ⚠ Endpoint fiducia-evolution returned ${resFiducia.status}`);
      }
    } catch (err) {
      console.error('[FINsim] ✗ Error fetching fiducia-evolution:', err.message);
    }

    // 6. Fetch dati profilo-portafoglio
    try {
      console.log('[FINsim] Fetching /api/charts/profilo-portafoglio...');
      const resProfilo = await fetchWithTimeout(`${baseURL}/api/charts/profilo-portafoglio?scenario_id=${currentScenario}`, 8000);
      if (resProfilo.ok) {
        const dataProfilo = await resProfilo.json();
        datiCliente.value.profilo_dichiarato = dataProfilo.profilo_dichiarato || [];
        datiCliente.value.portafoglio_assegnato = dataProfilo.portafoglio_assegnato || [];
        datiCliente.value.profilo_labels = dataProfilo.labels || [];
        console.log(`[FINsim] ✓ Profilo-portafoglio caricato`);
      } else {
        console.warn(`[FINsim] ⚠ Endpoint profilo-portafoglio returned ${resProfilo.status}`);
      }
    } catch (err) {
      console.error('[FINsim] ✗ Error fetching profilo-portafoglio:', err.message);
    }

    // 7. Fetch risk propensity heatmap
    try {
      console.log('[FINsim] Fetching /api/charts/risk-propensity-heatmap...');
      const resRisk = await fetchWithTimeout(`${baseURL}/api/charts/risk-propensity-heatmap?scenario_id=${currentScenario}`, 8000);
      if (resRisk.ok) {
        const dataRisk = await resRisk.json();
        datiCliente.value.risk_matrice = dataRisk.matrice || [];
        datiCliente.value.risk_profili = dataRisk.profili || [];
        datiCliente.value.risk_patrimoni = dataRisk.patrimoni || [];
        console.log(`[FINsim] ✓ Risk propensity heatmap caricata`);
      } else {
        console.warn(`[FINsim] ⚠ Endpoint risk-propensity-heatmap returned ${resRisk.status}`);
      }
    } catch (err) {
      console.error('[FINsim] ✗ Error fetching risk-propensity-heatmap:', err.message);
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

      // Salva nella cronologia conversazionale
      conversationHistory.value.push({
        id: Date.now(),
        question: messaggioUtente,
        brief: aiResponseBrief.value,
        detail: aiResponseDetail.value,
        timestamp: new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
      });
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

// FINSIM-MOD: Chart explanation via LLM
const apriSpiegazioneGrafico = async (chartId, chartTitle) => {
  showChartModal.value = true;
  chartModalTitle.value = chartTitle;
  chartModalSpiegazione.value = '';
  chartModalLoading.value = true;

  const descrizioniGrafici = {
    'bRaccolta': 'Grafico lineare che mostra la raccolta netta cumulata in milioni di euro su 200 proposte commerciali, confrontando Consulenza IA Adattiva (verde) vs Strategia Standard (blu).',
    'bRadar': 'Radar chart che mostra il profilo di allocation della banca su 5 dimensioni: Bond Corp, Monetario, Azionario, Illiquidi, Gov Bond. Verde = portafoglio attuale, grigio tratteggiato = target direttiva.',
    'plotly-heatmap': 'Heatmap che mostra il vantaggio della Consulenza IA Adattiva vs Strategia Standard per ogni combinazione di Patrimonio (basso/medio/alto) e Profilo di Rischio (basso/medio/alto). Celle verdi = IA domina, celle rosse = Standard domina.',
    'plotly-waterfall': 'Grafico a cascata che scompone il patrimonio gestito finale: partendo dal patrimonio iniziale, aggiungendo nuova raccolta, effetto mercato e sottraendo gli abbandoni clienti.',
    'plotly-lines': 'Linee comparative della raccolta cumulata su 200 proposte: Consulenza IA Adattiva (verde) vs Strategia Standard (rosso).',
    'plotly-spider-banca': 'Radar chart con 5 dimensioni strategiche della banca: Compliance, Raccolta, Fiducia Cliente, Aderenza Direttiva, Redditività. Verde = ADAPT, grigio = target banca.',
    'pCompliance': 'Grafico lineare della conformità/adeguatezza media per proposta commerciale. Confronto Consulenza Adattiva vs Strategia Standard su 200 proposte.',
    'pAccept': 'Grafico a barre delle proposte accettate aggregate in 10 blocchi da 20 proposte ciascuno. Verde = Consulenza Adattiva, Blu = Strategia Standard.',
    'plotly-heatmap-promotore': 'Heatmap del vantaggio strategico per cluster clienti, vista dal punto di vista del promotore.',
    'plotly-sopravvivenza': 'Curva di sopravvivenza Kaplan-Meier che mostra il tasso di retention clienti nel tempo. I gradini verso il basso indicano abbandoni.',
    'cFiducia': 'Curva di fiducia media dei clienti su 200 proposte, con media mobile a 15 periodi per eliminare il rumore.',
    'cRadar': 'Radar chart che confronta il profilo/soglia di riferimento (blu) con il portafoglio effettivamente assegnato (verde) su 3 dimensioni con dati reali: Profilo Rischio, Fiducia Cliente, Adeguatezza Proposta.',
    'spider-sentiment-clienti': 'Spider chart con 5 dimensioni psicologiche del cliente: Fiducia Percepita, Soddisfazione Proposta, Resilienza al Churn, Aderenza Normativa, Stabilità Comportamentale.',
    'plotly-cluster-evolution': 'Grafico a dispersione che mostra i momenti di cambio strategico del promotore verso un segmento specifico di clientela. Ogni pallino colorato rappresente un cambio di approccio: ross=Aggressiva, blu=Conservativa, verde=Relazionale. L\'asse Y mostra la fiducia del cliente (0-100%), la linea tratteggiata blu mostra l\'adeguatezza della proposta.',
    'plotly-cumulativa-categoria': 'Grafico ad area cumulativa che mostra quante volte ciascuna categoria di approccio strategico è stata utilizzata nel corso dei 200 round. Le linee mostrano l\'evoluzione dell\'approccio dominante nel tempo.',
    'heatmap-banca': 'Griglia che mostra il differenziale di conversione tra Conulenza Adattiva e Strategia Standard per ogni combinazione di Profilo di Rischio (righe) e Patrimonio del Cliente (colonne). Valori positivi in verde indicano che la Consulenza Adattiva converte meglio in quel segmento. Valori negativi in rosso indicano che la Strategia Standard è più efficace.',
    'heatmap-promotore': 'Griglia che mostra il differenziale di conversione tra Consulenza Adattiva e Strategia Standard per ogni segmento di clientela. Valori positivi in verde indicano che la Consulenza Adattiva converte meglio. Valori negativi in rosso indicano che Strategia Standard è più efficace in quel cluster.',
  };

  const descrizione = descrizioniGrafici[chartId] || `Grafico ${chartTitle} della dashboard FINsim.`;

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
        churn_risk_count: datiPromotore.value.alerts?.churn_risk_count || 0,
        mifid_alerts_count: datiPromotore.value.alerts?.mifid_alerts_count || 0,
      },
      user_message: `Spiega in modo chiaro e professionale questo grafico: ${descrizione}. Fornisci: 1) Come si legge il grafico (2-3 frasi), 2) Cosa indicano i dati attuali per lo scenario ${scenario.value} (3-4 frasi), 3) Raccomandazione strategica concreta (2 frasi). Usa linguaggio da consulente finanziario senior italiano, mai gergo informatico.`
    };

    const res = await fetch('http://10.12.7.53:8000/api/advisor/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      chartModalSpiegazione.value = data.dettaglio_risposta || data.suggerimento_breve || 'Spiegazione non disponibile.';
    } else {
      chartModalSpiegazione.value = 'Errore nel caricamento della spiegazione.';
    }
  } catch (error) {
    console.error('Errore nella chiamata grafico explanation:', error);
    chartModalSpiegazione.value = 'Errore nel caricamento della spiegazione.';
  } finally {
    chartModalLoading.value = false;
  }
};

const shouldRenderChart = (codice) => {
  return false;
};

let aiChartInstances = [];

const renderPlotlyChart = async (endpoint, divId, scenario_id = 'S0') => {
  try {
    await loadPlotly();
    await nextTick();

    // Leggi dati reali da MongoDB per questo scenario
    let metricsReali = {
      scenario_corrente: scenario_id,
      commissioni_cumulate_adapt: datiPromotore.value.adapt?.commissioni_cumulate || 0,
      commissioni_cumulate_fisso: datiPromotore.value.fisso?.commissioni_cumulate || 0,
      tasso_conversione_adapt_pct: datiPromotore.value.adapt?.tasso_conversione_pct || 0,
      tasso_conversione_fisso_pct: datiPromotore.value.fisso?.tasso_conversione_pct || 0,
      fiducia_media_adapt: datiPromotore.value.adapt?.fiducia_media || 0,
      fiducia_media_fisso: datiPromotore.value.fisso?.fiducia_media || 0,
      proposte_totali_adapt: datiPromotore.value.adapt?.proposte_totali || 0,
      proposte_totali_fisso: datiPromotore.value.fisso?.proposte_totali || 0,
      matrice_performance: [[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]],
      aum_iniziale: 100000000,
      nuova_raccolta_netta: 0,
      effetto_mercato: 0,
      patrimonio_perso_churn: 0
    };

    // Fetch dati specifici per tipo di grafico
    if (endpoint.includes('waterfall')) {
      try {
        const r = await fetch(`http://10.12.7.53:8000/api/charts/waterfall-data?scenario_id=${scenario_id}`);
        if (r.ok) {
          const d = await r.json();
          metricsReali.aum_iniziale = d.aum_iniziale;
          metricsReali.nuova_raccolta_netta = d.nuova_raccolta;
          metricsReali.effetto_mercato = d.effetto_mercato;
          metricsReali.patrimonio_perso_churn = d.churn;
        }
      } catch (e) { console.warn('[Waterfall] Fallback a dati statici:', e.message); }
    }

    if (endpoint.includes('heatmap')) {
      try {
        const r = await fetch(`http://10.12.7.53:8000/api/charts/heatmap-data?scenario_id=${scenario_id}`);
        if (r.ok) {
          const d = await r.json();
          metricsReali.matrice_performance = d.matrice;
        }
      } catch (e) { console.warn('[Heatmap] Fallback a dati statici:', e.message); }
    }

    const payload = { metrics_data: metricsReali, user_message: "" };

    const res = await fetch(`http://10.12.7.53:8000${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      let figData = typeof data.data === 'string' ? JSON.parse(data.data) : data.data;
      if (!figData.data || !figData.layout) {
        figData = { data: figData.data || figData, layout: figData.layout || {} };
      }
      const el = document.getElementById(divId);
      if (!el) { console.error(`DOM element #${divId} non trovato`); return; }
      if (window.Plotly) {
        if (divId === 'plotly-waterfall') {
          figData.layout = {
            ...figData.layout,
            showlegend: false,
            margin: { l: 60, r: 30, t: 70, b: 30 },
            xaxis: { ...figData.layout?.xaxis, automargin: true },
            yaxis: { ...figData.layout?.yaxis, automargin: true },
          };
        }
        Plotly.newPlot(divId, figData.data, figData.layout, { responsive: true });
      }

    } else {
      console.error(`Errore API Plotly ${endpoint}: ${res.status}`);
    }
  } catch (error) {
    console.error(`Errore nel rendering Plotly ${divId}:`, error);
  }
};

// Renderizza grafico evoluzione cluster con Fiducia e Adeguatezza
const renderClusterEvolutionChart = async () => {
  await loadPlotly();
  await nextTick();

  const el = document.getElementById('plotly-cluster-evolution');
  const rounds = eventiTransizione.value;
  if (!el || !rounds || rounds.length === 0) return;

  const xRounds = rounds.map(e => e.round);
  const fiducia = rounds.map(e => e.fiducia_media_post * 100);
  const adeguatezza = rounds.map(e => e.adeguatezza_score * 100);
  const traceColors = rounds.map(e => categoriaColori[e.categoria_approccio] || '#8593A8');
  const hoverText = rounds.map(e => `Round ${e.round}<br>${e.categoria_approccio}<br>Fiducia: ${(e.fiducia_media_post*100).toFixed(0)}%<br>Adeguatezza: ${(e.adeguatezza_score*100).toFixed(0)}%`);

  const traces = [
    {
      x: xRounds,
      y: adeguatezza,
      type: 'scatter',
      mode: 'lines',
      name: 'Adeguatezza Proposta (linea tratteggiata)',
      line: { color: 'rgba(46,111,214,0.5)', width: 2, dash: 'dot' },
      hoverinfo: 'skip'
    },
    {
      x: xRounds,
      y: fiducia,
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Fiducia Cliente (colore per categoria approccio)',
      line: { color: 'rgba(199,213,230,0.15)', width: 1 },
      marker: { size: 7, color: traceColors, line: { width: 1, color: '#ffffff' } },
      text: hoverText,
      hoverinfo: 'text'
    }
  ];
  const layout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(30,41,59,0.3)',
    font: { color: '#C7D5E6', family: 'Segoe UI, sans-serif' },
    xaxis: {
      title: { text: 'Round di Simulazione', font: { size: 12, color: '#8593A8' } },
      gridcolor: 'rgba(199,213,230,0.08)',
      tickfont: { size: 11, color: '#8593A8' },
      margin: { l: 60, 4: 30, t: 50, b: 80 },
      dragmode: 'zoom',
      modebar: { orientation: 'v' }
  },
  yaxis: {
    title: { text: 'Percentuale (%)', font: { size: 12, color: '#8593A8' } },
    range: [0, 100],
    gridcolor: 'rgba(199,213,230,0.08)',
    tickfont: { size: 11, color: '#8593A8' },
    ticksuffix: '%'
  },
  legend: {
    orientation: 'h',
    yanchor: 'bottom',
    y: -0.25,
    xanchor: 'center',
    x: 0.5,
    font: { size: 11, color: '#C7D5E6' },
    bgcolor: 'rgba(0,0,0,0)'
  },
  annotations: [
    {
      x: 0.01, y: 1.05, xref: 'paper', yref: 'paper',
      text: '🔴 Aggressiva  🔵 Conservativa  🟠 Informativa  🟢 Relazionale',
      showarrow: false,
      font: { size: 11, color: '#C7D5E6' },
      align: 'left'
     }
  ],
  margin: { l: 60, r: 30, t: 50, b: 80 }
};

  Plotly.newPlot('plotly-cluster-evolution', traces, layout, { responsive: true });
};

const renderCumulativaCategoria = async () => {
  await loadPlotly();
  await nextTick();

  const el = document.getElementById('plotly-cumulativa-categoria');
  const dati = cumulativaCategoria.value;
  if (!el || !dati.labels || dati.labels.length === 0) return;

  const traces = ['Aggressiva', 'Conservativa', 'Informativa', 'Relazionale'].map(cat => ({
    x: dati.labels,
    y: dati.serie[cat],
    type: 'scatter',
    mode: 'lines',
    name: cat,
    line: { color: categoriaColori[cat], width: 2 },
    fill: 'tozeroy',
    fillcolor: categoriaColori[cat] + '20'
  }));

  const layout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(30,41,59,0.3)',
    font: { color: '#C7D5E6' },
    xaxis: { title: 'Round', gridcolor: 'rgba(199,213,230,0.1)' },
    yaxis: { title: 'Utilizzo cumulativo', gridcolor: 'rgba(199,213,230,0.1)' },
    legend: { orientation: 'h', yanchor: 'bottom', y: -0.25, xanchor: 'center', x: 0.5 },
    margin: { l: 60, r: 30, t: 20, b: 80 }
  };

  Plotly.newPlot('plotly-cumulativa-categoria', traces, layout, { responsive: true });
};

const renderSpiderBanca = async () => {
  try{
    await loadPlotly();
    await nextTick();
    const targetDiv = document.getElementById('plotly-spider-banca');
    if (!targetDiv) { console.error('[Spider Banca] DIV non trovato'); return; }
    const res = await fetch(`http://10.12.7.53:8000/api/dati-banca-spider?scenario_id=${scenario.value}`);
    if (!res.ok) throw new Error(`API Error ${res.status}`);
    const data = await res.json();
    const adapt = data.adapt || [0,0,0,0,0];
    const target = data.target || [90,80,75,70,85];
    const labels = data.labels || ['Compliance','Raccolta','Fiducia Cliente','Aderenza Direttiva','Redditività'];
    const traces = [
      { type: 'scatterpolar', r: [...adapt, adapt[0]], theta: [...labels, labels[0]], fill: 'toself', opacity: 0.7, name: 'ADAPT (IA)', line: { color: '#1FA463', width: 3 } },
      { type: 'scatterpolar', r: [...target, target[0]], theta: [...labels, labels[0]], fill: 'toself', opacity: 0.3, name: 'Target Banca', line: { color: '#8593A8', width: 2, dash: 'dot' } }
    ];
    const layout = {
      polar: {
        bgcolor: 'rgba(30,41,59,0.5)',
        radialaxis: { visible: true, range: [0, 100], gridcolor: 'rgba(255,255,255,0.08)', linecolor: 'rgba(0,0,0,0)', tickfont: { color: '#94a3b8', size: 10 } },
        angularaxis: { gridcolor: 'rgba(255,255,255,0.08)', tickfont: { color: '#cbd5e0', size: 11 } }
      },
      showlegend: true,
      legend: { orientation: 'h', yanchor: 'bottom', y: -0.2, xanchor: 'center', x: 0.5, font: { color: '#cbd5e0', size: 11 } },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      margin: { t: 40, b: 40, l: 60, r: 60 }
    };
    Plotly.newPlot('plotly-spider-banca', traces, layout, { responsive: true});
    console.log('[Spider Banca] Renderizzato con successo');
  } catch (error) { console.error('[Spider Banca] Errore:', error.message); }
};

// Funzione dedicata per renderizzare la heatmap nella Vista Promotore
const renderHeatmapPromotore = async () => {
  try {
    console.log('[Heatmap Promotore] Inizio render...');

    // Carica Plotly se non è già disponibile
    await loadPlotly();
    console.log('[Heatmap Promotore] Plotly caricato:', !!window.Plotly);

    // Attendi che Vue abbia montato il div nel DOM
    await nextTick();
    console.log('[Heatmap Promotore] nextTick completato');
    let matriceReale = [[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]];
    try {
      const r = await fetch(`http://10.12.7.53:8000/api/charts/heatmap-data?scenario_id=${scenario.value}`);
      if (r.ok) {
        const d = await r.json();
        matriceReale = d.matrice;
      }
    } catch (e) { console.warn('[Heatmap Promotore] Fallback', e.message)}

    // Verifica che il div esista nel DOM
    const targetDiv = document.getElementById('plotly-heatmap-promotore');
    if (!targetDiv) {
      console.error('[Heatmap Promotore] ❌ DIV NON TROVATO nel DOM');
      return;
    }
    console.log('[Heatmap Promotore] ✓ DIV trovato:', targetDiv.style.width, targetDiv.style.height);

    // Prepara il payload
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
        matrice_performance: matriceReale,
        aum_iniziale: 100000000,
        nuova_raccolta_netta: 15500000,
        effetto_mercato: -3200000,
        patrimonio_perso_churn: -5800000
      },
      user_message: ""
    };

    // Fetch dai dati della heatmap
    console.log('[Heatmap Promotore] Fetching /api/charts/heatmap...');
    const res = await fetch('http://10.12.7.53:8000/api/charts/heatmap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`API Error ${res.status}: ${res.statusText}`);
    }

    const responseData = await res.json();
    console.log('[Heatmap Promotore] ✓ Response ricevuto, size:', JSON.stringify(responseData).length);

    // Parsifica il JSON della figura se è una stringa
    let figData = responseData.data;
    console.log('[Heatmap Promotore] Type of figData:', typeof figData);
    console.log('[Heatmap Promotore] figData is string?', typeof figData === 'string');

    if (typeof figData === 'string') {
      console.log('[Heatmap Promotore] Parsing JSON string...');
      figData = JSON.parse(figData);
      console.log('[Heatmap Promotore] ✓ Parsed JSON string, now type:', typeof figData);
    }

    // Verifica che figData abbia data e layout
    console.log('[Heatmap Promotore] figData keys:', Object.keys(figData).slice(0, 5));
    console.log('[Heatmap Promotore] Has .data?', !!figData.data, 'Has .layout?', !!figData.layout);

    if (!figData.data || !figData.layout) {
      console.error('[Heatmap Promotore] ❌ figData non ha structure corretta!');
      console.error('[Heatmap Promotore] Full figData:', JSON.stringify(figData).substring(0, 500));
      return;
    }

    console.log('[Heatmap Promotore] ✓ figData structure OK');
    console.log('[Heatmap Promotore] figData.data length:', figData.data.length);
    console.log('[Heatmap Promotore] drawing...');

    // Renderizza con Plotly
    if (window.Plotly) {
      Plotly.newPlot(
        'plotly-heatmap-promotore',
        figData.data,
        figData.layout,
        { responsive: true, displayModeBar: true }
      );
      console.log('[Heatmap Promotore] ✓✓ Grafico renderizzato con successo!');
    } else {
      console.error('[Heatmap Promotore] ❌ window.Plotly non disponibile');
    }
  } catch (error) {
    console.error('[Heatmap Promotore] ❌ Errore:', error.message);
    console.error('[Heatmap Promotore] Stack:', error.stack);
  }
};

// Funzione dedicata per renderizzare la Curva di Sopravvivenza (Kaplan-Meier)
const renderSopravvivenza = async () => {
  try {
    console.log('[Sopravvivenza] Inizio render curva Kaplan-Meier...');

    // Carica Plotly se non è già disponibile
    await loadPlotly();
    console.log('[Sopravvivenza] Plotly caricato:', !!window.Plotly);

    // Attendi che Vue abbia montato il div nel DOM
    await nextTick();
    console.log('[Sopravvivenza] nextTick completato');

    // Verifica che il div esista nel DOM
    const targetDiv = document.getElementById('plotly-sopravvivenza');
    if (!targetDiv) {
      console.error('[Sopravvivenza] ❌ DIV NON TROVATO nel DOM');
      return;
    }
    console.log('[Sopravvivenza] ✓ DIV trovato:', targetDiv.style.width, targetDiv.style.height);

    // Prepara il payload
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
        matrice_performance: [[1.5, -0.4, 2.1], [-0.8, 0.0, 1.2], [0.5, -1.1, -0.2]],
        aum_iniziale: 100000000,
        nuova_raccolta_netta: 15500000,
        effetto_mercato: -3200000,
        patrimonio_perso_churn: -5800000
      },
      user_message: ""
    };

    // Fetch dai dati della curva di sopravvivenza
    console.log('[Sopravvivenza] Fetching /api/charts/sopravvivenza...');
    const res = await fetch('http://10.12.7.53:8000/api/charts/sopravvivenza', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`API Error ${res.status}: ${res.statusText}`);
    }

    const responseData = await res.json();
    console.log('[Sopravvivenza] ✓ Response ricevuto, size:', JSON.stringify(responseData).length);

    // Parsifica il JSON della figura se è una stringa
    let figData = responseData.data;
    if (typeof figData === 'string') {
      figData = JSON.parse(figData);
      console.log('[Sopravvivenza] ✓ Parsed JSON string');
    }

    // Verifica che figData abbia data e layout
    if (!figData.data || !figData.layout) {
      console.error('[Sopravvivenza] ❌ figData non ha structure corretta:', Object.keys(figData));
      return;
    }

    console.log('[Sopravvivenza] ✓ figData structure OK, drawing...');

    // Renderizza con Plotly
    if (window.Plotly) {
      Plotly.newPlot(
        'plotly-sopravvivenza',
        figData.data,
        figData.layout,
        { responsive: true, displayModeBar: true }
      );
      console.log('[Sopravvivenza] ✓✓ Curva renderizzata con successo!');
    } else {
      console.error('[Sopravvivenza] ❌ window.Plotly non disponibile');
    }
  } catch (error) {
    console.error('[Sopravvivenza] ❌ Errore:', error.message);
    console.error('[Sopravvivenza] Stack:', error.stack);
  }
};

// FINSIM-MOD: Carica e renderizza il pannello Customer Sentiment (Vista Cliente)
const caricaVistaCliente = async () => {
  try {
    console.log('[Client Sentiment] Inizio caricamento Vista Cliente per scenario:', scenario.value);

    await loadPlotly();
    await nextTick();

    const targetDiv = document.getElementById('spider-sentiment-clienti');
    if (!targetDiv) {
      console.error('[Client Sentiment] ❌ DIV #spider-sentiment-clienti non trovato');
      return;
    }

    console.log('[Client Sentiment] Scenario corrente:', scenario.value, 'Type:', typeof scenario.value);

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
        proposte_totali_fisso: datiPromotore.value.fisso?.proposte_totali || 0
      }
    };

    console.log('[Client Sentiment] Fetching /api/charts/client-sentiment...');
    console.log('[Client Sentiment] Payload inviato:', JSON.stringify(payload).substring(0, 200) + '...');
    const res = await fetch('http://10.12.7.53:8000/api/charts/client-sentiment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      console.error(`[Client Sentiment] API Error ${res.status}`);
      return;
    }

    let rawData = await res.json();
    console.log('[Client Sentiment] Raw response type:', typeof rawData, 'has .data?', !!rawData.data);

    // Forza il parsing se il backend ha restituito una stringa
    let figData = typeof rawData === 'string' ? JSON.parse(rawData) : rawData;
    if (typeof figData.data === 'string') {
      figData.data = JSON.parse(figData.data);
    }

    await nextTick();

    console.log('[Client Sentiment] Parsed figData structure:', {
      hasData: !!figData.data,
      hasLayout: !!figData.layout,
      dataType: typeof figData.data,
      layoutType: typeof figData.layout
    });

    if (figData.data && figData.layout && window.Plotly) {
      console.log('[Client Sentiment] ✓ Renderizzando Spider Chart...');

      // FINSIM-MOD: Layout override con margini generosi per le label
      const layoutOverride = {
        ...figData.layout,
        margin: { t: 60, b: 60, l: 80, r: 80 },
        polar: {
          ...(figData.layout.polar || {}),
          radialaxis: { ...(figData.layout.polar?.radialaxis || {}), visible: true, range: [0, 100] }
        }
      };

      Plotly.newPlot('spider-sentiment-clienti', figData.data, layoutOverride, { responsive: true });
      console.log('[Client Sentiment] ✓ Spider Chart renderizzato con successo!');
    } else {
      console.error('[Client Sentiment] ❌ Struttura figData non valida. Keys:', Object.keys(figData).slice(0, 10));
    }
  } catch (error) {
    console.error('[Client Sentiment] ❌ Errore:', error.message);
  }
};

// FINSIM-MOD: Carica Heatmap Propensione Rischio da API
const caricaHeatmapRischio = async () => {
  try {
    const res = await fetch(`http://10.12.7.53:8000/api/charts/risk-propensity-heatmap?scenario_id=${scenario.value}`);
    if (res.ok) {
      const data = await res.json();
      const righeLabel = ['Alto Rischio', 'Medio Rischio', 'Basso Rischio', 'Conservativo'];
      heatmapReale.value = (data.matrice || []).map((riga, i) => ({
        label: righeLabel[i],
        cells: riga.map(v => {
          let bg = '#D64242', fg = '#FFFFFF';
          if (v >= 85) { bg = '#1E9E63'; fg = '#062017'; }
          else if (v >= 70) { bg = '#7DB85A'; fg = '#10240A'; }
          else if (v >= 55) { bg = '#E0922F'; fg = '#2E1C05'; }
          else if (v >= 42) { bg = '#D9703A'; fg = '#2E1305'; }
          return { value: v + '%', bg, fg };
        })
      }));
      console.log('[Heatmap Rischio] Dati caricati da API');
    }
  } catch (err) {
    console.warn('[Heatmap Rischio] Errore fetch API, fallback a dati statici:', err.message);
  }
};

const caricaHeatmapBanca = async () => {
  try {
    const res = await fetch(`http://10.12.7.53:8000/api/charts/heatmap-data?scenario_id=${scenario.value}`);
    if (res.ok) {
      const data = await res.json();
      const righeLabel = ['Alto Rischio', 'Aggressive', 'Balanced', 'Conservative'];
      heatmapBanca.value = (data.matrice || []).map((riga, i) => ({
        label: righeLabel[i],
        cells: riga.map(v => {
          let bg = '#D64242', fg = '#FFFFFF';
          if (v >= 5) { bg = '#1E9E63'; fg = '#062017'; }
          else if ( v>= 0) { bg = '#7DB85A'; fg = '#10240A'; }
          else if (v >= -3) { bg = '#E0922F'; fg = '#2E1C05'; }
          return { value: v.toFixed(1) + '%', bg, fg };
        })
      }));
    }
  } catch (err) {
      console.warn('[Heatmap Banca] Errore:', err.message);
    }
};

const ripristinaConversazione = async (conv) => {
  if (conv.clusterSnapshot) {
    view.value = 'evoluzione';
    clusterRiskIdx.value = conv.clusterSnapshot.riskIdx;
    clusterWealthIdx.value = conv.clusterSnapshot.wealthIdx;
    clusterEvolutionData.value = conv.clusterSnapshot.evolutionData;
    clusterAnalisiLLM.value = conv.clusterSnapshot.evolutionData.analisi_llm || '';
    clusterPromotoreType.value = conv.clusterSnapshot.evolutionData.promotore_tipo || '';
    await nextTick();
    await new Promise(resolve => setTimeout(resolve, 150));
    await renderClusterEvolutionChart();
    await renderCumulativaCategoria();
  }  else {
    aiResponseBrief.value = conv.brief;
    aiResponseDetail.value = conv.detail || '';
    aiResponseCharts.value = [];
  }
};

// FINSIM-MOD: Carica evoluzione cluster per Vista Evoluzione Cliente
const caricaEvoluzioneCluster = async () => {
  isLoadingClusterEvolution.value = true;
  try {
    const res = await fetch(`http://10.12.7.53:8000/api/cluster-evolution?scenario_id=${scenario.value}&risk_idx=${clusterRiskIdx.value}&wealth_idx=${clusterWealthIdx.value}`);
    if (res.ok) {
      const data = await res.json();
      clusterEvolutionData.value = data;
      clusterTransizioni.value = data.transizioni || [];
      clusterAnalisiLLM.value = data.analisi_llm || '';
      clusterPromotoreType.value = data.promotore_tipo || '';
      isLoadingClusterEvolution.value = false;

      if (data.analisi_llm) {
        conversationHistory.value.push({
          id: Date.now(),
          question: `${data.cluster_label} — Evoluzione Strategica`,
          brief: data.analisi_llm.slice(0, 120) + (data.analisi_llm.length > 120 ? '...': ''),
          detail: data.analisi_llm,
          timestamp: new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit'}),
          clusterSnapshot: {
            riskIdx: clusterRiskIdx.value,
            wealthIdx: clusterWealthIdx.value,
            evolutionData: data,
          }
        });
      }

      await nextTick();
      await new Promise(resolve => setTimeout(resolve, 150));
      await renderClusterEvolutionChart();
      await renderCumulativaCategoria();
      return;
    }
  } catch (err) {
    console.error('[Evoluzione Cluster] Errore:', err);
  }
  isLoadingClusterEvolution.value = false;
};

// FINSIM-MOD: Dynamic Plotly chart renderer for AI-suggested charts (STEP 3)
const renderAIPlotlyCharts = async () => {
  try {
    await loadPlotly();
    await nextTick();

    // FINSIM-MOD: Aggiungi piccolo delay per assicurar che Vue abbia creato gli elementi nel DOM
    await new Promise(resolve => setTimeout(resolve, 100));

    for (let idx = 0; idx < aiResponseCharts.value.length; idx++) {
      const chart = aiResponseCharts.value[idx];
      const divId = `plotly-ai-${idx}`;

      // Attendi che l'elemento DOM sia disponibile (max 5 tentativi)
      let el = document.getElementById(divId);
      let attempts = 0;
      while (!el && attempts < 5) {
        await new Promise(resolve => setTimeout(resolve, 50));
        el = document.getElementById(divId);
        attempts++;
      }

      if (!el) {
        console.warn(`[AI Chart Render] DOM element #${divId} not found after 5 attempts for chart ${chart.codice}`);
        continue;
      }

      // Get endpoint from mapping, fallback to placeholder if not found
      const endpoint = chartCodeToEndpoint[chart.codice];
      if (!endpoint) {
        console.error(`[AI Chart Render] No endpoint mapped for chart code: ${chart.codice}. Supported codes:`, Object.keys(chartCodeToEndpoint));
        continue;
      }

      let matriceReale = [[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]];
      let waterfallData = { aum_iniziale: 100000000, nuova_raccolta: 15500000, effetto_mercato: -3200000, churn: -5800000 };

      if (chart.codice === 'HEATMAP_PERFORMANCE') {
        try {
          const r = await fetch(`http://10.12.7.53:8000/api/charts/heatmap-data?scenario_id=${scenario.value}`);
          if (r.ok) { const d = await r.json(); matriceReale = d.matrice; }
        } catch (e) {console.warn ('[AI Heatmap] Fallback', e.message); }
      }

      if (chart.codice === 'WATERFALL_PATRIMONIO') {
        try {
          const r = await fetch(`http://10.12.7.53:8000/api/charts/waterfall-data?scenario_id=${scenario.value}`);
          if(r.ok) { const d = await r.json(); waterfallData = d; }
        } catch (e) { console.warn('[AI Waterfall] Fallback:', e.message);}
      }
      // Prepare payload with all necessary metrics
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
          matrice_performance: matriceReale,
          aum_iniziale: waterfallData.aum_iniziale,
          nuova_raccolta_netta: waterfallData.nuova_raccolta,
          effetto_mercato: waterfallData.effetto_mercato,
          patrimonio_perso_churn: waterfallData.churn
        },
        user_message: ""
      };

      try {
        console.log(`[AI Chart Render] Fetching ${chart.codice} from ${endpoint}...`);
        const res = await fetch(`http://10.12.7.53:8000${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          console.error(`[AI Chart Render] API error ${res.status} for ${chart.codice}`);
          continue;
        }

        const data = await res.json();
        let figData = data.data;

        if (typeof figData === 'string') {
          figData = JSON.parse(figData);
        }

        if (figData.data && figData.layout && window.Plotly) {
          console.log(`[AI Chart Render] ✓ Rendering ${chart.codice} to #${divId}`);
          Plotly.newPlot(divId, figData.data, figData.layout, { responsive: true });
        } else {
          console.error(`[AI Chart Render] Invalid figData structure for ${chart.codice}`);
        }
      } catch (error) {
        console.error(`[AI Chart Render] Error rendering ${chart.codice}:`, error.message);
      }
    }
  } catch (error) {
    console.error('Errore nel rendering dei grafici Plotly IA:', error);
  }
};

const createAICharts = async () => {
  // Pulisci istanze precedenti
  aiChartInstances.forEach(c => {
    if (c && typeof c.destroy === 'function') {
      try { c.destroy(); } catch (e) {}
    }
  });
  aiChartInstances = [];

  await nextTick();

  // Renderizza i grafici Plotly on-demand
  await renderAIPlotlyCharts();
};

const exportToPDF = async () => {
  try {
    let waterfallReale = { aum_iniziale: 100000000, nuova_raccolta: 15500000, effetto_mercato: -3200000, churn: -5800000 };
    let matriceReale = [[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]];
    try {
      const rw = await fetch(`http://10.12.7.53:8000/api/charts/waterfall-data?scenario_id=${scenario.value}`);
      if (rw.ok) { const d = await rw.json(); waterfallReale = d; }
      const rh = await fetch(`http://10.12.7.53:8000/api/charts/heatmap-data?scenario_id=${scenario.value}`);
      if (rh.ok) { const d = await rh.json(); matriceReale = d.matrice; }
    } catch (e) { console.warn('[Export PDF] Fallback dati statici:', e.message); }

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
        matrice_performance: matriceReale,
        aum_iniziale: waterfallReale.aum_iniziale,
        nuova_raccolta_netta: waterfallReale.nuova_raccolta,
        effetto_mercato: waterfallReale.effetto_mercato,
        patrimonio_perso_churn: waterfallReale.churn,
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
    let waterfallReale = { aum_iniziale: 100000000, nuova_raccolta: 15500000, effetto_mercato: -3200000, churn: -5800000 };
    let matriceReale = [[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]];
    try {
      const rw = await fetch(`http://10.12.7.53:8000/api/charts/waterfall-data?scenario_id=${scenario.value}`);
      if (rw.ok) { const d = await rw.json(); waterfallReale = d; }
      const rh = await fetch(`http://10.12.7.53:8000/api/charts/heatmap-data?scenario_id=${scenario.value}`);
      if (rh.ok) { const d = await rh.json(); matriceReale = d.matrice; }
    } catch (e) { console.warn('[Export PPTX] Fallback dati statici:', e.message); }

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
        matrice_performance: matriceReale,
        aum_iniziale: waterfallReale.aum_iniziale,
        nuova_raccolta_netta: waterfallReale.nuova_raccolta,
        effetto_mercato: waterfallReale.effetto_mercato,
        patrimonio_perso_churn: waterfallReale.churn,
        nota: "Esportazione PPTX"
      },
      user_message: aiResponseBrief.value || ""
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

  // FINSIM-MOD: Listener per Escape key per chiudere il modal di spiegazione grafico
  const handleEscapeKey = (e) => {
    if (e.key === 'Escape' && showChartModal.value) {
      showChartModal.value = false;
    }
  };
  window.addEventListener('keydown', handleEscapeKey);

  onBeforeUnmount(() => window.removeEventListener('keydown', handleEscapeKey));

  await fetchData();

  console.log('[FINsim] ✓ Dati caricati, renderizzazione grafici...');
  await nextTick(() => renderCharts());

  if (view.value === 'banca') {
    await loadPlotly();
    await nextTick();
    await renderSpiderBanca();
    await caricaHeatmapBanca();
    await renderPlotlyChart('/api/charts/waterfall', 'plotly-waterfall', scenario.value);
    await renderPlotlyChart('/api/charts/linee-comparative', 'plotly-lines', scenario.value);
  }

  if (view.value === 'promotore') {
    await Promise.all([
      renderSopravvivenza(),
      renderPlotlyChart('/api/charts/guadagni', 'plotly-guadagni', scenario.value)
    ]).catch(err => console.error('[FINsim] Errore nel rendering dei grafici:', err));
  }

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
  datiCliente.value = {
    labels: [],
    fiducia_adapt: [],
    fiducia_fisso: [],
    profilo_dichiarato: [],
    portafoglio_assegnato: [],
    profilo_labels: [],
    risk_matrice: [],
    risk_profili: [],
    risk_patrimoni: []
  };
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

// Nuovi dati per i grafici
await nextTick(() => renderCharts());
if (view.value === 'banca') {
  await nextTick();
  await renderSpiderBanca();
    await caricaHeatmapBanca();
  await renderPlotlyChart('/api/charts/waterfall', 'plotly-waterfall', newScenario);
  await renderPlotlyChart('/api/charts/linee-comparative', 'plotly-lines', newScenario);
} else if (view.value === 'promotore') {
  await nextTick();
  await Promise.all([
    renderSopravvivenza(),
    renderPlotlyChart('/api/charts/guadagni', 'plotly-guadagni', newScenario)
  ]).catch(err => console.error('[FINsim] Errore Vista Promotore:', err));
} else if (view.value === 'cliente') {
  await nextTick();
  await new Promise(resolve => setTimeout(resolve, 200));
  await Promise.all([
    caricaVistaCliente(),
    caricaHeatmapRischio(),
    renderPlotlyChart('/api/charts/prodotti', 'plotly-bar-prodotti', newScenario)
  ]).catch(err => console.error('[FINsim] Errore Vista Cliente:', err));
}
console.log(`[FINsim] ✓ Dashboard aggiornata per scenario ${newScenario}`);
});

// Watch sui grafici consigliati dall'IA per renderizzarli dinamicamente
watch(aiResponseCharts, async () => {
  console.log('[FINsim] 📊 Grafici consigliati aggiornati, inizializzo Chart.js...');
  await createAICharts();
}, { deep: true });

// FINSIM-MOD: Watch sulla vista E scenario per renderizzare i grafici Plotly
// Intercetta sia il cambio di tab (Banca/Promotore/Cliente) sia il cambio di Scenario (Base, Stress, ecc.)
watch([view, scenario], async ([nuovaVista, nuovoScenario], [vecchiaVista, vecchioScenario]) => {
  if (nuovoScenario !== vecchioScenario) return;
  if (nuovaVista === 'banca') {
    console.log('[FINsim] 📈 Vista Banca attiva, renderizzando grafici Plotly...');
    await nextTick();
    await renderSpiderBanca();
    await caricaHeatmapBanca();
    await renderPlotlyChart('/api/charts/waterfall', 'plotly-waterfall', nuovoScenario);
    await renderPlotlyChart('/api/charts/linee-comparative', 'plotly-lines', nuovoScenario);
  } else if (nuovaVista === 'promotore') {
    console.log('[FINsim] 📊 Vista proomotore attiva, renderizzando grafici Plotly...')
    await Promise.all([
      renderSopravvivenza(),
      renderPlotlyChart('/api/charts/guadagni', 'plotly-guadagni', nuovoScenario)
    ]).catch(err => console.error('[FINsim] Errore nel rendering dei grafici:', err));
  } else if (nuovaVista === 'cliente') {
    console.log('[FINsim] 👥 Vista Cliente attiva, caricando Intelligence/Sentiment per scenario:', nuovoScenario);
    await nextTick();
    await new Promise(resolve => setTimeout(resolve, 200));
    await Promise.all([
      caricaVistaCliente(),
      caricaHeatmapRischio(),
      renderPlotlyChart('/api/charts/prodotti', 'plotly-bar-prodotti', nuovoScenario)
    ]).catch(err => console.error('[FINsim] Errore nel caricamento Vista Cliente:', err));
  } else if (nuovaVista === 'evoluzione') {
    console.log('[FINsim] 📈 Vista Evoluzione Cliente attiva, caricando dati del cluster...');
    await caricaEvoluzioneCluster();
  }
});

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
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #111c24; color: #f8fafc; font-size: 14px; }

/* Layout Globale */
.dashboard-layout { display: flex; height: 100vh; overflow: hidden; }

/* Sidebar */
.sidebar { width: 260px; background-color: #0f172a; border-right: 1px solid #1C2B3A; padding: 24px 16px; display: flex; flex-direction: column; }
.sidebar-header { margin-bottom: 40px; }
.logo { font-size: 20px; font-weight: 700; color: #FFFFFF; letter-spacing: 0.5px; }
.version { font-size: 11px; color: #1FA463; margin-top: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
.sidebar-section h4 { font-size: 11px; color: #5C6F86; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background-color: #314457; transition: background-color 0.2s; }
.status-dot.active { background-color: #1FA463; box-shadow: 0 0 8px rgba(31,164,99,0.4); }

/* Main Content */
.main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.topbar { height: 64px; border-bottom: 1px solid #1C2B3A; display: flex; align-items: center; justify-content: space-between; padding: 0 32px; background-color: #111c24; }
.breadcrumb { font-size: 14px; color: #cbd5e0; }
.user-profile { width: 32px; height: 32px; border-radius: 50%; background-color: #1FA463; border: 2px solid #111A24; }

/* Area Contenuto */
.content-area { padding: 32px; overflow-y: auto; height: calc(100vh - 64px); background-color: #111c24; }
.dashboard-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 24px; }

/* Pannelli */
.panel { background-color: #273549; border: 1px solid #3d4d63; border-radius: 12px; padding: 20px; display: flex; flex-direction: column; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.panel-header h3 { font-size: 15px; font-weight: 600; color: #FFFFFF; }
.filters span { font-size: 12px; color: #cbd5e0; background: #3d4d63; padding: 4px 10px; border-radius: 20px; }

/* Tabelle */
.table-responsive { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; text-align: left; }
.data-table th { color: #cbd5e0; font-size: 12px; text-transform: uppercase; padding-bottom: 12px; border-bottom: 1px solid #3d4d63; font-weight: 600; }
.data-table td { padding: 14px 0; border-bottom: 1px solid #3d4d63; font-size: 13px; }
.data-table tr:last-child td { border-bottom: none; }

/* Elementi UI (Progress bar, badge, etc) */
.progress-bar-bg { background-color: #3d4d63; height: 6px; border-radius: 3px; display: inline-block; width: 60px; overflow: hidden; vertical-align: middle; }
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

/* Cronologia Conversazioni nella Sidebar */
.conversation-history-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-right: 4px;
  margin-top: 8px;
}

.conversation-history-scroll::-webkit-scrollbar {
  width: 6px;
}

.conversation-history-scroll::-webkit-scrollbar-track {
  background: rgba(133, 147, 168, 0.05);
  border-radius: 3px;
}

.conversation-history-scroll::-webkit-scrollbar-thumb {
  background: rgba(133, 147, 168, 0.3);
  border-radius: 3px;
}

.conversation-history-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(133, 147, 168, 0.5);
}

.history-item {
  background: rgba(31, 164, 99, 0.06);
  border-left: 2px solid rgba(31, 164, 99, 0.3);
  border-radius: 4px;
  padding: 8px;
  font-size: 11px;
  color: #C7D5E6;
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  background: rgba(31, 164, 99, 0.12);
  border-left-color: rgba(31, 164, 99, 0.6);
  transform: translateX(2px);
}

.history-time {
  font-size: 10px;
  color: #8593A8;
  margin-bottom: 4px;
  font-weight: 600;
}

.history-question {
  font-size: 11px;
  color: #1FA463;
  font-weight: 500;
  margin-bottom: 4px;
  line-height: 1.3;
  word-break: break-word;
}

.history-brief {
  font-size: 10px;
  color: #9CA3AF;
  line-height: 1.2;
  word-break: break-word;
  opacity: 0.9;
}

/* FINSIM-MOD: Chart Explanation Modal Styles */
.chart-explain-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(2px);
  animation: fadeInModal 0.2s ease-in-out;
}

@keyframes fadeInModal {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.chart-explain-content {
  background: #111A24;
  border: 1px solid #1FA463;
  border-radius: 12px;
  padding: 28px;
  max-width: 640px;
  width: 90%;
  max-height: 70vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
}

.chart-explain-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid rgba(31, 164, 99, 0.3);
  padding-bottom: 12px;
}

.chart-explain-header h3 {
  color: #1FA463;
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.chart-explain-body p {
  color: #C7D5E6;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  margin: 0;
}

</style>