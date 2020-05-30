# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import ActivityHandler, TurnContext, CardFactory
from botbuilder.schema import ChannelAccount, Activity
import json


class MyBot(ActivityHandler):
    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.

    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.text == '\\start':
            with open('sample.json', 'r', encoding="utf-8") as card_f:
                card = CardFactory.adaptive_card(json.load(card_f))
                await turn_context.send_activity(Activity(attachments=[card]))
        elif turn_context.activity.text == None and len(turn_context.activity.value['reakcja'])>1:
            await turn_context.send_activity("1 osoba zareagowała: "+turn_context.activity.value['reakcja'])

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")
