#!/usr/bin/env python3
"""
基金数据准确性验证脚本
功能：
1. 验证年化收益计算公式
2. 验证最大回撤计算公式
3. 边界测试
"""

import math
from datetime import datetime, timedelta


def calculate_annual_return(final_value: float, initial_value: float, days: int) -> float:
    """
    计算年化收益率 (CAGR - Compound Annual Growth Rate)
    
    公式: annual_return = (final_value / initial_value) ^ (1/years) - 1
    
    参数:
        final_value: 最终资产价值
        initial_value: 初始投入资金
        days: 持有天数
    返回:
        年化收益率 (%)
    """
    if initial_value <= 0 or days <= 0:
        return 0.0
    
    years = days / 365.0
    if years <= 0:
        return 0.0
    
    # 使用原始公式
    annual_return = (math.pow(final_value / initial_value, 1 / years) - 1) * 100
    return annual_return


def calculate_max_drawdown(daily_values: list) -> float:
    """
    计算最大回撤
    
    公式: max_drawdown = max((peak - value) / peak)
    
    参数:
        daily_values: 每日资产值列表
    返回:
        最大回撤 (%)
    """
    if not daily_values:
        return 0.0
    
    max_value = daily_values[0]
    max_drawdown = 0.0
    
    for value in daily_values:
        if value > max_value:
            max_value = value
        
        if max_value > 0:
            drawdown = (max_value - value) / max_value * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
    
    return max_drawdown


def test_annual_return_formula():
    """测试年化收益率计算"""
    print("\n" + "="*60)
    print("【测试1】年化收益率计算公式验证")
    print("="*60)
    
    test_cases = [
        # (初始投入, 最终价值, 天数, 预期年化收益率, 说明)
        (10000, 11000, 365, 10.0, "一年10%收益"),
        (10000, 11000, 182.5, 21.0, "半年10%收益，年化21%"),
        (10000, 12000, 365, 20.0, "一年20%收益"),
        (10000, 10000, 365, 0.0, "一年不赚不亏"),
        (10000, 8000, 365, -20.0, "一年亏损20%"),
    ]
    
    all_passed = True
    for initial, final, days, expected, desc in test_cases:
        result = calculate_annual_return(final, initial, days)
        passed = abs(result - expected) < 0.01
        status = "✅ 通过" if passed else "❌ 失败"
        
        print(f"\n{desc}")
        print(f"  初始投入: {initial}, 最终价值: {final}, 天数: {days}")
        print(f"  计算结果: {result:.2f}%")
        print(f"  预期结果: {expected:.2f}%")
        print(f"  状态: {status}")
        
        if not passed:
            all_passed = False
    
    # 验证与天天基金网数据的对比
    # 假设基金161039在一年内从2.08涨到2.52（37.96%收益）
    print("\n--- 天天基金网数据对标 ---")
    initial_nav = 2.08
    final_nav = 2.52
    days = 365
    expected_return = 37.96  # 来自网站显示的近1年收益
    
    calculated = calculate_annual_return(final_nav, initial_nav, days)
    diff = abs(calculated - expected_return)
    
    print(f"基金161039近1年收益验证:")
    print(f"  期初净值: {initial_nav}")
    print(f"  期末净值: {final_nav}")
    print(f"  天天基金网显示: {expected_return}%")
    print(f"  计算结果: {calculated:.2f}%")
    print(f"  差异: {diff:.2f}%")
    
    if diff < 0.1:
        print("  状态: ✅ 通过 - 与官网数据一致")
    else:
        print("  状态: ⚠️ 差异较大，需要检查数据源")
        all_passed = False
    
    return all_passed


def test_max_drawdown_formula():
    """测试最大回撤计算"""
    print("\n" + "="*60)
    print("【测试2】最大回撤计算公式验证")
    print("="*60)
    
    test_cases = [
        # (每日资产列表, 预期最大回撤, 说明)
        ([100, 105, 110, 105, 100, 95, 90], 18.18, "先涨后跌，最大回撤约18%"),
        ([100, 110, 120, 130, 140, 150], 0.0, "单边上涨，无回撤"),
        ([100, 90, 80, 70, 60, 50], 50.0, "单边下跌，最大回撤50%"),
        ([100, 95, 90, 85, 80, 75, 80, 85, 90], 25.0, "先跌后涨再跌"),
        ([100], 0.0, "只有一天，无回撤"),
    ]
    
    all_passed = True
    for values, expected, desc in test_cases:
        result = calculate_max_drawdown(values)
        passed = abs(result - expected) < 0.1
        status = "✅ 通过" if passed else "❌ 失败"
        
        print(f"\n{desc}")
        print(f"  每日资产: {values}")
        print(f"  计算结果: {result:.2f}%")
        print(f"  预期结果: {expected:.2f}%")
        print(f"  状态: {status}")
        
        if not passed:
            all_passed = False
    
    return all_passed


def test_boundary_conditions():
    """边界条件测试"""
    print("\n" + "="*60)
    print("【测试3】边界条件测试")
    print("="*60)
    
    all_passed = True
    
    # 年化收益边界测试
    print("\n--- 年化收益边界测试 ---")
    
    # 1. 初始投入为0
    result = calculate_annual_return(10000, 0, 365)
    print(f"初始投入为0: {result} (预期: 0.0)")
    if result != 0.0:
        print("  ❌ 失败")
        all_passed = False
    else:
        print("  ✅ 通过")
    
    # 2. 持有天数为0
    result = calculate_annual_return(11000, 10000, 0)
    print(f"持有天数为0: {result} (预期: 0.0)")
    if result != 0.0:
        print("  ❌ 失败")
        all_passed = False
    else:
        print("  ✅ 通过")
    
    # 3. 负收益
    result = calculate_annual_return(5000, 10000, 365)
    print(f"亏损50%: {result} (预期: -50.0%)")
    if abs(result + 50.0) < 0.1:
        print("  ✅ 通过")
    else:
        print("  ❌ 失败")
        all_passed = False
    
    # 4. 巨大收益
    result = calculate_annual_return(1000000, 10000, 365)  # 100倍
    print(f"收益100倍: {result:.2f}% (预期: ~9900%)")
    if result > 9000:
        print("  ✅ 通过")
    else:
        print("  ❌ 失败")
        all_passed = False
    
    # 5. 极短持有期
    result = calculate_annual_return(10010, 10000, 1)  # 1天
    print(f"持有1天收益10元: {result:.2f}%")
    expected = (10010/10000 - 1) * 100 * 365  # 年化
    if abs(result - expected) < 0.1:
        print("  ✅ 通过")
    else:
        print("  ❌ 失败")
        all_passed = False
    
    # 最大回撤边界测试
    print("\n--- 最大回撤边界测试 ---")
    
    # 1. 空列表
    result = calculate_max_drawdown([])
    print(f"空列表: {result} (预期: 0.0)")
    if result == 0.0:
        print("  ✅ 通过")
    else:
        print("  ❌ 失败")
        all_passed = False
    
    # 2. 单个值
    result = calculate_max_drawdown([100])
    print(f"单个值: {result} (预期: 0.0)")
    if result == 0.0:
        print("  ✅ 通过")
    else:
        print("  ❌ 失败")
        all_passed = False
    
    # 3. 全部相同值
    result = calculate_max_drawdown([100, 100, 100, 100])
    print(f"全部相同值: {result} (预期: 0.0)")
    if result == 0.0:
        print("  ✅ 通过")
    else:
        print("  ❌ 失败")
        all_passed = False
    
    # 4. 负值处理
    result = calculate_max_drawdown([100, -50, -100])
    print(f"包含负值: {result}% (预期: 超过100%)")
    if result > 100:
        print("  ✅ 通过 (超过100%回撤)")
    else:
        print("  ❌ 失败")
        all_passed = False
    
    return all_passed


def verify_formula_with_code():
    """与代码中的公式进行对比验证"""
    print("\n" + "="*60)
    print("【测试4】与代码实现对比")
    print("="*60)
    
    # 模拟 backtest_engine.py 中的计算逻辑
    def code_annual_return(final_value, total_invested, days):
        """代码中的年化收益计算"""
        years = days / 365 if days > 0 else 1
        return ((math.pow(final_value / total_invested, 1/years) - 1) * 100 
                if total_invested > 0 and years > 0 else 0)
    
    def code_max_drawdown(daily_records):
        """代码中的最大回撤计算"""
        max_value = 0
        max_drawdown = 0
        for record in daily_records:
            if record["total_value"] > max_value:
                max_value = record["total_value"]
            drawdown = (max_value - record["total_value"]) / max_value * 100 if max_value > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        return max_drawdown
    
    # 测试年化收益
    test_cases = [
        (11000, 10000, 365),
        (12000, 10000, 730),  # 2年
        (15000, 10000, 1095), # 3年
    ]
    
    print("\n--- 年化收益对比 ---")
    all_passed = True
    for final, invested, days in test_cases:
        my_result = calculate_annual_return(final, invested, days)
        code_result = code_annual_return(final, invested, days)
        diff = abs(my_result - code_result)
        
        print(f"投入:{invested} -> 最终:{final}, 天数:{days}")
        print(f"  我的实现: {my_result:.6f}%")
        print(f"  代码实现: {code_result:.6f}%")
        print(f"  差异: {diff:.10f}%")
        
        if diff < 0.0001:
            print("  ✅ 公式一致")
        else:
            print("  ❌ 公式不一致!")
            all_passed = False
    
    # 测试最大回撤
    print("\n--- 最大回撤对比 ---")
    test_records = [
        {"total_value": 100},
        {"total_value": 110},
        {"total_value": 105},
        {"total_value": 95},
        {"total_value": 85},
        {"total_value": 90},
    ]
    
    my_values = [r["total_value"] for r in test_records]
    my_result = calculate_max_drawdown(my_values)
    code_result = code_max_drawdown(test_records)
    
    print(f"资产变化: {my_values}")
    print(f"  我的实现: {my_result:.6f}%")
    print(f"  代码实现: {code_result:.6f}%")
    print(f"  差异: {abs(my_result - code_result):.10f}%")
    
    if abs(my_result - code_result) < 0.0001:
        print("  ✅ 公式一致")
    else:
        print("  ❌ 公式不一致!")
        all_passed = False
    
    return all_passed


def main():
    """主函数"""
    print("\n" + "="*60)
    print("      基金数据准确性验证测试")
    print("="*60)
    
    results = []
    
    # 执行各项测试
    results.append(("年化收益公式", test_annual_return_formula()))
    results.append(("最大回撤公式", test_max_drawdown_formula()))
    results.append(("边界测试", test_boundary_conditions()))
    results.append(("代码对比", verify_formula_with_code()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("           测试结果汇总")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("  🎉 所有测试通过！数据准确性验证完成。")
    else:
        print("  ⚠️ 部分测试失败，需要检查代码。")
    print("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    main()