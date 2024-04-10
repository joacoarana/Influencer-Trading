import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

import time
import re
import math
from binance import Client
import requests

#%%

class TwitterBot:
    def __init__(self, api_key, api_key_secret, usuario1, password1, usuario2, password2):
        self.api_key = api_key
        self.api_key_secret = api_key_secret
        self.usuario1 = usuario1
        self.usuario2 = usuario2
        self.password1 = password1
        self.password2 = password2
        self.usuario = self.usuario1
        self.password = self.password1
        self.last_tweet = 0
        self.api_url = ""
        self.driver = None
        self.HOSTNAME = 'us.smartproxy.com'                                                       #Proxy host:port configuration
        self.PORT = '10000'
        self.DRIVER = 'CHROME'   

    def get_ticker(self, string):
        pattern = r'\$([A-Za-z]{1,5})'
        matches = re.findall(pattern, string)

        if matches:
            tickers = [match.upper() for match in matches]
            return True, tickers
        else:
            return False, None

    def calculate_symbol_precision(self, symbol_filters):
        step_size = 0.0
        for symbol_filter in symbol_filters:
            if symbol_filter['filterType'] == 'LOT_SIZE':
                step_size = float(symbol_filter['stepSize'])
                break
        precision = int(round(-math.log(step_size, 10), 0))
        return precision

    def process_futures_info(self, futures_exchange_info):
        simple_info = {symbol['symbol']: {'precision':self.calculate_symbol_precision(symbol['filters'])} for symbol in futures_exchange_info['symbols'] if symbol['symbol'][-4:] == 'USDT' }
        return simple_info
    
    def get_precision(self, info):
        precision_dict = {}
        for pair in info['symbols']:
            asset = pair['symbol']
            quantity_precision = pair['quantityPrecision']
            price_precision = pair['pricePrecision']
            precision_dict[asset]={'pricePrecision': price_precision, 'quantityPrecision': quantity_precision }

        return precision_dict
    
    def change_user(self):
        if self.usuario == self.usuario1:
            self.usuario = self.usuario2
            self.password = self.password2
        elif self.usuario == self.usuario2:
            self.usuario = self.usuario1
            self.password = self.password1
    
    def driver_init(self):
        #if self.requests_counter >= 10:
            #self.proxy_index = (self.proxy_index + 1) % len(self.proxy_list)
            #uc.install()
            chrome_options = uc.ChromeOptions()
            # proxy_str = '{hostname}:{port}'.format(hostname=self.HOSTNAME, port=self.PORT)
            #chrome_options.add_argument('--proxy-server={}'.format(proxy_str))
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            #chrome_options.add_argument(f"--proxy-server={self.proxy_list[self.proxy_index]}")
            self.driver = uc.Chrome(options=chrome_options)
            #self.requests_counter = 0


    def run_bot(self):
        self.driver_init()
        driver = self.driver
        wait = WebDriverWait(driver, timeout=15)
        driver.get("https://twitter.com/i/flow/login")
        time.sleep(5)
        a = driver.find_element(By.XPATH, "//input")
        a.click()
        a.send_keys(self.usuario)
        time.sleep(1)
        siguiente = driver.find_element(By.XPATH, "//span[contains(text(), 'Siguiente')]")
        siguiente.click()
        time.sleep(3)
        driver.switch_to.active_element.send_keys(self.password)  # CONTRASENA
        time.sleep(3)
        entrar = driver.find_element(By.XPATH, "//span[contains(text(), 'Iniciar sesión')]")
        entrar.click()
        time.sleep(10)

        last_tweet = 0
        i = 0
        
        waiting = 0
        while True:
            i += 1
            print(i)
            try:
                # if i%5 ==0:
                #     driver.get("https://httpbin.org/ip")
                #     print(driver.find_element(By.TAG_NAME, "body").text)
                driver.get("https://twitter.com/CryptoWizardd")
                time.sleep(5)
                nn = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]'))
                    )
                n = nn[0]
                n_soup = BeautifulSoup(n.get_attribute('innerHTML'), 'html.parser')
                tweet_text_element = n_soup.find('div', {'data-testid': 'tweetText'})
                username_element = n_soup.find('div', {'data-testid': 'User-Name'})
                username_text = username_element.get_text(strip=True)
            except:
                print ("IP RATE LIMITED")
                #time.sleep(10)
                last_tweet = 0              
                # driver.quit()
                # self.change_user()
                # self.run_bot() #RESTART
                continue

            tweet_text = ''
            for element in tweet_text_element.children:
                if element.name == 'a':
                    tweet_text += f"{element.get_text(strip=True)} "
                elif element.name == 'span':
                    tweet_text += f"{element.get_text(strip=True)} "

            print(tweet_text)
            #waiting = 0
            if tweet_text == last_tweet or last_tweet == 0 or "@CryptoWizardd" not in username_text:
                last_tweet = tweet_text
                pass
            else:
                found, many_tickers = self.get_ticker(tweet_text)

                last_tweet = tweet_text
                if found:
                    ticker = many_tickers[0]
                    print(f"TRADE FOUND: {ticker}")
                    
                    stop_loss= None
                    take_profit = None
                    quantities = {}
                    symbol = ticker + 'USDT'
                    client = Client(api_key=self.api_key, api_secret=self.api_key_secret, testnet=False)
                    time.sleep(0.1)
                    info = client.futures_exchange_info()
                    precision  = self.get_precision(info)
                    time.sleep(0.1)
                    balance = client.futures_account_balance()
                    balance_USDT = int(float(balance[5]['availableBalance']) - 5)
                    time.sleep(0.1)
                    try:                      
                        price_request = client.futures_symbol_ticker(symbol=symbol)
                    except:
                        continue
                    price_symbol = float(price_request['price'])
                    quantity_precision = precision[symbol]['quantityPrecision'] if symbol in precision else None  # Default precision if not found
                    quantity = math.floor(balance_USDT / price_symbol * 10 ** quantity_precision) / 10 ** quantity_precision

                    time.sleep(0.1)
                    leverage_petition = client.futures_change_leverage(symbol=symbol, leverage=20)
                    leverage = leverage_petition['leverage']
                    time.sleep(0.1)
                    try:
                        print(symbol, quantity*leverage, "BUY")
                        market_order = client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=quantity * leverage)
                        print(f"MARKET ORDER FOR : {symbol} at {price_symbol}")
                        time.sleep(1)
                        try:
                            price_precision = precision[symbol]['pricePrecision'] if symbol in precision else None  # Default precision if not found
                            stop_price = math.floor(price_symbol*0.99 * 10 ** price_precision) / 10 ** price_precision
                            #stop loss order
                            stop_loss=client.futures_create_order(symbol=symbol,side='SELL',type='STOP_MARKET',stopPrice= stop_price, closePosition='true')            
                            #take profit order                       
                            print(f"SL ORDER FOR : {symbol}")
                            take_price = math.floor(price_symbol*1.005 * 10 ** price_precision) / 10 ** price_precision
                            
                            take_profit=client.futures_create_order(symbol=symbol,side='SELL',type='TAKE_PROFIT_MARKET',stopPrice= take_price,closePosition='true') 
                            print(f"TP ORDER FOR : {symbol}")
                            quantities[f'{symbol}'] = quantity * leverage
                        except:
                            if stop_loss is None:    
                                end_trade = client.futures_create_order(symbol=symbol,side='SELL',type='MARKET', quantity = quantity*leverage)
                                print(f"END TRADE 1 FOR : {symbol}")
                                cancel_symbol_orders = client.futures_cancel_all_open_orders(symbol=symbol)
                                print(f"CANCEL ORDERS 1 FOR : {symbol}")
                            elif take_profit is None:
                                orders = client.futures_get_open_orders(symbol=symbol)
                                if len(orders) == 1:
                                    cancel_symbol_orders = client.futures_cancel_all_open_orders(symbol=symbol)
                                    print(f"CANCEL ORDERS 1 FOR : {symbol}")
                                    end_trade = client.futures_create_order(symbol=symbol,side='SELL',type='MARKET', quantity = quantity*leverage)
                                    print(f"END TRADE 1 FOR : {symbol}")
                                elif len(orders) == 0:
                                    pass
                    except:
                        last_tweet = tweet_text
                        continue
                    
                    for _ in range (6):
                        time.sleep(10)
                        try:
                            orders = client.futures_get_open_orders(symbol=symbol)
                            print(f'Number of orders is {len (orders)}')
                            if len (orders) == 2:
                                pass
                            elif len (orders) == 1:
                                cancel_symbol_orders = client.futures_cancel_all_open_orders(symbol=symbol)
                        except:
                            print(f'Cannot get Orders: {_}')
                            pass

                    time.sleep(3)
                    trades = client.futures_account_trades()
                    last_trade = trades[-1]
                    orders = client.futures_get_open_orders(symbol=symbol)
                    if len(orders) == 2 and last_trade['side'] == 'BUY':
                        cancel_symbol_orders = client.futures_cancel_all_open_orders(symbol=symbol)
                        print(f"CANCEL ORDERS 2 FOR : {symbol}")
                        end_trade = client.futures_create_order(symbol=symbol,side='SELL',type='MARKET', quantity = quantities[symbol])
                        print(f"END TRADE 2 FOR : {symbol}")
                    else:
                        cancel_symbol_orders = client.futures_cancel_all_open_orders(symbol=symbol)
                        print(f"CANCEL ORDERS 3 FOR : {symbol}")
                        
                    data = {
                        "chat_id": "@joaco_arbi",
                        "text": f"TRADE FOUND FOR: {symbol} at {price_symbol} ",
                        "parse_mode": "Markdown"
                    }
                    response = requests.post(self.api_url, data=data)

                    last_tweet = 0
            
            time.sleep(5)                           
            


#%%
if __name__ == "__main__":
    api_key = ''  # Replace with your Binance API key
    api_key_secret = ''  # Replace with your Binance API key secret
    twitter_bot = TwitterBot(api_key, api_key_secret, '', '', "", "") #Users and passwords
    twitter_bot.run_bot()
