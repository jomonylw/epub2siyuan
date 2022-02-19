# coding=utf-8

import requests
import urllib3
from urllib3 import encode_multipart_formdata

from .settings import ADAPTER_WITH_RETRY
from .urls import LS_NOTEBOOKS_URL, EX_COPY_URL, CREATE_NOTE_URL, UPLOAD_URL, CREATE_NOTEBOOK_URL


class Client:

    def __init__(self, url, token):
        self._session = requests.session()
        self._root_url = url
        self._token = token

        # remove SSL Verify
        self._session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Add auto retry for session
        self._session.mount('http://', ADAPTER_WITH_RETRY)
        self._session.mount('https://', ADAPTER_WITH_RETRY)
        self._headers = {'Authorization': 'Token ' + self._token, 'Content-Type': 'application/json'}

    def request(self, url, params={}, data={}, json={}, headers={}):
        if headers == {}:
            headers = self._headers

        res = self._session.post(url=self._root_url + url, params=params, data=data, json=json, headers=headers)

        print('url -> ', res.url, res.status_code)
        # print(res.content)
        if res.status_code == 200:
            return res.json()
        else:
            return {'code': -1, 'msg': 'error', 'data': {}}

    def ls_notebooks(self):
        return self.request(url=LS_NOTEBOOKS_URL)

    def create_notebook(self, notebook_name):

        data = {'name': notebook_name}
        return self.request(url=CREATE_NOTEBOOK_URL, json=data)

    def ex_copy(self, dom, notebook):
        data = {'dom': dom,
                'notebook': notebook}
        encode_data = encode_multipart_formdata(data)
        headers = {'Authorization': 'Token ' + self._token, 'Content-Type': encode_data[1]}
        return self.request(url=EX_COPY_URL, data=encode_data[0], headers=headers)

    def create_note(self, notebook, path, markdown):
        data = {'path': path, 'notebook': notebook, 'markdown': markdown}
        return self.request(url=CREATE_NOTE_URL, json=data)

    def upload(self, notebook, file, path='/assets'):
        data = {'assetsDirPath': notebook + path}

        if 'data' in file and file['data']:
            file_data = (file['name'], file['data'])
            data.update({'file[]': file_data})
        else:
            with open(file['path'], 'rb') as f:
                file_data = (file['name'], f.read())
                data.update({'file[]': file_data})

        encode_data = encode_multipart_formdata(data)
        headers = {'Authorization': 'Token ' + self._token, 'Content-Type': encode_data[1]}
        return self.request(url=UPLOAD_URL, data=encode_data[0], headers=headers)
