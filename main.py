import json
import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Groq API kalitini atrof-muhitdan o'qiydi
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "gsk_o'zingizning_groq_api_kalitingizni_shu_yerga_yozing")

SYSTEM_PROMPT = """
You are an expert Senior Examiner for the Yunus Emre Enstitüsü Turkish Proficiency Exam (TYS).
Evaluate the submitted Turkish essay based on TYS B2 writing criteria.

You MUST respond strictly in valid JSON format matching this exact schema:
{
  "total_score": int (0-100),
  "cefr_level": string (e.g. "A1", "A2", "B1", "B2", "C1"),
  "feedback_summary_uzbek": [list of general feedback points in UZBEK language],
  "grammar_errors": [
    {
      "original": "original incorrect phrase or sentence",
      "correction": "corrected version",
      "explanation_uz": "explanation of the grammar error in UZBEK language"
    }
  ],
  "recommended_topics_uz": [list of specific Turkish grammar topics or vocabulary skills the student needs to review, in UZBEK language]
}
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TÜRKÇE USTOZ - Smart Writing Platform</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #f8fafc; color: #1e293b; padding: 15px; }
        
        .editor-container { max-width: 800px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); overflow: hidden; }
        
        .editor-header { display: flex; justify-content: space-between; align-items: center; background: #9f1239; color: white; padding: 12px 20px; font-size: 14px; font-weight: 600; flex-wrap: wrap; gap: 10px; }
        .header-title-box { display: flex; align-items: center; gap: 8px; }
        .badge-b2 { background: #ffe4e6; color: #9f1239; padding: 3px 8px; border-radius: 4px; font-weight: 700; text-transform: uppercase; font-size: 12px; }
        
        .task-box { background: #fff1f2; border-bottom: 1px solid #fecdd3; padding: 15px 20px; font-size: 14px; color: #881337; }
        
        .editor-body { padding: 20px; }
        textarea { width: 100%; height: 200px; border: 1px solid #cbd5e1; border-radius: 8px; padding: 15px; font-size: 16px; line-height: 1.6; color: #334155; resize: vertical; outline: none; }
        textarea:disabled { background-color: #f1f5f9; cursor: not-allowed; }
        
        .turkish-keyboard { display: flex; gap: 6px; margin-top: 12px; align-items: center; background: #f1f5f9; padding: 10px; border-radius: 6px; flex-wrap: wrap; }
        .keyboard-title { font-size: 12px; font-weight: 700; color: #64748b; width: 100%; margin-bottom: 3px; }
        .char-btn { background: white; border: 1px solid #cbd5e1; border-radius: 4px; padding: 6px 10px; font-size: 14px; font-weight: 600; color: #be123c; cursor: pointer; }
        .char-btn:hover { background: #ffe4e6; }
        
        .editor-footer { display: flex; justify-content: flex-end; padding: 0 20px 20px 20px; }
        .btn-submit { background: #be123c; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-size: 15px; font-weight: 700; cursor: pointer; width: 100%; }
        .btn-submit:disabled { background: #94a3b8; cursor: not-allowed; }

        .result-card { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 20px; margin: 0 20px 20px 20px; }
        .result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; flex-wrap: wrap; gap: 10px; }
        .result-title { color: #9f1239; font-size: 18px; font-weight: 700; }
        .result-badges-group { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .result-badge { background: #be123c; color: white; padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 13px; display: inline-block; white-space: nowrap; }
        .result-badge-dark { background: #0f172a; }

        .section-title { font-size: 15px; font-weight: 700; color: #1e293b; margin: 15px 0 8px 0; }
        .feedback-list { padding-left: 20px; font-size: 14px; color: #334155; line-height: 1.6; }
        
        .error-item { background: #fff1f2; border-left: 4px solid #be123c; padding: 10px 12px; border-radius: 4px; margin-bottom: 10px; font-size: 14px; line-height: 1.5; }
        .error-item .wrong { color: #e11d48; text-decoration: line-through; font-weight: 600; word-break: break-word; }
        .error-item .correct { color: #16a34a; font-weight: 700; word-break: break-word; }
        .error-item .exp { font-size: 13px; color: #475569; margin-top: 5px; }

        .topic-badge { display: inline-block; background: #e0f2fe; color: #0369a1; padding: 5px 10px; border-radius: 6px; font-size: 13px; font-weight: 600; margin: 4px 4px 4px 0; }

        .chat-section { background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px; }
        .chat-title { font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }
        .chat-history { max-height: 250px; overflow-y: auto; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
        .chat-msg { margin-bottom: 10px; font-size: 14px; line-height: 1.4; }
        .chat-msg.user { text-align: right; color: #9f1239; font-weight: 600; }
        .chat-msg.ai { text-align: left; color: #1e293b; background: #f1f5f9; padding: 8px 12px; border-radius: 8px; display: inline-block; max-width: 85%; }
        
        .chat-input-box { display: flex; gap: 8px; }
        .chat-input { flex: 1; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; outline: none; font-size: 14px; }
        .btn-chat { background: #0f172a; color: white; border: none; padding: 10px 18px; border-radius: 6px; font-weight: 600; cursor: pointer; white-space: nowrap; }
    </style>
</head>
<body>

<div class="editor-container">
    <div class="editor-header">
        <div class="header-title-box">
            <span class="badge-b2">TYS B2</span>
            <span>Sınav Görevi</span>
        </div>
        <div>Süre: <span id="timer">30:00</span> | Kelime: <span id="wordCount">0</span> / 200</div>
    </div>

    <div class="task-box">
        <strong>Konu:</strong> <em>"Teknolojinin eğitimdeki yeri ve gelecekteki olası etkileri hakkında bir kompozisyon yazınız."</em>
    </div>

    <div class="editor-body">
        <textarea id="essayInput" placeholder="Türkçe kompozisyonunuzu buraya yazmaya başlayın..."></textarea>
        
        <div class="turkish-keyboard">
            <span class="keyboard-title">Türkçe Karakterler:</span>
            <button class="char-btn" onclick="insertChar('ğ')">ğ</button>
            <button class="char-btn" onclick="insertChar('Ğ')">Ğ</button>
            <button class="char-btn" onclick="insertChar('ş')">ş</button>
            <button class="char-btn" onclick="insertChar('Ş')">Ş</button>
            <button class="char-btn" onclick="insertChar('ç')">ç</button>
            <button class="char-btn" onclick="insertChar('Ç')">Ç</button>
            <button class="char-btn" onclick="insertChar('ı')">ı</button>
            <button class="char-btn" onclick="insertChar('I')">I</button>
            <button class="char-btn" onclick="insertChar('i')">i</button>
            <button class="char-btn" onclick="insertChar('İ')">İ</button>
            <button class="char-btn" onclick="insertChar('ö')">ö</button>
            <button class="char-btn" onclick="insertChar('Ö')">Ö</button>
            <button class="char-btn" onclick="insertChar('ü')">ü</button>
            <button class="char-btn" onclick="insertChar('Ü')">Ü</button>
        </div>
    </div>

    <div id="resultContainer"></div>

    <div class="editor-footer" id="footerButtonBox">
        <button class="btn-submit" onclick="submitEssay()">TYS Yapay Zekaya Gönder</button>
    </div>
</div>

<script>
    const textarea = document.getElementById('essayInput');
    const wordCountSpan = document.getElementById('wordCount');
    const timerElement = document.getElementById('timer');
    let timeInSeconds = 1800;
    let currentEssay = "";

    function insertChar(char) {
        if (textarea.disabled) return;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;
        textarea.value = text.substring(0, start) + char + text.substring(end);
        textarea.selectionStart = textarea.selectionEnd = start + 1;
        textarea.focus();
        updateWordCount();
    }

    textarea.addEventListener('input', updateWordCount);

    function updateWordCount() {
        const text = textarea.value.trim();
        wordCountSpan.innerText = text ? text.split(/\s+/).length : 0;
    }

    const countdown = setInterval(() => {
        if (timeInSeconds <= 0) {
            clearInterval(countdown);
            timerElement.innerText = "00:00";
            textarea.disabled = true;
            alert("Süre doldu! Metniniz değerlendirmeye gönderiliyor.");
            submitEssay();
            return;
        }
        timeInSeconds--;
        const minutes = Math.floor(timeInSeconds / 60);
        const seconds = timeInSeconds % 60;
        timerElement.innerText = `${minutes < 10 ? '0' : ''}${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }, 1000);

    async function submitEssay() {
        const userText = textarea.value;
        const resultDiv = document.getElementById('resultContainer');
        const submitBtn = document.querySelector('.btn-submit');
        
        if (!userText.trim()) {
            alert("Lütfen önce bir metin yazın!");
            return;
        }

        currentEssay = userText;
        submitBtn.innerText = "Tahlil qilinmoqda (Kuting...)...";
        submitBtn.disabled = true;
        resultDiv.innerHTML = "";

        try {
            const response = await fetch("/api/v1/evaluate-essay", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    topic: "Teknolojinin eğitimdeki yeri ve gelecekteki olası etkileri",
                    target_level: "B2",
                    essay_text: userText
                })
            });

            let result = await response.json();
            if (typeof result === 'string') result = JSON.parse(result);

            if (response.status !== 200 || result.error) {
                alert("Xatolik: " + (result.error || "Server xatosi"));
                submitBtn.innerText = "TYS Yapay Zekaya Gönder";
                submitBtn.disabled = false;
                return;
            }

            const feedbacks = (result.feedback_summary_uzbek || []).map(f => `<li>${f}</li>`).join('');
            
            const errors = (result.grammar_errors || []).map(e => `
                <div class="error-item">
                    <span class="wrong">${e.original}</span> ➔ <span class="correct">${e.correction}</span>
                    <div class="exp">📌 ${e.explanation_uz}</div>
                </div>
            `).join('') || '<p style="font-size: 13px; color: #16a34a;">Ayon grammatik xatolar topilmadi!</p>';

            const topics = (result.recommended_topics_uz || []).map(t => `<span class="topic-badge">📖 ${t}</span>`).join('');

            resultDiv.innerHTML = `
                <div class="result-card">
                    <div class="result-header">
                        <div class="result-title">Tahlil Natijasi</div>
                        <div class="result-badges-group">
                            <span class="result-badge">Daraja: ${result.cefr_level || 'N/A'}</span>
                            <span class="result-badge result-badge-dark">Ball: ${result.total_score}/100</span>
                        </div>
                    </div>

                    <div class="section-title">💡 Umumiy Xulosa va Tavsiyalar:</div>
                    <ul class="feedback-list">${feedbacks}</ul>

                    <div class="section-title">🔍 Aniqlangan Xatolar va Tuzatishlar:</div>
                    ${errors}

                    <div class="section-title">📚 Qayta Takrorlash Tavsiya Etiladigan Mavzular:</div>
                    <div>${topics}</div>
                </div>

                <div class="chat-section">
                    <div class="chat-title">🤖 AI Ustozdan Qo'shimcha Savol So'ring</div>
                    <div class="chat-history" id="chatHistory">
                        <div class="chat-msg ai">Inshoingiz tahlil qilindi! Natijalar va xatolar bo'yicha tushunmagan savollaringiz bo'lsa, so'rashingiz mumkin.</div>
                    </div>
                    <div class="chat-input-box">
                        <input type="text" id="chatInput" class="chat-input" placeholder="Masalan: Nega bu yerda 'ki' alohida yozilishi kerak?" onkeypress="handleKeyPress(event)">
                        <button class="btn-chat" onclick="sendChatMessage()">Yuborish</button>
                    </div>
                </div>
            `;

            document.getElementById('footerButtonBox').style.display = 'none';

        } catch (error) {
            alert("Server bilan bog'lanishda xatolik!");
            submitBtn.innerText = "TYS Yapay Zekaya Gönder";
            submitBtn.disabled = false;
        }
    }

    function handleKeyPress(e) {
        if (e.key === 'Enter') sendChatMessage();
    }

    async function sendChatMessage() {
        const input = document.getElementById('chatInput');
        const history = document.getElementById('chatHistory');
        const question = input.value.trim();

        if (!question) return;

        const essayText = document.getElementById('essayInput').value || currentEssay;

        history.innerHTML += `<div class="chat-msg user">${question}</div>`;
        input.value = "";
        history.scrollTop = history.scrollHeight;

        const loadingId = 'loading-' + Date.now();
        history.innerHTML += `<div class="chat-msg ai" id="${loadingId}">Javob yozilmoqda...</div>`;
        history.scrollTop = history.scrollHeight;

        try {
            const response = await fetch("/api/v1/chat-essay", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    essay_text: essayText,
                    user_question: question
                })
            });

            const data = await response.json();
            const loadingElem = document.getElementById(loadingId);
            
            if (loadingElem) {
                loadingElem.innerText = data.reply || data.error || "Javob olib bo'lmadi.";
            }
            history.scrollTop = history.scrollHeight;
        } catch (err) {
            const loadingElem = document.getElementById(loadingId);
            if (loadingElem) {
                loadingElem.style.color = "red";
                loadingElem.innerText = "Ulanishda xatolik yuz berdi!";
            }
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
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30)
        res_data = res.json()
        
        if 'error' in res_data:
            return jsonify({"error": res_data['error']['message']}), 500
            
        raw_content = res_data['choices'][0]['message']['content']
        result_json = json.loads(raw_content)
        
        return jsonify(result_json), 200
    except requests.exceptions.Timeout:
        return jsonify({"error": "AI javob berishda vaqt tugadi. Qaytadan urinib ko'ring."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/chat-essay', methods=['POST'])
def chat_essay():
    data = request.get_json() or {}
    essay_text = data.get('essay_text', '')
    user_question = data.get('user_question', '')

    if not user_question.strip():
        return jsonify({"error": "Savol kiritilmadi!"}), 400

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    context_text = essay_text if essay_text.strip() else "Foydalanuvchi hali insho kiritmagan yoki tahlil xulosasi haqida so'ramoqda."

    system_msg = "You are a friendly, encouraging Turkish language teacher. Answer user questions in clear Uzbek language."
    user_msg = f"Insho/Kontekst: {context_text}\n\nFoydalanuvchi savoli: {user_question}"

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
    }

    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        res_data = res.json()
        
        if 'error' in res_data:
            return jsonify({"reply": f"Groq API xatosi: {res_data['error'].get('message', 'Xatolik')}"}), 200

        reply_text = res_data['choices'][0]['message']['content']
        return jsonify({"reply": reply_text}), 200
    except Exception as e:
        return jsonify({"reply": f"Server xatosi: {str(e)}"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
  
