import importlib.util
from pathlib import Path
import re
import yaml
import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent / "skills" / "celestial-whisper"

# Dynamically import verification utility from hyphenated skill directory
script_path = SKILL_DIR / "scripts" / "verify_ephemeris.py"
spec = importlib.util.spec_from_file_location("verify_ephemeris", script_path)
verify_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_module)
verify_celestial_skill = verify_module.verify_celestial_skill


def test_skill_markdown_exists_and_frontmatter_valid():
    """Verify SKILL.md exists and contains valid YAML frontmatter per the Open Standard."""
    skill_file = SKILL_DIR / "SKILL.md"
    assert skill_file.exists(), f"SKILL.md not found at {skill_file}"

    content = skill_file.read_text(encoding="utf-8")
    assert content.startswith("---"), "SKILL.md must begin with YAML frontmatter delimiter '---'"

    # Extract YAML frontmatter
    parts = content.split("---", 2)
    assert len(parts) >= 3, "SKILL.md frontmatter must be enclosed between '---' delimiters"
    frontmatter_raw = parts[1]

    metadata = yaml.safe_load(frontmatter_raw)
    assert isinstance(metadata, dict), "Frontmatter must parse into a YAML dictionary"

    # Mandatory Agent Skills Open Standard fields
    assert metadata.get("name") == "celestial-whisper"
    assert "description" in metadata and len(metadata["description"]) > 20
    assert metadata.get("license") == "Apache-2.0"
    assert "compatibility" in metadata
    assert "metadata" in metadata
    assert "version" in metadata["metadata"]
    assert "author" in metadata["metadata"]


def test_skill_markdown_required_sections_present():
    """Verify that SKILL.md includes procedural steps, hard rules, and schemas."""
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").lower()

    # Must contain procedural workflow
    assert "procedure" in content or "operating procedure" in content
    # Must contain hard rules / constraints
    assert "hard rule" in content or "invariant" in content
    # Must contain schema definitions
    assert "schema" in content or "input" in content
    # Must reference supporting documents
    assert "references" in content


def test_skill_references_exist_and_have_rich_content():
    """Verify reference documentation in references/ exists and contains comprehensive data."""
    ref_dir = SKILL_DIR / "references"
    assert ref_dir.is_dir(), f"References directory missing at {ref_dir}"

    constellations_file = ref_dir / "constellations.md"
    assert constellations_file.exists()
    constellations_text = constellations_file.read_text(encoding="utf-8")
    assert "Sirius" in constellations_text
    assert "Polaris" in constellations_text
    assert "Summer Triangle" in constellations_text
    assert "Winter Hexagon" in constellations_text

    seeing_file = ref_dir / "seeing-scale.md"
    assert seeing_file.exists()
    seeing_text = seeing_file.read_text(encoding="utf-8")
    assert "Antoniadi" in seeing_text
    assert "Pickering" in seeing_text
    assert "Dew Point Depression" in seeing_text


def test_skill_verification_script_execution():
    """Verify that the skill verification script executes and passes all invariant checks."""
    result = verify_celestial_skill(
        latitude=41.6631,
        longitude=-77.8236,
        heading=90.0,
        query="What bright star is rising in the east right now?"
    )

    assert result["verified"] is True
    assert len(result["violations"]) == 0
    assert 10 <= result["word_count"] <= 45
    assert result["visible_count"] > 0
    assert result["seeing_score"] >= 0.0
    assert not re.search(r"[*#_`\[\]]", result["spoken_answer"])
