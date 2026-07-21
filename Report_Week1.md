# Day 1

## 1 深化对Python的理解

### 异常中断处理

**raise** 关键词抛出异常进行系统调用或者说错误处理

try except结构中其中某行发生异常，Python 会：
1. 立即停止执行 try 中剩余代码。
1. 创建或接收一个异常对象。
1. 判断它是否属于 Exception。
1. 将异常对象赋给变量 error。
1. 执行 except 内的代码。

**Exception** 不会捕获所有 Python 退出事件。KeyboardInterrupt、SystemExit 等直接继承自BaseException，通常不应该被这种通用处理吞掉。

### 对输入的处理
```python
>>> value=input()

>>> print(repr(value))
''
>>> value=input()     
^Z
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
EOFError
```

用户按回车：读取到 "\n" -> input() 返回 ""
输入流结束：读取不到任何字符 -> input() 抛出 EOFError

## 2 DeepSeek API调用

response.choices[0].message得到输出格式：
DeepSeek: ChatCompletionMessage(content='Hello! How can I help you today?', refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=None)
response.choices[0].message.content输出格式：
Hello! How can I help you today?

## 3 LLM 调用的函数
### json.dumps()

json库中调用的函数
将Python对象转换为json格式字符串 function中的s imply string类型
```ensure_ascii=False #用于保留中文```

### model_dump

OPENAI库中调用的函数
用于 [converting a model to a dictionary.](https://pydantic.dev/docs/validation/2.4/concepts/serialization/#modelmodel_dump)

## 对计划书的回答
**Q:如果LLM回复中包含工具调用请求，循环怎么处理？**
A:response增加tools参数作为一次特定的消息传递，以assistant角色输出
你: 今天几号

ChatCompletionMessage(content='', refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_00_EstapS8Cs24ld1TUv3jh7457', function=Function(arguments='{}', name='get_current_time'), type='function', index=0)])

[调用工具 get_current_time: {"current_time": "2026-07-21T19:48:39+08:00"}]
DeepSeek: 今天是 **2026年7月21日，星期二**。

**Q:如果LLM回复被截断（finish_reason: length），循环怎么恢复？**
A:My Version：通过message的回退(pop或delete操作)将用户和LLM的本轮回答都撤回，通过下一次用户的提问恢复循环
Codex Version：finish_reason 有四个 ：{"stop","length","tool_calls","content_filter"}
针对length问题又有两个原因：输出长度不够，上下文不够
输出长度不够采用以下操作：
1. 保存已经生成的部分回复。
1. 把部分回复加入 messages。
1. 添加“从中断处继续”的用户消息。
1. 再次调用模型。
1. 拼接多次返回的内容。
1. 设置最大重试次数，防止无限循环。

> [!TIP]
> 在再次调用模型中是通过此前的message接上用户消息再接上LLM的消息接龙来实现了，实际上就是LLM的工作流程
> 可能会出现与上一段回答相似片段，则需要进行相似度比对的额外检验

如果采用重新生成的操作会导致长度不够的问题依然出现，只是输出的片段会有差异

## 问题

1. client.chat.completions.create函数究竟如何执行
2. 测试脚本如何设计