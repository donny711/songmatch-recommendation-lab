# Publish this project on your GitHub

These are manual instructions. No GitHub repository, remote, commit, or push has been created for you.

## 1. Keep a permanent copy

Extract songmatch-recommendation-lab.zip to a permanent project directory, such as a Projects folder. The ZIP includes source, licensed catalog derivatives, documentation, tests, and configuration. It excludes local dependencies, raw downloads, study feedback, and Git history.

Open a terminal in the extracted songmatch-recommendation-lab directory.

## 2. Create an empty GitHub repository

Create a repository named **songmatch-recommendation-lab** under your own account.

Suggested description:

> A Python and Streamlit music recommendation lab comparing musical-feature similarity with random and genre baselines through blind listening experiments.

Suggested topics:

```text
python streamlit recommendation-system music-recommendation
scikit-learn pandas sqlite experiment-design data-science
```

Use a public repository for portfolio visibility. When creating it, leave GitHub's generated README, .gitignore, and license options unchecked: this project already includes those files.

## 3. Initialize and review locally

```bash
git init -b main
git add .
git status --short
git diff --cached --stat
```

The staged files should include README.md, app.py, pages/, src/, scripts/, tests/, data/catalog.csv, attribution, reports, and configuration.

Local dependencies (.venv/ or .packages/), raw downloads, study databases, .env files, Streamlit secrets, backups, and private exports should not appear. The bundled clean catalog CSVs are intentional.

## 4. Commit and push yourself

Replace YOUR_USERNAME with your GitHub username:

```bash
git commit -m "Add SongMatch Recommendation Lab"
git remote add origin https://github.com/YOUR_USERNAME/songmatch-recommendation-lab.git
git push -u origin main
```

If you chose a different repository name, adjust the URL. If using an existing checkout with a remote already configured, inspect git remote -v and use that remote rather than adding it again.

Your normal GitHub authentication applies. No credentials belong in this repository.

## 5. Check the portfolio presentation

- Open the repository README on GitHub and check its links, tables, and diagram.
- Open the Actions tab and check the Python 3.12 and 3.14 jobs after the first push.
- Add the suggested description and topics.
- Pin the repository on your GitHub profile.
- Add actual app screenshots and a public demo link when available.

The README accurately marks human evaluation and deployment as pending. Replace those sections with measured findings and a real demo URL only after they exist.

## 6. Optional profile README entry

Replace YOUR_USERNAME before using this snippet:

```markdown
### SongMatch Recommendation Lab

A Python/Streamlit research app comparing musical-feature recommendations
with genre and random baselines. Includes a 2,000-song catalog, a blind
listening experiment, SQLite feedback storage, and 42 local passing tests.

[View project](https://github.com/YOUR_USERNAME/songmatch-recommendation-lab)
```

## Screenshots

Use the running app to capture:
1. Discover with recognizable songs selected.
2. Recommendations with explanations and the feature-comparison chart.
3. Compare methods with blinded listening controls.
4. Results, using an honest empty state until real volunteer data exists.

Save screenshots under assets/screenshots/ and insert relative image links into README.md. Avoid personal browser information and participant-level exports in screenshots.

## Hosting

A local localhost link works only while the app runs on your own computer. GitHub Pages serves static content and cannot run this Streamlit/Python server.

Use a Python-capable host with persistent database storage for a public demo. Dockerfile and compose.yaml are provided. Keep the code repository and study database separate.

## Later updates

After changing the project, run the relevant checks, then commit and push the update yourself:

```bash
python -m pytest
git add .
git commit -m "Describe your change"
git push
```
