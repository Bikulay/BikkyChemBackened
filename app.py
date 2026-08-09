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
# OPENROUTER AI FUNCTION
# ============================================================

def ask_openrouter(question):

    if not OPENROUTER_API_KEY:
        raise Exception(
            "OPENROUTER_API_KEY is not configured in Render."
        )

    system_prompt = """
You are BikkyChem, an educational Chemistry guidance engine.

Your purpose is NOT to act like an ordinary chatbot.

You must help the student LEARN how to solve the Chemistry problem.

For every Chemistry question:

1. Identify the exact Chemistry topic.
2. Identify the relevant concept.
3. Provide the appropriate formula or chemical equation when applicable.
4. Identify the quantities/data required.
5. Give logical step-by-step guidance.
6. Give progressive hints that help the student think.
7. Give feedback explaining what the student should check.
8. Do NOT directly provide the final numerical answer to a numerical problem.
9. Do NOT perform the complete calculation for the student.
10. Do not invent a formula.
11. If several formulas are possible, select the most appropriate one and explain why.
12. If the question is conceptual and no formula is required, clearly state that.
13. If the question is incomplete, identify the missing information.
14. Keep the explanation suitable for CBSE Class XI-XII Chemistry students.
15. Use scientifically correct Chemistry terminology.
16. Do not assume that every question is about Molarity.

IMPORTANT:
Return ONLY valid JSON.

Use exactly this structure:

{
  "topic": "Exact Chemistry topic",
  "concept": "Main concept involved",
  "formula": "Relevant formula or chemical equation",
  "given": [
    "Important quantity/data given in the question"
  ],
  "required": [
    "Quantity or result the student needs to determine"
  ],
  "steps": [
    "Step 1 guidance",
    "Step 2 guidance",
    "Step 3 guidance"
  ],
  "hints": [
    "Progressive hint 1",
    "Progressive hint 2",
    "Progressive hint 3",
    "Progressive hint 4"
  ],
  "feedback": [
    "Important thing the student should check",
    "Common mistake to avoid"
  ],
  "final_answer": ""
}

The "final_answer" field MUST remain empty.

For numerical problems, never put the final numerical result in any field.

For conceptual questions, explain the concept through the steps and hints rather than giving an unnecessarily long answer.
"""

    payload = {
        "model": "openrouter/free",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "temperature": 0.2
    }

    data = json.dumps(payload).encode("utf-8")

    headers = {
        "Authorization": "Bearer " + OPENROUTER_API_KEY,
        "Content-Type": "application/json",
        "HTTP-Referer": "https://bikkychem.onrender.com",
        "X-Title": "BikkyChem"
    }

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=data,
        headers=headers,
        method="POST"
    )

    try:

        with urllib.request.urlopen(req, timeout=90) as response:

            response_data = response.read().decode("utf-8")

        result = json.loads(response_data)

        content = (
            result
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        if not content:
            raise Exception(
                "OpenRouter returned an empty response."
            )

        # ----------------------------------------------------
        # Remove possible Markdown code fences
        # ----------------------------------------------------

        content = content.strip()

        if content.startswith("```json"):
            content = content[7:]

        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        # ----------------------------------------------------
        # Convert AI JSON into Python dictionary
        # ----------------------------------------------------

        return json.loads(content)

    except urllib.error.HTTPError as e:

        error_body = e.read().decode(
            "utf-8",
            errors="replace"
        )

        raise Exception(
            f"OpenRouter HTTP {e.code}: {error_body}"
        )

    except urllib.error.URLError as e:

        raise Exception(
            f"Unable to connect to OpenRouter: {e.reason}"
        )

    except json.JSONDecodeError:

        raise Exception(
            "OpenRouter returned an invalid JSON response."
        )


# ============================================================
# TEST AI CONNECTION
# ============================================================

@app.route("/test-ai")
def test_ai():

    if not OPENROUTER_API_KEY:

        return jsonify({
            "status": "error",
            "message": "OPENROUTER_API_KEY is not configured in Render."
        }), 500

    try:

        result = ask_openrouter(
            "What is molarity? Give only the topic, formula and one learning hint."
        )

        return jsonify({
            "status": "success",
            "message": "OpenRouter connection successful.",
            "ai_response": result
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ============================================================
# MAIN ASK ROUTE
# ============================================================

@app.route("/ask", methods=["POST"])
def ask():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "status": "error",
            "message": "No question received."
        }), 400


    question = str(
        data.get("question", "")
    ).strip()


    if not question:

        return jsonify({
            "status": "error",
            "message": "Please enter a Chemistry question."
        }), 400


    try:

        ai_result = ask_openrouter(question)


        # ----------------------------------------------------
        # Ensure expected fields exist
        # ----------------------------------------------------

        topic = ai_result.get(
            "topic",
            "Topic not identified"
        )

        concept = ai_result.get(
            "concept",
            ""
        )

        formula = ai_result.get(
            "formula",
            "No formula required."
        )

        given = ai_result.get(
            "given",
            []
        )

        required = ai_result.get(
            "required",
            []
        )

        steps = ai_result.get(
            "steps",
            []
        )

        hints = ai_result.get(
            "hints",
            []
        )

        feedback = ai_result.get(
            "feedback",
            []
        )


        # ----------------------------------------------------
        # Send structured result to frontend
        # ----------------------------------------------------

        return jsonify({

            "status": "success",

            "topic": topic,

            "concept": concept,

            "formula": formula,

            "given": given,

            "required": required,

            "steps": steps,

            "hints": hints,

            "feedback": feedback,

            # Intentionally empty.
            # BikkyChem should guide rather than solve.
            "final_answer": ""

        })


    except Exception as e:

        return jsonify({

            "status": "error",

            "topic": "AI connection problem",

            "formula": "",

            "steps": [],

            "hints": [
                "The Chemistry AI could not process the question.",
                "Please try again."
            ],

            "feedback": [
                str(e)
            ]

        }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
