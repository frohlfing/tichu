import os

dst = (
    # sw   bl    gr    rt
    "Hu",                    # Hund
    "Ma",                    # MahJong
    "S2", "B2", "G2", "R2",  # 2
    "S3", "B3", "G3", "R3",  # 3
    "S4", "B4", "G4", "R4",  # 4
    "S5", "B5", "G5", "R5",  # 5
    "S6", "B6", "G6", "R6",  # 6
    "S7", "B7", "G7", "R7",  # 7
    "S8", "B8", "G8", "R8",  # 8
    "S9", "B9", "G9", "R9",  # 9
    "SZ", "BZ", "GZ", "RZ",  # 10
    "SB", "BB", "GB", "RB",  # Bube
    "SD", "BD", "GD", "RD",  # Dame
    "SK", "BK", "GK", "RK",  # König
    "SA", "BA", "GA", "RA",  # As
    "Dr",                    # Drache
    "Ph",                    # Phönix
)

src = (
    # sw   bl    gr    rt
    "dog",                    # Hund
    "mah",                    # MahJong
    "02a", "02b", "02c", "02d",  # 2
    "03a", "03b", "03c", "03d",  # 3
    "04a", "04b", "04c", "04d",  # 4
    "05a", "05b", "05c", "05d",  # 5
    "06a", "06b", "06c", "06d",  # 6
    "07a", "07b", "07c", "07d",  # 7
    "08a", "08b", "08c", "08d",  # 8
    "09a", "09b", "09c", "09d",  # 9
    "10a", "10b", "10c", "10d",  # 10
    "11a", "11b", "11c", "11d",  # Bube
    "12a", "12b", "12c", "12d",  # Dame
    "13a", "13b", "13c", "13d",  # König
    "14a", "14b", "14c", "14d",  # As
    "dra",                    # Drache
    "pho",                    # Phönix
)

# Verzeichnis mit den PNG-Dateien
directory = "\\Users\\frank\\Source\\PyCharm\\tichu\\web\\images\\cards"

# Mapping-Dictionary erstellen
mapping = dict(zip(src, dst))

# Dateien umbenennen
for filename in os.listdir(directory):
    if filename.endswith(".png"):
        basename = filename[:-4]  # Entferne ".png"
        if basename in mapping:
            new_name = mapping[basename] + ".png"
            os.rename(os.path.join(directory, filename), os.path.join(directory, new_name))
            print(f"Umbenannt: {filename} → {new_name}")

print("Alle Dateien wurden umbenannt!")