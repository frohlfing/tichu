# Release in Github erstellen

- Schritt 1: Tag erstellen (falls noch nicht geschehen)

Falls du noch keinen Tag hast, erstelle einen neuen:
```bash
git tag -a v0.3.0 -m "Version 0.3.0 Release"
git push origin v0.3.0
git push --tags
```

- Schritt 2: Offizielles Release auf GitHub
  - Gehe zu GitHub und öffne dein Repository.
  - Klicke oben auf "Releases" / "Draft a new release" / v0.3.0
  - Beschreibung für das Release eingeben (Änderungen, Features, Bugfixes etc.)
  - "Publish release"