from pathlib import Path
import webbrowser

html = Path(__file__).resolve().parent / "painel_mcmv_rural.html"
webbrowser.open(html.as_uri())
print(f"Abrindo: {html}")
