import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Card, Row, Col, Select, Space, DatePicker, Button, Tag, Empty, Spin, message, Statistic, Tooltip } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, ReferenceLine, Area, ComposedChart } from 'recharts';
import { DownloadOutlined, ReloadOutlined, ZoomInOutlined, ZoomOutOutlined, FullscreenOutlined } from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import axios from 'axios';
import type { FundCompareData, NavPoint } from '../../types';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface FundCompareChartProps {
  funds?: Array<{
    fund_code: string;
    fund_name?: string;
    color?: string;
  }>;
  days?: number;
  onExport?: (chartType: string) => void;
  showCumulativeReturn?: boolean;
  showRelativeStrength?: boolean;
}

const COLORS = ['#1890ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16'];

const FundCompareChart: React.FC<FundCompareChartProps> = ({
  funds: initialFunds = [],
  days: defaultDays = 365,
  onExport,
  showCumulativeReturn = true,
  showRelativeStrength = false,
}) => {
  const [funds, setFunds] = useState<Fund[]>([]);
  const [selectedFunds, setSelectedFunds] = useState<string[]>(initialFunds.map(f => f.fund_code));
  const [compareData, setCompareData] = useState<Record<string, NavPoint[]>>({});
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().subtract(defaultDays, 'days'),
    dayjs(),
  ]);
  const [chartType, setChartType] = useState<'nav' | 'cumulative' | 'relative'>('nav');
  const [zoomLevel, setZoomLevel] = useState(1);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchFunds();
  }, []);

  useEffect(() => {
    if (selectedFunds.length > 0) {
      fetchCompareData();
    }
  }, [selectedFunds, dateRange]);

  const fetchFunds = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/funds`, {
        params: { page: 1, page_size: 200 },
      });
      setFunds(response.data.data || []);
    } catch (error) {
      console.error('获取基金列表失败:', error);
    }
  };

  const fetchCompareData = async () => {
    if (selectedFunds.length === 0) return;
    
    setLoading(true);
    const data: Record<string, NavPoint[]> = {};
    
    try {
      await Promise.all(
        selectedFunds.map(async (fundCode) => {
          const days = dateRange[1].diff(dateRange[0], 'days');
          const response = await axios.get(
            `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/funds/${fundCode}/nav`,
            { params: { days } }
          );
          data[fundCode] = (response.data.data || []).map((item: any) => ({
            date: item.nav_date,
            nav: item.nav,
            change_pct: item.change_pct,
          }));
        })
      );
      setCompareData(data);
    } catch (error) {
      message.error('获取净值数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理图表数据
  const chartData = useMemo(() => {
    if (Object.keys(compareData).length === 0) return [];
    
    // 获取所有日期
    const allDates = new Set<string>();
    Object.values(compareData).forEach(data => {
      data.forEach(point => allDates.add(point.date));
    });
    
    const sortedDates = Array.from(allDates).sort();
    const result: any[] = [];
    
    sortedDates.forEach((date, index) => {
      const point: any = { date: dayjs(date).format('MM/DD') };
      
      selectedFunds.forEach((fundCode, idx) => {
        const fundData = compareData[fundCode];
        const fundPoint = fundData?.find(p => p.date === date);
        
        if (fundPoint) {
          if (chartType === 'nav') {
            point[fundCode] = fundPoint.nav;
          } else if (chartType === 'cumulative') {
            // 计算累计收益率
            const firstNav = fundData[0]?.nav || 1;
            point[fundCode] = ((fundPoint.nav - firstNav) / firstNav) * 100;
          } else if (chartType === 'relative') {
            // 计算相对强弱（相对于第一个基金）
            if (index === 0) {
              point[fundCode] = 0;
            } else {
              const firstFundData = compareData[selectedFunds[0]] || [];
              const currentNav = fundPoint.nav;
              const firstFundNav = firstFundData[index]?.nav || firstFundData[0]?.nav || 1;
              const currentFirstFundNav = firstFundData[index]?.nav || firstFundData[0]?.nav || 1;
              const change = (currentNav - firstFundNav) / firstFundNav * 100;
              const firstFundChange = (currentFirstFundNav - firstFundData[0]?.nav) / firstFundData[0]?.nav * 100;
              point[fundCode] = change - firstFundChange;
            }
          }
        }
      });
      
      result.push(point);
    });
    
    // 应用缩放
    const zoomedLength = Math.floor(result.length * zoomLevel);
    const startIdx = Math.max(0, result.length - zoomedLength);
    
    return result.slice(startIdx);
  }, [compareData, selectedFunds, chartType, zoomLevel]);

  // 计算统计数据
  const stats = useMemo(() => {
    return selectedFunds.map((fundCode, idx) => {
      const data = compareData[fundCode];
      if (!data || data.length < 2) return { fundCode, totalReturn: 0, maxDrawdown: 0 };
      
      const firstNav = data[0].nav;
      const lastNav = data[data.length - 1].nav;
      const totalReturn = ((lastNav - firstNav) / firstNav) * 100;
      
      // 计算最大回撤
      let maxDrawdown = 0;
      let peak = firstNav;
      data.forEach(point => {
        if (point.nav > peak) peak = point.nav;
        const drawdown = ((peak - point.nav) / peak) * 100;
        if (drawdown > maxDrawdown) maxDrawdown = drawdown;
      });
      
      return {
        fundCode,
        totalReturn,
        maxDrawdown,
        color: COLORS[idx % COLORS.length],
      };
    });
  }, [compareData, selectedFunds]);

  const handleFundSelect = (value: string[]) => {
    setSelectedFunds(value);
  };

  const handleExport = () => {
    if (onExport) {
      onExport(chartType);
    } else {
      // 默认导出为图片
      const svg = containerRef.current?.querySelector('svg');
      if (svg) {
        const svgData = new XMLSerializer().serializeToString(svg);
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.onload = () => {
          canvas.width = svg.width.baseVal.value;
          canvas.height = svg.height.baseVal.value;
          ctx?.drawImage(img, 0, 0);
          const png = canvas.toDataURL('image/png');
          const link = document.createElement('a');
          link.download = `fund-compare-${chartType}-${dayjs().format('YYYYMMDD')}.png`;
          link.href = png;
          link.click();
        };
        img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
      }
    }
  };

  const getFundName = (code: string) => {
    const fund = funds.find(f => f.fund_code === code);
    return fund?.fund_name || code;
  };

  const renderChart = () => {
    if (!chartData || chartData.length === 0) {
      return <Empty description="暂无对比数据" style={{ height: 400 }} />;
    }

    const chartProps = {
      data: chartData,
      margin: { top: 10, right: 30, left: 10, bottom: 10 },
    };

    const xAxisProps = {
      dataKey: 'date',
      tick: { fontSize: 11 },
      tickFormatter: (value: string) => value,
    };

    const tooltipProps = {
      formatter: (value: number, name: string) => {
        if (chartType === 'nav') {
          return [value?.toFixed(4), '净值'];
        }
        return [value?.toFixed(2) + '%', '收益率'];
      },
      labelFormatter: (label: string) => `日期: ${label}`,
    };

    if (chartType === 'nav') {
      return (
        <ResponsiveContainer width="100%" height={450}>
          <ComposedChart {...chartProps}>
            <defs>
              {selectedFunds.map((_, idx) => (
                <linearGradient key={idx} id={`gradient-${idx}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS[idx % COLORS.length]} stopOpacity={0.2} />
                  <stop offset="95%" stopColor={COLORS[idx % COLORS.length]} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis {...xAxisProps} />
            <YAxis 
              tick={{ fontSize: 11 }} 
              tickFormatter={(v) => v?.toFixed(2)}
              domain={['auto', 'auto']}
            />
            <RechartsTooltip {...tooltipProps} />
            <Legend />
            {selectedFunds.map((fundCode, idx) => (
              <Area
                key={fundCode}
                type="monotone"
                dataKey={fundCode}
                name={getFundName(fundCode)}
                stroke={COLORS[idx % COLORS.length]}
                fill={`url(#gradient-${idx})`}
                strokeWidth={2}
              />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      );
    }

    return (
      <ResponsiveContainer width="100%" height={450}>
        <LineChart {...chartProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis {...xAxisProps} />
          <YAxis 
            tick={{ fontSize: 11 }} 
            tickFormatter={(v) => `${v?.toFixed(1)}%`}
          />
          <RechartsTooltip {...tooltipProps} />
          <Legend />
          {selectedFunds.map((fundCode, idx) => (
            <Line
              key={fundCode}
              type="monotone"
              dataKey={fundCode}
              name={getFundName(fundCode)}
              stroke={COLORS[idx % COLORS.length]}
              strokeWidth={2}
              dot={false}
              connectNulls
            />
          ))}
          {chartType === 'relative' && (
            <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" />
          )}
        </LineChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div ref={containerRef}>
      <Card
        title={
          <Space>
            <span>基金对比曲线</span>
            <Tag color="blue">{selectedFunds.length} 只基金</Tag>
          </Space>
        }
        extra={
          <Space>
            <Select
              mode="multiple"
              value={selectedFunds}
              onChange={handleFundSelect}
              style={{ minWidth: 300 }}
              placeholder="选择基金进行对比"
              maxTagCount={3}
              maxTagPlaceholder={(omitted) => `+${omitted.length}`}
            >
              {funds.map((fund) => (
                <Option key={fund.fund_code} value={fund.fund_code}>
                  <Space>
                    <span>{fund.fund_name}</span>
                    <Tag>{fund.fund_code}</Tag>
                  </Space>
                </Option>
              ))}
            </Select>
            <RangePicker
              value={dateRange}
              onChange={(dates) => {
                if (dates && dates[0] && dates[1]) {
                  setDateRange([dates[0], dates[1]]);
                }
              }}
              allowClear={false}
            />
          </Space>
        }
      >
        {/* 图表类型选择和数据统计 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col flex="auto">
            <Space>
              <Button
                type={chartType === 'nav' ? 'primary' : 'default'}
                onClick={() => setChartType('nav')}
              >
                净值走势
              </Button>
              <Button
                type={chartType === 'cumulative' ? 'primary' : 'default'}
                onClick={() => setChartType('cumulative')}
                disabled={!showCumulativeReturn}
              >
                累计收益
              </Button>
              <Button
                type={chartType === 'relative' ? 'primary' : 'default'}
                onClick={() => setChartType('relative')}
                disabled={!showRelativeStrength || selectedFunds.length < 2}
              >
                相对强弱
              </Button>
              <Button icon={<DownloadOutlined />} onClick={handleExport}>
                导出
              </Button>
            </Space>
          </Col>
          <Col>
            <Space>
              <Tooltip title="放大">
                <Button
                  icon={<ZoomInOutlined />}
                  onClick={() => setZoomLevel(Math.min(zoomLevel * 1.5, 3))}
                  disabled={zoomLevel >= 3}
                />
              </Tooltip>
              <Tooltip title="缩小">
                <Button
                  icon={<ZoomOutOutlined />}
                  onClick={() => setZoomLevel(zoomLevel / 1.5)}
                  disabled={zoomLevel <= 0.33}
                />
              </Tooltip>
              <Tooltip title="刷新">
                <Button icon={<ReloadOutlined />} onClick={fetchCompareData} loading={loading} />
              </Tooltip>
            </Space>
          </Col>
        </Row>

        {/* 统计卡片 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          {stats.map((stat, idx) => (
            <Col span={6} key={stat.fundCode}>
              <Card size="small">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div
                    style={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: stat.color,
                    }}
                  />
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <div style={{ fontWeight: 500, fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {getFundName(stat.fundCode)}
                    </div>
                    <div style={{ fontSize: 11, color: '#666' }}>
                      {stat.totalReturn >= 0 ? '+' : ''}{stat.totalReturn.toFixed(2)}%
                    </div>
                  </div>
                </div>
              </Card>
            </Col>
          ))}
        </Row>

        {/* 图表 */}
        <Spin spinning={loading}>{renderChart()}</Spin>

        {/* 说明 */}
        {chartType === 'nav' && (
          <div style={{ marginTop: 8, fontSize: 12, color: '#999', textAlign: 'center' }}>
            支持鼠标悬停查看详细数据，滚轮缩放图表
          </div>
        )}
      </Card>
    </div>
  );
};

export default FundCompareChart;