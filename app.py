from flask import Flask, request, jsonify, render_template

app = Flask(__name__, template_folder="Templates")


# ============================================================
# BIKKYCHEM PROTOTYPE DATABASE
# Chapter 1: Some Basic Concepts of Chemistry
# Topic: Molarity
# ============================================================

chemistry_data = {

    "molarity": {

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
    }
}


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():
    return render_template("Index.html")


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


    question = data.get("question", "").lower().strip()


    # --------------------------------------------------------
    # Molarity detection
    # --------------------------------------------------------

    molarity_keywords = [
        "molarity",
        "molar",
        "moles",
        "mol",
        "concentration"
    ]


    if any(word in question for word in molarity_keywords):

        topic_data = chemistry_data["molarity"]

        return jsonify({

            "topic": topic_data["topic"],

            "formula": topic_data["formula"],

            "steps": topic_data["steps"],

            "hints": topic_data["hints"]

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

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
