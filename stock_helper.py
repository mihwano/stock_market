#################################################################

#			REPOSITORY OF HELPER FUNCTIONS FOR STOCK_CLASS            #

#################################################################

import os
import datetime
import numpy as np
import pandas as pd
from pandas.io.data import DataReader
import statsmodels.tsa.stattools as ts
import pdb
from scipy.stats import linregress
from pandas.stats.api import ols
import arch.unitroot

def check_date_format(check_date):
  """
  Check that user entered date follows the format mm/dd/yyyy
  If format is correct, convert to a datetime format
  """
  date = []
  try:
    date = datetime.date(int(check_date[-4:]),int(check_date[-7:-5]),int(check_date[:2]))
    check = 'pass'
  except:
    check = 'fail'
  finally:
    return date, check

def load_symbol_dic():
  """
  Load a dictionary of all tickers symbols in the NSYE, NASDAQ and AMEX stock
  markets. {keys - values}  ==  {symbol - (company name,stock_type,sector,activity)}
  """
  directory = '/home/gilles/projects/trading/quant_trading/symbols'
  dic = {}
  for item in os.listdir(directory):
    with open(directory+'/'+item) as f:
      for line in f:
        if line.split(',')[0].replace('\"','') not in dic:
          info = line.split(',')
          if 'n/a' in info[6]:
            if 'ETF' in info[1]:
              stock_type = 'ETF'
            elif 'fund' in info[1].lower():
              stock_type = 'Fund'
            else:
              stock_type = 'unknown'
            dic[info[0].replace('\"','')] = (info[1].replace('\"','').lower(),stock_type,'n/a','n/a')
          else:
            dic[info[0].replace('\"','')] = (info[1].replace('\"','').lower(),'stock',info[7],info[8])
  return dic

def ADF_test(series,lag):
  """
  Outputs the result of the Augmented Dickey-Fuller test for the series.
  The series should be a pandas dataframe containing the adjusted close variable
  from yahoo finance.
  A typical value for the time lag is 1.
  Output Format: (test statistic, p-value,nbr of lags used,, nbr of observations used, dictionary of critical values)

  NOTES:
  - A negative output indicates the time series is not trending
  - The function returns a dictionary with the test statistic values at the 1%, 5%
    and 10% level. If the output is less negative than any of those, the series is NOT
    mean reverting, for those confidence levels (or rather, random walk can not be rejected).
  """
  return ts.adfuller(series['Adj Close'],lag)

def mean_reversion_half_life(series):
  """ 
  Determine the half life for mean reversion in case the ADF test outputs a negative lambda
  """
  y = (series['Adj Close'][2:].values - series['Adj Close'][1:-1].values)
  x = series['Adj Close'][1:-1].values
  alpha = linregress(x,y)
  return -(np.log(2)/np.log(10))/alpha[0]

def get_hurst(series,lag):
  """
  Estimate the Hurst exponent of the time series ts
  A good value for the lag is 100 (100 days)
  NOTES:
  - if 0.5 < H and H --> 1 : the series is trending
  - if H < 0.5 and H --> 0 : the series is mean reverting
  - if H < 0, white noise
  """
  lag = min(lag,len(series))-1
  lags = range(2,lag)

  #Calculate the array of the variances of the lagged differences
  tau = [np.sqrt(np.std(np.subtract(series[item:]['Adj Close'],series[:-item]['Adj Close']))) for item in lags]
  #Use linear fit to estimate the Hurst Exponent
  poly = np.polyfit(np.log(lags), np.log(tau),1)
  H = poly[0]*2.0
  return H

def variance_ratio_test(series,lag):
  """The ouputs are h and the p-value. h > 1 means the random walk hypothesis should be
     rejected, h < -1 it should be accepted. The closer to 0, the closer to a random
     walk te seri is. The p-value gives the probability that the
     random walk (null) hypothesis is true.
  """
  VR = arch.unitroot.VarianceRatio(series['Adj Close'],lag)
  return (VR.stat,VR.pvalue)

def cadf(s1,s2):
  """
  Cointegrated Augmented Dickey-Fuller test
  The first output is the test statistic, to compare with the dictionary of critical
  values at 1, 10 and 5 %
  """
  #Calculate optimal hedge ratio "beta"
  res = ols(y=s1['Adj Close'], x=s2['Adj Close'])
  beta_hr = res.beta.x

  #Calculate residuals of the linear combination
  residual = s1['Adj Close'] - s2['Adj Close']

  #calculate the CADF test on the residuals
  return ts.adfuller(residual), beta_hr

def momentum_autocorrelation(series,max_lag):
  """ calculate the """
  return