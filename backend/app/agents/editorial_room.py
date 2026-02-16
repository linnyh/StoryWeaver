from typing import List, TypedDict, Annotated, Dict, Any, Union
import operator
import json
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from app.config import settings

# --- State Definition ---

class EditorialState(TypedDict):
    draft: str
    context: str
    philosophical_theme: str
    
    # Accumulate critiques and scores from all rounds
    critiques: Annotated[List[str], operator.add]
    scores: Annotated[List[float], operator.add]
    
    iteration_count: int
    
    # Logs for the user
    logs: Annotated[List[str], operator.add]

# --- Agents Setup ---

def get_llm():
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_model,
        temperature=0.7,
        max_tokens=4000
    )

# --- Prompts ---

PROMPT_A = """你是一个严苛的小说编辑，代号【Agent A：节奏与逻辑审查员】。
你的职责是检查小说片段的战力体系是否崩坏，铺垫是否冗长，逻辑是否自洽。

当前小说片段：
{draft}

上下文信息：
{context}

请给出你的评分（0-10分）和批判意见。
如果评分低于8分，必须给出具体的修改建议。

请严格按照以下JSON格式输出：
{{
    "score": 7.5,
    "critique": "战力体系有点崩坏，主角明明...",
    "suggestion": "建议削弱主角的..."
}}
"""

PROMPT_B = """你是一个热血的小说读者兼评论家，代号【Agent B：爽点体验官】。
你的职责是模拟读者视角，检查期待感和情绪释放是否到位，是否有足够的“爽点”或情感共鸣。

当前小说片段：
{draft}

上下文信息：
{context}

请给出你的评分（0-10分）和批判意见。
如果评分低于8分，必须指出哪里让人觉得无聊或憋屈。

请严格按照以下JSON格式输出：
{{
    "score": 6.0,
    "critique": "期待感不足，反派的嘲讽不够...",
    "suggestion": "增加反派的嚣张气焰，让打脸更爽..."
}}
"""

PROMPT_C = """你是一个深刻的文学导师，代号【Agent C：思想升华导师】。
你的职责是审视关键转折点的情节是否呼应了小说的【哲学思想内核】，确保探讨深度。

小说哲学思想内核：【{philosophical_theme}】

当前小说片段：
{draft}

上下文信息：
{context}

请给出你的评分（0-10分）和批判意见。
如果评分低于8分，必须指出情节如何偏离了主题或显得肤浅。

请严格按照以下JSON格式输出：
{{
    "score": 8.5,
    "critique": "虽然情节紧凑，但没有体现出‘天道无情’的主题...",
    "suggestion": "在结尾处增加主角对命运的无奈感叹..."
}}
"""

REVISION_PROMPT = """你是一个专业的小说家。
请根据以下编辑委员会的反馈意见，修改并重写小说片段。

当前草稿：
{draft}

上下文信息：
{context}

哲学思想内核：{philosophical_theme}

编辑委员会反馈（请重点参考）：
{critiques}

请输出修改后的正文。
注意：直接输出正文，不要包含任何解释或“好的，我来修改”之类的废话。
"""

# --- Helper Functions ---

async def run_agent(name: str, prompt_template: str, state: EditorialState) -> Dict:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({
            "draft": state["draft"],
            "context": state["context"],
            "philosophical_theme": state["philosophical_theme"]
        })
        
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[0].strip()
            
        # Clean up potential trailing commas or comments that break JSON
        # This is a basic attempt, a robust parser would be better but this suffices for now
        
        data = json.loads(content)
        score = float(data.get("score", 0))
        critique = data.get("critique", "")
        suggestion = data.get("suggestion", "")
        
        log = f"【{name}】(评分 {score}): {critique} -> 建议: {suggestion}"
        full_critique = f"{name}: {critique} (建议: {suggestion})"
        
        return {
            "score": score,
            "critique": full_critique,
            "log": log
        }
    except Exception as e:
        print(f"{name} error: {e}")
        return {
            "score": 5.0,
            "critique": f"{name} 执行出错: {str(e)}",
            "log": f"【{name}】执行出错: {str(e)}"
        }

# --- Node Functions ---

async def critique_node(state: EditorialState):
    """Run all 3 agents in parallel"""
    
    results = await asyncio.gather(
        run_agent("Agent A (逻辑)", PROMPT_A, state),
        run_agent("Agent B (爽点)", PROMPT_B, state),
        run_agent("Agent C (思想)", PROMPT_C, state)
    )
    
    scores = [r["score"] for r in results]
    critiques = [r["critique"] for r in results]
    logs = [r["log"] for r in results]
    
    return {
        "scores": scores,
        "critiques": critiques,
        "logs": logs
    }

import re

# ...

async def revision_node(state: EditorialState):
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(REVISION_PROMPT)
    chain = prompt | llm
    
    # Get the critiques from the last round (last 3)
    current_critiques = state["critiques"][-3:]
    critiques_text = "\n".join(current_critiques)
    
    response = await chain.ainvoke({
        "draft": state["draft"],
        "context": state["context"],
        "philosophical_theme": state["philosophical_theme"],
        "critiques": critiques_text
    })
    
    content = response.content
    # Remove <think> tags and markdown bold
    clean_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    clean_content = re.sub(r'\*\*', '', clean_content).strip()
    
    return {
        "draft": clean_content,
        "iteration_count": state["iteration_count"] + 1,
        "logs": [f"【系统】已根据意见完成第 {state['iteration_count'] + 1} 版修改。"]
    }

def decision_node(state: EditorialState):
    iteration = state["iteration_count"]
    scores = state["scores"]
    
    # Get last 3 scores
    current_scores = scores[-3:] if scores else []
    
    print(f"DEBUG: Iteration {iteration}, Scores: {current_scores}")
    
    # Check max retries (2 retries = max iteration 2?)
    # Initial draft (iter 0) -> Critique -> Decision (iter 0) -> Revision -> iter 1
    # Rev 1 -> Critique -> Decision (iter 1) -> Revision -> iter 2
    # Rev 2 -> Critique -> Decision (iter 2) -> End?
    # User said: "Retry limit set to 2 times".
    # So max 2 revisions.
    
    if iteration >= 2:
        return "end"
    
    # If any score < 8, revise
    if any(s < 8.0 for s in current_scores):
        return "revise"
    
    return "end"

# --- Graph Construction ---

def create_editorial_graph():
    workflow = StateGraph(EditorialState)
    
    workflow.add_node("critique", critique_node)
    workflow.add_node("revision", revision_node)
    
    workflow.set_entry_point("critique")
    
    workflow.add_conditional_edges(
        "critique",
        decision_node,
        {
            "revise": "revision",
            "end": END
        }
    )
    
    workflow.add_edge("revision", "critique")
    
    return workflow.compile()

editorial_graph = create_editorial_graph()

class EditorialRoom:
    """多智能体审稿委员会"""
    
    @staticmethod
    async def review_and_revise(draft: str, context: str, philosophical_theme: str) -> Dict[str, Any]:
        """
        运行审稿委员会工作流
        """
        # Clean initial draft
        draft = re.sub(r'<think>.*?</think>', '', draft, flags=re.DOTALL).strip()
        
        initial_state = {
            "draft": draft,
            "context": context,
            "philosophical_theme": philosophical_theme or "无明确哲学主题",
            "critiques": [],
            "scores": [],
            "iteration_count": 0,
            "logs": ["【系统】初稿提交审稿委员会..."]
        }
        
        # Use ainvoke for async execution
        final_state = await editorial_graph.ainvoke(initial_state)
        
        # Clean final content again just in case
        final_content = final_state["draft"]
        final_content = re.sub(r'<think>.*?</think>', '', final_content, flags=re.DOTALL).strip()
        final_content = re.sub(r'\*\*', '', final_content).strip()
        
        return {
            "content": final_content,
            "logs": final_state["logs"],
            "final_scores": final_state["scores"][-3:] if final_state["scores"] else []
        }
