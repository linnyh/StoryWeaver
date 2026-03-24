# Backend Agents 模块

> [根目录](../../CLAUDE.md) > [backend](../) > **app/agents**

---

## 模块职责

**多智能体审稿委员会 (Editorial Room)** - 哲学多视角 AI 审查系统。

**设计目标**: 在场景生成后，引入三个独立 Agent 对初稿进行全方位体检，确保逻辑闭环、爽点到位、立意深刻。

---

## Agent 角色定义

| Agent | 职责 | 审查重点 |
|-------|------|---------|
| **Agent A (逻辑)** | 战力与铺垫检查 | 战力崩坏、逻辑漏洞、伏笔呼应 |
| **Agent B (爽点)** | 读者视角评估 | 期待感、情绪释放、节奏把控 |
| **Agent C (思想)** | 立意深度确保 | 哲学内核呼应、主题升华 |

---

## 核心类

```python
class EditorialRoom:
    @staticmethod
    async def review_and_revise(
        draft: str,                    # 初稿内容
        context: str,                  # 上下文（Prompt 信息部分）
        philosophical_theme: str,      # 哲学思想内核
        enable_log: bool = True        # 是否输出评审日志
    ) -> Dict:
        """
        执行审稿与修订循环
        返回: {
            "content": 最终修订后的正文,
            "logs": 评审日志列表
        }
        """

    @staticmethod
    async def _agent_a_logic_review(draft, context) -> Dict:
        """Agent A: 逻辑审查"""

    @staticmethod
    async def _agent_b_punchline_review(draft, context) -> Dict:
        """Agent B: 爽点审查"""

    @staticmethod
    async def _agent_c_philosophy_review(draft, philosophical_theme) -> Dict:
        """Agent C: 思想审查"""

    @staticmethod
    async def _revise_draft(draft, issues) -> str:
        """综合 Agent 意见修订初稿"""
```

---

## 审稿流程

```
1. 生成初稿 (SceneGenerator)
         |
         v
2. Agent A 逻辑审查 --> 问题列表 A
         |
         v
3. Agent B 爽点审查 --> 问题列表 B
         |
         v
4. Agent C 思想审查 --> 问题列表 C
         |
         v
5. 综合问题，修订初稿
         |
         v
6. 评分检查 (通过阈值?)
         | 是
         v
    返回最终正文 + 评审日志
         |
    (可选) 循环重试直到达标或上限
```

---

## 与场景生成的集成

```python
# generator.py - SceneGenerator.generate_scene_content()
async def generate_scene_content(..., enable_editorial=False):
    if not enable_editorial:
        # 直接流式生成
        yield {"type": "content", "content": chunk}
        return

    # 1. 生成初稿
    full_draft = await self.llm.generate(prompt)

    # 2. 提交审稿委员会
    review_result = await EditorialRoom.review_and_revise(
        draft=full_draft,
        context=context_str,
        philosophical_theme=novel.philosophical_theme
    )

    # 3. 输出日志
    for log in review_result["logs"]:
        yield {"type": "log", "content": log}

    # 4. 输出最终正文
    yield {"type": "content", "content": review_result["content"]}
```

---

## 评审日志格式

```json
{
  "type": "log",
  "content": "[Agent A] 发现战力崩坏：主角在筑基期击败元婴期敌人，缺乏铺垫..."
}
```

---

## 配置说明

- **默认关闭**: `enable_editorial=False`，优先生成速度
- **模型可配**: 可传入 `writing_model` 和 `editorial_model` 区分写作/审稿模型
- **重试机制**: 评分低于阈值时自动修订循环

---

## 依赖

- `app.services.generator` - LLMClient
- `app.config` - settings

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `editorial_room.py` | 多智能体审稿委员会实现 |
| `generator.py` | 场景生成器 (调用审稿) |
| `scene_usecases.py` | 场景用例 (控制开关) |

---

## 变更记录

- **2026-03-24**: 初始化文档

---

## 待补充

- [ ] 单元测试文件
- [ ] Agent 评分阈值配置说明
- [ ] 评审日志前端展示示例
