import json
import os
from datetime import datetime

from openai import OpenAI


TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "获取运行程序的计算机当前日期、时间和时区",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
}]

MAX_CONTINUATIONS = 5
CONTINUE_PROMPT = "请继续回答。"


def call_tool(name, arguments):
    if name == "get_current_time":
        return json.dumps(
            {"current_time": datetime.now().astimezone().isoformat(timespec="seconds")},
            ensure_ascii=False,
        )
    return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)


def main():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise SystemExit("请先设置环境变量 DEEPSEEK_API_KEY")

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    messages = []
    print("开始对话，输入 exit 或 quit 退出。")

    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if user_input.lower() in {"exit", "quit"}:
            print("再见！")
            break
        if not user_input:
            continue

        checkpoint = len(messages)
        messages.append({"role": "user", "content": user_input})
        partial_reply = ""
        continuation_count = 0
        reply = ""
        try:
            while True:
                if partial_reply:
                    request_messages = messages + [
                        {"role": "assistant", "content": partial_reply},
                        {"role": "user", "content": CONTINUE_PROMPT},
                    ]
                    response = client.chat.completions.create(
                        model="deepseek-chat", messages=request_messages
                    )
                else:
                    response = client.chat.completions.create(
                        model="deepseek-chat", messages=messages, tools=TOOLS
                    )

                choice = response.choices[0]
                assistant = choice.message

                # A truncated tool call may contain invalid JSON, so never execute it.
                if choice.finish_reason == "length":
                    if assistant.tool_calls:
                        raise RuntimeError("工具调用参数生成不完整，已取消本轮请求")
                    partial_reply += assistant.content or ""
                    continuation_count += 1
                    if continuation_count >= MAX_CONTINUATIONS:
                        break
                    continue

                if partial_reply:
                    reply = partial_reply + (assistant.content or "")
                    messages.append({"role": "assistant", "content": reply})
                    break

                messages.append(assistant.model_dump(exclude_none=True))
                if not assistant.tool_calls:
                    reply = assistant.content or ""
                    break

                for tool_call in assistant.tool_calls:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                    result = call_tool(tool_call.function.name, arguments)
                    print(assistant)
                    print("\n")
                    print(f"[调用工具 {tool_call.function.name}: {result}]")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
        except Exception as error:
            del messages[checkpoint:]
            print(f"请求失败: {type(error).__name__}: {error}")
            continue

        if continuation_count >= MAX_CONTINUATIONS:
            del messages[checkpoint:]
            print(f"DeepSeek（未完成）: {partial_reply}")
            print(f"[连续 {MAX_CONTINUATIONS} 段仍未完成，本轮未保存。]")
            continue

        print(f"DeepSeek: {reply}")


if __name__ == "__main__":
    main()
