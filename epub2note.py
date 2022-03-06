import time

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

from settings import SIYUAN_TOKEN, SIYUAN_URL, REPLACE_STR
from siyuan.client import Client


class Epub2note:

    def __init__(self, notebook_name):
        self._sy_client = Client(url=SIYUAN_URL, token=SIYUAN_TOKEN)
        self._imgs_map = {}
        self._toc_list = []
        self._toc_data = []
        self._doc_list = []
        self._book = None
        self._book_name = None
        self._notebook_id = self._get_notebook_id(notebook_name=notebook_name)

    def _upload_imgs(self):

        if not self._book:
            raise Exception

        self._imgs_map = {}
        print('upload imgs ...')
        for item in self._book.get_items():
            if item.get_type() == ebooklib.ITEM_IMAGE or item.get_type() == ebooklib.ITEM_COVER:
                img_name = item.get_name().split('/')[-1]
                res = self._sy_client.upload(notebook=self._notebook_id,
                                             file={'name': img_name, 'data': item.get_content()})
                self._imgs_map.update(res['data']['succMap'])

    def _get_notebook_id(self, notebook_name):

        self._notebook_id = ''
        res = self._sy_client.ls_notebooks()
        if 'data' in res:
            for item in res['data']['notebooks']:
                if item['name'] == notebook_name:
                    return item['id']
            # create notebook
            res = self._sy_client.create_notebook(notebook_name=notebook_name)
            if 'code' in res and res['code'] == 0:
                return res['data']['notebook']['id']
            else:
                raise Exception
        else:
            raise Exception

    def _add_toc_data(self, lvl, title, href):

        if '#' in href:
            href_list = href.split('#')
            href_link = href_list[0]
        else:
            href_link = href

        self._toc_data.append({'lvl': lvl, 'title': title, 'href': href_link})

    def _get_toc_data(self, toc, lvl):

        if not toc:
            raise Exception

        for item in toc:
            if isinstance(item, tuple):
                if len(item) > 1:
                    temp = item[0]
                    self._add_toc_data(lvl=lvl, title=temp.title, href=temp.href)
                    if isinstance(item[1], list):
                        self._get_toc_data(item[1], lvl=lvl + 1)
            else:
                temp = item
                self._add_toc_data(lvl=lvl, title=temp.title, href=temp.href)

    def _gen_toc_list(self):

        if not self._book:
            raise Exception

        if not self._book.toc:
            raise Exception

        self._toc_data = []
        self._toc_list = []

        self._get_toc_data(toc=self._book.toc, lvl=1)

        for item in self._toc_data:
            if item['href'] in self._doc_list:
                self._toc_list.append(item)
                self._doc_list.remove(item['href'])

        for item in self._doc_list:

            if '/' in item:
                title = item.split('/')[-1]
            else:
                title = item

            self._toc_list.append({'lvl': 1, 'title': 'not_in_toc_' + title, 'href': item})

    def _get_all_doc(self):

        if not self._book:
            raise Exception

        self._doc_list = []
        for item in self._book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                self._doc_list.append(item.get_name())

    def _get_alt_img(self, orgin_img):

        if not orgin_img:
            return None

        orgin_img_name = orgin_img.split('/')[-1]
        if orgin_img_name in self._imgs_map:
            return self._imgs_map[orgin_img_name]
        else:
            return None

    def _get_title(self, body_str):

        header = None
        for clazz in range(1, 7):
            soup = BeautifulSoup(body_str, features='html.parser')
            res = soup.find(name='h{}'.format(str(clazz)))
            if res:
                header = res.get_text()
                break
        return header

    def _gen_by_href(self, path, title, href):

        if not self._book:
            raise Exception

        res = self._book.get_item_with_href(href)
        soup = BeautifulSoup(res.get_content(), features='html.parser')
        body = soup.find(name='body')
        body_str = str(body)
        imgs = body.find_all(name='img')

        for img in imgs:
            if self._get_alt_img(orgin_img=img['src']):
                body_str = body_str.replace(img['src'], self._get_alt_img(orgin_img=img['src']))

        if 'not_in_toc_' in title:
            header = self._get_title(body_str=body_str)
            if header:
                title = header

        path_note = path + title
        print('gen:', path_note)
        res = self._sy_client.ex_copy(dom=body_str, notebook=self._notebook_id)
        if 'code' in res and res['code'] == 0:
            md_doc = res['data']['md']
            # replace str
            for old, new in REPLACE_STR.items():
                md_doc = md_doc.replace(old, new)
            self._sy_client.create_note(notebook=self._notebook_id, path=path_note, markdown=md_doc)
            time.sleep(4)
        else:
            raise Exception

    def _gen_book_content(self):

        if not self._book:
            raise Exception

        if not self._book_name:
            self._book_name = 'Book'

        prev_lvl = 1
        prev_title = ''
        root_path = '/' + self._book_name + '/'
        path_dict = {1: root_path}

        for item in self._toc_list:

            if item['lvl'] == 1:
                path_dict = {1: root_path}
            else:
                if item['lvl'] - prev_lvl == 1:
                    path_dict.update({item['lvl']: path_dict[item['lvl'] - 1] + prev_title + '/'})

            if item['lvl'] in path_dict:
                path = path_dict[item['lvl']]
            else:
                path = root_path

            title = item['title'].replace('/', '')
            self._gen_by_href(path=path, title=title, href=item['href'])
            prev_lvl = item['lvl']
            prev_title = title

    def _gen_cover(self):

        if not self._book:
            raise Exception

        res = self._book.get_metadata('DC', 'title')
        self._book_name = res[0][0].replace('/', '')
        img = self._book.get_metadata('OPF', 'cover')[0][-1]["content"]
        cover_image = self._book.get_item_with_id(img)
        alt_img = self._get_alt_img(orgin_img=cover_image.get_name())
        print('gen cover:', self._book_name)
        if alt_img:
            self._sy_client.create_note(notebook=self._notebook_id, path='/' + self._book_name,
                                        markdown=" ![]({})".format(alt_img))
        else:
            self._sy_client.create_note(notebook=self._notebook_id, path='/' + self._book_name, markdown="")
        time.sleep(4)

    def gen_note(self, epub_path):

        self._book = epub.read_epub(epub_path)
        self._get_all_doc()
        self._gen_toc_list()
        self._upload_imgs()
        self._gen_cover()
        self._gen_book_content()
