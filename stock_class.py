import os
import sys
import shutil
import urllib
import datetime
import pandas as pd
from pandas.io.data import DataReader
import easygui as eg
import stock_helper
import stock_database
import numpy as np
import pdb
import matplotlib.pyplot as plt

SYMBOL_DIC = stock_helper.load_symbol_dic()

class stock:
  """
  Class for creating and analyzing stocks from yahoo finance
  """

  def __init__(self,symbol='unknown',start=datetime.date.today()-datetime.timedelta(365/12),
              end=datetime.date.today(),name='unknown',mode='online',interactive=True,
              historical=None):
    """
    Parameters:
    		- symbol : string, optional. !! CAREFUL!! Either the symbol or the name has to be
                   provided. It is strongy recommended to provide the symbol rather than the name
                   Ticker symbol of the stock

        - start : string, optional (default: 30 days before today)
                  Starting date for the historical data. The format is mm/dd/yyyy
                  Default value is 30 days before the current date (or the nearest valid date)

        - end : string, optional (default: today)
                Ending date for the historical data. The format is mm/dd/yyyy
                Default is the current date (or the last valid date, eg. Friday for a Sunday)

        - name : string, optional(default="unknown")
                 Name of the company, index, fund or currency tracked

        - mode : string, optional (default: online)
                 In "online" mode, the historical data from start date to end date is directly
                 downloaded from Yahoo Finance API.
                 In "disk" mode, the historical data is extracted from hard drive 

        - symbol_dic : dictionary. At initialization, a dictionary {symbol - company name} will
                       be loaded. No need for modifications.
    """

    self._symbol = symbol
    self._name = name
    self._start = start
    self._end = end
    self._mode = mode
    self._interactive = interactive
    self._historical = historical

    self._start = self.start()   # <-- check format of start date
    self._end = self.end()       # <-- check format of end date, end that end > start

    if self._symbol == 'unknown' and self._name != 'unknown':
      self._symbol = self.get_symbol()

    elif self._name == 'unknown' and self._symbol != 'unknown':
      self._name = self.get_name()

    else:
      print 'please provide the symbol or name for the stock'

  def __repr__(self):
    """
    String representation of the instance stock object
    """
    rep = "stock("
    rep += str(self._symbol) + ", "
    rep += str(self._name) + ", from "
    rep += str(self._start) + " to "
    rep += str(self._end) + ", "
    rep += str(self._mode) + " mode)"
    return rep


  def symbol(self):
    return self._symbol

  def name(self):
    return self._name

  def mode(self):
    return self._mode

  def interactive(self):
    return self._interactive

  def historical(self):
    return self._historical


  def start(self):
    """
    Check that the start date has the correct format. Convert to datetime.date format
    """
    if type(self._start) != datetime.date:
      self._start,check = stock_helper.check_date_format(self._start)
      if check == 'fail':
        print ('please use the correct format for the date, dd/mm/yyyy')
        del self
        sys.exit()
    return self._start


  def end(self):
    """
    Check that the end date has the correct format. Convert to datetime.date format
    Then check that the end date is later than the start date
    """
    if type(self._end) != datetime.date:
      self._end,check = stock_helper.check_date_format(self._end)
      if check == 'fail':
        print ('please use the correct format for the date, dd/mm/yyyy')
        del self
        sys.exit()
    if self._start > self._end:
      print ('The start date must be prior to the end date')
      del self
      sys.exit()
    return self._end


  def get_historical(self):
    """
    If mode = "online", download Yahoo quotes from start to end date in a pandas dataframe
    If mode = "disk", the data is extracted from the hard drive
    """
    if self._mode == "online":
      self._historical = DataReader(self._symbol,'yahoo',self._start,self._end)
    else:
      # check dictionary of symbols and open the file at the correct location
      data = stock_database.extract_series(self._symbol)
      df = pd.DataFrame(data,columns = ['date','Open','High','Low','Close','Volume','Adj Close'])
      self._historical = df[pd.to_datetime(df['date']) > self._start]
      self._historical = self._historical[pd.to_datetime(df['date']) < self._end]
    self._historical = self._historical.set_index('date')
    return self._historical


  def get_name(self):
    """
    Get the name of the company associated with the symbol
    """
    try:
      self._name = SYMBOL_DIC[self._symbol]
    except:
      if self._interactive == True:
        print 'this symbol is currently not in the dictionary'
    return self._name


  def get_symbol(self):
    """
    Get the symbol associated with the company's or index name.
    Careful: If not in interactive mode, using company's name in class
             initialization is not recommended, or it has to be exactly matching
             the name in the dictionary.
    """
    idx = 0
    for company_name in SYMBOL_DIC.values():
      if self._name.lower() == company_name[0]:           # <-- check for exact match first
        self._symbol = SYMBOL_DIC.keys()[idx]
        break
      elif self._name.lower() in company_name[0] and self._interactive == True:  # <-- if partial match and interactive mode, ask the user
        question = eg.ynbox('are you talking about %s?' %(company_name[0]))
        if question == 1:
          self._symbol = SYMBOL_DIC.keys()[idx]
          break
      idx += 1
    if self._symbol == 'unknown':  # <-- after checking all entries of the dictionary
      print('The provided company name does not match any symbol')
      del self
      sys.exit()
    return self._symbol


  def get_Sharpe(self):
    """
    Calculate the Sharpe ratio for the perod between start and end dates
    assuming 4% annual risk-free rate, and 252 trading days a year
    """
    daily_return=(self._historical['Adj Close'][1:].as_matrix()-self._historical['Adj Close'][:-1].as_matrix())/self._historical['Adj Close'][:-1].as_matrix()
    excess = daily_return - 0.04/252
    Sharpe = np.sqrt(252)*np.mean(excess)/np.std(excess)
    return Sharpe

  def moving_avg(self,window):
    """M
    Calculate the moving average of the adjusted close price of the stock
    window is the number of days for calculating the average
    """
    try:
      if not self._historical:
        self.get_historical()
    except:
      pass
    return pd.rolling_mean(self._historical['Adj Close'].iloc[window+1:],window)

  def moving_std(self,window):
    try:
      if not self._historical:
        self.get_historical()
    except:
      pass
    return pd.rolling_std(self._historical['Adj Close'].iloc[window+1:],window)

  def bollinger_bands(self,N_period,K_sigma):
    """
    Plot the central bollinger band for a look back period of N_period, and the upper and
    lower band at K*standard deviations above the moving average
    """
    rolling_mean = self.moving_avg(N_period)
    rolling_std = self.moving_std(N_period)
    data = self._historical
    data['Adj Close'].plot(style='k.')
    plt.ylabel('Adj Close Price')
    rolling_mean.plot(color='k')
    top = rolling_mean + K_sigma * rolling_std
    bottom = rolling_mean - K_sigma * rolling_std
    top.plot(color='r')
    bottom.plot(color='b')
    plt.show()
    return