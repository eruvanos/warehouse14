from typing import Optional, List

import pyppeteer
from pyppeteer.element_handle import ElementHandle
from pyppeteer.page import Page


async def get_text_of_element(page, element: ElementHandle) -> Optional[str]:
    if element is None:
        return None

    return await page.evaluate("(element) => element.textContent", element)


async def get_text(page, selector: str) -> Optional[str]:
    return await get_text_of_element(page, await page.querySelector(selector))


async def get_texts(page: Page, selector: str) -> List[str]:
    texts = []
    try:
        for element in await page.querySelectorAll(selector):
            text = await get_text_of_element(page, element)
            if text:
                texts.append(text)
    except pyppeteer.errors.NetworkError:
        pass
    return texts


async def login(page: Page, server_url, username):
    await page.goto(f"{server_url}")
    await page.type("input[name=username]", username)
    await page.click("button[type=submit]")

    actual_username = await get_text(page, "#username")
    assert username == actual_username
