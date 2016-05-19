import requests
from bs4 import BeautifulSoup
import re
import sys


def print_definitions(word):
    print('Meanings:')
    word = word.replace(' ', '+')
    result = requests.get('https://www.diki.pl/slownik-angielskiego?q=%s' % word)
    soup = BeautifulSoup(result.text, 'html.parser')
    lis = soup.find_all('li', re.compile('^meaning'))

    for i, li in enumerate(lis):
        print('%s. %s' % (i+1, li.span.get_text().strip()))


def main():
    if len(sys.argv) == 2:
        word = sys.argv[1]
        print_definitions(word)
    else:
        print('Usage: \n$ python3 pydiki.py \"english word\"\nArgument can have one or more words between quotes.')

if __name__ == '__main__':
    main()
