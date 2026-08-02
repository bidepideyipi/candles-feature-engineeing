# `/regime/3-predict` 响应字段详解

本文以一次真实预测结果为例，说明 dual-track payload 每个字段怎么读、以及该不该告警。

示例摘要（`model_version=20260802T082036`）：

| 项 | 值 | 含义 |
|----|----|------|
| present | `TREND_DOWN` | 规则判定当前是下跌结构 |
| `p_change` | 0.3775 | 模型认为 12h 内发生确认切换的概率 |
| 子组阈值 | 0.32 | `TREND_DOWN` 策略阈值 |
| `prediction` | `CHANGE` | `0.3775 ≥ 0.32`，阈值决策为 CHANGE |
| `alert_eligible` | **false** | DOWN 子组未开告警；不发 transition Redis |
| 策略建议 | `default_short` | 来自 **规则 present**，不是模型 |

---

## 1. Dual-track 怎么读（先看这三块）

```text
present     → 现在是什么结构？（规则，确定性）
transition  → 未来 horizon 内切换风险多大？（模型概率 + 闸门）
redis       → 这次有没有真正推流告警？
```

**不要**只看顶层的 `prediction` / `changes` 就去吵人。是否推送看：

```text
transition.alert_eligible == true
```

本例：`changes=true` 但 `alert_eligible=false` → **仅记录概率，不发 transition 告警**。

---

## 2. 顶层身份与模型元数据

### `type`
固定 `"regime"`，方便下游区分消息类型。

### `target`
模型任务。`continue_change` = 预测 CONTINUE vs CHANGE，不是预测下一个具体 regime。

### `timestamp` / `inst_id` / `bar` / `price`
特征对应的 1H bar 时间戳、合约、周期、当时价格。本例 `price=1875.43`。

### `features_count`
模型使用的特征列数。本例 `48`，应与训练时 `feature_columns` 长度一致。

### `horizon_hours`
模型训练时绑定的前向视界（来自标签 `regime_horizon_hours`）。本例 `12`。

### `class_weight`
该模型训练选用的样本权重模式（写入 meta）。本例 `balanced`。

### `model_gate_passed`（顶层）
**全局** holdout 闸门是否通过。本例 `true`。  
注意：全局过闸 ≠ 每个 present 子组都能告警。

### `model_version`
模型代际。本例 `20260802T082036`。

### `calibration`
概率校准。`platt` = 输出概率已经过 Platt 校准。

---

## 3. `present`：当前结构（规则引擎）

| 字段 | 本例 | 含义 |
|------|------|------|
| `regime` | `2` | 枚举值（常见：1=UP, 2=DOWN, 3=RANGE） |
| `regime_label` | `TREND_DOWN` | 可读名称 |
| `source` | `rules` | **不是模型**；由指标规则即时分类 |
| `recommended_strategy` | `default_short` | 基于当前结构的交易偏置建议 |
| `regime_description` | Downtrend… | 人话说明 |

**用法**：仓位/方向偏置优先看 `present`；模型不负责「现在该空还是该多」的结构认定。

---

## 4. `transition`：切换风险（模型 + 策略闸门）

### 概率与阈值

| 字段 | 本例 | 含义 |
|------|------|------|
| `source` | `model` | 来自 XGBoost + 校准 |
| `horizon_hours` | `12` | 风险视界 |
| `p_continue` | `0.6225` | P(结构在视界内继续) |
| `p_change` | `0.3775` | P(发生确认切换) |
| `threshold` | `0.32` | **当前 present** 对应的决策阈值 |
| `present_regime_policy` | `TREND_DOWN` | 用了哪条子组策略 |

### 决策字段（阈值，不是 argmax）

| 字段 | 本例 | 怎么算 |
|------|------|--------|
| `changes` | `true` | `p_change >= threshold` → `0.3775 ≥ 0.32` |
| `continues` | `false` | `not changes` |
| `prediction` | `CHANGE` | 同上 |

要点：本例 **`p_continue > p_change`**，但因为阈值是 0.32（偏低），仍判 `CHANGE`。  
告警决策是「过阈值」，不是「谁概率更大」。

### 闸门与告警资格

| 字段 | 本例 | 含义 |
|------|------|------|
| `model_gate_passed` | `false` | **全局闸门 ∧ 该子组 `alert_enabled`**。DOWN 子组关闭 → false |
| `gate_reasons` | precision/acc 失败 | 通常来自该子组 holdout 闸门原因 |
| `alert_eligible` | `false` | `全局过闸 ∧ 子组启用 ∧ changes` |

本例逻辑链：

```text
全局 model_gate_passed = true
TREND_DOWN.alert_enabled = false   ← 训练时 holdout 不过
→ transition.model_gate_passed = false
→ alert_eligible = false（即使 changes=true）
→ redis.transition_alerted = false
```

---

## 5. `derived`

`transition` 概率/决策的精简镜像，便于旧消费者或 Redis 字段复用：

- `continues` / `changes`
- `p_continue` / `p_change`

不含阈值、闸门、`alert_eligible`。**不能**单靠 `derived` 决定是否推送。

---

## 6. 顶层扁平字段（兼容层）

为兼容旧字段，顶层再 mirror 一份 **present** 信息：

| 字段 | 本例 | 注意 |
|------|------|------|
| `regime` / `regime_label` | DOWN | 等于 `present.*`，**不是**模型预测的下一状态 |
| `regime_description` | … | 同上 |
| `recommended_strategy` | `default_short` | 来自规则 present |
| `confidence` | `0.6225` | `max(p_continue, p_change)`，本例等于 continue 概率 |
| `probabilities` | continue/change | 与 `transition` 概率一致 |

易错点：

- `confidence` **不一定**等于「预测类」的概率（注释写 predicted class，实现是 max）
- 顶层没有 `prediction`；模型决策在 `transition.prediction`

---

## 7. `redis`：这次副作用

| 字段 | 本例 | 含义 |
|------|------|------|
| `updated_current` | `true` | 已更新 Redis 当前 regime 状态 |
| `window_size` | `8` | 滑动窗口内点数（用于反转检测） |
| `reversal_detected` | `false` | 未检测到 UP↔DOWN 规则反转 |
| `reversal_alerted` | `false` | 未发 reversal 流消息 |
| `transition_alerted` | `false` | **未发** transition 风险流（因 `alert_eligible=false`） |
| `transition_stream_id` | `null` | 无 transition XADD |
| `stream_id` | `null` | 无 reversal XADD |
| `reversal` | `null` | 无反转详情 |
| `error` | `null` | Redis 无错误 |

推送规则回顾：

1. **每次** predict：更新 current + 窗口  
2. **仅当** `transition.alert_eligible`：XADD `regime_change_risk`  
3. **仅当** 窗口检出 present UP↔DOWN 反转：XADD `regime_reversal`

本例两种告警都没有触发。

---

## 8. 本例一句话结论

当前规则结构是 **下跌（TREND_DOWN）**，策略偏空。  
模型给出 12h 切换概率约 **38%**，因 DOWN 阈值 0.32 被标成 `CHANGE`，但 **DOWN 子组告警关闭**，故 `alert_eligible=false`，Redis 不推 transition。  
下游应：跟 `present` 做结构/策略；把 `p_change` 当风险参考；**不要**因 `prediction=CHANGE` 自动报警。

---

## 9. 字段速查

| 路径 | 一句话 |
|------|--------|
| `present.*` | 规则当前结构与策略 |
| `transition.p_change` | 校准后的切换概率 |
| `transition.threshold` | 当前 present 的决策阈值 |
| `transition.prediction` / `changes` | 是否过阈值（≠ argmax） |
| `transition.alert_eligible` | 能不能推 transition 告警 |
| `transition.model_gate_passed` | 全局∧子组是否允许告警 |
| `model_gate_passed`（顶层） | 仅全局 holdout 闸门 |
| `derived.*` | 概率/决策缩略，无闸门 |
| `regime*` / `recommended_strategy`（顶层） | present 兼容字段 |
| `confidence` | max(p_continue, p_change) |
| `redis.transition_alerted` | 本次是否真的 XADD 了切换风险 |
| `redis.reversal_alerted` | 本次是否 XADD 了 UP↔DOWN 反转 |

---

## 10. 相关接口与文档

- 预测：`GET /regime/3-predict?from_local=false`（实时）或 `from_local=true`（Mongo）
- 训练响应解读：[`regime_2_train_response_guide.md`](./regime_2_train_response_guide.md)
- 产品说明：`README.md`（dual-track / Redis 条件推送）

```bash
curl -s 'http://127.0.0.1:8000/regime/3-predict?from_local=false' | python -m json.tool
```
