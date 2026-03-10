import React, { useState, useEffect } from 'react';
import { Layout, Menu, Table, Card, Row, Col, Statistic, Select, Input, Button, Space, Tag, Spin, message, Breadcrumb, Descriptions, Divider, Modal, Form, DatePicker, InputNumber } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { FundOutlined, SearchOutlined, BarChartOutlined, SyncOutlined, FireOutlined, HomeOutlined, ArrowLeftOutlined, PlusOutlined, DeleteOutlined, PlayCircleOutlined, EditOutlined, PortfolioOutlined } from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';

const { Header, Content, Sider } = Layout;
const { Option } = Select;
const { TextArea } = Input;

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
  });

  useEffect(() => {
    fetchFunds();
    fetchStats();
  }, [pagination]);

  useEffect(() => {
    fetchFunds();
  }, [filters]);

  const fetchFunds = async () => {
    setLoading(true);
    try {
      const params = { page: pagination.current, page_size: pagination.pageSize };
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

  const columns = [
    { title: '基金代码', dataIndex: 'fund_code', key: 'fund_code', width: 100 },
    { title: '基金名称', dataIndex: 'fund_name', key: 'fund_name', ellipsis: true,
      render: (text, record) => <a onClick={() => onViewDetail(record)} style={{ fontWeight: 500 }}>{text}</a>
    },
    { title: '类型', dataIndex: 'fund_type', key: 'fund_type', width: 100,
      render: (type) => {
        const colorMap = { '股票型': 'red', '混合型': 'orange', '债券型': 'green', '指数型': 'blue', '货币型': 'gold', 'QDII': 'purple' };
        return <Tag color={colorMap[type] || 'default'}>{type}</Tag>;
      }
    },
    { title: '管理公司', dataIndex: 'manager', key: 'manager', ellipsis: true },
    { title: '规模(亿)', dataIndex: 'scale', key: 'scale', width: 100, render: (s) => s ? s.toFixed(2) : '-' },
    { title: '状态', dataIndex: 'status', key: 'status', width: 80, render: (s) => <Tag color={s === '在售' ? 'green' : 'red'}>{s}</Tag> },
    { title: '操作', key: 'action', width: 80, render: (_, r) => <Button type="link" size="small" onClick={() => onViewDetail(r)}>详情</Button> }
  ];

  return (
    <>
      {stats && (
        <Row gutter={16} style={{ marginBottom: '20px' }}>
          <Col span={6}><Card><Statistic title="基金总数" value={stats.total_count} prefix={<FundOutlined />} /></Card></Col>
          <Col span={6}><Card><Statistic title="总规模(亿)" value={stats.total_scale?.toFixed(2) || 0} precision={2} /></Card></Col>
          <Col span={6}><Card><Statistic title="股票型" value={stats.type_stats?.find(t => t.type === '股票型')?.count || 0} /></Card></Col>
          <Col span={6}><Card><Statistic title="混合型" value={stats.type_stats?.find(t => t.type === '混合型')?.count || 0} /></Card></Col>
        </Row>
      )}
      <Card title="筛选条件" size="small" style={{ marginBottom: '16px' }}>
        <Space wrap style={{ width: '100%' }}>
          <div><span style={{ marginRight: 8 }}>类型:</span>
            <Select placeholder="请选择" style={{ width: 120 }} allowClear value={filters.fund_type} onChange={(v) => setFilters(f => ({...f, fund_type: v}))}>
              <Option value="股票型">股票型</Option><Option value="混合型">混合型</Option><Option value="债券型">债券型</Option><Option value="指数型">指数型</Option><Option value="货币型">货币型</Option>
            </Select>
          </div>
          <div><span style={{ marginRight: 8 }}>管理公司:</span>
            <Input placeholder="输入公司名称" style={{ width: 150 }} value={filters.manager} onChange={(e) => setFilters(f => ({...f, manager: e.target.value}))} />
          </div>
          <div><span style={{ marginRight: 8 }}>最小规模:</span>
            <Input type="number" placeholder="亿" style={{ width: 80 }} onChange={(e) => setFilters(f => ({...f, min_scale: e.target.value ? parseFloat(e.target.value) : null}))} />
          </div>
          <div><span style={{ marginRight: 8 }}>最大规模:</span>
            <Input type="number" placeholder="亿" style={{ width: 80 }} onChange={(e) => setFilters(f => ({...f, max_scale: e.target.value ? parseFloat(e.target.value) : null}))} />
          </div>
          <Button type="primary" icon={<SearchOutlined />} onClick={fetchFunds}>查询</Button>
          <Button icon={<SyncOutlined />} onClick={fetchFunds}>刷新</Button>
        </Space>
      </Card>
      <Spin spinning={loading}>
        <Table columns={columns} dataSource={funds} rowKey="id" pagination={{ ...pagination, total, showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }} onChange={(p) => setPagination(p)} size="small" />
      </Spin>
    </>
  );
}

// ============ 基金详情页面组件 ============
function FundDetail({ fund, onBack }) {
  const [navData, setNavData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [days, setDays] = useState(30);

  useEffect(() => { if (fund) fetchNavData(); }, [fund, days]);

  const fetchNavData = async () => {
    if (!fund) return;
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/api/v1/funds/${fund.fund_code}/nav`, { params: { days } });
      const data = (response.data.data || []).reverse().map(item => ({ ...item, nav_date: new Date(item.nav_date).toLocaleDateString('zh-CN') }));
      setNavData(data);
    } catch (error) { message.error('获取净值数据失败'); }
    finally { setLoading(false); }
  };

  if (!fund) return null;

  const latestNav = navData.length > 0 ? navData[navData.length - 1] : null;
  const firstNav = navData.length > 0 ? navData[0] : null;
  const returnRate = firstNav && latestNav ? ((latestNav.nav - firstNav.nav) / firstNav.nav * 100).toFixed(2) : 0;

  return (
    <div>
      <Button type="link" icon={<ArrowLeftOutlined />} onClick={onBack} style={{ padding: 0, marginBottom: 16 }}>返回基金列表</Button>
      <Card title="基金基本信息" style={{ marginBottom: 16 }}>
        <Descriptions column={4} bordered size="small">
          <Descriptions.Item label="基金代码">{fund.fund_code}</Descriptions.Item>
          <Descriptions.Item label="基金名称">{fund.fund_name}</Descriptions.Item>
          <Descriptions.Item label="基金类型"><Tag color="blue">{fund.fund_type}</Tag></Descriptions.Item>
          <Descriptions.Item label="状态"><Tag color={fund.status === '在售' ? 'green' : 'red'}>{fund.status}</Tag></Descriptions.Item>
          <Descriptions.Item label="管理公司">{fund.manager || '-'}</Descriptions.Item>
          <Descriptions.Item label="基金规模">{fund.scale ? `${fund.scale.toFixed(2)} 亿` : '-'}</Descriptions.Item>
          <Descriptions.Item label="基金经理">{fund.fund_manager || '-'}</Descriptions.Item>
          <Descriptions.Item label="托管银行">{fund.custodian || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>
      <Card title={<Space><span>净值走势</span><Select value={days} onChange={setDays} style={{ width: 100 }} size="small">
        <Option value={7}>近7天</Option><Option value={30}>近30天</Option><Option value={90}>近90天</Option><Option value={180}>近180天</Option><Option value={365}>近1年</Option>
      </Select></Space>} extra={<Space><span>期间涨跌: </span><Tag color={returnRate >= 0 ? 'red' : 'green'}>{returnRate}%</Tag></Space>}>
        <Spin spinning={loading}>
          {navData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={navData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs><linearGradient id="colorNav" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#1890ff" stopOpacity={0.3}/><stop offset="95%" stopColor="#1890ff" stopOpacity={0}/></linearGradient></defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="nav_date" tick={{ fontSize: 12 }} tickFormatter={(v) => v.split('/').slice(1).join('/')} />
                <YAxis domain={['auto', 'auto']} tick={{ fontSize: 12 }} tickFormatter={(v) => v.toFixed(2)} />
                <Tooltip formatter={(v) => [v.toFixed(4), '单位净值']} labelFormatter={(l) => `日期: ${l}`} />
                <Area type="monotone" dataKey="nav" stroke="#1890ff" strokeWidth={2} fillOpacity={1} fill="url(#colorNav)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>暂无净值数据</div>}
        </Spin>
      </Card>
    </div>
  );
}

// ============ 策略管理组件 ============
function StrategyManager({ onBacktest }) {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => { fetchStrategies(); }, []);

  const fetchStrategies = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/api/v1/strategies`);
      setStrategies(response.data);
    } catch (error) { message.error('获取策略列表失败'); }
    finally { setLoading(false); }
  };

  const handleCreate = async (values) => {
    try {
      await axios.post(`${API_BASE}/api/v1/strategies`, {
        name: values.name, description: values.description, strategy_type: values.strategy_type,
        parameters: { amount: values.amount, frequency: values.frequency, day: values.day }, fund_codes: values.fund_codes
      });
      message.success('策略创建成功');
      setModalVisible(false);
      form.resetFields();
      fetchStrategies();
    } catch (error) { message.error('创建失败: ' + (error.response?.data?.detail || error.message)); }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API_BASE}/api/v1/strategies/${id}`);
      message.success('删除成功');
      fetchStrategies();
    } catch (error) { message.error('删除失败'); }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '策略名称', dataIndex: 'name', key: 'name' },
    { title: '类型', dataIndex: 'strategy_type', key: 'strategy_type', render: (t) => <Tag color="blue">{t}</Tag> },
    { title: '关联基金', dataIndex: 'fund_codes', key: 'fund_codes' },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
    { title: '操作', key: 'action', width: 180, render: (_, r) => (
      <Space>
        <Button type="primary" size="small" icon={<PlayCircleOutlined />} onClick={() => onBacktest(r)}>回测</Button>
        <Button danger size="small" icon={<DeleteOutlined />} onClick={() => handleDelete(r.id)}>删除</Button>
      </Space>
    )}
  ];

  return (
    <div>
      <Card title="策略管理" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>新建策略</Button>}>
        <Spin spinning={loading}><Table columns={columns} dataSource={strategies} rowKey="id" /></Spin>
      </Card>
      <Modal title="创建策略" open={modalVisible} onCancel={() => setModalVisible(false)} footer={null} width={600}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="策略名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="strategy_type" label="策略类型" rules={[{ required: true }]}>
            <Select><Option value="定投">定投</Option><Option value="一次性买入">一次性买入</Option></Select>
          </Form.Item>
          <Form.Item name="fund_codes" label="基金代码(逗号分隔)" rules={[{ required: true }]}><Input placeholder="如: 000001, 110011" /></Form.Item>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="amount" label="每次投入金额(元)" initialValue={1000}><InputNumber style={{ width: '100%' }} min={100} /></Form.Item></Col>
            <Col span={12}><Form.Item name="frequency" label="频率" initialValue="monthly"><Select><Option value="daily">每日</Option><Option value="weekly">每周</Option><Option value="monthly">每月</Option></Select></Form.Item></Col>
          </Row>
          <Form.Item name="description" label="描述"><TextArea rows={3} /></Form.Item>
          <Form.Item><Button type="primary" htmlType="submit" block>创建</Button></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

// ============ 回测管理组件 ============
function BacktestManager({ selectedStrategy, onBack }) {
  const [backtests, setBacktests] = useState([]);
  const [allStrategies, setAllStrategies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [selectedBacktest, setSelectedBacktest] = useState(null);

  useEffect(() => { fetchBacktests(); fetchStrategies(); }, []);

  const fetchStrategies = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/v1/strategies`);
      setAllStrategies(response.data);
    } catch (error) { console.error(error); }
  };

  const fetchBacktests = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/api/v1/backtests`);
      setBacktests(response.data);
    } catch (error) { message.error('获取回测列表失败'); }
    finally { setLoading(false); }
  };

  const handleCreate = async (values) => {
    try {
      await axios.post(`${API_BASE}/api/v1/backtests`, {
        name: values.name, strategy_id: values.strategy_id,
        start_date: values.start_date.format('YYYY-MM-DD'), end_date: values.end_date.format('YYYY-MM-DD'),
        initial_capital: values.initial_capital
      });
      message.success('回测创建成功');
      setModalVisible(false);
      form.resetFields();
      fetchBacktests();
    } catch (error) { message.error('创建失败: ' + (error.response?.data?.detail || error.message)); }
  };

  const handleRun = async (id) => {
    try {
      message.loading('回测执行中...', 0);
      await axios.post(`${API_BASE}/api/v1/backtests/${id}/run`);
      message.destroy();
      message.success('回测完成');
      fetchBacktests();
    } catch (error) { message.destroy(); message.error('执行失败'); }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 50 },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '策略', dataIndex: 'strategy_name', key: 'strategy_name' },
    { title: '日期', key: 'date', render: (_, r) => `${r.start_date} ~ ${r.end_date}` },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s) => {
      const color = { pending: 'default', running: 'processing', completed: 'success', failed: 'error' };
      return <Tag color={color[s]}>{s}</Tag>;
    }},
    { title: '操作', key: 'action', width: 200, render: (_, r) => (
      <Space>
        {r.status === 'pending' && <Button type="primary" size="small" onClick={() => handleRun(r.id)}>执行</Button>}
        <Button size="small" onClick={() => setSelectedBacktest(r)}>详情</Button>
      </Space>
    )}
  ];

  return (
    <div>
      {selectedStrategy && <Button type="link" icon={<ArrowLeftOutlined />} onClick={onBack} style={{ padding: 0, marginBottom: 16 }}>返回</Button>}
      <Card title="回测记录" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>新建回测</Button>}>
        <Spin spinning={loading}><Table columns={columns} dataSource={backtests} rowKey="id" /></Spin>
      </Card>
      <Modal title={`回测结果 - ${selectedBacktest?.name}`} open={!!selectedBacktest} onCancel={() => setSelectedBacktest(null)} footer={null} width={900}>
        {selectedBacktest?.result && (
          <div>
            <Row gutter={16}>
              <Col span={6}><Statistic title="初始资金" value={selectedBacktest.result.initial_capital} prefix="¥" /></Col>
              <Col span={6}><Statistic title="最终价值" value={selectedBacktest.result.final_value} prefix="¥" /></Col>
              <Col span={6}><Statistic title="总收益" value={selectedBacktest.result.total_return} prefix="¥" valueStyle={{ color: selectedBacktest.result.total_return >= 0 ? '#ff4d4f' : '#52c41a' }} /></Col>
              <Col span={6}><Statistic title="收益率" value={selectedBacktest.result.total_return_pct} suffix="%" valueStyle={{ color: selectedBacktest.result.total_return_pct >= 0 ? '#ff4d4f' : '#52c41a' }} /></Col>
            </Row>
            <Divider>收益曲线</Divider>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={selectedBacktest.result.equity_curve}>
                <defs><linearGradient id="cv" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#1890ff" stopOpacity={0.3}/><stop offset="95%" stopColor="#1890ff" stopOpacity={0}/></linearGradient></defs>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} /><Tooltip />
                <Area type="monotone" dataKey="value" stroke="#1890ff" fillOpacity={1} fill="url(#cv)" name="资产值" />
                <Line type="monotone" dataKey="invested" stroke="#ff4d4f" strokeDasharray="5 5" name="投入" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </Modal>
      <Modal title="创建回测" open={modalVisible} onCancel={() => setModalVisible(false)} footer={null} width={500}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="回测名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="strategy_id" label="选择策略" rules={[{ required: true }]}>
            <Select>{allStrategies.map(s => <Option key={s.id} value={s.id}>{s.name}</Option>)}</Select>
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="start_date" label="开始日期" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={12}><Form.Item name="end_date" label="结束日期" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
          </Row>
          <Form.Item name="initial_capital" label="初始资金(元)" initialValue={100000}><InputNumber style={{ width: '100%' }} min={1000} /></Form.Item>
          <Form.Item><Button type="primary" htmlType="submit" block>创建</Button></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

// ============ 组合管理组件 ============
function PortfolioManager({ onViewDetail }) {
  const [portfolios, setPortfolios] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editPortfolio, setEditPortfolio] = useState(null);
  const [detailPortfolio, setDetailPortfolio] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => { fetchPortfolios(); }, []);

  const fetchPortfolios = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/api/v1/portfolios`);
      setPortfolios(response.data);
    } catch (error) { message.error('获取组合列表失败'); }
    finally { setLoading(false); }
  };

  const handleCreate = async (values) => {
    try {
      const holdings = values.holdings?.filter(h => h.fund_code)?.map(h => ({
        fund_code: h.fund_code,
        fund_name: h.fund_name || '',
        weight: parseFloat(h.weight) / 100
      })) || [];
      
      await axios.post(`${API_BASE}/api/v1/portfolios`, {
        name: values.name,
        description: values.description,
        holdings: holdings,
        total_assets: values.total_assets || 0,
        cash: values.cash || 0,
        status: 'active'
      });
      message.success('组合创建成功');
      setModalVisible(false);
      form.resetFields();
      fetchPortfolios();
    } catch (error) { message.error('创建失败: ' + (error.response?.data?.detail || error.message)); }
  };

  const handleUpdate = async (values) => {
    if (!editPortfolio) return;
    try {
      const holdings = values.holdings?.filter(h => h.fund_code)?.map(h => ({
        fund_code: h.fund_code,
        fund_name: h.fund_name || '',
        weight: parseFloat(h.weight) / 100
      })) || [];
      
      await axios.put(`${API_BASE}/api/v1/portfolios/${editPortfolio.id}`, {
        name: values.name,
        description: values.description,
        holdings: holdings,
        total_assets: values.total_assets,
        cash: values.cash,
        status: values.status
      });
      message.success('组合更新成功');
      setEditPortfolio(null);
      form.resetFields();
      fetchPortfolios();
    } catch (error) { message.error('更新失败: ' + (error.response?.data?.detail || error.message)); }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API_BASE}/api/v1/portfolios/${id}`);
      message.success('删除成功');
      fetchPortfolios();
    } catch (error) { message.error('删除失败: ' + (error.response?.data?.detail || error.message)); }
  };

  const openEdit = (portfolio) => {
    setEditPortfolio(portfolio);
    const holdings = portfolio.holdings?.map(h => ({
      ...h,
      weight: Math.round((h.weight || 0) * 100)
    })) || [];
    form.setFieldsValue({
      ...portfolio,
      holdings
    });
  };

  const renderHoldings = (holdings) => {
    if (!holdings || holdings.length === 0) return '-';
    return (
      <Space direction="vertical" size={0}>
        {holdings.map((h, i) => (
          <Tag key={i} color="blue">{h.fund_code} ({((h.weight || 0) * 100).toFixed(0)}%)</Tag>
        ))}
      </Space>
    );
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '组合名称', dataIndex: 'name', key: 'name', render: (t, r) => <a onClick={() => setDetailPortfolio(r)} style={{ fontWeight: 500 }}>{t}</a> },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true, render: (t) => t || '-' },
    { title: '持仓', key: 'holdings', render: (_, r) => renderHoldings(r.holdings) },
    { title: '总资产(元)', dataIndex: 'total_assets', key: 'total_assets', render: (v) => v ? v.toLocaleString() : '-' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s) => <Tag color={s === 'active' ? 'green' : 'default'}>{s === 'active' ? '活跃' : '已归档'}</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (t) => t ? t.split('T')[0] : '-' },
    { title: '操作', key: 'action', width: 150, render: (_, r) => (
      <Space>
        <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEdit(r)}>编辑</Button>
        <Button type="link" danger size="small" icon={<DeleteOutlined />} onClick={() => handleDelete(r.id)}>删除</Button>
      </Space>
    )}
  ];

  const HoldingFormItems = () => (
    <Form.List name="holdings">
      {(fields, { add, remove }) => (
        <>
          {fields.map(({ key, name, ...restField }) => (
            <Row key={key} gutter={8} align="middle" style={{ marginBottom: 8 }}>
              <Col span={8}>
                <Form.Item {...restField} name={[name, 'fund_code']} style={{ marginBottom: 0 }}>
                  <Input placeholder="基金代码" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item {...restField} name={[name, 'fund_name']} style={{ marginBottom: 0 }}>
                  <Input placeholder="基金名称(可选)" />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item {...restField} name={[name, 'weight']} style={{ marginBottom: 0 }}>
                  <Input placeholder="权重%" type="number" min={0} max={100} addonAfter="%" />
                </Form.Item>
              </Col>
              <Col span={2}>
                <Button type="text" danger icon={<DeleteOutlined />} onClick={() => remove(name)} />
              </Col>
            </Row>
          ))}
          <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>添加持仓</Button>
        </>
      )}
    </Form.List>
  );

  return (
    <div>
      <Card title="组合管理" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditPortfolio(null); form.resetFields(); setModalVisible(true); }}>新建组合</Button>}>
        <Spin spinning={loading}><Table columns={columns} dataSource={portfolios} rowKey="id" /></Spin>
      </Card>
      
      {/* 创建/编辑弹窗 */}
      <Modal 
        title={editPortfolio ? '编辑组合' : '新建组合'} 
        open={modalVisible} 
        onCancel={() => { setModalVisible(false); setEditPortfolio(null); form.resetFields(); }} 
        footer={null} 
        width={700}
      >
        <Form 
          form={form} 
          layout="vertical" 
          onFinish={editPortfolio ? handleUpdate : handleCreate}
          initialValue={{ status: 'active', holdings: [], total_assets: 0, cash: 0 }}
        >
          <Form.Item name="name" label="组合名称" rules={[{ required: true, message: '请输入组合名称' }]}>
            <Input placeholder="如: 我的稳健组合" />
          </Form.Item>
          <Form.Item name="description" label="组合描述">
            <TextArea rows={2} placeholder="简要描述组合的投资目标或策略" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="total_assets" label="总资产(元)">
                <InputNumber style={{ width: '100%' }} min={0} placeholder="0" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="cash" label="现金(元)">
                <InputNumber style={{ width: '100%' }} min={0} placeholder="0" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="holdings" label="持仓明细" tooltip="添加基金代码和权重，权重以百分比计算">
            <HoldingFormItems />
          </Form.Item>
          <Form.Item name="status" label="状态" rules={[{ required: true }]}>
            <Select>
              <Option value="active">活跃</Option>
              <Option value="archived">已归档</Option>
            </Select>
          </Form.Item>
          <Form.Item><Button type="primary" htmlType="submit" block>{editPortfolio ? '保存修改' : '创建组合'}</Button></Form.Item>
        </Form>
      </Modal>

      {/* 详情弹窗 */}
      <Modal 
        title={`组合详情 - ${detailPortfolio?.name}`} 
        open={!!detailPortfolio} 
        onCancel={() => setDetailPortfolio(null)} 
        footer={[
          <Button key="edit" type="primary" icon={<EditOutlined />} onClick={() => { setDetailPortfolio(null); openEdit(detailPortfolio); setModalVisible(true); }}>
            编辑
          </Button>,
          <Button key="close" onClick={() => setDetailPortfolio(null)}>关闭</Button>
        ]}
        width={600}
      >
        {detailPortfolio && (
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="组合名称">{detailPortfolio.name}</Descriptions.Item>
            <Descriptions.Item label="描述">{detailPortfolio.description || '-'}</Descriptions.Item>
            <Descriptions.Item label="总资产">{detailPortfolio.total_assets ? `${detailPortfolio.total_assets.toLocaleString()} 元` : '-'}</Descriptions.Item>
            <Descriptions.Item label="现金">{detailPortfolio.cash ? `${detailPortfolio.cash.toLocaleString()} 元` : '-'}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={detailPortfolio.status === 'active' ? 'green' : 'default'}>
                {detailPortfolio.status === 'active' ? '活跃' : '已归档'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">{detailPortfolio.created_at?.replace('T', ' ').split('.')[0] || '-'}</Descriptions.Item>
            <Descriptions.Item label="更新时间">{detailPortfolio.updated_at?.replace('T', ' ').split('.')[0] || '-'}</Descriptions.Item>
            <Descriptions.Item label="持仓明细">
              {detailPortfolio.holdings && detailPortfolio.holdings.length > 0 ? (
                <Table
                  size="small"
                  dataSource={detailPortfolio.holdings.map((h, i) => ({ key: i, ...h }))}
                  columns={[
                    { title: '基金代码', dataIndex: 'fund_code' },
                    { title: '基金名称', dataIndex: 'fund_name' },
                    { title: '权重', dataIndex: 'weight', render: (w) => `${((w || 0) * 100).toFixed(0)}%` }
                  ]}
                  pagination={false}
                />
              ) : '无持仓'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
}

// ============ 主应用组件 ============
function App() {
  const [selectedMenu, setSelectedMenu] = useState('funds');
  const [currentView, setCurrentView] = useState('list');
  const [selectedFund, setSelectedFund] = useState(null);
  const [selectedStrategy, setSelectedStrategy] = useState(null);

  const handleViewDetail = (fund) => { setSelectedFund(fund); setCurrentView('detail'); };
  const handleBack = () => { setCurrentView('list'); setSelectedFund(null); setSelectedStrategy(null); };
  const handleBacktest = (strategy) => { setSelectedStrategy(strategy); setCurrentView('backtest'); };

  const renderContent = () => {
    if (currentView === 'detail') return <FundDetail fund={selectedFund} onBack={handleBack} />;
    if (currentView === 'backtest') return <BacktestManager selectedStrategy={selectedStrategy} onBack={handleBack} />;
    if (currentView === 'strategy') return <StrategyManager onBacktest={handleBacktest} />;
    if (currentView === 'portfolio') return <PortfolioManager />;
    return <FundList onViewDetail={handleViewDetail} />;
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 20px' }}>
        <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}><FireOutlined style={{ marginRight: '10px' }} />公募基金筛选与策略回测系统</div>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu mode="inline" selectedKeys={[selectedMenu]} onClick={(e) => {
            setSelectedMenu(e.key);
            if (e.key === 'funds') handleBack();
            else if (e.key === 'strategy') setCurrentView('strategy');
            else if (e.key === 'backtest') { setCurrentView('backtest'); setSelectedStrategy(null); }
            else if (e.key === 'portfolio') setCurrentView('portfolio');
          }} style={{ height: '100%', borderRight: 0 }} items={[
            { key: 'funds', icon: <FundOutlined />, label: '基金列表' },
            { key: 'portfolio', icon: <PortfolioOutlined />, label: '组合管理' },
            { key: 'strategy', icon: <BarChartOutlined />, label: '策略管理' },
            { key: 'backtest', icon: <SyncOutlined />, label: '回测记录' },
          ]} />
        </Sider>
        <Layout style={{ padding: '20px' }}>
          <Content style={{ background: '#fff', padding: 20, margin: 0, minHeight: 280 }}>{renderContent()}</Content>
        </Layout>
      </Layout>
    </Layout>
  );
}

export default App;