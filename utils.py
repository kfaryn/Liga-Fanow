#!/usr/bin/env python
# coding: utf-8

# In[9]:


# LIBRARIES NEEDED

import pandas as pd
import numpy as np

import requests
from bs4 import BeautifulSoup

import re
from unidecode import unidecode

# GLOBAL DICTIONARIES

ligi = {
    'ekstraklasa':'https://ligafanow.pl/rozgrywki/tabela/30/235',
    '1liga':'https://ligafanow.pl/rozgrywki/tabela/30/234',
    '2liga':'https://ligafanow.pl/rozgrywki/tabela/30/231',
    '3liga':'https://ligafanow.pl/rozgrywki/tabela/30/232',
    '4liga':'https://ligafanow.pl/rozgrywki/tabela/30/233',
    '5liga':'https://ligafanow.pl/rozgrywki/tabela/30/230',
    '6liga':'https://ligafanow.pl/rozgrywki/tabela/30/229',
    '7liga':'https://ligafanow.pl/rozgrywki/tabela/30/228',
    '8liga':'https://ligafanow.pl/rozgrywki/tabela/30/227',
    '9liga':'https://ligafanow.pl/rozgrywki/tabela/30/226',
    '10liga':'https://ligafanow.pl/rozgrywki/tabela/30/225',
    '11liga':'https://ligafanow.pl/rozgrywki/tabela/30/224',
    '12liga':'https://ligafanow.pl/rozgrywki/tabela/30/223',
    '13liga':'https://ligafanow.pl/rozgrywki/tabela/30/236'
}
ligi_strzelcy = {key: value.replace('tabela', 'strzelcy') + '?loadpl=all' for key, value in ligi.items()}

# MAIN FUNCTIONS

def get_table(league, ligi = ligi):
    """
    Retrieves and parses the league table data from the provided league name using the corresponding URL.
    
    Parameters:
    - league (str): The name of the league for which the table data will be fetched.
    - ligi (dict): A dictionary containing league names as keys and their corresponding URLs as values.
    
    Returns:
    - pandas.DataFrame: A DataFrame representing the league table, with headers and data extracted from the HTML
      content of the league's URL. The DataFrame is cleaned and formatted for further analysis.
    """
    # Get response from url
    response = requests.get(ligi[league])
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find table in url
    table = soup.find('table')
    
    # Empty lists for data
    headers = []
    rows = []
    
    # Get headers
    for th in table.findAll('th'):
        headers.append(th.text.strip())
        
    # Get data
    for tr in table.findAll('tr'):
        row = []
        for td in tr.findAll(['td', 'th']):
            row.append(td.text.strip())
        rows.append(row)
        
    # Create dataframe
    df = pd.DataFrame(rows, columns=headers)
    df.columns = df.iloc[0]
    df = df[1:]
    df = convert_to_int(df)
    df = adjust_dataframe(df)
    
    return df

def get_matches(league, round_=None, team=None, ligi=ligi):
    """
    Retrieves and compiles the match data for a given league, with optional filters for specific rounds or teams.

    Parameters:
    - league (str): The name of the league for which match data will be fetched.
    - round_ (int or None): If provided, filters the match data to include only matches from the specified round.
    - team (str or None): If provided, filters the match data to include only matches involving the specified team.
    - ligi (dict): A dictionary containing league names as keys and their corresponding URLs as values.

    Returns:
    - pandas.DataFrame: A DataFrame representing the match data for the specified league. The DataFrame is cleaned
      and formatted for further analysis. Optional filters based on round or team are applied if provided.
    """
    links = table_of_links(league)
    wyniki = []
    for zespol in links['Zespół']:
        wynik = take_table_results(extract_mecze_links(zespol))
        # Przykład użycia
        wynik['Kol.'] = wynik['Kol.'].apply(extract_round)   
        wyniki.append(wynik)
    df = pd.concat(wyniki)
    df = df.drop_duplicates()
    df = convert_to_int(df)
    df.sort_values(['Kol.', 'Godz.'], ascending=[False, True], inplace=True)  # Dodano inplace=True
    
    # When round added
    if round_ is not None:
        df = df[df['Kol.'] == round_]
    
    # When team added
    if team is not None:
        df = df[(df['Gospodarz'] == team) | (df['Gość'] == team)]      
    
    df = df.reset_index(drop=True)
    
    return df

def get_squad_details(league, team, ligi=ligi):
    links = table_of_links(league)
    try:
        link = links.loc[links['Zespół'].str.contains(adjust_team_name(team)), 'Zespół'].iloc[0]
        df = extract_team(link)
        return df
    except: 
        print('Podany zespół nie został znaleziony sprawdź pisownię ponownie')
        
def get_match_details(league, team, kolejka=None, opponent = None):
    """
    -opponent is not yet ready available
    """   
    if ((kolejka == None) & (opponent == None)) == False:
#         if kolejka != None:
#             link = matches[matches.kolejka == str(kolejka)].link[0]
#         else:
        matches = get_matches_links(league, team)
        link = matches[matches.kolejka == str(kolejka)].link.iloc[0]
    else:
        link = None
    return match_details(link)

# ASIDE FUNCTIONS

def table_of_links(league, ligi = ligi):
    """
    Retrieves and extracts a table with columns containing links from the specified league's URL.

    Parameters:
    - league (str): The name of the league for which the table with links will be extracted.
    - ligi (dict): A dictionary containing league names as keys and their corresponding URLs as values.

    Returns:
    - pandas.DataFrame: A DataFrame representing a table with columns containing links extracted from the HTML
      content of the league's URL. The DataFrame includes headers and link columns. Links are extracted from 'a' tags
      within 'td' elements of the HTML table. If a 'td' element contains no link, an empty string is appended.
    """
    # Get response from URL
    response = requests.get(ligi[league])
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table in the URL
    table = soup.find('table')

    # Empty lists for data
    headers = []
    link_columns = []

    # Get headers
    for th in table.findAll('th'):
        headers.append(th.text.strip())

    # Get data
    for tr in table.findAll('tr'):
        row = []
        for td in tr.findAll(['td', 'th']):
            # Check if the td tag contains an 'a' tag (link)
            link = td.find('a')
            if link:
                # If there is a link, append the link's href attribute
                row.append(link.get('href'))
            else:
                # If there is no link, append an empty string
                row.append('')
        link_columns.append(row)

    # Create a DataFrame with link columns
    df = pd.DataFrame(link_columns, columns=headers)

    # Remove rows with all empty values
    df = df.replace('', pd.NA).dropna(how='all')

    # Remove columns with all empty values
    df = df.replace('', pd.NA).dropna(axis=1, how='all')
    
    df = df.reset_index(drop=True)

    return df

def triple_strings(list_):
    """
    Formats data from league tables by grouping every three consecutive elements with varying space separations into
    clear rows. This function is designed to enhance the readability of league table data.

    Parameters:
    - list_ (list): A list containing strings, typically extracted from league tables, where data elements are
      separated by different numbers of spaces.

    Returns:
    - list of str: A list of formatted strings, with every three consecutive elements joined into clear rows for
      improved presentation of league table data.
    """
    result = []
    for i in range(0, len(list_), 3):
        triple = list_[i:i+3]
        result.append(' '.join(triple))
    return result

def string_divide(string, min_space_number=2):
    """
    Splits a given string into substrings based on consecutive spaces, while allowing for a minimum number of spaces
    between substrings. The function aims to identify meaningful segments of the input string, considering a specified
    minimum space count to distinguish between substrings.

    Parameters:
    - string (str): The input string to be divided.
    - min_space_number (int): The minimum number of consecutive spaces required to separate substrings. Default is 2.

    Returns:
    - list of str: A list containing the identified substrings from the input string, excluding leading and trailing
      whitespaces. Empty substrings are excluded from the result.
    """
    substrings = []
    current_podstring = ""
    space_number = 0

    for sign in string:
        if sign == ' ':
            if space_number >= min_space_number-1:
                substrings.append(current_podstring.strip())
                current_podstring = ""
            elif current_podstring.strip():
                current_podstring += ' '
            space_number += 1
        else:
            current_podstring += sign
            space_number = 0

    if current_podstring.strip():
        substrings.append(current_podstring.strip())

    substrings = [substring for substring in substrings if substring.strip()]

    return substrings

def convert_to_int(df):
    """
    Converts columns of a DataFrame to the int type where possible.
    
    Parameters:
    - df (pandas.DataFrame): DataFrame to be converted.
    
    Returns:
    - pandas.DataFrame: Modified DataFrame.
    """
    for column in df.columns:
        try:
            df[column] = df[column].astype(int)
        except ValueError:
            pass  # If conversion is not possible, proceed to the next column
    return df

def divide_events(text):
    pattern = re.compile(r'([PWR]) \d{4}-\d{2}-\d{2} \d{2}:\d{2}')
    # Wyszukiwanie pasujących sekwencji w tekście
    matches = pattern.findall(text)

    # Gromadzenie rodzajów wydarzeń
    event_types = [match[0] for match in matches]

    # Tworzenie stringa z rodzajami wydarzeń, oddzielonymi przecinkami
    result_string = ",".join(event_types)
    
    return result_string

def adjust_dataframe(df):
    df = df.replace('', pd.NA).dropna(axis=1, how='all')
    # Linijka do poprawy jeśli jakieś wartości są uzupełnione
    df.columns = ['Poz', 'Zespół', 'Mecze_rozegrane', 'Pkt.', 'Pkt.', 'Z', 'R', 'P', 'BZ', 'BS', '+/-','Forma']
    df['Forma'] = df['Forma'].apply(lambda x: divide_events(x))
    df = df.sort_values('Poz')
    df = df.reset_index(drop=True)
    return df

def team_form_df(df, team):
    data = df[df['Zespół'] == team]['Forma'][0] 
    
    # Podzielenie danych na wiersze
    rows = re.split(r'([PWR])\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', data)[1:]
    # Columns
    columns = ["Typ", "Data", "Czas", "Drużyna 1", "Wynik", "Drużyna 2", "Arena"]
    team_df = pd.DataFrame([row.split()[0:3] + [string_divide(row)[1]] + [string_divide(row)[2]]+ [string_divide(row)[3]] + [string_divide(row)[4]] for row in triple_strings(rows)], columns=columns)
    return team_df

def extract_mecze_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    mecze_links = []
    for link in soup.find_all('a', href=True):
        if 'mecze' in link['href']:
            mecze_links.append(link['href'])

    return mecze_links[0]

def extract_mecze_details_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    mecze_details_links = []
    for link in soup.find_all('a', href=True):
        if 'raport' in link['href'] and 'veo' not in link['href']:
            mecze_details_links.append(link['href'])

    return list(set(mecze_details_links))

def take_table_results(url):
    """
    Function that takes a table of league from the given url
    """
    # Get response from url
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find table in url
    table = soup.find('table')

    # Empty lists for data
    headers = []
    rows = []

    # Get headers
    for th in table.findAll('th'):
        headers.append(th.text.strip())

    # Get data
    for tr in table.findAll('tr')[1:]:  # Skip the first row as it contains headers
        row = []

        # Check if the row contains data or nested structure
        if tr.find('td', class_='hideonmobie'):
            # Extract data from nested structure
            mobile_data = tr.find('span', class_='d-block d-sm-none')
            row.append(mobile_data.find('div', class_='text-uppercase').text.strip())  # Extract mobile data
            row.extend([td.text.strip() for td in mobile_data.find_all('div', class_='text-center')])

        else:
            # Extract data from regular structure
            row.extend([td.text.strip() for td in tr.find_all(['td', 'th'])])

        rows.append(row)

    # Create DataFrame
    df = pd.DataFrame(rows, columns=headers)

    return df

# Customowa funkcja do wyciągania wartości
def extract_round(row):
    match = re.search(r'kolejka (\d+)', row)
    if match:
        return match.group(1)
    return None

def match_details(path):
    response = requests.get(path)

    soup = BeautifulSoup(response.text, 'html.parser')

    # Znajdź wszystkie tabelki na stronie
    tables = soup.find_all('table')

    # Przechowaj ramki danych w liście
    dataframes = []

    # Sprawdź, czy znaleziono jakiekolwiek tabele
    if tables:
        # Iteruj przez wszystkie znalezione tabele
        for table in tables:
            # Wydziel dane z tabeli do listy słowników
            table_data = []
            rows = table.find_all('tr')

            # Sprawdź, czy istnieje przynajmniej jeden wiersz
            if rows:
                header = [header.text.strip() for header in rows[0].find_all(['th', 'td'])]

                # Iteruj przez pozostałe wiersze
                for row in rows[1:]:
                    row_data = [cell.text.strip() for cell in row.find_all(['th', 'td'])]
                    table_data.append(dict(zip(header, row_data)))

                # Przekształć dane do DataFrame
                df = pd.DataFrame(table_data)
                dataframes.append(df)

    # Wydrukuj ramki danych
    df = pd.concat([dataframes[1],dataframes[2]]).dropna()
    
    return df

# Functions to gather teams data

def extract_table_data(table):
    table_data = []

    # Znajdź nagłówki z pierwszego wiersza thead
    header_row = table.select('thead tr')[1]  # Use the second row to get headers with tooltip
    headers = []

    for header in header_row.find_all(['th', 'td']):
        if 'tooltip' in header.attrs:
            headers.append(header['tooltip'].strip())
        else:
            headers.append(header.text.strip())

    rows = table.select('tbody tr')

    for row in rows:
        player_data = {}
        columns = row.find_all(['td', 'th'])

        # Iteruj przez kolumny w danym wierszu
        for i, col in enumerate(columns):
            player_data[headers[i]] = col.text.strip()

        table_data.append(player_data)

    return table_data

def extract_team(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table1 = soup.find('table', {'id': 'mytxablecc'})
    table2 = soup.find('table', {'id': 'mytxablec'})

    # Sprawdź, czy obie tabele zostały znalezione
    if table1 and table2:
        # Ekstrahuj dane z obu tabel
        data1 = extract_table_data(table1)
        data2 = extract_table_data(table2)

    # Połącz dane z obu tabel w jedną listę
    combined_data = data1 + data2

    # Przekształć dane do DataFrame
    df = pd.DataFrame(combined_data)
    df.columns = ['Imie i nazwisko', 'Numer', 'Liczba wystepów', 'Liczba bramek',
       'Asysty', 'Kanadyjcztk', 'Superstar', 'Top6', 'MVP', 'Czerwone kartki',
       'Zółte kartki', 'Stracone bramki', 'Samobój', 'Obronione karne',
       'Czyste konto', 'Gold Team','ID']
    return df

def reports_links(url):
    list_ = extract_mecze_details_links(extract_mecze_links(url)) #dff.Zespół[0])
    list_ = ['https://ligafanow.pl/'+ elem for elem in list_]
    return list_

def adjust_team_name(string, separator='-'):
    """
    Transforms the input text to lowercase (ASCII), removes diacritics,
    and then joins words using the specified separator.

    :param string: The original text
    :param separator: The separator used to join words
    :return: The transformed text
    """
    # Convert to lowercase (ASCII) and remove diacritics
    string = unidecode(string.lower())

    # Join words using the specified separator
    string = string.replace(' ', separator)

    return string

# Functions to gather matches data

def match_details(path):
    if path != None:
        response = requests.get(path)

        soup = BeautifulSoup(response.text, 'html.parser')

        # Znajdź wszystkie tabelki na stronie
        tables = soup.find_all('table')

        # Znajdź zespoły w title
        title_content = soup.title.string
        matches = re.search(r'\(.*?\)\s*(.+?)\s+vs\s+(.+?)\s+-', title_content)
        if matches:
            team1 = matches[1].strip()
            team2 = matches[2].strip()

        # Przechowaj ramki danych w liście
        dataframes = []

        # Sprawdź, czy znaleziono jakiekolwiek tabele
        if tables:
            # Iteruj przez wszystkie znalezione tabele
            for table in tables:
                # Wydziel dane z tabeli do listy słowników
                table_data = []
                rows = table.find_all('tr')

                # Sprawdź, czy istnieje przynajmniej jeden wiersz
                if rows:
                    header = [header.text.strip() for header in rows[0].find_all(['th', 'td'])]

                    # Iteruj przez pozostałe wiersze
                    for row in rows[1:]:
                        row_data = [cell.text.strip() for cell in row.find_all(['th', 'td'])]
                        table_data.append(dict(zip(header, row_data)))

                    # Przekształć dane do DataFrame
                    df = pd.DataFrame(table_data)
                    dataframes.append(df)

        # Wydrukuj ramki danych
        tab1 = dataframes[1]
        tab1['Zespół'] = team1
        tab2 = dataframes[2]
        tab2['Zespół'] = team2

        df = pd.concat([tab1,tab2]).dropna()
    else:
        df = None
    return df

def get_matches_links(league, team):
    # Inicjalizuj listy, do których będziemy dodawać dane
    links = table_of_links(league)
    link = links.loc[links['Zespół'].str.contains(adjust_team_name(team)), 'Zespół'].iloc[0]
    matches_links = reports_links(link)
    
    links_list = []
    kolejka_list = []
    data_list = []
    godzina_list = []

    # Iteruj po linkach
    for link in matches_links:
        # Pobierz zawartość strony
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Wyszukaj element z informacją o kolejce
        kolejka_element = soup.find('div', class_='BoxHeaderTitle')

        if kolejka_element:
            # Pobierz tekst
            tekst_kolejki = kolejka_element.get_text(strip=True)

            # Użyj wyrażenia regularnego do wyciągnięcia danych
            match = re.match(r"Raport   - Kolejka (\d+), (\d{4}-\d{2}-\d{2} \d{2}:\d{2})", tekst_kolejki)

            if match:
                numer_kolejki, data_godzina = match.groups()

                # Dodaj dane do odpowiednich list
                links_list.append(link)
                kolejka_list.append(numer_kolejki)
                data_list.append(data_godzina.split()[0])
                godzina_list.append(data_godzina.split()[1])

    # Stwórz DataFrame z zebranych danych
    df = pd.DataFrame({
        'link': links_list,
        'kolejka': kolejka_list,
        'data': data_list,
        'godzina': godzina_list
    })

    # Wyświetl ostateczną tabelkę
    return df