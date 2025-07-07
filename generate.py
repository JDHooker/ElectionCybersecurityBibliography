import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict
import copy
import os
import subprocess
from datetime import datetime
import platform

# Load BibTeX file
with open("references.bib", "r") as bib_file:
    bib_database = bibtexparser.load(bib_file)

# BibTeX writer for rendering entries
writer = BibTexWriter()
writer.indent = '  '
writer.order_entries_by = None

def indent_bibtex(bibtex_str, indent="  "):
    lines = bibtex_str.splitlines()
    if not lines:
        return ""
    lines[0] = lines[0].strip()  # Remove all leading/trailing whitespace from first line
    if len(lines) > 2:
        lines[1:-1] = [indent + line for line in lines[1:-1]]  # Indent all except first and last
    elif len(lines) == 2:
        lines[1] = indent + lines[1]
    lines[-1] = lines[-1].lstrip()
    return "\n".join(lines)

# Group by year
entries_by_year = defaultdict(list)
for entry in bib_database.entries:
    # Copy entry and generate clean BibTeX string
    entry_copy = copy.deepcopy(entry)
    db = bibtexparser.bibdatabase.BibDatabase()
    db.entries = [entry_copy]
    bib_str = writer.write(db).strip()
    entry['bibtex'] = indent_bibtex(bib_str)

    year = entry.get("year", "Unknown")
    entries_by_year[year].append(entry)

    pdf_folder = "pdf"
    pdf_filename = f"{entry['ID']}.pdf"
    pdf_path = os.path.join(pdf_folder, pdf_filename)
    if os.path.isfile(pdf_path):
        entry['cached_url'] = pdf_path

# Sort years descending
sorted_years = sorted(entries_by_year.keys(), reverse=True)

# Get latest git commit date
try:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%cI"],
        capture_output=True,
        text=True,
        check=True
    )
    latest_commit_iso = result.stdout.strip()
    # Format date nicely, e.g. "July 5, 2025"
    dt = datetime.fromisoformat(latest_commit_iso)
    if platform.system() == "Windows":
        latest_commit_date = dt.strftime("%B %#d, %Y")
    else:
        latest_commit_date = dt.strftime("%B %-d, %Y")
except Exception as e:
    print(f"Warning: Could not get git commit date: {e}")
    latest_commit_date = "Unknown"

github_commits_url = "https://github.com/JDHooker/ElectionCybersecurityBibliography/commits/main"
github_url = "https://github.com/JDHooker/ElectionCybersecurityBibliography"

# Render HTML with Jinja
env = Environment(loader=FileSystemLoader("templates"))
template = env.get_template("index.html.j2")
rendered_html = template.render(
    entries_by_year=entries_by_year,
    sorted_years=sorted_years,
    last_updated=latest_commit_date,
    commits_url=github_commits_url,
    github_url=github_url,
)

# Write output
with open("index.html", "w", encoding="utf-8") as f:
    f.write(rendered_html)

print("index.html generated")
