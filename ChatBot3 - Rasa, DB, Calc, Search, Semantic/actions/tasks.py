from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from database import UserDatabase
import json


class ActionAddTask(Action):
    def name(self) -> Text:
        return "action_add_task"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        task = next(tracker.get_latest_entity_values("task"), None)
        user_db = UserDatabase()

        try:
            user_data = user_db.get_user(tracker.sender_id) or {}
            tasks = json.loads(user_data.get("tasks", "[]"))
            tasks.append(task)
            user_db.save_user({"user_id": tracker.sender_id, "tasks": json.dumps(tasks)})
            dispatcher.utter_message(text=f"Задача '{task}' добавлена!")
        except Exception as e:
            dispatcher.utter_message(text=f"Ошибка при сохранении задачи: {str(e)}")
        finally:
            user_db.close()

        return []


class ActionListTasks(Action):
    def name(self) -> Text:
        return "action_list_tasks"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_db = UserDatabase()
        try:
            user_data = user_db.get_user(tracker.sender_id) or {}
            tasks = json.loads(user_data.get("tasks", "[]"))

            if not tasks:
                dispatcher.utter_message(text="Список задач пуст")
            else:
                task_list = "\n".join(f"{i + 1}. {task}" for i, task in enumerate(tasks))
                dispatcher.utter_message(text=f"Ваши задачи:\n{task_list}")

        except Exception as e:
            dispatcher.utter_message(text=f"Ошибка при загрузке задач: {str(e)}")
        finally:
            user_db.close()

        return []


class ActionDeleteTask(Action):
    def name(self) -> Text:
        return "action_delete_task"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        task_id = next(tracker.get_latest_entity_values("task_id"), None)
        user_db = UserDatabase()

        try:
            user_data = user_db.get_user(tracker.sender_id) or {}
            tasks = json.loads(user_data.get("tasks", "[]"))

            if task_id == "все":
                tasks = []
            elif task_id and task_id.isdigit():
                index = int(task_id) - 1
                if 0 <= index < len(tasks):
                    del tasks[index]

            user_db.save_user({"user_id": tracker.sender_id, "tasks": json.dumps(tasks)})
            dispatcher.utter_message(response="utter_task_deleted")

        except Exception as e:
            dispatcher.utter_message(text=f"Ошибка: {str(e)}")
        finally:
            user_db.close()

        return []