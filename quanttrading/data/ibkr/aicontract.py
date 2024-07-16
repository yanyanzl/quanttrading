"""
Copyright (C) Steven Jiang. All rights reserved. This code is subject to the terms
 and conditions of the MIT Non-Commercial License, as applicable.
build contract object:
    symbol: tick name for the contract. example: TSLA, AAPL
    SecType [get, set]
 	    The security's type: STK - stock (or ETF) OPT - option FUT - future IND - index FOP - futures option CASH - forex pair BAG - combo WAR - warrant BOND- bond CMDTY- commodity NEWS- news FUND- mutual fund
    ConId: int. Identifier to specify an exact contract.

    Exchange: String. Exchange for which data or trades should be routed.

    PrimaryExchange: String. Primary listing exchange of the instrument.

    Currency: String. Base currency the instrument is traded on.
"""
from ibapi.contract import Contract

#Function to create FX contract, by passing symbol of six letters like EURUSD
def fx_contract(symbol):
	contract = Contract()
	contract.symbol = symbol[:3]
	contract.secType = 'CASH'
	contract.exchange = 'IDEALPRO'
	contract.currency = symbol[3:]
	return contract

#Function to create stock contract, by passing ticker name
def stock_contract(symbol,pri_exchange=""):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    if pri_exchange:
        contract.primaryExchange = pri_exchange
    return contract