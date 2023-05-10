import asyncio
import urllib.parse
import aiohttp
from bs4 import BeautifulSoup

main_queue = asyncio.Queue()
parsed_links_queue = asyncio.Queue()
parsed_links = set()

SESSION = None
F_OUT = None
VISITED_URLS = 0

async def get_url(url):
    global VISITED_URLS
    try:
        async with SESSION.get(url) as resp:
            VISITED_URLS += 1
            return await resp.text()
    except:
        print(f'Bad URL: {url}')

async def worker():
    while True:
        url = await main_queue.get()
        soup = BeautifulSoup(await get_url(url), 'html.parser')

        for a in soup.select('a[href]'):
            href = a['href']
            if href.startswith('/uscode/') and ':' not in href:
                parsed_links_queue.put_nowait('https://www.law.cornell.edu' + href)

        main_queue.task_done()

async def consumer():
    while True:
        url = await parsed_links_queue.get()

        if url not in parsed_links:
            print(urllib.parse.unquote(url), file=F_OUT, flush=True)  # <-- print the url to file
            parsed_links.add(url)
            main_queue.put_nowait(url)

        parsed_links_queue.task_done()


async def main():
    global SESSION, F_OUT

    seed_url = 'https://www.law.cornell.edu/uscode'
    parsed_links.add(seed_url)

    with open('out.txt', 'w') as F_OUT:
        async with aiohttp.ClientSession() as SESSION:
            workers = {asyncio.create_task(worker()) for _ in range(16)}
            c = asyncio.create_task(consumer())

            main_queue.put_nowait(seed_url)
            print('Initializing...')
            await asyncio.sleep(5)

            while main_queue.qsize():
                print(f'Visited URLs: {VISITED_URLS:>7}  Known URLs (saved in out.txt): {len(parsed_links):>7}', flush=True)
                await asyncio.sleep(0.1)

    await main_queue.join()
    await parsed_links_queue.join()

asyncio.run(main())