from typing import Any, Text, Dict, List
from rasa_sdk.events import FollowupAction  # Добавьте эту строку
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import requests
import logging

logger = logging.getLogger(__name__)


class ActionAskFromCurrency(Action):
    """Запрос исходной валюты"""

    def name(self) -> Text:
        return "action_ask_from_currency"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_ask_from_currency")
        return []


class ActionAskToCurrency(Action):
    """Запрос целевой валюты"""

    def name(self) -> Text:
        return "action_ask_to_currency"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_ask_to_currency")
        return []


class ActionConvertCurrency(Action):
    """Основная логика конвертации"""

    def name(self) -> Text:
        return "action_convert_currency"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Извлекаем параметры
        amount = next(tracker.get_latest_entity_values("amount"), None)
        from_curr = tracker.get_slot("from_currency")
        to_curr = tracker.get_slot("to_currency")

        try:
            amount = float(amount)  # Добавляем проверку числа
            if amount <= 0:
                raise ValueError("Сумма должна быть положительной")

            # Проверяем коды валют через API
            currencies = requests.get("https://api.exchangerate.host/symbols").json()
            if from_curr not in currencies['symbols'] or to_curr not in currencies['symbols']:
                raise ValueError("Неверный код валюты")

            # Проверка обязательных параметров
            if not amount:
                dispatcher.utter_message(text="Укажите сумму для конвертации")
                return []

            if not from_curr:
                return [SlotSet("amount", amount), FollowupAction("action_ask_from_currency")]

            if not to_curr:
                return [SlotSet("amount", amount),
                        SlotSet("from_currency", from_curr),
                        FollowupAction("action_ask_to_currency")]

            # Конвертация через API
            response = requests.get(
                f"https://api.exchangerate.host/convert?from={from_curr}&to={to_curr}&amount={amount}",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    result = f"{amount} {from_curr} = {round(data['result'], 2)} {to_curr}"
                    return [SlotSet("result", result)]

            dispatcher.utter_message(response="utter_currency_error")
            return [SlotSet("result", None)]


        except ValueError as e:

            dispatcher.utter_message(text=str(e))

            return [SlotSet("result", None)]

        except Exception as e:

            logger.error(f"API Error: {str(e)}")

            dispatcher.utter_message(response="utter_currency_error")

            return [SlotSet("result", None)]