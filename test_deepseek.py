#!/usr/bin/env python3
"""
测试 DeepSeek V3.2 Speciale API 流式输出
"""
import os
import sys

# 添加 backend 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from openai import OpenAI

# API 配置
API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-35ee39593389409caf79dfbbadd90e5e')
BASE_URL = 'https://api.deepseek.com'  # 标准 API

# 测试问题（图2的几何题）
TEST_QUESTION = """圆Γ1和圆Γ2相交于点M和N，设l是圆Γ1和圆Γ2的两条公切线中距离M较近的那条公切线。l与圆Γ1相切于点A，与圆Γ2相切于点B。设经过点M且与l平行的直线与圆Γ1还相交于点C，与圆Γ2还相交于点D。直线CA和DB相交于点E，直线AN和CD相交于点R，直线BN和CD相交于点Q。求证：ER=EQ。"""

def test_streaming():
    """测试流式输出"""
    print("=" * 60)
    print("测试 DeepSeek V3.2 Speciale 流式输出")
    print("=" * 60)
    print(f"\n问题: {TEST_QUESTION}\n")
    print("-" * 60)
    
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )
    
    try:
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[{"role": "user", "content": TEST_QUESTION}],
            stream=True
        )
        
        reasoning_content = ""
        content = ""
        chunk_count = 0
        
        print("\n[开始接收流式响应]\n")
        
        for chunk in response:
            chunk_count += 1
            
            if not chunk.choices:
                print(f"[Chunk {chunk_count}] 空 choices")
                continue
            
            delta = chunk.choices[0].delta
            
            # 检查思维链
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                reasoning_content += delta.reasoning_content
                print(delta.reasoning_content, end='', flush=True)
            
            # 检查内容
            if hasattr(delta, 'content') and delta.content:
                if reasoning_content and not content:
                    print("\n\n" + "=" * 60)
                    print("[思维链结束，开始输出内容]")
                    print("=" * 60 + "\n")
                content += delta.content
                print(delta.content, end='', flush=True)
            
            # 每100个chunk打印状态
            if chunk_count % 100 == 0:
                print(f"\n[已接收 {chunk_count} 个 chunk, 思维链 {len(reasoning_content)} 字, 内容 {len(content)} 字]", flush=True)
        
        print("\n\n" + "=" * 60)
        print(f"[完成] 共 {chunk_count} 个 chunk")
        print(f"思维链长度: {len(reasoning_content)} 字")
        print(f"内容长度: {len(content)} 字")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_streaming()

