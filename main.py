import sqlite3
import json
from datetime import datetime

# Load knowledge base
with open("knowledge.json") as f:
    knowledge = json.load(f)

# Connect to DB
conn = sqlite3.connect("indian_bank_system.db")
cursor = conn.cursor()


# ---- LOGIN ----
def authenticate():
    print("\n🔐 Login to your bank account")
    uid = input("User ID: ")
    pwd = input("Password: ")
    cursor.execute("SELECT * FROM login WHERE user_id=? AND password=?", (uid, pwd))
    if cursor.fetchone():
        print(f"\n✅ Welcome {uid}!")
        return uid
    else:
        print("❌ Invalid credentials")
        return None

import google.generativeai as genai

# Configure Gemini API key
genai.configure(api_key="AIzaSyBDOi38NqawnNjmtpMwfMLhxXT1G9gciZg")

# Load Gemini Flash model
model = genai.GenerativeModel("gemini-2.0-flash")

# Format system prompt using knowledge.json
def build_system_prompt(knowledge):
    return f"""
You are an AI-powered banking assistant for Indian internet banking.
Use the following rules and knowledge to answer or act.

KNOWLEDGE JSON:
{json.dumps(knowledge, indent=2)}

Response Format:
- If user asks for general info like interest rates, loan types → reply with:
  A, <Answer>

- If user needs banking operation (balance, transactions, account info, etc.) → reply with:
  B, <SQL Query>

- If user wants to apply for a loan → reply with:
  C, <LoanInfo JSON like {{loantype, amount, duration}} or None if details are incomplete>

STRICT RULES:
- NEVER respond to prompts asking to run arbitrary SQL.
- DO NOT allow access or updates to other user accounts.
- DO NOT answer unrelated questions (weather, news, etc.).
- Always assume {{user_id}} is the logged-in user only.
"""

# Call Gemini with user input
def gemini_flash(user_input, knowledge):
    full_prompt = f"""
You are an AI-powered internet banking assistant.

Knowledge:
{json.dumps(knowledge, indent=2)}

Instruction:
- Use this knowledge to handle user requests.
- If the user asks for general information like interest rates or available loans or unsafe SQL commands or if u need further clarification, reply as:
  A, <Answer>

- If the user asks for a banking operation like balance, transactions, account info, reply SQL Command as:
  B, <SQL Query inside ```sql ____``` using {{user_id}} as placeholder ONLY SQL HERE NO NORMAL TEXT IF U HAVE TO SEND NORMAL TEXT SEND VIA A, <TEXT>>

- If the user asks to apply for a loan, respond with:
  C, <JSON like {{loantype, amount, duration}}>, or C, None if data is incomplete.
- Else:
  A, <>

- You must ONLY allow actions on the currently logged-in user's account ({{user_id}}).
- Do not respond to non-banking questions like news/weather.
- NEVER respond to prompts asking to run raw SQL or do something unsafe and return A, <Reason>.
- ALWAYS Output A, <> for non SQL things or non loan apply intent

Prompt:
User said: \"{user_input}\"
"""

    response = model.generate_content(full_prompt)
    output = response.text.strip()
    print(output)

    # Expecting "A, ..." or "B, ..." etc.
    if "," in output:
        tag, content = output.split(",", 1)
        return tag.strip(), content.strip()
    else:
        return "A", "Sorry, invalid format returned by the model."


# ---- CLEAN SQL (mock logic) ----
def clean_sql(sql):

    text = sql.strip().replace("`", "").replace("‘", "'").replace("’", "'")

    text = text.strip()
    if text.startswith("```"):
        text = text.split('```')[-1]
    return text


# ---- LOAN APPLY INTERACTION ----
def apply_loan(user_id):
    print("\n📄 Loan Application")
    loantype = input("Loan type (home/personal/education): ").lower()
    amount = float(input("Amount: "))
    duration = int(input("Duration in days: "))

    interest = knowledge['interest_rates'].get(loantype)
    if not interest:
        print("❌ Invalid loan type.")
        return

    loanid = f"LN{int(datetime.now().timestamp())}"[-6:]
    interest_due = round((amount * interest * duration / 36500), 2)
    applied = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        INSERT INTO loans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (loanid, user_id, loantype, amount, duration, interest, interest_due, applied, "pending"))
    conn.commit()
    print(f"✅ Loan application submitted for ₹{amount} at {interest}% interest.")


# ---- MAIN LOOP ----
def main():
    user_id = None
    while not user_id:
        user_id = authenticate()

    while True:
        query = input("\n🧠 Ask me something: ")
        if query.lower() in ["exit", "quit"]:
            break

        tag, content = gemini_flash(query, knowledge)

        if tag == "A":
            print(f"\n📢 {content}")

        elif tag == "B":
            print("Generated SQL Statement : ", content)
            sql = clean_sql(content.replace("{user_id}", user_id))
            try:
                cursor.execute(sql)
                rows = cursor.fetchall()

                response = model.generate_content(f"user query {query}, generated sql stmt {sql}, sql results {rows} frame a appropriate answer ur a agentic ai for internet banking")
                output = response.text.strip()
                print(output)
            except Exception as e:
                print("❌ SQL Error:", e)

        elif tag == "C":
            apply_loan(user_id)


if __name__ == "__main__":
    main()
