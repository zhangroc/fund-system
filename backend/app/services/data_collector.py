"""数据采集服务 - AkShare 集成"""
import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import pandas as pd
import akshare as ak

from app.models.fund import Fund, FundNav, FundHolding, FundType

logger = logging.getLogger(__name__)


class DataCollector:
    """数据采集器 - 使用 AkShare 获取基金数据"""
    
    def __init__(self, db: Session):
        self.db = db
        self.request_delay = 1.0  # 请求间隔(秒)，避免被封
    
    # ============ 基金基本信息采集 ============
    
    def collect_fund_list(self, min_scale: float = 1.0) -> Dict[str, Any]:
        """
        采集开放式基金列表
        
        Args:
            min_scale: 最小规模(亿元)，默认1亿
            
        Returns:
            dict: 采集结果统计
        """
        result = {
            "total": 0,
            "success": 0,
            "skipped": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            logger.info("开始采集基金列表...")
            
            # 获取基金列表
            fund_df = ak.fund_info_a_code_name()
            
            if fund_df is None or fund_df.empty:
                logger.warning("未获取到基金数据")
                return result
            
            result["total"] = len(fund_df)
            logger.info(f"获取到 {len(fund_df)} 个基金")
            
            for idx, row in fund_df.iterrows():
                try:
                    fund_code = str(row.get('code', '')).zfill(6)
                    fund_name = row.get('name', '')
                    
                    if not fund_code or not fund_name:
                        result["skipped"] += 1
                        continue
                    
                    # 检查是否已存在
                    existing = self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
                    if existing:
                        result["skipped"] += 1
                        continue
                    
                    # 获取基金详细信息
                    fund_type = self._get_fund_type(fund_code)
                    
                    # 创建基金记录
                    fund = Fund(
                        fund_code=fund_code,
                        fund_name=fund_name,
                        fund_type=fund_type,
                        status="在售"
                    )
                    self.db.add(fund)
                    result["success"] += 1
                    
                    # 每100条提交一次
                    if result["success"] % 100 == 0:
                        self.db.commit()
                        logger.info(f"已处理 {result['success']} 个基金")
                    
                    time.sleep(self.request_delay)
                    
                except Exception as e:
                    result["failed"] += 1
                    result["errors"].append(str(e))
                    logger.warning(f"处理基金失败: {e}")
                    continue
            
            self.db.commit()
            logger.info(f"基金列表采集完成: 成功 {result['success']}, 跳过 {result['skipped']}, 失败 {result['failed']}")
            
        except Exception as e:
            logger.error(f"采集基金列表失败: {e}")
            self.db.rollback()
            result["errors"].append(str(e))
        
        return result
    
    def _get_fund_type(self, fund_code: str) -> FundType:
        """获取基金类型"""
        try:
            detail_df = ak.fund_info_a_em(fund=fund_code)
            if detail_df is not None and not detail_df.empty:
                type_str = detail_df.iloc[0].get('type', '')
                for ft in FundType:
                    if ft.value in str(type_str):
                        return ft
        except Exception:
            pass
        return FundType.OTHER
    
    # ============ 基金净值采集 ============
    
    def collect_fund_nav(self, fund_codes: Optional[List[str]] = None, days: int = 30) -> Dict[str, Any]:
        """
        采集基金净值数据
        
        Args:
            fund_codes: 基金代码列表，None 表示采集所有基金
            days: 采集天数
            
        Returns:
            dict: 采集结果统计
        """
        result = {
            "funds_processed": 0,
            "nav_records": 0,
            "failed": 0,
            "errors": []
        }
        
        # 获取需要采集的基金列表
        if fund_codes:
            funds = self.db.query(Fund).filter(Fund.fund_code.in_(fund_codes)).all()
        else:
            funds = self.db.query(Fund).all()
        
        logger.info(f"开始采集净值数据，共 {len(funds)} 个基金")
        
        for fund in funds:
            try:
                nav_count = self._sync_single_fund_nav(fund.fund_code, days)
                result["nav_records"] += nav_count
                result["funds_processed"] += 1
                
                time.sleep(self.request_delay)
                
            except Exception as e:
                result["failed"] += 1
                result["errors"].append(f"{fund.fund_code}: {str(e)}")
                logger.warning(f"采集基金 {fund.fund_code} 净值失败: {e}")
                continue
        
        self.db.commit()
        logger.info(f"净值采集完成: 处理 {result['funds_processed']} 个基金，新增 {result['nav_records']} 条记录")
        
        return result
    
    def _sync_single_fund_nav(self, fund_code: str, days: int = 30) -> int:
        """同步单个基金的净值数据"""
        count = 0
        
        try:
            nav_df = ak.fund_nav_em(fund=fund_code)
            
            if nav_df is None or nav_df.empty:
                return 0
            
            # 获取最近的数据
            recent_nav = nav_df.head(days)
            
            for _, row in recent_nav.iterrows():
                try:
                    nav_date = row.get('净值日期')
                    if isinstance(nav_date, str):
                        nav_date = pd.to_datetime(nav_date)
                    
                    # 检查是否已存在
                    existing = self.db.query(FundNav).filter(
                        FundNav.fund_code == fund_code,
                        FundNav.nav_date == nav_date
                    ).first()
                    
                    if existing:
                        continue
                    
                    nav = row.get('单位净值')
                    accumulated_nav = row.get('累计净值')
                    daily_growth = row.get('日增长率')
                    
                    if nav:
                        nav_record = FundNav(
                            fund_code=fund_code,
                            nav_date=nav_date,
                            nav=float(nav),
                            accumulated_nav=float(accumulated_nav) if pd.notna(accumulated_nav) else None,
                            daily_growth=float(str(daily_growth).replace('%', '')) if pd.notna(daily_growth) else None
                        )
                        self.db.add(nav_record)
                        count += 1
                        
                except Exception as e:
                    logger.warning(f"处理净值记录失败: {e}")
                    continue
            
            self.db.commit()
            
        except Exception as e:
            logger.warning(f"获取基金 {fund_code} 净值失败: {e}")
        
        return count
    
    # ============ 基金详细信息更新 ============
    
    def update_fund_details(self, fund_codes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        更新基金详细信息（规模、基金公司、基金经理等）
        
        Args:
            fund_codes: 基金代码列表，None 表示更新所有基金
        """
        result = {
            "updated": 0,
            "failed": 0,
            "errors": []
        }
        
        if fund_codes:
            funds = self.db.query(Fund).filter(Fund.fund_code.in_(fund_codes)).all()
        else:
            funds = self.db.query(Fund).all()
        
        logger.info(f"开始更新基金详细信息，共 {len(funds)} 个基金")
        
        for fund in funds:
            try:
                self._update_single_fund_detail(fund)
                result["updated"] += 1
                
                time.sleep(self.request_delay)
                
            except Exception as e:
                result["failed"] += 1
                result["errors"].append(f"{fund.fund_code}: {str(e)}")
                logger.warning(f"更新基金 {fund.fund_code} 详情失败: {e}")
                continue
        
        self.db.commit()
        logger.info(f"基金详情更新完成: 成功 {result['updated']}, 失败 {result['failed']}")
        
        return result
    
    def _update_single_fund_detail(self, fund: Fund) -> None:
        """更新单个基金的详细信息"""
        try:
            detail_df = ak.fund_info_a_em(fund=fund.fund_code)
            
            if detail_df is None or detail_df.empty:
                return
            
            row = detail_df.iloc[0]
            
            # 更新字段
            if pd.notna(row.get('type')):
                for ft in FundType:
                    if ft.value in str(row.get('type')):
                        fund.fund_type = ft
                        break
            
            if pd.notna(row.get('found_date')):
                date_str = str(row.get('found_date'))
                try:
                    fund.establishment_date = datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    pass
            
            if pd.notna(row.get('manager')):
                fund.manager = str(row.get('manager'))
            
            if pd.notna(row.get('fund_manager')):
                fund.fund_manager = str(row.get('fund_manager'))
            
            if pd.notna(row.get('custodian')):
                fund.custodian = str(row.get('custodian'))
            
            # 费率
            if pd.notna(row.get('management_fee')):
                fund.management_fee = float(row.get('management_fee'))
            if pd.notna(row.get('custodian_fee')):
                fund.custodian_fee = float(row.get('custodian_fee'))
            if pd.notna(row.get('sales_service_fee')):
                fund.sales_service_fee = float(row.get('sales_service_fee'))
            
            # 规模
            if pd.notna(row.get('scale')):
                fund.scale = float(row.get('scale'))
            
            # 风险等级
            if pd.notna(row.get('risk_level')):
                fund.risk_level = str(row.get('risk_level'))
            
            fund.updated_at = datetime.now()
            
        except Exception as e:
            logger.warning(f"更新基金详情失败: {e}")
    
    # ============ 基金持仓采集 ============
    
    def collect_fund_holdings(self, fund_code: str, year: Optional[int] = None) -> Dict[str, Any]:
        """
        采集基金持仓数据
        
        Args:
            fund_code: 基金代码
            year: 年份，默认获取最新年份
        """
        result = {
            "fund_code": fund_code,
            "records": 0,
            "success": False,
            "error": None
        }
        
        try:
            # 获取最新年份的持仓
            if year is None:
                year = datetime.now().year
            
            holdings_df = ak.fund_portfolio_hold_em(symbol=fund_code, date=str(year))
            
            if holdings_df is None or holdings_df.empty:
                result["error"] = "无持仓数据"
                return result
            
            for _, row in holdings_df.iterrows():
                try:
                    holding = FundHolding(
                        fund_code=fund_code,
                        holding_date=datetime.now(),
                        stock_code=str(row.get('股票代码', '')),
                        stock_name=str(row.get('股票名称', '')),
                        holding_ratio=float(str(row.get('占净值比例', '0')).replace('%', '')) if pd.notna(row.get('占净值比例')) else None,
                        holding_market_value=float(row.get('持仓市值(万元)', 0)) if pd.notna(row.get('持仓市值(万元)')) else None,
                        shares=float(row.get('持股数', 0)) if pd.notna(row.get('持股数')) else None
                    )
                    self.db.add(holding)
                    result["records"] += 1
                    
                except Exception as e:
                    logger.warning(f"处理持仓记录失败: {e}")
                    continue
            
            self.db.commit()
            result["success"] = True
            logger.info(f"基金 {fund_code} 持仓采集完成: {result['records']} 条记录")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"采集基金 {fund_code} 持仓失败: {e}")
        
        return result
    
    # ============ ETF 数据采集 ============
    
    def collect_etf_hist(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        采集 ETF 历史数据
        
        Args:
            symbol: ETF 代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            DataFrame: ETF 历史数据
        """
        try:
            df = ak.fund_etf_hist_em(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )
            return df
        except Exception as e:
            logger.error(f"获取ETF {symbol} 历史数据失败: {e}")
            return pd.DataFrame()
    
    # ============ 基金排名采集 ============
    
    def collect_fund_rank(self, fund_type: str = "全部", top_n: int = 100) -> pd.DataFrame:
        """
        采集基金业绩排名
        
        Args:
            fund_type: 基金类型 (全部/股票型/混合型/债券型/指数型等)
            top_n: 返回前 N 名
            
        Returns:
            DataFrame: 基金排名数据
        """
        try:
            df = ak.fund_open_fund_rank_em(symbol=fund_type)
            if df is not None and not df.empty:
                return df.head(top_n)
            return df
        except Exception as e:
            logger.error(f"获取基金排名失败: {e}")
            return pd.DataFrame()
    
    # ============ 批量净值更新（增量） ============
    
    def update_latest_nav(self) -> Dict[str, Any]:
        """
        更新所有基金的最新净值（增量更新）
        
        Returns:
            dict: 更新结果统计
        """
        result = {
            "updated_funds": 0,
            "new_nav_records": 0,
            "skipped": 0,
            "errors": []
        }
        
        # 获取所有基金
        funds = self.db.query(Fund).all()
        
        logger.info(f"开始增量更新净值，共 {len(funds)} 个基金")
        
        for fund in funds:
            try:
                # 获取最新净值日期
                latest_nav = self.db.query(FundNav).filter(
                    FundNav.fund_code == fund.fund_code
                ).order_by(FundNav.nav_date.desc()).first()
                
                # 获取最近2天的净值数据
                nav_df = ak.fund_nav_em(fund=fund.fund_code)
                
                if nav_df is None or nav_df.empty:
                    result["skipped"] += 1
                    continue
                
                # 只处理比最新日期更新的数据
                new_count = 0
                for _, row in nav_df.head(5).iterrows():  # 只取最近5条
                    nav_date = row.get('净值日期')
                    if isinstance(nav_date, str):
                        nav_date = pd.to_datetime(nav_date)
                    
                    # 检查是否已存在
                    if latest_nav and nav_date <= latest_nav.nav_date:
                        continue
                    
                    nav = row.get('单位净值')
                    if nav:
                        nav_record = FundNav(
                            fund_code=fund.fund_code,
                            nav_date=nav_date,
                            nav=float(nav),
                            accumulated_nav=float(row.get('累计净值')) if pd.notna(row.get('累计净值')) else None,
                            daily_growth=float(str(row.get('日增长率', '0')).replace('%', '')) if pd.notna(row.get('日增长率')) else None
                        )
                        self.db.add(nav_record)
                        new_count += 1
                
                if new_count > 0:
                    result["updated_funds"] += 1
                    result["new_nav_records"] += new_count
                
                time.sleep(self.request_delay)
                
            except Exception as e:
                result["errors"].append(f"{fund.fund_code}: {str(e)}")
                logger.warning(f"更新基金 {fund.fund_code} 净值失败: {e}")
                continue
        
        self.db.commit()
        logger.info(f"净值更新完成: 更新 {result['updated_funds']} 个基金，新增 {result['new_nav_records']} 条记录")
        
        return result


class ScheduledCollector:
    """定时采集器"""
    
    @staticmethod
    def run_scheduled_collection(db: Session) -> Dict[str, Any]:
        """
        执行定时采集任务
        
        Args:
            db: 数据库会话
            
        Returns:
            dict: 采集结果
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "tasks": {}
        }
        
        collector = DataCollector(db)
        
        # 1. 增量更新净值
        logger.info("执行定时任务: 增量更新净值")
        results["tasks"]["update_nav"] = collector.update_latest_nav()
        
        # 2. 每天下午6点额外更新基金详情
        current_hour = datetime.now().hour
        if current_hour >= 18:  # 下午6点后
            logger.info("执行定时任务: 更新基金详情")
            results["tasks"]["update_details"] = collector.update_fund_details()
        
        return results