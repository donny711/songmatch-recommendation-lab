"""Bundle reviewable source and licensed catalog, excluding dependencies and feedback."""
from pathlib import Path
import hashlib
import zipfile
ROOT = Path(__file__).resolve().parents[1]

def main():
    output=ROOT.parent/(ROOT.name+".zip")
    names=["app.py","README.md","LICENSE","requirements.txt","requirements-lock.txt","pytest.ini",
           "Dockerfile","compose.yaml",".gitignore",".gitattributes",".dockerignore","start-local.cmd",
           ".streamlit/config.toml",".github/workflows/tests.yml",
           "data/catalog.csv","data/manifest.json","data/README.md","data/fma_catalog.csv","data/fma_manifest.json"]
    files=[ROOT/name for name in names]
    private_parts = {"__pycache__", "private", "backups", "exports", ".tmp"}
    public_extensions = {".py", ".md", ".css", ".png", ".jpg", ".jpeg", ".webp", ".svg"}
    for directory in ("src","pages","scripts","tests","reports","assets","docs"):
        files.extend(
            p for p in (ROOT/directory).rglob("*")
            if p.is_file() and not private_parts.intersection(p.relative_to(ROOT).parts)
            and p.suffix.lower() in public_extensions
        )
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            archive.write(path,ROOT.name+"/"+path.relative_to(ROOT).as_posix())
    print(output)
    print("SHA-256: "+hashlib.sha256(output.read_bytes()).hexdigest())

if __name__=="__main__":
    main()
