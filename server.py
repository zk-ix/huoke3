"""
获客3 本地开发服务器
启动: python server.py
访问: http://localhost:8888
"""
import http.server
import json
import urllib.request
import urllib.error
import os, sys, traceback

PORT = 8899
DOUBAO_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
DOUBAO_KEY = "ark-d1754a1a-98cd-4db6-8efa-d21e6c149359-01bf9"
DOUBAO_MODEL = "ep-20260528232335-78k69"

DEEPSEEK_URL = "https://api.deepseek.com/anthropic/v1/messages"
DEEPSEEK_KEY = "sk-ecf8b540e2bc4e2fa3e0d4cd3f5d34e8"


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/diagnose":
            return self.send_json(404, {"error": "not found"})

        try:
            body = self._read_json_body()
        except Exception as e:
            return self.send_json(400, {"error": f"请求解析失败: {e}"})

        try:
            result = self._diagnose(body)
            if result:
                self.send_json(200, result)
            else:
                self.send_json(502, {"error": "诊断服务暂不可用，请稍后重试"})
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            self.send_json(500, {"error": str(e)})

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = bytearray()
        while len(raw) < length:
            chunk = self.rfile.read(length - len(raw))
            if not chunk:
                break
            raw.extend(chunk)
        return json.loads(bytes(raw).decode("utf-8"))

    def _diagnose(self, body):
        backend = body.get("_backend", "doubao")
        if backend == "doubao":
            result = self._call_doubao(body)
            if result:
                return result
            print("[INFO] 豆包不可用，回退到 DeepSeek", flush=True)
        return self._call_deepseek(body)

    def _call_doubao(self, body):
        data = json.dumps({
            "model": DOUBAO_MODEL,
            "max_tokens": body.get("max_tokens", 2000),
            "temperature": body.get("temperature", 0.7),
            "messages": body.get("messages", []),
        }, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(DOUBAO_URL, data=data, method="POST")
        req.add_header("Content-Type", "application/json; charset=utf-8")
        req.add_header("Authorization", "Bearer " + DOUBAO_KEY)

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                r = json.loads(resp.read())
                content = r.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"content": content} if content else None
        except urllib.error.HTTPError as e:
            err = e.read().decode(errors="replace")
            print(f"[豆包] HTTP {e.code}: {err[:300]}", flush=True)
            return None
        except Exception as e:
            print(f"[豆包] {e}", flush=True)
            return None

    def _call_deepseek(self, body):
        messages = body.get("messages", [])
        system_prompt = ""
        user_msgs = []

        for m in messages:
            role = m.get("role", "")
            content = m.get("content", "")
            if role == "system":
                system_prompt = content if isinstance(content, str) else str(content)
            elif role == "user":
                if isinstance(content, list):
                    texts = [p["text"] for p in content if p.get("type") == "text"]
                    m = dict(m)
                    m["content"] = " ".join(texts) if texts else "[图片]"
                user_msgs.append(m)
            else:
                user_msgs.append(m)

        data = json.dumps({
            "model": "deepseek-v4-pro",
            "max_tokens": body.get("max_tokens", 2000),
            "temperature": body.get("temperature", 0.7),
            "system": system_prompt,
            "messages": user_msgs,
        }, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(DEEPSEEK_URL, data=data, method="POST")
        req.add_header("Content-Type", "application/json; charset=utf-8")
        req.add_header("x-api-key", DEEPSEEK_KEY)

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                r = json.loads(resp.read())
                for block in r.get("content", []):
                    if block.get("type") == "text":
                        return {"content": block["text"]}
                print("[DeepSeek] No text in response", flush=True)
                return None
        except Exception as e:
            print(f"[DeepSeek] {e}", flush=True)
            return None

    def send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"获客3 诊断服务: http://localhost:{PORT}", flush=True)
    http.server.HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
