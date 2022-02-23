import mimetypes
import threading
import time
import requests
from bs4 import BeautifulSoup
import random
import time
import os
from package.user_info import base_path, result_csv_path
from package.user_info import get_info
import csv
from urllib.parse import quote
import re
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import zipfile
import keepa
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email import encoders


user_agents = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0",
    "Mozilla/5.0 (Windows NT 10.0; yWOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3864.0 Safari/537.36",
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
]
proxy_path = base_path + '/datas/proxy_list.txt'
if os.path.isfile(proxy_path):
    with open(proxy_path, 'r') as f:
        proxy_list = [val.split(':') for val in f.read().split('\n')]
else:
    proxy_list = []

proxy_in_use_list = []

price_fee_list = {
    "本": 15,
    "CD・レコード": 15,
    "DVD": 15,
    "ビデオ": 15,
    "その他のカテゴリー": 15,
    "TVゲーム": 15,
    "DIY・工具": 15,
    "産業・研究開発用品": 15,
    "PCソフト": 15,
    "ホームアプライアンス": 15,
    "腕時計": 15,
    "ベビー&マタニティ": 15,
    "ペット用品": 15,
    "ホーム（インテリア・キッチン）": 15,
    "文房具・オフィス用品": 15,
    "エレクトロニクス（AV機器&携帯電話）": 8,
    "大型家電": 8,
    "カメラ": 8,
    "服&ファッション小物": 8,
    "パソコン・周辺機器": 8,
    "（エレクトロニクス、カメラ、パソコン）付属品": 10,
    "楽器": 10,
    "ドラッグストア": 10,
    "ビューティ": 10,
    "食品&飲料": 10,
    "おもちゃ&ホビー": 10,
    "スポーツ&アウトドア": 10,
    "カー&バイク用品": 10,
    "ホーム（家具）": 10,
    "Amazonデバイス用アクセサリ": 45,
    "シューズ&バッグ": 5,
}


class LogClass:
    counter = 0
    item_ids = []
    available_ids = []
    total_pages = 0

    id_price_and_names = {}

    print_func = print
    print_func_back = print

    def __init__(self, thread_num, print_func, print_func_back):
        self.counter = 0
        self.item_ids = []
        self.available_ids = []
        self.price_and_names = []
        self.total_pages = 0

        self._lock = threading.Lock()

        self.print_func_back = print_func_back
        self.print_func = print_func

    def log_print(self, msg, back=False):
        if back:
            self.print_func_back(msg)
        else:
            self.print_func(msg)

    def increment(self, text, first=False):
        with self._lock:
            self.counter += 1
            self.log_print(f'{text}・・・{self.counter}/{self.total_pages}', not first)


def get_random_proxy():
    proxy = []
    in_use = True
    while in_use:
            proxy = random.choice(proxy_list)

            if {
            'http': f'http://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}',
                    'https': f'https://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}',
            } not in proxy_in_use_list:
                in_use = False

    proxies = {
        'http': f'http://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}',
        'https': f'https://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}',
    }

    return proxies


# return response or None
def get_requests(url):
    tentative_num = 0

    proxies = get_random_proxy()

    proxy_in_use_list.append(proxies)

    while tentative_num < 3:
        agent = random.choice(user_agents)

        try:
            req = requests.get(url, headers={
                "User-Agent": agent
            }, proxies=proxies)
        except Exception as e:
            print(e)
            tentative_num += 1
            time.sleep(1)
            continue

        if req.ok:
            proxy_in_use_list.remove(proxies)

            return req
        else:
            tentative_num += 1

        time.sleep(3)

    proxy_in_use_list.remove(proxies)
    return None


# return soup or None using get_requests
def get_soup(url):
    res = get_requests(url)

    try:
        res.encoding = res.apparent_encoding
        return BeautifulSoup(res.text, 'html.parser')
    except:
        return None


def send_mail():
    info = get_info()
    [mail_address, user_pass] = [info['gmail'], info['gmail_pass']]

    smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    smtp.login(mail_address, user_pass)

    encoding = 'utf-8'
    title = f'ビックカメラ：在庫あり'

    message = MIMEMultipart()
    message['Subject'] = Header(title, encoding)
    message['From'] = mail_address
    message['To'] = mail_address

    ctype, encoding = mimetypes.guess_type(result_csv_path)
    if ctype is None or encoding is not None:
        ctype = "application/octet-stream"

    maintype, subtype = ctype.split("/", 1)
    with open(result_csv_path, 'rb') as fp:
        attachment = MIMEBase(maintype, subtype)
        attachment.set_payload(fp.read())

    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", "attachment", filename=result_csv_path)
    message.attach(attachment)

    smtp.sendmail(mail_address, [mail_address], message.as_string())

    smtp.close()


################ ビックカメラサイド ###################


def set_url(url):
    to_add_list = ['?', 'sold_out_tp2=2', 'min=2000', 'rowPerPage=100']
    for i, add in enumerate(to_add_list):
        if i == 0:
            if add not in url:
                url += add
        else:
            if add not in url:
                url += '&' + add
    return url


def get_item_ids(url, log_class: LogClass):
    url = set_url(url)
    result = []

    soup = get_soup(url)

    if soup:
        try:
            list_div = soup.find(id='ga_itam_list')

            li_list = list_div.find_all('li')

            for li in li_list:
                status_elm = li.find(class_='label_gray')
                if status_elm:
                    try:
                        id_ = li.attrs['id'].replace('bcs_item', '')
                        status = status_elm.text
                        price = li.find(class_='bcs_price_soldout').text

                        if '販売を終了しました' in status:
                            result.append(id_)
                            log_class.id_price_and_names[id_] = {
                                "price": price
                            }
                    except:
                        pass
        except:
            print('here')
            pass
    else:
        print('soup None')

    return result


def get_availability(item_id, log_class: LogClass):
    url = f'https://www.biccamera.com/bc/tenpo/CSfBcToriokiList.jsp?GOODS_NO={item_id}'

    soup = get_soup(url)
    available = False

    if soup:
        try:
            available = not '全てのお店で在庫がございません' in soup.text

            log_class.id_price_and_names[item_id]['name'] = soup.find(class_='goodsLink').text
        except:
            print('simply here')
            pass
    else:
        print('SOUP NONE')

    return available


def single_step_item_availabilities(ids, sleep, log_class: LogClass):
    for item_id in ids:
        ok = get_availability(item_id, log_class)
        if ok:
            log_class.available_ids.append(item_id)

        log_class.increment('在庫確認中')

        time.sleep(random.uniform(sleep[0], sleep[1]))


def single_step_item_ids(url_and_pages, sleep, log_class: LogClass):
    for u_p in url_and_pages:
        url = u_p[0]
        start_page = u_p[1]
        max_page = u_p[2]

        for page in range(start_page, max_page + 1):
            if '?' not in url:
                log_class.item_ids.extend(get_item_ids(f'{url}?p={page}', log_class))
            else:
                log_class.item_ids.extend(get_item_ids(f'{url}&p={page}', log_class))

            log_class.increment('販売終了商品を検索中')

            if page != max_page:
                time.sleep(random.uniform(sleep[0], sleep[1]))


######################################################

# max_page or 0

################# Amazon ############################
# def amazon_to_asin(item_name, bic_link):
#     soup = get_soup(bic_link)
#
#     model = ''
#     point = 0
#
#     try:
#         if '型番' in soup.text:
#             trs = soup.find_all('tr')
#             for tr in trs:
#                 if '型番' in tr.text:
#                     model = tr.find('td').text
#
#         point = int(re.sub('\\D', '', soup.find(class_='bcs_point bcs_basefont').text))
#     except Exception as e:
#         print(e)
#
#     if model:
#         k = model
#     else:
#         k = '+'.join([quote(val) for val in item_name.split(' ')])
#
#     soup = get_soup(f'https://www.amazon.co.jp/s?k={k}')
#
#     temp = soup.find_all(class_='sg-col-4-of-12 s-result-item s-asin sg-col-4-of-16 sg-col s-widget-spacing-small sg-col-4-of-20')
#
#     print(temp)
#     print(len(temp))
#     quit()
#
#     asin = temp['data-asin']
#     price = re.sub('\\D', '', temp.find(class_='a-price-whole').text)
#
#     print(k, asin, point, price)

def to_asin(session: requests.session, headers, proxies, item_name):
    url = f"https://www.google.com/search?q=amazon+{'+'.join(item_name.split(' '))}&hl=ja"
    soup = BeautifulSoup(session.get(url, headers=headers, proxies=proxies).text, 'html.parser')

    # print(soup)
    a_s = soup.find_all('a')
    asin = ''
    for a in a_s:
        if 'href' in a.attrs and 'amazon.co' in a['href']:
            try:
                asin = a['href'].split('/dp/')[1][:10]
                break
            except:
                pass

    return asin


def google_to_asin(item_ids, sleep, log_class: LogClass):
    headers = {
        "referer":"referer: https://www.google.com/",
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
    }

    session = requests.session()
    url = f"https://www.google.com/search?q=fitness+wear&hl=ja"

    for i, id_ in enumerate(item_ids):
        proxies = get_random_proxy()
        session.post(url, proxies=proxies, headers=headers)

        log_class.id_price_and_names[id_]['asin'] = to_asin(session, headers, proxies, log_class.id_price_and_names[id_]['name'])

        log_class.increment('ASIN検索中')

        if i != len(item_ids):
            time.sleep(random.uniform(sleep[0], sleep[1]))

#####################################################


def get_max_page_num(url):
    url = set_url(url)

    soup = get_soup(url)

    if soup:
        try:
            return int(soup.find(class_='bcs_last').text)
        except:
            pass

    return 1


# distribute urls & pages w.r.t. threads num
# return [ [[url, from_index, to_index], [url, from_index, to_index],...], [] ]
def distribute(url_and_max_pages: list, thread_num: int):
    total_page_nums = sum([val[1] for val in url_and_max_pages])
    single_thread_page_num = total_page_nums // thread_num
    res = [[] for i in range(thread_num)]

    if single_thread_page_num == 0:
        index = 1
        for val in url_and_max_pages:
            for i in range(1, val[1] + 1):
                res[index] = [[val[0], i, i]]
                index += 1
        # res[0] = [[val[0], 1, val[1]] for val in url_and_max_pages]
        return res

    current_index = 0
    current_to_page_index = 0
    for i in range(thread_num):

        if i == thread_num - 1:
            res[i].append(
                [url_and_max_pages[current_index][0],
                 current_to_page_index + 1,
                 url_and_max_pages[current_index][1]
                 ]
            )
            if current_index < len(url_and_max_pages) - 1:
                res[i].extend([[[val[0], 1, val[1]] for val in url_and_max_pages[current_index + 1:]]])
        else:
            temp = 0
            while temp != single_thread_page_num:
                url = url_and_max_pages[current_index][0]
                max_page = url_and_max_pages[current_index][1]
                diff = max_page - current_to_page_index

                if temp + diff <= single_thread_page_num:
                    res[i].append([url, current_to_page_index + 1, max_page])
                    temp += diff
                    current_to_page_index = 0
                    current_index += 1
                else:
                    current_temp = current_to_page_index
                    current_to_page_index = current_to_page_index + single_thread_page_num - temp
                    res[i].append([url, current_temp + 1, current_to_page_index])
                    temp = single_thread_page_num

    return res


def split(a, n):
    k, m = divmod(len(a), n)
    return list((a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)))


def main(urls, print_func, print_func_back):
    user_info = get_info()
    thread_num = user_info['thread_num']
    sleep_time: list = user_info['sleep']
    keepa_key = user_info['keepa']
    log_class = LogClass(thread_num, print_func, print_func_back)

    url_and_max_pages = []
    zero_item_urls = []
    total_page = 0

    log_class.log_print('全スクレイピングページ数取得中・・・')

    for url in urls:
        max_page = get_max_page_num(url)

        if max_page != 0:
            url_and_max_pages.append([url, max_page])
            total_page += max_page
        else:
            zero_item_urls.append(url)

    log_class.total_pages = total_page
    log_class.log_print(f'全{total_page}ページをスクレイピングします。')

    distributed_u_p = distribute(url_and_max_pages, thread_num)

    threads = []

    log_class.log_print('販売終了取得', False)
    for u_p in distributed_u_p:
        threads.append(threading.Thread(
            target=single_step_item_ids,
            kwargs={
                "url_and_pages": u_p,
                "log_class": log_class,
                "sleep": sleep_time,
            }
        ))

    for thread in threads:
        thread.start()
        time.sleep(1)
    for thread in threads:
        thread.join()

    log_class.item_ids = list(dict.fromkeys(log_class.item_ids))
    log_class.log_print(f'{len(log_class.item_ids)}件見つかりました。\n在庫を確認します。')
    split_item_ids = split(log_class.item_ids, thread_num)
    log_class.total_pages = len(log_class.item_ids)
    log_class.counter = 0

    threads = []
    log_class.log_print('在庫確認中', False)
    for item_ids in split_item_ids:
        threads.append(threading.Thread(
            target=single_step_item_availabilities,
            kwargs={
                "ids": item_ids,
                "log_class": log_class,
                "sleep": sleep_time,
            }
        ))
    for thread in threads:
        thread.start()
        time.sleep(1)
    for thread in threads:
        thread.join()

    log_class.log_print(f'在庫がある商品が{len(log_class.available_ids)}件見つかりました。')

    with open(result_csv_path, 'w', encoding='shift-jis', newline='') as f:
        csv.writer(f).writerow(['ビックカメラリンク', '商品名', '価格'])

        for key in log_class.available_ids:
            if key in log_class.id_price_and_names.keys():
                try:
                    log_class.id_price_and_names[key]['link'] = f'https://www.biccamera.com/bc/item/{key}/'
                    name = log_class.id_price_and_names[key]['name']
                    price = log_class.id_price_and_names[key]['price']
                    csv.writer(f).writerow([f'https://www.biccamera.com/bc/item/{key}/', name, price])
                except:
                    pass

    log_class.counter = 0
    log_class.total_pages = len(log_class.available_ids)
    split_ids = split(log_class.available_ids, thread_num)
    threads = []
    log_class.log_print('Asin変換中', False)
    for item_ids in split_ids:
        threads.append(
            threading.Thread(
                target=google_to_asin,
                kwargs={
                    "item_ids": item_ids,
                    "log_class": log_class,
                    "sleep": sleep_time
                }
            )
        )
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    api = keepa.Keepa(accesskey=keepa_key)
    temp_asin_list = []
    print_func('Asinから価格取得中・・・')
    for i, id_ in enumerate(log_class.available_ids):
        print_func_back(f'ASINから価格取得中・・・{i + 1}/{len(log_class.available_ids)}')
        asin = log_class.id_price_and_names[id_]['asin']
        if asin:
            temp_asin_list.append(asin)

        if len(temp_asin_list) == 10:
            results = api.query(temp_asin_list, domain='JP', wait=True)

            for res in results:
                try:
                    price = res['csv'][1][-1]
                    category = res['categoryTree'][0]['name']
                    for key in log_class.id_price_and_names.keys():
                        if log_class.id_price_and_names[key]['asin'] == res['asin']:
                            log_class.id_price_and_names[key]['amazon_price'] = price
                            if category in price_fee_list.keys():
                                log_class.id_price_and_names[key]['amazon_fee'] = price_fee_list[category]
                                log_class.id_price_and_names[key]['category'] = category
                            else:
                                log_class.id_price_and_names[key]['amazon_fee'] = 15
                                log_class.id_price_and_names[key]['category'] = 'その他のカテゴリー'
                except:
                    pass
            temp_asin_list = []

    if temp_asin_list:
        results = api.query(temp_asin_list, domain='JP', wait=True)

        for res in results:
            try:
                price = res['csv'][1][-1]
                category = res['categoryTree'][0]['name']
                for key in log_class.id_price_and_names.keys():
                    if log_class.id_price_and_names[key]['asin'] == res['asin']:
                        log_class.id_price_and_names[key]['amazon_price'] = price
                        if category in price_fee_list.keys():
                            log_class.id_price_and_names[key]['amazon_fee'] = price_fee_list[category]
                            log_class.id_price_and_names[key]['category'] = category
                        else:
                            log_class.id_price_and_names[key]['amazon_fee'] = 15
                            log_class.id_price_and_names[key]['category'] = 'その他のカテゴリー'
            except:
                pass

    with open(result_csv_path, 'w', encoding='shift-jis', newline='') as f:
        csv.writer(f).writerow(['ビックカメラリンク', '商品名', '価格', 'Amazon商品リンク', 'ASIN', 'Amazon価格', 'Amazonカテゴリ', '販売手数料', '利益'])
        for key in log_class.available_ids:
            temp = log_class.id_price_and_names[key]
            to_add = [temp['link'], temp['name'], temp['price'], f'https://www.amazon.co.jp/dp/{temp["asin"]}' if temp['asin'] else ''
                , temp['asin']]
            if 'amazon_price' in temp.keys():
                to_add.append(temp['amazon_price'])
                to_add.append(temp['category'])
                to_add.append(temp['amazon_fee'])
                try:
                    price = int(re.sub('\\D', '', temp['price']))
                    profit = int(price - price * 0.1 - temp['amazon_price'] - temp['amazon_price'] * temp['amazon_fee'] / 100)
                    to_add.append(profit)
                except:
                    to_add.append('')
            else:
                to_add.append('')
                to_add.append('')

            csv.writer(f).writerow(to_add)

    if log_class.available_ids:
        print_func('メールを送信します。')
        send_mail()
        print_func('送信完了')
    else:
        print_func('在庫のある商品が見つかりませんでした。\n動作を終了します。')


# log = LogClass(1, print, print)
# get_item_ids('https://www.biccamera.com/bc/category/?q=asus', log)
# print(get_availability('3126502', log))