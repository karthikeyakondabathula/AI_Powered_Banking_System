
# 💻 AI-Powered Internet Banking Assistant

This project is an intelligent banking chatbot built using **Flask**, **SQLite**, and **Gemini Flash API**. It allows users to interact with their banking system securely via natural language.

---

!(Output Screenshot 1)[output_1.png]
!(Output Screenshot 2)[output_2.png]
## 🚀 Features

- 🔐 User Login System
- 🤖 General Banking Questions via Read-Only Chatbot
- 🧠 Gemini-powered Chatbot for:
  - A: General Questions (Knowledge-based)
  - B: Database Actions via Secure SQL Query
  - C: Loan Application Module
- 💾 SQLite Backend with Schema for:
  - LOGIN, USERS, CARDS, LOANS, TRANSACTIONS
- 🔄 Multi-turn Context-Aware Chat
- 🛡️ Built-in SQL Cleaner & Safety Filters

---

## 🧱 Tech Stack

- Python 3.x
- Flask
- SQLite3
- Google Gemini API (generativeai)
- HTML (Jinja Templates)

---

## 🧠 System Workflow

1. **Start**
2. **Ask Question / Login**
3. If General Question → Read-Only Chatbot (Class A)
4. If Login → Verify Credentials → Chat Interface
5. On Each Query:
   - A: Return Answer from Knowledge Base
   - B: Generate SQL, Execute Safely, Return Result
   - C: Parse & Submit Loan Application
6. Repeat Until Logout

---

## 📦 Setup Instructions

1. Clone the Repository
2. Install Dependencies:
    ```bash
    pip install flask google-generativeai
    ```
3. Add your Gemini API Key in `app.py`
4. Ensure `indian_bank_system.db` & `knowledge.json` are present
5. Run the App:
    ```bash
    python app.py
    ```
6. Visit: [http://localhost:5000](http://localhost:5000)

---

## 📂 File Structure

```
├── app.py                # Main Flask application
├── knowledge.json        # Contains bank-related facts and schema
├── indian_bank_system.db # SQLite DB with banking tables
├── templates/
│   ├── login.html
│   └── chat.html
```

---

## 📌 Notes

- All user actions are confined to their `user_id`
- No unrelated queries (weather/news) are allowed
- Prevents SQL injection & unauthorized data access

---

## 🤝 Credits

Built by: [Your Name]  
For: HSBC x T-Hub Hackathon — Problem Statement 2 (AI Fraud-Resistant System)
