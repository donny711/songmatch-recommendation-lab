"""Read selected members from official FMA ZIPs without downloading whole archives."""
import io
from functools import lru_cache
import urllib.request
import zipfile

FMA_BASE = "https://os.unil.cloud.switch.ch/fma/"

@lru_cache(maxsize=32)
def _read_range(url, start, size):
    request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{start+size-1}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        if response.status != 206:
            raise OSError("The FMA server must support byte-range requests.")
        data = response.read()
    if len(data) != size:
        raise OSError("Incomplete FMA download. Try again.")
    return data

class RemoteZip(io.RawIOBase):
    def __init__(self, url):
        self.url, self.pos = url, 0
        request = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            if response.status != 206:
                raise OSError("The FMA archive server does not support ranges.")
            self.size = int(response.headers["Content-Range"].split("/")[-1])
    def seekable(self):
        return True
    def tell(self):
        return self.pos
    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos+offset if whence == 1 else self.size+offset
        return self.pos
    def read(self, size=-1):
        size = self.size-self.pos if size < 0 else min(size, self.size-self.pos)
        if size <= 0:
            return b""
        data = _read_range(self.url, self.pos, size)
        self.pos += len(data)
        return data

def read_member(archive_name, member):
    if archive_name not in ("fma_metadata", "fma_small", "fma_medium"):
        raise ValueError("Unsupported official FMA archive.")
    with zipfile.ZipFile(RemoteZip(FMA_BASE+archive_name+".zip")) as archive:
        return archive.read(member)  # ZipFile verifies the member CRC.

def load_preview(song_id, subset):
    number = int(song_id)
    if number < 1 or subset not in ("small", "medium"):
        raise ValueError("No preview is available for this track.")
    archive = "fma_small" if subset == "small" else "fma_medium"
    return read_member(archive, f"{archive}/{number//1000:03d}/{number:06d}.mp3")
