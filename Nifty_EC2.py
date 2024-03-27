from neo_api_client import NeoAPI
from datetime import datetime
import pandas as pd
import datetime
import calendar
import time
import sys
import json

# CREDENTIALS
#consumer_key = 'key'
#consumer_secret = 'key'
#mobile_number = 'key'
#password = 'key'

def on_message(message):
    print(message)    
def on_error(error_message):
    print(error_message)
client = NeoAPI(consumer_key = consumer_key, consumer_secret = consumer_secret, 
                environment='prod', on_message=on_message, on_error=on_error, on_close=None, on_open=None)
client.login(mobilenumber = mobile_number, password = password)

otp = input("Enter OTP: ")
client.session_2fa(str(otp))
reuse_session = client.reuse_session
with open("creds.json","w") as file:
    file.write(json.dumps(reuse_session))

#nfo_url = client.scrip_master(exchange_segment = "NFO")
today = date.today()
nfo_url = f"https://lapi.kotaksecurities.com/wso2-scripmaster/v1/prod/{today}/transformed/nse_fo.csv"
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
    print(message)
    with open(filename, "a") as f:
        f.write(message + "\n")

# EXPIRY
exp_year = 2024
exp_month = int(input("Expiry Month: "))
exp_day = int(input("Expiry Day: "))
expiry = get_expiry(exp_year, exp_month, exp_day)
offset = datetime.timedelta(hours=5, minutes=30)

temp = get_ltp_index()
if (temp != -1):
    spot = temp
elif (temp == -1):
    while (temp == -1):
        log_text(f"Error initializing Index!")
        with open("creds.json","r") as file:
            reuse_session = json.load(file)
        client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session)
        temp = get_ltp_index()
        spot = temp
print("Spot price =", spot)

atm_strike = round_off(spot)
print("ATM strike =", atm_strike)

straddle = 0
for option in ["CE", "PE"]:
    temp = get_ltp(atm_strike, option, expiry)
    if (temp != -1):
        tk = temp
    elif (temp == -1):
        while (temp == -1):
            log_text(f"Error initializing ATM strike!")
            with open("creds.json","r") as file:
                reuse_session = json.load(file)
            client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session)
            temp = get_ltp(atm_strike, option, expiry)
            tk = temp
    straddle += tk
print("Straddle price =", straddle)

put_strike = round_off(spot - straddle)
call_strike = round_off(spot + straddle)

temp = get_ltp(put_strike, "PE" , expiry)
if (temp != -1):
    ltp_put = temp
elif (temp == -1):
    while (temp == -1):
        log_text(f"Error initializing Put!")
        with open("creds.json","r") as file:
            reuse_session = json.load(file)
        client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session)
        temp = get_ltp(put_strike, "PE" , expiry)
        ltp_put = temp
print(put_strike,"PE =", ltp_put)

temp = get_ltp(call_strike, "CE" , expiry)
if (temp != -1):
    ltp_call = temp
elif (temp == -1):
    while (temp == -1):
        log_text(f"Error initializing Call!")
        with open("creds.json","r") as file:
            reuse_session = json.load(file)
        client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session)
        temp = get_ltp(call_strike, "CE" , expiry)
        ltp_call = temp
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

while True:
    now = datetime.datetime.now()
    tstamp = now + offset
    tstamp = tstamp.strftime("%H:%M:%S")
    print(f"{tstamp} | Market is closed")

    if ((tstamp > "09:18:00") and (tstamp < "09:20:00")) :

        temp = get_ltp_index()
        if (temp != -1):
            spot = temp
        elif (temp == -1):
            while (temp == -1):
                log_text(f"Error initializing Index!")
                with open("creds.json","r") as file:
                    reuse_session = json.load(file)
                client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session)
                temp = get_ltp_index()
                spot = temp
        print("Spot price =", spot)

        atm_strike = round_off(spot)
        print("ATM strike =", atm_strike)

        straddle = 0
        for option in ["CE", "PE"]:
            temp = get_ltp(atm_strike, option, expiry)
            if (temp != -1):
                tk = temp
            elif (temp == -1):
                while (temp == -1):
                    log_text(f"Error initializing ATM strike!")
                    with open("creds.json","r") as file:
                        reuse_session = json.load(file)
                    client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session)
                    temp = get_ltp(atm_strike, option, expiry)
                    tk = temp
            straddle += tk
        print("Straddle price =", straddle)

        put_strike = round_off(spot - straddle)
        call_strike = round_off(spot + straddle)

        temp = get_ltp(put_strike, "PE" , expiry)
        if (temp != -1):
            ltp_put = temp
        elif (temp == -1):
            while (temp == -1):
                log_text(f"Error initializing Put!")
                with open("creds.json","r") as file:
                    reuse_session = json.load(file)
                client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session)
                temp = get_ltp(put_strike, "PE" , expiry)
                ltp_put = temp
        print(put_strike,"PE =", ltp_put)

        temp = get_ltp(call_strike, "CE" , expiry)
        if (temp != -1):
            ltp_call = temp
        elif (temp == -1):
            while (temp == -1):
                log_text(f"Error initializing Call!")
                with open("creds.json","r") as file:
                    reuse_session = json.load(file)
                client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session)
                temp = get_ltp(call_strike, "CE" , expiry)
                ltp_call = temp
        print(call_strike,"CE =", ltp_call)

        sold_premium = ltp_put + ltp_call
        sold_premium = round(sold_premium, 2)
        print("Sold premium =", sold_premium)

        i = 0
        pnl = 0
        curr_pnl = 0
        total_pnl = 0
        count = 0
        max_loss = 0
        max_profit = 0


    while ((tstamp > "09:20:00") and (tstamp < "15:22:00")):
        now = datetime.datetime.now()
        tstamp = now + offset
        tstamp = tstamp.strftime("%H:%M:%S")

        if (tstamp > "15:20:00") :

            temp = get_ltp(call_strike, "CE" , expiry)
            if (temp != -1):
                pnl += ltp_call - temp
            elif (temp == -1):
                log_text(f"{tstamp} | Error fetching Quote!")
                with open("creds.json","r") as file:
                    reuse_session = json.load(file)
                client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session )

            temp = get_ltp(put_strike, "PE" , expiry)
            if (temp != -1):
                pnl += ltp_put - temp
            elif (temp == -1):
                log_text(f"{tstamp} | Error fetching Quote!")
                with open("creds.json","r") as file:
                    reuse_session = json.load(file)
                client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session )
  
            pnl = round(pnl, 2)
            if (total_pnl > max_profit):
                max_profit = total_pnl
            elif (total_pnl < max_loss):
                max_loss = total_pnl

            log_text(f"DAY ENDED! PNL = {total_pnl} | Max Loss = {max_loss} | Total Adjustments = {count} | Max Profit = {max_profit}")
            today = datetime.datetime.now().date().strftime("%d_%m_%Y")
            csv_log.to_csv(f'Trade_Logs_{today}.csv', index=False)
            sys.exit(101)

        change1 = 1
        change2 = 1

        temp = get_ltp_index()
        if (temp != -1):
            spot = temp
        elif (temp == -1):
            log_text(f"{tstamp} | Error fetching Quote!")
            with open("creds.json","r") as file:
                reuse_session = json.load(file)
            client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session )

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
            print ("--- Changing Call Strike ---")

            temp = get_ltp(call_strike, "CE" , expiry)
            if (temp != -1):
                exit_price = temp
            elif (temp == -1):
                log_text(f"{tstamp} | Error fetching Quote!")
                with open("creds.json","r") as file:
                    reuse_session = json.load(file)
                client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session)

            temp = get_ltp(new_call, "CE" , expiry)
            if (temp != -1):
                entry_price = temp
            elif (temp == -1):
                log_text(f"{tstamp} | Error fetching Quote!")
                with open("creds.json","r") as file:
                    reuse_session = json.load(file)
                client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session )

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
            print ("--- Changing PUT Strike ---")

            temp = get_ltp(put_strike, "PE" , expiry)
            if (temp != -1):
                exit_price = temp
            elif (temp == -1):
                log_text(f"{tstamp} | Error fetching Quote!")
                with open("creds.json","r") as file:
                    reuse_session = json.load(file)
                client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session )

            temp = get_ltp(new_put, "PE" , expiry)
            if (temp != -1):
                entry_price = temp
            elif (temp == -1):
                log_text(f"{tstamp} | Error fetching Quote!")
                with open("creds.json","r") as file:
                    reuse_session = json.load(file)
                client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session )

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
            log_text(f"{tstamp} | Error fetching Quote!")
            with open("creds.json","r") as file:
                reuse_session = json.load(file)
            client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session) 

        temp = get_ltp(call_strike, "CE" , expiry)
        if (temp != -1):
            curr_call = temp 
        elif (temp == -1):
            log_text(f"{tstamp} | Error fetching Quote!")
            with open("creds.json","r") as file:
                reuse_session = json.load(file)
            client = NeoAPI(access_token="test",environment="prod", reuse_session=reuse_session ) 

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

        today = datetime.datetime.now().date().strftime("%d_%m_%Y")
        csv_log.to_csv(f'Trade_Logs_{today}.csv', index=False)
        i += 1
        time.sleep(2.5)
    time.sleep(60)
