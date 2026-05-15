/**
 * Stalize API Client
 * Backend FastAPI ile iletişim katmanı
 */

const API_BASE_ENV = process.env.NEXT_PUBLIC_API_URL;
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

interface FetchOptions {
  method?: string;
  body?: unknown;
  signal?: AbortSignal;
}

function getApiBase() {
  if (API_BASE_ENV) return API_BASE_ENV;
  if (typeof window === 'undefined') return 'http://localhost:8000/api';

  const hostname = window.location.hostname || 'localhost';
  return `${window.location.protocol}//${hostname}:8000/api`;
}

async function apiFetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { method = 'GET', body, signal } = options;

  const res = await fetch(`${getApiBase()}${endpoint}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
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
  data_quality_score?: number | null;
  liquidity_score?: string | null;    // "yüksek" | "orta" | "düşük"
  amihud_ratio?: number | null;
  sector_category?: string | null;    // "banka" | "gyo" | "holding" | null
  nav_discount?: number | null;        // Holdings: NAV iskonto oranı (pozitif = iskonto)
  liquidity_level?: 'low' | 'medium' | 'high' | string | null;
  avg_traded_value?: number | null;
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
  updated_at?: string | null;
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

export interface DiagnosticItem {
  key: string;
  title: string;
  status: 'ok' | 'warning' | 'critical';
  detail: string;
  remediation: string;
  metadata: Record<string, unknown>;
}

export interface SystemDiagnosticsResponse {
  status: 'healthy' | 'degraded' | 'down';
  summary: {
    ok: number;
    warning: number;
    critical: number;
    total: number;
  };
  items: DiagnosticItem[];
  timestamp: string;
}

export interface BacktestTrade {
  symbol: string;
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  return_pct: number;
  holding_days: number;
  exit_reason: string;
}

export interface BacktestMetrics {
  trades: number;
  total_return_pct: number | null;
  benchmark_return_pct: number | null;
  excess_return_pct: number | null;
  max_drawdown_pct: number | null;
  win_rate_pct: number | null;
  avg_gain_pct: number | null;
  avg_loss_pct: number | null;
  avg_trade_pct: number | null;
  profit_factor: number | null;
  volatility_pct: number | null;
}

export interface BacktestResponse {
  strategy: {
    key: string;
    label: string;
    description: string;
  };
  period: {
    years: number;
    start: string | null;
    end: string | null;
  };
  benchmark: {
    symbol: string;
    return_pct: number | null;
    start_close?: number | null;
    end_close?: number | null;
  };
  portfolio: BacktestMetrics;
  verdict: {
    status: string;
    label: string;
    reason: string;
  };
  stocks: Array<BacktestMetrics & {
    symbol: string;
    name: string | null;
    sector: string | null;
    trades: BacktestTrade[];
  }>;
  trade_count: number;
}

export interface BacktestCompareResponse {
  years: number;
  benchmark_symbol: string;
  strategies: Array<{
    strategy: BacktestResponse['strategy'];
    period: BacktestResponse['period'];
    benchmark: BacktestResponse['benchmark'];
    portfolio: BacktestMetrics;
    verdict: BacktestResponse['verdict'];
    trade_count: number;
  }>;
}

export interface PortfolioRiskResponse {
  portfolio_value: number;
  invested_pct: number;
  cash_pct: number;
  recommended_cash_pct: number;
  cash_action: {
    status: string;
    detail: string;
    remediation: string;
  };
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | string;
  estimated_capital_at_risk: number;
  market_regime: Record<string, unknown>;
  sector_exposure: Array<{
    sector: string;
    exposure: number;
    exposure_pct: number;
    limit_pct: number;
    status: string;
  }>;
  positions: Array<{
    symbol: string;
    sector: string;
    entry_price: number;
    current_price: number;
    quantity: number;
    exposure: number;
    exposure_pct: number;
    stop_loss: number | null;
    target_price: number | null;
    stop_gap_pct: number | null;
    target_gap_pct: number | null;
    at_risk: boolean;
    score: number | null;
  }>;
  rules: Record<string, number>;
}

export interface AlertItem {
  kind: string;
  severity: 'critical' | 'warning' | 'info' | string;
  symbol: string | null;
  detail: string;
  remediation: string;
  metadata: Record<string, unknown>;
}

export interface AlertsResponse {
  status: 'ok' | 'warning' | 'critical' | string;
  summary: {
    critical: number;
    warning: number;
    info: number;
    total: number;
  };
  alerts: AlertItem[];
  generated_at: string;
}

export interface AIAuditResponse {
  symbol: string;
  decision: InvestmentDecision;
  audit: {
    auditor_action: string;
    severity: string;
    contradictions: string[];
    risk_report: string[];
    positive_evidence: string[];
    kap_news_summary: Array<Record<string, unknown>>;
    failure_scenario: string;
  };
  narrative: string;
  generated_at: string;
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
  raw_score: number | null;
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
  guardrails?: DecisionGuardrails;
  sector_category?: string | null;
  sector_scoring_method?: string | null;
  nav_discount?: number | null;
  timestamp: string;
}

export type InvestmentAction = 'strong_buy' | 'buy' | 'watch' | 'hold' | 'reduce' | 'exit';
export type InvestmentRiskLevel = 'low' | 'medium' | 'high';

export interface DecisionGuardrailCheck {
  key: string;
  label: string;
  status: 'pass' | 'warning' | 'block' | string;
  detail: string;
}

export interface DecisionGuardrails {
  data_quality: {
    score: number;
    level: 'low' | 'medium' | 'high' | string;
    label: string;
    price_history_days?: number;
    last_update_age_hours?: number | null;
    issues: string[];
    source_caveat: string;
  };
  liquidity: {
    score: number;
    level: 'low' | 'medium' | 'high' | string;
    label: string;
    avg_traded_value_20d?: number | null;
    avg_volume_20d?: number | null;
    source?: string;
    issues: string[];
  };
  limit_lock: {
    status: string;
    label: string;
    stop_reliability: string;
    up_days_5d: number;
    down_days_5d: number;
    warning: string | null;
  };
  sector_profile: {
    type: string;
    label: string;
    requires_special_model: boolean;
    required_metrics: string[];
    warning: string | null;
  };
  market_regime: {
    label: string;
    score: number;
    detail?: string;
    drawdown_pct?: number;
    five_day_return_pct?: number;
  };
  pre_trade_checklist: DecisionGuardrailCheck[];
  summary: {
    action_blocks: string[];
    warnings: string[];
    confidence_adjustment: number;
    tradable: boolean;
  };
}

export interface InvestmentDecision {
  symbol: string;
  name: string | null;
  action: InvestmentAction;
  action_label: string;
  confidence: number;
  risk_level: InvestmentRiskLevel;
  time_horizon: string;
  current_price: number;
  entry_zone: {
    low: number;
    high: number;
  };
  stop_loss: number;
  target_price: number;
  risk_reward: number;
  position_size: {
    risk_budget: number;
    shares: number;
    estimated_exposure: number;
    estimated_exposure_pct: number;
    max_exposure_pct: number;
  };
  signals: {
    overall_score: number | null;
    technical_score: number | null;
    fundamental_score: number | null;
    sentiment_score: number | null;
    recommendation: string | null;
    trend: string;
    drawdown_pct: number | null;
    annualized_volatility_pct: number | null;
    data_quality_score?: number | null;
    liquidity_score?: number | null;
    limit_lock_status?: string | null;
    market_regime_label?: string | null;
    sector_profile?: string | null;
  };
  guardrails?: DecisionGuardrails;
  thesis: string[];
  invalidation: string;
  watch_items: string[];
  policy?: {
    mode: string;
    notes: string[];
  };
  generated_at?: string;
}

export interface TopSignalsResponse {
  signals: InvestmentDecision[];
  count: number;
  generated_at: string;
}

export interface SignalOutcomeItem {
  id: number;
  symbol: string;
  sector: string | null;
  decision_date: string;
  action: InvestmentAction;
  action_label: string;
  confidence: number;
  risk_level: InvestmentRiskLevel;
  current_price: number;
  stop_loss: number | null;
  target_price: number | null;
  risk_reward: number | null;
  suggested_shares: number | null;
  estimated_exposure_pct: number | null;
  overall_score: number | null;
  trend: string | null;
  actual_return_1w_pct: number | null;
  benchmark_return_1w_pct: number | null;
  excess_return_1w_pct: number | null;
  outcome_1w: 'success' | 'partial' | 'failure' | null;
  actual_return_1m_pct: number | null;
  benchmark_return_1m_pct: number | null;
  excess_return_1m_pct: number | null;
  outcome_1m: 'success' | 'partial' | 'failure' | null;
  generated_at: string | null;
  evaluated_at: string | null;
}

export interface SignalOutcomesResponse {
  items: SignalOutcomeItem[];
  count: number;
  summary: {
    success: number;
    partial: number;
    failure: number;
    pending: number;
  };
}

export interface SignalCalibrationBucket {
  key: string;
  count: number;
  success: number;
  partial: number;
  failure: number;
  success_rate: number;
  non_failure_rate: number;
  avg_return_pct: number | null;
  avg_excess_return_pct: number | null;
}

export interface SignalCalibrationResponse {
  horizon: '1w' | '1m';
  sample_size: number;
  overall: SignalCalibrationBucket;
  by_action: SignalCalibrationBucket[];
  by_risk_level: SignalCalibrationBucket[];
  by_sector: SignalCalibrationBucket[];
  recommendations: string[];
  suggested_policy: {
    mode: string;
    measured_count: number;
    min_buy_confidence: number;
    min_buy_risk_reward: number;
    block_high_risk_buys: boolean;
    reasons: string[];
  };
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
  kap_category?: string | null;
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
  data_quality?: string;
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
  partial: boolean;
  // PORT-02: pozisyon kapatma alanları
  is_active: boolean;
  exit_price: number | null;
  exit_date: string | null;
  realized_pnl: number | null;
  // GUNLUK-01, GUNLUK-02: işlem disiplini alanları
  exit_reason: string | null;
  invalidation_condition: string | null;
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
  benchmark_entry?: number | null;
  benchmark_last?: number | null;
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
  summary?: string | null;
  ai_summary?: string | null;
  ai_assessment?: {
    stance?: 'positive' | 'negative' | 'neutral' | string;
    label?: string;
    action?: string;
    reasoning?: string;
    risk?: string;
    confidence?: number;
  } | null;
  source_url: string | null;
  publisher: string | null;
  sentiment_score: number;
  timestamp: string;
  category?: string;
  importance_score?: number | null;
  symbol?: string;
  thesis_horizon?: string;
}

export interface IntelligenceOverview {
  feed: MarketFeedItem[];
  scenarios: EventScenarioResult[];
  source_summary: Record<string, number>;
  horizon_summary?: Record<string, number>;
  ai_digest?: {
    summary: string;
    generated_by?: string;
    confidence?: number;
    generated_at?: string;
  };
  priority_mode: string;
  primary_source: string;
  warnings?: string[];
  scope?: {
    language: string;
    region: string;
    source_policy: string;
  };
  cache?: {
    status: 'hit' | 'miss' | string;
    age_seconds: number;
    ttl_seconds: number;
  };
}

export interface DailySummaryResponse {
  summary: string;
  generated_at: string;
  from_cache: boolean;
}

export interface MacroIndicators {
  usdtry: number | null;
  gold_try: number | null;
  bist100: number | null;
  interest_rate: number | null;
  inflation_rate: number | null;
  as_of: string;
  usdtry_as_of: string | null;
  gold_try_as_of: string | null;
  bist100_as_of: string | null;
  interest_rate_as_of: string | null;
  inflation_rate_as_of: string | null;
}

export interface KapNotification {
  id: number;
  symbol: string;
  title: string;
  published_at: string;
  kap_url: string | null;
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

export interface StockAnalysisResponse {
  symbol: string;
  analysis: string;
  cached: boolean;
  generated_at: string;
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

// ── BIST100 History Interface ──────────────────────────────

export interface Bist100HistoryPoint { date: string; close: number; }
export interface Bist100HistoryResponse { points: Bist100HistoryPoint[]; count: number; }

// ── Market Regime Interface (Phase 50) ─────────────────────

export interface MarketRegimeResponse {
  regime: 'Boğa' | 'Ayı' | 'Yatay' | 'Volatil' | string;
  date: string;
  adx: number | null;
  ema200: number | null;
  atr: number | null;
}

// ── Market Interfaces (Phase 29) ───────────────────────────

export interface MarketBist100Response {
  value: number | null;
  daily_change_pct: number | null;
  volume: number | null;
  as_of: string;
}

export interface ForexPair {
  symbol: string;
  name: string;
  rate: number | null;
  daily_change_pct: number | null;
  as_of: string;
}

export interface MarketForexResponse {
  pairs: ForexPair[];
  count: number;
  as_of: string;
}

export interface MarketGoldResponse {
  forms: {
    gram: number | null;
    ons: number | null;
    ceyrek: number | null;
    yarim: number | null;
    tam: number | null;
  };
  gold_usd_per_oz: number | null;
  usdtry: number | null;
  as_of: string | null;
}

// ── API Functions ──────────────────────────────────────────

export const api = {
  // Dashboard
  getDashboard: () => apiFetch<DashboardData>('/dashboard'),

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
    symbols?: string;
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
    if (params?.symbols) searchParams.set('symbols', params.symbols);
    return apiFetch<StockListResponse>(`/stocks?${searchParams.toString()}`);
  },

  getStockDetail: (symbol: string) =>
    apiFetch<StockDetail>(`/stocks/${symbol}`),

  getStockPrices: (symbol: string, period: string = '1y') =>
    apiFetch<StockPricesResponse>(`/stocks/${symbol}/prices?period=${period}`),

  // Technical Analysis
  getStockTechnical: (symbol: string) =>
    apiFetch<TechnicalResult>(`/stocks/${symbol}/technical`),

  getStockScoreBreakdown: (symbol: string) =>
    apiFetch<ScoreBreakdownResponse>(`/stocks/${symbol}/score-breakdown`),

  getStockDecision: (symbol: string, portfolioValue: number = 100000, riskPerTradePct: number = 1, calibrated = false) =>
    apiFetch<InvestmentDecision>(
      `/stocks/${symbol}/decision?portfolio_value=${portfolioValue}&risk_per_trade_pct=${riskPerTradePct}&calibrated=${calibrated ? 'true' : 'false'}`,
    ),

  getStockNews: (symbol: string, limit: number = 50) =>
    apiFetch<StockNewsResponse>(`/stocks/${symbol}/news?limit=${limit}`),

  getTopSignals: (limit: number = 20, portfolioValue: number = 100000, riskPerTradePct: number = 1, calibrated = false) =>
    apiFetch<TopSignalsResponse>(
      `/signals/top?limit=${limit}&portfolio_value=${portfolioValue}&risk_per_trade_pct=${riskPerTradePct}&calibrated=${calibrated ? 'true' : 'false'}`,
    ),

  runSignalSnapshot: (limit: number = 40, portfolioValue: number = 100000, riskPerTradePct: number = 1) =>
    apiFetch<{ decision_date: string; created_or_updated: number; benchmark_symbol: string; benchmark_close: number | null }>(
      `/signals/snapshots/run?limit=${limit}&portfolio_value=${portfolioValue}&risk_per_trade_pct=${riskPerTradePct}`,
      { method: 'POST' },
    ),

  evaluateSignalOutcomes: () =>
    apiFetch<{ evaluated_1w: number; evaluated_1m: number; as_of: string }>('/signals/outcomes/evaluate', {
      method: 'POST',
    }),

  getSignalOutcomes: (limit: number = 20, horizon: '1w' | '1m' = '1w') =>
    apiFetch<SignalOutcomesResponse>(`/signals/outcomes?limit=${limit}&horizon=${horizon}`),

  getSignalCalibration: (horizon: '1w' | '1m' = '1w', minCount: number = 1) =>
    apiFetch<SignalCalibrationResponse>(`/signals/calibration?horizon=${horizon}&min_count=${minCount}`),

  getStockFundamentals: (symbol: string) =>
    apiFetch<StockFundamentals>(`/stocks/${symbol}/fundamentals`),

  getStockPeers: (symbol: string) =>
    apiFetch<StockPeersResponse>(`/stocks/${symbol}/peers`),

  analyzeStock: (symbol: string) =>
    apiFetch<StockAnalysisResponse>(`/stocks/${symbol}/analyze`, { method: 'POST' }),

  getStockSectors: () =>
    apiFetch<StockSectorsResponse>('/stocks/sectors'),

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
    invalidation_condition?: string;
  }) =>
    apiFetch<{ id: number; symbol: string; status: string }>('/portfolio/positions', {
      method: 'POST',
      body: data,
    }),

  closePosition: (id: number, data: { exit_price: number; exit_date: string; exit_reason: string }) =>
    apiFetch<{ id: number; symbol: string; realized_pnl: number | null; status: string }>(
      `/portfolio/positions/${id}/close`,
      { method: 'PATCH', body: data },
    ),

  getCurrentModelPortfolio: () =>
    apiFetch<ModelPortfolioCurrentResponse>('/model-portfolio/current'),

  getModelPortfolioHistory: (limit: number = 12) =>
    apiFetch<ModelPortfolioHistoryResponse>(`/model-portfolio/history?limit=${limit}`),

  generateModelPortfolio: (force: boolean = false) =>
    apiFetch<ModelPortfolioCurrentResponse>(`/model-portfolio/generate?force=${force ? 'true' : 'false'}`, {
      method: 'POST',
    }),

  getHealth: () =>
    apiFetch<HealthResponse>('/health'),

  getSystemDiagnostics: () =>
    apiFetch<SystemDiagnosticsResponse>('/system/diagnostics'),

  getBacktest: (strategy: string = 'composite_signal', years: number = 1, limit: number = 100) =>
    apiFetch<BacktestResponse>(`/strategy/backtests?strategy=${strategy}&years=${years}&limit=${limit}`),

  compareBacktests: (years: number = 1, limit: number = 100) =>
    apiFetch<BacktestCompareResponse>(`/strategy/backtests/compare?years=${years}&limit=${limit}`),

  getPortfolioRiskGuard: (portfolioValue: number = 100000) =>
    apiFetch<PortfolioRiskResponse>(`/risk/portfolio?portfolio_value=${portfolioValue}`),

  getAlerts: (portfolioValue: number = 100000) =>
    apiFetch<AlertsResponse>(`/alerts?portfolio_value=${portfolioValue}`),

  auditStock: (symbol: string, portfolioValue: number = 100000, riskPerTradePct: number = 1, includeLlm = false) =>
    apiFetch<AIAuditResponse>(
      `/ai/audit/${symbol}?portfolio_value=${portfolioValue}&risk_per_trade_pct=${riskPerTradePct}&include_llm=${includeLlm ? 'true' : 'false'}`,
    ),

  getIntelligenceOverview: (limit: number = 10) =>
    apiFetch<IntelligenceOverview>(`/intelligence/overview?limit=${limit}`),

  getKapFeed: (limit: number = 10) =>
    apiFetch<KapNotification[]>(`/stocks/kap-feed?limit=${limit}`),

  getDailySummary: (): Promise<DailySummaryResponse> =>
    apiFetch<DailySummaryResponse>('/intelligence/daily-summary'),

  // ── Market Endpoints (Phase 29) ─────────────────────────
  getMarketBist100: () => apiFetch<MarketBist100Response>('/market/bist100'),

  getMarketForex: () => apiFetch<MarketForexResponse>('/market/forex'),

  getMarketGold: () => apiFetch<MarketGoldResponse>('/market/gold'),

  getMarketBist100History: (days = 30) => apiFetch<Bist100HistoryResponse>(`/market/bist100/history?days=${days}`),

  getMarketRegime: () => apiFetch<MarketRegimeResponse>('/market-regime'),
};

export default api;
