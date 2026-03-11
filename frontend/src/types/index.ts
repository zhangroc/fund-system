// 策略类型枚举
export enum StrategyType {
  DCA = 'DCA',                    // 定投策略 (Dollar Cost Averaging)
  BATCH_BUILD = 'BATCH_BUILD',    // 分批建仓策略
  VALUE = 'VALUE',                // 价值策略
  MOMENTUM = 'MOMENTUM'           // 动量策略
}

// 策略参数类型
export interface BaseStrategyParams {
  name: string;
  description?: string;
  strategyType: StrategyType;
}

export interface DCAParams extends BaseStrategyParams {
  strategyType: StrategyType.DCA;
  amount: number;              // 每次投入金额
  frequency: 'daily' | 'weekly' | 'monthly';  // 投资频率
  dayOfWeek?: number;          // 每周几 (1-5)
  dayOfMonth?: number;         // 每月几号 (1-28)
  startDate: string;           // 开始日期
  endDate?: string;            // 结束日期（可选）
  initialCapital?: number;     // 初始资金
}

export interface BatchBuildParams extends BaseStrategyParams {
  strategyType: StrategyType.BATCH_BUILD;
  totalAmount: number;         // 总投入金额
  batchCount: number;          // 分批次数
  batchInterval: number;       // 每批间隔天数
  startDate: string;
}

export interface ValueParams extends BaseStrategyParams {
  strategyType: StrategyType.VALUE;
  targetP/E?: number;          // 目标市盈率
  maxP/E?: number;             // 最高市盈率
  minP/E?: number;             // 最低市盈率
  rebalanceThreshold: number;  // 再平衡阈值 (%)
  rebalancePeriod: number;     // 再平衡周期 (天)
}

export interface MomentumParams extends BaseStrategyParams {
  strategyType: StrategyType.MOMENTUM;
  lookbackPeriod: number;      // 回看周期 (天)
  momentumThreshold: number;   // 动量阈值 (%)
  holdingPeriod: number;       // 持有周期 (天)
  topN: number;                // 持仓前N只
}

export type StrategyParams = DCAParams | BatchBuildParams | ValueParams | MomentumParams;

// 基金类型
export interface Fund {
  id: number;
  fund_code: string;
  fund_name: string;
  fund_type: string;
  manager?: string;
  scale?: number;
  status?: string;
  custodian?: string;
  fund_manager?: string;
}

// 持仓类型
export interface Holding {
  fund_code: string;
  fund_name: string;
  weight: number;              // 权重 (0-1)
  shares?: number;             // 持有份额
  cost?: number;               // 成本
}

// 组合类型
export interface Portfolio {
  id: number;
  name: string;
  description?: string;
  holdings: Holding[];
  total_assets: number;
  cash: number;
  status: 'active' | 'archived';
  created_at: string;
  updated_at?: string;
}

// 回测结果类型
export interface BacktestResult {
  id: number;
  name: string;
  strategy_id: number;
  strategy_name: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_value: number;
  total_return: number;
  total_return_pct: number;
  equity_curve: EquityPoint[];
  trades: Trade[];
  monthly_returns?: MonthlyReturn[];
}

export interface EquityPoint {
  date: string;
  value: number;
  invested: number;
  cash?: number;
}

export interface Trade {
  date: string;
  action: 'buy' | 'sell';
  fund_code: string;
  fund_name: string;
  price: number;
  shares: number;
  amount: number;
  commission?: number;
}

export interface MonthlyReturn {
  month: string;
  return: number;
  isPositive: boolean;
}

// 风险指标类型
export interface RiskMetrics {
  annualizedReturn: number;    // 年化收益率
  maxDrawdown: number;         // 最大回撤
  volatility: number;          // 年化波动率
  sharpeRatio: number;         // 夏普比率
  calmarRatio: number;         // 卡玛比率
  sortinoRatio: number;        // 索提诺比率
  alpha?: number;              // Alpha
  beta?: number;               // Beta
  riskLevel: string;           // 风险等级 A/B/C/D/E
  monthlyReturns?: MonthlyReturn[];
}

// 基金对比数据
export interface FundCompareData {
  fund_code: string;
  fund_name: string;
  nav_data: NavPoint[];
  cumulative_return?: number;
}

export interface NavPoint {
  date: string;
  nav: number;
  change_pct?: number;
}

// 持仓热力图数据
export interface HeatmapData {
  industry: string;
  holdings: HoldingData[];
}

export interface HoldingData {
  name: string;
  code: string;
  weight: number;
  change?: number;
}