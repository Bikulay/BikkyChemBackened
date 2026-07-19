		from flask import Flask, request, jsonify
import google.generativeai as genai

# Paste your Gemini API key below (inside the quotes)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Load Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")

# Create Flask app
app = Flask(__name__)

# BikkyChem system instruction
SYSTEM_PROMPT = """
You are BikkyChem, an AI Chemistry Mentor for CBSE, JEE, and NEET students.

Rules:
- Never give the final answer directly.
- First identify the chapter and topic.
- Explain the required concepts.
- Provide only the relevant formulas.
- Give a step-by-step solving strategy.
- Ask the student to attempt the calculation.
- Give progressive hints if needed.
- Encourage independent thinking like an experienced chemistry teacher.
"""

# API endpoint
@app.route('/solve', methods=['POST'])
def solve():
    data = request.get_json()

    # Get question from request
    question = data.get('question', '')

    # Send to Gemini
    response = model.generate_content(
        SYSTEM_PROMPT + "\\n\\nQuestion: " + question
    )

    # Return response
    return jsonify({
        "status": "success",
        "question": question,
        "response": response.text
    })

# Run the server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)