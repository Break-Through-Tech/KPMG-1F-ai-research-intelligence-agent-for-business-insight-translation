"""Bounded archive assets; no filesystem extraction, compilation or network."""
import gzip
import io
import tarfile

from .tex_source import MAX_EXPANDED, _name, read_source

MAX_ASSET = 16 * 1024 * 1024
MAX_ASSET_TOTAL = 32 * 1024 * 1024


def asset_members(data, selected=()):
    """Validate the complete archive first; return names and selected bytes.

    A second pass reuses the validated bounded expansion. Unselected binary
    assets are never decoded. Duplicate asset paths are rejected, not guessed.
    """
    read_source(data)
    if data.startswith(b'\x1f\x8b'):
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
            data = stream.read(MAX_EXPANDED + 1)
    names, payloads, total = set(), {}, 0
    try:
        archive = tarfile.open(fileobj=io.BytesIO(data), mode='r:')
    except tarfile.ReadError:
        return names, payloads
    with archive:
        for member in archive:
            if not member.isfile():
                continue
            name = _name(member.name)
            if name in names:
                raise ValueError('Duplicate archive asset path')
            names.add(name)
            if name in selected:
                total += member.size
                if member.size > MAX_ASSET or total > MAX_ASSET_TOTAL:
                    raise ValueError('Figure/bibliography asset byte limit exceeded')
                payloads[name] = archive.extractfile(member).read()
    return names, payloads
