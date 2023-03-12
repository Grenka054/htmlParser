import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import re
import pandas as pd


# def parse_selenium(url):
#     driver = webdriver.Chrome()
#     driver.maximize_window()
#     driver.get(url)

#     time.sleep(5)
#     content = driver.page_source.encode('utf-8').strip()
#     print(content)
#     parse_soup(url, content)
#     driver.quit()


def format_text(text, new_lines=True):
    '''
    Убрать из текста (если нужно) переносы строк и повторяющиеся пробелы.
    У mi-shop.com они повсюду.
    '''
    if new_lines:
        text = text.replace('\n', '')
        text = text.replace('\r', '')
    text = re.sub(' +', ' ', text)
    return text


def find_data(soup, tag, class_, href=False):
    '''
    Получить DataFrame с отформатриованным содержимым или ссылками, найденными по тегу и классу.
    '''
    goods = soup.findAll(tag, class_=class_, href=href)
    lst = []
    for good in goods:
        if href:
            text = good.get('href')
        else:
            text = good.text
            if format:
                text = format_text(text)
        lst.append(text)
    
    return pd.DataFrame(lst)


def get_description(url):
    '''
    Получить описание о товаре в формате строки.
    '''
    response = requests.get('https://mi-shop.com' + url)
    soup = BeautifulSoup(response.text, "html.parser")
    df1 = find_data(soup, 'td', 'detail__table-one')
    df2 = find_data(soup, 'td', 'detail__table-two')
    description_from_df = (pd.concat([df1, df2], axis=1, join="inner")).to_string(header=False, index=False)
    description = format_text(description_from_df, new_lines=False)
    return description


def parse_soup(response):
    '''
    Парсер сайта. На выходе DataFrame со всем содержимым.
    '''
    soup = BeautifulSoup(response.text, "html.parser")
    df_list = []
    
    # Названия
    df = find_data(soup, 'div', 'product-card__title font-weight-bold')
    df_list.append(df)

    # Стоимость
    df = find_data(soup, 'span', 'font-weight-bolder price__new mr-2')
    df_list.append(df)

    # Описание
    df_urls = find_data(soup, 'a', 'product-card__name d-block text-dark', href=True)
    df = pd.DataFrame({'A' : []})
    urls = df_urls.values.flatten()
    for url in urls:
        description = get_description(url)
        df.loc[len(df)] = description
    df_list.append(df)

    df_data = pd.concat(df_list, axis=1, join="outer")
    df_data.columns = ['Name', 'Price', 'Description']
    return df_data


if __name__ == '__main__':
    url = "https://mi-shop.com/ru/catalog/smartphones/"
    response = requests.get(url)
    df_main_list = []
    # пагинация
    page = 1
    url_page = url
    while response.status_code == 200:
        df = parse_soup(response)
        df_main_list.append(df)
        page += 1
        url_page = url + f"page/{page}/"
        response = requests.get(url_page)
        # не все страницы, а то долго ждатб :)
        if page == 3:
            break

    df_main = pd.concat(df_main_list)
    df_main.to_csv('out.csv', index=False)

    url = 'https://mi-shop.com/ru/personal/?login=yes&backurl=%2Fru%2Fcatalog%2Fsmartphones%2Fredmi-9c-nfc-4-128gb-fioletovyy%2F'
