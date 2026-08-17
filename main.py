import json
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Groq API kalitingizni shu yerga qo'ying:
GROQ_API_KEY = "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"

SYSTEM_PROMPT = """
You are an official Senior Examiner for the Yunus Emre Enstitüsü Turkish Proficiency Exam (TYS).
Evaluate the Turkish essay according to TYS Writing Criteria.
You MUST respond strictly in valid JSON format with keys:
- total_score (int 0-100)
- cefr_level (string)
- feedback_summary_uzbek (array of strings in UZBEK language)
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TÜRKÇE USTOZ - TYS Yazma</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }
        body { background-color: #f8fafc; padding: 15px; }
        .editor-container { max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }
        .editor-header { background: #9f1239; color: white; padding: 12px; font-weight: bold; display: flex; justify-content: space-between; }
        .task-box { background: #fff1f2; padding: 12px; font-size: 14px; color: #881337; border-bottom: 1px solid #fecdd3; }
        .editor-body { padding: 15px; }
        textarea { width: 100%; height: 200px; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; font-size: 16px; outline: none; }
        .turkish-keyboard { display: flex; gap: 5px; margin-top: 10px; flex-wrap: wrap; }
        .char-btn { background: #f1f5f9; border: 1px solid #cbd5e1; padding: 8px 12px; font-weight: bold; color: #be123c; border-radius: 4px; cursor: pointer; }
        .editor-footer { padding: 15px; text-align: right; }
        .btn-submit { background: #be123c; color: white; border: none; padding: 12px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>

<div class="editor-container">
    <div class="editor-header">
        <div>TYS B2 Sınav Görevi</div>
        <div>Süre: <span id="timer">30:00</span> | Kelime: <span id="wordCount">0</span></div>
    </div>
    <div class="task-box">
        <strong>Konu:</strong> <em>Teknolojinin eğitimdeki yeri ve gelecekteki olası etkileri hakkında bir kompozisyon yazınız.</em>
    </div>
    <div class="editor-body">
        <textarea id="essayInput" placeholder="Kompozisyonunuzu buraya yazın..."></textarea>
        <div class="turkish-keyboard">
            <button class="char-btn" onclick="insertChar('ğ')">ğ</button>
            <button class="char-btn" onclick="insertChar('ş')">ş</button>
            <button class="char-btn" onclick="insertChar('ç')">ç</button>
            <button class="char-btn" onclick="insertChar('ı')">ı</button>
            <button class="char-btn" onclick="insertChar('ö')">ö</button>
            <button class="char-btn" onclick="insertChar('ü')">ü</button>
            <button class="char-btn" onclick="insertChar('Ğ')">Ğ</button>
            <button class="char-btn" onclick="insertChar('Ş')">Ş</button>
            <button class="char-btn" onclick="insertChar('Ç')">Ç</button>
            <button class="char-btn" onclick="insertChar('İ')">İ</button>
            <button class="char-btn" onclick="insertChar('Ö')">Ö</button>
            <button class="char-btn" onclick="insertChar('Ü')">Ü</button>
        </div>
    </div>
    <div class="editor-footer">
        <button class="btn-submit" onclick="submitEssay()">TYS Yapay Zekaya Gönder</button>
    </div>
</div>

<script>
    const textarea = document.getElementById('essayInput');
    function insertChar(c) {
        const start = textarea.selectionStart;
        textarea.value = textarea.value.substring(0, start) + c + textarea.value.substring(textarea.selectionEnd);
        textarea.selectionStart = textarea.selectionEnd = start + 1;
        textarea.focus();
        updateWordCount();
    }
    textarea.addEventListener('input', updateWordCount);
    function updateWordCount() {
        const text = textarea.value.trim();
        document.getElementById('wordCount').innerText = text ? text.split(/\s+/).length : 0;
    }

    async function submitEssay() {
        const userText = textarea.value;
        if (!userText.trim()) return alert("Lütfen önce bir metin yazın!");

        const btn = document.querySelector('.btn-submit');
        btn.innerText = "Değerlendiriliyor...";
        btn.disabled = true;

        try {
            const res = await fetch("/api/v1/evaluate-essay", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    topic: "Teknolojinin eğitimdeki yeri",
                    essay_text: userText
                })
            });
            
            const data = await res.json();
            
            if (res.status !== 200 || data.error) {
                alert("Xatolik: " + (data.error || "Server xatosi"));
                return;
            }

            alert(`Tahlil Yakunlandi!\\nUmumiy Puan: ${data.total_score} / 100\\nSeviye: ${data.cefr_level}`);
        } catch (e) {
            alert("Xatolik yuz berdi: " + e);
        } finally {
            btn.innerText = "TYS Yapay Zekaya Gönder";
            btn.disabled = false;
        }
    }
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/v1/evaluate-essay', methods=['POST'])
def evaluate_essay():
    data = request.get_json() or {}
    essay_text = data.get('essay_text', '')
    topic = data.get('topic', '')

    if not essay_text.strip():
        return jsonify({"error": "Metin boş olamaz!"}), 400

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Topic: {topic}\nEssay: {essay_text}"}
        ],
        "response_format": {"type": "json_object"}
    }

    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        res_data = res.json()
        
        if 'error' in res_data:
            return jsonify({"error": res_data['error']['message']}), 500
            
        raw_content = res_data['choices'][0]['message']['content']
        result_json = json.loads(raw_content)
        
        return jsonify(result_json), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
