from rest_framework.test import APILiveServerTestCase
from chisubmit import client
    
class ChisubmitClientLibsTestCase(APILiveServerTestCase):
        
    def get_api_client(self, api_token, password=None, deferred_save = False):
        base_url = self.live_server_url + "/api/v1"
        
        return client.Chisubmit(login_or_token=api_token, password=password, base_url=base_url, deferred_save=deferred_save)  