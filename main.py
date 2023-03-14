import re
from time import sleep

import requests
from bs4 import BeautifulSoup
from pandas import DataFrame, concat
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def format_text(text: str, new_lines: bool = True):
    """
    Убрать из текста (если нужно) переносы строк и повторяющиеся пробелы.
    У mi-shop.com они повсюду.
    """
    if new_lines:
        text = re.sub(' +', ' ', text.replace('\r', '').replace('\n', ''))
    else:
        text = re.sub(' +', ' ', text)
    return text


def find_data(soup: BeautifulSoup, tag: str, class_: str, href: bool = False) -> DataFrame:
    """
    Получить DataFrame с отформатриованным содержимым или ссылками, найденными по тегу и классу.
    """
    goods = soup.findAll(tag, class_=class_, href=href)
    lst = []
    for good in goods:
        if href:
            text = good.get('href')
        else:
            text = format_text(good.text)
        lst.append(text)

    return DataFrame(lst)


def get_description(url: str) -> str:
    """
    Получить описание о товаре в формате строки.
    """
    response = requests.get('https://mi-shop.com' + url)
    soup = BeautifulSoup(response.text, "html.parser")
    df_table = [find_data(soup, 'td', 'detail__table-one'),
                find_data(soup, 'td', 'detail__table-two')]
    description_from_df = (concat(df_table, axis=1, join="inner")).to_string(
        header=False, index=False)
    description = format_text(description_from_df, new_lines=False)
    return description


def parse_page(response: requests) -> DataFrame:
    """
    Парсер одной страницы. На выходе DataFrame со всем содержимым.
    """
    soup = BeautifulSoup(response.text, "html.parser")
    df_list = []

    # Названия
    df = find_data(soup, 'div', 'product-card__title font-weight-bold')
    df_list.append(df)

    # Стоимость
    df = find_data(soup, 'span', 'font-weight-bolder price__new mr-2')
    df_list.append(df)

    # Описание
    df_urls = find_data(
        soup, 'a', 'product-card__name d-block text-dark', href=True)
    df = DataFrame({'A': []})
    urls = df_urls.values.flatten()
    for url in urls:
        description = get_description(url)
        df.loc[len(df)] = description
    df_list.append(df)

    df_data = concat(df_list, axis=1, join="outer")
    df_data.columns = ['Name', 'Price', 'Description']
    return df_data


def parse():
    """
    Парсер с пагинацией
    """
    url = "https://mi-shop.com/ru/catalog/smartphones/"
    response = requests.get(url)
    df_main_list = []
    # пагинация
    page = 1
    while response.status_code == 200:
        df = parse_page(response)
        df_main_list.append(df)
        page += 1
        url_page = url + f"page/{page}/"
        response = requests.get(url_page)
    df_main = concat(df_main_list)
    df_main.to_csv('out.csv', index=False)


def find_selenium(driver: webdriver, id: str, key: str):
    """
    Найти поле для ввода по id и заполнить его содержимое ключом.
    """
    input = driver.find_element("id", id)
    input.clear()
    input.send_keys(key)


def authorize():
    """
    Авторизация через Selenium.
    """
    url = 'https://mi-shop.com/ru/personal/?login=yes&backurl=%2Fru%2Fcatalog%2Fsmartphones%2Fredmi-9c-nfc-4-128gb-fioletovyy%2F'
    # to supress the error messages/logs
    try:
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(options=options, service=Service(
            ChromeDriverManager().install()))
        driver.get(url)
        # Данные для ввода
        email = "amogus"
        password = "imposter"
        # Заполнение полей
        find_selenium(driver, "auth-default-email", email)
        find_selenium(driver, "auth-default-password", password)
        # Кнопка ВОЙТИ
        driver.find_element("id", "auth-default-submit").click()
        # Подождать ответа
        sleep(1)
        # Сохранить скриншот
        driver.save_screenshot("auth.png")
    except Exception as ex:
        print(ex)
    finally:
        driver.quit()


if __name__ == '__main__':
    parse()
    authorize()
