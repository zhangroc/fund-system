import React, { useState, useMemo } from 'react';
import {
  Card,
  Row,
  Col,
  Select,
  Space,
  Tag,
  Spin,
  Empty,
  Tooltip,
  Progress,
  Table,
  Radio,
} from 'antd';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import {
  HeatMapOutlined,
  PieChartOutlined,
  BarChartOutlined,
  RadarChartOutlined,
} from '@ant-design/icons';
import type { Holding, Portfolio } from '../../types';

const { Option } = Select;

const COLORS = [
  '#1890ff',
  '#52c41a',
  '#faad14',
  '#ff4d4f',
  '#722ed1',
  '#13c2c2',
  '#eb2f96',
  '#fa8c16',
  '#2f54eb',
  '#a0d911',
];

// 模拟行业数据（实际应该从API获取）
const INDUSTRY_DATA = {
  '000001': '金融地产',
  '000002': '消费',
  '000003': '医药',
  '000004': '科技',
  '000005': '制造',
  '110011': '消费',
  '110022': '医药',
  '160121': '科技',
  '161039': '新能源',
  '470009': '金融地产',
};

// 模拟重仓股数据（实际应该从API获取）
const HOLDING_STOCKS = {
  '000001': ['贵州茅台', '宁德时代', '招商银行', '中国平安', '五粮液'],
  '000002': ['海康威视', '美的集团', '格力电器', '比亚迪', '立讯精密'],
  '000003': ['恒瑞医药', '药明康德', '迈瑞医疗', '爱尔眼科', '智飞生物'],
  '000004': ['隆基绿能', '阳光电源', '通威股份', '宁德时代', '亿纬锂能'],
  '000005': ['中国中免', '上海机场', '宋城演艺', '锦江酒店', '首旅酒店'],
};

interface HoldingsHeatmapProps {
  portfolio?: Portfolio;
  holdings?: Holding[];
  loading?: boolean;
}

// 风格因子定义
const STYLE_FACTORS = [
  { key: 'size', name: '规模', min: 0, max: 100 },
  { key: 'value', name: '价值', min: 0, max: 100 },
  { key: 'momentum', name: '动量', min: 0, max: 100 },
  { key: 'quality', name: '质量', min: 0, max: 100 },
  { key: 'volatility', name: '波动', min: 0, max: 100 },
  { key: 'growth', name: '成长', min: 0, max: 100 },
];

const HoldingsHeatmap: React.FC<HoldingsHeatmapProps> = ({
  portfolio,
  holdings: propHoldings,
  loading = false,
}) => {
  const [viewType, setViewType] = useState<'heatmap' | 'pie' | 'bar' | 'radar'>('heatmap');
  const [dimension, setDimension] = useState<'industry' | 'stock'>('industry');

  // 处理持仓数据
  const holdings = useMemo(() => {
    if (propHoldings) return propHoldings;
    if (portfolio?.holdings) return portfolio.holdings;
    return [];
  }, [propHoldings, portfolio]);

  // 行业分布数据
  const industryData = useMemo(() => {
    const data: Record<string, number> = {};
    holdings.forEach((holding) => {
      const industry = INDUSTRY_DATA[holding.fund_code] || '其他';
      data[industry] = (data[industry] || 0) + holding.weight * 100;
    });
    return Object.entries(data).map(([name, value]) => ({
      name,
      value: Math.round(value * 10) / 10,
    }));
  }, [holdings]);

  // 排序后的持仓数据
  const sortedHoldings = useMemo(() => {
    return [...holdings].sort((a, b) => b.weight - a.weight);
  }, [holdings]);

  // 计算风格因子（模拟数据）
  const styleData = useMemo(() => {
    return STYLE_FACTORS.map((factor) => ({
      ...factor,
      value: Math.random() * 60 + 20, // 模拟数据 20-80
    }));
  }, [holdings]);

  // 渲染热力图
  const renderHeatmap = () => {
    if (holdings.length === 0) {
      return <Empty description="暂无持仓数据" style={{ height: 400 }} />;
    }

    if (dimension === 'industry') {
      return (
        <Row gutter={[16, 16]}>
          {industryData.map((item, idx) => (
            <Col xs={12} sm={8} md={6} key={item.name}>
              <Card
                size="small"
                hoverable
                style={{
                  background: `linear-gradient(135deg, ${COLORS[idx % COLORS.length]}20 0%, ${COLORS[idx % COLORS.length]}40 100%)`,
                  borderColor: COLORS[idx % COLORS.length],
                }}
              >
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 16, fontWeight: 'bold', marginBottom: 8 }}>
                    {item.name}
                  </div>
                  <div
                    style={{
                      fontSize: 24,
                      fontWeight: 'bold',
                      color: COLORS[idx % COLORS.length],
                    }}
                  >
                    {item.value.toFixed(1)}%
                  </div>
                  <Progress
                    percent={item.value}
                    showInfo={false}
                    strokeColor={COLORS[idx % COLORS.length]}
                    style={{ marginTop: 8 }}
                  />
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      );
    }

    // 股票维度热力图
    return (
      <Table
        dataSource={sortedHoldings.slice(0, 20).map((h, idx) => ({
          key: idx,
          rank: idx + 1,
          fund_name: h.fund_name,
          fund_code: h.fund_code,
          weight: h.weight * 100,
          color: COLORS[idx % COLORS.length],
        }))}
        columns={[
          {
            title: '排名',
            dataIndex: 'rank',
            width: 60,
          },
          {
            title: '基金名称',
            dataIndex: 'fund_name',
          },
          {
            title: '基金代码',
            dataIndex: 'fund_code',
            render: (code: string) => <Tag>{code}</Tag>,
          },
          {
            title: '持仓占比',
            dataIndex: 'weight',
            render: (weight: number, record: any) => (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Progress
                  percent={weight}
                  showInfo={false}
                  strokeColor={record.color}
                  style={{ width: 100 }}
                />
                <span>{weight.toFixed(2)}%</span>
              </div>
            ),
          },
        ]}
        pagination={false}
        size="small"
      />
    );
  };

  // 渲染饼图
  const renderPieChart = () => {
    if (industryData.length === 0) {
      return <Empty description="暂无数据" style={{ height: 400 }} />;
    }

    return (
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <Pie
            data={industryData}
            cx="50%"
            cy="50%"
            labelLine={true}
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
            outerRadius={120}
            fill="#8884d8"
            dataKey="value"
          >
            {industryData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <RechartsTooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  // 渲染条形图
  const renderBarChart = () => {
    const data = dimension === 'industry' ? industryData : sortedHoldings.slice(0, 10).map((h) => ({
      name: h.fund_name.length > 6 ? h.fund_name.substring(0, 6) + '...' : h.fund_name,
      fullName: h.fund_name,
      value: h.weight * 100,
    }));

    if (data.length === 0) {
      return <Empty description="暂无数据" style={{ height: 400 }} />;
    }

    return (
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 80, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            type="number"
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => `${v}%`}
            domain={[0, 'auto']}
          />
          <YAxis
            type="category"
            dataKey={dimension === 'stock' ? 'name' : 'name'}
            tick={{ fontSize: 11 }}
            width={80}
          />
          <RechartsTooltip
            formatter={(value: number, name: string, props: any) => [
              `${value.toFixed(2)}%`,
              '持仓占比',
            ]}
            labelFormatter={(_, payload) => payload[0]?.payload?.fullName || ''}
          />
          <Bar dataKey="value" name="持仓占比" radius={[0, 4, 4, 0]}>
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );
  };

  // 渲染雷达图
  const renderRadarChart = () => {
    return (
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={styleData}>
          <PolarGrid stroke="#e0e0e0" />
          <PolarAngleAxis dataKey="name" tick={{ fontSize: 12 }} />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fontSize: 10 }}
          />
          <Radar
            name="持仓风格"
            dataKey="value"
            stroke="#1890ff"
            fill="#1890ff"
            fillOpacity={0.3}
          />
          <RechartsTooltip />
          <Legend />
        </RadarChart>
      </ResponsiveContainer>
    );
  };

  const renderContent = () => {
    switch (viewType) {
      case 'heatmap':
        return renderHeatmap();
      case 'pie':
        return renderPieChart();
      case 'bar':
        return renderBarChart();
      case 'radar':
        return renderRadarChart();
      default:
        return null;
    }
  };

  return (
    <Spin spinning={loading}>
      <Card
        title={
          <Space>
            <HeatMapOutlined />
            <span>持仓热力图</span>
            <Tag color="blue">{holdings.length} 只基金</Tag>
          </Space>
        }
        extra={
          <Space>
            <Radio.Group
              value={viewType}
              onChange={(e) => setViewType(e.target.value)}
              buttonStyle="solid"
              size="small"
            >
              <Radio.Button value="heatmap">
                <Tooltip title="热力图">
                  <HeatMapOutlined />
                </Tooltip>
              </Radio.Button>
              <Radio.Button value="pie">
                <Tooltip title="饼图">
                  <PieChartOutlined />
                </Tooltip>
              </Radio.Button>
              <Radio.Button value="bar">
                <Tooltip title="条形图">
                  <BarChartOutlined />
                </Tooltip>
              </Radio.Button>
              <Radio.Button value="radar">
                <Tooltip title="雷达图">
                  <RadarChartOutlined />
                </Tooltip>
              </Radio.Button>
            </Radio.Group>
            {viewType === 'heatmap' && (
              <Select
                value={dimension}
                onChange={setDimension}
                style={{ width: 100 }}
                size="small"
              >
                <Option value="industry">按行业</Option>
                <Option value="stock">按基金</Option>
              </Select>
            )}
          </Space>
        }
      >
        {/* 统计摘要 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card size="small">
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: '#999', fontSize: 12 }}>持有基金数</div>
                <div style={{ fontSize: 24, fontWeight: 'bold' }}>{holdings.length}</div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: '#999', fontSize: 12 }}>行业覆盖</div>
                <div style={{ fontSize: 24, fontWeight: 'bold' }}>{industryData.length}</div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: '#999', fontSize: 12 }}>第一大持仓</div>
                <div style={{ fontSize: 14, fontWeight: 'bold' }}>
                  {sortedHoldings[0]?.fund_name || '-'}
                </div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: '#999', fontSize: 12 }}>前五大持仓</div>
                <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                  {sortedHoldings
                    .slice(0, 5)
                    .reduce((sum, h) => sum + h.weight, 0)
                    .toFixed(1)}
                  %
                </div>
              </div>
            </Card>
          </Col>
        </Row>

        {/* 图表内容 */}
        {renderContent()}
      </Card>
    </Spin>
  );
};

export default HoldingsHeatmap;