import threading
import queue
import time
import random
import json
from datetime import datetime
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    COOKING = "cooking"
    READY = "ready"
    COMPLETED = "completed"

class OrderSystem:
    def __init__(self):
        # сигнал, что кухня готова к работе (типа ресторан открывается)
        self.kitchen_ready = threading.Event()

        # для управления доступом к плите (ограниченное количество мест)
        self.stove_condition = threading.Condition()
        self.available_stoves = 2  # всего 2 конфорки :( Мы бедный ресторан

        # очередь заказов
        self.order_queue = queue.Queue(maxsize=10)

        # статистика
        self.stats = {
            "total_orders": 0,
            "completed_orders": 0,
            "failed_orders": 0,
            "cooking_time_total": 0
        }
        self.stats_lock = threading.Lock()

        # флаг работы системы
        self.system_running = False

        # потоки
        self.producers = []
        self.consumers = []
        self.monitor_thread = None

    # функция подготовки кухни, при открытии ресторана, кухня сначала готовится
    def kitchen_preparation(self):
        print("ПОВАР: Начинаю подготовку кухни...")

        # имитация подготовки
        tasks = [
            "Проверяю оборудование",
            "Настраиваю температуру плит",
            "Подготавливаю ингредиенты",
            "Запускаю вытяжку",
            "Натираю приборы"
        ]

        # TODO: Выполняем подготовительные действия и сообщаем поварам и официантам "ОТКРЫВАЕМСЯ!!!"
        for task in tasks:
            print(f"ПОВАР: {task}")
            time.sleep(1)
        
        print("ПОВАР: Кухня готова! ОТКРЫВАЕМСЯ!")
        self.kitchen_ready.set()


    # функция для генерации заказов (то есть наши официанты). Не забываем, что ресторан должен быть открыт!
    def order_producer(self, producer_id):
        menu_items = [
            # придумайте пулл блюд, с которыми будут генерироваться заказы
            "Пицца Маргарита", "Паста Карбонара", "Стейк Рибай", "Салат Цезарь", "Бургер Делишес", "Суп Том-Ям", 
            "Тако с говядиной", "Греческий салат", "Суши Филадельфия", "Рамен с говядиной"
        ]

        while self.system_running:
            self.kitchen_ready.wait()
            order = {
                "order_id": random.randint(1000, 9999),
                "customer_id": random.randint(1, 100),
                "dish": random.choice(menu_items),
                "complexity": random.randint(1, 5),  # сложность приготовления 1-5
                "status": OrderStatus.PENDING.value,
                "created_time": datetime.now(),
                "producer_id": producer_id
            }

            # TODO: Официант принимает заказ (мы его генерируем), отправляет поварам (не забываем про подсчет статистики)
            self.order_queue.put(order)
            print(f"ОФИЦИАНТ - {producer_id}, принял заказ {order['order_id']}")
            with self.stats_lock:
                self.stats["total_orders"] += 1

            time.sleep(random.uniform(0.5, 2))

    # функция для обработки заказов (наши поварята) - повар спрашивает повара... Не забываем, что ресторан должен быть открыт!
    def chef_consumer(self, chef_id):
        # TODO: Повар забирает заказ, проверяет есть ли свободная конфорка (если нет, то ждет, естественно), готовит по
        #  длительности в зависимости от сложности блюда cook_time = order["complexity"] * 0.5. Не забываем про статистику и статусы блюд!
        while self.system_running:
            self.kitchen_ready.wait()

            #получаем заказ
            try:
                order = self.order_queue.get(timeout=1)
            except queue.Empty:
                continue

            order["status"] = OrderStatus.COOKING.value
            order["chef_id"] = chef_id
            start_cooking = datetime.now()

            #занимаем конфорку
            with self.stove_condition:
                while self.available_stoves == 0 and self.system_running:
                    self.stove_condition.wait(timeout=1)

            if not self.system_running: 
                break

            self.available_stoves -= 1
            
            print(f"ПОВАР {chef_id}: Занял комфорку и начинаю готовить заказ №{order["order_id"]}")
            
            #готовим заказ
            if self.system_running:
                cooking_time = order["complexity"] * 0.5
                time.sleep(cooking_time)

                order["status"] = OrderStatus.READY.value
                end_cooking = datetime.now()

                print(f"ПОВАР {chef_id}: заказ №{order["order_id"]} готов! Освобождаю конфорку...")

            #освобождаем конфорку
            with self.stove_condition:
                self.available_stoves += 1
                self.stove_condition.notify_all()
            
            #обновляем статистику
            with self.stats_lock:
                self.stats["completed_orders"] += 1
                self.stats["cooking_time_total"] += (end_cooking - start_cooking).total_seconds()

            self.order_queue.task_done()
            
    
    # Функция для демон-потока
    def monitoring(self):

        # TODO: Если рестик работает, каждые 5 секунд забираем статистику по параметрам:
        #  "Всего заказов",
        #  "Выполнено",
        #  "В очереди",
        #  "Среднее время приготовления блюд",
        #  "Количество свободных конфорок" и записываем статистику в файл со временем когда эта статистика была записана
        while self.system_running:
            time.sleep(5)
            self.kitchen_ready.wait()
            with self.stats_lock:
                total_orders = self.stats["total_orders"]
                completed_orders = self.stats["completed_orders"]
                cooking_time_total = self.stats["cooking_time_total"]
        
            average_time = (cooking_time_total / completed_orders) if completed_orders > 0 else 0

            in_queue = self.order_queue.qsize()
            free_stoves = self.available_stoves

            timestamp = datetime.now().strftime("%H:%M:%S")
            log_mes = f"[{timestamp}] [{total_orders}] [{in_queue}] [{average_time}] [{free_stoves}]\n"
            with open('restaurant_logs.txt', 'a', encoding="utf-8") as f:
                f.write(log_mes)
            

    def start_system(self):
        print("ЗАПУСК СИСТЕМЫ РЕСТОРАНА...")

        # TODO: Запускаем нашу подготовку ресторана в отдельном потоке, ждем завершения и запускаем официантов и
        #  поваров, а также нашего демон-потока для статистики
        self.system_running = True

        preparation_thread = threading.Thread(target = self.kitchen_preparation)
        preparation_thread.start()
        preparation_thread.join()

        for i in range(3):
            producer_thread = threading.Thread(target = self.order_producer, args = (i + 1,))
            self.producers.append(producer_thread)
            producer_thread.start()

        for i in range(2):
            consumer_thread = threading.Thread(target = self.chef_consumer, args = (i + 1,))
            self.consumers.append(consumer_thread)
            consumer_thread.start()
        
        self.monitor_thread = threading.Thread(target=self.monitoring, daemon=True)
        self.monitor_thread.start()

    def stop_system(self):
        print("ЗАКРЫТИЕ РЕСТОРАНА...")

        # TODO: ждем когда все освободятся, выводим в консоль итоги рабочего дня:
        #  "Всего принято заказов",
        #  "Успешно выполнено",
        #  "Среднее время приготовления
        self.system_running = False

        time.sleep(0.5)

        for i in self.producers:
            i.join()

        for j in self.consumers:
            j.join()
        
        with self.stats_lock:
            total_orders = self.stats["total_orders"]
            completed_orders = self.stats["completed_orders"]
            cooking_time_total = self.stats["cooking_time_total"]

        average_time = (cooking_time_total / completed_orders) if completed_orders > 0 else 0

        print("ИТОГИ РАБОЧЕГО ДНЯ:")
        print(f"Всего принято заказов: {total_orders}")
        print(f"Успешно выполнено: {completed_orders}")
        print(f"Среднее время приготовления: {average_time:.2f} сек")

        print("РЕСТОРАН ЗАКРЫТ!")


# Запуск системы
if __name__ == "__main__":
    restaurant = OrderSystem()

    try:
        restaurant.start_system()

        # работаем 60 секунд
        time.sleep(30)

        restaurant.stop_system()

    except KeyboardInterrupt:
        print("!ЭКСТРЕННОЕ ЗАКРЫТИЕ!")
        restaurant.stop_system()