
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, date as dt



# ---- Simple Login ----
st.set_page_config(page_title="Expense Tracker", layout="wide")

from PIL import Image
logo = Image.open(r"C:\Users\snega\Downloads\eXPENSE tRANCKER.png")
st.sidebar.image(logo, use_column_width=True)

st.title("🧾 Personal Expense Tracker")

users = {
    "snegab": "sbtrack789",
    "harshitb": "hbtrack654",
    "gayathrip": "gptrack321S"
}

# Login Form
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.sidebar.title("🔐 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if username in users and users[username] == password:
            st.session_state["logged_in"] = True
            st.session_state["user"] = username
            st.success(f"Welcome, {username} 👋")
        else:
            st.error("Invalid credentials.")
    st.stop()

# ---- App Content for Logged-in User ----
user = st.session_state["user"]
st.sidebar.success(f"Logged in as: {user}")

# ---- Logout Button ----
if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.session_state.pop("user", None)
    st.rerun()

filename = f"expenses_{user}.csv"

# ---- Sidebar for Monthly Income ----
st.sidebar.header("💰 Monthly Income")
monthly_income = st.sidebar.number_input("Enter your income for the month", min_value=0.0, format="%.2f")

# ---- Input Form ----
st.header("Add New Expense")
st.markdown("📅 Select a date from the calendar below:")
date = st.date_input("Date", value=dt.today(), min_value=dt(2020, 1, 1), max_value=dt.today())
category = st.selectbox("Category", ["Groceries", "Transport", "Monthly Bills", "Entertainment","Shopping", "Savings" , "Take Out"])
currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"])
amount = st.number_input("Amount", min_value=0.0, format="%.2f")
desc = st.text_input("Description")

# Conversion logic
conversion_rates = {"INR": 1.0, "USD": 83.0, "EUR": 90.0, "GBP": 104.0}
amount_in_inr = amount * conversion_rates[currency]

if st.button("Add Expense"):
    new_data = pd.DataFrame([[str(date), category, amount_in_inr, desc]], 
                            columns=["Date", "Category", "Amount", "Description"])
    try:
        old_data = pd.read_csv(filename)
        duplicate = old_data[
            (old_data["Date"] == str(date)) &
            (old_data["Category"] == category) &
            (old_data["Amount"] == amount_in_inr) &
            (old_data["Description"] == desc)
        ]
        if not duplicate.empty:
            st.warning("This expense already exists.")
        else:
            updated_data = pd.concat([old_data, new_data], ignore_index=True)
            updated_data.to_csv(filename, index=False)
            st.success(f"Expense added and converted to ₹{amount_in_inr:.2f}")
    except FileNotFoundError:
        new_data.to_csv(filename, index=False)
        st.success(f"Expense added and converted to ₹{amount_in_inr:.2f}")

# ---- Load and Display Data ----
st.header("📑 All Expenses")
try:
    df = pd.read_csv(filename)
    df["Date"] = pd.to_datetime(df["Date"])
    st.dataframe(df)
except FileNotFoundError:
    st.info("No expenses added yet.")
    df = pd.DataFrame()

if not df.empty:
    df["Month"] = df["Date"].dt.to_period("M")
    df["Weekday"] = df["Date"].dt.day_name()

    st.subheader("📈 Monthly Spend Trend")
    monthly_spend = df.groupby("Month")["Amount"].sum()
    st.line_chart(monthly_spend)

    st.subheader("📊 Category Spending Trend Over Time")
    category_trend = df.groupby([df["Date"].dt.to_period("M"), "Category"])["Amount"].sum().unstack().fillna(0)
    st.line_chart(category_trend)

    st.subheader("📆 Top 3 Highest Expense Days")
    top_days = df.groupby("Date").agg({'Amount':'sum' , 'Category':'first'}).sort_values(by="Amount", ascending=False).head(3)
    st.dataframe(top_days.reset_index())

    st.subheader("📊 Spend by Category (% of Income)")
    selected_month = st.selectbox("Select a month to analyze", df["Month"].astype(str).unique())
    month_df = df[df["Month"].astype(str) == selected_month]

    avg_spend = df["Amount"].mean()
    st.metric("📈 Average Spend Per Transaction", f"₹{avg_spend:.2f}")

    cumulative_df = monthly_spend.reset_index()
    cumulative_df["Cumulative"] = cumulative_df["Amount"].cumsum()
    st.subheader("📉 Cumulative Spending Over Time")
    st.line_chart(cumulative_df.set_index("Month")[["Cumulative"]])

    st.subheader("📊 Category Spending Volatility")
    monthly_cat = df.groupby([df["Date"].dt.to_period("M"), "Category"])["Amount"].sum().unstack().fillna(0)
    volatility = monthly_cat.std().sort_values(ascending=False)
    st.bar_chart(volatility)

    st.subheader("🚨 Outlier Transactions (High Spend)")
    q1 = df["Amount"].quantile(0.25)
    q3 = df["Amount"].quantile(0.75)
    iqr = q3 - q1
    outliers = df[df["Amount"] > (q3 + 1.5 * iqr)]
    st.dataframe(outliers)

    if monthly_income > 0 and not month_df.empty:
        category_spend = month_df.groupby("Category")["Amount"].sum()
        for cat, amt in category_spend.items():
            percent = (amt / monthly_income) * 100
            st.metric(label=f"{cat}", value=f"₹{amt:.2f}", delta=f"{percent:.1f}% of income")
    elif monthly_income == 0:
        st.info("Please enter your monthly income in the sidebar.")
