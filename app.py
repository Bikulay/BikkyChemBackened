from flask import Flask, request, jsonify, render_template
import os
import requests

app = Flask(__name__, template_folder="Templates")


# ============================================================
# OPENROUTER SETTINGS
# ============================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():
    return render_template("Index.html")


# ============================================================
# OPENROUTER CONNECTION TEST
# ============================================================

@app.route("/test-ai")
def test_ai():

    if not OPENROUTER_API_KEY:
        return jsonify({
            "status": "error",
            "message": "OPENROUTER_API_KEY is not available in Render."
        }), 500

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://bikkychem.onrender.com",
        "X-Title": "BikkyChem"
    }

    payload = {
        "model": "openrouter/free",
        "messages": [
            {
                "role": "user",
                "content": "Reply with exactly: OpenRouter connection successful."
            }
        ]
    }

    try:

        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:

            return jsonify({
                "status": "error",
                "openrouter_status": response.status_code,
                "message": response.text
            }), 500

        result = response.json()

        answer = result["choices"][0]["message"]["content"]

        return jsonify({
            "status": "success",
            "message": answer
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ============================================================
# ASK ROUTE — TEMPORARY EXISTING FUNCTION
# ============================================================

@app.route("/ask", methods=["POST"])
def ask():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "topic": "No question received",
            "formula": "",
            "steps": [],
            "hints": [
                "Please enter a Chemistry question."
            ]
        })

    question = data.get("question", "").lower().strip()

    # --------------------------------------------------------
    # Temporary Molarity detection
    # --------------------------------------------------------

    molarity_keywords = [
        "molarity",
        "molar",
        "moles",
        "mol",
        "concentration"
    ]

    if any(word in question for word in molarity_keywords):

        return jsonify({

            "topic": "Molarity",

            "formula": "M = n / V",

            "steps": [
                "Calculate the molar mass of the solute.",
                "Calculate the number of moles using n = given mass / molar mass.",
                "Convert the volume of solution into litres.",
                "Apply M = n / V to calculate molarity."
            ],

            "hints": [
                "What quantity do you need before calculating the number of moles?",
                "You need the molar mass of the solute.",
                "Which formula relates mass, molar mass and number of moles?",
                "Use n = given mass / molar mass.",
                "Is the volume given in litres or millilitres?",
                "Convert mL into L before using the molarity formula.",
                "Which formula connects moles and volume with molarity?",
                "Use M = n / V."
            ]
        })

    # --------------------------------------------------------
    # Topic not yet available
    # --------------------------------------------------------

    return jsonify({

        "topic": "Topic not yet available",

        "formula": "The formula will be provided after identifying the topic.",

        "steps": [
            "Identify the Chemistry topic involved in the question.",
            "Recall the relevant concept.",
            "Select the appropriate formula.",
            "Proceed step by step."
        ],

        "hints": [
            "Which Chemistry chapter does your question belong to?",
            "Identify the quantity that is being asked.",
            "Recall the definition of the relevant concept."
        ]
    })


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
