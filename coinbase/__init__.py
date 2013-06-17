"""
Coinbase Python Client Library

AUTHOR

George Sibble
Github:  sibblegp

LICENSE (The MIT License)

Copyright (c) 2013 George Sibble "gsibble@gmail.com"

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

__author__ = 'gsibble'

from oauth2client.client import AccessTokenRefreshError, OAuth2Credentials, AccessTokenCredentialsError

import requests
import httplib2
import json

#TODO: Switch to decimals from floats
#from decimal import Decimal

from coinbase.config import COINBASE_ENDPOINT
from coinbase.models import CoinbaseAmount, CoinbaseTransaction, CoinbaseUser


class CoinbaseAccount(object):
    """
    Primary object for interacting with a Coinbase account

    You may either use oauth credentials or a classic API key
    """

    def __init__(self,
                 oauth2_credentials=None,
                 api_key=None):
        """

        :param oauth2_credentials: JSON representation of Coinbase oauth2 credentials
        :param api_key:  Coinbase API key
        """

        #Set up our requests session
        self.session = requests.session()

        #Set our Content-Type
        self.session.headers.update({'content-type': 'application/json'})

        if oauth2_credentials:

            #Set CA certificates (breaks without them)
            self.http = httplib2.Http(ca_certs='ca-certs.txt')

            #Create our credentials from the JSON sent
            self.oauth2_credentials = OAuth2Credentials.from_json(oauth2_credentials)

            #Check our token
            self._check_oauth_expired()

            #Apply our oAuth credentials to the session
            self.oauth2_credentials.apply(headers=self.session.headers)

            #Set our request parameters to be empty
            self.global_request_params = {}

        elif api_key:
            if type(api_key) is str:

                #Set our API Key
                self.api_key = api_key

                #Set our global_request_params
                self.global_request_params = {'api_key':api_key}
            else:
                print "Your api_key must be a string"
        else:
            print "You must pass either an api_key or oauth_credentials"

    def _check_oauth_expired(self):
        """
        Internal function to check if the oauth2 credentials are expired
        """

        #Check if they are expired
        if self.oauth2_credentials.access_token_expired == True:

            #Print an notification message if they are
            print 'oAuth2 Token Expired'

            #Raise the appropriate error
            raise AccessTokenCredentialsError

    def refresh_oauth(self):
        """
        Refresh our oauth2 token
        :return: JSON representation of oauth token
        :raise: AccessTokenRefreshError if there was an error refreshing the token
        """

        #See if we can refresh the token
        try:
            #Ask to refresh the token
            self.oauth2_credentials.refresh(http=self.http)

            #We were successful
            print 'Your token was refreshed with the following response...'

            #Return the token for storage
            return self.oauth2_credentials.to_json()

        #If the refresh token was invalid
        except AccessTokenRefreshError:

            #Print a warning
            print 'Your refresh token is invalid'

            #Raise the appropriate error
            raise AccessTokenRefreshError

    def _prepare_request(self):
        """
        Prepare our request in various ways
        """

        #Check if the oauth token is expired and refresh it if necessary
        self._check_oauth_expired()

    @property
    def balance(self):
        """
        Retrieve coinbase's account balance

        :return: CoinbaseAmount (float) with currency attribute
        """

        url = COINBASE_ENDPOINT + '/account/balance'
        response = self.session.get(url, params=self.global_request_params)
        results = response.json()
        return CoinbaseAmount(results['amount'], results['currency'])

    @property
    def receive_address(self):
        """
        Get the account's current receive address

        :return: String address of account
        """
        url = COINBASE_ENDPOINT + '/account/receive_address'
        response = self.session.get(url, params=self.global_request_params)
        return response.json()['address']

    @property
    def contacts(self):
        """
        Get the account's contacts

        :return: List of contacts in the account
        """
        url = COINBASE_ENDPOINT + '/contacts'
        response = self.session.get(url, params=self.global_request_params)
        return [contact['contact'] for contact in response.json()['contacts']]

    def buy_price(self, qty=1):
        """
        Return the buy price of BitCoin in USD
        :param qty: Quantity of BitCoin to price
        :return: CoinbaseAmount (float) with currency attribute
        """
        url = COINBASE_ENDPOINT + '/prices/buy'
        params = {'qty': qty}
        params.update(self.global_request_params)
        response = self.session.get(url, params=params)
        results = response.json()
        return CoinbaseAmount(results['amount'], results['currency'])

    def sell_price(self, qty=1):
        """
        Return the sell price of BitCoin in USD
        :param qty: Quantity of BitCoin to price
        :return: CoinbaseAmount (float) with currency attribute
        """
        url = COINBASE_ENDPOINT + '/prices/sell'
        params = {'qty': qty}
        params.update(self.global_request_params)
        response = self.session.get(url, params=params)
        results = response.json()
        return CoinbaseAmount(results['amount'], results['currency'])

    # @property
    # def user(self):
    #     url = COINBASE_ENDPOINT + '/account/receive_address'
    #     response = self.session.get(url)
    #     return response.json()

    def request(self, from_email, amount, notes='', currency='BTC'):
        """
        Request BitCoin from an email address to be delivered to this account
        :param from_email: Email from which to request BTC
        :param amount: Amount to request in assigned currency
        :param notes: Notes to include with the request
        :param currency: Currency of the request
        :return: CoinbaseTransaction with status and details
        """
        url = COINBASE_ENDPOINT + '/transactions/request_money'

        if currency == 'BTC':
            request_data = {
                "transaction": {
                    "from": from_email,
                    "amount": amount,
                    "notes": notes
                }
            }
        else:
            request_data = {
                "transaction": {
                    "from": from_email,
                    "amount_string": str(amount),
                    "amount_currency_iso": currency,
                    "notes": notes
                }
            }

        response = self.session.post(url=url, data=json.dumps(request_data), params=self.global_request_params)
        response_parsed = response.json()
        if response_parsed['success'] == False:
            pass
            #DO ERROR HANDLING and raise something

        return CoinbaseTransaction(response_parsed['transaction'])

    def send(self, to_address, amount, notes='', currency='BTC'):
        """
        Send BitCoin from this account to either an email address or a BTC address
        :param to_address: Email or BTC address to where coin should be sent
        :param amount: Amount of currency to send
        :param notes: Notes to be included with transaction
        :param currency: Currency to send
        :return: CoinbaseTransaction with status and details
        """
        url = COINBASE_ENDPOINT + '/transactions/send_money'

        if currency == 'BTC':
            request_data = {
                "transaction": {
                    "to": to_address,
                    "amount": amount,
                    "notes": notes
                }
            }
        else:

            request_data = {
                "transaction": {
                    "to": to_address,
                    "amount_string": str(amount),
                    "amount_currency_iso": currency,
                    "notes": notes
                }
            }

        response = self.session.post(url=url, data=json.dumps(request_data), params=self.global_request_params)
        response_parsed = response.json()

        if response_parsed['success'] == False:
            print response_parsed
            raise ValueError, "asd"
            #TODO:  DO ERROR HANDLING and raise something

        return CoinbaseTransaction(response_parsed['transaction'])


    def transactions(self, count=30):
        """
        Retrieve the list of transactions for the current account
        :param count: How many transactions to retrieve
        :return: List of CoinbaseTransaction objects
        """
        url = COINBASE_ENDPOINT + '/transactions'
        pages = count / 30 + 1
        transactions = []

        reached_final_page = False

        for page in xrange(1, pages + 1):

            if not reached_final_page:
                params = {'page': page}
                params.update(self.global_request_params)
                response = self.session.get(url=url, params=params)
                parsed_transactions = response.json()

                if parsed_transactions['num_pages'] == page:
                    reached_final_page = True

                for transaction in parsed_transactions['transactions']:
                    transactions.append(CoinbaseTransaction(transaction['transaction']))

        return transactions

    def get_transaction(self, transaction_id):
        """
        Retrieve a transaction's details
        :param transaction_id: Unique transaction identifier
        :return: CoinbaseTransaction object with transaction details
        """
        url = COINBASE_ENDPOINT + '/transactions/' + str(transaction_id)
        response = self.session.get(url, params=self.global_request_params)
        results = response.json()

        if results.get('success', True) == False:
            pass
            #TODO:  Add error handling

        return CoinbaseTransaction(results['transaction'])

    def get_user_details(self):
        """
        Retrieve the current user's details

        :return: CoinbaseUser object with user details
        """
        url = COINBASE_ENDPOINT + '/users'
        response = self.session.get(url, params=self.global_request_params)
        results = response.json()

        user_details = results['users'][0]['user']

        #Convert our balance and limits to proper amounts
        balance = CoinbaseAmount(user_details['balance']['amount'], user_details['balance']['currency'])
        buy_limit = CoinbaseAmount(user_details['buy_limit']['amount'], user_details['buy_limit']['currency'])
        sell_limit = CoinbaseAmount(user_details['sell_limit']['amount'], user_details['sell_limit']['currency'])

        user = CoinbaseUser(user_id=user_details['id'],
                            name=user_details['name'],
                            email=user_details['email'],
                            time_zone=user_details['time_zone'],
                            native_currency=user_details['native_currency'],
                            balance=balance,
                            buy_level=user_details['buy_level'],
                            sell_level=user_details['sell_level'],
                            buy_limit=buy_limit,
                            sell_limit=sell_limit)

        return user

    def generate_receive_address(self, callback_url=None):
        """
        Generate a new receive address
        :param callback_url: The URL to receive instant payment notifications
        :return: The new string address
        """
        url = COINBASE_ENDPOINT + '/account/generate_receive_address'
        request_data = {
            "address": {
                "callback_url": callback_url
            }
        }
        response = self.session.post(url=url, data=json.dumps(request_data), params=self.global_request_params)
        return response.json()