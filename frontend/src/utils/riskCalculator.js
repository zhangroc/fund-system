/**
 * 风险指标计算工具
 * 用于计算收益率、最大回撤、夏普比率等风险指标
 */

/**
 * 计算累计收益率
 * @param {number[]} equityCurve - 净值曲线
 * @returns {number} 累计收益率 (%)
 */
export function calculateTotalReturn(equityCurve) {
  if (!equityCurve || equityCurve.length < 2) return 0;
  const first = equityCurve[0].value;
  const last = equityCurve[equityCurve.length - 1].value;
  if (first === 0) return 0;
  return ((last - first) / first) * 100;
}

/**
 * 计算年化收益率
 * @param {number[]} equityCurve - 净值曲线
 * @param {number} days - 投资天数
 * @returns {number} 年化收益率 (%)
 */
export function calculateAnnualizedReturn(equityCurve, days) {
  if (!equityCurve || equityCurve.length < 2 || days <= 0) return 0;
  const totalReturn = calculateTotalReturn(equityCurve);
  const years = days / 365;
  return ((Math.pow(1 + totalReturn / 100, 1 / years) - 1) * 100);
}

/**
 * 计算最大回撤 (Max Drawdown)
 * @param {number[]} equityCurve - 净值曲线
 * @returns {number} 最大回撤 (%)
 */
export function calculateMaxDrawdown(equityCurve) {
  if (!equityCurve || equityCurve.length === 0) return 0;
  
  let maxDrawdown = 0;
  let peak = equityCurve[0].value;
  
  for (const point of equityCurve) {
    if (point.value > peak) {
      peak = point.value;
    }
    const drawdown = ((peak - point.value) / peak) * 100;
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown;
    }
  }
  
  return maxDrawdown;
}

/**
 * 计算年化波动率 (Annual Volatility)
 * @param {number[]} equityCurve - 净值曲线
 * @param {number} days - 投资天数
 * @returns {number} 年化波动率 (%)
 */
export function calculateVolatility(equityCurve, days) {
  if (!equityCurve || equityCurve.length < 2 || days <= 0) return 0;
  
  // 计算日收益率
  const dailyReturns = [];
  for (let i = 1; i < equityCurve.length; i++) {
    const prev = equityCurve[i - 1].value;
    const curr = equityCurve[i].value;
    if (prev > 0) {
      dailyReturns.push((curr - prev) / prev);
    }
  }
  
  if (dailyReturns.length === 0) return 0;
  
  // 计算标准差
  const mean = dailyReturns.reduce((a, b) => a + b, 0) / dailyReturns.length;
  const squaredDiffs = dailyReturns.map(r => Math.pow(r - mean, 2));
  const variance = squaredDiffs.reduce((a, b) => a + b, 0) / dailyReturns.length;
  const stdDev = Math.sqrt(variance);
  
  // 年化波动率 (假设252个交易日)
  return stdDev * Math.sqrt(252) * 100;
}

/**
 * 计算夏普比率 (Sharpe Ratio)
 * @param {number[]} equityCurve - 净值曲线
 * @param {number} days - 投资天数
 * @param {number} riskFreeRate - 无风险利率 (默认3%)
 * @returns {number} 夏普比率
 */
export function calculateSharpeRatio(equityCurve, days, riskFreeRate = 0.03) {
  if (!equityCurve || equityCurve.length < 2 || days <= 0) return 0;
  
  const annualizedReturn = calculateAnnualizedReturn(equityCurve, days);
  const volatility = calculateVolatility(equityCurve, days);
  
  if (volatility === 0) return 0;
  
  return (annualizedReturn / 100 - riskFreeRate) / (volatility / 100);
}

/**
 * 计算卡玛比率 (Calmar Ratio)
 * @param {number[]} equityCurve - 净值曲线
 * @param {number} days - 投资天数
 * @returns {number} 卡玛比率
 */
export function calculateCalmarRatio(equityCurve, days) {
  if (!equityCurve || equityCurve.length < 2 || days <= 0) return 0;
  
  const annualizedReturn = calculateAnnualizedReturn(equityCurve, days);
  const maxDrawdown = calculateMaxDrawdown(equityCurve);
  
  if (maxDrawdown === 0) return 0;
  
  return annualizedReturn / maxDrawdown;
}

/**
 * 计算索提诺比率 (Sortino Ratio)
 * @param {number[]} equityCurve - 净值曲线
 * @param {number} days - 投资天数
 * @param {number} riskFreeRate - 无风险利率 (默认3%)
 * @returns {number} 索提诺比率
 */
export function calculateSortinoRatio(equityCurve, days, riskFreeRate = 0.03) {
  if (!equityCurve || equityCurve.length < 2 || days <= 0) return 0;
  
  const annualizedReturn = calculateAnnualizedReturn(equityCurve, days);
  
  // 计算下行偏差
  const dailyReturns = [];
  for (let i = 1; i < equityCurve.length; i++) {
    const prev = equityCurve[i - 1].value;
    const curr = equityCurve[i].value;
    if (prev > 0) {
      dailyReturns.push((curr - prev) / prev);
    }
  }
  
  if (dailyReturns.length === 0) return 0;
  
  const negativeReturns = dailyReturns.filter(r => r < 0);
  if (negativeReturns.length === 0) return Infinity;
  
  const mean = dailyReturns.reduce((a, b) => a + b, 0) / dailyReturns.length;
  const squaredDiffs = negativeReturns.map(r => Math.pow(r - mean, 2));
  const downsideVariance = squaredDiffs.reduce((a, b) => a + b, 0) / negativeReturns.length;
  const downsideDeviation = Math.sqrt(downsideVariance);
  
  if (downsideDeviation === 0) return 0;
  
  // 年化下行偏差
  const annualizedDownsideDeviation = downsideDeviation * Math.sqrt(252);
  
  return (annualizedReturn / 100 - riskFreeRate) / annualizedDownsideDeviation;
}

/**
 * 计算交易统计
 * @param {Array} trades - 交易记录
 * @returns {Object} 交易统计
 */
export function calculateTradeStats(trades) {
  if (!trades || trades.length === 0) {
    return {
      totalTrades: 0,
      buyCount: 0,
      sellCount: 0,
      avgHoldingDays: 0,
      winRate: 0
    };
  }
  
  const buys = trades.filter(t => t.action === 'buy');
  const sells = trades.filter(t => t.action === 'sell');
  
  // 计算盈利交易占比
  let winCount = 0;
  for (const sell of sells) {
    const buy = buys.find(b => 
      b.fund_code === sell.fund_code && 
      new Date(b.date) < new Date(sell.date)
    );
    if (buy && sell.price > buy.price) {
      winCount++;
    }
  }
  
  return {
    totalTrades: trades.length,
    buyCount: buys.length,
    sellCount: sells.length,
    avgHoldingDays: 0, // 需要根据具体日期计算
    winRate: sells.length > 0 ? (winCount / sells.length * 100).toFixed(1) : 0
  };
}

/**
 * 计算月度收益
 * @param {number[]} equityCurve - 净值曲线
 * @returns {Array} 月度收益数组
 */
export function calculateMonthlyReturns(equityCurve) {
  if (!equityCurve || equityCurve.length === 0) return [];
  
  // 按月份分组
  const monthlyData = {};
  for (const point of equityCurve) {
    const month = point.date.substring(0, 7); // YYYY-MM
    if (!monthlyData[month]) {
      monthlyData[month] = { start: point.value, end: point.value };
    }
    monthlyData[month].end = point.value;
  }
  
  // 计算月度收益率
  const monthlyReturns = Object.entries(monthlyData).map(([month, data]) => {
    const returnPct = ((data.end - data.start) / data.start) * 100;
    return {
      month,
      return: returnPct,
      isPositive: returnPct >= 0
    };
  });
  
  return monthlyReturns;
}

/**
 * 评估风险等级
 * @param {Object} metrics - 风险指标对象
 * @returns {string} 风险等级 (A/B/C/D/E)
 */
export function assessRiskLevel(metrics) {
  const { sharpeRatio, maxDrawdown, volatility } = metrics;
  
  // 综合评分
  let score = 0;
  
  // 夏普比率评分 (权重40%)
  if (sharpeRatio >= 2) score += 40;
  else if (sharpeRatio >= 1) score += 30;
  else if (sharpeRatio >= 0.5) score += 20;
  else if (sharpeRatio > 0) score += 10;
  
  // 最大回撤评分 (权重35%)
  if (maxDrawdown <= 5) score += 35;
  else if (maxDrawdown <= 10) score += 28;
  else if (maxDrawdown <= 20) score += 21;
  else if (maxDrawdown <= 30) score += 14;
  else if (maxDrawdown <= 50) score += 7;
  
  // 波动率评分 (权重25%)
  if (volatility <= 5) score += 25;
  else if (volatility <= 10) score += 20;
  else if (volatility <= 15) score += 15;
  else if (volatility <= 20) score += 10;
  else if (volatility <= 30) score += 5;
  
  // 评级
  if (score >= 90) return 'A';
  if (score >= 75) return 'B';
  if (score >= 60) return 'C';
  if (score >= 40) return 'D';
  return 'E';
}

/**
 * 计算所有风险指标
 * @param {Object} backtestResult - 回测结果
 * @returns {Object} 完整的风险指标
 */
export function calculateAllRiskMetrics(backtestResult) {
  const { equity_curve, trades, start_date, end_date } = backtestResult;
  
  if (!equity_curve || equity_curve.length === 0) {
    return null;
  }
  
  // 计算天数
  const days = Math.ceil(
    (new Date(end_date) - new Date(start_date)) / (1000 * 60 * 60 * 24)
  );
  
  const totalReturn = calculateTotalReturn(equity_curve);
  const annualizedReturn = calculateAnnualizedReturn(equity_curve, days);
  const maxDrawdown = calculateMaxDrawdown(equity_curve);
  const volatility = calculateVolatility(equity_curve, days);
  const sharpeRatio = calculateSharpeRatio(equity_curve, days);
  const calmarRatio = calculateCalmarRatio(equity_curve, days);
  const sortinoRatio = calculateSortinoRatio(equity_curve, days);
  const tradeStats = calculateTradeStats(trades);
  const monthlyReturns = calculateMonthlyReturns(equity_curve);
  
  const metrics = {
    totalReturn,
    annualizedReturn,
    maxDrawdown,
    volatility,
    sharpeRatio,
    calmarRatio,
    sortinoRatio,
    ...tradeStats,
    monthlyReturns
  };
  
  // 添加风险等级
  metrics.riskLevel = assessRiskLevel({
    sharpeRatio,
    maxDrawdown,
    volatility
  });
  
  return metrics;
}