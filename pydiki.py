import requests
from bs4 import BeautifulSoup
import re
import sys
import sqlite3
import datetime


def print_definitions(word):
    found = False
    word = word.replace(' ', '+')
    result = requests.get('https://www.diki.pl/slownik-angielskiego?q=%s' % word)
    soup = BeautifulSoup(result.text, 'html.parser')
    lis = soup.find_all('li', re.compile('^meaning'))
    meanings = list()

    for i, li in enumerate(lis):
        found = True
        definition = li.span.get_text().strip()
        print('%s. %s' % (i+1, definition))
        meanings.append(definition)

    if found:
        add_to_db(word, meanings)


def add_to_db(word, meanings):
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    conn, c = db_connect()
    word_date = (word, date)
    try:
        c.execute('INSERT INTO word (word, createdate) VALUES (?, ?)', word_date)
        conn.commit()
    except sqlite3.IntegrityError:
        c.close()
        conn.close()
        print('(Info) Definition already exists in db')
        return
    c.execute('SELECT id FROM word WHERE word = ?', (word,))
    wid = c.fetchone()
    id_mean = [(wid[0], meaning) for meaning in meanings]
    print(id_mean)
    c.executemany('INSERT INTO meaning (wrd_id, meaning) VALUES (?, ?)', id_mean)
    conn.commit()


def db_connect():
    """
    Create database connection and cursor
    :return: connection and cursor
    """
    conn = sqlite3.connect('pydiki.db')
    cursor = conn.cursor()
    return conn, cursor


def db_prep():
    """
    Connect to existing database or create new one
    :return:
    """
    conn, cursor = db_connect()
    cursor.execute('''CREATE TABLE word (id INTEGER  PRIMARY  KEY,
                   word TEXT UNIQUE,
                   createdate TEXT)''')
    cursor.execute('''CREATE TABLE meaning (wrd_id INTEGER,
                   meaning TEXT)''')
    conn.commit()
    conn.close()


def main():
    """
    Prepare database if needed and search definition.
    :return:
    """
    if len(sys.argv) == 2:
        try:
            db_prep()
        except sqlite3.OperationalError as e:
            if 'already exists' not in str(e):
                raise
        word = sys.argv[1]
        print_definitions(word)
    else:
        print('Usage: \n$ python3 pydiki.py \"english or polish word\"\n'
              'Argument can have one or more words between quotes.')


if __name__ == '__main__':
    main()
