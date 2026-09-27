"""Regression checks for the sourced rental-law knowledge additions."""

from datetime import date
from pathlib import Path

import pytest
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.rag.knowledge_files import load_source


POLICIES = Path(__file__).resolve().parents[1] / "core" / "data" / "policies"
TOPICS = {
    "housing_regulation_deposit_registration.txt": "第十条",
    "housing_regulation_safety_disputes.txt": "第三十五条",
    "housing_regulation_agencies_platforms.txt": "第三十六条",
    "civil_code_contract_maintenance.txt": "第七百一十三条",
    "civil_code_subletting_sale.txt": "第七百一十七条",
    "civil_code_termination_renewal.txt": "第七百三十四条",
}


@pytest.mark.parametrize("filename,article", TOPICS.items())
def test_sourced_policy_loads_and_preserves_chunk_metadata(filename, article):
    """Keep each topic discoverable with a dated official source on every chunk."""
    documents = load_source(POLICIES / filename)
    assert len(documents) == 1
    document = documents[0]
    assert document.metadata["knowledge_type"] == "policy"
    assert document.metadata["verification_status"] == "source_required"
    assert ".gov.cn/" in document.metadata["source_url"]
    assert date.fromisoformat(document.metadata["effective_at"]) <= date.fromisoformat(
        document.metadata["collected_at"]
    )
    assert document.metadata["jurisdiction"]
    assert article in document.page_content
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=60)
    chunks = splitter.split_documents(documents)
    assert chunks
    assert all(chunk.metadata == document.metadata for chunk in chunks)
    assert any(article in chunk.page_content for chunk in chunks)


def test_maintenance_and_subletting_exceptions_are_retained():
    """Prevent simplified excerpts from removing liability and consent exceptions."""
    maintenance = load_source(POLICIES / "civil_code_contract_maintenance.txt")[0]
    assert "但是当事人另有约定的除外" in maintenance.page_content
    assert "因承租人的过错致使租赁物需要维修的" in maintenance.page_content
    subletting = load_source(POLICIES / "civil_code_subletting_sale.txt")[0]
    assert "但是出租人与承租人另有约定的除外" in subletting.page_content
    assert "承租人未经出租人同意转租的，出租人可以解除合同" in subletting.page_content
