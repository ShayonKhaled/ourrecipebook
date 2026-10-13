"""Create or update a GitHub Actions repository secret.

Encrypts the value with the repository public key (libsodium sealed box) as the
GitHub API requires, so the plaintext is never sent and never printed.

    python _tools/set_repo_secret.py <owner/repo> <SECRET_NAME> <value>

Needs PyNaCl (`pip install pynacl`).
"""

import base64
import json
import sys
import urllib.error
import urllib.request

from nacl import encoding, public

API = "https://api.github.com"


def request(url, token, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "recipebook-secret-setter")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
            return resp.status, (json.loads(body) if body.strip() else {})
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": exc.read().decode()[:400]}


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2

    repo, name, value = sys.argv[1], sys.argv[2], sys.argv[3]

    token = sys.stdin.readline().strip()
    if not token:
        print("ERROR: no token on stdin", file=sys.stderr)
        return 1

    status, key = request(f"{API}/repos/{repo}/actions/secrets/public-key", token)
    if status != 200:
        print(f"ERROR: could not fetch public key ({status}): {key}", file=sys.stderr)
        return 1

    sealed = public.SealedBox(
        public.PublicKey(key["key"].encode(), encoding.Base64Encoder())
    ).encrypt(value.encode())

    status, result = request(
        f"{API}/repos/{repo}/actions/secrets/{name}",
        token,
        method="PUT",
        payload={
            "encrypted_value": base64.b64encode(sealed).decode(),
            "key_id": key["key_id"],
        },
    )

    if status in (201, 204):
        # Never echo the value.
        print(f"OK: secret {name} set on {repo} (value length {len(value)})")
        return 0

    print(f"ERROR: failed to set secret ({status}): {result}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
