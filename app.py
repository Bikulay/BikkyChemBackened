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

# OpenRouter free router
OPENROUTER_MODEL = "openrouter/free"


# ============================================================
# RETRY CONFIGURATION
# ============================================================

# Maximum number of attempts for one request.
MAX_RETRIES = 3

# Delay before each retry.
# Attempt 1 -> failure -> 1 second
# Attempt 2 -> failure -> 2 seconds
# Attempt 3 -> failure -> final error
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

You must help the student LEARN how to solve the Chemistry
problem rather than simply giving the answer.

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

Return ONLY a valid JSON object.

Do not use Markdown.
Do not use ```json fences.
Do not write anything before or after the JSON.

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

For numerical problems:

NEVER put the final numerical result in any field.

For conceptual questions:

Explain the concept through the steps and hints rather
than giving an unnecessarily long answer.
"""


# ============================================================
# EXTRACT JSON FROM AI RESPONSE
# ============================================================

def extract_json_from_response(content):

    if content is None:

        raise Exception(
            "OpenRouter returned no content."
        )


    # --------------------------------------------------------
    # If already a dictionary
    # --------------------------------------------------------

    if isinstance(content, dict):

        return content


    # --------------------------------------------------------
    # Handle list-style content
    # --------------------------------------------------------

    if isinstance(content, list):

        text_parts = []

        for item in content:

            if isinstance(item, dict):

                if item.get("type") == "text":

                    text_parts.append(
                        str(item.get("text", ""))
                    )

                elif "text" in item:

                    text_parts.append(
                        str(item.get("text", ""))
                    )

            elif isinstance(item, str):

                text_parts.append(item)


        content = "".join(text_parts)


    content = str(content).strip()


    if not content:

        raise Exception(
            "OpenRouter returned an empty response."
        )


    # --------------------------------------------------------
    # Attempt 1: direct JSON
    # --------------------------------------------------------

    try:

        return json.loads(content)

    except json.JSONDecodeError:

        pass


    # --------------------------------------------------------
    # Remove Markdown fences
    # --------------------------------------------------------

    cleaned = content

    cleaned = cleaned.replace(
        "```json",
        ""
    )

    cleaned = cleaned.replace(
        "```JSON",
        ""
    )

    cleaned = cleaned.replace(
        "```",
        ""
    )

    cleaned = cleaned.strip()


    # --------------------------------------------------------
    # Attempt 2
    # --------------------------------------------------------

    try:

        return json.loads(cleaned)

    except json.JSONDecodeError:

        pass


    # --------------------------------------------------------
    # Attempt 3:
    # Find JSON object inside additional text.
    # --------------------------------------------------------

    start = cleaned.find("{")
    end = cleaned.rfind("}")


    if start != -1 and end != -1 and end > start:

        possible_json = cleaned[
            start:end + 1
        ]


        try:

            return json.loads(
                possible_json
            )

        except json.JSONDecodeError:

            pass


    # --------------------------------------------------------
    # Failed
    # --------------------------------------------------------

    raise Exception(
        "The AI response was not valid JSON."
    )


# ============================================================
# CALL OPENROUTER ONCE
# ============================================================

def call_openrouter_once(messages):

    if not OPENROUTER_API_KEY:

        raise Exception(
            "OPENROUTER_API_KEY is not configured in Render."
        )


    payload = {

        "model":
            OPENROUTER_MODEL,

        "messages":
            messages,

        "temperature":
            0.1,

        "response_format": {
            "type": "json_object"
        }

    }


    data = json.dumps(
        payload
    ).encode("utf-8")


    headers = {

        "Authorization":
            "Bearer " + OPENROUTER_API_KEY,

        "Content-Type":
            "application/json",

        "HTTP-Referer":
            "https://bikkychem-prototype.onrender.com",

        "X-Title":
            "BikkyChem AI"

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
                .decode(
                    "utf-8",
                    errors="replace"
                )
            )


    except urllib.error.HTTPError as e:

        error_body = e.read().decode(
            "utf-8",
            errors="replace"
        )


        # Give us the actual OpenRouter error.
        raise Exception(
            f"OpenRouter HTTP {e.code}: "
            f"{error_body[:1000]}"
        )


    except urllib.error.URLError as e:

        raise Exception(
            "Unable to connect to OpenRouter: "
            + str(e.reason)
        )


    except TimeoutError:

        raise Exception(
            "OpenRouter request timed out."
        )


    except Exception as e:

        raise Exception(
            "OpenRouter connection error: "
            + str(e)
        )


    # --------------------------------------------------------
    # Parse HTTP response
    # --------------------------------------------------------

    try:

        result = json.loads(
            response_data
        )

    except json.JSONDecodeError:

        raise Exception(
            "OpenRouter returned a non-JSON response."
        )


    # --------------------------------------------------------
    # Check API error
    # --------------------------------------------------------

    if "error" in result:

        error_info = result.get(
            "error"
        )


        if isinstance(
            error_info,
            dict
        ):

            error_message = error_info.get(
                "message",
                str(error_info)
            )

        else:

            error_message = str(
                error_info
            )


        raise Exception(
            "OpenRouter error: "
            + error_message
        )


    # --------------------------------------------------------
    # Get choices
    # --------------------------------------------------------

    choices = result.get(
        "choices",
        []
    )


    if not choices:

        raise Exception(
            "OpenRouter returned no AI choices."
        )


    # --------------------------------------------------------
    # Get message
    # --------------------------------------------------------

    message = choices[0].get(
        "message",
        {}
    )


    content = message.get(
        "content",
        ""
    )


    if not content:

        raise Exception(
            "OpenRouter returned an empty AI response."
        )


    # --------------------------------------------------------
    # Convert AI response to JSON
    # --------------------------------------------------------

    return extract_json_from_response(
        content
    )


# ============================================================
# CALL OPENROUTER WITH AUTOMATIC RETRY
# ============================================================

def call_openrouter(messages):

    last_error = None


    for attempt in range(
        MAX_RETRIES
    ):

        try:

            return call_openrouter_once(
                messages
            )


        except Exception as e:

            last_error = e


            # -----------------------------------------------
            # If this was the final attempt, stop.
            # -----------------------------------------------

            if attempt == MAX_RETRIES - 1:

                break


            # -----------------------------------------------
            # Wait before retry.
            # -----------------------------------------------

            delay = RETRY_DELAYS[
                attempt
            ]


            time.sleep(
                delay
            )


    # --------------------------------------------------------
    # All attempts failed.
    # --------------------------------------------------------

    raise Exception(
        "BikkyChem tried "
        f"{MAX_RETRIES} times, but OpenRouter "
        "could not process the request. "
        f"Last error: {last_error}"
    )


# ============================================================
# TEXT QUESTION
# ============================================================

def analyse_text_question(
    question
):

    messages = [

        {
            "role":
                "system",

            "content":
                SYSTEM_PROMPT

        },

        {
            "role":
                "user",

            "content":
                question

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

    # --------------------------------------------------------
    # Convert image to Base64
    # --------------------------------------------------------

    encoded_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")


    # --------------------------------------------------------
    # Create data URL
    # --------------------------------------------------------

    image_data_url = (
        f"data:{mime_type};base64,"
        f"{encoded_image}"
    )


    messages = [

        {
            "role":
                "system",

            "content":
                SYSTEM_PROMPT

        },

        {
            "role":
                "user",

            "content": [

                {
                    "type":
                        "text",

                    "text":
                        """
Read the uploaded image carefully.

The image contains a Chemistry question.

Identify exactly what the question asks.

Then provide:

- Topic
- Concept
- Formula or chemical principle
- Given information
- Required information
- Guided steps
- Progressive hints
- Feedback

Do NOT provide the final answer.

Pay special attention to:

- chemical symbols
- subscripts
- superscripts
- numerical values
- units
- chemical equations
- structures
- diagrams
- tables
- graphs

If something is unclear, do not guess.
Mention that the information is unclear.
"""

                },

                {
                    "type":
                        "image_url",

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

def normalise_result(
    ai_result
):

    if not isinstance(
        ai_result,
        dict
    ):

        raise Exception(
            "AI returned an unexpected response format."
        )


    # --------------------------------------------------------
    # Given
    # --------------------------------------------------------

    given = ai_result.get(
        "given",
        []
    )


    if not isinstance(
        given,
        list
    ):

        given = [
            str(given)
        ]


    # --------------------------------------------------------
    # Required
    # --------------------------------------------------------

    required = ai_result.get(
        "required",
        []
    )


    if not isinstance(
        required,
        list
    ):

        required = [
            str(required)
        ]


    # --------------------------------------------------------
    # Steps
    # --------------------------------------------------------

    steps = ai_result.get(
        "steps",
        []
    )


    if not isinstance(
        steps,
        list
    ):

        steps = [
            str(steps)
        ]


    # --------------------------------------------------------
    # Hints
    # --------------------------------------------------------

    hints = ai_result.get(
        "hints",
        []
    )


    if not isinstance(
        hints,
        list
    ):

        hints = [
            str(hints)
        ]


    # --------------------------------------------------------
    # Feedback
    # --------------------------------------------------------

    feedback = ai_result.get(
        "feedback",
        []
    )


    if not isinstance(
        feedback,
        list
    ):

        feedback = [
            str(feedback)
        ]


    # --------------------------------------------------------
    # Stable response
    # --------------------------------------------------------

    return {

        "status":
            "success",

        "topic":
            str(
                ai_result.get(
                    "topic",
                    "Topic not identified"
                )
            ),

        "concept":
            str(
                ai_result.get(
                    "concept",
                    ""
                )
            ),

        "formula":
            str(
                ai_result.get(
                    "formula",
                    "No formula required."
                )
            ),

        "given":
            given,

        "required":
            required,

        "steps":
            steps,

        "hints":
            hints,

        "feedback":
            feedback,

        # ----------------------------------------------------
        # Final answer is ALWAYS hidden.
        # ----------------------------------------------------

        "final_answer":
            ""

    }


# ============================================================
# TEST AI CONNECTION
# ============================================================

@app.route(
    "/test-ai"
)
def test_ai():

    try:

        result = analyse_text_question(

            "What is molarity? "
            "Identify the topic, concept, formula "
            "and one useful learning hint. "
            "Do not give a final answer."

        )


        return jsonify({

            "status":
                "success",

            "message":
                "OpenRouter connection successful.",

            "ai_response":
                normalise_result(
                    result
                )

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
        # CASE 1 — IMAGE
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


            # ------------------------------------------------
            # Read image
            # ------------------------------------------------

            image_bytes = (
                uploaded_file.read()
            )


            # ------------------------------------------------
            # Check image size
            # ------------------------------------------------

            if len(
                image_bytes
            ) > MAX_FILE_SIZE:

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "Image is too large. "
                        "Maximum size is 10 MB."

                }), 400


            # ------------------------------------------------
            # Determine MIME type
            # ------------------------------------------------

            mime_type = (
                uploaded_file
                .mimetype
                .lower()
                .strip()
            )


            # ------------------------------------------------
            # iOS/browser fallback
            # ------------------------------------------------

            if mime_type not in ALLOWED_IMAGE_TYPES:

                filename = (
                    uploaded_file
                    .filename
                    .lower()
                )


                if (
                    filename.endswith(".jpg")
                    or
                    filename.endswith(".jpeg")
                ):

                    mime_type = "image/jpeg"


                elif filename.endswith(
                    ".png"
                ):

                    mime_type = "image/png"


                else:

                    return jsonify({

                        "status":
                            "error",

                        "message":
                            "For Stage 2A, please upload "
                            "a JPG, JPEG or PNG image."

                    }), 400


            # ------------------------------------------------
            # Send image to OpenRouter
            # ------------------------------------------------

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


        # ----------------------------------------------------
        # Analyse text
        # ----------------------------------------------------

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

        error_message = str(e)


        return jsonify({

            "status":
                "error",

            "message":
                error_message,

            "topic":
                "AI processing problem",

            "concept":
                "",

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
                [
                    error_message
                ],

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
