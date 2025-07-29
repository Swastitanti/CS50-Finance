# 💸 Finance Tracker

A web-based finance application built for CS50x Final Project that lets users manage their stock portfolio, track spending goals, and analyze historical transactions. Built with **Flask**, **SQLite**, **Bootstrap**, and integrated with **Financial Modeling Prep API** for real-time stock data.

---

## 🧠 Project Functionality

- Register: Any person can register to make a new account.
- Quote: A registered user can quote a price for a stock.
- Buy: Users can buy shares for a price.
- Index: Shows the stocks in the user's account.
- Sell: Users can sell shares of a stock.
- History: Users can view past transaction history.

---

## 🚀 Features

- 🔐 User Registration & Login (hashed passwords using Argon2)
- 💵 Simulated Cash Balance & Stock Transactions
- 📈 Real-time Stock Quote Lookup
- 📊 Transaction History & Portfolio Overview
- 📉 Error Handling & 404 Support

---

## 🛠️ Tech Stack

- **Frontend**: HTML, CSS (Bootstrap 5), JavaScript
- **Backend**: Flask (Python), SQLAlchemy
- **Database**: SQLite (`db.sqlite3`)
- **API**: [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs)
- **Auth**: Argon2 for secure password hashing

---

### 📝 Register
![Register](static/screenshots/register.png)

### 🔐 Login
![Login](static/screenshots/login.png)

### 🏠 Home (Dashboard)
![Home](static/screenshots/home.png)

### 💬 Quote
![Quote](static/screenshots/quote.png)

### 🛒 Buy Stocks
![Buy](static/screenshots/buy.png)

### 💼 Sell Stocks
![Sell](static/screenshots/sell.png)

### 📜 Transaction History
![History](static/screenshots/history.png)

---

## ⚙️ Setup Instructions (Local)

1. Clone the project:
   ```bash
   git clone https://github.com/Swastitanti/CS50-Finance.git
   cd finance-project

---

## Installation-

## 1. Download and unzip the project files provided by CS50
wget https://cdn.cs50.net/2024/fall/psets/9/finance.zip
unzip finance.zip
cd finance

## 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate   # For Windows

## 3. Install required packages
pip install flask flask_sqlalchemy argon2-cffi

### 4. Freeze dependencies into requirements.txt
pip freeze > requirements.txt

# 5. Rename the main application file (if needed)
ren app.py main.py   # Use 'mv app.py main.py' for Mac/Linux

# 6. Create the SQLite database (this will auto-generate db.sqlite3)
sqlite3 db.sqlite3
.exit

# 7. Run the Flask application
python main.py
# OR
flask --app main run
