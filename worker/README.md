# Convoy manifest save service

A small Cloudflare Worker that lets people add, edit and delete convoy manifests on the website with a
**passcode** instead of a GitHub account. It holds one GitHub token (as a secret) and saves changes to this
repo for them. `convoy-worker.js` contains no secrets.

## One-off setup (about 15 minutes)

1. **GitHub token for the service** – github.com → Settings → Developer settings → Personal access tokens →
   **Fine-grained tokens → Generate new token**. Name it "CFO save service", pick an expiry, choose
   *Only select repositories* → this repo, and set **Contents: Read and write**. Copy the token.
2. **Cloudflare account** – sign up free at dash.cloudflare.com.
3. **Create the worker** – Workers & Pages → **Create** → *Create Worker* → name it e.g. `cfo-convoys` →
   **Deploy**, then **Edit code**, replace everything with the contents of `convoy-worker.js`, and **Deploy**.
4. **Settings** – the worker → Settings → **Variables and secrets** → add:
   - `GITHUB_TOKEN` (type *Secret*) – the token from step 1
   - `PASSCODES` (type *Secret*) – the passcode(s), comma-separated, e.g. `aiambak-ops` or `aiambak-ops,night-shift`
   - `ALLOWED_ORIGIN` (type *Text*) – `https://myles-rowcliff.github.io`
   - `REPO` (type *Text*) – `myles-rowcliff/CFO---VESSEL-ROAD---SCHEDULE`
5. **Send the worker's address** (e.g. `https://cfo-convoys.<your-name>.workers.dev`) to Claude, who puts it in
   `SAVE_URL` near the top of the manifest code in `docs/index.html`. The address isn't secret.

## Day to day

- People press **Add or edit convoys** on the Convoy manifest tab and enter the passcode once; that computer
  remembers it.
- **Change the passcode** any time in the worker's settings (`PASSCODES`). Everyone is asked for the new one at
  their next save.
- When the GitHub token expires, make a new one and replace `GITHUB_TOKEN`.
- A GitHub token pasted into the page itself still works and takes priority (for Myles).
