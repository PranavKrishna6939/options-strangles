import streamlit as st
from datetime import timedelta
import datetime
import pandas as pd
import time
import sys

offset = datetime.timedelta(hours=5, minutes=30)
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)
st.title("""Nifty Strangle :green[PNL] Tracker""")
st.divider()

while True:
    now = datetime.datetime.now()
    tstamp = now + offset
    tstamp = tstamp.strftime("%H:%M:%S")
    today = datetime.datetime.now().date().strftime("%d_%m_%Y")

    placeholder4 = st.empty()
    with placeholder4.container():
        st.metric("Time", f"{tstamp}")
        st.header("""Market is :red[Closed]""")

    while ((tstamp > "09:25:00") and (tstamp < "15:21:00")):
        placeholder4.empty()
        now = datetime.datetime.now()
        tstamp = now + offset
        tstamp = tstamp.strftime("%H:%M:%S")

        if (tstamp > "15:20:00"):
            print(f"DAY ENDED!")
            sys.exit(101)

        df = pd.read_csv(f'Trade_Logs_{today}.csv')
        i = len(df)-1
        curr_pnl = df.loc[i, 'Call Entry'] + df.loc[i, 'Put Entry'] - df.loc[i, 'Put LTP'] - df.loc[i, 'Call LTP']
        curr_pnl = round(curr_pnl, 2)
        re_pnl = df.loc[i, 'PNL'] - curr_pnl
        re_pnl = round(re_pnl, 2)
        placeholder = st.empty()
        with placeholder.container():
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Time", f"{df.loc[i, 'Timestamp']}")
            col2.metric("Nifty 50", f"{df.loc[i, 'Spot']}")
            col3.metric("Current Premium", f"{round(df.loc[i, 'Current Premium'], 2)}")
            col4.metric("Sold Premium", f"{df.loc[i, 'Sold Premium']}")

        placeholder1 = st.empty()
        with placeholder1.container():
            st.text(" ")
            column_names = ["Instrument", "Entry", "Current", "PNL" ]
            display = pd.DataFrame(columns=column_names)
            display.loc[0, 'Instrument'] = df.loc[i, 'Call Strike']
            display.loc[0, 'Entry'] = df.loc[i, 'Call Entry']
            display.loc[0, 'Current'] = df.loc[i, 'Call LTP']
            display.loc[0, 'PNL'] = round(df.loc[i, 'Call Entry'] - df.loc[i, 'Call LTP'], 2)
            display.loc[1, 'Instrument'] = df.loc[i, 'Put Strike']
            display.loc[1, 'Entry'] = df.loc[i, 'Put Entry']
            display.loc[1, 'Current'] = df.loc[i, 'Put LTP']
            display.loc[1, 'PNL'] = round(df.loc[i, 'Put Entry'] - df.loc[i, 'Put LTP'], 2)
            st.table(display)


        placeholder2 = st.empty()
        with placeholder2.container():
            st.text(" ")
            col1, col2, col3= st.columns(3)
            col1.metric("Realised PNL", f"{re_pnl}")
            col2.metric("Unrealised PNL", f"{curr_pnl}")
            col3.metric("Total PNL", f"{df.loc[i, 'PNL']}")
        
        placeholder3 = st.empty()
        with placeholder3.container():
            st.text(" ")
            df_graph = df[0 : i]
            st.line_chart(df_graph['PNL'], color=["#FFEF00"])
        
        time.sleep(3)
        placeholder.empty()
        placeholder1.empty()
        placeholder2.empty()
        placeholder3.empty()
    time.sleep(60)
    placeholder4.empty()
