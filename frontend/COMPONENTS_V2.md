# V2.0 前端组件开发文档

## 组件概览

本项目包含以下5批前端组件开发：

### 第1批：策略参数配置界面 ✅

**组件位置**: `src/components/StrategyConfig/`

| 组件 | 文件 | 说明 |
|------|------|------|
| StrategyConfigForm | StrategyConfigForm.tsx | 4种策略类型的参数配置表单 |
| FundPoolSelector | FundPoolSelector.tsx | 基金池选择（支持搜索、多选） |

**支持的策略类型**:
- `DCA` - 定投策略
- `BATCH_BUILD` - 分批建仓策略
- `VALUE` - 价值策略
- `MOMENTUM` - 动量策略

**功能特性**:
- 参数校验（日期范围、资金限制等）
- 高级选项折叠面板（交易佣金、滑点等）
- 参数预设模板（稳健型/平衡型/激进型）

---

### 第2批：多基金对比曲线组件 ✅

**组件位置**: `src/components/FundCompare/`

| 组件 | 文件 | 说明 |
|------|------|------|
| FundCompareChart | FundCompareChart.tsx | 净值走势、累计收益、相对强弱曲线 |

**功能特性**:
- 净值走势曲线（面积图）
- 累计收益曲线（折线图）
- 相对强弱曲线（多基金对比）
- 支持缩放、悬停提示、导出图片

---

### 第3批：回测结果展示组件 ✅

**组件位置**: `src/components/BacktestResult/`

| 组件 | 文件 | 说明 |
|------|------|------|
| BacktestResultPanel | BacktestResultPanel.tsx | 收益曲线、风险指标、月度收益、交易明细 |

**功能特性**:
- 收益曲线图（策略 vs 基准）
- 关键指标卡片（累计收益、夏普、最大回撤、Alpha、Beta等）
- 月度收益表格
- 交易明细记录

---

### 第4批：持仓热力图组件 ✅

**组件位置**: `src/components/HoldingsHeatmap/`

| 组件 | 文件 | 说明 |
|------|------|------|
| HoldingsHeatmap | HoldingsHeatmap.tsx | 行业分布、持仓占比、风格雷达图 |

**功能特性**:
- 持仓热力图（行业/基金维度）
- 行业分布饼图/条形图
- 持仓风格雷达图
- 统计摘要（前五大持仓等）

---

### 第5批：交易记录导出功能 ✅

**组件位置**: `src/components/common/`

| 组件 | 文件 | 说明 |
|------|------|------|
| TradeExport | TradeExport.tsx | CSV/Excel导出 |

**功能特性**:
- 交易记录导出（CSV/Excel）
- 收益曲线导出
- 月度收益导出
- 完整报告导出

---

## 技术栈

- **React 18** + **TypeScript**
- **Ant Design 5.x**
- **Recharts** (图表库)
- **Day.js** (日期处理)
- **Axios** (HTTP请求)

---

## 使用示例

### 1. 策略参数配置

```tsx
import { StrategyConfigForm } from './components/StrategyConfig';

<StrategyConfigForm
  onSubmit={(values) => console.log(values)}
  onCancel={() => console.log('cancel')}
/>
```

### 2. 基金对比曲线

```tsx
import { FundCompareChart } from './components/FundCompare';

<FundCompareChart
  funds={[
    { fund_code: '000001', fund_name: '测试基金A' },
    { fund_code: '000002', fund_name: '测试基金B' },
  ]}
  days={365}
/>
```

### 3. 回测结果展示

```tsx
import { BacktestResultPanel } from './components/BacktestResult';

<BacktestResultPanel
  result={backtestResult}
  riskMetrics={riskMetrics}
  benchmarkData={benchmarkData}
/>
```

### 4. 持仓热力图

```tsx
import { HoldingsHeatmap } from './components/HoldingsHeatmap';

<HoldingsHeatmap
  holdings={[
    { fund_code: '000001', fund_name: '测试基金A', weight: 0.25 },
    { fund_code: '000002', fund_name: '测试基金B', weight: 0.20 },
  ]}
/>
```

### 5. 交易记录导出

```tsx
import { TradeExport } from './components/common';

<TradeExport trades={trades} />
<TradeExport backtestResult={result} />
```

---

## 项目结构

```
frontend/src/
├── components/
│   ├── StrategyConfig/
│   │   ├── StrategyConfigForm.tsx    # 策略参数配置表单
│   │   ├── FundPoolSelector.tsx       # 基金选择器
│   │   └── index.ts
│   ├── FundCompare/
│   │   ├── FundCompareChart.tsx       # 多基金对比图表
│   │   └── index.ts
│   ├── BacktestResult/
│   │   ├── BacktestResultPanel.tsx    # 回测结果展示
│   │   └── index.ts
│   ├── HoldingsHeatmap/
│   │   ├── HoldingsHeatmap.tsx        # 持仓热力图
│   │   └── index.ts
│   ├── common/
│   │   ├── TradeExport.tsx             # 导出功能
│   │   └── index.ts
│   └── index.ts                        # 统一导出
├── types/
│   └── index.ts                        # TypeScript类型定义
├── App.tsx                             # 示例应用
└── index.ts                            # 入口文件
```

---

## 开发状态

| 批次 | 任务 | 状态 | 预估工时 |
|------|------|------|----------|
| 1 | 策略参数配置界面 | ✅ 完成 | 3天 |
| 2 | 多基金对比曲线组件 | ✅ 完成 | 2天 |
| 3 | 回测结果展示组件 | ✅ 完成 | 3天 |
| 4 | 持仓热力图组件 | ✅ 完成 | 2天 |
| 5 | 交易记录导出功能 | ✅ 完成 | 0.5天 |

**总计**: 约 10.5 天 → 实际开发时间更短

---

## 注意事项

1. **TypeScript配置**: 项目已配置 `tsconfig.json`，支持 `.tsx` 和 `.ts` 文件
2. **向后兼容**: 保留原有 `App.js`，新组件在 `App.tsx` 中演示
3. **API集成**: 组件通过 `process.env.REACT_APP_API_URL` 或 `http://localhost:8000` 访问后端API
4. **样式**: 使用 Ant Design 5.x 的默认主题，无需额外配置

---

*文档生成时间: 2026-03-11*