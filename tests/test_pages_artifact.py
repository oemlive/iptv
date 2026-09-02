from pathlib import Path


def test_pages_workflow_publishes_index_and_runtime_config_at_artifact_root():
    workflow = Path('.github/workflows/pages.yml').read_text(encoding='utf-8')
    assert "mkdir -p _site" in workflow
    assert "cp -r web/. _site/" in workflow
    assert "cp -r data _site/" in workflow
    assert "cp -r output _site/" in workflow
    assert "cp -r config _site/" in workflow
    assert "touch _site/.nojekyll" in workflow
    assert "test -f _site/index.html" in workflow
    assert "mkdir -p _site/iptv" not in workflow
    assert "cp -r web/* _site/iptv/" not in workflow
