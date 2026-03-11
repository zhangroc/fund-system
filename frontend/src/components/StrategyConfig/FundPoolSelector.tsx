import React, { useState, useEffect, useMemo } from 'react';
import {
  Transfer,
  Spin,
  Tag,
  Empty,
  Input,
  Space,
  Card,
  Badge,
  Typography,
  Button,
} from 'antd';
import { SearchOutlined, SwapOutlined, FundOutlined } from '@ant-design/icons';
import axios from 'axios';
import type { Fund } from '../../types';

const { Text } = Typography;

interface FundPoolSelectorProps {
  value?: string[];
  onChange?: (values: string[]) => void;
  maxCount?: number;
  minCount?: number;
}

const FundPoolSelector: React.FC<FundPoolSelectorProps> = ({
  value = [],
  onChange,
  maxCount = 10,
  minCount = 1,
}) => {
  const [loading, setLoading] = useState(false);
  const [funds, setFunds] = useState<Fund[]>([]);
  const [targetKeys, setTargetKeys] = useState<string[]>(value);
  const [searchText, setSearchText] = useState('');
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);

  useEffect(() => {
    fetchFunds();
  }, []);

  useEffect(() => {
    setTargetKeys(value);
  }, [value]);

  const fetchFunds = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/funds`, {
        params: { page: 1, page_size: 500 },
      });
      setFunds(response.data.data || []);
    } catch (error) {
      console.error('获取基金列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 过滤基金
  const filteredFunds = useMemo(() => {
    if (!searchText) return funds;
    const lower = searchText.toLowerCase();
    return funds.filter(
      (f) =>
        f.fund_code.toLowerCase().includes(lower) ||
        f.fund_name.toLowerCase().includes(lower)
    );
  }, [funds, searchText]);

  // 左侧数据源（可选基金）
  const leftDataSource = useMemo(() => {
    return filteredFunds
      .filter((f) => !targetKeys.includes(f.fund_code))
      .map((fund) => ({
        key: fund.fund_code,
        fund_code: fund.fund_code,
        fund_name: fund.fund_name,
        fund_type: fund.fund_type,
        manager: fund.manager,
        scale: fund.scale,
      }));
  }, [filteredFunds, targetKeys]);

  // 右侧数据源（已选基金）
  const rightDataSource = useMemo(() => {
    return funds
      .filter((f) => targetKeys.includes(f.fund_code))
      .map((fund) => ({
        key: fund.fund_code,
        fund_code: fund.fund_code,
        fund_name: fund.fund_name,
        fund_type: fund.fund_type,
        manager: fund.manager,
        scale: fund.scale,
      }));
  }, [funds, targetKeys]);

  const handleChange = (newTargetKeys: string[]) => {
    if (newTargetKeys.length > maxCount) {
      return;
    }
    setTargetKeys(newTargetKeys);
    onChange?.(newTargetKeys);
  };

  const handleSearch = (direction: 'left' | 'right', value: string) => {
    setSearchText(value);
  };

  // 渲染每条记录
  const renderItem = (item: any) => {
    const fund = funds.find((f) => f.fund_code === item.key);
    const typeColor: Record<string, string> = {
      股票型: 'red',
      混合型: 'orange',
      债券型: 'green',
      指数型: 'blue',
      货币型: 'gold',
      QDII: 'purple',
    };

    return {
      label: (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0' }}>
          <div>
            <Text strong style={{ marginRight: 8 }}>{item.fund_name}</Text>
            <Tag color={typeColor[item.fund_type] || 'default'} style={{ marginRight: 8 }}>
              {item.fund_type}
            </Tag>
            {item.manager && (
              <Text type="secondary" style={{ fontSize: 12 }}>{item.manager}</Text>
            )}
          </div>
          <div>
            <Text code>{item.fund_code}</Text>
            {item.scale && (
              <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
                {item.scale.toFixed(2)}亿
              </Text>
            )}
          </div>
        </div>
      ),
      value: item.key,
    };
  };

  const renderSelectedItem = (item: any) => {
    const typeColor: Record<string, string> = {
      股票型: 'red',
      混合型: 'orange',
      债券型: 'green',
      指数型: 'blue',
      货币型: 'gold',
      QDII: 'purple',
    };

    return {
      label: (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Text strong>{item.fund_name}</Text>
            <Tag color={typeColor[item.fund_type] || 'default'}>{item.fund_type}</Tag>
            <Text code>{item.fund_code}</Text>
          </Space>
          {item.scale && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {item.scale.toFixed(2)}亿
            </Text>
          )}
        </div>
      ),
      value: item.key,
    };
  };

  const isDisabled = targetKeys.length >= maxCount;

  return (
    <Card
      size="small"
      title={
        <Space>
          <FundOutlined />
          <span>基金池选择</span>
          <Badge 
            count={`${targetKeys.length}/${maxCount}`} 
            style={{ 
              backgroundColor: targetKeys.length >= maxCount ? '#ff4d4f' : '#1890ff',
              boxShadow: 'none'
            }} 
          />
        </Space>
      }
      extra={
        <Space>
          {targetKeys.length < minCount && (
            <Text type="warning" style={{ fontSize: 12 }}>
              至少选择{minCount}只基金
            </Text>
          )}
        </Space>
      }
    >
      <Spin spinning={loading}>
        <Input
          placeholder="搜索基金代码或名称..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ marginBottom: 16 }}
          allowClear
        />
        
        <Transfer
          dataSource={[
            ...leftDataSource.map(renderItem),
            ...rightDataSource.map(renderSelectedItem),
          ]}
          titles={[
            <span key="left">
              可选基金 <Badge count={leftDataSource.length} showZero style={{ backgroundColor: '#f0f0f0', color: '#666', boxShadow: 'none' }} />
            </span>,
            <span key="right">
              已选基金 <Badge count={targetKeys.length} showZero style={{ backgroundColor: '#1890ff', boxShadow: 'none' }} />
            </span>,
          ]}
          targetKeys={targetKeys}
          selectedKeys={selectedKeys}
          onChange={handleChange}
          onSelectChange={(sourceSelectedKeys, targetSelectedKeys) => {
            setSelectedKeys([...sourceSelectedKeys, ...targetSelectedKeys]);
          }}
          onSearch={handleSearch}
          render={renderItem}
          disabled={isDisabled}
          listStyle={{
            width: 300,
            height: 400,
          }}
          showSearch
          filterOption={(inputValue, item) => 
            item.fund_name.includes(inputValue) || item.fund_code.includes(inputValue)
          }
          operations={['添加', '移除']}
          operationBottom={<div style={{ textAlign: 'center', padding: '8px 0' }}>可拖拽调整</div>}
        />

        {targetKeys.length === 0 && (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="请从左侧选择基金"
            style={{ marginTop: 16 }}
          />
        )}
      </Spin>
    </Card>
  );
};

export default FundPoolSelector;