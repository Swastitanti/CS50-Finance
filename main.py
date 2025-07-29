#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
from flask import Flask, render_template, request, redirect, session, \
    url_for
from flask_sqlalchemy import SQLAlchemy
from argon2 import PasswordHasher

import json

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY'] = 'the random string'    
db = SQLAlchemy(app)
ph = PasswordHasher()

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


def getQuotePrice(symbol):
    api_key = "vrte2uzCQ7EkwRB9O75KNniqF5DZLI6z"  # Replace with your actual API key from financialmodelingprep.com
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={api_key}"

    try:
        response = requests.get(url)
        data = response.json()

        if data and isinstance(data, list) and "price" in data[0]:
            print(f"{symbol} price: {data[0]['price']}")
            return data[0]["price"]
        else:
            print("Invalid symbol or data not found.")
            return None
    except Exception as e:
        print("Error while fetching quote:", e)
        return None



@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:

        try:
            email = request.form['email']
            password = request.form['password']
            data = User.query.filter_by(email=email).first()
            
            if (data is not None) and ph.verify(data.password, password):
                session['user'] = data.id
                print (session['user'])
                return redirect(url_for('home'))
            return render_template('incorrect_login.html')
        except:
            return render_template('incorrect_login.html')



@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashedPassword = ph.hash(request.form['password'])
        new_user = User(email=request.form['email'],
                        password=hashedPassword)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))



#############################################################################

@app.route('/home')
def home():
    # s = Stock.query.filter_by(owner_id =user_id).first()
    user_id = session['user']
    u = User.query.get(user_id)
    stock = Stock.query.all()

    return render_template('home.html', stock=stock, user=user_id, cash=u.cash_in_hand)

@app.route('/show')
def show():
    show_user = User.query.all()
    return render_template('show.html', show_user=show_user)


@app.route('/stock')
def stock():
    stock = Stock.query.all()
    return render_template('show.html', stock=stock)



#############################################################################

@app.route('/quote', methods=['GET', 'POST'])
def quote():
    # If the user is submitting the form (POST method)
    if request.method == 'POST':
        
        # Get the symbol from the form input field named "quote"
        symbol = request.form.get('quote')

        # If no symbol was entered, show an error page
        if not symbol:
            return render_template('404.html', display_content='No quote provided')

        # Use your helper function to fetch the stock price
        quote = getQuotePrice(symbol)

        # If the quote function returned None (meaning symbol was invalid or API failed)
        if quote is None:
            return render_template('404.html', display_content='Could not retrieve stock price')

        # If a valid quote was returned, pass it to the template and show it
        return render_template('quote.html', quote=quote)

    # If the user just opened the page (GET method), show the form without any quote yet
    return render_template('quote.html')




#############################################################################

@app.route('/buy', methods=['GET', 'POST'])
def buy():
    if request.method == 'POST':
        # Get form data
        symbol = request.form.get('symbol').upper().strip()
        shares = request.form.get('shares')

        # Check if user left symbol blank
        if not symbol:
            return render_template('404.html', display_content='No symbol provided')

        try:
            # Get current stock price
            price = getQuotePrice(symbol)
            if price is None:
                return render_template('404.html', display_content='Could not retrieve stock price')

            # Convert shares to int
            try:
                shares = int(shares)
            except ValueError:
                return render_template('404.html', display_content='Invalid number of shares')

            # Calculate total cost
            total_cash_spend = price * shares

            # Get current user
            user_id = session.get('user')
            if not user_id:
                return redirect(url_for('login'))  # If not logged in

            u = User.query.get(user_id)

            # Check if user has enough balance
            if u.cash_in_hand >= total_cash_spend:
                # Deduct cash
                u.cash_in_hand -= total_cash_spend

                # Check if stock already exists in user portfolio
                s = Stock.query.filter_by(owner_id=user_id, name=symbol).first()

                if s:
                    s.qty += shares
                    s.price = price  # Optionally update to latest price
                else:
                    # Create new stock entry
                    new_stock = Stock(name=symbol, qty=shares, owner_id=user_id, price=price)
                    db.session.add(new_stock)

                # Record the transaction
                new_trans = Transcation(type='Bought', name=symbol, qty=shares, owner_id=user_id)
                db.session.add(new_trans)

                db.session.commit()

                return redirect(url_for('home'))
            else:
                return render_template('404.html', display_content='Insufficient balance to complete purchase')

        except Exception as e:
            print("Error while buying:", e)
            return render_template('404.html', display_content='Something went wrong while processing your request')

    # If GET request, show the buy page
    return render_template('buy.html')




#############################################################################

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if request.method == 'POST':
        symbol = request.form['symbol']
        shares = request.form['shares']

        if not request.form.get('symbol'):
            return render_template('404.html',display_content='No symbol provided')

        try:
            price = getQuotePrice(symbol)
            if price is None:
                return render_template('404.html', display_content='Could not retrieve stock price')
            total_cash_spend = price * int(shares)
            user_id = session['user']
            u = User.query.get(user_id)
            s = Stock.query.filter_by(owner_id=user_id, name=symbol).first()
            print (s.name, 'and symbol - ', symbol)
            if s.name == symbol and s.qty > 0:
                final_cash_in_hand = u.cash_in_hand + total_cash_spend
                print ('final= ', final_cash_in_hand)
                u.cash_in_hand = final_cash_in_hand
                final_qty = s.qty - int(shares)
                print ('final qty', final_qty)
                s.qty = final_qty
                new_transcation = Transcation(type='Sold', name=symbol, qty=shares, owner_id=u.id)
                db.session.add(new_transcation)
                db.session.commit()
                return redirect(url_for('home'))
            else:
                return render_template('404.html',display_content='Insufficient shares to sell')

        except:
            return render_template('404.html', display_content='123Invalid symbol. No quote available')
    else:
    # GET method
        return render_template('sell.html')



#############################################################################

@app.route('/history')
def history():
    transcation = Transcation.query.all()
    user_id = session['user']
    return render_template('history.html', transcation=transcation, user=user_id)



#############################################################################


if __name__ == '__main__':
    #Added secret key that the top app.secret_key = 'super secret key'
    with app.app_context():
        db.create_all()
    app.run(debug=True)