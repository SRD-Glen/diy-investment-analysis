from datetime import datetime
import json
import requests
import streamlit as st
import pandas_ta as ta
import time
import pandas as pd
import altair as alt
from urllib.error import URLError
# Read stocks
import yfinance as yf
# For plotting
import plotly.graph_objects as go
from plotly.subplots import make_subplots


MARGIN = dict(l=0,r=10,b=10,t=25)


st.set_page_config(page_title="Long term", page_icon="🐢")
st.toast("Disclaimer: The information provided in this app is solely for educational purposes and is not intended to be personal financial, investment or other advice.")

def read_yf(yf_data, ticker, start_date):
    # print('Start date: {}'.format(start_date))
    df = pd.DataFrame()
    try:
        df = yf_data.history(start=start_date)[['Open', 'Close', 'Volume']]
    except Exception as e:
        print("The error is: ", e)
    if not df.empty:
        # Create a Date column
        df['Date'] = df.index.date
        # Drop the Date as index
        df.reset_index(drop=True, inplace=True)
        # Added extra columns
        df['Ticker'] = ticker
        df['Refreshed Date'] = datetime.now()
        # Calculate the MAs for graphs
        df['SMA-50'] = ta.sma(df["Close"], length=50)
        df['SMA-200'] = ta.sma(df["Close"], length=200)
    return df

def date_breaks(df):
    # build complete timeline from start date to end date
    dt_all = pd.date_range(start=df.iloc[0]['Date'], end=df.iloc[-1]['Date'])
    # retrieve the dates that are in the original datset
    dt_obs = [d.strftime("%Y-%m-%d") for d in pd.to_datetime(df['Date'])]
    # define dates with missing values
    return [d for d in dt_all.strftime("%Y-%m-%d").tolist() if not d in dt_obs]


st.title(":rainbow[Investing Strategies]")
st.write("""Investment strategies are set of principles that guide long term investment decisions.""")


st.sidebar.header("Long term investing!")
# st.sidebar.markdown("### Select atleast one strategy from below")
with st.sidebar.container(height=300, border=False):
    detail = st.radio(
        "How detail do you want to analyze?",
        ["**Macro**", "**Meso**", "Micro :movie_camera:"],
        captions = ["Laugh out loud.", "Get the popcorn.", "Never stop learning."])


tab1, tab2, tab3 = st.tabs(["Choice of ETF", "Momentum portfolio", "TBD..."])
with tab1:
    ticker = "AUTOBEES.NS"
    st.header("Nippon India Nifty Auto ETF:gray[(NSE: AUTOBEES)]")
    st.write("This week's choice of ETF!")
    st.divider()

    # YF object to read financial data
    yf_data = yf.Ticker(ticker)

    price_change = yf_data.info['currentPrice'] - yf_data.info['previousClose']
    price_change_ratio = (abs(price_change) / yf_data.info['previousClose'] * 100)
    price_change_direction = lambda i: ("+" if i > 0 else "-")

    st.metric(label='Current Price', value=round(yf_data.info['currentPrice'], 2), delta="{:.2f} ({}{:.2f}%)".format(
        price_change, price_change_direction(price_change), price_change_ratio))
    
    if detail != "**Macro**":
        col1, col2, col3, col4 = st.columns([1,1,1,1])
        with col1:
            st.text('Previous Close')
            st.text(yf_data.info['previousClose'])
            if detail == "Micro :movie_camera:":
                st.divider()
                st.text('50-Day Average')
                st.text('{0:.2f}'.format(yf_data.info['fiftyDayAverage']))
        with col2:
            st.text('Open')
            st.text(yf_data.info['open'])
            if detail == "Micro :movie_camera:":
                st.divider()
                st.text('200-Day Average')
                st.text('{0:.2f}'.format(yf_data.info['twoHundredDayAverage']))
        with col3:
            st.text('Day\'s Range')
            st.text('{0} - {1}'.format(yf_data.info['dayLow'], yf_data.info['dayHigh']))
            if detail == "Micro :movie_camera:":
                st.divider()
                st.text('Average Volume')
                st.text('{:,}'.format(yf_data.info['averageVolume']))
            
        with col4:
            st.text('52-Week Range')
            st.text('{0:.2f} - {1:.2f}'.format(yf_data.info['fiftyTwoWeekLow'], yf_data.info['fiftyTwoWeekHigh']))
            if detail == "Micro :movie_camera:":
                st.divider()
                st.text('Volume')
                st.text('{:,}'.format(yf_data.info['volume']))
    st.divider()

    # Fetch historical data
    start_date = datetime.now() + pd.DateOffset(years=-2)
    # Read YF data
    df = read_yf(yf_data, ticker, start_date)

    # Construct a 2 x 1 Plotly figure for MA and Volume charts
    fig = make_subplots(rows=2, cols=1, vertical_spacing=0.01, shared_xaxes=True)
    # Remove dates without values
    fig.update_xaxes(rangebreaks=[dict(values=date_breaks(df))])

    # Plot the Price chart
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='Price', marker_color='#C39BD3'),
                    row=1, col=1)
    # Color maps for different MAs
    COLORS_MAPPER = {
        'SMA-50': '#38BEC9',
        'SMA-200': '#E67E22'
    }
    for ma, col in COLORS_MAPPER.items():
        fig.add_trace(go.Scatter(x=df['Date'], y=df[ma], name=ma, marker_color=col))

    # Colours for the Bar chart
    colors = ['#B03A2E' if row['Open'] - row['Close'] >= 0 
        else '#27AE60' for index, row in df.iterrows()]
    
    if detail != "**Macro**":
        # Adds the volume as a bar chart
        fig.add_trace(go.Bar(x=df['Date'], y=df['Volume'], showlegend=False, marker_color=colors), row=2, col=1)
    # plot the chart
    layout = go.Layout(title='Price chart', height=500, margin=MARGIN)
    fig.update_layout(layout)
    st.plotly_chart(fig, theme='streamlit', use_container_width=True)
        
       
with tab2:
    hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """
    
    st.header("Top performing stocks!")

    if st.button("Scan Stocks"):
        # progress_bar = st.sidebar.progress(0, text="Initializing...")
        # time.sleep(1)
        # progress_bar.progress(50, text="⏳ Fetching data...")
        # time.sleep(1)
        # progress_bar.progress(100, text="Complete...")
        # time.sleep(1)
        # progress_bar.empty()

        with st.spinner("⏳ Fetching data..."):
            api_url = "https://je1joyu2ga.execute-api.ap-south-1.amazonaws.com/stocks"
            payload = {}
            headers = {}
            response_mr = requests.request(
                "GET", api_url, headers=headers, data=payload
            )
            data = json.loads(response_mr.text)
            st.text("")
            df = pd.DataFrame(data["stocks"])
            df.rename(columns={"tradingSymbol": "Stock Name"}, inplace=True)
            st.markdown(hide_table_row_index, unsafe_allow_html=True)
            st.caption("Trade Date: " + data["date"])
            st.table(df["Stock Name"])

with tab3:
    st.header("Coming soon!")

# @st.cache_data
# def get_trade_data():
#     # Fetch past trade logs from Mongo Db
#     ...


# try:
#     get_trade_data()
# except URLError as e:
#     st.error("""**This demo requires internet access.**Connection error: %s""" % e.reason)