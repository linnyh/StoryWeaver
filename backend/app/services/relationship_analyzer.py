import json
from typing import Optional, Dict, List, Any
from app.services.generator import llm_client
from app.models import Character, Relationship

async def analyze_relationships(
    content: str, 
    characters: List[Character], 
    existing_relationships: Dict[str, Relationship]
) -> List[Dict[str, Any]]:
    """
    分析场景内容，更新角色关系
    
    Args:
        content: 场景正文
        characters: 参与场景的角色列表
        existing_relationships: 现有的关系字典，key为 "id_a:id_b" (id_a < id_b)
        
    Returns:
        List of updates: [{"char_a_id": str, "char_b_id": str, "affinity_change": int, "new_conflict": str}]
    """
    if len(characters) < 2:
        return []
        
    # 构建角色列表描述
    char_desc = "\n".join([f"- {c.name} (ID: {c.id})" for c in characters])
    
    # 构建现有关系描述
    rel_desc = ""
    processed_pairs = set()
    
    for i in range(len(characters)):
        for j in range(i + 1, len(characters)):
            c1 = characters[i]
            c2 = characters[j]
            # 确保 ID 排序一致性
            id_a, id_b = sorted([c1.id, c2.id])
            key = f"{id_a}:{id_b}"
            
            rel = existing_relationships.get(key)
            if rel:
                rel_desc += f"- {c1.name} <-> {c2.name}: 当前好感度 {rel.affinity_score}, 核心矛盾: {rel.core_conflict or '无'}\n"
            else:
                rel_desc += f"- {c1.name} <-> {c2.name}: 暂无记录 (默认好感度 0)\n"

    prompt = f"""你是一个小说人际关系分析师。请分析以下小说正文，判断角色之间的关系变化。

【角色列表】
{char_desc}

【现有关系】
{rel_desc}

【小说正文】
{content[:4000]}
(截取部分)

【任务】
1. 分析正文中是否有明显的互动导致角色关系变化（好感度升降、产生新误会、化解旧矛盾）。
2. 只关注**有实质性变化**的关系对。如果只是普通对话且无情感波动，请忽略。
3. "affinity_change" 是好感度变化值（例如 +5, -10）。范围通常在 -10 到 +10 之间，除非发生重大事件。
4. "new_conflict" 是更新后的核心矛盾或羁绊。如果矛盾解决了，请更新为新的状态或清空；如果有新矛盾，请追加。

【输出格式】
请输出 JSON 列表，格式如下（不要包含 Markdown）：
[
  {{
    "char_a_id": "ID_1",
    "char_b_id": "ID_2",
    "affinity_change": 5,
    "new_conflict": "两人因误会解开而关系缓和，但仍对上次的背叛心存芥蒂"
  }}
]
如果无变化，输出空列表 []。
"""
    
    response = await llm_client.generate(prompt)
    
    try:
        # Cleanup response if it contains <think> tags
        import re
        cleaned_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        
        # Cleanup response if it contains markdown code blocks
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        
        cleaned_response = cleaned_response.strip()
        
        updates = json.loads(cleaned_response)
        if isinstance(updates, list):
            return updates
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing relationship analysis: {e}")
        print(f"Raw response: {response}")
        return []
    except Exception as e:
        print(f"Error analyzing relationships: {e}")
        return []
