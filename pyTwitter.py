

import requests
import configparser

from http import HTTPStatus

config = configparser.ConfigParser()
config.read('config.ini')


class Twitter:
    def __init__(self):
        self._token_url = 'https://api.twitter.com/oauth2/token'
        self._server = 'https://api.twitter.com/1.1/'
        self._key = config['TWITTER']['Key']
        self._secret = config['TWITTER']['Secret']

    def __get_token__(self):
        res = requests.post(self._token_url,
                            auth=(self._key, self._secret),
                            data={'grant_type': 'client_credentials'},
                            verify=False)

        self.token = res.json()['access_token']

        self.headers = {'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + self.token}

    def search_tweets(self, q):
        self.__get_token__()
        url = '{server}search/tweets.json?q={q}'.format(server=self._server, q=q)
        response = requests.get(url, headers=self.headers, verify=False)
        if response.status_code != HTTPStatus.OK:
            raise Exception('Error while calling external service')

        response = response.json()
        # object to json => json.dumps(object)
        # json to object => json.loads(json)
        #print(response)
        return response




#     def test(self, a, b, c, d='d'):
#         print(a, b, c, d)
# Twitter().test('a', 'b', 'c')
# Twitter().test('a', 'b', 'c', 'dddd')
# Twitter().test(d=1, c=2, b=3, a=4)
# Twitter().test('a', d='d', b='b', c='c')
