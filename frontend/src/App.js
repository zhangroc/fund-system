import React, { useState, useEffect } from 'react';
import { Layout, Menu, Table, Card, Row, Col, Statistic, Select, Input, Button, Space, Tag, Spin, message, Breadcrumb, Descriptions, Divider } from 'antd';
import { FundOutlined, SearchOutlined, BarChartOutlined, SyncOutlined, FireOutlined, HomeOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

const { Header, Content, Sider } = Layout;
const { Option } = Select;

// 动态获取API地址，支持环境变量或当前host
const API_BASE = process.env.REACT_APP_API_URL || `${window.location.protocol}//${window.location.hostname}:8000`;

// ============ 基金列表页面组件 ============
function FundList({ onViewDetail }) {
  const [funds, setFunds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });
  const [stats, setStats] = useState(null);
  const [filters, setFilters] = useState({
    fund_type: null,
    manager: '',
    min_scale: null,
    max_scale: null,
    status: null,
    risk_level: null,
    min_nav: null,
    max_nav: null,
  });

  useEffect(() => {
    fetchFunds();
    fetchStats();
  }, [pagination]);

  useEffect(() => {
    // 筛选条件变化时重新加载数据
    fetchFunds();
  }, [filters]);

  const fetchFunds = async () => {
    setLoading(true);
    try {
      const params = {
        page: pagination.current,
        page_size: pagination.pageSize,
      };
      
      // 添加筛选参数
      if (filters.fund_type) params.fund_type = filters.fund_type;
      if (filters.manager) params.manager = filters.manager;
      if (filters.min_scale) params.min_scale = filters.min_scale;
      if (filters.max_scale) params.max_scale = filters.max_scale;
      if (filters.status) params.status = filters.status;
      
      const response = await axios.get(`${API_BASE}/api/v1/funds`, { params });
      setFunds(response.data.data);
      setTotal(response.data.total);
    } catch (error) {
      message.error('获取基金列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/v1/funds/stats/summary`);
      setStats(response.data);
    } catch (error) {
      console.error('获取统计数据失败');
    }
  };

  const handleTableChange = (newPagination) => {
    setPagination(newPagination);
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleReset = () => {
    setFilters({
      fund_type: null,
      manager: '',
      min_scale: null,
      max_scale: null,
      status: null,
      risk_level: null,
      min_nav: null,
      max_nav: null,
    });
  };

  const columns = [
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
      render: (text, record) => (
        <a onClick={() => onViewDetail(record)} style={{ fontWeight: 500 }}>
          {text}
        </a>
      ),
    },
    {
      title: '基金类型',
      dataIndex: 'fund_type',
      key: 'fund_type',
      width: 100,
      render: (type) => {
        const colorMap = {
          '股票型': 'red',
          '混合型': 'orange',
          '债券型': 'green',
          '指数型': 'blue',
          '货币型': 'gold',
          'QDII': 'purple',
        };
        return <Tag color={colorMap[type] || 'default'}>{type}</Tag>;
      },
    },
    {
      title: '管理公司',
      dataIndex: 'manager',
      key: 'manager',
      ellipsis: true,
    },
    {
      title: '基金规模(亿)',
      dataIndex: 'scale',
      key: 'scale',
      width: 120,
      sorter: (a, b) => (a.scale || 0) - (b.scale || 0),
      render: (scale) => scale ? scale.toFixed(2) : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status) => (
        <Tag color={status === '在售' ? 'green' : 'red'}>{status}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Button type="link" size="small" onClick={() => onViewDetail(record)}>
          查看详情
        </Button>
      ),
    },
  ];

  return (
    <>
      {/* 统计卡片 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: '20px' }}>
          <Col span={6}>
            <Card>
              <Statistic title="基金总数" value={stats.total_count} prefix={<FundOutlined />} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="总规模(亿)" value={stats.total_scale?.toFixed(2) || 0} precision={2} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="股票型" value={stats.type_stats?.find(t => t.type === '股票型')?.count || 0} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="混合型" value={stats.type_stats?.find(t => t.type === '混合型')?.count || 0} />
            </Card>
          </Col>
        </Row>
      )}

      {/* 筛选条件 */}
      <Card title="筛选条件" size="small" style={{ marginBottom: '16px' }}>
        <Space wrap style={{ width: '100%' }}>
          <div>
            <span style={{ marginRight: 8 }}>基金类型:</span>
            <Select
              placeholder="请选择"
              style={{ width: 120 }}
              allowClear
              value={filters.fund_type}
              onChange={(value) => handleFilterChange('fund_type', value)}
            >
              <Option value="股票型">股票型</Option>
              <Option value="混合型">混合型</Option>
              <Option value="债券型">债券型</Option>
              <Option value="指数型">指数型</Option>
              <Option value="货币型">货币型</Option>
              <Option value="QDII">QDII</Option>
            </Select>
          </div>
          <div>
            <span style={{ marginRight: 8 }}>管理公司:</span>
            <Input
              placeholder="输入公司名称"
              style={{ width: 150 }}
              value={filters.manager}
              onChange={(e) => handleFilterChange('manager', e.target.value)}
            />
          </div>
          <div>
            <span style={{ marginRight: 8 }}>最小规模(亿):</span>
            <Input
              type="number"
              placeholder="最小规模"
              style={{ width: 100 }}
              value={filters.min_scale}
              onChange={(e) => handleFilterChange('min_scale', e.target.value ? parseFloat(e.target.value) : null)}
            />
          </div>
          <div>
            <span style={{ marginRight: 8 }}>最大规模(亿):</span>
            <Input
              type="number"
              placeholder="最大规模"
              style={{ width: 100 }}
              value={filters.max_scale}
              onChange={(e) => handleFilterChange('max_scale', e.target.value ? parseFloat(e.target.value) : null)}
            />
          </div>
          <div>
            <span style={{ marginRight: 8 }}>状态:</span>
            <Select
              placeholder="请选择"
              style={{ width: 100 }}
              allowClear
              value={filters.status}
              onChange={(value) => handleFilterChange('status', value)}
            >
              <Option value="在售">在售</Option>
              <Option value="停售">停售</Option>
              <Option value="募集">募集</Option>
            </Select>
          </div>
          <div>
            <Button type="primary" icon={<SearchOutlined />} onClick={fetchFunds}>
              查询
            </Button>
            <Button style={{ marginLeft: 8 }} icon={<SyncOutlined />} onClick={fetchFunds}>
              刷新
            </Button>
            <Button style={{ marginLeft: 8 }} onClick={handleReset}>
              重置
            </Button>
          </div>
        </Space>
      </Card>

      {/* 基金表格 */}
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={funds}
          rowKey="id"
          pagination={{
            ...pagination,
            total: total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          onChange={handleTableChange}
          size="small"
        />
      </Spin>
    </>
  );
}

// ============ 基金详情页面组件 ============
function FundDetail({ fund, onBack }) {
  const [navData, setNavData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [days, setDays] = useState(30);

  useEffect(() => {
    if (fund) {
      fetchNavData();
    }
  }, [fund, days]);

  const fetchNavData = async () => {
    if (!fund) return;
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/api/v1/funds/${fund.fund_code}/nav`, {
        params: { days }
      });
      
      // 处理数据，按日期正序排列
      const data = (response.data.data || []).reverse().map(item => ({
        ...item,
        nav_date: new Date(item.nav_date).toLocaleDateString('zh-CN'),
      }));
      setNavData(data);
    } catch (error) {
      message.error('获取净值数据失败');
    } finally {
      setLoading(false);
    }
  };

  if (!fund) return null;

  // 计算收益率
  const latestNav = navData.length > 0 ? navData[navData.length - 1] : null;
  const firstNav = navData.length > 0 ? navData[0] : null;
  const returnRate = firstNav && latestNav ? ((latestNav.nav - firstNav.nav) / firstNav.nav * 100).toFixed(2) : 0;

  return (
    <div>
      <Button 
        type="link" 
        icon={<ArrowLeftOutlined />} 
        onClick={onBack}
        style={{ padding: 0, marginBottom: 16 }}
      >
        返回基金列表
      </Button>

      {/* 基本信息 */}
      <Card title="基金基本信息" style={{ marginBottom: 16 }}>
        <Descriptions column={4} bordered size="small">
          <Descriptions.Item label="基金代码">{fund.fund_code}</Descriptions.Item>
          <Descriptions.Item label="基金名称">{fund.fund_name}</Descriptions.Item>
          <Descriptions.Item label="基金类型">
            <Tag color="blue">{fund.fund_type}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={fund.status === '在售' ? 'green' : 'red'}>{fund.status}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="管理公司">{fund.manager || '-'}</Descriptions.Item>
          <Descriptions.Item label="基金规模">{fund.scale ? `${fund.scale.toFixed(2)} 亿` : '-'}</Descriptions.Item>
          <Descriptions.Item label="基金经理">{fund.fund_manager || '-'}</Descriptions.Item>
          <Descriptions.Item label="托管银行">{fund.custodian || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 净值走势 */}
      <Card 
        title={
          <Space>
            <span>净值走势</span>
            <Select 
              value={days} 
              onChange={setDays}
              style={{ width: 100 }}
              size="small"
            >
              <Option value={7}>近7天</Option>
              <Option value={30}>近30天</Option>
              <Option value={90}>近90天</Option>
              <Option value={180}>近180天</Option>
              <Option value={365}>近1年</Option>
            </Select>
          </Space>
        }
        extra={
          <Space>
            <span>期间涨跌: </span>
            <Tag color={returnRate >= 0 ? 'red' : 'green'}>
              {returnRate}%
            </Tag>
          </Space>
        }
      >
        <Spin spinning={loading}>
          {navData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={navData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorNav" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1890ff" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#1890ff" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="nav_date" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => value.split('/').slice(1).join('/')}
                />
                <YAxis 
                  domain={['auto', 'auto']}
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => value.toFixed(2)}
                />
                <Tooltip 
                  formatter={(value) => [value.toFixed(4), '单位净值']}
                  labelFormatter={(label) => `日期: ${label}`}
                />
                <Area 
                  type="monotone" 
                  dataKey="nav" 
                  stroke="#1890ff" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorNav)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              暂无净值数据
            </div>
          )}
        </Spin>
      </Card>

      {/* 净值明细表 */}
      <Card title="净值明细" style={{ marginTop: 16 }}>
        <Table
          dataSource={navData.slice().reverse().slice(0, 10)}
          columns={[
            { title: '日期', dataIndex: 'nav_date', key: 'nav_date' },
            { 
              title: '单位净值', 
              dataIndex: 'nav', 
              key: 'nav',
              render: (val) => val.toFixed(4)
            },
            { 
              title: '累计净值', 
              dataIndex: 'accumulated_nav', 
              key: 'accumulated_nav',
              render: (val) => val ? val.toFixed(4) : '-'
            },
            { 
              title: '日增长率', 
              dataIndex: 'daily_growth', 
              key: 'daily_growth',
              render: (val) => (
                <span style={{ color: val >= 0 ? '#ff4d4f' : '#52c41a' }}>
                  {val ? `${val.toFixed(2)}%` : '-'}
                </span>
              )
            },
          ]}
          rowKey={(record) => record.id}
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
}

// ============ 主应用组件 ============
function App() {
  const [selectedMenu, setSelectedMenu] = useState('funds');
  const [currentView, setCurrentView] = useState('list');
  const [selectedFund, setSelectedFund] = useState(null);

  const handleViewDetail = (fund) => {
    setSelectedFund(fund);
    setCurrentView('detail');
  };

  const handleBack = () => {
    setCurrentView('list');
    setSelectedFund(null);
  };

  const renderContent = () => {
    if (currentView === 'detail') {
      return <FundDetail fund={selectedFund} onBack={handleBack} />;
    }
    return <FundList onViewDetail={handleViewDetail} />;
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 20px' }}>
        <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
          <FireOutlined style={{ marginRight: '10px' }} />
          公募基金筛选与策略回测系统
        </div>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[selectedMenu]}
            onClick={(e) => {
              setSelectedMenu(e.key);
              if (e.key === 'funds') {
                handleBack();
              }
            }}
            style={{ height: '100%', borderRight: 0 }}
            items={[
              {
                key: 'funds',
                icon: <FundOutlined />,
                label: '基金列表',
              },
              {
                key: 'filter',
                icon: <SearchOutlined />,
                label: '基金筛选',
              },
              {
                key: 'backtest',
                icon: <BarChartOutlined />,
                label: '策略回测',
              },
            ]}
          />
        </Sider>
        <Layout style={{ padding: '20px' }}>
          <Content style={{ background: '#fff', padding: 20, margin: 0, minHeight: 280 }}>
            <Breadcrumb style={{ marginBottom: 16 }}>
              <Breadcrumb.Item>
                <HomeOutlined /> 首页
              </Breadcrumb.Item>
              <Breadcrumb.Item>
                {currentView === 'detail' ? '基金详情' : '基金列表'}
              </Breadcrumb.Item>
            </Breadcrumb>
            {renderContent()}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}

export default App;