#!/usr/bin/env python3
import aiohttp
import asyncio
import async_timeout

async def fetch(session, url):
    print('3')
    with async_timeout.timeout(10):
        print('4')
        async with session.get(url) as response:
            print('5')
            return await response.text()

async def main():
    print('1')
    async with aiohttp.ClientSession() as session:
        print('2')
        html1 = await fetch(session, 'http://python.org')
        print('6')
        html2 = await fetch(session, 'http://python.org')
        print('7')
        html3 = await fetch(session, 'http://python.org')
        print('done')
    print('9')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())