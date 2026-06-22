"""Script de diagnóstico: verifica o DOM após Vue montar."""
import sys
from playwright.sync_api import sync_playwright
from pathlib import Path

html = Path(__file__).parent.parent / "static-html" / "painel_mcmv_rural.html"
URL = "file:///" + html.as_posix()

def p(text):
    sys.stdout.buffer.write((str(text) + "\n").encode("utf-8", errors="replace"))

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})

    # Captura erros JS
    js_errors = []
    pg.on("pageerror", lambda e: js_errors.append(str(e)))

    pg.goto(URL)
    pg.wait_for_load_state("load")
    pg.wait_for_timeout(4000)

    p(f"JS errors: {js_errors}")
    p(f"#app elems   : {pg.evaluate('document.querySelectorAll(\"#app *\").length')}")
    p(f"Vue defined  : {pg.evaluate('typeof Vue !== \"undefined\"')}")

    # Listar tags e classes dos elementos dentro de #app
    elems = pg.evaluate("""
        [...document.querySelectorAll('#app *')].map(e => ({
            tag: e.tagName,
            cls: e.className,
            id: e.id,
            tip: e.getAttribute('data-tip') ? 'Y' : (e.getAttribute('data-tip-b') ? 'Yb' : '-')
        }))
    """)
    for el in elems:
        p(f"  {el['tag']:10} cls={el['cls'][:30]:30} id={el['id']:10} tip={el['tip']}")

    b.close()
