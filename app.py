from flask import Flask, request, jsonify, render_template
import os
import json
import urllib.request
import urllib.error
import base64


app = Flask(__name__, template_folder="Templates")


# ============================================================
# OPENROUTER CONFIGURATION
# ============================================================

OPENROUTER_API_KEY = os.environ.get(
    "OPENROUTER_API_KEY",
    ""
).strip()

OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

# OpenRouter's free router can select an available
# model capable of handling the requested modality.
OPENROUTER_MODEL = "openrouter/free"


# ============================================================
# UPLOAD CONFIGURATION
# ============================================================

MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png"
}


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template("Index.html")


# ============================================================
# COMMON BIKKYCHEM SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are BikkyChem, an educational Chemistry guidance engine.

Your purpose is NOT to act like an ordinary chatbot.

You must help the student LEARN how to solve the Chemistry problem.

For every Chemistry question:

1. Identify the exact Chemistry topic.
2. Identify the main Chemistry concept.
3. Provide the appropriate formula, relationship,
   chemical equation, or principle when applicable.
4. Identify the quantities/data given.
5. Identify what the student is required to find.
6. Give logical step-by-step guidance.
7. Give progressive hints that help the student think.
8. Give useful feedback about what the student should check.
9. DO NOT directly provide the final numerical answer.
10. DO NOT complete the entire calculation for the student.
11. Do not invent a formula.
12. If several formulas are possible, select the most
    appropriate one.
13. If no formula is required, clearly state that.
14. If the question is incomplete, identify the missing
    information.
15. Keep the explanation suitable for CBSE Class XI-XII
    Chemistry students.
16. Use scientifically correct Chemistry terminology.
17. Do not assume every question is about Molarity.

IMPORTANT FOR IMAGE QUESTIONS:

- Carefully read the uploaded Chemistry question.
- Read subscripts and superscripts correctly.
- Read chemical symbols correctly.
- Read numerical values and units carefully.
- Read chemical equations correctly.
- If the image contains a diagram, graph, table,
  structure, or equation, use it as part of the question.
- Do not invent information that cannot be read.
- If part of the image is unclear, mention that.

IMPORTANT:

Return ONLY valid JSON.

Use exactly this structure:

{
  "topic": "Exact Chemistry topic",
  "concept": "Main concept involved",
  "formula": "Relevant formula, relationship, equation or principle",
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

For numerical problems, NEVER put the final numerical
result in any field.

For conceptual questions, explain the concept through
the steps and hints rather than giving an unnecessarily
long answer.
"""


# ============================================================
# CLEAN AI JSON RESPONSE
# ============================================================

def clean_ai_json(content):

    content = content.strip()

    # Remove Markdown code fences if the model adds them.

    if content.startswith("```json"):

        content = content[7:]

    elif content.startswith("```"):

        content = content[3:]


    if content.endswith("```"):

        content = content[:-3]


    return content.strip()


# ============================================================
# CALL OPENROUTER
# ============================================================

def call_openrouter(messages):

    if not OPENROUTER_API_KEY:

        raise Exception(
            "OPENROUTER_API_KEY is not configured in Render."
        )


    payload = {

        "model": OPENROUTER_MODEL,

        "messages": messages,

        "temperature": 0.2
    }


    data = json.dumps(payload).encode("utf-8")


    headers = {

        "Authorization":
            "Bearer " + OPENROUTER_API_KEY,

        "Content-Type":
            "application/json",

        "HTTP-Referer":
            "https://bikkychem-prototype.onrender.com",

        "X-Title":
            "BikkyChem"
    }


    req = urllib.request.Request(

        OPENROUTER_URL,

        data=data,

        headers=headers,

        method="POST"
    )


    try:

        with urllib.request.urlopen(
            req,
            timeout=90
        ) as response:

            response_data = (
                response
                .read()
                .decode("utf-8")
            )


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


    content = clean_ai_json(content)


    try:

        return json.loads(content)

    except json.JSONDecodeError:

        raise Exception(
            "OpenRouter returned an invalid JSON response."
        )


# ============================================================
# TEXT QUESTION
# ============================================================

def analyse_text_question(question):

    messages = [

        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },

        {
            "role": "user",
            "content": question
        }

    ]


    return call_openrouter(messages)


# ============================================================
# IMAGE QUESTION
# ============================================================

def analyse_image_question(
    image_bytes,
    mime_type
):

    # Convert uploaded image into Base64.

    encoded_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")


    # Create a data URL.

    image_data_url = (
        f"data:{mime_type};base64,"
        f"{encoded_image}"
    )


    messages = [

        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },

        {
            "role": "user",

            "content": [

                {
                    "type": "text",

                    "text": """
Read the uploaded image carefully.

Identify the Chemistry question shown
in the image and then analyse it according
to the BikkyChem learning instructions.

Pay special attention to:
- chemical symbols
- subscripts
- superscripts
- numerical values
- units
- equations
- diagrams
- tables
- graphs

Do not give the final answer.
"""
                },

                {
                    "type": "image_url",

                    "image_url": {
                        "url": image_data_url
                    }
                }

            ]
        }

    ]


    return call_openrouter(messages)


# ============================================================
# NORMALISE AI RESPONSE
# ============================================================

def normalise_result(ai_result):

    return {

        "status": "success",

        "topic":
            ai_result.get(
                "topic",
                "Topic not identified"
            ),

        "concept":
            ai_result.get(
                "concept",
                ""
            ),

        "formula":
            ai_result.get(
                "formula",
                "No formula required."
            ),

        "given":
            ai_result.get(
                "given",
                []
            ),

        "required":
            ai_result.get(
                "required",
                []
            ),

        "steps":
            ai_result.get(
                "steps",
                []
            ),

        "hints":
            ai_result.get(
                "hints",
                []
            ),

        "feedback":
            ai_result.get(
                "feedback",
                []
            ),

        # Always empty by design.

        "final_answer": ""

    }


# ============================================================
# TEST AI CONNECTION
# ============================================================

@app.route("/test-ai")
def test_ai():

    try:

        result = analyse_text_question(
            "What is molarity? Give the topic, formula "
            "and one learning hint."
        )


        return jsonify({

            "status": "success",

            "message":
                "OpenRouter connection successful.",

            "ai_response":
                result

        })


    except Exception as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 500


# ============================================================
# MAIN ASK ROUTE
# ============================================================

@app.route(
    "/ask",
    methods=["POST"]
)
def ask():

    try:

        # ====================================================
        # CASE 1 — IMAGE UPLOAD
        # ====================================================

        if "file" in request.files:

            uploaded_file = (
                request.files["file"]
            )


            if not uploaded_file:

                return jsonify({

                    "status": "error",

                    "message":
                        "No image was received."

                }), 400


            if not uploaded_file.filename:

                return jsonify({

                    "status": "error",

                    "message":
                        "No file was selected."

                }), 400


            # Read image.

            image_bytes = (
                uploaded_file.read()
            )


            # Check size.

            if len(image_bytes) > MAX_FILE_SIZE:

                return jsonify({

                    "status": "error",

                    "message":
                        "Image is too large. "
                        "Maximum size is 10 MB."

                }), 400


            # Determine MIME type.

            mime_type = (
                uploaded_file
                .mimetype
                .lower()
            )


            if mime_type not in ALLOWED_IMAGE_TYPES:

                return jsonify({

                    "status": "error",

                    "message":
                        "For Stage 2A, please upload "
                        "a JPG, JPEG or PNG image."

                }), 400


            # Send image to OpenRouter.

            ai_result = (
                analyse_image_question(
                    image_bytes,
                    mime_type
                )
            )


            return jsonify(
                normalise_result(ai_result)
            )


        # ====================================================
        # CASE 2 — NORMAL TEXT QUESTION
        # ====================================================

        data = request.get_json(
            silent=True
        )


        if not data:

            return jsonify({

                "status": "error",

                "message":
                    "No question received."

            }), 400


        question = str(
            data.get(
                "question",
                ""
            )
        ).strip()


        if not question:

            return jsonify({

                "status": "error",

                "message":
                    "Please enter a Chemistry question."

            }), 400


        # Analyse typed question.

        ai_result = (
            analyse_text_question(
                question
            )
        )


        return jsonify(
            normalise_result(ai_result)
        )


    except Exception as e:

        return jsonify({

            "status": "error",

            "message": str(e),

            "topic":
                "AI processing problem",

            "formula": "",

            "given": [],

            "required": [],

            "steps": [],

            "hints": [],

            "feedback": [
                str(e)
            ],

            "final_answer": ""

        }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False
    )
