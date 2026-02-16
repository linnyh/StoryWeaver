import json
import re
from typing import Dict, Any, Optional
from app.models import Character
from app.services.generator import llm_client

async def analyze_state(character: Character, text: str, genre: str = "玄幻") -> Optional[Dict[str, Any]]:
    """
    分析文本，更新角色状态
    """
    current_state = character.power_state or {}
    
    # 默认 Prompt (修仙/玄幻)
    role_desc = "修仙小说战力分析师"
    task_desc = "分析正文是否涉及该角色的境界突破、获得/消耗物品、习得/升级技能。"
    output_example = """{
  "realm": "筑基后期",
  "bottleneck": "心魔未除",
  "inventory": [
    {"item": "残破的飞剑", "uses_left": 2},
    {"item": "筑基丹", "uses_left": 0}
  ],
  "core_skills": ["青云剑法(圆满)", "御风术(入门)"]
}"""

    # 根据类型调整 Prompt
    if "言情" in genre or "都市" in genre or "现实" in genre:
        role_desc = "小说情感与关系分析师"
        task_desc = """分析正文是否涉及该角色的：
1. 情感状态变化（如：暗恋、热恋、失恋、结婚）。
2. 重要人际关系进展（如：与某人关系破冰、决裂）。
3. 获得的纪念物品或重要礼物。
4. "realm" 字段请填写当前的【核心人际关系状态】或【情感阶段】。
5. "core_skills" 字段请填写【关键经历】或【性格成长点】。"""
        output_example = """{
  "realm": "与男主处于暧昧期",
  "bottleneck": "不敢表白",
  "inventory": [
    {"item": "男主送的项链", "uses_left": 1},
    {"item": "电影票根", "uses_left": 1}
  ],
  "core_skills": ["初次约会", "解开误会"]
}"""
    elif "悬疑" in genre or "推理" in genre:
        role_desc = "悬疑小说线索分析师"
        task_desc = """分析正文是否涉及该角色的：
1. 理智值/精神状态变化 ("realm")。
2. 获得的线索、道具 ("inventory")。
3. 掌握的关键技能或推论 ("core_skills")。"""
        output_example = """{
  "realm": "理智值 80/100 (轻度惊恐)",
  "bottleneck": "找不到凶器",
  "inventory": [
    {"item": "沾血的钥匙", "uses_left": 1},
    {"item": "神秘日记本", "uses_left": 1}
  ],
  "core_skills": ["法医鉴定(入门)", "侧写能力"]
}"""

    prompt = f"""你是一个{role_desc}。请根据以下小说正文内容，更新角色的状态。

【角色信息】
姓名：{character.name}
当前状态：{json.dumps(current_state, ensure_ascii=False)}

【小说正文】
{text[:3000]} 
(截取部分内容)

【任务】
{task_desc}
2. 如果有变化，请更新状态。如果没有变化，保持原样。
3. "inventory" 字段是物品列表，请注意增减数量 (uses_left)。
4. "bottleneck" 是当前瓶颈或困境。

【输出格式】
请直接输出 JSON 格式，不要包含任何 Markdown 标记或思考过程。
格式示例：
{output_example}
"""
    try:
        response = await llm_client.generate(prompt)
        
        # 清理响应
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        response = re.sub(r'```json', '', response)
        response = re.sub(r'```', '', response)
        response = response.strip()
        
        new_state = json.loads(response)
        return new_state
    except Exception as e:
        print(f"State analysis failed: {e}")
        return None
