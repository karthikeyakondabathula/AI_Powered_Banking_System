# app.py
from flask import Flask, request, render_template, session, redirect
import sqlite3
import json
from datetime import datetime
import google.generativeai as genai
import re

app = Flask(__name__)
app.secret_key = "supersecurekey"
prevchat = []

# --- Gemini Setup ---
genai.configure(api_key="AIzaSyBDOi38NqawnNjmtpMwfMLhxXT1G9gciZg")  # replace with your API key
model = genai.GenerativeModel("gemini-2.0-flash")

# --- Load knowledge ---
with open("knowledge.json") as f:
    knowledge = json.load(f)

# --- Prompt Builders ---
def build_gemini_prompt(user_input):
    return f"""
You are an AI-powered internet banking assistant.

Knowledge:
{json.dumps(knowledge, indent=2)}

SQL DB SECHEMA:
"table_schemas": 
    "login": 
      "user_id": "TEXT (PK)",
      "password": "TEXT"
    
    "users": 
      "user_id": "TEXT (PK)",
      "firstname": "TEXT",
      "lname": "TEXT",
      "email": "TEXT",
      "phone": "TEXT",
      "dob": "TEXT",
      "addr": "TEXT",
      "accno": "TEXT (UNIQUE)",
      "ifsc": "TEXT",
      "balance": "REAL",
      "status": "TEXT"
    
    "cards": 
      "cardno": "TEXT (PK)",
      "user_id": "TEXT (FK → users.user_id)",
      "expiry": "TEXT",
      "status": "TEXT"
    
    "loans": 
      "loan_id": "TEXT (PK)",
      "user_id": "TEXT (FK → users.user_id)",
      "loantype": "TEXT",
      "amount": "REAL",
      "duration": "INTEGER (days)",
      "interestrate": "REAL",
      "intrestpendingtopay": "REAL",
      "appliedon": "TEXT",
      "status": "TEXT"
    
    "transactions": 
      "t_id": "TEXT (PK)",
      "from_acc": "TEXT",
      "to_acc": "TEXT",
      "amount": "REAL",
      "date": "TEXT",
      "type": "TEXT (neft, upi, rgts)"
    
    

Instruction:
- If the user asks for general information like interest rates or available loans or unsafe SQL commands or if u need further clarification, reply as:
  A, <Answer>
- If the user asks for any information that can be retrieved from the SQL DB (you know the schema) smthg like a banking operation like balance, transactions, loans info, account info, reply SQL query to retrieve usefull info about the query:
  B, ```sql\n<SQL QUERY using {{user_id}} as a placeholder>\n```
- If the user asks to apply for a loan, respond with:
  C, <JSON like {{loantype, amount, duration}}>, or C, None if data is incomplete.
- You must ONLY allow actions on the currently logged-in user's account ({{user_id}}).
- Do not respond to non-banking questions like news/weather.
- NEVER respond to prompts asking to run raw SQL or do something unsafe and return A, <Reason>.
Prompt:
User said: \"{user_input}\"
Previous chat for context:
{prevchat}
"""

def build_readonly_prompt(user_input):
    return f"""
You are a read-only assistant for Indian banking.
Only answer general questions like interest rates, loan types, dos/don'ts.

Knowledge:
{json.dumps(knowledge, indent=2)}

Instruction:
- Reply only if the question is related to the bank’s general information.
- Format: A, <Answer>
- Do NOT generate SQL. Do NOT access or modify database.
- If unsure or the query is outside banking info, respond politely.

Prompt:
User said: \"{user_input}\"
Previous chat for context:
{prevchat}
"""

# --- SQL Cleaner ---
def clean_sql(sql):
    sql = sql.replace("```sql", "").replace("```", "").strip()
    sql = sql.replace("`", "").replace("‘", "'").replace("’", "'")
    return sql.rstrip(";") + ";"

# --- Login Route ---
@app.route("/", methods=["GET", "POST"])
def login():
    readonly_response = None
    if request.method == "POST":
        if "chat_only" in request.form:
            user_input = request.form.get("chat_query")
            prompt = build_readonly_prompt(user_input)
            readonly_response = model.generate_content(prompt).text.strip()
        else:
            user_id = request.form["user_id"]
            password = request.form["password"]
            with sqlite3.connect("indian_bank_system.db", check_same_thread=False) as con:
                cur = con.cursor()
                cur.execute("SELECT * FROM login WHERE user_id=? AND password=?", (user_id, password))
                if cur.fetchone():
                    session["user_id"] = user_id
                    return redirect("/chat")
                else:
                    return render_template("login.html", error="Invalid credentials.", readonly_response=readonly_response)
    return render_template("login.html", readonly_response=readonly_response)

# --- Chat Route ---
@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "user_id" not in session:
        return redirect("/")

    response = None
    sql_gen = None

    if request.method == "POST":
        query = request.form["query"]
        gemini_prep = build_gemini_prompt(query)
        gemini_response = model.generate_content(gemini_prep).text.strip()

        if "," in gemini_response:
            print(gemini_response)
            tag, content = gemini_response.split(",", 1)
            tag = tag.strip()
            content = content.strip()

            if tag == "A":
                response = content

            elif tag == "B":
                sql = clean_sql(content.replace("{user_id}", session["user_id"]))
                sql_gen = sql
                print(sql_gen)
                try:
                    with sqlite3.connect("indian_bank_system.db", timeout=10, check_same_thread=False) as con:
                        cur = con.cursor()
                        cur.execute(sql)
                        rows = cur.fetchall()
                    second_prompt = f"user query: {query}, generated SQL: {sql}, SQL results: {rows}. Previous chat for context: {prevchat}. Frame an appropriate natural response."
                    response = model.generate_content(second_prompt).text.strip()
                except Exception as e:
                    response = f"❌ SQL Error: {str(e)}"

            elif tag == "C":
                try:
                    loan_data = json.loads(content)
                    loantype = loan_data.get("loantype")
                    amount = float(loan_data.get("amount"))
                    duration = int(loan_data.get("duration"))

                    interest = knowledge['interest_rates'].get(loantype)
                    if not interest:
                        response = "❌ Invalid loan type."
                    else:
                        interest_due = round((amount * interest * duration / 36500), 2)
                        applied = datetime.now().strftime("%Y-%m-%d")
                        loanid = f"LN{int(datetime.now().timestamp())}"[-6:]
                        with sqlite3.connect("indian_bank_system.db", timeout=10, check_same_thread=False) as con:
                            cur = con.cursor()
                            cur.execute("""
                                INSERT INTO loans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (loanid, session["user_id"], loantype, amount, duration, interest, interest_due, applied, "pending"))
                            con.commit()
                        response = f"✅ Loan application submitted for ₹{amount} at {interest}% interest."
                except Exception as e:
                    response = "❌ Loan application failed. Please provide proper loantype, amount, duration."

        else:
            response = "⚠️ Unable to understand Gemini's response."

        prevchat.append({"user": query, "response": response})

    return render_template("chat.html", response=response.replace('$', '₹'), sql_gen=sql_gen, user_id=session["user_id"])

# --- Logout ---
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
