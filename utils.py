import subprocess

def call_chatglm(prompt: str, model: str = "EntropyYue/chatglm3") -> str:
    proc = subprocess.Popen(
        ["ollama", "run", model],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    out, err = proc.communicate(prompt)
    if proc.returncode != 0:
        raise RuntimeError(f"Ollama 執行失敗: {err}")
    return out.strip()