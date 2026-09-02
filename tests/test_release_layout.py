from pathlib import Path

def test_release_has_flat_repo_layout():
    assert Path("web/index.html").is_file()
    assert Path(".github/workflows/pages.yml").is_file()
    assert Path("config/settings.json").is_file()
    assert not Path("advanced_live_source_v2").exists()

def test_pages_workflow_has_smoke_test():
    s = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")
    assert "Verify deployed site" in s
    assert "steps.deployment.outputs.page_url" in s
    assert "GitHub Pages smoke test passed." in s
