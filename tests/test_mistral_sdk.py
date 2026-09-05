def test_installed_mistral_sdk_exposes_the_primary_client() -> None:
    from mistralai import Mistral

    client = Mistral(api_key="test-key")
    assert hasattr(client.chat, "complete")
