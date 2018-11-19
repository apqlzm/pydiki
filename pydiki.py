import requests
from bs4 import BeautifulSoup, element
import re
import sqlite3
import datetime
import argparse
import os

DATE_FORMAT = '%Y-%m-%d'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'pydiki.db')


def print_definitions(word):
    """
    Print definition and save in history
    :param word: that's what will be translated
    :return:
    """
    found = False
    word = word.replace(' ', '+')
    result = requests.get('https://www.diki.pl/slownik-angielskiego?q=%s' % word)
    soup = BeautifulSoup(result.text, 'html.parser')
    meanings = dict()

    list_def = soup.find_all('ol', re.compile(
        'foreignToNativeMeanings|nativeToForeignEntrySlices'))
    
    for ol in list_def:
        add_info = '|en->pl|'
        if 'foreignToNativeMeanings' in str(ol):
            for i, m in enumerate(ol.find_all('li', re.compile('^meaning\d+'))):
                meaning = ''
                for span in m.find_all('span', 'hw'):
                    meaning += span.text + ', '
                if meaning:
                    meaning = meaning.strip()[:-1]
                    meanings[meaning] = add_info
                    found = True
                    print('%s. %s %s' % (i + 1, meaning, add_info))
        else:
            add_info = '|pl->en|'
            j = 0
            for li in ol.contents:
                meaning = ''
                if isinstance(li, element.Tag):
                    for hw in li.contents:
                        if isinstance(hw, element.Tag):
                            if hw['class'][0] == 'hw':
                                meaning += hw.text.strip() + ', '
                if meaning:
                    j += 1
                    meaning = meaning.strip()[:-1]
                    meanings[meaning] = add_info
                    found = True
                    print('%s. %s %s' % (j, meaning, add_info))
    if found:
        add_to_db(word.replace('+', ''), meanings)


def add_to_db(word, meanings):
    """
    Add word and list off meanings to database
    :param word:
    :param meanings: translations
    :return:
    """
    date = datetime.datetime.now().strftime(DATE_FORMAT)
    conn, c = db_connect()
    word_date = (word, date)
    try:
        c.execute('INSERT INTO word (word, createdate, learned) VALUES (?, ?, ?)', (word_date + (0,)))
        conn.commit()
    except sqlite3.IntegrityError:
        c.close()
        conn.close()
        print('(Info) Definition could not be saved')
        return
    c.execute('SELECT id FROM word WHERE word = ?', (word,))
    wid = c.fetchone()
    id_mean = [(wid[0], meaning, add_info) for meaning, add_info in meanings.items()]
    c.executemany('INSERT INTO meaning (word_id, meaning, ainfo) VALUES (?, ?, ?)', id_mean)
    conn.commit()
    c.close()
    conn.close()


def db_connect():
    """
    Create database connection and cursor
    :return: connection and cursor
    """
    conn = sqlite3.connect(DB_PATH)
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
                   createdate TEXT,
                   learned NUMERIC)''')
    cursor.execute('''CREATE TABLE meaning (word_id INTEGER,
                   meaning TEXT,
                   ainfo TEXT)''')
    conn.commit()
    cursor.close()
    conn.close()


def show_history(begin_date='2000-01-01'):
    """
    Show history since date
    """
    conn, cursor = db_connect()
    cursor.execute('SELECT word, meaning, ainfo, word_id FROM word JOIN meaning ON id = word_id '
                   'WHERE createdate >= (?) AND learned = 0', (begin_date,))

    last_word = ''
    for r in cursor.fetchall():
        (word, meaning, ainfo, word_id) = r
        if last_word != word:
            print('%s (id=%s)' % (word, word_id))
            last_word = word
        print('    %s %s' % (meaning, ainfo))
    cursor.close()
    conn.close()


def mark_learned(word_id):
    """
    Mark word as learned
    :param word_id: word id
    :return:
    """
    conn, cursor = db_connect()
    cursor.execute('UPDATE word SET learned = 1 WHERE id = ?', (str(word_id[0]),))
    conn.commit()
    cursor.close()
    conn.close()


def main():
    """
    Prepare database if needed and search for a definition.
    :return:
    """

    def date_type(arg_date):
        return datetime.datetime.strptime(arg_date, DATE_FORMAT)

    parser = argparse.ArgumentParser(description='English <-> Polish dictionary')
    parser.add_argument('-t', dest='word', nargs=1,
                        help='english or polish word to be translated. '
                             'It is possible to have one or more words between quotes')
    parser.add_argument('-l', dest='date', action='store_true',
                        help='show history of searched words which are not marked as learned '
                             'since specified date (format: yyyy-MM-dd)')
    parser.add_argument('-m', dest='word_id', nargs=1, type=int, help='mark word as learned')

    args = parser.parse_args()

    if args.word:
        try:
            db_prep()
        except sqlite3.OperationalError as e:
            if 'already exists' not in str(e):
                raise
        print_definitions(args.word[0])
    elif not os.path.isfile(DB_PATH):
        print('[ERROR] db file doesn\'t exist yet. Please translate (-t) at least one word.')
        return
    elif args.date:
        show_history()
    elif args.word_id:
        mark_learned(args.word_id)


if __name__ == '__main__':
    main()
