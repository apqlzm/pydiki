### pydiki
Słownik CLI angielsko <-> polski

#### Przykłady użycia
Tłumaczenie słów
```
python3 pydiki.py -t "umbrella"
python3 pydiki.py -t "umbrella organization"
```

Przeglądanie historii. 
```
python3 pydiki.py -l 
```

Oznaczanie słowa jako nauczone. Argumentem jest id słowa (id można podejrzeć w historii). 
```
python3 pydiki.py -m 1
```

#### Przykładowa konfiguracja w systemie z wykorzystaniem virtualenv

Przygotowanie skryptu i umieszczenie go w katalogu domowym
```
#!/bin/bash
source /home/user/Programs/virtualenv/bin/activate
python /home/user/Programs/pydiki/pydiki.py $@
deactivate
```

Umieszczenie w *.bashrc* linii ze ścieżką wskazującej na przygotowany skrypt  
```
alias pydiki="/home/user/Programs/pydiki/pydiki.sh"
```

Po tych czynnościach można uruchamiać skrypt następująco:
```
pydiki -t krotka
```
