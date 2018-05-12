# -*- coding:utf-8 -*-
__author__ = 'jasonchen'

import hashlib

def get_md5(url):
    if isinstance(url, unicode):
        url = url.encode('utf8')
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()

# if __name__ == '__main__' :
#     print get_md5("http://jobbole.com")