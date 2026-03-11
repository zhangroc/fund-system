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
        self.request_delay = 0.5  # 请求间隔(秒)，避免被封
    
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
            
            # 获取基金列表 - 使用 fund_name_em 接口
            fund_df = ak.fund_name_em()
            
            if fund_df is None or fund_df.empty:
                logger.warning("未获取到基金数据")
                return result
            
            result["total"] = len(fund_df)
            logger.info(f"获取到 {len(fund_df)} 个基金")
            
            for idx, row in fund_df.iterrows():
                try:
                    fund_code = str(row.get('基金代码', '')).zfill(6)
                    fund_name = row.get('基金简称', '')
                    fund_type_str = row.get('基金类型', '')
                    
                    if not fund_code or not fund_name:
                        result["skipped"] += 1
                        continue
                    
                    # 检查是否已存在
                    existing = self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
                    if existing:
                        result["skipped"] += 1
                        continue
                    
                    # 解析基金类型
                    fund_type = self._parse_fund_type(fund_type_str)
                    
                    # 创建基金记录
                    fund = Fund(
                        fund_code=fund_code,
                        fund_name=fund_name,
                        fund_type=fund_type,
                        status="在售"
                    )
                    self.db.add(fund)
                    result["success"] += 1
                    
                    # 每500条提交一次
                    if result["success"] % 500 == 0:
                        self.db.commit()
                        logger.info(f"已处理 {result['success']} 个基金")
                    
                    # 减少请求间隔以加快采集速度
                    if result["success"] % 50 == 0:
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
    
    def _parse_fund_type(self, type_str: str) -> str:
        """解析基金类型 - 返回字符串"""
        type_str = str(type_str).lower()
        if '股票' in type_str:
            return "股票型"
        elif '混合' in type_str:
            return "混合型"
        elif '债券' in type_str:
            return "债券型"
        elif '指数' in type_str:
            return "指数型"
        elif '货币' in type_str:
            return "货币型"
        elif 'QDII' in type_str:
            return "QDII"
        elif 'ETF' in type_str or 'LOF' in type_str:
            return "ETF"
        elif 'FOF' in type_str:
            return "FOF"
        return "其他"
    
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
    
    def collect_fund_nav_batch(self, top_n: int = 5000, days: int = 365) -> Dict[str, Any]:
        """
        批量采集基金净值数据 - 高效版本
        1. 先用 fund_open_fund_daily_em 批量获取所有基金的最新净值
        2. 然后对前 top_n 只基金采集历史净值
        
        Args:
            top_n: 采集历史净值的基金数量
            days: 采集的历史天数
            
        Returns:
            dict: 采集结果统计
        """
        result = {
            "latest_nav_records": 0,
            "history_funds_processed": 0,
            "history_nav_records": 0,
            "errors": []
        }
        
        try:
            # 步骤1: 批量获取所有基金的最新净值
            logger.info("步骤1: 批量获取所有基金的最新净值...")
            daily_df = ak.fund_open_fund_daily_em()
            
            if daily_df is not None and not daily_df.empty:
                # 解析列名获取最新日期
                cols = daily_df.columns.tolist()
                nav_col = [c for c in cols if '单位净值' in c]
                accum_nav_col = [c for c in cols if '累计净值' in c]
                growth_col = [c for c in cols if '增长率' in c]
                
                today = datetime.now()
                
                for _, row in daily_df.iterrows():
                    try:
                        fund_code = str(row.get('基金代码', '')).zfill(6)
                        if not fund_code:
                            continue
                        
                        nav_date = today
                        nav = row.get(nav_col[0]) if nav_col else None
                        if nav is None:
                            continue
                        
                        # 检查是否已存在
                        existing = self.db.query(FundNav).filter(
                            FundNav.fund_code == fund_code,
                            FundNav.nav_date == nav_date
                        ).first()
                        
                        if existing:
                            continue
                        
                        accum_nav = row.get(accum_nav_col[0]) if accum_nav_col else None
                        daily_growth = row.get(growth_col[0]) if growth_col else None
                        if daily_growth and isinstance(daily_growth, str):
                            daily_growth = daily_growth.replace('%', '')
                        
                        nav_record = FundNav(
                            fund_code=fund_code,
                            nav_date=nav_date,
                            nav=float(nav),
                            accumulated_nav=float(accum_nav) if accum_nav else None,
                            daily_growth=float(daily_growth) if daily_growth else None
                        )
                        self.db.add(nav_record)
                        result["latest_nav_records"] += 1
                        
                    except Exception as e:
                        logger.warning(f"处理净值记录失败: {e}")
                        continue
                
                self.db.commit()
                logger.info(f"最新净值采集完成: {result['latest_nav_records']} 条记录")
            
            # 步骤2: 对前 top_n 只基金采集历史净值
            logger.info(f"步骤2: 采集前 {top_n} 只基金的历史净值...")
            funds = self.db.query(Fund).limit(top_n).all()
            
            for i, fund in enumerate(funds):
                try:
                    nav_count = self._sync_single_fund_nav(fund.fund_code, days)
                    result["history_nav_records"] += nav_count
                    result["history_funds_processed"] += 1
                    
                    if (i + 1) % 100 == 0:
                        logger.info(f"已处理 {i+1}/{top_n} 只基金的历史净值")
                        time.sleep(0.5)
                    
                except Exception as e:
                    result["errors"].append(f"{fund.fund_code}: {str(e)}")
                    continue
            
            self.db.commit()
            logger.info(f"历史净值采集完成: 处理 {result['history_funds_processed']} 个基金，新增 {result['history_nav_records']} 条记录")
            
        except Exception as e:
            logger.error(f"批量采集净值失败: {e}")
            result["errors"].append(str(e))
        
        return result
    
    def _sync_single_fund_nav(self, fund_code: str, days: int = 30) -> int:
        """同步单个基金的净值数据"""
        count = 0
        
        try:
            # 使用 fund_etf_fund_info_em 接口获取基金净值历史
            nav_df = ak.fund_etf_fund_info_em(fund=fund_code)
            
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
    
    def _parse_scale(self, scale_str) -> float:
        """解析基金规模字符串为数值（单位：亿元）"""
        if not scale_str or scale_str == '--' or pd.isna(scale_str):
            return 0.0
        scale_str = str(scale_str).strip()
        try:
            if '亿' in scale_str:
                return float(scale_str.replace('亿', ''))
            elif '万' in scale_str:
                return float(scale_str.replace('万', '')) / 10000
            elif '千万' in scale_str:
                return float(scale_str.replace('千万', '')) / 10
            elif '千万' in scale_str:
                return float(scale_str.replace('千万', '')) / 10
            else:
                return float(scale_str)
        except:
            return 0.0

    def _update_single_fund_detail(self, fund: Fund) -> None:
        """更新单个基金的详细信息"""
        try:
            # 使用 fund_individual_basic_info_xq 接口获取基金详情
            info_df = ak.fund_individual_basic_info_xq(symbol=fund.fund_code)
            
            if info_df is None or info_df.empty:
                fund.updated_at = datetime.now()
                return
            
            # 转换为字典方便查询
            info_dict = {}
            for _, row in info_df.iterrows():
                item = row.get('item', '')
                value = row.get('value', '')
                if item:
                    info_dict[item] = value
            
            # 更新基金规模
            scale_str = info_dict.get('最新规模', '0')
            fund.scale = self._parse_scale(scale_str)
            
            # 更新基金公司
            if '基金公司' in info_dict:
                fund.manager = info_dict['基金公司']
            
            # 更新基金经理
            if '基金经理' in info_dict:
                fund.fund_manager = info_dict['基金经理']
            
            # 更新托管银行
            if '托管银行' in info_dict:
                fund.custodian = info_dict['托管银行']
            
            # 更新成立日期
            if '成立时间' in info_dict:
                est_date = info_dict['成立时间']
                if est_date and est_date != '--':
                    try:
                        fund.establishment_date = pd.to_datetime(est_date)
                    except:
                        pass
            
            # 更新基金类型
            if '基金类型' in info_dict:
                fund_type = info_dict['基金类型']
                if fund_type and fund_type != '--':
                    fund.fund_type = self._parse_fund_type(fund_type)
            
            fund.updated_at = datetime.now()
            
        except Exception as e:
            logger.warning(f"更新基金 {fund.fund_code} 详情失败: {e}")
            fund.updated_at = datetime.now()
    
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
                
                # 获取最近2天的净值数据 - 使用 fund_etf_fund_info_em
                nav_df = ak.fund_etf_fund_info_em(fund=fund.fund_code)
                
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