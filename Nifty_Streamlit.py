from neo_api_client import NeoAPI
from datetime import datetime
import streamlit as st
import pandas as pd
import datetime
import calendar
import time

# CREDENTIALS
consumer_key = 'key'
consumer_secret = 'key'
mobile_number = 'number'
password = 'password'

st.title("""Nifty Strangle :green[PNL] Tracker""")

def on_message(message):
    print(message)    
def on_error(error_message):
    print(error_message)
client = NeoAPI(consumer_key = consumer_key, consumer_secret = consumer_secret, 
                environment='prod', on_message=on_message, on_error=on_error, on_close=None, on_open=None)
client.login(mobilenumber = mobile_number, password = password)

otp = input("Enter OTP: ")
client.session_2fa(str(otp))

nfo_url = client.scrip_master(exchange_segment = "NFO")
nfo_df = pd.read_csv(nfo_url)
columns_to_keep = ['pSymbol', 'pSymbolName', 'pTrdSymbol', 'pOptionType', 'pExpiryDate', 'dStrikePrice;']
nfo_df = nfo_df.drop(columns=[col for col in nfo_df.columns if col not in columns_to_keep], axis=1)

def get_ltp_index():
    ins_token = [{"instrument_token": "Nifty 50", "exchange_segment": "nse_cm"}]
    try:
        ltp = (client.quotes(instrument_tokens=ins_token, quote_type="ltp", isIndex=True))['message'][0]['last_traded_price']
        return round(float(ltp))
    except Exception as e:
        print("Exception when calling get Quote api->quotes: %s\n" % e)
        return -1

def get_ltp(strike, opt_type, expiry):
    ins_token = [{"instrument_token": str(get_token(strike, opt_type, expiry)) , "exchange_segment": "nse_fo"}]
    try:
        ltp = (client.quotes(instrument_tokens=ins_token, quote_type="ltp", isIndex=False))['message'][0]['ltp']
        return float(ltp)
    except Exception as e:
        print("Exception when calling get Quote api->quotes: %s\n" % e)
        return -1

def get_token(strike, opt_type, expiry):
    tmp = nfo_df[(nfo_df["pSymbolName"] == 'NIFTY') & (nfo_df["pExpiryDate"] == expiry) & (nfo_df["dStrikePrice;"] == strike*100) & (nfo_df["pOptionType"]==opt_type)]
    tmp = tmp.reset_index(drop=True)
    token = int(tmp.loc[0, 'pSymbol'])
    return token

def round_off(num):
    return 50 * round(num/50)

def get_expiry(exp_year, exp_month, exp_day):
    t = datetime.datetime((exp_year-10), exp_month, (exp_day+1), 20, 0, 0)
    return (calendar.timegm(t.timetuple())-19800)

def log_text(message):
    today = datetime.datetime.now().date().strftime("%d_%m_%Y")
    filename = f'Text_Logs_{today}.txt'
    with open(filename, "a") as f:
        f.write(message + "\n")

# EXPIRY
exp_year = 2024
exp_month = 3
exp_day = 28
expiry = get_expiry(exp_year, exp_month, exp_day)
offset = datetime.timedelta(hours=5, minutes=30)

spot = get_ltp_index()
print("Spot price =", spot)
atm_strike = round_off(spot)
print("ATM strike =", atm_strike)

straddle = 0
for option in ["CE", "PE"]:
    tk = get_ltp(atm_strike, option, expiry)
    straddle += tk
print("Straddle price =", straddle)

put_strike = round_off(spot - straddle)
call_strike = round_off(spot + straddle)
print("Put Strike =" , put_strike)
print("Call Strike =" , call_strike)

ltp_put = get_ltp(put_strike, "PE" , expiry)
print(put_strike,"PE =", ltp_put)

ltp_call = get_ltp(call_strike, "CE" , expiry)
print(call_strike,"CE =", ltp_call)

sold_premium = ltp_put + ltp_call
sold_premium = round(sold_premium, 2)
print("Sold premium =", sold_premium)

column_names = ['Index','Timestamp', 'Spot', 'Put Strike','Put LTP', 'Put Entry', 'Call Strike', 'Call LTP', 'Call Entry','Sold Premium', 'Current Premium', 'PNL']
csv_log = pd.DataFrame(columns=column_names)
curr_log = pd.DataFrame(columns=column_names)
i = 0
pnl = 0
curr_pnl = 0
total_pnl = 0
count = 0
max_loss = 0
max_profit = 0

placeholder = st.empty()
placeholder1 = st.empty()
placeholder2 = st.empty()
placeholder3 = st.empty()
placeholder4 = st.empty()
placeholder5 = st.empty()

while True:

    now = datetime.datetime.now()
    tstamp = now + offset
    tstamp = tstamp.strftime("%H:%M:%S")
    print(f"{tstamp} | Market is closed")
    placeholder4.empty()
    with placeholder4.container():
        st.divider()
        st.header(f"{tstamp} | Market is closed")

    if ((tstamp > "09:18:00") and (tstamp < "09:20:00")) :

        spot = get_ltp_index()
        print("Spot price =", spot)
        atm_strike = round_off(spot)
        print("ATM strike =", atm_strike)

        straddle = 0
        for option in ["CE", "PE"]:
            tk = get_ltp(atm_strike, option, expiry)
            straddle += tk
        print("Straddle price =", straddle)

        put_strike = round_off(spot - straddle)
        call_strike = round_off(spot + straddle)
        print("Put Strike =" , put_strike)
        print("Call Strike =" , call_strike)

        ltp_put = get_ltp(put_strike, "PE" , expiry)
        print(put_strike,"PE =", ltp_put)

        ltp_call = get_ltp(call_strike, "CE" , expiry)
        print(call_strike,"CE =", ltp_call)

        sold_premium = ltp_put + ltp_call
        sold_premium = round(sold_premium, 2)
        print("Sold premium =", sold_premium)

        column_names = ['Index','Timestamp', 'Spot', 'Put Strike','Put LTP', 'Put Entry', 'Call Strike', 'Call LTP', 'Call Entry','Sold Premium', 'Current Premium', 'PNL']
        csv_log = pd.DataFrame(columns=column_names)
        i = 0
        pnl = 0
        curr_pnl = 0
        total_pnl = 0
        count = 0
        max_loss = 0
        max_profit = 0

    while ((tstamp > "09:20:00") and (tstamp < "15:25:00")):
        placeholder5.empty()
        now = datetime.datetime.now()
        tstamp = now + offset
        tstamp = tstamp.strftime("%H:%M:%S")

        if (tstamp > "15:20:00") :

            temp = get_ltp(call_strike, "CE" , expiry)
            if (temp != -1):
                pnl += ltp_call - temp
            elif (temp == -1):
                print(f"{tstamp} | Error fetching Quote!")
                log_text(f"{tstamp} | Error fetching Quote!")

            temp = get_ltp(put_strike, "PE" , expiry)
            if (temp != -1):
                pnl += ltp_put - temp
            elif (temp == -1):
                print(f"{tstamp} | Error fetching Quote!")
                log_text(f"{tstamp} | Error fetching Quote!")
  
            pnl = round(pnl, 2)
            if (total_pnl > max_profit):
                max_profit = total_pnl
            elif (total_pnl < max_loss):
                max_loss = total_pnl
            print(f"DAY ENDED! PNL = {total_pnl} | Max Loss = {max_loss} | Total Adjustments = {count} | Max Profit = {max_profit}")
            log_text(f"DAY ENDED! PNL = {total_pnl} | Max Loss = {max_loss} | Total Adjustments = {count} | Max Profit = {max_profit}")
            with placeholder5.container():
                st.divider()
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("PNL", f"{total_pnl}")
                col2.metric("Max Loss", f"{max_loss}")
                col3.metric("Adjustments", f"{count}")
                col4.metric("Max Profit", f"{max_profit}")
            
            today = datetime.datetime.now().date().strftime("%d_%m_%Y")
            csv_log.to_csv(f'Trade_Logs_{today}.csv', index=False)
            break

        change1 = 1
        change2 = 1
        temp = get_ltp_index()

        if (temp != -1):
            spot = temp
        elif (temp == -1):
            print(f"{tstamp} | Error fetching Quote!")
            log_text(f"{tstamp} | Error fetching Quote!")

        new_atm = round_off(spot)
        new_put = round_off(spot - straddle)
        new_call = round_off(spot + straddle)
        end_call = round(spot + straddle)%100

        if ((end_call>= 15 and end_call<=35) or (end_call>= 65 and end_call<=85)):
            change1 = 0
        end_put = round(spot - straddle)%100
        if ((end_put>= 15 and end_put<=35) or (end_put>= 65 and end_put<=85)):
            change2 = 0
        
        if ((new_call != call_strike) and change1 == 1):
            print ("--- Changing Strikes ---")

            temp = get_ltp(call_strike, "CE" , expiry)
            if (temp != -1):
                exit_price = temp
            elif (temp == -1):
                print(f"{tstamp} | Error fetching Quote!")
                log_text(f"{tstamp} | Error fetching Quote!")

            temp = get_ltp(new_call, "CE" , expiry)
            if (temp != -1):
                entry_price = temp
            elif (temp == -1):
                print(f"{tstamp} | Error fetching Quote!")
                log_text(f"{tstamp} | Error fetching Quote!")

            print(f"Exited {call_strike} CE at {exit_price} and entered {new_call} CE at {entry_price}")
            log_text(f"Changing Strikes | Exited {call_strike} CE at {exit_price} and entered {new_call} CE at {entry_price}")

            pnl += ltp_call - exit_price
            pnl = round(pnl, 2)
            call_strike = new_call
            ltp_call = entry_price
            sold_premium = ltp_put + ltp_call
            sold_premium = round(sold_premium, 2)
            count += 1


        elif ((new_put != put_strike) and change2 == 1):
            print ("--- Changing Strikes ---")

            temp = get_ltp(put_strike, "PE" , expiry)
            if (temp != -1):
                exit_price = temp
            elif (temp == -1):
                print(f"{tstamp} | Error fetching Quote!")
                log_text(f"{tstamp} | Error fetching Quote!")

            temp = get_ltp(new_put, "PE" , expiry)
            if (temp != -1):
                entry_price = temp
            elif (temp == -1):
                print(f"{tstamp} | Error fetching Quote!")
                log_text(f"{tstamp} | Error fetching Quote!")

            print(f"Exited {put_strike} PE at {exit_price} and entered {new_put} PE at {entry_price}")
            log_text(f"Changing Strikes | Exited {put_strike} PE at {exit_price} and entered {new_put} PE at {entry_price}")

            pnl += ltp_put - exit_price
            pnl = round(pnl, 2)
            put_strike = new_put
            ltp_put = entry_price
            sold_premium = ltp_put + ltp_call
            sold_premium = round(sold_premium, 2)
            count += 1

        temp = get_ltp(put_strike, "PE" , expiry)

        if (temp != -1):
            curr_put = temp
        elif (temp == -1):
            print(f"{tstamp} | Error fetching Quote!")
            log_text(f"{tstamp} | Error fetching Quote!") 

        temp = get_ltp(call_strike, "CE" , expiry)
        if (temp != -1):
            curr_call = temp 
        elif (temp == -1):
            print(f"{tstamp} | Error fetching Quote!")
            log_text(f"{tstamp} | Error fetching Quote!")

        curr_pnl = sold_premium - curr_put - curr_call
        curr_pnl = round(curr_pnl, 2)
        total_pnl = pnl + curr_pnl
        total_pnl = round(total_pnl, 2)

        if (total_pnl > max_profit):
            max_profit = total_pnl
        elif (total_pnl < max_loss):
            max_loss = total_pnl

        now = datetime.datetime.now()
        tstamp = now + offset
        tstamp = tstamp.strftime("%H:%M:%S")
        print(f"{tstamp} | {put_strike} PE current:{curr_put} entry:{ltp_put} | {call_strike} CE current:{curr_call} entry:{ltp_call} | PNL = {total_pnl}")
        log_text(f"{tstamp} | {put_strike} PE current:{curr_put} entry:{ltp_put} | {call_strike} CE current:{curr_call} entry:{ltp_call} | PNL = {total_pnl}")

        csv_log.loc[i, 'Index'] = i
        csv_log.loc[i, 'Timestamp'] = tstamp
        csv_log.loc[i, 'Spot'] = spot
        csv_log.loc[i, 'Put Strike'] = f"{put_strike} PE"
        csv_log.loc[i, 'Put LTP'] = curr_put
        csv_log.loc[i, 'Put Entry'] = ltp_put
        csv_log.loc[i, 'Call Strike'] = f"{call_strike} CE"
        csv_log.loc[i, 'Call LTP'] = curr_call
        csv_log.loc[i, 'Call Entry'] = ltp_call
        csv_log.loc[i, 'Sold Premium'] = sold_premium
        csv_log.loc[i, 'Current Premium'] = round(curr_put + curr_call, 2)
        csv_log.loc[i, 'PNL'] = total_pnl

        placeholder = st.empty()
        placeholder1 = st.empty()
        placeholder2 = st.empty()
        placeholder3 = st.empty()

        with placeholder.container():
            st.divider()
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Time", f"{tstamp}")
            col2.metric("Nifty 50", f"{spot}")
            col3.metric("Current Premium", f"{round(curr_put + curr_call, 2)}")
            col4.metric("Sold Premium", f"{sold_premium}")

        with placeholder1.container():
            st.text(" ")
            column_names = ["Instrument", "Entry", "Current", "PNL" ]
            display = pd.DataFrame(columns=column_names)
            display.loc[0, 'Instrument'] = f"{call_strike} CE"
            display.loc[0, 'Entry'] = ltp_call
            display.loc[0, 'Current'] = curr_call
            display.loc[0, 'PNL'] = round(ltp_call - curr_call, 2)
            display.loc[1, 'Instrument'] = f"{put_strike} PE"
            display.loc[1, 'Entry'] = ltp_put
            display.loc[1, 'Current'] = curr_put
            display.loc[1, 'PNL'] = round(ltp_put - curr_put, 2)
            st.table(display)
            
        with placeholder2.container():
            st.text(" ")
            col1, col2, col3= st.columns(3)
            col1.metric("Realised PNL", f"{pnl}")
            col2.metric("Unrealised PNL", f"{curr_pnl}")
            col3.metric("Total PNL", f"{total_pnl}")

        with placeholder3.container():
            st.text(" ")
            st.line_chart(csv_log['PNL'], color=["#FFEF00"])

        today = datetime.datetime.now().date().strftime("%d_%m_%Y")
        csv_log.to_csv(f'Trade_Logs_{today}.csv', index=False)
        i += 1
        time.sleep(2.5)
    time.sleep(60)
