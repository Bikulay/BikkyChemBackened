from flask import Flask, request, render_template, jsonify

app = Flask(__name__)


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

    return """
<!DOCTYPE html>

<html>

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>BikkyChem</title>

    <style>

        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #f7f9fc;
            color: #222;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 30px 20px;
        }

        .header {
            text-align: center;
            background: white;
            padding: 30px 20px;
            border-radius: 15px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
        }

        .logo {
            width: 140px;
            height: auto;
            display: block;
            margin: 0 auto 15px auto;
        }

        h1 {
            margin: 5px 0;
            font-size: 34px;
        }

        .tagline {
            font-size: 18px;
            color: #555;
            margin-top: 8px;
        }

        .version {
            color: #777;
            font-size: 14px;
        }

        .question-box {
            background: white;
            margin-top: 25px;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
        }

        textarea {
            width: 100%;
            min-height: 130px;
            padding: 15px;
            box-sizing: border-box;
            border: 1px solid #ccc;
            border-radius: 10px;
            font-size: 16px;
            resize: vertical;
        }

        button {
            margin-top: 15px;
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            background: #2878e8;
            color: white;
            font-size: 16px;
            cursor: pointer;
        }

        button:hover {
            background: #185fc0;
        }

        #result {
            margin-top: 25px;
            padding: 20px;
            background: #f1f6ff;
            border-radius: 10px;
            display: none;
        }

        .section {
            margin-top: 15px;
        }

        .section h3 {
            margin-bottom: 8px;
        }

        ul {
            line-height: 1.8;
        }

    </style>

</head>


<body>

<div class="container">

    <div class="header">

        <!-- BIKKYCHEM LOGO -->
        <img
            src="{{ url_for('static', filename='IMG_0898.png') }}"
            alt="BikkyChem Logo"
            class="logo"
        >

        <h1>BikkyChem</h1>

        <div class="tagline">
            Guided Chemistry Learning
        </div>

        <div class="version">
            Prototype Version 1
        </div>

    </div>


    <div class="question-box">

        <h2>Ask a Chemistry Question</h2>

        <textarea
            id="question"
            placeholder="Type your Chemistry question here..."
        ></textarea>

        <br>

        <button onclick="askBikkyChem()">
            ASK BIKKYCHEM
        </button>


        <div id="result">

            <div class="section">

                <h3>Topic</h3>

                <p id="topic"></p>

            </div>


            <div class="section">

                <h3>Formula</h3>

                <p id="formula"></p>

            </div>


            <div class="section">

                <h3>Guided Steps</h3>

                <ul id="steps"></ul>

            </div>


            <div class="section">

                <h3>Hints</h3>

                <ul id="hints"></ul>

            </div>

        </div>

    </div>

</div>


<script>

async function askBikkyChem() {

    const question =
        document.getElementById("question").value;

    if (!question.trim()) {

        alert("Please enter a Chemistry question.");

        return;
    }


    const response = await fetch("/ask", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            question: question
        })

    });


    const data = await response.json();


    document.getElementById("result").style.display = "block";


    document.getElementById("topic").innerText =
        data.topic;


    document.getElementById("formula").innerText =
        data.formula;


    const stepsList =
        document.getElementById("steps");

    stepsList.innerHTML = "";


    data.steps.forEach(function(step) {

        const li = document.createElement("li");

        li.innerText = step;

        stepsList.appendChild(li);

    });


    const hintsList =
        document.getElementById("hints");

    hintsList.innerHTML = "";


    data.hints.forEach(function(hint) {

        const li = document.createElement("li");

        li.innerText = hint;

        hintsList.appendChild(li);

    });

}


</script>


</body>

</html>
"""


# ============================================================
# ASK ROUTE
# ============================================================

@app.route("/ask", methods=["POST"])
def ask():

    data = request.get_json()

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
    # If topic is not yet available
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
