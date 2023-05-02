import asyncio
from typing import Optional, List

import pyppeteer
from pyppeteer.element_handle import ElementHandle
from pyppeteer.page import Page


async def _evaluate(page, script, element, retries=0):
    """
    https://github.com/miyakogi/pyppeteer/issues/63#issuecomment-388647523
    """
    if retries > 10:
        return await page.evaluate(script, element)

    try:
        return await page.evaluate(script, element)
    except pyppeteer.errors.NetworkError:
        await asyncio.sleep(0.5)
        return await _evaluate(page, script, element, retries + 1)


async def get_text_of_element(page, element: ElementHandle) -> Optional[str]:
    if element is None:
        return None
    return await _evaluate(page, "(element) => element.textContent", element)


async def get_text(page, selector: str) -> Optional[str]:
    return await get_text_of_element(page, await page.querySelector(selector))


async def get_texts(page: Page, selector: str) -> List[str]:
    texts = []
    try:
        for element in await page.querySelectorAll(selector):
            text = await get_text_of_element(page, element)
            if text:
                texts.append(text)
    except pyppeteer.errors.NetworkError as e:
        print(e)
    return texts


async def click(page, selector):
    await asyncio.gather(
        page.waitForNavigation(),
        page.click(selector),
    )


async def login(page, server_url, username):
    await page.goto(f"{server_url}")
    await page.type("input[name=username]", username)
    await click(page, "button[type=submit]")

    actual_username = await get_text(page, "#username")
    assert username == actual_username
