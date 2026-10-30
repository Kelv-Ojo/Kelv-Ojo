# GitHub statistics and refresh notes

The README combines a working external live streak card with locally generated fallback panels. The public GitHub Readme Stats instance returned HTTP 503 during this review; the external activity-graph service returned HTTP 402. Those broken widgets are not embedded.

## Scope

- **Live streak card:** DenverCoder1's service, requested for `Kelv-Ojo`. The service's total is account-lifetime; its longest streak may span more than the fallback calendar window. Public GitHub data and caches can affect the response. [Service source and documentation](https://github.com/DenverCoder1/github-readme-streak-stats).
- **Local contribution panels:** the calendar publicly exposed at https://github.com/users/Kelv-Ojo/contributions. The exact date window and capture date appear in the graphic and `assets/public-stats.json`. It is GitHub's displayed window, which can include partial weeks, not a strict 365-day calculation. Counts are reconciled with GitHub's heading before writing output.
- **Local current streak:** consecutive contribution dates ending on the UTC capture date. Unlike some services, no “yesterday grace day” is used. A 0 is a genuine result, not missing data.
- **Languages:** sum of code-byte values from GitHub's language endpoint for each public non-fork repository. Binary Power BI/workbook artefacts, SQL and Markdown may not be reflected in GitHub language detection. Bytes are not proficiency, time spent or analytical importance.
- **Achievement:** the profile visibly showed Pull Shark on 29 October 2026. The image is GitHub's original asset, linking to the native achievement page. No trophy-service award is inferred from commit counts.

## Refresh local panels

From this repository, run:

```sh
python scripts/refresh_stats.py
```

Python 3.10+ standard library only. No package installation, token, credential access or write permission is required. It reads public repository metadata, public language data and the public contribution calendar. It writes SVG panels and a JSON source snapshot locally; it does not commit, push, change settings or create a workflow. Review the diff before publishing. A public API rate limit or changed calendar format raises an error rather than inventing missing data.

Live display is inherently a dependency on another service. If it fails, the native activity link and labelled snapshots remain usable. The user can approve a scheduled refresh workflow separately; none was installed by this task.
