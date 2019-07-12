#!/usr/bin/env python3
import sys
sys.path.append('/damg/skynet/exchanges')
from bitmart import *
import creds
import json
import time
from subprocess import call
import datetime
import pytz
import decimal
import threading
from random import *
import sched
import requests
from pprint import pprint
import re
import os
import argparse
import requests

#---------------------------------------------
# PARSER ARGS
#---------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument('-s','--side', help='buy(2) or sell(1)', required=True)
parser.add_argument('-p','--price', help='desired trade price(in sat)', required=True)
parser.add_argument('-m','--pair', help='which pair to trade(def: RITETH)', required=True)
parser.add_argument('-q','--size', help='size/qunatity to trade(def: 1)', required=True)

args = parser.parse_args()

side  = args.side
price = args.price
pair  = args.pair
size  = args.size
#----------------------------------------------
# API AUTHENTICATION
#----------------------------------------------
#api_key = creds.api.bitmart()['api_key_1']
api_key = "ee0291ef0214dcc0f10fb23b40e64e4b"
secret_key = "1ad36b1caaa4818498b2ebb0f7e42ea3"
#secret_key = creds.api.bitmart()['api_secret_1']
title = '123'
#---------------------------------------------
# CONSTRUCTORS
#---------------------------------------------
enum = {'ETH':1,'ZCO':121}
bitmart = Bitmart(api_key,secret_key,title)


def depth():

   depth                  = bitmart.orderbook(pair,8)

   ask_pair_eth           = float(depth['sells'][0]['price'])
   bid_pair_eth           = float(depth['buys'][0]['price'])

   ask_size_pair_eth      = float(depth['sells'][0]['amount'])
   bid_size_pair_eth      = float(depth['buys'][0]['amount'])
   return{'depth':depth,'ask':ask_pair_eth,'bid':bid_pair_eth,0:ask_size_pair_eth,1:bid_size_pair_eth}


def spread():
    spread   = round(denominator * (float(depth['ask']) - float(depth['bid'])),0)
    return {'spread': spread }

def fetchTicker():
    #bid_1 ask_1
    fetch_ticker_pair = bitmart.ticker(pair)
    bid_zco_eth       = fetch_ticker_pair['bid_1']
    ask_zco_eth       = fetch_ticker_pair['ask_1']
    last_zco_eth      = fetch_ticker_pair['current_price']

    return {'bid_eth':bid_zco_eth,'ask_eth':ask_zco_eth,'last_eth':last_zco_eth}

if __name__ == '__main__':

  #seconds_to_wait   = randrange(2, 46)
  seconds_to_wait   = randrange(0,2)
  buy_or_sell_first = randrange(0, 16)

  localtime = time.asctime( time.localtime(time.time()) )
  print('Local current time:',localtime,'CDT\n')

  print('Waiting',seconds_to_wait,'seconds')
  time.sleep( seconds_to_wait )

  localtime = time.asctime( time.localtime(time.time()) )
  print('Local current time:',localtime,'CDT\n')

  #
  mult            = 1.2875 * 0.43952
  #GPM
  gwei_adjust     = 0
  #formatting
  round_decimal   = 8
  denominator     = 10.0 ** round_decimal
  denom_inverse   = 1.0 / denominator
  fmt   = '{0:.8f}'
  minute = datetime.datetime.now().minute

  #MR
  buy_below       = 2600 / denominator
  sell_above      = 3000 / denominator
  large_size      = round(randint(400,500))
  medium_size     = round(randint(300,360))
  small_size      = round(randint(230,320))
  very_small_size = round(randint(220,300))
  locked_spread   = 1

  #GVM
  size_mult       = 1.34 * 2.0 * 0.43952


  #Short hand Variables
  depth   = depth()
  spread  = spread()
  ft      = fetchTicker()
  print('-' * 80)

  print('-' * 80)
  print('large_size =',large_size)
  print('medium_size =',medium_size)
  print('small_size =',small_size)
  print('very_small_size =',very_small_size)
  print('-' * 20)
  print('MR')
  print('buy_below =',fmt.format(buy_below))
  print('sell_above =',fmt.format(sell_above))
  print('-' * 20)
  print('locked_spread =',locked_spread)
  print('round_decimal =',round_decimal)
  print('denominator =',denominator)
  print('denom_inverse =',fmt.format(denom_inverse))
  print('-' * 80)
  print ('Adjusting by',gwei_adjust,'gwei from',fmt.format(float(price)),'to',fmt.format(float(price) + denom_inverse *gwei_adjust) )
  price         = float(price) + denom_inverse * gwei_adjust


  print('-' * 80)
  localtime = time.asctime( time.localtime(time.time()) )
  print('Local current time:',localtime,'CDT\n')

  if spread['spread'] <= locked_spread: # if zco-btc  spread is locked
    print (pair,'spread is locked!')
    if depth['ask'] <= buy_below: # if zco-eth is trading at levels where we'd prefer to buy
      print (pair,'is in buying territory!')
      print ("Lift the best offer for small size (limit price = our medium offer)...")
      lift_offer = bitmart.place_order(pair,small_size,depth['ask'],'buy')
      print ("Cancel all three orders...")
      cancel_lift_offer  = bitmart.cancel_order(lift_offer['entrust_id'])
      pprint("ATTN: cancel lift offer Exception [the order probably executed successfully]")
    elif depth['bid'] >= sell_above: # if ZCO-BTC is trading at levels where we'd prefer to sell
      print (pair,'is in selling territory!')
      print ("Hit the best bid for small size (limit price = our medium bid)...")
      hit_bid = bitmart.place_order(pair,small_size,depth['bid'],'sell')
      cancel_hit_bid  = bitmart.cancel_order(hit_bid['entrust_id'])
      pprint("ATTN: cancel hit bid Exception [the order probably executed successfully]")
    else: # if ZCO-ETH is in a neutral zone where we don't have a buy or sell preferences
      print (pair,'is in neutral territory!')
      if price >= depth['ask']: # if we are scheduled to buy above the current ask, buy very small
         print ("Lift the best offer for very small size (limit price = our medium offer)...")
         lift_offer = bitmart.place_order(pair,very_small_size,depth['ask'],'buy')
         cancel_lift_offer  = bitmart.cancel_order(lift_offer['entrust_id'])
         pprint("ATTN: cancel lift offer Exception [the order probably executed successfully]")
      elif price <= depth['bid']: # if we are scheduled to sell below the current bid, sell very small
           print ("Hit the best bid for very small size (limit price = our medium bid)...")
           hit_bid = bitmart.place_order(pair,very_small_size,depth['bid'],'sell')
           cancel_hit_bid  = bitmart.cancel_order(hit_bid['entrust_id'])
           pprint("Great Canceled hit bid")
           pprint("ATTN: cancel hit bid Exception [the order probably executed successfully]")
      else: # impossible outcome
        print ("How did I get here???")
        print ("Cancel all three orders...")
  else: # otherwise, just do what we've been doing this whole time
    size = float(size) * size_mult
    #print('size * size_mult<',size_mult,'> =',size)
    do_buy  = 1
    do_sell = 1
    if depth['ask'] <= price:
      if depth[0] > 10:
        print ("SMART PRICE ADJUSTMENT!")
        prev_price = price
        price   = round(depth['ask'] - denom_inverse,round_decimal)
        print ('price [',fmt.format(prev_price),'->',fmt.format(price),']')
      else:
        print ("SMARTER PRICE ADJUSTMENT!")
        prev_size = size
        n = 1
        for x in range( int(denominator * depth['ask']), int(denominator * price) ):
          depth[0] = min(230,depth[0] + float(depth['depth']['asks'][n][1]))
          n += 1
        size = depth[0]
        do_sell = 0
        print ('size [',prev_size,'->',size,']')
    elif depth['bid'] >= price:
      if depth[1] > 10:
        print ("SMART PRICE ADJUSTMENT!")
        prev_price = price
        price   = round(depth['bid'] + denom_inverse,round_decimal)
        print ('price [',fmt.format(prev_price),'->',fmt.format(price),']')
      else:
        print ("SMARTER PRICE ADJUSTMENT!")
        prev_size = size
        n = 1
        for x in range( int(denominator * price),int(denominator * depth['bid']) ):
          depth[1] = min(230,depth[1] + float(depth['depth']['bids'][n][1]))
          n += 1
        size = depth[1]
        do_buy  = 0
        print ('size [',prev_size,'->',size,']')
    print('Fire away!')
    if buy_or_sell_first > 8:
      print('Will buy first, then sell')
      if do_buy == 1:
        buy_zco_eth = bitmart.place_order(pair,size,price,'buy')
        print(buy_zco_eth)
      if do_sell == 1:
        sell_zco_eth = bitmart.place_order(pair,size,price,'sell')
        print(sell_zco_eth)
    else:
      print('Will sell first, then buy')
      if do_sell == 1:
        sell_zco_eth = bitmart.place_order(pair,size,price,'sell')
        print(sell_zco_eth)
      if do_buy == 1:
        buy_zco_eth = bitmart.place_order(pair,size,price,'buy')
        print(buy_zco_eth)
    print(bitmart)
    if do_buy == 1:
      #cancel_buy_order  = bitmart.cancel_order(buy_zco_eth['entrust_id'])
      #print(cancel_buy_order)
      pprint("canceled the  buy order ")
    if do_sell == 1:
      #cancel_sell_order  = bitmart.cancel_order(sell_zco_eth['entrust_id'])
      #print(cancel_sell_order)

      pprint("Canceling the  sell order")





exit()
