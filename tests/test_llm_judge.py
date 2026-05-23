import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from omomuki.bridge.config import BridgeConfig
from omomuki.core.loader import load_profile
from omomuki.evaluators.judge_config import JudgeConfig, load_judge_config
from omomuki.evaluators.llm_judge import review_with_llm
from omomuki.evaluators.proposal import build_proposal_from_content
from omomuki.evaluators.service import evaluate_candidate
from omomuki.storage.candidates import create_from_capture


def test_load_judge_config_level2_default_local(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("OMOMUKI_JUDGE_BASE_URL", raising=False)
    cfg = load_judge_config(2)
    assert cfg is not None
    assert "11434" in cfg.base_url


def test_load_judge_config_level3_requires_key(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("OMOMUKI_JUDGE_BASE_URL", "https://api.example.com/v1")
    monkeypatch.delenv("OMOMUKI_JUDGE_API_KEY", raising=False)
    assert load_judge_config(3) is None


@patch("omomuki.evaluators.llm_judge.urllib.request.urlopen")
def test_review_with_llm_parses_json(mock_urlopen: MagicMock, examples_dir: Path) -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "rde_class": "Inferred Extension",
                            "notes": ["ok"],
                            "uib": {
                                "UD": 0.8,
                                "MI": 0.7,
                                "CH": 0.6,
                                "DT": 0.7,
                                "VP": 0.5,
                                "FG": 0.7,
                            },
                        },
                    ),
                },
            },
        ],
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_resp

    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    proposal = build_proposal_from_content("New idea about portability")
    cfg = JudgeConfig(base_url="http://127.0.0.1:11434/v1", api_key=None, model="test")
    review = review_with_llm(cfg, 2, profile, "content", proposal)
    assert review.rde_class == "Inferred Extension"
    assert review.uib is not None


@patch("omomuki.evaluators.llm_judge.urllib.request.urlopen")
def test_review_with_llm_partial_uib(mock_urlopen: MagicMock, examples_dir: Path) -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "rde_class": "Unresolved Gap",
                            "notes": ["partial uib"],
                            "uib": {"UD": 0.2, "MI": 0.3, "CH": 0.4},
                        },
                    ),
                },
            },
        ],
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_resp

    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    proposal = build_proposal_from_content("Maybe uncertain extension")
    cfg = JudgeConfig(base_url="http://127.0.0.1:11434/v1", api_key=None, model="test")
    review = review_with_llm(cfg, 2, profile, "content", proposal)
    assert review.rde_class == "Unresolved Gap"
    assert review.uib is not None
    assert review.uib.DT == 0.5
    assert review.uib.VP == 0.5
    assert review.uib.FG == 0.5


@patch("omomuki.evaluators.service.review_with_llm")
@patch("omomuki.evaluators.service.load_judge_config")
def test_evaluate_level2_attaches_llm_review(
    mock_cfg: MagicMock,
    mock_review: MagicMock,
    tmp_path: Path,
    examples_dir: Path,
) -> None:
    from omomuki.core.candidate import LLMReview, UIBScores

    home = tmp_path / "omomuki"
    config = BridgeConfig(home=home)
    profile_dir = config.profiles_dir / "default"
    profile_dir.mkdir(parents=True)
    shutil.copy(
        examples_dir / "profiles" / "minimal.yaml",
        profile_dir / "omomuki.profile.yaml",
    )

    mock_cfg.return_value = JudgeConfig(
        base_url="http://127.0.0.1:11434/v1",
        api_key=None,
        model="mock",
    )
    mock_review.return_value = LLMReview(
        model="mock",
        level=2,
        rde_class="Inferred Extension",
        notes=["mocked"],
        uib=UIBScores(UD=0.9, MI=0.9, CH=0.9, DT=0.9, VP=0.9, FG=0.9),
    )

    candidate = create_from_capture(config, content="Portable context patterns", source_type="test")
    evaluated = evaluate_candidate(config, candidate.id, level=2)
    assert evaluated.evaluation is not None
    assert evaluated.evaluation.level == 2
    assert evaluated.evaluation.llm_review is not None
