import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  InputNumber,
  DatePicker,
  Button,
  Space,
  Tabs,
  Row,
  Col,
  Collapse,
  Tag,
  Divider,
  message,
  Spin,
  AutoComplete,
  Checkbox,
  Badge,
  Alert,
} from 'antd';
import {
  SettingOutlined,
  RocketOutlined,
  LineChartOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  SearchOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  FundOutlined,
} from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import axios from 'axios';
import type { StrategyType, Fund } from '../../types';

const { TextArea } = Input;
const { Option } = Select;
const API_BASE = process.env.REACT_APP_API_URL || `${window.location.protocol}//${window.location.hostname}:8000`;

// 策略类型配置
const STRATEGY_TYPES = [
  {
    type: 'DCA' as StrategyType,
    name: '定投策略',
    icon: <ClockCircleOutlined />,
    color: 'blue',
    description: '定期定额投资，平滑市场波动',
  },
  {
    type: 'BATCH_BUILD' as StrategyType,
    name: '分批建仓策略',
    icon: <SettingOutlined />,
    color: 'green',
    description: '分批次买入，降低择时风险',
  },
  {
    type: 'VALUE' as StrategyType,
    name: '价值策略',
    icon: <LineChartOutlined />,
    color: 'orange',
    description: '基于估值指标，选择低估基金',
  },
  {
    type: 'MOMENTUM' as StrategyType,
    name: '动量策略',
    icon: <ThunderboltOutlined />,
    color: 'red',
    description: '追随强势基金，趋势投资',
  },
];

// 参数预设模板
const PARAM_PRESETS = {
  conservative: {
    name: '稳健型',
    description: '低风险，适合保守投资者',
    params: {
      DCA: { frequency: 'monthly', amount: 1000 },
      BATCH_BUILD: { batchCount: 5, batchInterval: 30 },
      VALUE: { rebalanceThreshold: 10, rebalancePeriod: 90 },
      MOMENTUM: { lookbackPeriod: 60, momentumThreshold: 5, holdingPeriod: 30, topN: 3 },
    },
  },
  balanced: {
    name: '平衡型',
    description: '中等风险，追求稳健收益',
    params: {
      DCA: { frequency: 'weekly', amount: 2000 },
      BATCH_BUILD: { batchCount: 8, batchInterval: 14 },
      VALUE: { rebalanceThreshold: 15, rebalancePeriod: 60 },
      MOMENTUM: { lookbackPeriod: 90, momentumThreshold: 8, holdingPeriod: 21, topN: 5 },
    },
  },
  aggressive: {
    name: '激进型',
    description: '高风险，追求高收益',
    params: {
      DCA: { frequency: 'daily', amount: 5000 },
      BATCH_BUILD: { batchCount: 12, batchInterval: 7 },
      VALUE: { rebalanceThreshold: 20, rebalancePeriod: 30 },
      MOMENTUM: { lookbackPeriod: 120, momentumThreshold: 15, holdingPeriod: 14, topN: 8 },
    },
  },
};

interface StrategyConfigFormProps {
  initialValues?: any;
  onSubmit: (values: any) => void;
  onCancel?: () => void;
  loading?: boolean;
}

const StrategyConfigForm: React.FC<StrategyConfigFormProps> = ({
  initialValues,
  onSubmit,
  onCancel,
  loading = false,
}) => {
  const [form] = Form.useForm();
  const [strategyType, setStrategyType] = useState<StrategyType>('DCA');
  const [funds, setFunds] = useState<Fund[]>([]);
  const [selectedFunds, setSelectedFunds] = useState<string[]>([]);
  const [fundSearchLoading, setFundSearchLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<Fund[]>([]);
  const [activeKey, setActiveKey] = useState<string[]>(['basic', 'funds']);

  useEffect(() => {
    fetchFunds();
  }, []);

  useEffect(() => {
    if (initialValues) {
      form.setFieldsValue(initialValues);
      setStrategyType(initialValues.strategyType || 'DCA');
      setSelectedFunds(initialValues.fundCodes || []);
    }
  }, [initialValues, form]);

  const fetchFunds = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/v1/funds`, { params: { page: 1, page_size: 100 } });
      setFunds(response.data.data || []);
    } catch (error) {
      console.error('获取基金列表失败:', error);
    }
  };

  const searchFunds = async (keyword: string) => {
    if (!keyword || keyword.length < 2) {
      setSearchResults([]);
      return;
    }
    setFundSearchLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/api/v1/funds`, {
        params: { page: 1, page_size: 20, fund_code: keyword, fund_name: keyword },
      });
      setSearchResults(response.data.data || []);
    } catch (error) {
      console.error('搜索基金失败:', error);
    } finally {
      setFundSearchLoading(false);
    }
  };

  const handleFundSelect = (fund: Fund) => {
    if (!selectedFunds.includes(fund.fund_code)) {
      setSelectedFunds([...selectedFunds, fund.fund_code]);
    }
    setSearchResults([]);
  };

  const handleFundRemove = (code: string) => {
    setSelectedFunds(selectedFunds.filter((f) => f !== code));
  };

  const applyPreset = (presetKey: string) => {
    const preset = PARAM_PRESETS[presetKey];
    if (!preset) return;

    const currentParams = preset.params[strategyType];
    if (currentParams) {
      form.setFieldsValue(currentParams);
      message.success(`已应用「${preset.name}」预设参数`);
    }
  };

  // 参数校验规则
  const validateParams = (_: any, value: any) => {
    if (!value) {
      return Promise.reject('请输入参数值');
    }
    return Promise.resolve();
  };

  // 日期范围校验
  const validateDateRange = (_: any, value: Dayjs) => {
    const startDate = form.getFieldValue('startDate');
    if (startDate && value && value.isBefore(startDate)) {
      return Promise.reject('结束日期不能早于开始日期');
    }
    return Promise.resolve();
  };

  // 金额校验
  const validateAmount = (_: any, value: number) => {
    if (value && value < 100) {
      return Promise.reject('最小投资金额为100元');
    }
    return Promise.resolve();
  };

  // 渲染策略选择标签页
  const renderStrategyTabs = () => (
    <Tabs
      activeKey={strategyType}
      onChange={(key) => setStrategyType(key as StrategyType)}
      type="card"
      size="large"
    >
      {STRATEGY_TYPES.map((st) => (
        <Tabs.TabPane
          key={st.type}
          tab={
            <Space>
              {st.icon}
              <span>{st.name}</span>
            </Space>
          }
        >
          <Alert
            message={st.description}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        </Tabs.TabPane>
      ))}
    </Tabs>
  );

  // 渲染定投策略参数
  const renderDCAParams = () => (
    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          name="amount"
          label="每次投入金额(元)"
          rules={[{ required: true, validator: validateAmount }]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={100}
            step={100}
            placeholder="如: 1000"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            parser={(value) => value?.replace(/\$\s?|(,*)/g, '') as any}
          />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          name="frequency"
          label="投资频率"
          rules={[{ required: true }]}
          initialValue="monthly"
        >
          <Select placeholder="选择投资频率">
            <Option value="daily">每日</Option>
            <Option value="weekly">每周</Option>
            <Option value="monthly">每月</Option>
          </Select>
        </Form.Item>
      </Col>
      {form.getFieldValue('frequency') === 'weekly' && (
        <Col span={12}>
          <Form.Item name="dayOfWeek" label="每周几买入" rules={[{ required: true }]}>
            <Select placeholder="选择星期几">
              <Option value={1}>周一</Option>
              <Option value={2}>周二</Option>
              <Option value={3}>周三</Option>
              <Option value={4}>周四</Option>
              <Option value={5}>周五</Option>
            </Select>
          </Form.Item>
        </Col>
      )}
      {form.getFieldValue('frequency') === 'monthly' && (
        <Col span={12}>
          <Form.Item name="dayOfMonth" label="每月几号买入" rules={[{ required: true }]}>
            <InputNumber min={1} max={28} style={{ width: '100%' }} placeholder="1-28" />
          </Form.Item>
        </Col>
      )}
      <Col span={12}>
        <Form.Item
          name="initialCapital"
          label="初始资金(元)"
          tooltip="用于首次买入的起始资金"
        >
          <InputNumber
            style={{ width: '100%' }}
            min={0}
            placeholder="如: 10000"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            parser={(value) => value?.replace(/\$\s?|(,*)/g, '') as any}
          />
        </Form.Item>
      </Col>
    </Row>
  );

  // 渲染分批建仓策略参数
  const renderBatchBuildParams = () => (
    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          name="totalAmount"
          label="总投入金额(元)"
          rules={[{ required: true, validator: validateAmount }]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={1000}
            step={1000}
            placeholder="如: 100000"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            parser={(value) => value?.replace(/\$\s?|(,*)/g, '') as any}
          />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          name="batchCount"
          label="分批次数"
          rules={[{ required: true }]}
          tooltip="将总金额分成多少批买入"
        >
          <InputNumber min={2} max={20} style={{ width: '100%' }} placeholder="如: 5" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          name="batchInterval"
          label="每批间隔天数"
          rules={[{ required: true }]}
          tooltip="每批买入之间的间隔天数"
        >
          <InputNumber min={1} max={90} style={{ width: '100%' }} placeholder="如: 30" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item name="batchStrategy" label="分批策略" initialValue="equal">
          <Select placeholder="选择分批策略">
            <Option value="equal">等额分批</Option>
            <Option value="pyramid">金字塔买入(越跌越多)</Option>
            <Option value="inverted_pyramid">倒金字塔(越跌越少)</Option>
          </Select>
        </Form.Item>
      </Col>
    </Row>
  );

  // 渲染价值策略参数
  const renderValueParams = () => (
    <Row gutter={16}>
      <Col span={12}>
        <Form.Item name="minP/E" label="最低市盈率(P/E)">
          <InputNumber min={0} max={100} step={0.5} style={{ width: '100%' }} placeholder="如: 10" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item name="maxP/E" label="最高市盈率(P/E)">
          <InputNumber min={0} max={100} step={0.5} style={{ width: '100%' }} placeholder="如: 30" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item name="minP/B" label="最低市净率(P/B)">
          <InputNumber min={0} max={20} step={0.1} style={{ width: '100%' }} placeholder="如: 1" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item name="maxP/B" label="最高市净率(P/B)">
          <InputNumber min={0} max={20} step={0.1} style={{ width: '100%' }} placeholder="如: 5" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          name="rebalanceThreshold"
          label="再平衡阈值(%)"
          initialValue={10}
          tooltip="持仓偏离目标权重多少时触发再平衡"
        >
          <InputNumber min={1} max={50} style={{ width: '100%' }} />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          name="rebalancePeriod"
          label="再平衡周期(天)"
          initialValue={90}
          tooltip="定期检查是否需要再平衡的周期"
        >
          <InputNumber min={30} max={365} step={30} style={{ width: '100%' }} />
        </Form.Item>
      </Col>
    </Row>
  );

  // 渲染动量策略参数
  const renderMomentumParams = () => (
    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          name="lookbackPeriod"
          label="回看周期(天)"
          rules={[{ required: true }]}
          tooltip="计算动量时回看多少天的涨幅"
        >
          <InputNumber min={20} max={365} style={{ width: '100%' }} placeholder="如: 90" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          name="momentumThreshold"
          label="动量阈值(%)"
          initialValue={5}
          tooltip="超过这个涨幅才认为是强势基金"
        >
          <InputNumber min={0} max={50} step={1} style={{ width: '100%' }} />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          name="holdingPeriod"
          label="持有周期(天)"
          rules={[{ required: true }]}
          tooltip="持有多少天后重新调仓"
        >
          <InputNumber min={7} max={180} style={{ width: '100%' }} placeholder="如: 30" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          name="topN"
          label="持仓前N只"
          initialValue={5}
          tooltip="选择动量最强的前几只基金"
        >
          <InputNumber min={1} max={10} style={{ width: '100%' }} />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item name="momentumType" label="动量类型" initialValue="price">
          <Select placeholder="选择动量计算方式">
            <Option value="price">价格动量</Option>
            <Option value="risk_adjusted">风险调整动量</Option>
          </Select>
        </Form.Item>
      </Col>
    </Row>
  );

  // 渲染策略参数
  const renderStrategyParams = () => {
    switch (strategyType) {
      case 'DCA':
        return renderDCAParams();
      case 'BATCH_BUILD':
        return renderBatchBuildParams();
      case 'VALUE':
        return renderValueParams();
      case 'MOMENTUM':
        return renderMomentumParams();
      default:
        return null;
    }
  };

  // 渲染基金选择区域
  const renderFundSelector = () => (
    <Card
      size="small"
      title={
        <Space>
          <FundOutlined />
          <span>基金池选择</span>
          <Badge count={selectedFunds.length} showZero style={{ backgroundColor: '#1890ff' }} />
        </Space>
      }
      style={{ marginTop: 16 }}
    >
      <AutoComplete
        style={{ width: '100%', marginBottom: 16 }}
        placeholder="搜索基金代码或名称..."
        onSearch={searchFunds}
        options={searchResults.map((f) => ({
          value: f.fund_code,
          label: (
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>{f.fund_name}</span>
              <Tag color="blue">{f.fund_code}</Tag>
            </div>
          ),
        }))}
        onSelect={(value) => {
          const fund = searchResults.find((f) => f.fund_code === value);
          if (fund) handleFundSelect(fund);
        }}
        notFoundContent={fundSearchLoading ? <Spin size="small" /> : '未找到相关基金'}
      />

      {selectedFunds.length > 0 ? (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {selectedFunds.map((code) => {
            const fund = funds.find((f) => f.fund_code === code);
            return (
              <Tag
                key={code}
                closable
                onClose={() => handleFundRemove(code)}
                color="blue"
                style={{ padding: '4px 8px' }}
              >
                {fund?.fund_name || code}
              </Tag>
            );
          })}
        </div>
      ) : (
        <div style={{ textAlign: 'center', color: '#999', padding: 20 }}>
          <ExclamationCircleOutlined style={{ marginRight: 8 }} />
          请从上方搜索并选择基金
        </div>
      )}

      {selectedFunds.length > 0 && (
        <>
          <Divider style={{ margin: '12px 0' }} />
          <div style={{ fontSize: 12, color: '#666' }}>
            <Checkbox.Group
              value={selectedFunds}
              onChange={(values) => setSelectedFunds(values as string[])}
            >
              <Row gutter={[8, 8]}>
                {selectedFunds.slice(0, 6).map((code) => {
                  const fund = funds.find((f) => f.fund_code === code);
                  return (
                    <Col span={8} key={code}>
                      <Checkbox value={code}>
                        <Space direction="vertical" size={0}>
                          <span style={{ fontWeight: 500 }}>{fund?.fund_name || code}</span>
                          <span style={{ fontSize: 12, color: '#999' }}>{fund?.fund_type}</span>
                        </Space>
                      </Checkbox>
                    </Col>
                  );
                })}
              </Row>
            </Checkbox.Group>
          </div>
        </>
      )}
    </Card>
  );

  // 渲染高级选项
  const renderAdvancedOptions = () => (
    <Collapse
      ghost
      activeKey={activeKey}
      onChange={(key) => setActiveKey(key as string[])}
      style={{ marginTop: 16 }}
    >
      <Collapse.Panel header="高级选项" key="advanced">
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="maxPosition" label="单只基金最大仓位(%)">
              <InputNumber min={5} max={100} style={{ width: '100%' }} defaultValue={30} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="minPosition" label="单只基金最小仓位(%)">
              <InputNumber min={0} max={50} style={{ width: '100%' }} defaultValue={5} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="commission" label="交易佣金(%)">
              <InputNumber
                min={0}
                max={1}
                step={0.0001}
                style={{ width: '100%' }}
                defaultValue={0.001}
                precision={4}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="slippage" label="滑点(%)">
              <InputNumber
                min={0}
                max={1}
                step={0.001}
                style={{ width: '100%' }}
                defaultValue={0.001}
                precision={3}
              />
            </Form.Item>
          </Col>
          <Col span={24}>
            <Form.Item name="rebalanceOnAdd" valuePropName="checked">
              <Checkbox>新资金入账时触发再平衡</Checkbox>
            </Form.Item>
          </Col>
        </Row>
      </Collapse.Panel>
    </Collapse>
  );

  const handleSubmit = async (values: any) => {
    const params = {
      ...values,
      strategyType,
      fundCodes: selectedFunds,
      startDate: values.startDate?.format('YYYY-MM-DD'),
      endDate: values.endDate?.format('YYYY-MM-DD'),
    };
    onSubmit(params);
  };

  return (
    <Spin spinning={loading}>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          strategyType: 'DCA',
          frequency: 'monthly',
          amount: 1000,
          batchCount: 5,
          batchInterval: 30,
          rebalanceThreshold: 10,
          rebalancePeriod: 90,
          lookbackPeriod: 90,
          momentumThreshold: 5,
          holdingPeriod: 30,
          topN: 5,
          maxPosition: 30,
          minPosition: 5,
          commission: 0.001,
          slippage: 0.001,
        }}
      >
        {/* 策略类型选择 */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 16, fontWeight: 500 }}>
            <RocketOutlined style={{ marginRight: 8 }} />
            选择策略类型
          </div>
          {renderStrategyTabs()}
        </Card>

        {/* 参数预设 */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <Space>
            <span>快速预设:</span>
            {Object.entries(PARAM_PRESETS).map(([key, preset]) => (
              <Button
                key={key}
                size="small"
                onClick={() => applyPreset(key)}
              >
                {preset.name}
              </Button>
            ))}
          </Space>
        </Card>

        {/* 基础参数配置 */}
        <Card size="small" title="基础参数" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="策略名称"
                rules={[
                  { required: true, message: '请输入策略名称' },
                  { min: 2, max: 50, message: '名称长度为2-50个字符' },
                ]}
              >
                <Input placeholder="如: 我的稳健定投策略" maxLength={50} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="description" label="策略描述">
                <TextArea
                  rows={1}
                  placeholder="简要描述该策略的投资目标"
                  maxLength={200}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="startDate"
                label="开始日期"
                rules={[{ required: true, message: '请选择开始日期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="endDate"
                label="结束日期"
                rules={[{ validator: validateDateRange }]}
              >
                <DatePicker
                  style={{ width: '100%' }}
                  placeholder="不设置则使用当前日期"
                />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* 策略类型参数 */}
        <Card
          size="small"
          title={
            <Space>
              <CheckCircleOutlined />
              <span>{STRATEGY_TYPES.find((s) => s.type === strategyType)?.name}参数</span>
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          {renderStrategyParams()}
        </Card>

        {/* 基金选择 */}
        {renderFundSelector()}

        {/* 高级选项 */}
        {renderAdvancedOptions()}

        {/* 提交按钮 */}
        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <Space>
            {onCancel && (
              <Button size="large" onClick={onCancel}>
                取消
              </Button>
            )}
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              icon={<SearchOutlined />}
              disabled={selectedFunds.length === 0}
            >
              开始回测
            </Button>
          </Space>
        </div>
      </Form>
    </Spin>
  );
};

export default StrategyConfigForm;