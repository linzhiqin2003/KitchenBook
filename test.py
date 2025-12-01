def generate():
    """流式生成器"""
    from openai import OpenAI
    
    client = OpenAI(
        api_key="sk-35ee39593389409caf79dfbbadd90e5e",
        base_url="https://api.deepseek.com/v3.2_speciale_expires_on_20251215"
    )
    
    try:
        # 发送初始状态
        yield f"data: {json.dumps({'type': 'status', 'content': '正在连接 DeepSeek V3.2 Speciale...'}, ensure_ascii=False)}\n\n"
        
        # 调用 DeepSeek V3.2 Speciale (思考模型，流式)
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[{"role": "user", "content": "你好，我是DeepSeek，一个AI助手。"}],
            stream=True
            # max_tokens=128000  # 注释掉以避免思维链被截断
        )
        
        current_reasoning = ""
        current_content = ""
        reasoning_started = False
        content_started = False
        
        for chunk in response:
            # 处理思维链 (reasoning_content)
            if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                reasoning_chunk = chunk.choices[0].delta.reasoning_content
                current_reasoning += reasoning_chunk
                if not reasoning_started:
                    reasoning_started = True
                    yield f"data: {json.dumps({'type': 'reasoning_start'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_chunk}, ensure_ascii=False)}\n\n"
            
            # 处理最终内容 (content)
            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                content_chunk = chunk.choices[0].delta.content
                current_content += content_chunk
                if not content_started:
                    content_started = True
                    # 标记思维链结束
                    if reasoning_started:
                        yield f"data: {json.dumps({'type': 'reasoning_end'}, ensure_ascii=False)}\n\n"
                    yield f"data: {json.dumps({'type': 'content_start'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'content', 'content': content_chunk}, ensure_ascii=False)}\n\n"
        
        # 发送完成信号
        yield f"data: {json.dumps({'type': 'done', 'reasoning_length': len(current_reasoning), 'content_length': len(current_content)}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"

response = StreamingHttpResponse(generate(), content_type='text/event-stream')
response['Cache-Control'] = 'no-cache'
response['X-Accel-Buffering'] = 'no'
print(response.content)