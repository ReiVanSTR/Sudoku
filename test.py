import aiohttp
import asyncio
import time

address = "0xf84a54504B247b54BBF83220A4cdFBeF485855B7"
apikey = "B99B28TQ6Q6JZV3G4N5NB1G148KTD159TR"

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text() 

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            tasks.append(fetch(session, url))
        return await asyncio.gather(*tasks)

start_time = time.time()


urls = ["https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={apikey}"]   # Пример 10 запросов
result = asyncio.run(fetch_all(urls))

print(f"Completed in: {time.time() - start_time} seconds \n Result: {result}")