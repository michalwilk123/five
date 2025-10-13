The puspose of the code_agent is to provide a runtime for Script

Script is a JSON object that is long and multistep prompt that can be for example used to
generate a project from scratch

The Script is an abstract prompt representation. It can be used for anything.
In this project it is used as a massive prompt to represent the whole programming project from scratch

The main difference between Script and regular prompt is that the Script is executed by the
LLM element after element. It can be nested and be really complex, allowing for detailed project generation.


## Potrzebne prompty 

## alfa) Generowanie prototypu od zera, krok najpierwszy
1) Prompt od uzytkownika:

1.1) Sprawdzenie czy prompt jest wykonalny i czy wymaga rozbudowania / dopytania sie uzytkownika / ew. jakiegoś rozbicia **

1.2) Rozbudowa promptu o:
- kontekst
- kontrakt
- logika

2) One shot funkcjonalności *** (Najmocniejszy model)

3) Generowanie struktury plików / wywiad z użytkownikiem odnośnie preferowanego stylu



### a) Dodawanie funkcjonalności

1) Tworzenie prompta / Enhancing (wymagany opis opis projektu krótki na 1 zdanie)
2) Weryfikacja zadania czy jest do wykonania w jednym prompcie
3) Tworzenie opisu logiki kodu w krokach
4) Tworzenie opisu kontraktu funkcjonalności
5) One-shotowanie kodu dodajac opis logiki + kontrakt
6) Dodanie wywołań nowego kodu w obecnym projekcie na podstawie kontraktu i logiki
7) Dostosowanie nowego kodu do wywołań (może być potrzebne więcej niż 1 dostowanie)
8) Wdrożenie kodu z funkcjonalnościa -> określenie miejsc gdzie dany kod ma zostać dodany
9) Dla kazdego edytowanego pliku -> edycja pliku zmienianego
10) Poprawienie importów / konfiguracji


Poprawione:
1) Określenie wymagań, wywiad z użytkownkiem przygotowanie kontekstu, kontraktu, opisu logiki
2) One shot z promptem - generowanie kodu
3) Wdrażanie kodu


Jakie narzedzia sa potrzebne
1) Edytowanie kodu
2) Czytanie drzewa plików. Możliwa wariacja zwyklego czytania kodu
3) Find / Grep
4) Mover (przenoszenie kodu bez obowiazku dodawania kodu do kontekstu). Możliwe że to wariacja edytowania
5) Czytanie / foldowanie kodu


Kroki:
1) Prompt od uzytkownika:

1.1) Sprawdzenie czy prompt jest wykonalny i czy wymaga rozbudowania / dopytania sie uzytkownika / ew. jakiegoś rozbicia **

1.2) Rozbudowa promptu o:
- kontekst
- kontrakt
- logika

2) One shot funkcjonalności *** (Najmocniejszy model)

2.1) Określenie gdzie wygenerowany prompt ma sie finalnie znaleźć i określenie jaki kod będzie go wywoływał (duży kontekst, kilka kroków)

2.2) Podanie kodu który został pobrany w poprzednim kroku do kontekstu prompta i na jego podstawie edytowanie kodu projektu. Ew. dodanie importow

2.3) Poprawienie powiazanego kodu. Trzeba zobaczyc prompt który wygenerował zmieniony kod, stamtad pobrac pliki


Kroki 2.1, 2.2 moga byc rozbite na kilka krokow jezeli to konieczne

