import asyncio
from websockets import c
import json
import requests

# TronGrid HTTP API для начального баланса
HTTP_API_URL = "https://api.trongrid.io"
WS_API_URL = "wss://api.trongrid.io/v1/events"
ADDRESS = "TPXauFLfM89qAosiagcGT6WiYtGc8zqdQY"  # Укажите ваш Tron-адрес
API_KEY = "c3f785b3-1946-44d6-9a41-598cf0cf4241"  # Добавьте API-ключ, если используется платный доступ TronGrid

# Функция для получения начального баланса
def get_wallet_balance(address):
    url = f"{HTTP_API_URL}/v1/accounts/{address}"
    
    if API_KEY:
        headers = {
            "Authorization": f"Bearer {API_KEY}"
        }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data["data"]:
            return int(data["data"][0]["balance"]) / 1e6  # Баланс в TRX
    else:
        print(f"Ошибка API: {response.status_code}, {response.text}")
    return None

# Асинхронная функция для отслеживания событий через WebSocket
async def monitor_balance_via_websocket(address):
    balance = get_wallet_balance(address)
    if balance is None:
        print("Не удалось получить начальный баланс. Проверьте адрес или подключение.")
        return

    print(f"Начальный баланс: {balance} TRX")

    async with websockets.create_connection(WS_API_URL) as websocket:
        # Подписка на события транзакций для указанного адреса
        subscribe_message = json.dumps({
            "eventName": "contractevent",  # События контрактов
            "contractAddress": address,   # Адрес для фильтрации
            "type": "subscribe"
        })
        await websocket.send(subscribe_message)
        print(f"Подписка на события для адреса: {address}")

        while True:
            try:
                # Получение сообщения
                message = await websocket.recv()
                data = json.loads(message)
                print("Получено событие:", data)

                # Обработка входящих и исходящих транзакций
                if "result" in data and data["result"].get("eventName") == "Transfer":
                    transfer_event = data["result"]
                    value = int(transfer_event["raw_data"]["value"]) / 1e6  # Сумма в TRX
                    from_address = transfer_event["raw_data"]["from"]
                    to_address = transfer_event["raw_data"]["to"]

                    # Изменение баланса
                    if from_address == address:
                        balance -= value
                        print(f"Транзакция на {value} TRX отправлена. Новый баланс: {balance} TRX")
                    elif to_address == address:
                        balance += value
                        print(f"Транзакция на {value} TRX получена. Новый баланс: {balance} TRX")
            except Exception as e:
                print(f"Ошибка при обработке данных: {e}")
                break

# Запуск мониторинга
if __name__ == "__main__":
    try:
        print(f"Начинаем мониторинг баланса кошелька {ADDRESS}...")
        asyncio.run(monitor_balance_via_websocket(ADDRESS))
    except KeyboardInterrupt:
        print("Мониторинг остановлен.")
