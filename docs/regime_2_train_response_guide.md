# `/regime/2-train` 响应字段详解

本文以一次真实训练结果（`model_version=20260802T074318`，`horizon_hours=12`）为例，逐项说明 JSON 中每个字段的含义、如何计算、以及如何阅读。

---

## 1. 先看结论（读数顺序）

建议按这个顺序扫一遍：

1. **`gate_passed`**：全局 holdout 闸门是否通过（能否作为可用模型）
2. **`regime_policies.*.alert_enabled`**：各 present regime 是否允许发 transition 告警
3. **`per_present_regime`**：各子组在 holdout 上的真实表现
4. **`accuracy` / `change_precision` / `predicted_change_rate`**：整体决策质量与告警密度
5. **`walk_forward`**：验证阶段如何选 class_weight 与阈值

本例结论摘要：

| 项 | 值 | 含义 |
|----|----|------|
| 全局闸门 | `gate_passed=true` | 模型可用于 serving |
| RANGE | threshold `0.36`，`alert_enabled=true` | 最好用的子组 |
| TREND_UP | threshold `0.34`，`alert_enabled=true` | 可用，但告警偏密 |
| TREND_DOWN | threshold `0.34`，`alert_enabled=false` | 只出概率，不发模型告警 |

---

## 2. 任务定义（理解所有字段的前提）

| 概念 | 含义 |
|------|------|
| 目标 `continue_change` | 二分类：未来是否发生**已确认的结构切换** |
| `CONTINUE`（标签 0） | 在 `horizon_hours` 内，confirmed 前向 regime 仍等于当前 `regime_now` |
| `CHANGE`（标签 1） | confirmed 前向 regime ≠ 当前 `regime_now` |
| `present` / `regime_now` | 规则引擎给出的**当前**市场状态（UP / DOWN / RANGE） |
| Dual-track | present 仍由规则决定；模型只估 `P(change)`，用于 transition 风险 |

本例：`horizon_hours=12`，`confirm_bars=2`（前向切换需再确认 2 根 1H bar）。

---

## 3. 顶层身份与配置字段

### `success`
请求是否成功完成训练。`true` 表示流程跑完并返回指标；不等于闸门一定通过（本例两者都为 true）。

### `target`
模型目标类型。当前为 `continue_change`（继续/切换）。历史遗留的 `regime_48h` 三分类已废弃。

### `label_version`
标签版本。`confirmed_change_v1` 表示使用「确认后才算 CHANGE」的标签逻辑，而不是简单看 T+H 终点是否不同。

### `horizon_hours`
前向预测视界（小时）。本例为 `12`。  
**来源是打标结果**（特征上的 `regime_horizon_hours`），由 `/regime/1-label` 写入；`/regime/2-train` 默认自动读取，无需再传。  
若库中仍混有多种 horizon，train 会报错，需统一重标，或仅在消歧时显式传 `horizon_hours`。

### `change_threshold`
**全局回退阈值**（本例 `0.36`）。  
在 walk-forward 校准概率上做阈值扫描后选出。  
线上优先用 `regime_policies[present].threshold`；只有缺少 per-regime 策略时才退回该值。

### `class_weight`
最终选用的样本权重模式。本例 `none` = 训练时不加类别权重。  
候选通常还有 `balanced`；由 walk-forward 的 PR-AUC 择优。

### `class_weights`
实际用到的类别权重字典。`none` 时为空 `{}`。

### `calibration`
概率校准方法。`platt` = 在 out-of-fold 原始分数上拟合 Platt（logistic）校准，使 `p_change` 更接近真实频率。

### `model_version`
模型代际 ID（UTC 时间戳风格）。本例 `20260802T074318`。写入 `models/regime_model_meta.json`，便于追溯。

### `feature_schema_version`
特征 schema 版本。`transition_v1` 表示包含 transition 动态特征（delta、margin、regime_age 等）。merge/特征定义变更后应重跑 merge + label + train。

### `confirm_bars`
确认 CHANGE 所需的额外 bar 数。本例 `2`：结构切换后还需再稳住 2 根才记为 CHANGE。

### `trained_at`
训练完成的本地时间戳（本例 `2026-08-02T15:43:18...`）。

---

## 4. 全局闸门（能不能上线）

### `gate_requirements`
闸门规则定义（不是结果）：

| 字段 | 含义 |
|------|------|
| `change_precision_gt` | CHANGE 精确率必须 **大于** 该值（本例 `0.5`） |
| `accuracy_gt_always_continue` | 准确率必须高于「永远预测 CONTINUE」基线 |
| `pr_auc_gt_prevalence` | PR-AUC 必须高于 CHANGE 先验比例（正类占比） |

### `gate_reasons`
三条规则在 **未触碰 holdout** 上的逐项布尔结果：

| 字段 | 本例 | 含义 |
|------|------|------|
| `change_precision` | true | holdout 上 CHANGE precision > 0.5 |
| `accuracy_vs_always_continue` | true | acc > always_continue_baseline |
| `pr_auc_vs_prevalence` | true | PR-AUC > test_change_rate |

### `gate_passed`
`all(gate_reasons.values())`。本例 `true`。  
全局闸门通过后，模型才允许进入「可告警」候选；具体某 present 是否告警还要看 `regime_policies.*.alert_enabled`。

---

## 5. 数据切分与训练规模

### `train_size`
最终拟合 booster 的训练样本数。本例 `14388`。  
最终训练集会在 holdout 前再 purge `horizon_hours` 行，避免标签泄漏。

### `holdout_size`
完全未参与调参的 holdout 样本数。本例 `3600`。

### `holdout_start_ts`
Holdout 起始时间戳（毫秒）。本例 `1772510400000`。  
请求里固定该参数可保证多次训练对比同一时间段。

### `purge_rows`
时间泄漏隔离行数。本例 `12`（等于 `horizon_hours`）：验证/holdout 边界前丢掉近 horizon 的样本，因为标签依赖未来 H 小时。

### `test_period`
Holdout 覆盖的时间范围：

- `from_ts`：holdout 第一根 bar
- `to_ts`：holdout 最后一根 bar

---

## 6. `feature_columns`

训练/推理实际使用的特征名列表（本例 48 列）。大致分组：

| 组 | 示例 | 作用 |
|----|------|------|
| 4H 趋势/动量 | `adx_4h`, `ema_*_4h`, `macd_*_4h` | 主结构状态 |
| 1H / 15m / 1D | `rsi_14_1h`, `stoch_*_15m`, `bollinger_position_1d` | 多周期上下文 |
| 收益 | `price_return_1h/4h/12h` | 近期价格动能 |
| 动态 delta | `adx_4h_delta_6h`, `ema_gap_4h_delta_6h` 等 | 结构是否在加速变化 |
| 阈值距离 | `adx_range_margin`, `adx_trend_margin` 等 | 离规则边界有多近 |
| Regime 历史 | `regime_age_1h`, `regime_switches_24h`, `rule_conflict_score` | 状态年龄与冲突 |

线上预测必须用同一列集合（保存在 `models/regime_model_features.json`）。

---

## 7. `walk_forward`（验证阶段做了什么）

Walk-forward 在 **holdout 之前** 的数据上做 purged 滚动验证，用于：

1. 在 `none` / `balanced` 中选 class_weight  
2. 拟合 Platt 校准器  
3. 选全局阈值与各 present 的 regime 阈值  

### `walk_forward.selected_class_weight`
最终模式，本例 `none`（与顶层 `class_weight` 一致）。

### `walk_forward.candidate_modes`

#### `none` / `balanced`
每种模式下的汇总与折详情：

| 字段 | 含义 |
|------|------|
| `pr_auc` | 各折 OOF 汇总后的平均精度（选模主指标） |
| `roc_auc` | ROC-AUC |
| `brier_score` | 概率校准误差（越小越好） |
| `folds[]` | 每一折的 train/val 规模与折内 AUC |

本例：`none` 的 `pr_auc≈0.655` 高于 `balanced≈0.644`，故选 `none`。

单折字段：

| 字段 | 含义 |
|------|------|
| `fold` | 折号 |
| `train_size` | 该折训练行数 |
| `validation_size` | 该折验证行数 |
| `purge_rows` | 折边界 purge |
| `roc_auc` / `pr_auc` | 该折验证分数 |

### `walk_forward.selected_threshold`
全局阈值，本例 `0.36`（写入顶层 `change_threshold`）。

### `walk_forward.threshold_sweep`
在 **全部 OOF 校准概率** 上，对阈值 `0.30 ~ 0.90`（步长 0.02）扫描的结果表。每行：

| 字段 | 含义 |
|------|------|
| `threshold` | 判定 `p_change >= threshold` 则为 CHANGE |
| `precision` | 预测为 CHANGE 中真正 CHANGE 的比例 |
| `recall` | 真实 CHANGE 被召回的比例 |
| `f1` | precision/recall 调和平均 |
| `accuracy` | 整体正确率 |
| `alert_rate` | 预测为 CHANGE 的比例（告警密度） |
| `accuracy_gain_vs_continue` | 相对「永远 CONTINUE」基线的准确率提升 |

**选阈规则（代码）**：先筛 `precision > min_precision` 且 `accuracy_gain_vs_continue > 0` 的候选；再在候选中取 **最大 F1**，F1 相同取更大 accuracy。若无候选则退回全表按同样准则选。

本例全局选中 `0.36`：F1≈0.6965，且满足 precision>0.5。注意其 `alert_rate≈0.76` 仍然偏高——这是「保 F1」目标下的自然结果。

### `walk_forward.regime_policies`
验证阶段按 **present regime** 切分后的策略草案（结构与顶层 `regime_policies` 相同，见第 9 节）。Holdout 闸门通过后会补上 `holdout_gate_*` 与 `alert_enabled`。

---

## 8. 全局 Holdout 指标（顶层）

这些字段描述 **整段 holdout** 在「按行使用对应 present 阈值」后的表现。

### `accuracy`
正确率。本例 `≈0.627`。

### `always_continue_baseline`
永远预测 CONTINUE 的准确率 = holdout 中 CONTINUE 占比。本例 `≈0.520`。

### `always_change_baseline`
永远预测 CHANGE 的准确率 = CHANGE 占比。本例 `≈0.480`。

### `majority_baseline_accuracy`
多数类基线 = `max(always_continue, always_change)`。本例同 continue 基线。

### `roc_auc`
用连续 `p_change` 算的 ROC-AUC（与阈值无关）。本例 `≈0.672`。>0.5 表示有排序能力。

### `pr_auc`
Precision-Recall AUC（平均精度）。对类别不平衡更敏感。本例 `≈0.616`，高于 `test_change_rate≈0.480`。

### `brier_score`
概率与真实 0/1 的均方误差。越小校准/分辨越好。本例 `≈0.227`。

### `change_precision`
在选定阈值决策下，预测 CHANGE 的精确率。本例 `≈0.574`。

### `predicted_change_rate`
模型预测为 CHANGE 的比例（告警率）。本例 `≈0.724`——整体仍偏「爱报警」。

### `test_change_rate`
Holdout 真实 CHANGE 占比（先验）。本例 `≈0.480`。

### `classification_report`
sklearn 风格分类报告，按 `CONTINUE` / `CHANGE` 给出 precision、recall、f1、support。

阅读要点（本例）：

- CHANGE recall 高（`≈0.865`）：漏报少  
- CHANGE precision 中等（`≈0.574`）：误报仍多  
- CONTINUE recall 偏低（`≈0.407`）：很多真正 CONTINUE 被判成 CHANGE  

### `confusion_matrix`
与 `confusion_matrix_labels: ["CONTINUE","CHANGE"]` 对齐：

```text
                预测 CONTINUE    预测 CHANGE
真实 CONTINUE      762              1109
真实 CHANGE        233              1496
```

- 左上 / 右下：正确  
- 右上：假阳性告警  
- 左下：漏报  

### `beats_always_continue` / `beats_majority` / `beats_persistence`
是否超过对应基线。本例均为 `true`。  
`persistence_baseline_accuracy` 在 continue/change 任务里等于 always-continue 基线（「结构会持续」的朴素假设）。

---

## 9. `regime_policies`（按 present 的部署策略）

对每个 `TREND_UP` / `TREND_DOWN` / `RANGE` 各有一份策略。  
**线上 transition 告警**：全局 `gate_passed` **且** 该 regime 的 `alert_enabled` **且** `p_change >= threshold`。

### 公共字段

| 字段 | 含义 |
|------|------|
| `threshold` | 该 present 下判定 CHANGE 的概率阈值（验证集选出） |
| `gate_passed` | **验证集**上三条闸门是否全过 |
| `gate_reasons` | 验证集逐项闸门 |
| `validation_size` | 验证 OOF 中该 present 的样本数 |
| `validation_metrics` | 验证集上用该 threshold 的指标摘要 |
| `threshold_sweep` | 该子组自己的阈值扫描表（字段同全局 sweep） |
| `holdout_gate_reasons` | **未触碰 holdout** 上逐项闸门 |
| `holdout_gate_passed` | holdout 闸门是否全过 |
| `alert_enabled` | `gate_passed AND holdout_gate_passed`；为 false 则禁止模型告警 |

### 本例三态解读

#### `TREND_UP`
- `threshold=0.34`，`alert_enabled=true`
- 验证/holdout 闸门都过
- 但 validation `predicted_change_rate≈0.91`：阈值偏低，几乎常报警
- Holdout：acc≈0.66，roc≈0.69，可用但吵

#### `TREND_DOWN`
- `threshold=0.34`，**`alert_enabled=false`**
- 验证闸门过，但 holdout 失败：
  - `change_precision=false`（holdout precision≈0.47 < 0.5）
  - `accuracy_vs_always_continue=false`（acc≈0.49 < 基线≈0.55）
  - `pr_auc_vs_prevalence=true`（仍略高于先验）
- 含义：验证乐观、holdout 崩；**只输出 `p_change`，不发 Redis/API transition alert**

#### `RANGE`
- `threshold=0.36`，`alert_enabled=true`
- 样本最多（validation_size≈5179，holdout support≈1975）
- Holdout 最好：acc≈0.68，roc≈0.74，alert_rate≈0.59
- 是目前最值得信任的告警子组

> 顶层 `regime_policies` 与 `walk_forward.regime_policies` 内容相同（训练结束时的最终策略）。读一份即可。

---

## 10. `per_present_regime`（Holdout 分桶成绩单）

对 holdout 按当时的 `regime_now` 分组评估。比全局指标更适合判断「现在处于某 regime 时模型靠不靠谱」。

每个 key（`TREND_UP` / `TREND_DOWN` / `RANGE`）包含：

| 字段 | 含义 |
|------|------|
| `threshold` | 该组使用的决策阈值 |
| `alert_enabled` | 是否允许告警（同 regime_policies） |
| `accuracy` 等 | 同第 8 节全局指标，但只在该子组计算 |
| `classification_report` / `confusion_matrix` | 该子组混淆与分类报告 |

### 本例速读

| Present | n | Acc | ROC | CHANGE precision | 预测 CHANGE 率 | 告警 |
|---------|---|-----|-----|------------------|----------------|------|
| RANGE | 1975 | 0.677 | 0.737 | 0.612 | 0.589 | 开 |
| TREND_UP | 719 | 0.658 | 0.692 | 0.638 | 0.880 | 开（密） |
| TREND_DOWN | 906 | 0.493 | 0.510 | 0.470 | 0.892 | **关** |

`TREND_UP` 混淆矩阵解读：

```text
[[ 69, 229],   # CONTINUE: 只抓对 69，误报 229
 [ 17, 404]]   # CHANGE: 几乎全召回
```

策略偏向「宁可错报也不漏报」。

---

## 11. 线上如何使用这些字段

```text
present = 规则引擎(regime_now)
p_change = 模型校准概率
policy = regime_policies[present]

alert_eligible =
    gate_passed
    AND policy.alert_enabled
    AND (p_change >= policy.threshold)
```

因此：

- 看概率：始终可读 `probabilities.change`
- 看是否该吵人：看 `transition.alert_eligible`（或等价逻辑）
- `TREND_DOWN` 下即使 `p_change` 很高，本模型也不会开告警

---

## 12. 字段索引（速查）

| 字段路径 | 一句话 |
|----------|--------|
| `success` | 训练 API 是否成功 |
| `target` | 任务类型 continue/change |
| `label_version` | 标签定义版本 |
| `horizon_hours` | 前向视界（小时） |
| `change_threshold` | 全局回退阈值 |
| `class_weight` / `class_weights` | 样本权重模式 |
| `calibration` | 概率校准方法 |
| `gate_passed` / `gate_reasons` / `gate_requirements` | 全局上线闸门 |
| `model_version` | 模型代际 |
| `feature_schema_version` | 特征 schema |
| `confirm_bars` | CHANGE 确认 bar 数 |
| `train_size` / `holdout_size` / `holdout_start_ts` / `purge_rows` | 数据切分 |
| `feature_columns` | 使用的特征列 |
| `walk_forward.*` | 验证选模/选阈过程 |
| `regime_policies.*` | 分 present 阈值与是否告警 |
| `per_present_regime.*` | Holdout 分桶指标 |
| `test_period` | Holdout 时间窗 |
| `trained_at` | 训练完成时间 |
| `accuracy` 等顶层指标 | Holdout 全局成绩 |
| `classification_report` / `confusion_matrix` | 详细分类结果 |
| `beats_*` / `persistence_baseline_accuracy` | 是否打赢基线 |

---

## 13. 相关代码与接口

- 训练与指标：`src/models/regime_trainer.py`
- API：`GET /regime/2-train`
- 预测：`GET /regime/3-predict`（present 规则 + transition 模型）
- 产品说明：`README.md`、`PRD.md`

复现本例训练：

```bash
curl 'http://127.0.0.1:8000/regime/2-train?limit=18000&test_ratio=0.2&holdout_start_ts=1772510400000'
```
