/**
 * Stalize API Client
 * Backend FastAPI ile iletişim katmanı
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface FetchOptions {
  method?: string;
  body?: unknown;
  signal?: AbortSignal;
}

async function apiFetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { method = 'GET', body, signal } = options;

  const res = await fetch(`${API_BASE}${endpoint}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
    signal,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'API Hatası' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// ── Types ──────────────────────────────────────────────────

export interface StockSummary {
  symbol: string;
  name: string;
  sector: string | null;
  industry?: string | null;
  current_price: number | null;
  daily_change_pct: number | null;
  volume: number | null;
  volume_ratio: number | null;
  market_cap: number | null;
  is_bist30: boolean;
  is_bist100?: boolean;
  is_bist250?: boolean;
  market_tier?: string | null;
  technical_score: number | null;
  fundamental_score: number | null;
  sentiment_score: number | null;
  overall_score: number | null;
  recommendation: string | null;
  stop_loss?: number | null;
  target_price?: number | null;
}

export interface DashboardData {
  top_buy: StockSummary[];
  top_sell: StockSummary[];
  top_gainers: StockSummary[];
  top_losers: StockSummary[];
  stats: {
    total_stocks: number;
    avg_score: number | null;
    strong_buy_count: number;
    buy_count: number;
    hold_count: number;
    sell_count: number;
    strong_sell_count: number;
  };
}

export interface HealthSourceStatus {
  status: 'fresh' | 'stale' | 'missing' | string;
  last_seen: string | null;
  age_minutes: number | null;
  records: number | null;
  last_successful_fetch?: string | null;
  last_attempt_at?: string | null;
  last_error?: string | null;
  last_error_at?: string | null;
  detail?: Record<string, unknown>;
  last_outcome?: 'success' | 'failure' | null;
  consecutive_failures?: number;
  success_rate?: number | null;
  recent_outcomes?: Array<'success' | 'failure'>;
  history_size?: number;
  trend?: 'improving' | 'deteriorating' | 'stable' | 'unknown' | string;
  latest_ledger_at?: string | null;
  latest_ledger_error?: string | null;
  ledger_event_count?: number;
  alert_level?: 'ok' | 'watch' | 'warning' | 'critical' | 'planned' | string;
  attention_required?: boolean;
  attention_reason?: string | null;
}

export interface HealthResponse {
  status: string;
  stocks_in_db: number;
  canonical_universe_count?: number;
  universe_sync?: boolean;
  official_source_count?: number;
  active_official_source_count?: number;
  sources: {
    kap: HealthSourceStatus;
    tcmb: HealthSourceStatus;
    tuik: HealthSourceStatus;
    portfolio_snapshot: HealthSourceStatus;
  };
  timestamp: string;
}

export interface SourceCatalogItem {
  key: string;
  name: string;
  url: string;
  category: string;
  ingest_status: 'active' | 'planned' | string;
  priority: string;
  scan_mode: string;
  status_note: string;
  api_endpoint?: string;
  runner_available: boolean;
  health_status: 'fresh' | 'failing' | 'stale' | 'missing' | 'not_run' | string;
  health: Record<string, unknown>;
  health_detail: HealthSourceStatus;
}

export interface SourceCatalogResponse {
  sources: SourceCatalogItem[];
  summary: {
    total: number;
    active: number;
    planned: number;
    scheduler_or_manual: number;
    on_demand: number;
    needs_attention: number;
    health: {
      fresh: number;
      failing: number;
      stale: number;
      missing: number;
      not_run: number;
    };
  };
  timestamp: string;
}

export interface SourceHealthHistoryItem {
  id: number;
  source_key: string;
  status: 'success' | 'failure' | string;
  error: string | null;
  detail: Record<string, unknown>;
  recorded_at: string | null;
}

export interface SourceHealthHistoryResponse {
  items: SourceHealthHistoryItem[];
  source_key: string | null;
  limit: number;
  count: number;
  timestamp: string;
}

export interface SourceHealthAlertItem {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'planned' | string;
  title: string;
  detail: string;
  note: string;
  score: number;
}

export interface SourceHealthRollupItem {
  source: SourceCatalogItem;
  history: SourceHealthHistoryItem[];
  failure_count: number;
  success_count: number;
  latest_event: SourceHealthHistoryItem | null;
  risk_score: number;
  success_ratio: number | null;
  freshness_rank: number;
  incident_state: 'open' | 'recovering' | 'watch' | 'stable' | 'planned' | string;
}

export interface SourceHealthDashboardResponse {
  source_catalog: SourceCatalogResponse;
  ledger: {
    total_events: number;
    success_count: number;
    failure_count: number;
    failure_rate: number | null;
    recent_events: SourceHealthHistoryItem[];
  };
  counts: {
    at_risk_sources: number;
    planned_sources: number;
  };
  metrics: {
    open_incidents: number;
    watchlist_sources: number;
    recovering_sources: number;
    max_failure_streak: number;
    average_success_rate: number | null;
  };
  alerts: SourceHealthAlertItem[];
  unstable_sources: SourceHealthRollupItem[];
  recovery_candidates: SourceHealthRollupItem[];
  healthy_sources: SourceHealthRollupItem[];
  timestamp: string;
}

export interface StockListResponse {
  stocks: StockSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface PricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  sma_20?: number | null;
  sma_50?: number | null;
  sma_200?: number | null;
  ema_12?: number | null;
  ema_26?: number | null;
  rsi_14?: number | null;
  macd?: number | null;
  macd_signal?: number | null;
  macd_histogram?: number | null;
  bb_upper?: number | null;
  bb_middle?: number | null;
  bb_lower?: number | null;
  atr_14?: number | null;
  obv?: number | null;
}

export interface StockDetail {
  stock: StockSummary & {
    currency: string;
    last_data_update: string | null;
  };
  recent_prices: PricePoint[];
}

export interface StockPricesResponse {
  symbol: string;
  name: string;
  period: string;
  prices: PricePoint[];
}

export interface TechnicalResult {
  symbol: string;
  score: number;
  recommendation: string;
  signals: Array<{
    type: string;
    name: string;
    direction: string;
    strength: number;
  }>;
  support: number | null;
  resistance: number | null;
  stop_loss: number | null;
  target_price: number | null;
  indicators: Record<string, number | null>;
  ema_50?: Array<{ date: string; value: number }>;
  ema_200?: Array<{ date: string; value: number }>;
}

export interface ScoreBreakdownComponent {
  key: string;
  label: string;
  raw_score: number;
  base_weight: number;
  normalized_weight: number;
  contribution: number;
  reason: string;
}

export interface ScoreBreakdownMissingComponent {
  key: string;
  label: string;
  reason: string;
}

export interface ScoreBreakdownResponse {
  symbol: string;
  name: string;
  breakdown: {
    overall_score: number;
    recommendation: string;
    components: ScoreBreakdownComponent[];
    missing_components: ScoreBreakdownMissingComponent[];
    summary: {
      available_component_count: number;
      missing_component_count: number;
      normalization_applied: boolean;
      weight_coverage: number;
    };
  };
  timestamp: string;
}

export interface StockNewsItem {
  id: number;
  title: string;
  summary: string | null;
  source: string | null;
  category: string | null;
  url: string | null;
  published_at: string | null;
  sentiment_score: number | null;
  sentiment_label: string | null;
  importance_score: number | null;
}

/** Alias for KAP/news items used by KAPNewsCard */
export type KapNewsItem = StockNewsItem;

export interface StockNewsResponse {
  symbol: string;
  name: string;
  items: StockNewsItem[];
  count: number;
  timestamp: string;
}

export interface StockFundamentals {
  symbol: string;
  period: string | null;
  pe_ratio: number | null;
  pb_ratio: number | null;
  roe: number | null;
  net_margin: number | null;
  debt_to_equity: number | null;
  fundamental_score: number | null;
  ev_ebitda?: number | null;
}

export interface EventImpact {
  symbol: string;
  name: string;
  sector: string | null;
  current_price: number | null;
  direction: string;
  impact_score: number;
  impact_pct: number;
  reasons: string[];
  confidence: number;
}

export interface EventScenarioResult {
  scenario: {
    trigger: string;
    trigger_id: string;
    direction: string;
    magnitude: string;
    category: string;
    source_news_headline?: string;
    source_url?: string | null;
    publisher?: string | null;
    computed_at?: string;
  };
  impacts: EventImpact[];
  summary: {
    headline: string;
    total_stocks_affected: number;
    positive_stocks: number;
    negative_stocks: number;
    top_winners: Array<{ symbol: string; score: number }>;
    top_losers: Array<{ symbol: string; score: number }>;
  };
}

export interface SectorSummary {
  sector: string;
  stock_count: number;
  avg_score: number | null;
  avg_daily_change: number | null;
}

export interface StockSectorsResponse {
  sectors: string[];
}

export interface PortfolioPosition {
  id: number;
  symbol: string;
  entry_price: number;
  quantity: number;
  entry_date: string;
  stop_loss: number | null;
  target_price: number | null;
  rationale: string | null;
  current_price: number | null;
  pnl_pct: number | null;
}

export interface PortfolioSnapshot {
  date: string;             // "YYYY-MM-DD"
  total_value: number | null;
  daily_pnl_pct: number | null;
  positions_json: unknown | null;
}

export interface PortfolioComparisonPoint {
  date: string;
  value?: number | null;
  close?: number | null;
  return_pct: number | null;
  daily_pnl_pct?: number | null;
}

export interface PortfolioHistoryResponse {
  snapshots: PortfolioSnapshot[];
  comparison: {
    portfolio_series: PortfolioComparisonPoint[];
    benchmark_series: PortfolioComparisonPoint[];
    benchmark_symbol: string;
    benchmark_label: string;
    active_return_spread: number | null;
  };
  risk_summary: {
    active_positions: number;
    positions_at_risk: number;
    positions_near_target: number;
    latest_portfolio_return_pct: number | null;
    latest_benchmark_return_pct: number | null;
  };
  timestamp: string;
}

export interface ModelPortfolioHolding {
  id: number;
  symbol: string;
  name: string | null;
  sector: string | null;
  allocation_pct: number;
  entry_price: number | null;
  current_price: number | null;
  weekly_return_pct: number | null;
  daily_change_pct: number | null;
  technical_score: number | null;
  fundamental_score: number | null;
  sentiment_score: number | null;
  overall_score: number | null;
  recommendation: string | null;
  rank: number;
  rationale: string | null;
}

export interface ModelPortfolioReviewPerformer {
  symbol: string;
  sector: string | null;
  return_pct: number;
  overall_score: number | null;
  technical_score: number | null;
  fundamental_score: number | null;
  sentiment_score: number | null;
  failure_tags: string[];
  primary_reason: string;
}

export interface ModelPortfolioFactorDragItem {
  factor: string;
  label: string;
  weighted_drag: number;
}

export interface ModelPortfolioSectorDragItem {
  sector: string;
  weighted_drag: number;
}

export interface ModelPortfolioAdjustmentPlan {
  penalized_symbols: string[];
  sector_caps: Record<string, number>;
  factor_penalties: Record<string, number>;
  review_mode: string;
}

export interface ModelPortfolioReviewNotes {
  poor_performers: ModelPortfolioReviewPerformer[];
  sector_drag: ModelPortfolioSectorDragItem[];
  weakest_dimension: string;
  factor_drag: ModelPortfolioFactorDragItem[];
  next_week_adjustments: ModelPortfolioAdjustmentPlan;
}

export interface ModelPortfolioGenerationNotes {
  selected_count?: number;
  selection_rule?: string;
  penalized_symbols: string[];
  sector_caps?: Record<string, number>;
  factor_penalties?: Record<string, number>;
  previous_adjustment_mode?: string | null;
  previous_review_summary?: string | null;
  holdings?: Array<{
    symbol: string;
    allocation_pct: number;
    sector: string | null;
    overall_score: number | null;
    recommendation: string | null;
  }>;
}

export interface ModelPortfolioChangeItem {
  symbol: string;
  previous_allocation_pct: number;
  current_allocation_pct: number;
  delta_pct: number;
}

export interface ModelPortfolioChanges {
  added: string[];
  removed: string[];
  increased: ModelPortfolioChangeItem[];
  decreased: ModelPortfolioChangeItem[];
  unchanged: string[];
  summary: string;
}

export interface ModelPortfolioDecisionBand {
  headline: string;
  focus: string;
  actions: string[];
}

export interface ModelPortfolioWeekSummary {
  id: number;
  week_start: string;
  week_end: string;
  status: string;
  strategy_version?: string;
  portfolio_return_pct: number | null;
  daily_return_pct?: number | null;
  benchmark_symbol?: string;
  benchmark_return_pct: number | null;
  active_return_spread: number | null;
  review_summary?: string | null;
  review_notes?: ModelPortfolioReviewNotes | null;
  generation_notes?: ModelPortfolioGenerationNotes | null;
  change_summary?: string | null;
  reviewed_at?: string | null;
}

export interface ModelPortfolioSnapshot {
  date: string;
  total_return_pct: number | null;
  daily_return_pct: number | null;
  benchmark_return_pct: number | null;
  active_return_spread: number | null;
  positions_json: unknown | null;
}

export interface ModelPortfolioCurrentResponse {
  week: ModelPortfolioWeekSummary | null;
  holdings: ModelPortfolioHolding[];
  snapshots: ModelPortfolioSnapshot[];
  summary: {
    holding_count: number;
    best_holding: { symbol: string; weekly_return_pct: number; allocation_pct: number } | null;
    worst_holding: { symbol: string; weekly_return_pct: number; allocation_pct: number } | null;
  } | null;
  changes?: ModelPortfolioChanges | null;
  decision_band?: ModelPortfolioDecisionBand | null;
  timestamp: string;
  generated?: boolean;
  generated_at?: string;
  generation_notes?: ModelPortfolioGenerationNotes;
}

export interface ModelPortfolioHistoryResponse {
  weeks: ModelPortfolioWeekSummary[];
  count: number;
  timestamp: string;
}

export interface MarketFeedItem {
  trigger_id: string;
  direction: string;
  magnitude: string;
  headline: string;
  original_headline?: string;
  source_url: string | null;
  publisher: string | null;
  sentiment_score: number;
  timestamp: string;
  category?: string;
  importance_score?: number | null;
  symbol?: string;
}

export interface IntelligenceOverview {
  feed: MarketFeedItem[];
  scenarios: EventScenarioResult[];
  source_summary: Record<string, number>;
  priority_mode: string;
  primary_source: string;
}

export interface MacroIndicators {
  usdtry: number | null;
  gold_try: number | null;
  bist100: number | null;
  interest_rate: number | null;
  inflation_rate: number | null;
  as_of: string;
}

export interface KapNotification {
  id: number;
  symbol: string;
  title: string;
  published_at: string;
  kap_url: string | null;
}

export interface SparklinePoint {
  date: string;
  close: number;
}

export interface SparklineResponse {
  symbol: string;
  points: SparklinePoint[];
}

export interface MacroEventItem {
  source?: string;
  category?: string;
  title?: string;
  symbol?: string;
  sentiment_score?: number;
  sentiment_label?: string;
}

export interface MacroEventsResponse {
  events: MacroEventItem[];
}

export interface StockPeer {
  symbol: string;
  name: string;
  current_price: number | null;
  daily_change_pct: number | null;
  market_cap: number | null;
  overall_score: number | null;
  recommendation: string | null;
  is_bist30: boolean;
  is_bist100: boolean;
}

export interface StockPeersResponse {
  symbol: string;
  sector: string;
  peers: StockPeer[];
}

export interface ImpactRankingItem {
  title?: string;
  sources?: string[];
  affected_symbols?: string[];
  impact_score?: number;
}

export interface ImpactRankingResponse {
  ranked_events: ImpactRankingItem[];
}

export interface CorrelationStatistics {
  mean_correlation?: number;
  max_correlation?: number;
  min_correlation?: number;
  mean_volatility_pct?: number;
  max_volatility_pct?: number;
  num_stocks?: number;
  num_observations?: number;
}

export interface CorrelationMatrixResponse {
  statistics?: CorrelationStatistics;
  crisis_mode?: boolean;
}

export interface CrisisModeResponse {
  crisis_mode?: boolean;
  alert_level?: string;
  statistics?: CorrelationStatistics;
}

export interface DiversificationAdviceResponse {
  mode?: string;
  actions?: string[];
}

export interface LowCorrelationPairsResponse {
  pairs: Array<{
    symbol1: string;
    symbol2: string;
    correlation: number;
    quality: string;
  }>;
  total_found: number;
  threshold: number;
  timestamp: string;
}

// ── API Functions ──────────────────────────────────────────

export const api = {
  // Dashboard
  getDashboard: () => apiFetch<DashboardData>('/dashboard'),
  getSourceCatalog: () => apiFetch<SourceCatalogResponse>('/sources/catalog'),

  // Stocks
  getStocks: (params?: {
    sort_by?: string;
    limit?: number;
    offset?: number;
    sector?: string;
    bist30?: boolean;
    bist100?: boolean;
    bist250?: boolean;
    search?: string;
    recommendation?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.sort_by) searchParams.set('sort_by', params.sort_by);
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    if (params?.sector) searchParams.set('sector', params.sector);
    if (params?.bist30) searchParams.set('bist30', 'true');
    if (params?.bist100) searchParams.set('bist100', 'true');
    if (params?.bist250) searchParams.set('bist250', 'true');
    if (params?.search) searchParams.set('search', params.search);
    if (params?.recommendation) searchParams.set('recommendation', params.recommendation);
    return apiFetch<StockListResponse>(`/stocks?${searchParams.toString()}`);
  },

  getStockDetail: (symbol: string) =>
    apiFetch<StockDetail>(`/stocks/${symbol}`),

  getStockPrices: (symbol: string, period: string = '1y') =>
    apiFetch<StockPricesResponse>(`/stocks/${symbol}/prices?period=${period}`),

  // Technical Analysis
  getStockTechnical: (symbol: string) =>
    apiFetch<TechnicalResult>(`/stocks/${symbol}/technical`),

  runTechnicalAnalysis: () =>
    apiFetch<{ status: string; analyzed: number }>('/analysis/technical/run', { method: 'POST' }),

  // Scoring
  updateScores: () =>
    apiFetch<{ status: string; updated: number }>('/scoring/update', { method: 'POST' }),

  getStockScoreBreakdown: (symbol: string) =>
    apiFetch<ScoreBreakdownResponse>(`/stocks/${symbol}/score-breakdown`),

  getStockNews: (symbol: string, limit: number = 10) =>
    apiFetch<StockNewsResponse>(`/stocks/${symbol}/news?limit=${limit}`),

  getStockFundamentals: (symbol: string) =>
    apiFetch<StockFundamentals>(`/stocks/${symbol}/fundamentals`),

  getStockPeers: (symbol: string) =>
    apiFetch<StockPeersResponse>(`/stocks/${symbol}/peers`),

  getRankings: (params?: { sort_by?: string; limit?: number; sector?: string; bist30?: boolean }) => {
    const searchParams = new URLSearchParams();
    if (params?.sort_by) searchParams.set('sort_by', params.sort_by);
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.sector) searchParams.set('sector', params.sector);
    if (params?.bist30) searchParams.set('bist30', 'true');
    return apiFetch<{ rankings: StockSummary[]; sort_by: string; count: number }>(`/rankings?${searchParams.toString()}`);
  },

  // Sectors
  getSectors: () =>
    apiFetch<{ sectors: SectorSummary[] }>('/sectors'),

  getStockSectors: () =>
    apiFetch<StockSectorsResponse>('/stocks/sectors'),

  // Health
  health: () =>
    apiFetch<HealthResponse>('/health'),
  getSourceHealthHistory: (params?: { source_key?: string; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.source_key) searchParams.set('source_key', params.source_key);
    if (params?.limit) searchParams.set('limit', String(params.limit));
    return apiFetch<SourceHealthHistoryResponse>(`/sources/health/history?${searchParams.toString()}`);
  },
  getSourceHealthDashboard: (params?: { limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', String(params.limit));
    return apiFetch<SourceHealthDashboardResponse>(`/sources/health/dashboard?${searchParams.toString()}`);
  },

  // Portfolio
  getPortfolioPositions: () =>
    apiFetch<PortfolioPosition[]>('/portfolio/positions'),

  getPortfolioHistory: (days: number = 90) =>
    apiFetch<PortfolioHistoryResponse>(`/portfolio/history?days=${days}`),

  addPosition: (data: {
    symbol: string;
    entry_price: number;
    quantity: number;
    entry_date: string;
    stop_loss?: number;
    target_price?: number;
    rationale?: string;
  }) =>
    apiFetch<{ id: number; symbol: string; status: string }>('/portfolio/positions', {
      method: 'POST',
      body: data,
    }),

  closePosition: (positionId: number) =>
    apiFetch<{ status: string; symbol: string }>(`/portfolio/positions/${positionId}`, {
      method: 'DELETE',
    }),

  getCurrentModelPortfolio: () =>
    apiFetch<ModelPortfolioCurrentResponse>('/model-portfolio/current'),

  getModelPortfolioHistory: (limit: number = 12) =>
    apiFetch<ModelPortfolioHistoryResponse>(`/model-portfolio/history?limit=${limit}`),

  generateModelPortfolio: (force: boolean = false) =>
    apiFetch<ModelPortfolioCurrentResponse>(`/model-portfolio/generate?force=${force ? 'true' : 'false'}`, {
      method: 'POST',
    }),

  getIntelligenceOverview: (limit: number = 10) =>
    apiFetch<IntelligenceOverview>(`/intelligence/overview?limit=${limit}`),

  // ─── FAZ 9: TCMB, TUIK, EVENT FUSION, KORELASYON ───

  // Makro Olaylar
  getMacroEvents: (params?: { limit?: number; days?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.days) searchParams.set('days', String(params.days));
    return apiFetch<MacroEventsResponse>(`/macro/events?${searchParams.toString()}`);
  },

  triggerTCMBScan: () =>
    apiFetch<{ status: string; stored: number; source: string; timestamp: string }>('/macro/tcmb/scan', {
      method: 'POST',
    }),

  triggerTUIKScan: () =>
    apiFetch<{ status: string; stored: number; source: string; timestamp: string }>('/macro/tuik/scan', {
      method: 'POST',
    }),

  // Dinamik Korelasyon
  getCorrelationMatrix: (window_days: number = 30) =>
    apiFetch<CorrelationMatrixResponse>(`/correlation/matrix?window_days=${window_days}`),

  getCrisisMode: () =>
    apiFetch<CrisisModeResponse>('/correlation/crisis'),

  getDiversificationAdvice: () =>
    apiFetch<DiversificationAdviceResponse>('/correlation/diversification-advice'),

  getLowCorrelationPairs: (params?: { threshold?: number; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.threshold) searchParams.set('threshold', String(params.threshold));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    return apiFetch<LowCorrelationPairsResponse>(`/correlation/low-correlation-pairs?${searchParams.toString()}`);
  },

  getMacroIndicators: () => apiFetch<MacroIndicators>('/macro/indicators'),

  getKapFeed: (limit: number = 10) =>
    apiFetch<KapNotification[]>(`/stocks/kap-feed?limit=${limit}`),

  getSparklineData: (symbol: string, days: number = 30) =>
    apiFetch<SparklineResponse>(`/stocks/sparkline?symbol=${encodeURIComponent(symbol)}&days=${days}`),
};

export default api;
