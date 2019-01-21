# импортируем flack и запускаем Web сервер
from flask import Flask, abort, request
import json
import requests
import re
from pprint import pprint
import datetime
from time import sleep

#Задаем константы

url = "http://10.100.1.104"
headers = {'Authorization': "Basic YWRtaW46QzFzY28xMjM=", 'Cache-Control': "no-cache"}
querystring = {"location":"/Status/UserInterface/Extensions"}

#Считываем переменные с кодека

def sturtupval():
    global url
    response = requests.request("GET", url + "/getxml", headers=headers, params=querystring)
    widgets = re.findall(r'<WidgetId>(\w+)', response.text)
#    print(" ".join(str(x) for x in widgets))
    windget_val = {}
    for item in widgets:
        Value = re.findall(r'<Value>(\w*)', response.text)
        if Value[widgets.index(item)] == "":
            windget_val[item] = 0
        else:
            windget_val[item] = Value[int(widgets.index(item))]
    return windget_val

windget_val = sturtupval()
# print(" ".join(str(x) for x in windget_val.items()))

server = Flask(__name__)
# декоратор
@server.route('/drinks', methods=['POST'])

def drinks():
    global windget_val
    drinks = {"tea_wgt": "чай черный", "tgrn_wgt": "чай зеленый", "cof_wgt": "кофе черный", "capp_wgt": "кофе капучино"}
    print(drinks.keys())
    if not request.json:
        abort(400)
    parsed_request = request.json
    pprint(parsed_request)
    drink = (parsed_request['Event']['UserInterface']['Extensions']['Event']['Clicked']['Signal']['Value']).split(":")
    pprint(drink)
    if drink[0] == "tgrn_wgt" or drink[0] == "cof_wgt" or drink[0] == "capp_wgt" or drink[0] == "tea_wgt":
        if len(drink) > 1:
            if drink[1] == 'increment':
                windget_val[drink[0]] = int(windget_val[drink[0]]) + 1
                setwidget(drink[0], str(windget_val[drink[0]]))
            elif drink[1] == 'decrement' and int(windget_val[drink[0]]) > 0:
                windget_val[drink[0]] = int(windget_val[drink[0]]) - 1
                setwidget(drink[0], str(windget_val[drink[0]]))
    elif drink[0] == 'order_wgt' and summ () > 0:

        newpayload = "Добрый день! Пожалуйста, принесите для наших гостей в шоурум следующие напитки: \n"
        for item in windget_val.keys():
            if item == "tgrn_wgt" or item == "cof_wgt" or item == "capp_wgt" or item == "tea_wgt" and int(windget_val[item]) > 0:
                print(item)
                print(drinks[item])
                newpayload = newpayload + drinks[item] + " -" + str(windget_val[item]) + "\n"
                setwidget(item, "0")
                windget_val[item] = int(0)
        post2tproom("Заказ отправлен", "Пожалуйста, подождите подтверждения заказа")
        post2spark(newpayload)
        person = check2spark()
        print (person)
        post2tproom("Заказ принят - " + person, "Ваш заказ подтвержден. ID сотрудника подтвердившего заказ - " + person)
        post2spark("Спасибо!")

    pprint(windget_val)

    return 'ok'

def register_webhook():
    global url

    payload = "<Command>\r\n   <HttpFeedback>\r\n      <Register>\r\n         <FeedbackSlot>1</FeedbackSlot>\r\n         <ServerUrl>http://10.100.1.104:5000/drinks</ServerUrl>\r\n         <Format>JSON</Format>\r\n         <Expression item=\"1\">event/userinterface/extensions/event/Clicked</Expression>\r\n      </Register>\r\n   </HttpFeedback>\r\n</Command>"

    headers = {
        'content-type': "text/xml",
        'authorization': "Basic YWRtaW46QzFzY28xMjM=",
        'cache-control': "no-cache"
    }

    requests.request("POST", url + "/putxml", data=payload, headers=headers)

def setwidget(name,value):
    global url
    payload = "<Command>\n<UserInterface>\n<Extensions>\n<Widget>\n<SetValue>\n<WidgetId>" + name + "</WidgetId>\n<Value>" + value + "</Value>\n</SetValue>\n</Widget>\n</Extensions>\n</UserInterface>\n</Command>"
    headers = {
    'Content-Type': "text/xml",
    'Authorization': "Basic YWRtaW46QzFzY28xMjM=",
    'Cache-Control': "no-cache"
    }
    requests.request("POST", url + "/putxml", data=payload, headers=headers)

# Это функция, которая передает сообщение в комнату spark
def post2spark(message):

    url = "https://api.ciscospark.com/v1/messages"
    roomId = 'Y2lzY29zcGFyazovL3VzL1JPT00vZGVkNTZmZTAtMGNhZi0xMWU4LWE5NzctNjFjMmI3NjNlOWQ3'
    token = 'ZTIxZjE3ZGMtMTdkNS00MmNkLWI3YjItZmZjNmIxNjEyY2RkYjdhMjA1NDMtMGJk'

    payload = {'roomId': roomId,
                 'text': message
        }

    headers = {
        'Authorization': "Bearer ZTIxZjE3ZGMtMTdkNS00MmNkLWI3YjItZmZjNmIxNjEyY2RkYjdhMjA1NDMtMGJk",
        'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
        'Cache-Control': "no-cache"
        }

    response = requests.request("POST", url, data=payload, headers=headers)

    print (response.json())

# Это функция, которая передает сообщение о статусе заказа на сенсорную панель и экран видеосистемы

def post2tproom(message, message4screen):
    global url
    payload1 = "<Command>\n<UserInterface>\n<Extensions>\n<Widget>\n<SetValue>\n<WidgetId>stat_wgt</WidgetId>\n<Value>" + message + "</Value>\n</SetValue>\n</Widget>\n</Extensions>\n</UserInterface>\n</Command>"
    data1_to_send = payload1.encode("utf-8")
    payload2 ="<Command>\r\n<UserInterface>\r\n<Message>\r\n\t<Alert>\r\n\t<Display>\r\n\t\t<Duration>10</Duration>\r\n\t\t<Text>" + message4screen +  "</Text>\r\n\t</Display>\r\n</Alert>\r\n</Message>\r\n</UserInterface>\r\n</Command>"
    data2_to_send = payload2.encode("utf-8")
    headers = {
    'Content-Type': "text/xml",
    'Authorization': "Basic YWRtaW46QzFzY28xMjM=",
    'Cache-Control': "no-cache"
    }
    r=requests.request("POST", url + "/putxml", data=data1_to_send, headers=headers)
    print(r.text)
    r=requests.request("POST", url + "/putxml", data=data2_to_send, headers=headers)
    print(r.text)

# Эта функция проверяет ответ "ok" или "ок"в Spark комнате:

def check2spark():

    timestart = datetime.datetime.now()

    url = "https://api.ciscospark.com/v1/messages"

    querystring = {"mentionedPeople": "me",
                   "roomId": "Y2lzY29zcGFyazovL3VzL1JPT00vZGVkNTZmZTAtMGNhZi0xMWU4LWE5NzctNjFjMmI3NjNlOWQ3",
                   "max": 1}

    headers = {
        'Authorization': "Bearer ZTIxZjE3ZGMtMTdkNS00MmNkLWI3YjItZmZjNmIxNjEyY2RkYjdhMjA1NDMtMGJk",
    }

    sparktime = timestart - datetime.timedelta(seconds=2)

    answer = ["ок","ok"]
    userinput = False

    while not userinput or timestart > sparktime:
        if not userinput:
            print ("Первое условие выполнено")
        if timestart > sparktime:
            print("второе условие выполнено")

        sleep(5)
        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            print(response.status_code)
            if response.status_code == 200:
                print(response.json())
                timelist = response.json()['items'][0]['created'].split('T')[1].split(':')
                datelist = response.json()['items'][0]['created'].split('T')[0].split('-')
                y = int(datelist[0])
                m = int(datelist[1])
                d = int(datelist[2])
                hr = int(timelist[0]) + 3
                min = int(timelist[1])
                sec = int(timelist[2][:-5])
                sparktime = sparktime.replace(year=y, month=m, day=d, hour=hr, minute=min, second=sec, microsecond=0)
                print(timestart)
                print(sparktime)
                text = response.json()['items'][0]['text']
                for i in answer:
                    if i in text:
                        userinput = True
                    else:
                        userinput = False
                print(response.json()['items'][0]['text'])
                person = response.json()['items'][0]['personEmail']

            elif response.status_code == 429:
                print(response.headers['Retry-After'])
        except requests.exceptions.RequestException as e:
            print(e)
    return person

def summ ():
    global windget_val
    type (windget_val["capp_wgt"])
    windget_valsumm = int(windget_val["capp_wgt"]) + int(windget_val["cof_wgt"]) + int(windget_val["tea_wgt"]) + int(windget_val["tgrn_wgt"])
    type(windget_valsumm)
    type(0)
    type("00000")
    pprint("Это сумма:  " + str(windget_valsumm))
    return windget_valsumm


register_webhook()

if __name__ == '__main__':

    server.run(host='0.0.0.0', port=5000, debug=False)
