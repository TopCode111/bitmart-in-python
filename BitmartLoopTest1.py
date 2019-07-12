from bitmart import *

api_key = "ee0291ef0214dcc0f10fb23b40e64e4b"
secret_key = "1ad36b1caaa4818498b2ebb0f7e42ea3"
title = '123'



bitmart = Bitmart(api_key, secret_key, title)


startingPrice = 0.00002
endingPrice = 0.00004
step = 0.0000002


price= startingPrice
messages = []
while price <= endingPrice :
    print(price,end='\r')
    message = bitmart.place_order('ZCO_ETH', 400, price, 'buy')
    if message not in messages :
        print(price, message)
        messages.append(message)
        
    price += step
    
print()
print ('Done')   
