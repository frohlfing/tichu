import itertools


def get_max_rank(row: tuple, m: int):
    # row: row[0] == Phönix, row[1] bis row[14] == Rang 1 bis 14
    for r in range(14, m - 1, -1):  # [14 ... 5] (höchste Rang zuerst)
        r_start = r - m + 1
        r_end = r + 1  # exklusiv
        if row[0]:  # mit Phönix
            if any(all(row[i] for i in range(r_start, r_end) if i != j) for j in range(r_start, r_end)):
                return r
        else:  # ohne Phönix
            if all(row[i] for i in range(r_start, r_end)):  # Karten für die Kombination verfügbar?
                return r
    return False


def is_already_in_table(table: list, row: tuple, m: int, r: int):
    muster = row[r - m + 1:]
    for row_ in table:
        if row_[0] == row[0] and row_[r - m + 1:] == muster:
            return True
    return False


def generate_table(m: int):  # pragma: no cover
    c_all = 0
    c_matches = 0
    c_unique = 0
    table = []
    for row in itertools.product(range(2), repeat=15):
        c_all += 1
        r = get_max_rank(row, m)
        if r:
            c_matches += 1
            found = is_already_in_table(table, row, m, r)
            if not found:
                c_unique += 1
                table.append(row)
                print(row, f"r: {r}, muster: {row[r - m + 1:]}, start_index: {r - m + 1}, phoenix: {row[0]}")
            # else:
            #     print(row, f"r: {r}")

    print("all:", c_all)
    print("matches:", c_matches)
    print("unique:", c_unique)


if __name__ == '__main__':  # pragma: no cover
    generate_table(5)