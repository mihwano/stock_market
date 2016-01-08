import os
import sys
import shutil
import pdb
import sqlite3
from stock_class import stock
import pandas as pd
import stock_helper

"""
Helper functions to download stock market data from yahoo finance API and store it into
a sqlite database.

The database contain one relation per ticker symbol. The columns in the relation
are "open", "high", "low", "close", "volume", "adj close"
"""

def connection():
  """
  connect to the database on disk and creates the cursor object
  """
  # "Connect" to the database
  db = sqlite3.connect('/home/gilles/projects/trading/quant_trading/database/market.db')
  # Create a "cursor" object that will pass the SQL statements and execute them
  cur = db.cursor()  
  return db,cur

def update_summary_table(symbol):
  """
  If information about the symbol is not known yet (stock_type, sector, industry/activity),
  create a new entry in the summary table
  """
  try:
    if not cur:
      db,cur = connection()
  except:
    db,cur = connection()

  dic = stock_helper.load_symbol_dic()
  info = dic[symbol]

  cur.execute('INSERT OR IGNORE INTO SUMMARY(Symbol,Name,Type,Sector,Industry) VALUES(?,?,?,?,?)', (symbol,info[0],info[1],info[2],info[3]))
  db.commit()
  db.close()
  return  

def create_table(symbol):
  """
  If the historical table for the stock does not exist, create it
  """
  try:
    if not cur:
      db,cur = connection()
  except:
    db,cur = connection()

  cur.execute('CREATE TABLE %s(date TEXT PRIMARY KEY, Open REAL, High REAL, Low REAL, Close REAL, Volume INTEGER, Adj_Close REAL)' %symbol)
  # Commit the changes
  db.commit()
  return
  
def update_data(stk):
  """ 
  Update the database with historical data (only update for entries
  that do not currently exist
  """
  try:
    if not cur:
      db,cur = connection()
  except:
    db,cur = connection()

  symbol = stk._symbol
  start = stk._start
  end = stk._end

  data = stk._historical   #remember to retrieve historical data before calling the function

  # Check if the table for the symbol already exists in the database
  cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="%s"' %symbol)
  table = cur.fetchall()
  if not table:
    try:
      create_table(symbol)
    except:
      # update relative to previous date?
      return

  for i in xrange(len(data)):
    date = pd.to_datetime(str(data.index.values[i])).strftime('%Y.%m.%d')
    values = data.iloc[i]
    cur.execute('INSERT OR IGNORE INTO %s(date,Open,High,Low,Close,Volume,Adj_Close) VALUES(?,?,?,?,?,?,?)' %symbol, (date,values[0],values[1],values[2],values[3],values[4],values[5]))
    db.commit()
  db.close()
  return

def full_download(start):
  """
  Download all the data from yahoo.finance from start to today
  (takes several days)
  """
  symbols = stock_helper.load_symbol_dic()

  con = sqlite3.connect('/home/gilles/projects/trading/quant_trading/database/market.db')
  cur = con.cursor()
  cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
  tables = cur.fetchall()

  for key in symbols.keys():
    if '^' in key or '/' in key:
      del symbols[key]
      continue
#    if (key,) in tables:
#      cur.execute('SELECT COUNT(*) FROM %s' %key)
#      entries = cur.fetchall()
#      pdb.set_trace()
#      if entries[0][0] > 0:
#        del symbols[key]
  print len(symbols)

#  sys.exit()
  for item in symbols:
    stk = stock(item,start)
    try:
      stk.get_historical()
    except:
      continue

    try:
      update_summary_table(stk._symbol)
      update_data(stk)
    except:
      continue
    print '%s completed' %stk._symbol
  return

def regular_download(start=None):
  """
  Download last month of data for all symbols, to update the database regularly
  """
  symbols = stock_helper.load_symbol_dic()
  
  for item in symbols:
    if start == None:
      stk = stock(item)
    else:
      stk = stock(item,start)
    try:
      stk.get_historical()
      update_summary_table(stk._symbol)
      update_data(stk)
      print 'updated %s' %item
    except:
      continue
  return

def extract_series(symbol):
  """
  Get the stock data between start and end from the sqlite database
  """
  try:
    if not cur:
      db,cur = connection()
  except:
    db,cur = connection()

  cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="%s"' %symbol)
  table = cur.fetchall()
  if not table:
    print '%s is not in the database' %symbol
    return
  else:
    cur.execute('SELECT * FROM %s' %symbol)
    return cur.fetchall()

