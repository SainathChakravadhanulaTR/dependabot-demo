"""Trivial demo app — exists only so the deps in requirements.txt are
actually imported, which makes the security-update path (CVE detection)
look meaningful in the Security tab."""

import click
import requests
import yaml


@click.command()
def main() -> None:
    response = requests.get("https://api.github.com", timeout=10)
    click.echo(f"GitHub API status: {response.status_code}")
    click.echo(yaml.safe_dump({"demo": "dependabot", "ok": True}))


if __name__ == "__main__":
    main()
