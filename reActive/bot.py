# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
from time import sleep
import datetime
import requests

from botbuilder.core import ActivityHandler, CardFactory, TurnContext
from botbuilder.schema import Activity, ChannelAccount


def now():
    """
    :return: str now
    """
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def delta_datetime(dt):
    delta = datetime.datetime.now() - datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    return delta.seconds

def send_db(value, label, user_type, conv_id, message_id, user_id):
    data = {'value': value, 'label': label, 'user_type': user_type, 'user_id': user_id,
            "conv_id": conv_id, "message_id": message_id, 'timestamp': now()}
    requests.post(
        'http://piosow.pythonanywhere.com/api/add_log_data', json=data)


class MyBot(ActivityHandler):
    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.

    async def on_message_activity(self, turn_context: TurnContext):
        c_id = turn_context.activity.conversation.id

        if turn_context.activity.text == '\\start':
            with open('cards/react_panel.json', 'r', encoding="utf-8") as card_f:
                card = CardFactory.adaptive_card(json.load(card_f))
                await turn_context.send_activity(Activity(attachments=[card]))
        elif turn_context.activity.text is None and len(turn_context.activity.value) > 0:
            if turn_context.activity.value.get('quick_quiz', None) != None:
                send_db(turn_context.activity.value['quick_quiz'],
                        'answer', 'user', c_id, turn_context.activity.id, turn_context.activity.from_property.id)
                req = requests.post(f'http://piosow.pythonanywhere.com/api/pollsincebot?chatid={c_id}').text
                if req != 'EMPTY SET' and req[0] != '<':
                    try:
                        result = json.loads(req)
                    except json.JSONDecodeError:
                        result = []
                        print('coś padło')
                else:
                    result = []
                    print('pusty zbiór')
                am = {i: 0 for i in ["A","B","C","D"]}
                for i in result:
                    am[i['value']] += 1
                suma = sum(am.values())
                text = "## Wyniki:\n  "
                if suma > 0:
                    text += "  \n".join(
                        [f'{round(i[1]/suma, 2)*100}% osób zagłosowało za "{i[0]}"' for i in am.items() if i[1]>0])
                text += f'  \nŁącznie zagłosowało {suma} {"osoba"*(suma==1)+"osoby"*(suma in [2,3,4])+"osób"*(suma>4 or suma==0)}'
                await turn_context.send_activity(text)
            elif turn_context.activity.value.get('pytanie', None) != None:
                pytanie = turn_context.activity.value['pytanie']
                odpowiedzi = {"A": turn_context.activity.value['quickanswer_A'], "B": turn_context.activity.value['quickanswer_B'],
                              "C": turn_context.activity.value['quickanswer_C'], "D": turn_context.activity.value['quickanswer_D']}
                odpowiedzi = {i: odpowiedzi[i] for i in odpowiedzi.keys(
                ) if odpowiedzi[i].strip() != ''}
                with open('cards/poll.json', 'r', encoding="utf-8") as card_f:
                    card_text = card_f.read()
                card_text = card_text.replace("PYTANIE PLC", pytanie)
                ans = ""
                for i in odpowiedzi.keys():
                    ans += '{"title": "x: PLACEHOLDER","value": "x"},'.replace(
                        "x", i).replace("PLACEHOLDER", odpowiedzi[i])
                card_text = card_text.replace("ODP_PLC", ans[:-1])
                card = CardFactory.adaptive_card(json.loads(card_text))
                act = Activity(attachments=[card])
                res = await turn_context.send_activity(act)
                with open('cards/react_panel.json', 'r', encoding="utf-8") as card_f:
                    card = CardFactory.adaptive_card(json.load(card_f))
                await turn_context.send_activity(Activity(attachments=[card]))
                send_db('', 'ankieta', 'bot', c_id, res.id, 'bot')
            elif turn_context.activity.value.get('reakcja', None) != None:
                req = requests.post(
                    f"http://piosow.pythonanywhere.com/api/lastbotfbf?chatid={c_id}").text
                if req != 'EMPTY SET':
                    try:
                        last = json.loads(req)
                        am = json.loads(last['value'])
                    except json.JSONDecodeError:
                        am = {"Tak": 0, "Nie": 0, "Nie rozumiem": 0,
                              "Mam pytanie": 0, "Zaraz wracam": 0}
                        print('coś padło')
                    if delta_datetime(last['timestamp'])>15:
                        am = {"Tak": 0, "Nie": 0, "Nie rozumiem": 0,
                              "Mam pytanie": 0, "Zaraz wracam": 0}
                else:
                    am = {"Tak": 0, "Nie": 0, "Nie rozumiem": 0,
                          "Mam pytanie": 0, "Zaraz wracam": 0}
                am[turn_context.activity.value['reakcja']] += 1
                reacts = json.dumps(am)
                text = "## Otrzymany feedback\n  " + \
                    "  \n".join(
                        [f'{i[1]} os{"oba zareagowała"*(i[1]==1)+"oby zareagowały"*(i[1]in [2,3,4])+"ób zareagowało"*(i[1]>4)} "{i[0]}"' for i in am.items() if i[1] > 0])
                res = await turn_context.send_activity(text)
                send_db(reacts, 'feedback', 'bot', c_id, res.id, 'bot')

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Aby mnie uruchomić wpisz `\\start` :)")
