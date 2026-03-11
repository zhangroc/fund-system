import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Space,
  Tabs,
  Spin,
  Empty,
  Select,
  Button,
  Tooltip,
  Divider,
} from 'antd';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
  BarChart,
  Bar,
  ReferenceLine,
  Scatter,
  ScatterChart,
  ZAxis,
} from 'recharts';
import {
  RiseOutlined,
  FallOutlined,
  TrophyOutlined,
  ThunderboltOutlined,
  SafetyOutlined,
  DollarOutlined,
  DownloadOutlined,
  FileExcelOutlined,
} from '@ant-design/icons';
import type { BacktestResult, RiskMetrics, EquityPoint, Trade, MonthlyReturn } from '../../types';

const { Option } = Select;

interface BacktestResultPanelProps {
  result: BacktestResult;
  riskMetrics?: RiskMetrics;
  benchmarkData?: Array<{ date: string; value: number }>;
  loading?: boolean;
  onExportCSV?: () => void;
  onExportExcel?: () => void;
}

// 风险等级颜色
const RISK_COLORS: Record<string, string> = {
  A: '#52c41a',
  B: '#1890ff',
  C: '#faad14',
  D: '#fa8c16',
  E: '#ff4d4f',
};

const BacktestResultPanel: React.FC<BacktestResultPanelProps> = ({
  result,
  riskMetrics,
  benchmarkData = [],
  loading = false,
  onExportCSV,
  onExportExcel,
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [showBenchmark, setShowBenchmark] = useState(true);

  // 处理收益曲线数据
  const equityCurveData = useMemo(() => {
    if (!result.equity_curve) return [];
    
    const data = result.equity_curve.map((point: EquityPoint) => ({
      date: point.date,
      value: point.value,
      invested: point.invested,
      cash: point.cash || 0,
    }));
    
    // 合并基准数据
    if (showBenchmark && benchmarkData.length > 0) {
      const benchmarkStart = benchmarkData[0].value;
      return data.map((point) => {
        const benchmarkPoint = benchmarkData.find(b => b.date === point.date);
        return {
          ...point,
          benchmark: benchmarkPoint ? (benchmarkPoint.value / benchmarkStart) * result.initial_capital : null,
        };
      });
    }
    
    return data;
  }, [result, benchmarkData, showBenchmark]);

  // 计算关键统计
  const stats = useMemo(() => {
    if (!result) return null;
    
    return {
      totalReturn: result.total_return,
      totalReturnPct: result.total_return_pct,
      finalValue: result.final_value,
      initialCapital: result.initial_capital,
      totalInvested: result.equity_curve?.[result.equity_curve.length - 1]?.invested || 0,
    };
  }, [result]);

  // 渲染风险指标卡片
  const renderRiskMetrics = () => {
    if (!riskMetrics) return null;

    const metrics = [
      {
        title: '年化收益率',
        value: riskMetrics.annualizedReturn,
        suffix: '%',
        precision: 2,
        color: riskMetrics.annualizedReturn >= 0 ? '#ff4d4f' : '#52c41a',
        icon: <RiseOutlined />,
      },
      {
        title: '最大回撤',
        value: riskMetrics.maxDrawdown,
        suffix: '%',
        precision: 2,
        color: riskMetrics.maxDrawdown > 20 ? '#ff4d4f' : riskMetrics.maxDrawdown > 10 ? '#faad14' : '#52c41a',
        icon: <FallOutlined />,
        tooltip: '从最高点到最低点的最大跌幅',
      },
      {
        title: '年化波动率',
        value: riskMetrics.volatility,
        suffix: '%',
        precision: 2,
        icon: <ThunderboltOutlined />,
        tooltip: '收益率的标准差年化值',
      },
      {
        title: '夏普比率',
        value: riskMetrics.sharpeRatio,
        precision: 2,
        icon: <TrophyOutlined />,
        tooltip: '风险调整后的收益指标，越高越好',
      },
      {
        title: '卡玛比率',
        value: riskMetrics.calmarRatio,
        precision: 2,
        icon: <SafetyOutlined />,
        tooltip: '年化收益/最大回撤，越高越好',
      },
      {
        title: 'Alpha',
        value: riskMetrics.alpha,
        suffix: '%',
        precision: 2,
        icon: <DollarOutlined />,
        tooltip: '相对于基准的超额收益',
      },
      {
        title: 'Beta',
        value: riskMetrics.beta,
        precision: 2,
        icon: <ThunderboltOutlined />,
        tooltip: '相对于基准的系统性风险',
      },
      {
        title: '风险等级',
        value: riskMetrics.riskLevel,
        color: RISK_COLORS[riskMetrics.riskLevel] || '#999',
        isRiskLevel: true,
        icon: <SafetyOutlined />,
        tooltip: '综合风险评级',
      },
    ];

    return (
      <Row gutter={[16, 16]}>
        {metrics.map((metric, idx) => (
          <Col xs={12} sm={8} md={6} key={idx}>
            <Card size="small" hoverable>
              <Statistic
                title={
                  <Tooltip title={metric.tooltip}>
                    <Space>
                      {metric.title}
                      {metric.tooltip && <span style={{ color: '#999' }}>ⓘ</span>}
                    </Space>
                  </Tooltip>
                }
                value={metric.isRiskLevel ? metric.value : metric.value?.toFixed(metric.precision)}
                suffix={metric.suffix}
                valueStyle={{
                  color: metric.color,
                  fontSize: metric.isRiskLevel ? 28 : 20,
                  fontWeight: 'bold',
                }}
                prefix={!metric.isRiskLevel ? metric.icon : undefined}
              />
            </Card>
          </Col>
        ))}
      </Row>
    );
  };

  // 渲染收益曲线图
  const renderEquityCurve = () => {
    if (!equityCurveData || equityCurveData.length === 0) {
      return <Empty description="暂无收益曲线数据" style={{ height: 400 }} />;
    }

    return (
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={equityCurveData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="valueGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#1890ff" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#1890ff" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11 }}
            tickFormatter={(value) => value.split('-').slice(1).join('/')}
          />
          <YAxis
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => `¥${(v / 10000).toFixed(1)}万`}
            domain={['auto', 'auto']}
          />
          <RechartsTooltip
            formatter={(value: number, name: string) => {
              const labels: Record<string, string> = {
                value: '资产值',
                invested: '累计投入',
                benchmark: '基准(沪深300)',
              };
              return [`¥${value?.toLocaleString()}`, labels[name] || name];
            }}
            labelFormatter={(label) => `日期: ${label}`}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#1890ff"
            fillOpacity={1}
            fill="url(#valueGradient)"
            name="资产值"
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="invested"
            stroke="#ff4d4f"
            strokeDasharray="5 5"
            name="累计投入"
            dot={false}
            strokeWidth={2}
          />
          {showBenchmark && (
            <Line
              type="monotone"
              dataKey="benchmark"
              stroke="#52c41a"
              strokeWidth={2}
              name="基准(沪深300)"
              dot={false}
              connectNulls
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    );
  };

  // 渲染月度收益表格
  const renderMonthlyReturns = () => {
    if (!result.monthly_returns || result.monthly_returns.length === 0) {
      return <Empty description="暂无月度收益数据" />;
    }

    const columns = [
      {
        title: '月份',
        dataIndex: 'month',
        key: 'month',
        width: 100,
      },
      {
        title: '收益率',
        dataIndex: 'return',
        key: 'return',
        width: 120,
        render: (value: number) => (
          <Tag color={value >= 0 ? 'red' : 'green'}>
            {value >= 0 ? '+' : ''}{value?.toFixed(2)}%
          </Tag>
        ),
      },
      {
        title: '收益柱',
        key: 'bar',
        render: (_: any, record: MonthlyReturn) => {
          const maxReturn = Math.max(...result.monthly_returns!.map((m) => Math.abs(m.return)));
          const width = maxReturn > 0 ? (Math.abs(record.return) / maxReturn) * 100 : 0;
          return (
            <div
              style={{
                width: '100%',
                height: 20,
                backgroundColor: '#f0f0f0',
                borderRadius: 2,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${width}%`,
                  height: '100%',
                  backgroundColor: record.isPositive ? '#ff4d4f' : '#52c41a',
                  display: 'inline-block',
                }}
              />
            </div>
          );
        },
      },
    ];

    return (
      <Table
        dataSource={result.monthly_returns}
        columns={columns}
        rowKey="month"
        pagination={false}
        size="small"
      />
    );
  };

  // 渲染交易记录
  const renderTradeHistory = () => {
    if (!result.trades || result.trades.length === 0) {
      return <Empty description="暂无交易记录" />;
    }

    const columns = [
      {
        title: '日期',
        dataIndex: 'date',
        key: 'date',
        width: 120,
        render: (date: string) => date?.split('T')[0],
      },
      {
        title: '操作',
        dataIndex: 'action',
        key: 'action',
        width: 80,
        render: (action: string) => (
          <Tag color={action === 'buy' ? 'red' : 'green'}>
            {action === 'buy' ? '买入' : '卖出'}
          </Tag>
        ),
      },
      {
        title: '基金代码',
        dataIndex: 'fund_code',
        key: 'fund_code',
        width: 100,
      },
      {
        title: '基金名称',
        dataIndex: 'fund_name',
        key: 'fund_name',
        ellipsis: true,
      },
      {
        title: '价格',
        dataIndex: 'price',
        key: 'price',
        width: 100,
        render: (value: number) => value?.toFixed(4),
      },
      {
        title: '份额',
        dataIndex: 'shares',
        key: 'shares',
        width: 100,
        render: (value: number) => value?.toFixed(2),
      },
      {
        title: '金额',
        dataIndex: 'amount',
        key: 'amount',
        width: 120,
        render: (value: number) => `¥${value?.toFixed(2)}`,
      },
      {
        title: '手续费',
        dataIndex: 'commission',
        key: 'commission',
        width: 100,
        render: (value: number) => value ? `¥${value?.toFixed(2)}` : '-',
      },
    ];

    return (
      <Table
        dataSource={result.trades}
        columns={columns}
        rowKey={(record) => `${record.date}-${record.action}-${record.fund_code}`}
        pagination={{ pageSize: 10, showSizeChanger: true }}
        size="small"
        scroll={{ x: 800 }}
      />
    );
  };

  // 渲染月度收益柱状图
  const renderMonthlyChart = () => {
    if (!result.monthly_returns || result.monthly_returns.length === 0) {
      return <Empty description="暂无月度收益数据" style={{ height: 300 }} />;
    }

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={result.monthly_returns.slice(-24)} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="month" tick={{ fontSize: 10 }} />
          <YAxis
            tick={{ fontSize: 10 }}
            tickFormatter={(v) => `${v}%`}
          />
          <RechartsTooltip formatter={(value: number) => `${value?.toFixed(2)}%`} />
          <Bar dataKey="return" name="月收益率%">
            {result.monthly_returns.slice(-24).map((entry, index) => (
              <Bar key={index} dataKey="return" fill={entry.isPositive ? '#ff4d4f' : '#52c41a'} />
            ))}
          </Bar>
          <ReferenceLine y={0} stroke="#666" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  // 渲染交易统计
  const renderTradeStats = () => {
    if (!result.trades || result.trades.length === 0) return null;

    const buyCount = result.trades.filter((t) => t.action === 'buy').length;
    const sellCount = result.trades.filter((t) => t.action === 'sell').length;
    const totalCommission = result.trades.reduce((sum, t) => sum + (t.commission || 0), 0);
    const avgBuyPrice = result.trades
      .filter((t) => t.action === 'buy')
      .reduce((sum, t, _, arr) => sum + t.price / arr.length, 0);

    return (
      <Row gutter={16}>
        <Col span={6}>
          <Statistic title="总交易次数" value={result.trades.length} />
        </Col>
        <Col span={6}>
          <Statistic title="买入次数" value={buyCount} valueStyle={{ color: '#ff4d4f' }} />
        </Col>
        <Col span={6}>
          <Statistic title="卖出次数" value={sellCount} valueStyle={{ color: '#52c41a' }} />
        </Col>
        <Col span={6}>
          <Statistic title="总手续费" value={totalCommission} precision={2} prefix="¥" />
        </Col>
      </Row>
    );
  };

  if (!result) {
    return <Empty description="暂无回测结果" />;
  }

  return (
    <Spin spinning={loading}>
      {/* 基础收益指标 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="初始资金"
              value={stats?.initialCapital}
              prefix="¥"
              precision={0}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="最终价值"
              value={stats?.finalValue}
              prefix="¥"
              precision={0}
              valueStyle={{ color: stats?.finalValue >= stats?.initialCapital ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="总收益"
              value={stats?.totalReturn}
              prefix="¥"
              precision={0}
              valueStyle={{ color: stats?.totalReturn >= 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="收益率"
              value={stats?.totalReturnPct}
              suffix="%"
              precision={2}
              valueStyle={{ color: stats?.totalReturnPct >= 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Tab 切换 */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'overview',
            label: '收益概览',
            children: (
              <>
                <Space style={{ marginBottom: 16 }}>
                  <Button onClick={() => setShowBenchmark(!showBenchmark)}>
                    {showBenchmark ? '隐藏基准' : '显示基准'}
                  </Button>
                  <Button icon={<DownloadOutlined />} onClick={onExportCSV}>
                    导出CSV
                  </Button>
                  <Button icon={<FileExcelOutlined />} onClick={onExportExcel}>
                    导出Excel
                  </Button>
                </Space>
                {renderEquityCurve()}
              </>
            ),
          },
          {
            key: 'risk',
            label: '风险指标',
            children: renderRiskMetrics(),
          },
          {
            key: 'monthly',
            label: '月度收益',
            children: (
              <>
                <Divider>月度收益柱状图</Divider>
                {renderMonthlyChart()}
                <Divider>月度收益详情</Divider>
                {renderMonthlyReturns()}
              </>
            ),
          },
          {
            key: 'trades',
            label: '交易记录',
            children: (
              <>
                <Divider>交易统计</Divider>
                {renderTradeStats()}
                <Divider>交易明细</Divider>
                {renderTradeHistory()}
              </>
            ),
          },
        ]}
      />
    </Spin>
  );
};

export default BacktestResultPanel;