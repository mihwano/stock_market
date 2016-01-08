"""
Retrieves data from Yahoo Finance. Plots candle stick chart, adjusted close and volume
as a function of date. Calculates Sharpe ratio, plots trends and give buy 
and sell points
"""
import easygui as eg
import os
import sys
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick
import matplotlib
from matplotlib.dates import  DateFormatter,MonthLocator,WeekdayLocator,DayLocator,MONDAY
import pandas as pd
from pandas.io.data import DataReader
import datetime
import time
import pdb

def select_options(symbol_dic):
  """ Set a few options for the plots"""
  options = 0
#  candle_chart = eg.ynbox(msg = 'Plot candle chart?', title = 'option 1')
  while options == 0:
    title = 'Please enter some information'
    msg = 'Note: the format for the date is dd/mm/yyyy. By default the end date is today, the start date, one month before'
    fieldNames = ['start_date','end_date','stock_symbol or company name']
    fieldValues = eg.multenterbox(msg,title,fieldNames)

    if not fieldValues[1]:
      end = datetime.date.today()
    else:
      try:
        end = datetime.datetime(int(fieldValues[1][-4:]),int(fieldValues[1][-7:-5]),int(fieldValues[1][:2]))
      except:
        eg.msgbox('please use the correct format for the date, day / month / year')
        options = 0
        continue

    if not fieldValues[0]:
      start = datetime.date.today()-datetime.timedelta(365/12)
    else:
      try:
        start = datetime.date(int(fieldValues[0][-4:]),int(fieldValues[0][-7:-5]),int(fieldValues[0][:2]))
      except:
        eg.msgbox('please use the correct format for the date, day / month / year')
        options = 0
        continue

    if start > end:
      eg.msgbox('The start date should be before the end date, noob')
      options = 0
      continue

    options = 1
    """ Check the correctness of the entries"""
    if fieldValues[2] not in symbol_dic:
      fieldValues[2] = fieldValues[2].lower()
      idx = 0
      for name in symbol_dic.values():
        if fieldValues[2] in name:
          question = eg.ynbox('are you talking about %s?' %(name))
          if question == 1:
            fieldValues[2] = symbol_dic.keys()[idx]
            break
          else:
            idx += 1
            continue
        idx += 1
      if idx == len(symbol_dic):
        eg.msgbox('the company is not in the database or the symbol is incorrect')
        options = 0
        continue
        
  return start, end, fieldValues[2]     #, candle_chart

def load_symbol_dic():
  """
  Load a dictionary of all tickers symbols in the NSYE, NASDAQ and AMEX stock
  markets. {keys - values}  ==  {symbol - company name}
  """
  directory = '/home/gilles/projects/trading/quant_trading/symbols'
  dic = {}
  for item in os.listdir(directory):
    with open(directory+'/'+item) as f:
      for line in f:
        if line.split(',')[0].replace('\"','') not in dic:
          dic[line.split(',')[0].replace('\"','')] = line.split(',')[1].replace('\"','').lower()
  return dic

def plot_data(data,stock):
  ticks = eg.choicebox(msg = 'choose ticks for the plot',choices = ['day','week','month'])
  if ticks == 'month':
    loc = MonthLocator()
  elif ticks == 'week':
    loc = WeekdayLocator(byweekday=MONDAY)
  elif ticks == 'day':
    loc = DayLocator()
  weekFormatter = DateFormatter('%b %d')
  dayFormatter = DateFormatter('%d')
    
#  if candle_chart == 1:
  fig = plt.figure()
  ax1 = fig.add_subplot(211)
  datelist = [matplotlib.dates.date2num(x) for x in data['Time']]
  Prices = []
  for idx in xrange(len(data)):
    Prices.append((datelist[idx],data['Open'].ix[idx],data['Close'].ix[idx],data['High'].ix[idx],data['Low'].ix[idx]))
#    candlestick(ax1,[datelist,data['Open'],data['Close'],data['High'],data['Low']])
  candlestick(ax1,Prices)
  ax1.set_xlabel('Date')
  ax1.set_ylabel('$')
  ax1.set_title('Candlestick plot for %s' %stock)
  ax2 = fig.add_subplot(212)
  ax2.plot(datelist,data['Adj Close'],'-r',label = 'Adj. Close')
  ax2.set_ylabel('$')
  ax2.legend()
  ax3 = ax2.twinx()
  ax3.bar(data['Time'],data['Volume'])
  ax3.set_ylabel('Shares')
  ax1.xaxis_date()
  ax2.xaxis_date()
  ax3.xaxis_date()
  plt.show()
  return

def Sharpe_ratio(data):
  """ Assuming 4% annual risk-free rate, and 252 trading days a year"""
  daily_return=(data['Adj Close'][1:].as_matrix()-data['Adj Close'][:-1].as_matrix())/data['Adj Close'][:-1].as_matrix()
  excess = daily_return - 0.04/252
  Sharpe = np.sqrt(252)*np.mean(excess)/np.std(excess)
  return Sharpe

# -----------------------------------------------------------------------#
stock_dic = load_symbol_dic()
start_date, end_date, stock = select_options(stock_dic)

data = DataReader(stock,'yahoo',start_date,end_date)
data['Time'] = data.index

Sharpe = Sharpe_ratio(data)
eg.msgbox('The Sharpe ratio(%s) = %s' %(stock,Sharpe)) 

plot_data(data,stock)

