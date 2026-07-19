from flask import Flask, request, jsonify
import google.generativeai as genai
import os

# ---------------------------------------------------
# Configure Gemini API
# ---------------------------------------------------
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Load Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")

# Create Flask app
app = Flask(__name__)

# ---------------------------------------------------
# BikkyChem System Prompt
# ---------------------------------------------------
SYSTEM_PROMPT = """
You are BikkyChem, an AI chemistry mentor created by Bikulay, a higher-secondary chemistry teacher from India.

Your goal is to help students learn chemistry by guiding their thinking, not by giving the final answer immediately.

TEACHING RULES:
- Do not give the final numerical answer in the first response.
- Identify the chapter and topic first.
- Explain the concept in simple English.
- Provide the relevant formula(s).
- Show the step-by-step strategy.
- Give a guided hint for the next step.
- Mention one common mistake students make.
- Encourage the student to attempt the calculation.

RESPONSE FORMAT:

Chapter / Topic:
- Mention the chapter and subtopic.

Key Concept:
- Explain the idea in 3-5 simple points.

Formula(s) to Use:
- Write the formula and define symbols.

Step-by-Step Strategy:
1. Identify given data.
2. Convert units if needed.
3. Choose the correct formula.
4. Substitute values symbolically.
5. Simplify carefully.
6. Ask the student to calculate the final value.

Guided Hint:
- Give only the next clue, not the final answer.

Common Mistake to Avoid:
- Mention one likely error.

Keep the explanation suitable for CBSE, NEET, and JEE students.
Use simple English and a teacher-like tone.
"""

# ---------------------------------------------------
# Home Route
# ---------------------------------------------------
@app.route('/')
def home():
    return jsonify({
        "app": "BikkyChem",
        "status": "live",
        "message": "BikkyChem AI backend is running successfully"
    })

# ---------------------------------------------------
# Test Route
# ---------------------------------------------------
@app.route('/test')
def test():
    try:
        question = "Calculate the volume occupied by 0.5 mol of an ideal gas at STP."

        response = model.generate_content(
            SYSTEM_PROMPT + "\n\nQuestion: " + question
        )

        return response.text

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ---------------------------------------------------
# Main Solve API
# ---------------------------------------------------
@app.route('/solve', methods=['POST'])
def solve():
    try:
        data = request.get_json()

        if not data or "question" not in data:
            return jsonify({
                "status": "error",
                "message": "Please provide a question in JSON format."
            }), 400

        question = data["question"].strip()

        if not question:
            return jsonify({
                "status": "error",
                "message": "Question cannot be empty."
            }), 400

        # Generate AI response
        response = model.generate_content(
            SYSTEM_PROMPT + "\n\nQuestion: " + question
        )

        return jsonify({
            "status": "success",
            "question": question,
            "response": response.text
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ---------------------------------------------------
# Run the server
# ---------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
