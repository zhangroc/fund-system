import React, { useState } from 'react';
import { Layout, Menu, Card, Tabs, message } from 'antd';
import {
  SettingOutlined,
  LineChartOutlined,
  BarChartOutlined,
  HeatMapOutlined,
  DownloadOutlined,
} from '@ant-design/icons';

import { StrategyConfigForm, FundPoolSelector } from './components/StrategyConfig';
import { FundCompareChart } from './components/FundCompare';
import { BacktestResultPanel } from './components/BacktestResult';
import { HoldingsHeatmap } from './components/HoldingsHeatmap';
import { TradeExport } from './components/common';
import type { BacktestResult, RiskMetrics, Holding } from './types';

const { Header, Content, Sider } = Layout;
const { TabPane } = Tabs;

// 模拟回测结果数据
const mockBacktestResult: BacktestResult = {
  id: 1,
  name: '测试回测',
  strategy_id: 1,
  strategy_name: '稳健定投策略',
  start_date: '2023-01-01',
  end_date: '2024-12-31',
  initial_capital: 100000,
  final_value: 156000,
  total_return: 56000,
  total_return_pct: 56,
  equity_curve: [
    { date: '2023-01-01', value: 100000, invested: 10000 },
    { date: '2023-02-01', value: 102000, invested: 20000 },
    { date: '2023-03-01', value: 105000, invested: 30000 },
    { date: '2023-04-01', value: 108000, invested: 40000 },
    { date: '2023-05-01', value: 112000, invested: 50000 },
  ],
  trades: [
    { date: '2023-01-01', action: 'buy', fund_code: '000001', fund_name: '测试基金A', price: 1.2345, shares: 1000, amount: 1234.5, commission: 1.23 },
    { date: '2023-02-01', action: 'buy', fund_code: '000002', fund_name: '测试基金B', price: 2.3456, shares: 800, amount: 1876.48, commission: 1.88 },
    { date: '2023-03-01', action: 'sell', fund_code: '000001', fund_name: '测试基金A', price: 1.4567, shares: 500, amount: 728.35, commission: 0.73 },
  ],
  monthly_returns: [
    { month: '2023-01', return: 2.5, isPositive: true },
    { month: '2023-02', return: -1.2, isPositive: false },
    { month: '2023-03', return: 3.8, isPositive: true },
    { month: '2023-04', return: 1.5, isPositive: true },
    { month: '2023-05', return: -0.8, isPositive: false },
    { month: '2023-06', return: 4.2, isPositive: true },
  ],
};

const mockRiskMetrics: RiskMetrics = {
  annualizedReturn: 18.5,
  maxDrawdown: 12.3,
  volatility: 15.6,
  sharpeRatio: 1.18,
  calmarRatio: 1.5,
  sortinoRatio: 1.62,
  alpha: 5.2,
  beta: 0.85,
  riskLevel: 'B',
};

const mockHoldings: Holding[] = [
  { fund_code: '000001', fund_name: '测试基金A', weight: 0.25 },
  { fund_code: '000002', fund_name: '测试基金B', weight: 0.20 },
  { fund_code: '110011', fund_name: '测试基金C', weight: 0.15 },
  { fund_code: '160121', fund_name: '测试基金D', weight: 0.12 },
  { fund_code: '161039', fund_name: '测试基金E', weight: 0.10 },
  { fund_code: '470009', fund_name: '测试基金F', weight: 0.08 },
  { fund_code: '000003', fund_name: '测试基金G', weight: 0.05 },
  { fund_code: '000004', fund_name: '测试基金H', weight: 0.05 },
];

function App() {
  const [selectedKey, setSelectedKey] = useState('strategy');

  const handleStrategySubmit = (values: any) => {
    console.log('策略参数:', values);
    message.success('策略参数已提交，开始回测...');
    // 这里可以调用回测API
  };

  const renderContent = () => {
    switch (selectedKey) {
      case 'strategy':
        return (
          <Card title="策略参数配置" style={{ marginBottom: 16 }}>
            <StrategyConfigForm
              onSubmit={handleStrategySubmit}
              onCancel={() => message.info('取消配置')}
            />
          </Card>
        );

      case 'compare':
        return (
          <FundCompareChart
            funds={[
              { fund_code: '000001', fund_name: '测试基金A' },
              { fund_code: '000002', fund_name: '测试基金B' },
            ]}
            days={365}
          />
        );

      case 'backtest':
        return (
          <BacktestResultPanel
            result={mockBacktestResult}
            riskMetrics={mockRiskMetrics}
            benchmarkData={[
              { date: '2023-01-01', value: 100 },
              { date: '2023-02-01', value: 102 },
              { date: '2023-03-01', value: 98 },
              { date: '2023-04-01', value: 105 },
              { date: '2023-05-01', value: 108 },
            ]}
          />
        );

      case 'heatmap':
        return (
          <HoldingsHeatmap holdings={mockHoldings} />
        );

      case 'export':
        return (
          <Card title="交易记录导出">
            <Tabs defaultActiveKey="trades">
              <TabPane tab="交易记录" key="trades">
                <TradeExport trades={mockBacktestResult.trades}>
                  <div style={{ padding: 20, textAlign: 'center' }}>
                    <p>点击按钮导出交易记录</p>
                    <TradeExport trades={mockBacktestResult.trades} />
                  </div>
                </TradeExport>
                <pre style={{ background: '#f5f5f5', padding: 16, borderRadius: 4 }}>
                  {JSON.stringify(mockBacktestResult.trades, null, 2)}
                </pre>
              </TabPane>
              <TabPane tab="完整报告" key="full">
                <TradeExport backtestResult={mockBacktestResult}>
                  <div style={{ padding: 20, textAlign: 'center' }}>
                    <p>点击导出完整回测报告</p>
                  </div>
                </TradeExport>
              </TabPane>
            </Tabs>
          </Card>
        );

      default:
        return null;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 20px', color: 'white', fontSize: 20, fontWeight: 'bold' }}>
        🚀 公募基金筛选与策略回测系统 V2.0
      </Header>
      <Layout>
        <Sider width={220} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            onClick={(e) => setSelectedKey(e.key)}
            style={{ height: '100%' }}
            items={[
              { key: 'strategy', icon: <SettingOutlined />, label: '策略配置' },
              { key: 'compare', icon: <LineChartOutlined />, label: '基金对比' },
              { key: 'backtest', icon: <BarChartOutlined />, label: '回测结果' },
              { key: 'heatmap', icon: <HeatMapOutlined />, label: '持仓热力图' },
              { key: 'export', icon: <DownloadOutlined />, label: '导出功能' },
            ]}
          />
        </Sider>
        <Layout style={{ padding: '20px' }}>
          <Content style={{ background: '#fff', padding: 20, minHeight: 280 }}>
            {renderContent()}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}

export default App;