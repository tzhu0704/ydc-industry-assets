"""Generate -> check in code -> repair once. Shared by the scenarios that ask a model for text."""

from you_api import chat


def checked_chat(prompt: str, check, retries: int = 1):
    """Return (text, attempts). `check(text)` returns a list of problems; an empty list passes.

    On failure the problems are appended to the prompt and the model is asked once more.
    """
    attempts, problems, text = [], [], ""
    for i in range(retries + 1):
        p = prompt if i == 0 else (prompt + "\n\n上一版未通過程式校驗，問題如下，請修正後重新輸出完整內容：\n- " + "\n- ".join(problems))
        text = chat(p)["choices"][0]["message"]["content"]
        problems = check(text)
        attempts.append({"attempt": i + 1, "problems": problems})
        if not problems:
            break
    return text, attempts
