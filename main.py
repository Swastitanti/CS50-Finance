import os
import requests
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from argon2 import PasswordHasher

# Load API Key
api_key = os.getenv("ALPHA_VANTAGE_KEY")
# print("API Key loaded:", api_key is not None)

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
# app.config['SECRET_KEY'] = 'the random string'
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "fallback-secret")

db = SQLAlchemy(app)
ph = PasswordHasher()

# ====================== DATABASE MODELS ======================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50))
    password = db.Column(db.String(100))
    cash_in_hand = db.Column(db.Integer, default=500)
    stock = db.relationship('Stock', backref='owner')

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    qty = db.Column(db.Integer)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    price = db.Column(db.Float)

class Transcation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    name = db.Column(db.String(50))
    qty = db.Column(db.Integer)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# ====================== HELPER FUNCTION ======================
def getQuotePrice(symbol):
    """Fetch real-time stock price from Alpha Vantage"""
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        quote = data.get("Global Quote", {})
        price = quote.get("05. price")
        if price:
            return float(price)
        return None
    except Exception as e:
        print("Error while fetching quote:", e)
        return None


# ====================== AUTH ROUTES ======================
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form.get('email')
    password = request.form.get('password')
    if not email or not password:
        return render_template('incorrect_login.html')

    user = User.query.filter_by(email=email).first()
    if user:
        try:
            if ph.verify(user.password, password):
                session['user'] = user.id
                return redirect(url_for('home'))
        except:
            pass
    return render_template('incorrect_login.html')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashedPassword = ph.hash(request.form['password'])
        new_user = User(email=request.form['email'], password=hashedPassword)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# ====================== MAIN PAGES ======================
@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']
    user = User.query.get(user_id)
    stock = Stock.query.filter_by(owner_id=user_id).all()
    return render_template('home.html', stock=stock, user=user_id, cash=user.cash_in_hand)

@app.route('/show')
def show():
    show_user = User.query.all()
    return render_template('show.html', show_user=show_user)

@app.route('/stock')
def stock():
    stock = Stock.query.all()
    return render_template('show.html', stock=stock)

# ====================== QUOTE ======================
@app.route('/quote', methods=['GET', 'POST'])
def quote():
    if request.method == 'POST':
        symbol = request.form.get('quote')
        if not symbol:
            return render_template('404.html', display_content='No symbol provided')

        symbol = symbol.upper().strip()
        price = getQuotePrice(symbol)
        if price is None:
            return render_template('404.html', display_content='Invalid symbol or API error')

        return render_template('quote.html', quote=price, symbol=symbol)

    # GET request
    return render_template('quote.html')

# ====================== BUY ======================
@app.route('/buy', methods=['GET', 'POST'])
def buy():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        symbol = request.form.get('symbol', '').upper().strip()
        shares = request.form.get('shares')

        if not symbol:
            return render_template('404.html', display_content='No symbol provided')

        price = getQuotePrice(symbol)
        if price is None:
            return render_template('404.html', display_content='Invalid symbol or API error')

        try:
            shares = int(shares)
        except:
            return render_template('404.html', display_content='Invalid number of shares')

        user_id = session['user']
        u = User.query.get(user_id)
        total_cost = price * shares

        if u.cash_in_hand < total_cost:
            return render_template('404.html', display_content='Insufficient balance')

        u.cash_in_hand -= total_cost
        s = Stock.query.filter_by(owner_id=user_id, name=symbol).first()
        if s:
            s.qty += shares
            s.price = price
        else:
            new_stock = Stock(name=symbol, qty=shares, owner_id=user_id, price=price)
            db.session.add(new_stock)

        new_trans = Transcation(type='Bought', name=symbol, qty=shares, owner_id=user_id)
        db.session.add(new_trans)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('buy.html')

# ====================== SELL ======================
@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        symbol = request.form.get('symbol', '').upper().strip()
        shares = request.form.get('shares')

        if not symbol:
            return render_template('404.html', display_content='No symbol provided')

        price = getQuotePrice(symbol)
        if price is None:
            return render_template('404.html', display_content='Invalid symbol or API error')

        try:
            shares = int(shares)
        except:
            return render_template('404.html', display_content='Invalid number of shares')

        user_id = session['user']
        u = User.query.get(user_id)
        s = Stock.query.filter_by(owner_id=user_id, name=symbol).first()

        if not s or s.qty < shares:
            return render_template('404.html', display_content='Insufficient shares to sell')

        s.qty -= shares
        u.cash_in_hand += price * shares

        new_trans = Transcation(type='Sold', name=symbol, qty=shares, owner_id=user_id)
        db.session.add(new_trans)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('sell.html')

# ====================== HISTORY ======================
@app.route('/history')
def history():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']
    transcation = Transcation.query.filter_by(owner_id=user_id).all()
    return render_template('history.html', transcation=transcation, user=user_id)

# ====================== MAIN ======================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
