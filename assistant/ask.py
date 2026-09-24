"""
Ask the project assistant from the command line.

Uses the same project notes (docs/knowledge/chunks.json) and the same keyword search as the web page, and any
OpenAI-compatible model server: Ollama, LM Studio, llama.cpp server, vLLM.

usage
  python ask.py "Why use 40-ft squares?"
  python ask.py                               interactive: ask several questions, 'q' to quit
  python ask.py --notes "station 74"          only show the matching notes (no model needed)
options
  --url    chat endpoint   (default http://localhost:11434/v1/chat/completions, i.e. Ollama)
  --model  model name      (default qwen3:14b; any model pulled on the server)
  --step   1-10            treat the question as being about that step of the walk-through
"""
import argparse, json, math, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNKS = os.path.join(HERE, "..", "docs", "knowledge", "chunks.json")
STOP = set(("a an the and or but if of to in on at by for with from as is are was were be been being it its this that these "
            "those there here what which who whom why how when where do does did doing can could would should will shall may "
            "might must i you we they he she them our your my me us about into over under than then so such not no yes also just "
            "only very much many more most some any each every all both between within without per via up down out off again "
            "once same other own").split())
SYN = {"rectangle": "square", "rectangles": "squares", "box": "square", "boxes": "squares", "window": "square",
       "windows": "squares", "laser": "lidar", "lasers": "lidar", "centerline": "centreline", "center": "centre",
       "centers": "centres", "color": "colour", "colors": "colours", "gray": "grey", "eroding": "erosion",
       "eroded": "erosion", "erode": "erosion", "meter": "metre", "meters": "metres", "dtm": "dem"}


def stem(w):
    if re.match(r"^\d", w):
        return w
    if len(w) > 5 and w.endswith("ing"):
        w = w[:-3]
    elif len(w) > 4 and (w.endswith("ies") or w.endswith("ied")):
        w = w[:-3] + "y"
    elif len(w) > 4 and w.endswith("ed"):
        w = w[:-2]
    elif len(w) > 4 and re.search(r"(ss|x|z|ch|sh)es$", w):
        w = w[:-2]
    elif len(w) > 3 and w.endswith("s") and not re.search(r"(ss|us|is)$", w):
        w = w[:-1]
    if len(w) >= 4 and w.endswith("e"):
        w = w[:-1]
    return w


def tokens(text, expand=False):
    out = []
    for w in re.split(r"[^a-z0-9.\-]+", text.lower()):
        w = w.strip(".-")
        if not w or w in STOP:
            continue
        if expand and w in SYN:
            out.append(stem(SYN[w]))
        out.append(stem(w))
        if "-" in w:
            out += [stem(p) for p in w.split("-") if p and p not in STOP]
    return out


class Notes:
    def __init__(self, path):
        self.chunks = json.load(open(path, encoding="utf-8"))
        self.df, self.tf = {}, []
        for c in self.chunks:
            toks = tokens(c["title"] + " " + c["title"] + " " + c["text"])
            tf = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            for t in tf:
                self.df[t] = self.df.get(t, 0) + 1
            self.tf.append((tf, len(toks)))
        self.avgdl = sum(n for _, n in self.tf) / len(self.tf)

    def search(self, query, step=None, budget=2600):
        q, n, k1, b = set(tokens(query, True)), len(self.chunks), 1.2, 0.75
        scored = []
        for c, (tf, dl) in zip(self.chunks, self.tf):
            s = 0.0
            for t in q:
                f = tf.get(t)
                if f:
                    idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                    s += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * dl / self.avgdl))
            if s > 0 and step is not None and step in c["steps"]:
                s *= 1.35
            scored.append((s, c))
        scored.sort(key=lambda x: -x[0])
        picked = [c for s, c in scored if s > 0][:8] or [c for c in self.chunks if step is not None and step in c["steps"]][:3]
        out, words = [], 0
        for c in picked:
            w = len(c["text"].split())
            if out and words + w > budget:
                continue
            out.append(c)
            words += w
            if len(out) >= 6:
                break
        return out


def system_prompt(hits):
    notes = "\n\n".join(f"[{i + 1}] {c['title']}\n{c['text']}" for i, c in enumerate(hits))
    return ('You are the project assistant for a desktop study of the Minisceongo Creek "M" bend behind Samsondale Avenue in '
            "West Haverstraw, New York. The study measured how the creek's south bank (the house side) moved between two "
            "lidar surveys (19 November 2011 and 15 April 2022).\n\nRules:\n"
            '- Answer ONLY from the project notes below. If the notes do not cover the question, say "The project notes '
            "don't cover that.\" and, if useful, say what they do cover.\n"
            "- Use plain, simple English for someone who is not a specialist.\n"
            "- Keep it short: 2 to 5 sentences, or up to 5 short bullets.\n"
            "- Copy numbers, units (feet) and station numbers exactly from the notes. Never invent numbers.\n\n"
            "Project notes:\n" + notes)


def ask_model(url, model, messages):
    body = json.dumps({"model": model, "messages": messages, "stream": True, "temperature": 0.3, "max_tokens": 800}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    text, thinking = "", False
    with urllib.request.urlopen(req, timeout=600) as r:
        for raw in r:
            line = raw.decode("utf-8", "ignore").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                d = json.loads(data)["choices"][0]["delta"].get("content") or ""
            except (ValueError, KeyError, IndexError):
                continue
            text += d
            if "<think>" in d:
                thinking = True
            if not thinking:
                print(d, end="", flush=True)
            if "</think>" in d:
                thinking = False
    print()
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def main():
    ap = argparse.ArgumentParser(description="Ask the Minisceongo Creek project assistant.")
    ap.add_argument("question", nargs="*")
    ap.add_argument("--url", default=os.environ.get("ASSISTANT_URL", "http://localhost:11434/v1/chat/completions"))
    ap.add_argument("--model", default=os.environ.get("ASSISTANT_MODEL", "qwen3:14b"))
    ap.add_argument("--notes", action="store_true", help="only show the matching notes")
    ap.add_argument("--step", type=int, help="walk-through step (1-10) the question is about")
    a = ap.parse_args()
    notes = Notes(CHUNKS)
    step = a.step - 1 if a.step else None
    history = []

    def one(q):
        hits = notes.search(q, step)
        if a.notes:
            for c in hits[:3]:
                print(f"\n## {c['title']}\n{c['text']}")
            return
        msgs = [{"role": "system", "content": system_prompt(hits)}] + history[-4:] + [{"role": "user", "content": q}]
        try:
            ans = ask_model(a.url, a.model, msgs)
        except Exception as e:
            print(f"Could not reach the model server at {a.url}: {e}\n(Start it, e.g. 'ollama serve', or use --notes.)")
            return
        history.extend([{"role": "user", "content": q}, {"role": "assistant", "content": ans}])
        print("Sources: " + "; ".join(c["title"] for c in hits))

    if a.question:
        one(" ".join(a.question))
        return
    print("Ask about the study ('q' to quit).")
    while True:
        try:
            q = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in ("q", "quit", "exit"):
            break
        if q:
            one(q)


if __name__ == "__main__":
    sys.exit(main())
