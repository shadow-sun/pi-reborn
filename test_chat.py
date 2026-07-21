import io
import os
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

import chat


def make_response(content, finish_reason):
    assistant = SimpleNamespace(content=content, tool_calls=None)
    choice = SimpleNamespace(message=assistant, finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice])


class FakeCompletions:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        return next(self.responses)


class RecoveryTest(unittest.TestCase):
    def test_joins_truncated_responses_without_removing_duplicates(self):
        completions = FakeCompletions([
            make_response("第一段结尾是重复内容。", "length"),
            make_response("重复内容。第二段仍未结束。", "length"),
            make_response("第三段完成。", "stop"),
        ])
        client = SimpleNamespace(
            chat=SimpleNamespace(completions=completions)
        )
        output = io.StringIO()

        with (
            patch.dict(os.environ, {"DEEPSEEK_API_KEY": "fake-key"}),
            patch.object(chat, "OpenAI", return_value=client),
            patch("builtins.input", side_effect=["生成长回答", "exit"]),
            patch("sys.stdout", output),
        ):
            chat.main()

        text = output.getvalue()
        expected = "第一段结尾是重复内容。重复内容。第二段仍未结束。第三段完成。"
        self.assertIn(f"DeepSeek: {expected}", text)
        self.assertEqual(len(completions.calls), 3)
        self.assertIn("tools", completions.calls[0])
        self.assertNotIn("tools", completions.calls[1])
        self.assertEqual(
            [message["role"] for message in completions.calls[1]["messages"]],
            ["user", "assistant", "user"],
        )
        self.assertEqual(
            completions.calls[1]["messages"][-1]["content"],
            chat.CONTINUE_PROMPT,
        )
        print("\n捕获到的程序输出：\n" + text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
