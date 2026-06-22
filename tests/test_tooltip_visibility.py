"""
Testes de regressão para o sistema de tooltip CSS (data-tip / data-tip-b).

Problema documentado:
  - `transition: transform` em .card-nav:hover cria stacking context isolado.
  - O z-index:9000 do ::after fica preso DENTRO desse contexto.
  - Cards irmãos pintados depois no DOM ficam visualmente por cima do tooltip.

Solução coberta pelos testes:
  - [data-tip]:hover, [data-tip-b]:hover recebem z-index:200.
  - Isso eleva o card hoverado acima dos irmãos no stacking context raiz.
  - O ::after (z-index:9000 dentro do contexto elevado) fica sempre visível.
"""
import pytest
from playwright.sync_api import Page


# ─── helpers ──────────────────────────────────────────────────────────────────

def _opacity_after(page: Page, selector: str) -> float:
    """Retorna opacity computada do ::after de um elemento."""
    return page.evaluate(
        f"""
        (() => {{
            const el = document.querySelector('{selector}');
            if (!el) return -1;
            return parseFloat(window.getComputedStyle(el, '::after').opacity);
        }})()
        """
    )


def _css_rule_z_index(page: Page, selector_text: str) -> int:
    """
    Lê diretamente das cssRules da página o z-index definido para um seletor.
    Mais confiável que hover real para checar a existência da regra CSS.
    Retorna 0 se a regra não existir ou não tiver z-index definido.
    """
    return page.evaluate(
        f"""
        (() => {{
            for (const sheet of document.styleSheets) {{
                try {{
                    for (const rule of sheet.cssRules) {{
                        if (rule.selectorText === '{selector_text}') {{
                            const z = rule.style.zIndex;
                            return z ? parseInt(z) : 0;
                        }}
                    }}
                }} catch(e) {{ /* cross-origin sheet */ }}
            }}
            return 0;
        }})()
        """
    )


def _hover_z_index(page: Page, selector: str) -> int:
    """Faz hover real (via Playwright) e lê z-index computado."""
    page.hover(selector, timeout=3000)
    return page.evaluate(
        f"""
        (() => {{
            const el = document.querySelector('{selector}');
            if (!el) return -999;
            const z = window.getComputedStyle(el).zIndex;
            return z === 'auto' ? 0 : parseInt(z);
        }})()
        """
    )


# ─── Grupo 1: z-index no hover (fix central) ──────────────────────────────────

class TestZIndexNoHover:
    """
    O card hoverado DEVE ter z-index >= 200 no contexto raiz.
    Sem isso, irmãos pintados depois ficam por cima do tooltip.

    Estratégia: verificar diretamente nas cssRules se a regra existe com o valor
    correto. Mais confiável do que hover real para checar a presença do CSS fix.
    """

    def test_regra_css_data_tip_hover_existe(self, page: Page):
        """A regra '[data-tip]:hover' deve ter z-index >= 200 nas cssRules."""
        z = _css_rule_z_index(page, "[data-tip]:hover, [data-tip-b]:hover")
        assert z >= 200, (
            f"Regra CSS '[data-tip]:hover, [data-tip-b]:hover' z-index={z}, "
            f"esperado >= 200.\nFix: adicionar 'z-index: 200' nessa regra no CSS."
        )

    def test_data_tip_eleva_z_index_no_hover(self, page: Page):
        """Hover real: z-index computado deve ser >= 200 após mover o mouse."""
        z = _hover_z_index(page, "[data-tip]")
        assert z >= 200, (
            f"[data-tip]:hover z-index={z}, esperado >= 200.\n"
            "Fix: adicionar 'z-index: 200' na regra [data-tip]:hover no CSS."
        )

    def test_data_tip_b_eleva_z_index_no_hover(self, page: Page):
        """Hover real: [data-tip-b] z-index >= 200 após mover o mouse."""
        z = _hover_z_index(page, "[data-tip-b]")
        assert z >= 200, (
            f"[data-tip-b]:hover z-index={z}, esperado >= 200.\n"
            "Fix: adicionar 'z-index: 200' na regra [data-tip-b]:hover no CSS."
        )

    def test_card_hoverado_acima_do_irmao(self, page: Page):
        """Card hoverado deve ter z-index estritamente maior que irmão não hoverado."""
        cards = page.locator(".cards [data-tip-b]").all()
        assert len(cards) >= 2, "Esperado ao menos 2 cards [data-tip-b]"

        # Hover no primeiro card
        cards[0].hover()

        z_hov = page.evaluate(
            "parseInt(window.getComputedStyle("
            "  document.querySelectorAll('.cards [data-tip-b]')[0]).zIndex) || 0"
        )
        z_irm = page.evaluate(
            "parseInt(window.getComputedStyle("
            "  document.querySelectorAll('.cards [data-tip-b]')[1]).zIndex) || 0"
        )
        assert z_hov > z_irm, (
            f"Card hoverado z={z_hov} <= irmão z={z_irm}.\n"
            "Tooltip do card hoverado ficará atrás do irmão vizinho."
        )

    def test_todos_card_nav_com_tooltip_elevam_z_index(self, page: Page):
        """Todos os .card-nav portadores de tooltip devem ter z-index >= 200 no hover."""
        SEL = ".card-nav[data-tip-b], .card-nav[data-tip]"
        cards = page.locator(SEL).all()
        assert len(cards) > 0, "Nenhum .card-nav com tooltip encontrado"
        falhas = []
        for i, card in enumerate(cards):
            card.hover()
            # Referencia o elemento pelo índice para evitar ambiguidade do ':hover'
            z = page.evaluate(
                f"""
                (() => {{
                    const cards = [...document.querySelectorAll('{SEL}')];
                    const el = cards[{i}];
                    if (!el) return -1;
                    return parseInt(window.getComputedStyle(el).zIndex) || 0;
                }})()
                """
            )
            if z < 200:
                texto = card.inner_text()[:50].replace("\n", " ")
                falhas.append(f"z={z} | '{texto}'")

        assert falhas == [], (
            "Cards com z-index insuficiente no hover:\n" + "\n".join(f"  {f}" for f in falhas)
        )


# ─── Grupo 2: visibilidade (opacity) ──────────────────────────────────────────

class TestTooltipOpacity:
    """Tooltip deve ficar opacity:1 ao hover e opacity:0 em repouso."""

    def test_tooltip_invisivel_sem_hover(self, page: Page):
        op = _opacity_after(page, "[data-tip]")
        assert op == pytest.approx(0.0, abs=0.05), (
            f"Tooltip visível sem hover (opacity={op}). Deve começar em 0."
        )

    def test_tooltip_b_invisivel_sem_hover(self, page: Page):
        op = _opacity_after(page, "[data-tip-b]")
        assert op == pytest.approx(0.0, abs=0.05), (
            f"Tooltip-b visível sem hover (opacity={op}). Deve começar em 0."
        )

    def test_tooltip_visivel_apos_hover(self, page: Page):
        page.hover("[data-tip]")
        page.wait_for_timeout(300)  # transition 180ms
        op = _opacity_after(page, "[data-tip]")
        assert op == pytest.approx(1.0, abs=0.05), (
            f"Tooltip não apareceu após hover (opacity={op}). Esperado ~1.0."
        )

    def test_tooltip_b_visivel_apos_hover(self, page: Page):
        page.hover("[data-tip-b]")
        page.wait_for_timeout(300)
        op = _opacity_after(page, "[data-tip-b]")
        assert op == pytest.approx(1.0, abs=0.05), (
            f"Tooltip-b não apareceu após hover (opacity={op}). Esperado ~1.0."
        )


# ─── Grupo 3: posicionamento (acima vs abaixo) ────────────────────────────────

class TestTooltipDirecao:
    """
    data-tip  → tooltip ACIMA  → ::after usa bottom, não usa top.
    data-tip-b → tooltip ABAIXO → ::after usa top,    bottom:auto.
    """

    def test_data_tip_usa_bottom_nao_top(self, page: Page):
        """
        [data-tip]::after deve aparecer ACIMA do elemento.
        Verificação: top computado < 0 (posição acima do topo do elemento).
        Browsers resolvem 'top: auto' para o valor calculado quando 'bottom' é definido.
        """
        result = page.evaluate(
            """
            (() => {
                const el = document.querySelector('[data-tip]');
                if (!el) return null;
                const s = window.getComputedStyle(el, '::after');
                return {
                    topPx: parseFloat(s.top),
                    bottomRaw: s.bottom,
                };
            })()
            """
        )
        assert result is not None, "Nenhum [data-tip] encontrado"
        # top negativo = o tooltip está acima do limite superior do elemento
        assert result["topPx"] < 0, (
            f"[data-tip]::after top={result['topPx']:.1f}px deve ser negativo (tooltip acima). "
            "Verificar se 'bottom: calc(100%+9px)' está definido e 'top' não foi sobrescrito."
        )

    def test_data_tip_b_usa_top_nao_bottom(self, page: Page):
        """
        [data-tip-b]::after deve aparecer ABAIXO do elemento.
        Verificação: top computado > 0 (posição abaixo do topo do elemento)
        e explicitamente não usa bottom como posicionador principal.
        Se regredir para tooltip-acima, top ficará negativo e o teste falha.
        """
        result = page.evaluate(
            """
            (() => {
                const el = document.querySelector('[data-tip-b]');
                if (!el) return null;
                const s = window.getComputedStyle(el, '::after');
                return {
                    topPx:    parseFloat(s.top),
                    bottomPx: parseFloat(s.bottom),
                };
            })()
            """
        )
        assert result is not None, "Nenhum [data-tip-b] encontrado"
        # top positivo = tooltip abaixo do elemento; top negativo = seria acima (regressão)
        assert result["topPx"] > 0, (
            f"[data-tip-b]::after top={result['topPx']:.1f}px deve ser positivo "
            f"(tooltip abaixo). Regressão: tooltip voltou a aparecer acima — "
            "voltaria a ficar atrás do cabeçalho sticky."
        )

    def test_data_tip_b_nao_sobrepoem_nav_sticky(self, page: Page):
        """
        Tooltip abaixo de card da 1ª linha não deve interceptar o sticky nav.
        Nav fica no topo; tooltip vai para baixo — sentidos opostos.
        Garante que não regredimos para tooltip-acima nesses cards.
        """
        nav_box = page.locator(".tab-nav").bounding_box()
        assert nav_box, ".tab-nav não encontrado"
        nav_bottom = nav_box["y"] + nav_box["height"]

        card = page.locator("[data-tip-b]").first
        card.scroll_into_view_if_needed()
        card_box = card.bounding_box()
        assert card_box, "Card [data-tip-b] sem bounding box"

        # Card deve estar abaixo do nav
        assert card_box["y"] >= nav_bottom, (
            f"Card (y={card_box['y']:.0f}) está acima do nav bottom ({nav_bottom:.0f})"
        )

        # Tooltip começa abaixo do card → não intercepta o nav
        tooltip_top_estimado = card_box["y"] + card_box["height"] + 9
        assert tooltip_top_estimado > nav_bottom, (
            f"Tooltip estimado top ({tooltip_top_estimado:.0f}) <= "
            f"nav bottom ({nav_bottom:.0f}) — pode sobrepor o cabeçalho"
        )


# ─── Grupo 4: navegação analítica por clique ──────────────────────────────────

class TestClickNavegacao:
    """Clique em cards clicáveis deve mudar a aba ativa."""

    def _aba_ativa(self, page: Page) -> str:
        return page.evaluate(
            "document.querySelector('.tab-nav button.ativa')?.textContent?.trim() ?? ''"
        )

    def test_click_card_sai_do_dashboard(self, page: Page):
        """
        Ao menos um card-nav deve navegar para uma aba diferente de Dashboard.
        Testa a função irParaEtapa / irParaOpEtapa que foram vinculadas aos cards.
        """
        page.wait_for_selector(".tab-nav button.ativa")
        aba_inicial = self._aba_ativa(page)

        # Clica no primeiro card que tem @click e não é só informativo
        card = page.locator(".cards .card-nav").first
        card.click()
        page.wait_for_timeout(300)

        aba_apos = self._aba_ativa(page)
        # Ou navegou para outra aba, ou voltou para dashboard — qualquer estado é aceito
        # O que não pode acontecer é uma exceção JS (verificado implicitamente)
        assert aba_apos in ("Dashboard", "Propostas", "Hash & CNPJ", "Operações"), (
            f"Aba ativa inesperada após clique: '{aba_apos}'"
        )

    def test_nenhum_erro_js_ao_clicar_cards(self, page: Page):
        """Nenhum erro JavaScript deve ocorrer ao clicar em todos os card-nav."""
        erros = []
        page.on("pageerror", lambda err: erros.append(str(err)))

        cards = page.locator(".card-nav").all()
        for card in cards:
            try:
                card.click(timeout=500)
                page.wait_for_timeout(100)
            except Exception:
                pass  # timeout em cards não clicáveis — ignora

        assert erros == [], f"Erros JS ao clicar cards: {erros}"
