# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
from time import sleep

from botbuilder.core import ActivityHandler, CardFactory, TurnContext
from botbuilder.schema import Activity, ChannelAccount


class MyBot(ActivityHandler):
    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.

    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.text == '\\start':
            with open('cards/react_panel.json', 'r', encoding="utf-8") as card_f:
                card = CardFactory.adaptive_card(json.load(card_f))
                await turn_context.send_activity(Activity(attachments=[card]))
        elif turn_context.activity.text is None and len(turn_context.activity.value) > 0:
            if turn_context.activity.value.get('ankieta', None) != None:
                # wrzucenie odpowiedzi na serwer
                pass
            elif turn_context.activity.value.get('admin', None) != None:
                if turn_context.activity.value['admin'] == 'ankieta':
                    # kod do generowania odpowiedzi w ankiecie
                    am = {"Tak": 0, "Nie": 0, "Mordo ja sam nie wiem": 0, "Andrzeeej": 0, "Łazanki": 0}
                    with open('cards/poll.json', 'r', encoding="utf-8") as card_f:
                        card = CardFactory.adaptive_card(json.load(card_f))
                        act = Activity(attachments=[card])
                    await turn_context.send_activity(act)
                    sleep(60)
                    # zbieranie wyników
                    text = "## Statystyki dla ostatnich x minut:\n  " + \
                    "  \n".join([f'{i[1]} osób zareagowało "{i[0]}"' for i in am.items()])
                    reacts = ";".join([str(i[1]) for i in am.items()])
                    act = Activity(text=text, id=act.id)
                    await turn_context.update_activity(act)
            elif turn_context.activity.value.get('reakcja', None) != None:
                # TODO: sprawdzanie ilości reakcji w ciągu ostatniego x czasu
                am = {"Tak": 0, "Nie": 0, "Nie rozumiem": 0,
                      "Mam pytanie": 0, "Zaraz wracam": 0}
                am[turn_context.activity.value['reakcja']] += 1
                text = "## Otrzymany feedback\n  " + \
                    "  \n".join([f'{i[1]} os{"oba"*(i[1]==1)+"oby"*(i[1]in [2,3,4])+"ób"*(i[1]>4)} zareagowało "{i[0]}"' for i in am.items() if i[1] > 0])
                if sum(am.values()) > 1:
                    await turn_context.update_activity(Activity(text=text, label='feedback')) # TODO: dodać id
                else:
                    await turn_context.send_activity(Activity(text=text, label='feedback'))

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")
