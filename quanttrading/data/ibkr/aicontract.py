"""
Copyright (C) Steven Jiang. All rights reserved. This code is subject to the terms
 and conditions of the MIT Non-Commercial License, as applicable.

The Contract Object
The Contract object is an object used throughout the TWS API 
to define the target of your requests. 
Contract objects will be used for market data, 
portfolios, orders, executions, and even some news request.
 This is the staple structure used for all of the TWS API.

In all contracts, the minimum viable structure requires 
at least a conId and exchange, or a symbol, secType, 
exchange, primaryExchange, and currency. Derivatives 
will require additional fields, such as 
lastTradeDateOrExpiration, tradingClass, multiplier, 
strikes, and so on.

build contract object:
    symbol: tick name for the contract. example: TSLA, AAPL
    SecType [get, set]
 	    The security's type: STK - stock (or ETF) OPT - option FUT - future IND - index FOP - futures option CASH - forex pair BAG - combo WAR - warrant BOND- bond CMDTY- commodity NEWS- news FUND- mutual fund
    ConId: int. Identifier to specify an exact contract.

    Exchange: String. Exchange for which data or trades should be routed.

    PrimaryExchange: String. Primary listing exchange of the instrument.

    Currency: String. Base currency the instrument is traded on.
"""
from ibapi.contract import * # @UnusedWildImport

#Function to create FX contract, by passing symbol of six letters like EURUSD
def fx_contract(symbol):
	contract = Contract()
	contract.symbol = symbol[:3]
	contract.secType = 'CASH'
	contract.exchange = 'IDEALPRO'
	contract.currency = symbol[3:]
	return contract


def stock_contract(symbol,pri_exchange=""):
    """
    #Function to create stock contract by passing ticker name,
    #for USD currency.
    # on US market.
    """
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    if pri_exchange:
        contract.primaryExchange = pri_exchange
    return contract


class ContractSamples:

    """ Usually, the easiest way to define a Stock/CASH contract is through 
    these four attributes. 
        contract.symbol
        contract.secType
        contract.currency
        contract.exchange
    """

    @staticmethod
    def EurGbpFx():
        #! [cashcontract]
        contract = Contract()
        contract.symbol = "EUR"
        contract.secType = "CASH"
        contract.currency = "GBP"
        contract.exchange = "IDEALPRO"
        #! [cashcontract]
        return contract


    @staticmethod
    def Index(symbol:str=""):
        #! [indcontract]
        contract = Contract()
        contract.symbol = symbol if symbol else "DAX"
        contract.secType = "IND"
        contract.currency = "EUR"
        contract.exchange = "EUREX"
        #! [indcontract]
        return contract


    @staticmethod
    def CFD(symbol:str=""):
        #! [cfdcontract]
        contract = Contract()
        contract.symbol = symbol if symbol else "IBDE30"
        contract.secType = "CFD"
        contract.currency = "EUR"
        contract.exchange = "SMART"
        #! [cfdcontract]
        return contract


    @staticmethod
    def EuropeanStock(symbol:str=""):
        contract = Contract()
        contract.symbol = symbol if symbol else "BMW"
        contract.secType = "STK"
        contract.currency = "EUR"
        contract.exchange = "SMART"
        contract.primaryExchange = "IBIS"
        return contract

    @staticmethod
    def EuropeanStock2(symbol:str=""):
        contract = Contract()
        contract.symbol = symbol if symbol else "NOKIA"
        contract.secType = "STK"
        contract.currency = "EUR"
        contract.exchange = "SMART"
        contract.primaryExchange = "HEX"
        return contract

    @staticmethod
    def OptionAtIse(symbol:str=""):
        contract = Contract()
        contract.symbol = symbol if symbol else "COF"
        contract.secType = "OPT"
        contract.currency = "USD"
        contract.exchange = "ISE"
        contract.lastTradeDateOrContractMonth = "20190315"
        contract.right = "P"
        contract.strike = 105
        contract.multiplier = "100"
        return contract


    @staticmethod
    def BondWithCusip(symbol:str=""):
            #! [bondwithcusip]
            contract = Contract()
            # enter CUSIP as symbol
            contract.symbol= symbol if symbol else "449276AA2"
            contract.secType = "BOND"
            contract.exchange = "SMART"
            contract.currency = "USD"
            #! [bondwithcusip]
            return contract


    @staticmethod
    def Bond(symbol:int=""):
            #! [bond]
            contract = Contract()
            contract.conId = symbol if symbol else 456467716
            contract.exchange = "SMART"
            #! [bond]
            return contract


    @staticmethod
    def MutualFund(symbol:str=""):
            #! [fundcontract]
            contract = Contract()
            contract.symbol = symbol if symbol else "VINIX"
            contract.secType = "FUND"
            contract.exchange = "FUNDSERV"
            contract.currency = "USD"
            #! [fundcontract]
            return contract


    @staticmethod
    def Commodity(symbol:str=""):
            #! [commoditycontract]
            contract = Contract()
            contract.symbol = symbol if symbol else "XAUUSD"
            contract.secType = "CMDTY"
            contract.exchange = "SMART"
            contract.currency = "USD"
            #! [commoditycontract]
            return contract
    

    @staticmethod
    def USStock(symbol:str=""):
        #! [stkcontract]
        contract = Contract()
        contract.symbol = symbol if symbol else "SPY"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "ARCA"
        #! [stkcontract]
        return contract


    @staticmethod
    def USStockWithPrimaryExch(symbol:str=""):
        #! [stkcontractwithprimary]
        contract = Contract()
        contract.symbol = symbol if symbol else "SPY"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        contract.primaryExchange = "ARCA"
        #! [stkcontractwithprimary]
        return contract

            
    @staticmethod
    def USStockAtSmart(symbol:str=""):
        contract = Contract()
        contract.symbol = symbol if symbol else "IBM"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        return contract

    @staticmethod
    def etf(symbol:str=""):
        contract = Contract()
        contract.symbol = symbol if symbol else "QQQ"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        return contract

    @staticmethod
    def USOptionContract(symbol:str=""):
        #! [optcontract_us]
        contract = Contract()
        contract.symbol = symbol if symbol else "GOOG"
        contract.secType = "OPT"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.lastTradeDateOrContractMonth = "20190315"
        contract.strike = 1180
        contract.right = "C"
        contract.multiplier = "100"
        #! [optcontract_us]
        return contract


    @staticmethod
    def OptionAtBOX(symbol:str=""):
        #! [optcontract]
        contract = Contract()
        contract.symbol = symbol if symbol else "GOOG"
        contract.secType = "OPT"
        contract.exchange = "BOX"
        contract.currency = "USD"
        contract.lastTradeDateOrContractMonth = "20190315"
        contract.strike = 1180
        contract.right = "C"
        contract.multiplier = "100"
        #! [optcontract]
        return contract


    """ Option contracts require far more information since there are many 
    contracts having the exact same attributes such as symbol, currency, 
    strike, etc. This can be overcome by adding more details such as the 
    trading class"""

    @staticmethod
    def OptionWithTradingClass(symbol:str=""):
        #! [optcontract_tradingclass]
        contract = Contract()
        contract.symbol = symbol if symbol else "SANT"
        contract.secType = "OPT"
        contract.exchange = "MEFFRV"
        contract.currency = "EUR"
        contract.lastTradeDateOrContractMonth = "20190621"
        contract.strike = 7.5
        contract.right = "C"
        contract.multiplier = "100"
        contract.tradingClass = "SANEU"
        #! [optcontract_tradingclass]
        return contract


    """ Using the contract's own symbol (localSymbol) can greatly simplify a
    contract description """

    @staticmethod
    def OptionWithLocalSymbol(symbol:str=""):
        #! [optcontract_localsymbol]
        contract = Contract()
        #Watch out for the spaces within the local symbol!
        contract.localSymbol = symbol if symbol else "P BMW  20221216 72 M"
        contract.secType = "OPT"
        contract.exchange = "EUREX"
        contract.currency = "EUR"
        #! [optcontract_localsymbol]
        return contract

    """ Dutch Warrants (IOPTs) can be defined using the local symbol or conid 
    """

    @staticmethod
    def DutchWarrant(symbol:str=""):
        #! [ioptcontract]
        contract = Contract()
        contract.localSymbol = symbol if symbol else "B881G"
        contract.secType = "IOPT"
        contract.exchange = "SBF"
        contract.currency = "EUR"
        #! [ioptcontract]
        return contract

    """ Future contracts also require an expiration date but are less
    complicated than options."""

    @staticmethod
    def SimpleFuture(symbol:str=""):
        #! [futcontract]
        contract = Contract()
        contract.symbol = symbol if symbol else "GBL"
        contract.secType = "FUT"
        contract.exchange = "EUREX"
        contract.currency = "EUR"
        contract.lastTradeDateOrContractMonth = "202303"
        #! [futcontract]
        return contract


    """Rather than giving expiration dates we can also provide the local symbol
    attributes such as symbol, currency, strike, etc. """

    @staticmethod
    def FutureWithLocalSymbol(symbol:str=""):
        #! [futcontract_local_symbol]
        contract = Contract()
        contract.secType = "FUT"
        contract.exchange = "EUREX"
        contract.currency = "EUR"
        contract.localSymbol = symbol if symbol else "FGBL MAR 23"
        #! [futcontract_local_symbol]
        return contract


    @staticmethod
    def FutureWithMultiplier(symbol:str=""):
        #! [futcontract_multiplier]
        contract = Contract()
        contract.symbol = symbol if symbol else "DAX"
        contract.secType = "FUT"
        contract.exchange = "EUREX"
        contract.currency = "EUR"
        contract.lastTradeDateOrContractMonth = "202303"
        contract.multiplier = "1"
        #! [futcontract_multiplier]
        return contract


    """ Note the space in the symbol! """

    @staticmethod
    def WrongContract(symbol:str=""):
        contract = Contract()
        contract.symbol = symbol if symbol else " IJR "
        contract.conId = 9579976
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    @staticmethod
    def FuturesOnOptions(symbol:str=""):
        #! [fopcontract]
        contract = Contract()
        contract.symbol = symbol if symbol else "GBL"
        contract.secType = "FOP"
        contract.exchange = "EUREX"
        contract.currency = "EUR"
        contract.lastTradeDateOrContractMonth = "20230224"
        contract.strike = 138
        contract.right = "C"
        contract.multiplier = "1000"
        #! [fopcontract]
        return contract

    @staticmethod
    def Warrants(symbol:str=""):
        #! [warcontract]
        contract = Contract()
        contract.symbol = symbol if symbol else "GOOG"
        contract.secType = "WAR"
        contract.exchange = "FWB"
        contract.currency = "EUR"
        contract.lastTradeDateOrContractMonth = "20201117"
        contract.strike = 1500.0
        contract.right = "C"
        contract.multiplier = "0.01"
        #! [warcontract]
        return contract

    """ It is also possible to define contracts based on their ISIN (IBKR STK
    sample). """

    @staticmethod
    def ByISIN(symbol:str=""):
        contract = Contract()
        contract.secIdType = "ISIN"
        contract.secId = symbol if symbol else "US45841N1072"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.secType = "STK"
        return contract


    """ Or their conId (EUR.uSD sample).
    Note: passing a contract containing the conId can cause problems if one of 
    the other provided attributes does not match 100% with what is in IB's 
    database. This is particularly important for contracts such as Bonds which 
    may change their description from one day to another.
    If the conId is provided, it is best not to give too much information as
    in the example below. """

    @staticmethod
    def ByConId(symbol:int=""):
        contract = Contract()
        contract.secType = "CASH"
        contract.conId = symbol if symbol else 12087792
        contract.exchange = "IDEALPRO"
        return contract


    """ Ambiguous contracts are great to use with reqContractDetails. This way
    you can query the whole option chain for an underlying. Bear in mind that
    there are pacing mechanisms in place which will delay any further responses
    from the TWS to prevent abuse. """

    @staticmethod
    def OptionForQuery(symbol:str=""):
        #! [optionforquery]
        contract = Contract()
        contract.symbol = symbol if symbol else "FISV"
        contract.secType = "OPT"
        contract.exchange = "SMART"
        contract.currency = "USD"
        #! [optionforquery]
        return contract


    @staticmethod
    def OptionComboContract(symbol:str=""):
        #! [bagoptcontract]
        contract = Contract()
        contract.symbol = symbol if symbol else "DBK"
        contract.secType = "BAG"
        contract.currency = "EUR"
        contract.exchange = "EUREX"

        leg1 = ComboLeg()
        leg1.conId = 577164786 #DBK Jun21'24 2 CALL @EUREX
        leg1.ratio = 1
        leg1.action = "BUY"
        leg1.exchange = "EUREX"

        leg2 = ComboLeg()
        leg2.conId = 577164767 #DBK Dec15'23 2 CALL @EUREX
        leg2.ratio = 1
        leg2.action = "SELL"
        leg2.exchange = "EUREX"

        contract.comboLegs = []
        contract.comboLegs.append(leg1)
        contract.comboLegs.append(leg2)
        #! [bagoptcontract]
        return contract


    """ STK Combo contract
    Leg 1: 43645865 - IBKR's STK
    Leg 2: 9408 - McDonald's STK """

    @staticmethod
    def StockComboContract(symbol:str=""):
        #! [bagstkcontract]
        contract = Contract()
        contract.symbol = symbol if symbol else "IBKR,MCD"
        contract.secType = "BAG"
        contract.currency = "USD"
        contract.exchange = "SMART"

        leg1 = ComboLeg()
        leg1.conId = 43645865#IBKR STK
        leg1.ratio = 1
        leg1.action = "BUY"
        leg1.exchange = "SMART"

        leg2 = ComboLeg()
        leg2.conId = 9408#MCD STK
        leg2.ratio = 1
        leg2.action = "SELL"
        leg2.exchange = "SMART"

        contract.comboLegs = []
        contract.comboLegs.append(leg1)
        contract.comboLegs.append(leg2)
        #! [bagstkcontract]
        return contract


    """ CBOE Volatility Index Future combo contract """

    @staticmethod
    def FutureComboContract(symbol:str=""):
        #! [bagfutcontract]
        contract = Contract()
        contract.symbol = symbol if symbol else "VIX"
        contract.secType = "BAG"
        contract.currency = "USD"
        contract.exchange = "CFE"

        leg1 = ComboLeg()
        leg1.conId = 326501438 # VIX FUT 201903
        leg1.ratio = 1
        leg1.action = "BUY"
        leg1.exchange = "CFE"

        leg2 = ComboLeg()
        leg2.conId = 323072528 # VIX FUT 2019049
        leg2.ratio = 1
        leg2.action = "SELL"
        leg2.exchange = "CFE"

        contract.comboLegs = []
        contract.comboLegs.append(leg1)
        contract.comboLegs.append(leg2)
        #! [bagfutcontract]
        return contract

    @staticmethod
    def SmartFutureComboContract(symbol:str=""):
        #! [smartfuturespread]
        contract = Contract()
        contract.symbol = symbol if symbol else "WTI" # WTI,COIL spread. Symbol can be defined as first leg symbol ("WTI") or currency ("USD")
        contract.secType = "BAG"
        contract.currency = "USD"
        contract.exchange = "SMART"

        leg1 = ComboLeg()
        leg1.conId = 55928698 # WTI future June 2017
        leg1.ratio = 1
        leg1.action = "BUY"
        leg1.exchange = "IPE"

        leg2 = ComboLeg()
        leg2.conId = 55850663 # COIL future June 2017
        leg2.ratio = 1
        leg2.action = "SELL"
        leg2.exchange = "IPE"

        contract.comboLegs = []
        contract.comboLegs.append(leg1)
        contract.comboLegs.append(leg2)
        #! [smartfuturespread]
        return contract

    @staticmethod
    def InterCmdtyFuturesContract(symbol:str=""):
        #! [intcmdfutcontract]
        contract = Contract()
        contract.symbol = symbol if symbol else "COL.WTI" #symbol is 'local symbol' of intercommodity spread. 
        contract.secType = "BAG"
        contract.currency = "USD"
        contract.exchange = "IPE"

        leg1 = ComboLeg()
        leg1.conId = 183405603 #WTI�Dec'23�@IPE
        leg1.ratio = 1
        leg1.action = "BUY"
        leg1.exchange = "IPE"

        leg2 = ComboLeg()
        leg2.conId = 254011009 #COIL�Dec'23�@IPE
        leg2.ratio = 1
        leg2.action = "SELL"
        leg2.exchange = "IPE"

        contract.comboLegs = []
        contract.comboLegs.append(leg1)
        contract.comboLegs.append(leg2)
        #! [intcmdfutcontract]
        return contract


    @staticmethod
    def NewsFeedForQuery():
        #! [newsfeedforquery]
        contract = Contract()
        contract.secType = "NEWS"
        contract.exchange = "BRFG" #Briefing Trader
        #! [newsfeedforquery]
        return contract


    @staticmethod
    def BTbroadtapeNewsFeed():
        #! [newscontractbt]
        contract = Contract()
        contract.symbol  = "BRF:BRF_ALL"
        contract.secType = "NEWS"
        contract.exchange = "BRF"
        #! [newscontractbt]
        return contract


    @staticmethod
    def BZbroadtapeNewsFeed():
        #! [newscontractbz]
        contract = Contract()
        contract.symbol = "BZ:BZ_ALL"
        contract.secType = "NEWS"
        contract.exchange = "BZ"
        #! [newscontractbz]
        return contract


    @staticmethod
    def FLYbroadtapeNewsFeed():
        #! [newscontractfly]
        contract = Contract()
        contract.symbol  = "FLY:FLY_ALL"
        contract.secType = "NEWS"
        contract.exchange = "FLY"
        #! [newscontractfly]
        return contract


    @staticmethod
    def ContFut(symbol:str=""):
        #! [continuousfuturescontract]
        contract = Contract()
        contract.symbol = symbol if symbol else "GBL"
        contract.secType = "CONTFUT"
        contract.exchange = "EUREX"
        #! [continuousfuturescontract]
        return contract

    @staticmethod
    def ContAndExpiringFut(symbol:str=""):
        #! [contandexpiringfut]
        contract = Contract()
        contract.symbol = symbol if symbol else "GBL"
        contract.secType = "FUT+CONTFUT"
        contract.exchange = "EUREX"
        #! [contandexpiringfut]
        return contract

    @staticmethod
    def JefferiesContract(symbol:str=""):
        #! [jefferies_contract]
        contract = Contract()
        contract.symbol = symbol if symbol else "AAPL"
        contract.secType = "STK"
        contract.exchange = "JEFFALGO"
        contract.currency = "USD"
        #! [jefferies_contract]
        return contract

    @staticmethod
    def CSFBContract(symbol:str=""):
        #! [csfb_contract]
        contract = Contract()
        contract.symbol = symbol if symbol else "IBKR"
        contract.secType = "STK"
        contract.exchange = "CSFBALGO"
        contract.currency = "USD"
        #! [csfb_contract]
        return contract

    @staticmethod
    def USStockCFD(symbol:str=""):
        # ! [usstockcfd_conract]
        contract = Contract()
        contract.symbol = symbol if symbol else "IBM"
        contract.secType = "CFD"
        contract.currency = "USD"
        contract.exchange = "SMART"
        # ! [usstockcfd_conract]
        return contract

    @staticmethod
    def EuropeanStockCFD(symbol:str=""):
        # ! [europeanstockcfd_contract]
        contract = Contract()
        contract.symbol = symbol if symbol else "BMW"
        contract.secType = "CFD"
        contract.currency = "EUR"
        contract.exchange = "SMART"
        # ! [europeanstockcfd_contract]
        return contract

    @staticmethod
    def CashCFD(symbol:str=""):
        # ! [cashcfd_contract]
        contract = Contract()
        contract.symbol = symbol if symbol else "EUR"
        contract.secType = "CFD"
        contract.currency = "USD"
        contract.exchange = "SMART"
        # ! [cashcfd_contract]
        return contract

    @staticmethod
    def QBAlgoContract(symbol:str=""):
        # ! [qbalgo_contract]
        contract = Contract()
        contract.symbol = symbol if symbol else "ES"
        contract.secType = "FUT"
        contract.exchange = "QBALGO"
        contract.currency = "USD"
        contract.lastTradeDateOrContractMonth = "202003"
        # ! [qbalgo_contract]
        return contract

    @staticmethod
    def IBKRATSContract(symbol:str=""):
        # ! [ibkrats_contract]
        contract = Contract()
        contract.symbol = symbol if symbol else "SPY"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "IBKRATS"
        # ! [ibkrats_contract]
        return contract

    @staticmethod
    def CryptoContract(symbol:str=""):
        # ! [crypto_contract]
        contract = Contract()
        contract.symbol = symbol if symbol else "ETH"
        contract.secType = "CRYPTO"
        contract.currency = "USD"
        contract.exchange = "PAXOS"
        # ! [crypto_contract]
        return contract

    @staticmethod
    def StockWithIPOPrice(symbol:str=""):
        # ! [stock_with_IPO_price]
        contract = Contract()
        contract.symbol = symbol if symbol else "EMCGU"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        # ! [stock_with_IPO_price]
        return contract

    @staticmethod
    def ByFIGI():
        # ! [ByFIGI]
        contract = Contract()
        contract.secIdType = "FIGI"
        contract.secId = "BBG000B9XRY4"
        contract.exchange = "SMART"
        # ! [ByFIGI]
        return contract
        
    @staticmethod
    def ByIssuerId(symbol:str=""):
        # ! [ByIssuerId]
        contract = Contract()
        contract.issuerId = symbol if symbol else "e1453318"
        # ! [ByIssuerId]
        return contract

    @staticmethod
    def FundContract(symbol:str=""):
        # ! [fundcontract]
        contract = Contract()
        contract.symbol = symbol if symbol else "I406801954"
        contract.secType = "FUND"
        contract.exchange = "ALLFUNDS"
        contract.currency = "USD"
        # ! [fundcontract]
        return contract

def Test():
    from ibapi.utils import ExerciseStaticMethods
    ExerciseStaticMethods(ContractSamples)


if "__main__" == __name__:
    Test()

