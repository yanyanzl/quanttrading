"""
Copyright (C) Steven Jiang. All rights reserved. This code is subject to the terms
 and conditions of the MIT Non-Commercial License, as applicable.
"""

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.reader import EReader

from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum
from ibapi.execution  import Execution
from datetime import datetime
import pandas

from ibapi.common import * # @UnusedWildImport
from ibapi.utils import * # @UnusedWildImport
from .aiorder import *
from setting import Aiconfig
import logging
from .aitools import *

logger = logging.getLogger(__name__)

# BUY_LMT_PLUS = 0.05

# ACCOUNT_COLUMNS=['key', 'value', 'currency']

# PORTFOLIO_COLUMNS = ['symbol', 'sectype', 'exchange', 'position', 'marketprice', 'marketvalue', 'averagecost', 'unrealizedpnl', 'realizedpnl']

# ACCOUNT_INFO_SHOW_LIST = ['UnrealizedPnL','RealizedPnL', "NetLiquidation","TotalCashValue", "BuyingPower","GrossPositionValue", "AvailableFunds"]

class AiWrapper(EWrapper):
    """
    implement IBKR EWapper class. which is the interface that will need to be overloaded by the customer so
    that his/her code can receive info from the TWS/IBGW. 
    The user just needs to override EWrapper methods to receive the answers.
    """
    # The API treats many items as errors even though they are not.
    def error(self, reqId, errorCode, errorMsg="", advancedOrderRejectJson=""):
        super().error(reqId, errorCode, errorMsg, advancedOrderRejectJson)
        display_message(f'error message : {errorMsg}')
        if errorCode == 202:
            display_message(f'order canceled - Reason , {errorMsg}') 
        # else:
        #     print(f'errorcode {errorCode}, error message: {errorMsg}')

    # This function is fired when an order is filled or reqExcutions() called.
    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
         super().execDetails(reqId,contract, execution)

         print('Order Executed: ', reqId, contract.symbol, contract.secType, contract.currency, execution.execId, execution.orderId, execution.shares, execution.lastLiquidity)    

    def marketDataType(self, reqId: TickerId, marketDataType: int):
        super().marketDataType(reqId, marketDataType)

        print("MarketDataType. ReqId:", reqId, "Type:", marketDataType)

    def openOrderEnd(self):
            super().openOrderEnd()
            print("OpenOrderEnd")
            # logging.debug("Received %d openOrders", len(self.permId2ord))     

class AiClient(EClient):
    """
    The main class to use from API user's point of view.
    It takes care of almost everything:
    - implementing the requests
    - creating the answer decoder
    - creating the connection to TWS/IBGW
    """
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)


class IbkrApp(AiWrapper, AiClient):
    """
    Reimplement both Client and Wrapper so that
    we could creating the connection, 
    send request, receive the answers, decoding the answers,
    """
    # message queue is used to process real time messages generated
    # by the programm. it could help the user to monitor the progress
    message_q = queue.Queue()
    # data queue is used to transfer data
    data_q = queue.Queue()
    def __init__(self):
        AiWrapper.__init__(self)
        AiClient.__init__(self, wrapper=self)
        self.data = [] #Initialize variable to store data
        self.account = "" 
        #  account_info;` columns: key, value, currency`
        self.account_info = pandas.DataFrame()
        # self.mkt_price = ""
        self.last_price = ""
        self.bid_price = ""
        self.ask_price = ""
        self.portfolio = pandas.DataFrame()
        # this is used for the cancel of the last order.
        self.lastOrderId = 0
        self.currentContract = Contract()
        self.previous_contract = Contract()
        self.tick_bidask_reqId = -1
        self.realtime_bar_reqId = -1
        self.market_reqId = -1
    
    @staticmethod
    def has_message_queue():
         if IbkrApp.message_q and isinstance(IbkrApp.message_q, queue.Queue):
              return True
         return False
    
    @staticmethod
    def has_data_queue():
         if IbkrApp.data_q and isinstance(IbkrApp.data_q, queue.Queue):
              return True
         return False

    def _processMessage(self, message:str) -> None:
        """
        internal method which used to process Message
        """
        if message is not None:
            logger.info(message)
            if IbkrApp.has_message_queue():
                IbkrApp.message_q.put(message)

    def reqTickByTickData(self, reqId:int, contract:Contract,tickType:str,numberOfTicks:int,ignoreSize:bool):
         super().reqTickByTickData(reqId, contract, tickType, numberOfTicks, ignoreSize)
         self.tick_bidask_reqId = reqId
    
    def cancelTickByTickData(self, reqId:int):
        super().cancelTickByTickData(reqId)
        self.tick_bidask_reqId = -1
        message = f'cancelTickByTickData... ReqId:, {reqId}'
        self._processMessage(message)

    def reqRealTimeBars(self,reqId:TickerId, contract:Contract, barSize:int,whatToShow:str,useRTH:bool,realTimeBarsOptions:TagValueList):
        super().reqRealTimeBars(reqId,contract,barSize,whatToShow,useRTH,realTimeBarsOptions)
        self.realtime_bar_reqId = reqId
    
    def cancelRealTimeBars(self,reqId:TickerId):
        super().cancelRealTimeBars(reqId)
        self.realtime_bar_reqId = -1
        message = f'cancelRealTimeBars... ReqId:, {reqId}'
        self._processMessage(message)

    def reqMktData(self, reqId:TickerId,contract:Contract, genericTickList:str, snapshot:bool,regulatorySnapshot:bool, mktDataOptions:TagValueList):
        super().reqMktData(reqId, contract, genericTickList,snapshot, regulatorySnapshot,mktDataOptions)
        self.market_reqId = reqId
    
    def cancelMktData(self,reqId:TickerId):
        super().cancelMktData(reqId)
        self. market_reqId = -1
        message = f'cancelMktData... ReqId:, {reqId}'
        self._processMessage(message)

    # overide the account Summary method. to get all the account summary information
    def accountSummary(self, reqId: int, account: str, tag: str, value: str,currency: str):
        # print("AccountSummary. ReqId:", reqId, "Account:", account,"Tag: ", tag, "Value:", value, "Currency:", currency)
        super().accountSummary(reqId,account, tag, value, currency)

        self.account = account
        if tag != None and tag != "":
             self.account_info = pandas.concat([self.account_info,pandas.DataFrame([[tag, value, currency]],
                   columns=Aiconfig.get('ACCOUNT_COLUMNS'))])
 

    # overide the account Summary end method. 
    # Notifies when all the accounts’ information has ben received.
    def accountSummaryEnd(self, reqId: int):
        message = f'AccountSummaryEnd. ReqId:, {reqId}'
        self._processMessage(message)

    # Receiving Account Updates
    # Resulting account and portfolio information will be delivered via the IBApi.EWrapper.updateAccountValue, IBApi.EWrapper.updatePortfolio, IBApi.EWrapper.updateAccountTime and IBApi.EWrapper.accountDownloadEnd
        
    # Receives the subscribed account’s information. Only one account can be subscribed at a time. After the initial callback to updateAccountValue, callbacks only occur for values which have changed. This occurs at the time of a position change, or every 3 minutes at most. This frequency cannot be adjusted.
    def updateAccountValue(self, key: str, val: str, currency: str,accountName: str):
        # print("UpdateAccountValue. Key:", key, "Value:", val, "Currency:", currency, "AccountName:", accountName)
        if key != None and key != "":
            # print(f"key is {key}. {val}")

            # if exist in the data list already. drop it firstly.
            if not self.account_info.loc[self.account_info['key'] == key].empty:
                # print("not empty. drop .... --- ")
                self.account_info = self.account_info.drop(index=self.account_info.loc[self.account_info['key'] == key].index)
                                                           
            self.account_info = pandas.concat([self.account_info,pandas.DataFrame([[key, val, currency]],
                   columns=Aiconfig.get('ACCOUNT_COLUMNS'))], ignore_index=True)


    # Receives the subscribed account’s portfolio. This function will receive only the portfolio of the subscribed account. After the initial callback to updatePortfolio, callbacks only occur for positions which have changed.

    def updatePortfolio(self, contract: Contract, position: Decimal, marketPrice: float, marketValue: float, averageCost: float, unrealizedPNL: float, realizedPNL: float, accountName: str):
         # print("UpdatePortfolio.", "Symbol:", contract.symbol, "SecType:", contract.secType, "Exchange:",contract.exchange, "Position:", position, "MarketPrice:", marketPrice,"MarketValue:", marketValue, "AverageCost:", averageCost, "UnrealizedPNL:", unrealizedPNL, "RealizedPNL:", realizedPNL, "AccountName:", accountName)
        #   to save those portfolio positions information to a dataset.
        for _ in self.portfolio.index:
            # psoppcprint(f"portforlio {_}, symbol is {self.portfolio.iloc[_]['symbol']}")
            # if the symbol already in the portfolio. drop it.
            if contract.symbol == self.portfolio.iloc[_]['symbol']:
                #  print(f"droping {self.portfolio.iloc[_]}")
                 self.portfolio = self.portfolio.drop(index=_)
                 break

        self.portfolio = pandas.concat([self.portfolio, pandas.DataFrame([[contract.symbol,contract.secType, contract.exchange,position,marketPrice,marketValue,averageCost, unrealizedPNL,realizedPNL]],
                   columns=Aiconfig.get('PORTFOLIO_COLUMNS') )], ignore_index=True)

    # Receives the last time on which the account was updated.
    def updateAccountTime(self, timeStamp: str):
        message = f'UpdateAccountTime. Time:, {timeStamp}'
        self._processMessage(message)

    # Notifies when all the account’s information has finished.
    def accountDownloadEnd(self, accountName: str):
        message = f'AccountDownloadEnd. Account:, {accountName}'
        self._processMessage(message)

    # after reqMktData, this function is used to receive the data.
    def tickPrice(self, reqId, tickType, price, attrib):
            super().tickPrice(reqId,tickType,price,attrib)
            # for i in range(91):
            #     print(TickTypeEnum.to_str(i), i)
            tickType = TickTypeEnum.toStr(tickType)
            message = f"reqID is , {reqId}, tickType is : {tickType}, price is: {price}, attrib is: {attrib}"
            if price > 0:
                if tickType == "LAST":
                    self.last_price = price
                elif tickType == "BID":
                    self.bid_price = price
                elif tickType == "ASK":
                    self.ask_price = price
            self._processMessage(message)

    # after reqHistoricalData, this function is used to receive the data.
    def historicalData(self, reqId, bar):
            # print(f'Time: {bar.date} Close: {bar.close}')
            self.data.append([bar.date, bar.close])

    # To fire an order, we simply create a contract object with the asset details and an order object with the order details. Then call app.placeOrder to submit the order.
    # The IB API requires an order id associated with all orders and it needs to be a unique positive integer. It also needs to be larger than the last order id used. Fortunately, there is a built in function which will tell you the next available order id.
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextorderId = orderId
        message = f'The next valid order id is:  {self.nextorderId}'
        self._processMessage(message)

    # order status, will be called after place/cancel order
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)
        message = f'orderStatus - orderid: {orderId}, status: {status}, filled: {filled}, remaining: {remaining}, lastFillPrice: {lastFillPrice}, avgFullPrice: {avgFillPrice}, mktCapPrice: {mktCapPrice}'
        self._processMessage(message)

    # will be called after place order
    def openOrder(self, orderId, contract, order, orderState):
        super().openOrder(orderId, contract, order, orderState)
        message = f'openOrder id: {orderId}, {contract.symbol}, {contract.secType}, @  {contract.exchange} , {order.action}, {order.orderType}, {order.totalQuantity}, at price , {order.lmtPrice}, {orderState.status}'
        self.lastOrderId = orderId
        self._processMessage(message)

    # tickByTickBidAsk function to receive the data.
    def tickByTickBidAsk(self, reqId: int, time: int, bidPrice: float, askPrice: float, bidSize: Decimal, askSize: Decimal, tickAttribBidAsk: TickAttribBidAsk):
        super().tickByTickBidAsk(reqId, time, bidPrice, askPrice, bidSize, askSize, tickAttribBidAsk)
        
        message = f'BidAsk. ReqId: {reqId}, Time: {datetime.fromtimestamp(time).strftime("%Y%m%d-%H:%M:%S")}, BidPrice: {floatMaxString(bidPrice)}, AskPrice: {floatMaxString(askPrice)}, BidSize: {decimalMaxString(bidSize)}, AskSize: {decimalMaxString(askSize)}, BidPastLow: {tickAttribBidAsk.bidPastLow}, AskPastHigh: {tickAttribBidAsk.askPastHigh}'
        self.ask_price = askPrice
        self.bid_price = bidPrice
        
        self._processMessage(message)

    def realtimeBar(self,reqId:TickerId,time:int,open_:float,high:float,low:float,close:float,volume:Decimal,wap:Decimal, count:int):
        super().realtimeBar(reqId, time, open_,high,low, close, volume, wap,count)
        message = f'Realtime Bar... ReqId:, {reqId}, time: {time}, open: {open_}, high: {high}, low: {low}, close: {close}, volume:{volume}, wap: {wap}, count: {count}'
        self._processMessage(message)

    def close_contract_data(self, contract:Contract=None):
        message = ""
        if self.isConnected():

            if not contract:
                   contract = self.currentContract
            
            message = f"closing all data for contract.symbol: {contract.symbol}"

            if self.tick_bidask_reqId > 0:
                 self.cancelTickByTickData(self.tick_bidask_reqId)
            if self.realtime_bar_reqId > 0:
                 self.cancelRealTimeBars(self.realtime_bar_reqId)
            if self.market_reqId > 0:
                 self.cancelMktData(self.market_reqId)
        else:
            message = "not connected to server yet ..."
            logging.warning(message)

        self._processMessage(message)            

    
    def close_previous_contract(self):
        if self.previous_contract and self.currentContract and self.currentContract.symbol != self.previous_contract.symbol:
            self.close_contract_data(self.previous_contract)

    def set_current_Contract(self, contract: Contract):
        """ change the current contract. all functions use contract will be affected.
        """
        message = ""
        if contract and isinstance(contract,Contract):
            message = "current contract.symbol changed to" + contract.symbol
            self.currentContract = contract
            
            self.close_previous_contract()

            if self.isConnected():
                #Request Market Data. should be in market open time.
                self.reqMarketDataType(1) # -1 is real time stream. 3 is delayed data.
                self.reqMktData(1, self.currentContract, '', True, False, [])
        else:
            message = "invalid parameter: contract" + str(type(contract.__name__))
        
        self._processMessage(message)

    def disconnect(self):
        self.close_contract_data()
        super().disconnect()


def place_lmt_order(app=IbkrApp(), action:str="", tif:str="DAY", increamental=Aiconfig.get('BUY_LMT_PLUS'), quantity=10, priceTickType="LAST"):
    """
    send limit order to server
    """
    ############ placing order started here
    # print(f'ask price {app.ask_price}, bid price {app.bid_price}, last price {app.last_price}')
    message = ""
    price = 0
    if action != 'BUY' and action != 'SELL':
             message = f"invalid  action {action} in place_lmt_order!"
             if IbkrApp.has_message_queue():
                  IbkrApp.message_q.put(message)
             raise ValueError(message)
    try:
        message = f'ask price {app.ask_price}, bid price {app.bid_price}, last price {app.last_price}'
        print(message)
        if IbkrApp.has_message_queue():
            IbkrApp.message_q.put(message) 
        # print("before get order price")
        price = float(_get_order_price_by_type(app, priceTickType))
        # print("after get order price")
        if len(app.currentContract.symbol) > 0:
            # print("before building order")
            order = lmt_order(price + float(increamental), action, quantity,tif)
            # print("after building order")
            #Place order
            message = f'placing limit order now ...\n orderid {app.nextorderId}, action: {action}, symbol {app.currentContract.symbol}, quantity: {quantity}, tif: {tif} at price: {order.lmtPrice}'
            print(message)
            if IbkrApp.has_message_queue():
               IbkrApp.message_q.put(message) 
            
            # print("id:" , app.nextorderId, "contract", app.currentContract, "order is ", order)
            app.placeOrder(app.nextorderId, app.currentContract, order)
            # print("after place oder...")
            # orderId used, now get a new one for next time
            app.reqIds(app.nextorderId)
            # print("after reqIds")

        else:
            message = f'place order failed.:  symbol is {app.currentContract.symbol}, action is {action}'
            print(message)
            if IbkrApp.has_message_queue():
                IbkrApp.message_q.put(message) 

    except Exception as ex:
        message = f"place order failed.: for price {price}, priceTickType: {priceTickType}, symbol is {app.currentContract.symbol}, action is {action}"
        print(message, ex.args)
        if IbkrApp.has_message_queue():
            IbkrApp.message_q.put(message) 

def _get_order_price_by_type(app=IbkrApp(),priceTickType="LAST"): 
     """
     get the price for the order based on the priceTickType. inner function
     """
    #  print(f"prictTickType is {priceTickType}, app.lastprice is {app.last_price}")
     if priceTickType == "LAST" and app.last_price and float(app.last_price) > 0:
        # print(f"prictTickType is {priceTickType}, app.lastprice is {app.last_price}")
        return app.last_price
     elif priceTickType == "ASK" and app.ask_price and float(app.ask_price) > 0:
        #   print(f"prictTickType is {priceTickType}, app.ask is {app.ask_price}")
          return app.ask_price
     elif priceTickType == "BID" and app.bid_price and float(app.bid_price) > 0:
        #   print(f"prictTickType is {priceTickType}, app.bid is {app.bid_price}")
          return app.bid_price
     else:
          raise ValueError(f"unexpected priceTickType {priceTickType} or no correspondont price availalbe.")

# cancel last order
def cancel_last_order(app=IbkrApp()):
    message = ""
    if app.lastOrderId > 0:
        message = f'placing orderId {app.lastOrderId} to server now ...'
        print(message)
        app.cancelOrder(app.lastOrderId,"")
    else:
        message = 'no order to be cancelled...'
        print(message)

    if IbkrApp.has_message_queue():
        IbkrApp.message_q.put(message)

# cancel all open orders
# IBApi::EClient::reqGlobalCancel will cancel all open orders, regardless of how they were originally placed.
def cancel_all_order(app=IbkrApp()):
    message = ""
    if app.isConnected():
          message = 'Cancelling all open orders to server now ...'
          print(message)
          app.reqGlobalCancel()
    else:
          message = 'calling all open orders failed. No connection ...'
          print(message)
    if IbkrApp.has_message_queue():
        IbkrApp.message_q.put(message)

# show the current portforlio 
def show_portforlio(app=IbkrApp()):
    message = ""
    if app.isConnected():
        message = f'current portforlio for account {app.account} are showing below ... \n {app.portfolio}'
        print(message)        
    else:
        message = 'show portforlio failed. No connection ...'
        print(message)
    if IbkrApp.has_message_queue():
        IbkrApp.message_q.put(message)

# show the current account summary 
def show_summary(app=IbkrApp()):
    message = ""
    if app.isConnected():
        message = f'current portforlio for account{app.account} are showing below ... \n'
        message = message + "Account info in the Show List are : \n", app.account_info.loc[app.account_info['key'].isin(Aiconfig.get('ACCOUNT_INFO_SHOW_LIST'))]
        print(message)
    else:
        message = 'show account summary failed. No connection ...'
        print(message)
    if IbkrApp.has_message_queue():
        IbkrApp.message_q.put(message)



def main():
     app = IbkrApp()

if __name__ == "__main__":
    main()