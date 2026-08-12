from flask import Flask, request, jsonify, render_template
import os
import json
import urllib.request
import urllib.error
import base64
import time


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

OPENROUTER_MODEL = "openrouter/free"


# ============================================================
# RETRY CONFIGURATION
# ============================================================

MAX_RETRIES = 3

# Delay before retrying:
# Attempt 1 fails → wait 1 second
# Attempt 2 fails → wait 2 seconds
# Attempt 3 fails → stop

RETRY_DELAYS = [1, 2]


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
# BIKKYCHEM SYSTEM PROMPT
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

    if content.startswith("```json"):
        content = content[7:]

    elif content.startswith("```"):
        content = content[3:]

    if content.endswith("```"):
        content = content[:-3]

    return content.strip()


# ============================================================
# DETERMINE WHETHER ERROR SHOULD BE RETRIED
# ============================================================

def is_retryable_error(error):

    # Network/connection errors
    if isinstance(error, urllib.error.URLError):
        return True

    # HTTP errors
    if isinstance(error, urllib.error.HTTPError):

        # 429 = rate limit
        if error.code == 429:
            return True

        # 500, 502, 503, 504 = temporary server errors
        if error.code in [500, 502, 503, 504]:
            return True

        # Other HTTP errors should NOT be retried
        return False

    # Timeout errors
    if isinstance(error, TimeoutError):
        return True

    return False


# ============================================================
# CALL OPENROUTER — WITH AUTOMATIC RETRY
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


    last_error = None


    # ========================================================
    # RETRY LOOP
    # ========================================================

    for attempt in range(MAX_RETRIES):

        try:

            print(
                f"BikkyChem OpenRouter attempt "
                f"{attempt + 1}/{MAX_RETRIES}"
            )


            req = urllib.request.Request(

                OPENROUTER_URL,

                data=data,

                headers=headers,

                method="POST"
            )


            with urllib.request.urlopen(
                req,
                timeout=90
            ) as response:

                response_data = (
                    response
                    .read()
                    .decode("utf-8")
                )


            result = json.loads(
                response_data
            )


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


            content = clean_ai_json(
                content
            )


            try:

                return json.loads(
                    content
                )

            except json.JSONDecodeError:

                raise Exception(
                    "OpenRouter returned an invalid JSON response."
                )


        except Exception as error:

            last_error = error


            print(
                f"BikkyChem OpenRouter error "
                f"on attempt {attempt + 1}: {error}"
            )


            # ------------------------------------------------
            # If error is NOT temporary, stop immediately.
            # ------------------------------------------------

            if not is_retryable_error(error):

                raise error


            # ------------------------------------------------
            # If this was the final attempt, stop.
            # ------------------------------------------------

            if attempt == MAX_RETRIES - 1:

                break


            # ------------------------------------------------
            # Wait before next attempt.
            # ------------------------------------------------

            delay = RETRY_DELAYS[attempt]

            print(
                f"Retrying OpenRouter in {delay} second(s)..."
            )

            time.sleep(
                delay
            )


    # ========================================================
    # ALL ATTEMPTS FAILED
    # ========================================================

    raise Exception(
        f"OpenRouter request failed after "
        f"{MAX_RETRIES} attempts: {last_error}"
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


    return call_openrouter(
        messages
    )


# ============================================================
# IMAGE QUESTION
# ============================================================

def analyse_image_question(
    image_bytes,
    mime_type
):

    encoded_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")


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
in the image and analyse it according
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

                        "url":
                            image_data_url

                    }

                }

            ]

        }

    ]


    return call_openrouter(
        messages
    )


# ============================================================
# NORMALISE AI RESPONSE
# ============================================================

def normalise_result(ai_result):

    return {

        "status":
            "success",

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

        "final_answer":
            ""

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

            "status":
                "success",

            "message":
                "OpenRouter connection successful.",

            "ai_response":
                result

        })


    except Exception as e:

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

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

                    "status":
                        "error",

                    "message":
                        "No image was received."

                }), 400


            if not uploaded_file.filename:

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "No file was selected."

                }), 400


            image_bytes = (
                uploaded_file.read()
            )


            if len(image_bytes) > MAX_FILE_SIZE:

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "Image is too large. "
                        "Maximum size is 10 MB."

                }), 400


            mime_type = (
                uploaded_file
                .mimetype
                .lower()
            )


            if mime_type not in ALLOWED_IMAGE_TYPES:

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "For Stage 2A, please upload "
                        "a JPG, JPEG or PNG image."

                }), 400


            ai_result = (
                analyse_image_question(
                    image_bytes,
                    mime_type
                )
            )


            return jsonify(
                normalise_result(
                    ai_result
                )
            )


        # ====================================================
        # CASE 2 — TEXT QUESTION
        # ====================================================

        data = request.get_json(
            silent=True
        )


        if not data:

            return jsonify({

                "status":
                    "error",

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

                "status":
                    "error",

                "message":
                    "Please enter a Chemistry question."

            }), 400


        ai_result = (
            analyse_text_question(
                question
            )
        )


        return jsonify(
            normalise_result(
                ai_result
            )
        )


    except Exception as e:

        print(
            "BikkyChem request error:",
            e
        )


        return jsonify({

            "status":
                "error",

            "message":
                str(e),

            "topic":
                "AI processing problem",

            "formula":
                "",

            "given":
                [],

            "required":
                [],

            "steps":
                [],

            "hints":
                [],

            "feedback":
                [str(e)],

            "final_answer":
                ""

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
