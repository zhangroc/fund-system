"""
回测引擎核心逻辑
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import FundNav, Backtest, BacktestTrade
from app.models.backtest import StrategyType
import calendar


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, db: Session, backtest: Backtest):
        self.db = db
        self.backtest = backtest
        self.strategy = backtest.strategy
        
        # 持仓数据
        self.holdings: Dict[str, float] = {}  # fund_code -> shares
        self.cash = float(backtest.initial_capital)
        self.total_invested = 0
        
        # 交易记录
        self.trades: List[Dict] = []
        
        # 每日资产记录 (用于计算收益率曲线)
        self.daily_records: List[Dict] = []
        
    def run(self) -> Dict[str, Any]:
        """执行回测"""
        strategy_type = self.strategy.strategy_type
        parameters = self.strategy.parameters or {}
        
        if strategy_type == StrategyType.DOLLAR_COST_AVERAGING.value:
            return self._run_dollar_cost_averaging(parameters)
        elif strategy_type == StrategyType.LUMP_SUM.value:
            return self._run_lump_sum(parameters)
        else:
            raise ValueError(f"不支持的策略类型: {strategy_type}")
    
    def _run_dollar_cost_averaging(self, params: Dict) -> Dict[str, Any]:
        """定期定额策略"""
        amount = params.get("amount", 1000)  # 每次投入金额
        frequency = params.get("frequency", "monthly")  # 频率: daily/weekly/monthly
        day = params.get("day", 1)  # 每月几号
        
        # 获取回测时间范围内的所有交易日
        start_date = self.backtest.start_date
        end_date = self.backtest.end_date
        
        # 获取关联的基金
        fund_codes = []
        if self.strategy.fund_codes:
            fund_codes = [fc.strip() for fc in self.strategy.fund_codes.split(",")]
        
        if not fund_codes:
            raise ValueError("策略未关联基金")
        
        # 选择第一个基金进行回测
        fund_code = fund_codes[0]
        
        # 获取该基金的净值数据
        nav_records = self.db.query(FundNav).filter(
            FundNav.fund_code == fund_code,
            FundNav.nav_date >= start_date,
            FundNav.nav_date <= end_date
        ).order_by(FundNav.nav_date).all()
        
        if not nav_records:
            raise ValueError(f"基金 {fund_code} 在回测期间内没有净值数据")
        
        # 按月定投
        current_date = start_date
        month_invested = {}  # key: "2020-01", value: bool
        
        for nav_record in nav_records:
            nav_date = nav_record.nav_date
            should_invest = False
            
            if frequency == "monthly":
                # 每月day号投入
                if nav_date.day >= day:
                    month_key = nav_date.strftime("%Y-%m")
                    if month_key not in month_invested:
                        should_invest = True
                        month_invested[month_key] = True
            
            # 执行买入
            if should_invest and self.cash >= amount:
                self._buy(fund_code, nav_date, amount, nav_record.nav)
            
            # 记录当日资产
            self._record_daily(fund_code, nav_date, nav_record.nav)
        
        # 计算最终收益
        return self._calculate_result()
    
    def _run_lump_sum(self, params: Dict) -> Dict[str, Any]:
        """一次性买入策略"""
        amount = params.get("amount", self.backtest.initial_capital)
        
        start_date = self.backtest.start_date
        end_date = self.backtest.end_date
        
        # 获取关联的基金
        fund_codes = []
        if self.strategy.fund_codes:
            fund_codes = [fc.strip() for fc in self.strategy.fund_codes.split(",")]
        
        if not fund_codes:
            raise ValueError("策略未关联基金")
        
        # 选择第一个基金进行回测
        fund_code = fund_codes[0]
        
        # 获取该基金的净值数据
        nav_records = self.db.query(FundNav).filter(
            FundNav.fund_code == fund_code,
            FundNav.nav_date >= start_date,
            FundNav.nav_date <= end_date
        ).order_by(FundNav.nav_date).all()
        
        if not nav_records:
            raise ValueError(f"基金 {fund_code} 在回测期间内没有净值数据")
        
        # 第一天全部买入
        first_nav = nav_records[0]
        self._buy(fund_code, first_nav.nav_date, amount, first_nav.nav)
        
        # 记录每日资产
        for nav_record in nav_records:
            self._record_daily(fund_code, nav_record.nav_date, nav_record.nav)
        
        # 计算最终收益
        return self._calculate_result()
    
    def _buy(self, fund_code: str, date: datetime, amount: float, nav: float):
        """买入基金"""
        shares = amount / nav
        if fund_code not in self.holdings:
            self.holdings[fund_code] = 0
        self.holdings[fund_code] += shares
        self.cash -= amount
        self.total_invested += amount
        
        # 记录交易
        trade = BacktestTrade(
            backtest_id=self.backtest.id,
            trade_date=date,
            trade_type="buy",
            fund_code=fund_code,
            amount=amount,
            nav=nav,
            shares=shares
        )
        self.db.add(trade)
        self.trades.append({
            "date": date,
            "type": "buy",
            "fund_code": fund_code,
            "amount": amount,
            "nav": nav,
            "shares": shares
        })
    
    def _record_daily(self, fund_code: str, date: datetime, nav: float):
        """记录每日资产"""
        # 只计算基金持仓价值，不包含现金
        # 收益率 = (基金持仓价值 - 总投入) / 总投入
        total_value = 0
        for fc, shares in self.holdings.items():
            # 如果是当前基金的持仓，按当前nav计算
            if fc == fund_code:
                total_value += shares * nav
            else:
                # 其他基金需要查对应日期的nav，这里简化处理
                latest_nav = self.db.query(FundNav).filter(
                    FundNav.fund_code == fc,
                    FundNav.nav_date <= date
                ).order_by(FundNav.nav_date.desc()).first()
                if latest_nav:
                    total_value += shares * latest_nav.nav
        
        self.daily_records.append({
            "date": date,
            "nav": nav,
            "cash": self.cash,
            "shares": self.holdings.get(fund_code, 0),
            "total_value": total_value,
            "total_invested": self.total_invested
        })
    
    def _calculate_result(self) -> Dict[str, Any]:
        """计算回测结果"""
        if not self.daily_records:
            return {}
        
        initial_capital = self.backtest.initial_capital
        final_record = self.daily_records[-1]
        final_value = final_record["total_value"]
        
        # 总收益
        total_return = final_value - self.total_invested
        total_return_pct = (total_return / self.total_invested * 100) if self.total_invested > 0 else 0
        
        # 年化收益
        days = (self.backtest.end_date - self.backtest.start_date).days
        years = days / 365 if days > 0 else 1
        annual_return_pct = ((final_value / self.total_invested) ** (1/years) - 1) * 100 if self.total_invested > 0 and years > 0 else 0
        
        # 最大回撤
        max_value = 0
        max_drawdown = 0
        for record in self.daily_records:
            if record["total_value"] > max_value:
                max_value = record["total_value"]
            drawdown = (max_value - record["total_value"]) / max_value * 100 if max_value > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        # 收益曲线数据
        equity_curve = [
            {
                "date": r["date"].strftime("%Y-%m-%d") if isinstance(r["date"], datetime) else r["date"],
                "value": round(r["total_value"], 2),
                "invested": round(r["total_invested"], 2)
            }
            for r in self.daily_records
        ]
        
        return {
            "initial_capital": initial_capital,
            "final_value": round(final_value, 2),
            "total_invested": round(self.total_invested, 2),
            "total_return": round(total_return, 2),
            "total_return_pct": round(total_return_pct, 2),
            "annual_return_pct": round(annual_return_pct, 2),
            "max_drawdown": round(max_drawdown, 2),
            "total_trades": len(self.trades),
            "holding_days": days,
            "equity_curve": equity_curve,
            "trades": [
                {
                    "date": t["date"].strftime("%Y-%m-%d") if isinstance(t["date"], datetime) else t["date"],
                    "type": t["type"],
                    "fund_code": t["fund_code"],
                    "amount": round(t["amount"], 2),
                    "nav": round(t["nav"], 4),
                    "shares": round(t["shares"], 4)
                }
                for t in self.trades
            ]
        }


def run_backtest(db: Session, backtest_id: int) -> Dict[str, Any]:
    """执行回测的入口函数"""
    backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    if not backtest:
        raise ValueError(f"回测记录不存在: {backtest_id}")
    
    # 更新状态为运行中
    backtest.status = "running"
    backtest.started_at = datetime.now()
    db.commit()
    
    try:
        engine = BacktestEngine(db, backtest)
        result = engine.run()
        
        # 保存回测结果
        backtest.status = "completed"
        backtest.completed_at = datetime.now()
        backtest.progress = 100
        backtest.result = result
        db.commit()
        
        return result
    except Exception as e:
        backtest.status = "failed"
        backtest.error_message = str(e)
        backtest.completed_at = datetime.now()
        db.commit()
        raise