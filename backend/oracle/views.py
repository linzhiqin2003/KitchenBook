from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import requests
import re

class DivinationView(APIView):
    def post(self, request):
        question = request.data.get('question')
        cards_data = request.data.get('cards') # List of {name, position, meaning}
        spread_type = request.data.get('spread_type', 'reading')
        
        if not question or not cards_data:
            return Response({"error": "Missing question or cards"}, status=status.HTTP_400_BAD_REQUEST)

        # Build card list for unified prompt
        card_list = ", ".join([f"{c['name']} ({c['position']})" for c in cards_data])
        
        # Prompt for unified narrative PLUS simple summary
        prompt = f"""The Querent asks: "{question}"

Cards drawn: {card_list}

Provide your reading in TWO parts:

**PART 1 - MYSTICAL INTERPRETATION:**
Provide a flowing, unified interpretation that weaves all the cards together into ONE cohesive narrative. 
DO NOT list each card separately with headers. Tell the story naturally, incorporating what each card reveals as part of a continuous flow.
Keep it mystical, insightful, and under 150 words.

**PART 2 - SIMPLE SUMMARY (用中文):**
用简单易懂的中文写一个2-3句话的总结，直接说明：
1. 当前情况怎么样
2. 应该怎么做
3. 最终结果会如何

格式:
---INTERPRETATION---
(English mystical interpretation here)
---SUMMARY---
(中文简明总结)"""

        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            # Mock response if no key
            return Response({
                "interpretation": "The mists part to reveal your path... The cards speak of transformation and new beginnings. Trust in the journey ahead.",
                "summary": "目前正处于转变期，保持开放心态，迎接新机遇。相信自己的直觉，前方的道路会逐渐明朗。"
            })

        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a mystical Tarot Reader. Provide unified, flowing interpretations with a simple Chinese summary. Follow the exact format requested."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500
                }
            )
            response.raise_for_status()
            ai_text = response.json()['choices'][0]['message']['content']
            
            # Parse interpretation and summary
            interpretation = ai_text
            summary = ""
            
            if "---INTERPRETATION---" in ai_text and "---SUMMARY---" in ai_text:
                parts = ai_text.split("---SUMMARY---")
                interpretation = parts[0].replace("---INTERPRETATION---", "").strip()
                summary = parts[1].strip() if len(parts) > 1 else ""
            elif "SUMMARY" in ai_text or "总结" in ai_text:
                # Fallback parsing
                lines = ai_text.split("\n")
                summary_start = False
                summary_lines = []
                interp_lines = []
                for line in lines:
                    if "SUMMARY" in line.upper() or "总结" in line:
                        summary_start = True
                        continue
                    if summary_start:
                        summary_lines.append(line)
                    else:
                        interp_lines.append(line)
                interpretation = "\n".join(interp_lines).strip()
                summary = "\n".join(summary_lines).strip()
            
            return Response({
                "interpretation": interpretation,
                "summary": summary if summary else "牌阵揭示了你当前所面临的情况，建议保持积极的态度，相信自己的选择。"
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

