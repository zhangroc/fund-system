# 净值历史数据采集任务

## 背景
- 规模≥2亿基金共5,122只
- 当前仅有14只有完整历史数据（≥1000条）
- 需要为剩余5,108只基金补采历史净值

## 执行步骤

### 1. 启动采集（后台运行）
```bash
cd /home/ubuntu/.openclaw/workspace/fund-system
python3 scripts/collect_nav_history.py --delay 0.5 --retry 3
```

### 2. 监控进度
```bash
# 查看日志
tail -f logs/nav_collection_*.log

# 查看覆盖率（可中途运行）
python3 scripts/validate_coverage.py
```

### 3. 验收标准
| 指标 | 目标 |
|------|------|
| 有数据基金比例 | ≥80% |
| 有≥1年数据 | ≥50% |
| 有≥2年数据 | ≥30% |
| 异常率 | <0.1% |

## 注意事项
- 采集约需4-6小时，可随时中断（支持断点续采）
- 如遇API限速，可使用 --delay 参数调大间隔
- 建议晚间执行，避免白天占用带宽

## 完成后
- 运行 `python3 scripts/validate_coverage.py` 确认覆盖率
- 运行 `python3 scripts/validate_reasonableness.py` 确认数据质量
- 如有异常运行 `python3 scripts/clean_nav_data.py` 清洗