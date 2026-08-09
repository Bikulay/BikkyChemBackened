from flask import Flask, request, jsonify, render_template
import os
import json
import urllib.request
import urllib.error

app = Flask(__name__, template_folder="Templates")

# ============================================================
# OPENROUTER CONFIGURATION
# ============================================================

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():
    return render_template("Index.html")


# ============================================================
# OPENROUTER TEST
# ============================================================

@app.route("/test-ai")
def test_ai():

    if not OPENROUTER_API_KEY:
        return jsonify({
            "status": "error",
            "message": "OPENROUTER_API_KEY is not configured in Render."
        }), 500

    headers = {
        "Authorization": "Bearer " + OPENROUTER_API_KEY,
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

        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            OPENROUTER_URL,
            data=data,
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=60) as response:

            response_data = response.read().decode("utf-8")
            result = json.loads(response_data)

        answer = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        return jsonify({
            "status": "success",
            "message": answer
        })

    except urllib.error.HTTPError as e:

        error_body = e.read().decode("utf-8", errors="replace")

        return jsonify({
            "status": "error",
            "openrouter_status": e.code,
            "message": error_body
        }), 500

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ============================================================
# ASK ROUTE
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

    question = str(
        data.get("question", "")
    ).lower().strip()


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
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
