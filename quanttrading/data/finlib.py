#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 24 12:39:21 2023
@author: yanyanzl

"""


import pandas as pd
from pandas_datareader import data
from datetime import datetime, timedelta
import requests_cache
import sys
import requests
import statistics as st

import traceback
# import logging

import yfinance as yf

from pathlib import Path  # if you haven't already done so
from sys import path as pt
file = Path(__file__).resolve()
pt.append(str(file.parents[1]))

from data.db.db_settings import VALIDATION_ADDRESS, DEBUG
from constant import ChartInterval

# this is the only way works so far. to use yfinance override pandas_datareader.
yf.pdr_override()


default_asset = "SPX"
start = datetime(datetime.now().year, 1, 1)

end = datetime.today()

# the price to be choosen as the base of the calculation. from Open,
# Close, High, Low, adjClose. default is Close
target_price = "Close"

# initialize the mode to be test mode
test_mode = True


"""
Making the same request repeatedly can use a lot of bandwidth, slow down
your code and may result in your IP being banned.
pandas-datareader allows you to cache queries using requests_cache
by passing a requests_cache. Session to DataReader or Options
using the session parameter.
"""

# cache time for the connection sessions
expire_after = timedelta(days=1)

# With caching, the response will be fetched once, saved to cache.sqlite,
# and subsequent requests will return the cached response near-instantly.
csession = requests_cache.CachedSession(
    cache_name="cache",
    backend="sqlite",
    expire_after=expire_after,
    cache_control=True,
)


# define a descriptor class by implementing the .__get__() and .__set__()
# special methods, which are part of the descriptor protocol
# set and get the attribute of the class by a positive number
# example: in another class Rectangle, you have
# an attribute length = PositiveNumber(), then you could use the following:
# rectangle1 = Rectangle(100)
# rectangle1.length or rectangle1.length = 200,

class PositiveNumber:
    def __set_name__(self, owner, name):
        self._name = name

    # instance is the current instance of the Class itself
    # __dict__ is all the attributes and functions it has
    def __get__(self, instance, owner):
        return instance.__dict__[self._name]

    def __set__(self, instance, value):
        if not isinstance(value, int | float) or value < 0:
            raise ValueError("positive number expected for ", self._name)
        instance.__dict__[self._name] = value

class PositiveNumber:
    def __set_name__(self, owner, name):
        self._name = name

    # instance is the current instance of the Class itself
    # __dict__ is all the attributes and functions it has
    def __get__(self, instance, owner):
        return instance.__dict__[self._name]

    def __set__(self, instance, value):
        if not isinstance(value, int | float) or value < 0:
            raise ValueError("positive number expected for ", self._name)
        instance.__dict__[self._name] = value


# descriptor class for string attributes
class StringName(str):
    def __init__(self, name=""):
        self.name = name

    def __set_name__(self, owner, name):
        self._name = name

    # instance is the current instance of the Class itself
    # __dict__ is all the attributes and functions it has
    def __get__(self, instance, owner):
        return instance.__dict__[self._name]

    def __set__(self, instance, value):
        if not isinstance(value, str):
            raise ValueError("string expected for ", self._name)
        instance.__dict__[self._name] = value


# finclass
# to be added:
# max draw down (month, year): from nearest peak to nearest trough 
# to define a function to get N months max draw down for the asset.

# and unit test cases

class Asset:
    # intiate the attributes of the asset. 
    def __init__(self, asset_name=default_asset, data_interval: ChartInterval = ChartInterval.D1, startdate: datetime = start, enddate: datetime = end):
        self.name = StringName(asset_name)

        self._interval = data_interval

        self.startdate = startdate

        self.enddate = enddate

        # format the data structure for target, prices info get from internet
        # from startdate to enddate
        self.his_price = pd.DataFrame()

        # mean value for prices from startdate to enddate
        self.price_mean = PositiveNumber()

        # standard deviation of the asset based on the prices
        # from startdate to enddate, is the risk of the asset
        self.price_sd = PositiveNumber()

        # variation of the asset based on the prices from startdate to enddate
        self.price_va = PositiveNumber()

        # variation of the asset based on the prices from startdate to enddate
        self.expect_return = PositiveNumber()

        # Beta (β) is primarily used in the capital asset pricing model (CAPM), is a measure of the volatility–or systematic risk–of a security or portfolio compared to the market as a whole (usually the S&P 500); 
        # can only provide an investor with an approximation of how much risk the stock will add to a (presumably) diversified portfolio
        # Stocks with betas above 1 will tend to move with more momentum than the S&P 500; stocks with betas less than 1 with less momentum
        # In order to make sure that a specific stock is being compared to the right benchmark, it should have a high R-squared value in relation to the benchmark
        # Cov(Ri,Rm)/σm2 : correlation between an asset and the market devided by the market variance. or (ρ * σi) / σm : correlation coefficient * standard deviation of asset devided by standard deviation of market
        self.beta = 0

        # Sharpe Ratio : The Sharpe ratio compares the return of an investment with its risk.
        # Sharpe = (Rp - Rf) / σp : (return of portfolio - Risk-free rate) / Standard deviation of the portfolio's return
        self.sharpe = 0

        # The Treynor ratio is a simple extension of the Sharpe ratio and resolves the Sharpe ratio’s first limitation by substituting beta (systematic risk) for total risk
        # Treynor Ratio = (Rp - Rf) / βp : (asset return - risk-free rate) / systematic risk β.
        self.treynor = 0

        # M2 provides a measure of portfolio return that is adjusted for the total risk of the portfolio relative to that of some benchmark. risk-adjusted performance
        # M2 borrows from capital market theory by assuming a portfolio is leveraged or de-leveraged until its volatility (as measured by standard deviation) matches that of the market. This adjustment produces a portfolio-specific leverage ratio that equates the portfolio’s risk to that of the market. The portfolio’s excess return times the lever- age ratio plus the risk-free rate is then compared with the markets actual return to determine whether the portfolio has outperformed or underperformed the market on a risk-adjusted basis.M can be thought of as a rescaling of the Sharpe ratio that allows for easier comparisons among different portfolios. M2 = (Rp - Rf) * σm / σp + Rf = SharpeRatio * σm + Rf
        self.m2 = 0

        # Jensen’s Alpha
        # Jensen’s alpha is based on systematic risk. We can measure a portfolio’s systematic risk by estimating the market model, which is done by regress- ing the portfolio’s daily return on the market’s daily return. The coefficient on the market return is an estimate of the beta risk of the portfolio. We can calculate the risk-adjusted return of the portfolio using the beta of the portfolio and the CAPM. The difference between the actual portfolio return and the calculated risk-adjusted return is a measure of the portfolio’s performance relative to the market portfolio and is called Jensen’s alpha. By definition, αm of the market is zero. Jensen’s alpha is also the vertical distance from the SML measuring the excess return for the same risk as that of the market
        # αp = Rp - [Rf + β(Rm -Rf)]
        self.alpha = 0

    def is_valid(self, name=""):
        """
        check if the give name is an valid asset ticker online. if name is empty. check the asset itself.
        """
        if name == "":
            name = self.name
        try:
            res = requests.get(VALIDATION_ADDRESS + name)
            if DEBUG:
                print("----Response in is_valid funcion is ---------", res)
                print("Status code is ",res.status_code,
                      "ticker name is ", name, 
                      "validation address is ", VALIDATION_ADDRESS, 
                      name)

            if res.status_code == 200:
                return True
        except Exception as ex:
            pass
        return False
    
    def getData(self, chartInterval: ChartInterval = None):
        """
        
        """
        ticker = yf.Ticker(self.name)
        data = yf.download()
        return data
        pass

    def get_return_his(self, name="", period=0):
        """
        Get Asset Expected return: get the expected return for a specific asset based on the historical data
        the return is an average return for the given period (number of years, default current year only)
        """
        try:
            # bey default, get the class's price data.
            if name == "" and period == 0:
                # the price data is not ready yet.
                if len(self.his_price) == 0:
                    self.fetch_his_price()

                his_price = self.his_price

            # period is specified.
            elif name == "":
                his_price = self.fetch_his_price(period=period)

            # if the name is given, fetch the specified name's price data
            else:
                his_price = self.fetch_his_price(name=name, period=period)

            if test_mode:
                print(
                    "$$$$$$$$$$$$$$$ this is the head data of the asset $$$$$$$$$$$$$"
                )
                print(his_price.head(1))
                print(
                    "$$$$$$$$$$$$$$$ this is the head data of the asset $$$$$$$$$$$$$"
                )
                # for col in asset_data.columns:
                print(his_price.columns)
                # print(asset_data.index)

            asset_return = self.avg_return_years(
                asset_his_data=his_price, period=period
            )

            return format(asset_return, ".3f")

        except Exception as ex:
            format_excetpion_message(ex)

    # =============================================================================
    # get the average return of the past n years.
    # =============================================================================

    def avg_return_years(
        self,
        asset_his_data=pd.DataFrame(),
        period=1,
    ):
        try:
            # n years have n return rates to calculate.
            start_price_list = list()
            end_price_list = list()

            if test_mode:
                print(
                    "^^^^^^^head data of the asset in avg_return_years ^^^^^^"
                )
                print(asset_his_data.head(1))
                print(
                    "^^^^^^ head data of the asset in avg_return_years ^^^^^^"
                )

            for i in range(period):
                # start date list building -----------------
                i_start_date = datetime(self.enddate.year - i, month=1, day=2)

                if test_mode:
                    print(
                        "date to string of the last -- ",
                        i,
                        "--- years is",
                        date_to_str(i_start_date),
                    )

                # find the first trading date of the year
                j = 0
                while True:
                    j = j + 1
                    # the first trading day.
                    if date_to_str(i_start_date) in asset_his_data.index:
                        start_price_list.append(
                            asset_his_data.loc[date_to_str(i_start_date)][
                                target_price
                            ]
                        )

                        break
                    # exception if can't find it in 365 days.
                    elif j > 365:
                        raise Exception(
                            "start date can't find data in the given dataset",
                            "in function avg_return_years with start date: ",
                            i_start_date,
                            "and asset history data dates are\n",
                            asset_his_data.index,
                        )
                    else:
                        # start date + 1
                        i_start_date = i_start_date + timedelta(days=1)

                # end date list building---------------

                # current year, the end_date is not the end of the year
                if i == 0:
                    i_end_date = self.enddate
                # the other years, the end_date is the end of the year
                else:
                    i_end_date = datetime(
                        self.enddate.year - i, month=12, day=31
                    )

                if test_mode:
                    print(
                        "date to string of the last -- ",
                        i,
                        "--- years is",
                        date_to_str(i_end_date),
                    )

                k = 0
                while True:
                    k = k + 1
                    if date_to_str(i_end_date) in asset_his_data.index:
                        end_price_list.append(
                            asset_his_data.loc[date_to_str(i_end_date)][
                                target_price
                            ]
                        )

                        break
                    # exception if can't find it in 365 days.
                    elif k > 365:
                        raise Exception(
                            "end date can't find data in the given dataset",
                            "in function avg_return_years with end date: ",
                            i_end_date,
                            "and asset history data dates are\n",
                            asset_his_data.index,
                        )
                    else:
                        # end date - 1
                        i_end_date = i_end_date - timedelta(days=1)

            # get the result from the other function
            result = self.avg_return_from_list(
                start_price_list, end_price_list
            )
            return result

        except Exception as ex:
            format_excetpion_message(ex)

    # =============================================================================
    # Time-weighted rate of return
    # An investment measure that is not sensitive to the additions and withdrawals
    # of funds is the time-weighted rate of return. The time-weighted rate of
    # return measures the compound rate of growth of $1 initially invested in the
    # portfolio over a stated mea- surement period. For the evaluation of
    # portfolios of publicly traded securities, the time-weighted rate of return
    # is the preferred performance measure as it neutralizes the effect of cash
    # withdrawals or additions to the portfolio, which are generally outside of
    # the control of the portfolio manager.
    # rTW = ([(1+r1)×(1+r2)×... ×(1+rN)] root N) − 1
    # calculate avg return from two list.
    # =============================================================================

    def avg_return_from_list(
        self, start_price_list=list(), end_price_list=list()
    ):
        try:
            # the length of these two list should be equal
            if test_mode:
                print(
                    "this is the start price list--------:\n", start_price_list
                )
                print("this is the end price list--------:\n", end_price_list)

            list_size = len(start_price_list)

            # if list is empty
            if list_size == 0:
                raise Exception(
                    "input list size in avg_return_from_list is 0. start_price_list is\n",
                    start_price_list,
                    "and the end_price list is\n",
                    end_price_list,
                )

            # if the elements number are same
            elif len(start_price_list) == len(end_price_list):
                # format the list to float
                new_start_price_list = [float(i) for i in start_price_list]
                new_end_price_list = [float(j) for j in end_price_list]

                total_return = 1
                for k in range(list_size):
                    # (1+r1) * (1+r2) * ... * (1+rN)
                    total_return = total_return * (
                        new_end_price_list[k] / new_start_price_list[k]
                    )

                # rTW = ([(1+r1)×(1+r2)×... ×(1+rN)] root N) − 1
                total_return = total_return ** (1 / list_size) - 1

                # change unit is percentage
                total_return = total_return * 100

                return total_return

            # if the elements number are not same, this is an exception
            else:
                raise Exception(
                    "input of two list size is not equal. start_price_list is\n",
                    start_price_list,
                    "and the end_price list is\n",
                    end_price_list,
                )

        except Exception as ex:
            format_excetpion_message(ex)


    # fetch history price data for asset "name". default is the class's
    # history price, for period of n years
    def fetch_his_price(self, name="", period=0) -> pd.DataFrame:
        try:
            # bey default, get the class's price data.

            # no input for name
            if name == "":
                # no input for period
                if period == 0:
                    # if history price for self is not available yet. get it.
                    if len(self.his_price) == 0:
                       self.his_price = data.DataReader(
                            self.name,
                            # data_source = 'yahoo',
                            start = self.startdate,
                            end = self.enddate,
                            session = csession,
                        )

                    his_price = self.his_price

                # period is specified. get data for period years
                else:
                    # yf.download()
                    his_price = data.DataReader(
                        self.name,
                        datetime(datetime.now().year - period, 1, 1),
                        self.enddate,
                        session=csession,
                    )

            # if the name is given, fetch the specified name's price data
            else:
                # no input for period
                if period == 0:
                    his_price = data.DataReader(
                        name, self.startdate, self.enddate, session=csession
                    )

                # period is specified. get data for period years
                else:
                    his_price = data.DataReader(
                        name,
                        datetime(datetime.now().year - period, 1, 1),
                        self.enddate,
                        session=csession,
                    )

            # if the data is empty, raise exception
            if len(his_price) == 0:
                raise Exception(
                    f"can not get any history price data for {self.name} date from {self.startdate} to {self.enddate}"
                )
            else:
                return his_price

        except Exception as ex:
            format_excetpion_message(ex)

    # calculate the mean of the price
    def cal_price_mean(self):
        try:
            if len(self.his_price) == 0:
                self.fetch_his_price()

            self.mean = self.his_price[target_price].mean()

            # if the data is empty, raise exception
            if self.mean == 0:
                raise Exception(f"mean of history price is 0 for {self.name}")
            else:
                return self.mean

        except Exception as ex:
            format_excetpion_message(ex)

    # calculate the standard deviation of the price. it;s the risk
    # standard deviation  = square root of sample variance
    # Standard deviation is a measure of the dispersion of data from
    # its average
    def cal_price_sd(self):
        try:
            if len(self.his_price) == 0:
                self.fetch_his_price()

            self.price_sd = st.stdev(self.his_price[target_price])

            # debug mode only
            if test_mode:
                print(
                    "Standard deviation for the",
                    target_price,
                    "of",
                    self.name,
                    "is",
                    "{:.3f}".format(self.price_sd),
                )

            # if the data is empty, raise exception
            if self.price_sd == 0:
                raise Exception(
                    f"standard deviation of history price is 0 for {self.name}"
                )
            else:
                return self.price_sd

        except Exception as ex:
            format_excetpion_message(ex)

    # Variance for targets sample Variance (Sum of square of (Xi - meanX)) / (n-1)
    # Variance for targets population Variance (Sum of square of (Xi - meanX))
    # Covariance shows whether the two variables tend to move in the same direction
    # calculate the variation of the price.
    def cal_price_variation(self):
        try:
            if len(self.his_price) == 0:
                self.fetch_his_price()

            self.price_va = st.variance(self.his_price[target_price])

            # debug mode only
            if test_mode:
                print(
                    "Variance for the",
                    target_price,
                    "of",
                    self.name,
                    "is",
                    "{:.3f}".format(self.price_va),
                )

            # if the data is empty, raise exception
            if self.price_va == 0:
                raise Exception(
                    f"variance of history price is 0 for {self.name}"
                )
            else:
                return self.price_va

        except Exception as ex:
            format_excetpion_message(ex)


# time to date string format: 2023-10-23
def date_to_str(dt=datetime.today()):
    try:
        date_format = "%Y-%m-%d"
        result = dt.strftime(date_format)
    except ValueError:
        result = datetime.today().strftime(date_format)
    return result


# standardize the format to handle the exeption
def format_excetpion_message(ex=Exception("General exception")):
    try:
        template = "An exception of type {0} occurred. Arguments:\n {1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)

        if test_mode:
            # the same stacktrace you get if you do not catch the exception
            print("trace back message:", traceback.format_exc())

            # log the exception message
            # If you use the logging module, you can print the exception to the log (along with a message)
            # log = logging.getLogger()
            # log.exception("Logging message to debug!")

            # dig deeper and examine the stack, look at variables etc.,
            # use the post_mortem function of the pdb module inside the except block:
            # pdb.post_mortem()

        sys.exit()

    except Exception:
        print("trace back message:", traceback.format_exc())
        sys.exit()


# test the function
def main():
    asset = Asset("TSLA")
    print(asset)
    asset.fetch_his_price()
    print(asset.his_price)
    

if __name__ == "__main__":
    main()



