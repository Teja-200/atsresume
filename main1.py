import os
import json
from flask import Flask, request, jsonify, render_template
from google import genai
import PyPDF2

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

client = genai.Client(
    api_key="AIzaSyAnFpucHrr4mBFS97HBjrp3ExM9PuiGG1g"
)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def parse_gemini_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

def ats_analysis(resume_text):
    prompt = f"""
You are an Applicant Tracking System (ATS).

Analyze the resume content below and generate insights
STRICTLY based on the resume.

Return ONLY valid JSON in this exact format:

{{
  "score": number,
  "description": "3–4 line professional summary of the resume",
  "pros": [
    "strength 1",
    "strength 2",
    "strength 3"
  ],
  "cons": [
    "gap 1",
    "gap 2",
    "gap 3"
  ]
}}

RESUME CONTENT:
{resume_text}
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return parse_gemini_json(response.text)

@app.route("/")
def home():
    return render_template("index1.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "PDF resume is required"}), 400

    resume_file = request.files["file"]
    pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_file.filename)
    resume_file.save(pdf_path)

    resume_text = extract_text_from_pdf(pdf_path)

    if not resume_text:
        resume_text = (
            "The resume text could not be extracted clearly. "
            "Analyze the resume structure and provide general insights."
        )

    try:
        result = ats_analysis(resume_text)
    except Exception as e:
        return jsonify({
            "error": "ATS analysis failed",
            "details": str(e)
        }), 500

    return jsonify({
        "score": result["score"],
        "description": result["description"],
        "pros": result["pros"],
        "cons": result["cons"]
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
