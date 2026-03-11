import React from 'react';
import { Button, Space, Dropdown, Tooltip, message } from 'antd';
import {
  DownloadOutlined,
  FileExcelOutlined,
  FileTextOutlined,
  FilePdfOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import type { Trade, BacktestResult, EquityPoint, MonthlyReturn } from '../../types';
import dayjs from 'dayjs';

interface TradeExportProps {
  trades?: Trade[];
  backtestResult?: BacktestResult;
  onExportCSV?: () => void;
  onExportExcel?: () => void;
  onExportPDF?: () => void;
  loading?: boolean;
  children?: React.ReactNode;
}

// CSV 导出
const exportToCSV = (data: any[], filename: string) => {
  if (!data || data.length === 0) {
    message.warning('没有可导出的数据');
    return;
  }

  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map((row) =>
      headers
        .map((header) => {
          const value = row[header];
          // 处理包含逗号的值
          if (typeof value === 'string' && value.includes(',')) {
            return `"${value}"`;
          }
          return value;
        })
        .join(',')
    ),
  ].join('\n');

  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}_${dayjs().format('YYYYMMDD_HHmmss')}.csv`;
  link.click();
  message.success('CSV导出成功');
};

// Excel 导出（使用HTML table方式，兼容性较好）
const exportToExcel = (
  data: any[],
  filename: string,
  sheetName: string = 'Sheet1'
) => {
  if (!data || data.length === 0) {
    message.warning('没有可导出的数据');
    return;
  }

  const headers = Object.keys(data[0]);
  const htmlContent = `
    <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
    <head>
      <meta charset="UTF-8">
      <style>
        table { border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #1890ff; color: white; }
      </style>
    </head>
    <body>
      <table>
        <thead>
          <tr>${headers.map((h) => `<th>${h}</th>`).join('')}</tr>
        </thead>
        <tbody>
          ${data
            .map(
              (row) =>
                `<tr>${headers
                  .map((h) => `<td>${row[h] ?? ''}</td>`)
                  .join('')}</tr>`
            )
            .join('')}
        </tbody>
      </table>
    </body>
    </html>
  `;

  const blob = new Blob([htmlContent], { type: 'application/vnd.ms-excel' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}_${dayjs().format('YYYYMMDD_HHmmss')}.xls`;
  link.click();
  message.success('Excel导出成功');
};

// 交易记录导出
const exportTrades = (trades: Trade[], format: 'csv' | 'excel') => {
  const data = trades.map((trade) => ({
    日期: trade.date?.split('T')[0] || '',
    操作: trade.action === 'buy' ? '买入' : '卖出',
    基金代码: trade.fund_code,
    基金名称: trade.fund_name,
    价格: trade.price?.toFixed(4),
    份额: trade.shares?.toFixed(2),
    金额: trade.amount?.toFixed(2),
    手续费: trade.commission?.toFixed(2) || '0',
  }));

  if (format === 'csv') {
    exportToCSV(data, '交易记录');
  } else {
    exportToExcel(data, '交易记录');
  }
};

// 收益曲线导出
const exportEquityCurve = (equityCurve: EquityPoint[], format: 'csv' | 'excel') => {
  const data = equityCurve.map((point) => ({
    日期: point.date,
    资产值: point.value?.toFixed(2),
    累计投入: point.invested?.toFixed(2),
    现金: point.cash?.toFixed(2) || '0',
  }));

  if (format === 'csv') {
    exportToCSV(data, '收益曲线');
  } else {
    exportToExcel(data, '收益曲线');
  }
};

// 月度收益导出
const exportMonthlyReturns = (monthlyReturns: MonthlyReturn[], format: 'csv' | 'excel') => {
  const data = monthlyReturns.map((item) => ({
    月份: item.month,
    收益率: `${item.return?.toFixed(2)}%`,
    类型: item.isPositive ? '正收益' : '负收益',
  }));

  if (format === 'csv') {
    exportToCSV(data, '月度收益');
  } else {
    exportToExcel(data, '月度收益');
  }
};

// 完整回测报告导出
const exportFullReport = (result: BacktestResult, format: 'csv' | 'excel') => {
  // 导出交易记录
  if (result.trades && result.trades.length > 0) {
    exportTrades(result.trades, format);
  }

  // 导出收益曲线
  if (result.equity_curve && result.equity_curve.length > 0) {
    exportEquityCurve(result.equity_curve, format);
  }

  // 导出月度收益
  if (result.monthly_returns && result.monthly_returns.length > 0) {
    exportMonthlyReturns(result.monthly_returns, format);
  }

  message.success('报告导出完成');
};

const TradeExport: React.FC<TradeExportProps> = ({
  trades,
  backtestResult,
  children,
}) => {
  const handleExport: MenuProps['onClick'] = ({ key }) => {
    const format = key.includes('csv') ? 'csv' : 'excel';

    if (backtestResult) {
      // 完整报告导出
      exportFullReport(backtestResult, format);
    } else if (trades && trades.length > 0) {
      // 交易记录导出
      exportTrades(trades, format);
    } else {
      message.warning('没有可导出的数据');
    }
  };

  const items: MenuProps['items'] = [
    {
      key: 'csv-trades',
      icon: <FileTextOutlined />,
      label: '导出交易记录 (CSV)',
    },
    {
      key: 'excel-trades',
      icon: <FileExcelOutlined />,
      label: '导出交易记录 (Excel)',
    },
    { type: 'divider' },
    {
      key: 'csv-full',
      icon: <FileTextOutlined />,
      label: '导出完整报告 (CSV)',
      disabled: !backtestResult,
    },
    {
      key: 'excel-full',
      icon: <FileExcelOutlined />,
      label: '导出完整报告 (Excel)',
      disabled: !backtestResult,
    },
  ];

  return (
    <Dropdown menu={{ items, onClick: handleExport }} trigger={['click']}>
      {children || (
        <Tooltip title="导出交易记录">
          <Button icon={<DownloadOutlined />}>导出</Button>
        </Tooltip>
      )}
    </Dropdown>
  );
};

// 独立导出按钮组件
export const ExportButton: React.FC<{
  type: 'trades' | 'equity' | 'monthly' | 'full';
  data: Trade[] | EquityPoint[] | MonthlyReturn[] | BacktestResult;
  format: 'csv' | 'excel';
  children?: React.ReactNode;
}> = ({ type, data, format, children }) => {
  const handleExport = () => {
    switch (type) {
      case 'trades':
        exportTrades(data as Trade[], format);
        break;
      case 'equity':
        exportEquityCurve(data as EquityPoint[], format);
        break;
      case 'monthly':
        exportMonthlyReturns(data as MonthlyReturn[], format);
        break;
      case 'full':
        exportFullReport(data as BacktestResult, format);
        break;
    }
  };

  return (
    <Button icon={<DownloadOutlined />} onClick={handleExport}>
      {children || `导出${format.toUpperCase()}`}
    </Button>
  );
};

export default TradeExport;