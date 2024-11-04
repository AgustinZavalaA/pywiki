import enum
from dataclasses import dataclass
import os
import re
import uvicorn
from fastapi import FastAPI, Form
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")
global all_page_titles


class Template(enum.Enum):
    INDEX = "index.html"
    EDIT = "edit.html"
    VIEW = "view.html"


@dataclass
class Page:
    title: str
    content: str

    def save(self) -> None:
        with open("data/" + self.title + ".txt", "w") as file:
            file.write(self.content)


def loadPage(title: str) -> Page:
    try:
        with open("data/" + title + ".txt", "r") as file:
            content = file.read()
    except FileNotFoundError:
        return Page(title, "")
    return Page(title=title, content=content)


def loadAllPageTitles() -> list[str]:
    dir_list = os.listdir("data/")
    return list(map(lambda s: s.removesuffix(".txt"), dir_list))


def regex_page_links(text: str) -> str:
    global all_page_titles
    pattern = "\\[(" + "|".join(all_page_titles) + ")\\]"
    replacement = '[<a href="/view/\\1">\\1</a>]'
    print(pattern, replacement)
    return re.sub(pattern, replacement, text)


templates.env.filters["regex_page_links"] = regex_page_links


@app.get("/", response_class=HTMLResponse)
async def wiki_index(request: Request) -> HTMLResponse:
    global all_page_titles
    all_page_titles = loadAllPageTitles()
    print(all_page_titles)
    return templates.TemplateResponse(
        Template.INDEX.value, {"request": request, "pages": all_page_titles}
    )


@app.get("/view/{page_name}")
async def view_page(request: Request, page_name: str):
    page = loadPage(page_name)
    if page.content == "":
        return RedirectResponse(url="/edit/" + page_name, status_code=303)
    return templates.TemplateResponse(
        Template.VIEW.value, {"request": request, "page": page}
    )


@app.get("/edit/{page_name}", response_class=HTMLResponse)
async def edit_page(request: Request, page_name: str) -> HTMLResponse:
    page = loadPage(page_name)
    return templates.TemplateResponse(
        Template.EDIT.value, {"request": request, "page": page}
    )


@app.post("/save/{page_name}")
async def save_page(page_name: str, page_content: str = Form(...)) -> RedirectResponse:
    page = Page(title=page_name, content=page_content)
    page.save()
    return RedirectResponse(url="/view/" + page_name, status_code=303)


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
