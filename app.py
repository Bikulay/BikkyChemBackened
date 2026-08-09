from flask import Flask, request, jsonify

app = Flask(__name__)

# -----------------------------------------
# BIKKYCHEM PROTOTYPE DATABASE
# Chapter 1: Some Basic Concepts of Chemistry
# Topic: Molarity
# -----------------------------------------

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


@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>BikkyChem</title>
    </head>

    <body>

        <h1>🧪 BikkyChem</h1>

        <h2>Guided Chemistry Learning</h2>

        <p>Prototype Version 1</p>

        <hr>

        <h3>Ask a Chemistry Question</h3>

        <form action="/ask" method="post">

            <textarea
                name="question"
                rows="6"
                cols="60"
                placeholder="Type your Chemistry question here..."
            ></textarea>

            <br><br>

            <button type="submit">
                ASK BIKKYCHEM
            </button>

        </form>

    </body>
    </html>
    """


@app.route("/ask", methods=["POST"])
def ask():

    question = request.form.get("question", "").lower()

    # -----------------------------------------
    # Simple topic identification
    # -----------------------------------------

    if "molarity" in question:

        data = chemistry_data["molarity"]

        return f"""
        <html>
        <head>
            <title>BikkyChem - Guided Learning</title>
        </head>

        <body>

            <h1>🧪 BikkyChem</h1>

            <hr>

            <h3>Topic Identified</h3>

            <p><strong>{data["topic"]}</strong></p>

            <h3>Formula</h3>

            <p><strong>{data["formula"]}</strong></p>

            <h3>Step 1</h3>

            <p>{data["steps"][0]}</p>

            <h3>Hint</h3>

            <p>{data["hints"][0]}</p>

            <hr>

            <p>
            <strong>
            BikkyChem does not give the final answer immediately.
            It guides you step by step.
            </strong>
            </p>

            <br>

            <a href="/">← Ask another question</a>

        </body>
        </html>
        """

    else:

        return """
        <html>

        <head>
            <title>BikkyChem</title>
        </head>

        <body>

            <h1>🧪 BikkyChem</h1>

            <h3>Topic not identified</h3>

            <p>
            This prototype currently understands
            questions related to <strong>Molarity</strong>.
            </p>

            <a href="/">← Try again</a>

        </body>

        </html>
        """


if __name__ == "__main__":
    app.run()
    