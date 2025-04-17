from huggingface_hub import hf_hub_download
import re

def cached_download(**kwargs):
    """
    Shim for legacy `cached_download(url=...)` using hf_hub_download.
    """
    url = kwargs.get("url")
    if url is None:
        raise ValueError("Expected 'url' keyword argument in cached_download")

    # Match URLs like:
    # https://huggingface.co/<repo_id>/resolve/<revision>/<filename>
    match = re.match(
        r"https?://huggingface\.co/([^/]+/[^/]+)/resolve/([^/]+)/(.+)", url
    )

    if not match:
        raise ValueError(f"Unsupported URL format: {url}")

    repo_id, revision, filename = match.groups()

    return hf_hub_download(repo_id=repo_id, filename=filename, revision=revision)