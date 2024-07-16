# this is a learning file for IB TWS connection


from ibapi.account_summary_tags import AccountSummaryTags
from ibapi.contract import Contract
# from ibapi.ticktype import TickTypeEnum
# from ibapi.execution  import Execution

from ibapi.common import * # @UnusedWildImport
from ibapi.utils import * # @UnusedWildImport
from ibapi.order import *
from pynput import keyboard
from pynput.keyboard import KeyCode

import pandas
import threading
import time

from aiapp import *
from aiorder import *
from aicontract import *
import queue

DEBUG = Aiconfig.get('DEBUG')

# get the histroy data for a contract
def get_his_data(app=AiApp(),contract=Contract()):
    #Request historical candles
    app.reqHistoricalData(1, contract, '', '5 D', '1 hour', 'BID', 0, 2, False, [])

    #Sleep interval to allow time for incoming price data. 
    # without this sleep. the data will be empty
    time.sleep(2) 
    # transform data to Dataframe format. 
    df = pandas.DataFrame(app.data, columns=['DateTime', 'Close'])
    df['DateTime'] = pandas.to_datetime(df['DateTime'],unit="s")

    # 20 SMA of the close price.
    df['20SMA'] = df['Close'].rolling(20).mean()
    # print(df.tail(10))


def change_current_Contract(app=AiApp()):
    """ change the current contract object for the current AiApp instance.
    """
    try:
        if app.isConnected():

            while True:
                contractType = input("Input F (for FX) or S (for Stock):")
                if any([contractType.lower() in ['f','s']]):
                    break
                else:
                    print("invalid input...")

            while True:
                if contractType.lower() == 'f':
                    symbol = input("Input FX name (six letter, like EURUSD):")
                    if symbol and len(symbol) == 6:
                        app.set_current_Contract(fx_contract(symbol))
                        break
                        
                else:
                    symbol = input("Input stock tick name (like TSLA or AAPL):")
                    if symbol and len(symbol) > 0:
                        app.set_current_Contract(stock_contract(symbol))
                        break
                print("invalid input...")

    except Exception as ex:
        print("failed to change current contract. invalid input.")

def show_current_Contract(app=AiApp()):
    """ show the current contract in the current AiApp instance. 
    """
    message = ""
    if app.isConnected() and app.currentContract:
        message = f"current contract is :{app.currentContract}"

    else:
        message = f"show current contract failed.connected: {app.isConnected()}. current contract {app.currentContract}"

    print(message)
    if AiApp.has_message_queue():
        AiApp.message_q.put(message)

from aigui import *


def main():

    message_q = queue.Queue()

    def worker():
        while True:
            if not message_q.empty():
                item = message_q.get()
                # print(f'Working on {item}')
                if item:
                    if mainframe:
                        display_message(str(item),mainframe.message_area)
                    if str(item) == Aiconfig.get("SYMBOL_CHANGED"):
                        if app and mainframe:
                            app.set_current_Contract(stock_contract(mainframe.symbol_selected))
                # print(f'Finished {item}')
                message_q.task_done()

    # Turn-on the worker thread.
    que_thread = StoppableThread(target=worker, daemon=True)
    que_thread.start()

    def exit_app():
        # Once the subscription to account updates is no longer needed, it can be cancelled by invoking the IBApi.EClient.reqAccountUpdates method while specifying the susbcription flag to be False.
        app.reqAccountUpdates(False, app.account)
        time.sleep(1) 
        print("Exiting Program...")
        app.disconnect()
        api_thread.stop()
        que_thread.stop()
        # listener.stop()
        root.destroy()

    def tick_data():
        for key in Aiconfig.get('TICK_BIDASK'):
            on_press(key)
    def bar_data():
        for key in Aiconfig.get('REQUIRE_REALTIME_BAR'):
            on_press(key)
    # function to be called when keyboard buttons are pressed
    def key_press(event):
        
        # key = event.char
        keysymbol = str(event.keysym).lower()
        
        if len(keysymbol) > 1:
            keysymbol = "key."+keysymbol.strip('_l').strip('_r')
        # print(key, 'is pressed')
        print(keysymbol, 'is pressed')
        # display_message(str(event), mainframe.message_area)
        display_message(keysymbol, mainframe.message_area)
        on_press(keysymbol)

    def key_release(event):
        # key = event.char
        keysymbol = str(event.keysym).lower()
        
        if len(keysymbol) > 1:
            keysymbol = "key."+keysymbol.strip('_l').strip('_r')
        # print(key, 'is pressed')
        print(keysymbol, 'is released')
        # display_message(str(event), mainframe.message_area)
        # display_message(keysymbol, mainframe.message_area)
        on_release(keysymbol)

####### create GUI part  --------------------- start
    root = tk.Tk()
    # root.geometry('800x800')
    root.wm_title('AI Investment')

    mainframe = AIGUIFrame(root)
    mainframe.order_button.configure(command=exit_app)
    mainframe.redbutton.configure(command=tick_data)
    mainframe.bar_data_button.configure(command=bar_data)


    # create menu of the application
    menu = AiGUIMenu(root)
    menu.filemenu.add_command(label='Exit', command=exit_app)

    # Tkinter supports a mechanism called protocol handlers. Here, the term protocol refers to the interaction between the application and the window manager. The most commonly used protocol is called WM_DELETE_WINDOW, and is used to define what happens when the user explicitly closes a window using the window manager.
    root.protocol("WM_DELETE_WINDOW", exit_app)
    # add righ click menu to the app. those menu could bind different command.
    right_click_menu = RightClickMenu(root)
    # For most mice, this will be '1' for left button, '2' for middle, '3' for right.
    root.bind("<Button-2>", right_click_menu.do_popup) 

    root.bind('<Key>', key_press)
    root.bind('<KeyRelease>', key_release)


####### create GUI part  --------------------- end

    app = AiApp()
    print("program is starting ...")
    app.connect('127.0.0.1', 7497, 36)
    # app.connect('192.168.1.146', 7497, 1)
    
    print(app.isConnected())

    app.nextorderId = None
    
    #Start the socket in a thread
    api_thread = StoppableThread(target=app.run, daemon=True)
    api_thread.start()
    

    #Check if the API is connected via orderid
    while True:
        if isinstance(app.nextorderId, int):
            print('connected')
            break
        else:
            print('waiting for connection')
            time.sleep(1)

    time.sleep(1) #Sleep interval to allow time for connection to server

    # requre all the 
    app.reqAccountSummary(9001, "All", AccountSummaryTags.AllTags)

    #Sleep interval to allow time for response data from server
    time.sleep(2) 

    # The IBApi.EClient.reqAccountUpdates function creates a subscription to the TWS through which account and portfolio information is delivered. This information is the exact same as the one displayed within the TWS’ Account Window. Just as with the TWS’ Account Window, unless there is a position change this information is updated at a fixed interval of three minutes.
    app.reqAccountUpdates(True, app.account)

    app.set_current_Contract(stock_contract("AAPL"))

    # time.sleep(2)


    ################ keyboard input monitoring part start
    # monitoring the keyboard and make it available to control the order
    combo_key = set()

    def on_press(key):
        try:
            message = ""
            # print('alphanumeric key pressed', key.char.lower())
            # change object key to lower string case without quotation mark.
            key = str(key).lower().strip("'")

            print(f"key is --- : {key}")
            # print(Aiconfig.get('PLACE_BUY_ORDER'))

            # place limit buy order Tif = day
            if key == Aiconfig.get('PLACE_BUY_ORDER'):
                place_lmt_order(app, "BUY", increamental=Aiconfig.get("BUY_LMT_PLUS"))

            # place limit buy order Tif = day
            elif key == Aiconfig.get('PLACE_SELL_ORDER'):
                place_lmt_order(app, "SELL", increamental=Aiconfig.get("SELL_LMT_PLUS"))

             
            # # cancel last order
            # elif any([key in COMBO for COMBO in Aiconfig.get('CANCEL_LAST_ORDER')]): # Checks if pressed key is in any combinations
            #     combo_key.add(key)
            #     if any(all (k in combo_key for k in COMBO) for COMBO in Aiconfig.get('CANCEL_LAST_ORDER')): # Checks if every key of the combination has been pressed
            #         cancel_last_order(app)
            #         combo_key.clear()
            
            # cancel last order
            elif any([key in Aiconfig.get('CANCEL_LAST_ORDER')]): # Checks if pressed key is in any combinations
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('CANCEL_LAST_ORDER')): # Checks if every key of the combination has been pressed
                    cancel_last_order(app)
                    combo_key.clear()

            elif key == Aiconfig.get('CHANGE_CONTRACT'):
                message = "change current contract..."
                print(message)
                change_current_Contract(app)
            
            elif key == Aiconfig.get('SHOW_CURRENT_CONTRACT'):
                show_current_Contract(app)

            # cancel all orders
            elif any([key in Aiconfig.get('CANCEL_ALL_ORDER')]): # Checks if pressed key is in any combinations
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('CANCEL_ALL_ORDER')): # Checks if every key of the combination has been pressed
                    cancel_all_order(app)
                    combo_key.clear()

            elif key == Aiconfig.get('PLACE_IOC_BUY'):
                 place_lmt_order(app, "BUY", tif="IOC", increamental=Aiconfig.get('BUY_LMT_PLUS'), priceTickType="ASK")
            
            elif key ==  Aiconfig.get('PLACE_IOC_SELL'):
                 place_lmt_order(app, "SELL", tif="IOC", increamental=Aiconfig.get('SELL_LMT_PLUS'), priceTickType="BID")
            
            ########### to be completed
            elif key ==  Aiconfig.get('PLACE_STOP_SELL'):
                 pass
            
            elif key ==  Aiconfig.get('PLACE_STOP_BUY'):
                 pass
            
            elif key ==  Aiconfig.get('PLACE_BRACKET_BUY'):
                 pass
            
            elif key ==  Aiconfig.get('PLACE_BRACKET_SELL'):
                 pass
            
            elif any([key in Aiconfig.get('REQ_OPEN_ORDER')]): #  Requests all current open orders in associated accounts at the current moment. The existing orders will be received via the openOrder and orderStatus events. Open orders are returned once; this function does not initiate a subscription.
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('REQ_OPEN_ORDER')): # Checks if every key of the combination has been pressed
                    message = "requesting all Open orders from server now ..."
                    print(message)
                    app.reqAllOpenOrders()
                    combo_key.clear()

            elif any([key in Aiconfig.get('TICK_BIDASK')]): 
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('TICK_BIDASK')): # Checks if every key of the combination has been pressed
                    message = f"requesting tick by tick bidask data from server for {app.currentContract} now ..."
                    print()
                    app.reqTickByTickData(19003, app.currentContract, "BidAsk", 0, True)
                    combo_key.clear()

            elif any([key in Aiconfig.get('CANCEL_TICK_BIDASK')]): 
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('CANCEL_TICK_BIDASK')): # Checks if every key of the combination has been pressed
                    message = "cancelling tick by tick bidask data from server now ..."
                    print(message)
                    app.cancelTickByTickData(19003)
                    combo_key.clear()

            elif any([key in Aiconfig.get('SHOW_PORT')]): 
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('SHOW_PORT')): # Checks if every key of the combination has been pressed
                    show_portforlio(app)
                    combo_key.clear()

            elif any([key in Aiconfig.get('SHOW_SUMMARY')]): 
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('SHOW_SUMMARY')): # Checks if every key of the combination has been pressed
                    show_summary(app)
                    combo_key.clear()

            elif any([key in Aiconfig.get('REQUIRE_REALTIME_BAR')]): 
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('REQUIRE_REALTIME_BAR')): 
                    message = "requesting real time Bars data from server now ..."
                    print(message)
                    # whatToShow	the nature of the data being retrieved: TRADES, MIDPOINT, BID, ASK
                    app.reqRealTimeBars(19002,app.currentContract,1,"TRADES", 0,[])
                    combo_key.clear() 

            elif any([key in Aiconfig.get('CANCEL_REALTIME_BAR')]): 
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('CANCEL_REALTIME_BAR')): 
                    message = "cancalling real time Bars data from server now ..."
                    print(message)
                    app.cancelRealTimeBars(19002)
                    combo_key.clear()        

            else:
                 if DEBUG:
                     pass
                    #print(f"{key} is not defined for any function now ...")
            if message and AiApp.has_message_queue():
                AiApp.message_q.put(message)

        except AttributeError:
            message = 'special key {0} pressed'.format(key)
            print(message)

    def on_release(key):
        # print('{0} released'.format(key))
        # change object key to lower string case without quotation mark.
        key = str(key).lower().strip("'")
        message = ""
        if key == 'key.esc' or key == 'key.escape':
            # Stop listener
            message = "Stopping Listener..."
            print(message)
            if AiApp.has_message_queue():
                AiApp.message_q.put(message)
            exit_app()
            return False # return False to the call thread. it will terminate the thread
        
        # in case only part of the key pressed. those key should be removed from combo_key.
        elif any([key in combo_key]):
             combo_key.remove(key)
            #  print(f"removing...{key}")
        # else:
        #     print(f"you pressed...{key}")


    # in a non-blocking fashion:
    # A keyboard listener is a threading.Thread, and all callbacks will be invoked from the thread.
    # Call pynput.keyboard.Listener.stop from anywhere, raise StopException or return False from a callback to stop the listener.
    # The key parameter passed to callbacks is a pynput.keyboard.Key, for special keys, a pynput.keyboard.KeyCode for normal alphanumeric keys, or just None for unknown keys.
    # When using the non-blocking version above, the current thread will continue executing. This might be necessary when integrating with other GUI frameworks that incorporate a main-loop, but when run from a script, this will cause the program to terminate immediately.
    # listener = keyboard.Listener(
    # on_press=on_press,
    # on_release=on_release)
    # listener.start()
    ################ keyboard input monitoring part end
    AiApp.message_q = message_q
    root.mainloop()


if __name__ == "__main__":
    main()
