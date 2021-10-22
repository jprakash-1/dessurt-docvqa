from datasets import load_dataset
import random
import os
from utils.util import ensure_dir
import re
#import unicodedata


if os.path.exists('DIR'):
    with open('DIR') as f:
        cache_path = f.readline().strip()
else:
    cache_path = '../data/wiki_cache' #/Data6/davis/data_cache
    ensure_dir(cache_path)

#if 'myVar' in locals():
#_text_data = []#load_dataset('wikipedia', '20200501.en', cache_dir=cache_path)['train']

_prune_headers = ["See also", "Gallery", "External media", "History", "Notes"]
_wiki_end_keywords = ['References','Sources','External links']
_wiki_end_keywords = ['\n'+k+'\n' for k in _wiki_end_keywords] + ['\n'+k+' \n' for k in _wiki_end_keywords] + ['\nCategory:']


def getWikiArticle(all_newline=False):
    global _text_data
    #Returns a list of text paragraphs from a randome wikipedia article
    if '_text_data' not in globals():
        _text_data = load_dataset('wikipedia', '20200501.en', cache_dir=cache_path)['train']

    instance_i = random.randrange(_text_data.num_rows)
    text = _text_data[instance_i]['text']
    #text = unicodedata.normalize(text,'NFC')#.decode('utf')


    #We first want to cut off the end of the wikipedia article, which has the references and stuff 
    for keyword in _wiki_end_keywords:
        cut_i = text.find(keyword)
        if cut_i>-1:
            break
    if cut_i>-1:
        text = text[:cut_i]

    #break by paragraph (double newline)
    text=re.sub(r' +',r' ',text)
    if all_newline:
        text=re.sub(r'\n+',r'\n',text)
        paras = text.split('\n')
    else:
        paras = text.split('\n\n')

    paras = [para for para in paras if para.strip() not in _prune_headers]
    
    if len(paras)>0:
        return paras
    else:
        print('blank article:')
        print(text)
        print('------------')
        print(_text_data[instance_i]['text'])
        return getWikiArticle()
