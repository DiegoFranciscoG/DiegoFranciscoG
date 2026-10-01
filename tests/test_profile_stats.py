import xml.etree.ElementTree as ET
from datetime import date

import pytest

from scripts import profile_stats as ps


def fake_api(pages: dict[str, object]):
    calls: list[str] = []

    def fetch(url: str) -> object:
        calls.append(url)
        return pages[url]

    fetch.calls = calls  # type: ignore[attr-defined]
    return fetch


def repo(name: str, **flags) -> dict:
    return {"name": name, "fork": False, "archived": False, "private": False, **flags}


class TestListPublicRepos:
    def test_skips_forks_archived_and_private(self):
        fetch = fake_api(
            {
                f"{ps.API}/users/u/repos?type=owner&per_page=100&page=1": [
                    repo("b-app"),
                    repo("fork", fork=True),
                    repo("old", archived=True),
                    repo("secret", private=True),
                    repo("A-lib"),
                ],
            }
        )
        assert ps.list_public_repos("u", fetch) == ["A-lib", "b-app"]

    def test_follows_pagination_until_short_page(self):
        first = [repo(f"r{i:03d}") for i in range(100)]
        fetch = fake_api(
            {
                f"{ps.API}/users/u/repos?type=owner&per_page=100&page=1": first,
                f"{ps.API}/users/u/repos?type=owner&per_page=100&page=2": [repo("last")],
            }
        )
        names = ps.list_public_repos("u", fetch)
        assert len(names) == 101
        assert len(fetch.calls) == 2

    def test_empty_account(self):
        fetch = fake_api({f"{ps.API}/users/u/repos?type=owner&per_page=100&page=1": []})
        assert ps.list_public_repos("u", fetch) == []


class TestAggregate:
    def test_sums_bytes_counts_repos_and_sorts(self):
        shares = ps.aggregate([{"Java": 600, "HTML": 100}, {"Python": 200, "Java": 100}])
        assert [s.name for s in shares] == ["Java", "Python", "HTML"]
        java = shares[0]
        assert java.bytes == 700 and java.repos == 2
        assert java.percent == pytest.approx(70.0)
        assert java.color == ps.LANGUAGE_COLORS["Java"]

    def test_groups_tail_into_otros_and_percentages_add_to_100(self):
        per_repo = [{f"L{i}": 100 - i for i in range(12)}]
        shares = ps.aggregate(per_repo, top_n=3)
        assert [s.name for s in shares] == ["L0", "L1", "L2", "Otros"]
        assert shares[-1].repos == 0
        assert sum(s.percent for s in shares) == pytest.approx(100.0)

    def test_exclude_and_ignore_zero_sizes(self):
        shares = ps.aggregate([{"Java": 10, "HTML": 90, "Empty": 0}], exclude={"HTML"})
        assert [(s.name, s.percent) for s in shares] == [("Java", 100.0)]

    def test_unknown_language_uses_fallback_color(self):
        assert ps.aggregate([{"Zig": 5}])[0].color == ps.OTHER_COLOR

    def test_no_data(self):
        assert ps.aggregate([]) == []
        assert ps.aggregate([{"HTML": 5}], exclude={"HTML"}) == []

    def test_ties_are_ordered_by_name(self):
        assert [s.name for s in ps.aggregate([{"B": 5, "A": 5}])] == ["A", "B"]


class TestRenderSvg:
    @pytest.mark.parametrize("theme", sorted(ps.THEMES))
    def test_is_valid_xml_with_title_and_legend(self, theme):
        shares = ps.aggregate([{"Java": 70, "C#": 20, "Python": 10}])
        svg = ps.render_svg(shares, 3, theme, date(2026, 9, 30))
        root = ET.fromstring(svg)
        ns = "{http://www.w3.org/2000/svg}"
        assert root.find(f"{ns}title").text == "Lenguajes en 3 repositorios públicos"
        texts = [t.text for t in root.iter(f"{ns}text")]
        assert "C#" in texts
        assert "70.0 % · 1 repo" in texts
        assert any("2026-09-30" in (t or "") for t in texts)
        assert ps.THEMES[theme]["bg"] in svg

    def test_escapes_markup_in_names(self):
        svg = ps.render_svg(ps.aggregate([{"<x&y>": 1}]), 1, "light", date(2026, 1, 1))
        ET.fromstring(svg)
        assert "&lt;x&amp;y&gt;" in svg

    def test_bar_segments_fill_the_bar(self):
        shares = ps.aggregate([{"Java": 1, "Python": 1, "Dart": 2}])
        svg = ps.render_svg(shares, 1, "dark", date(2026, 1, 1))
        root = ET.fromstring(svg)
        ns = "{http://www.w3.org/2000/svg}"
        group = next(g for g in root.iter(f"{ns}g") if g.get("clip-path"))
        widths = [float(r.get("width")) for r in group]
        assert sum(widths) == pytest.approx(432, abs=0.05)

    def test_height_grows_with_legend_rows(self):
        few = ps.render_svg(ps.aggregate([{"A": 1}]), 1, "light", date(2026, 1, 1))
        many = ps.render_svg(ps.aggregate([{c: 1 for c in "ABCDEFGHIJ"}]), 1, "light", date(2026, 1, 1))
        assert int(ET.fromstring(many).get("height")) > int(ET.fromstring(few).get("height"))


class TestMain:
    def api(self):
        return fake_api(
            {
                f"{ps.API}/users/u/repos?type=owner&per_page=100&page=1": [repo("one"), repo("two")],
                f"{ps.API}/repos/u/one/languages": {"Java": 300, "HTML": 50},
                f"{ps.API}/repos/u/two/languages": {"Python": 100},
            }
        )

    def test_writes_both_themes(self, tmp_path):
        code = ps.main(["--user", "u", "--out-dir", str(tmp_path)], fetch=self.api(), today=date(2026, 9, 30))
        assert code == 0
        for theme in ("light", "dark"):
            text = (tmp_path / f"languages-{theme}.svg").read_text(encoding="utf-8")
            assert "Lenguajes en 2 repositorios públicos" in text

    def test_exclude_option(self, tmp_path):
        ps.main(
            ["--user", "u", "--out-dir", str(tmp_path), "--exclude", "HTML, Python"],
            fetch=self.api(),
            today=date(2026, 9, 30),
        )
        text = (tmp_path / "languages-light.svg").read_text(encoding="utf-8")
        assert "HTML" not in text and "Python" not in text and "Java" in text

    def test_does_not_rewrite_when_only_the_date_changes(self, tmp_path, capsys):
        args = ["--user", "u", "--out-dir", str(tmp_path)]
        ps.main(args, fetch=self.api(), today=date(2026, 9, 1))
        ps.main(args, fetch=self.api(), today=date(2026, 9, 30))
        text = (tmp_path / "languages-dark.svg").read_text(encoding="utf-8")
        assert "2026-09-01" in text
        assert "sin cambios" in capsys.readouterr().out

    def test_rewrites_when_data_changes(self, tmp_path):
        args = ["--user", "u", "--out-dir", str(tmp_path)]
        ps.main(args, fetch=self.api(), today=date(2026, 9, 1))
        changed_pages = {
            f"{ps.API}/users/u/repos?type=owner&per_page=100&page=1": [repo("one")],
            f"{ps.API}/repos/u/one/languages": {"Kotlin": 10},
        }
        ps.main(args, fetch=fake_api(changed_pages), today=date(2026, 9, 30))
        text = (tmp_path / "languages-light.svg").read_text(encoding="utf-8")
        assert "Kotlin" in text and "2026-09-30" in text

    def test_fails_without_languages(self, tmp_path):
        fetch = fake_api({f"{ps.API}/users/u/repos?type=owner&per_page=100&page=1": []})
        assert ps.main(["--user", "u", "--out-dir", str(tmp_path)], fetch=fetch) == 1
        assert not list(tmp_path.iterdir())


class TestHttpFetcher:
    def test_sends_api_headers_and_token(self, monkeypatch):
        seen = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self, *args):
                return b'{"ok": true}'

        def fake_urlopen(request, timeout):
            seen["headers"] = dict(request.header_items())
            seen["timeout"] = timeout
            return Response()

        monkeypatch.setattr(ps.urllib.request, "urlopen", fake_urlopen)
        assert ps.http_fetcher("tkn")("https://api.github.com/x") == {"ok": True}
        assert seen["headers"]["Authorization"] == "Bearer tkn"
        assert seen["headers"]["X-github-api-version"] == "2022-11-28"
        assert seen["timeout"] == 30

    def test_rejects_urls_outside_the_api(self):
        with pytest.raises(ValueError):
            ps.http_fetcher(None)("file:///etc/passwd")

    def test_without_token_sends_no_authorization(self, monkeypatch):
        captured = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self, *args):
                return b"[]"

        def fake_urlopen(request, timeout):
            captured.update(dict(request.header_items()))
            return Response()

        monkeypatch.setattr(ps.urllib.request, "urlopen", fake_urlopen)
        ps.http_fetcher(None)("https://api.github.com/x")
        assert "Authorization" not in captured
