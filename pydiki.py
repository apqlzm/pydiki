import requests
from bs4 import BeautifulSoup, element
import re
import sqlite3
import datetime
import argparse

DATE_FORMAT = '%Y-%m-%d'


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
    lis = soup.find_all('li', re.compile('^meaning'))
    meanings = dict()

    for i, li in enumerate(lis):
        meaning = ''
        add_info = ''
        for e in li.find('span', re.compile('^hw')).children:
            if isinstance(e, element.NavigableString):
                if len(e.string.strip()):
                    meaning = e.string.strip()
            else:
                if e.name == 'span' and e['class'][0] == 'meaningAdditionalInformation':
                    if len(e.get_text('|').strip()) > 1:
                        add_info = e.get_text('|').strip()
        if meaning != '':
            meanings[meaning] = add_info
            found = True
            print('%s. %s %s' % (i + 1, meaning, add_info))

    if found:
        add_to_db(word, meanings)


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
        c.execute('INSERT INTO word (word, createdate) VALUES (?, ?)', word_date)
        conn.commit()
    except sqlite3.IntegrityError:
        c.close()
        conn.close()
        print('(Info) Definition already exists in db')
        return
    c.execute('SELECT id FROM word WHERE word = ?', (word,))
    wid = c.fetchone()
    id_mean = [(wid[0], meaning, add_info) for meaning, add_info in meanings.items()]
    c.executemany('INSERT INTO meaning (wrd_id, meaning, ainfo) VALUES (?, ?, ?)', id_mean)
    conn.commit()
    c.close()
    conn.close()


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
                   meaning TEXT,
                   ainfo TEXT)''')
    conn.commit()
    conn.close()


def show_history(date=''):
    """
    Show history beginning with date
    """
    conn, cursor = db_connect()
    if date == '':
        cursor.execute('''SELECT MIN(createdate) FROM word''')
        max_date = cursor.fetchone()
        date = datetime.datetime.strptime(max_date, DATE_FORMAT)

    cursor.execute('SELECT word, meaning, ainfo, wrd_id FROM word JOIN meaning ON id = wrd_id WHERE createdate >= (?)', (date.strftime(DATE_FORMAT),))

    last_word = ''
    for r in cursor.fetchall():
        (word, meaning, ainfo, wrd_id) = r
        if last_word != word:
            print('%s (id=%s)' % (word, wrd_id))
            last_word = word
        print('    %s %s' % (meaning, ainfo))


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
    parser.add_argument('-l', type=date_type, dest='date', nargs='?',
                        help='show history of searched words which are not marked as learned')
    parser.add_argument('-m', dest='word_id', nargs=1, type=int, help='mark word as learned')

    args = parser.parse_args()

    if args.word:
        try:
            db_prep()
        except sqlite3.OperationalError as e:
            if 'already exists' not in str(e):
                raise
        print_definitions(args.word[0])
    elif args.date:
        show_history(args.date)


if __name__ == '__main__':
    main()
