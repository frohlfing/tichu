import re


def get_version_from_readme():
    with open("README.md", "r", encoding="utf-8") as file:
        content = file.read()

    match = re.search(r"Version\-(\d+\.\d+\.\d+)", content)
    return match.group(1) if match else "Version nicht gefunden"


print(f"Aktuelle Version: {get_version_from_readme()}")
