// Unit-Tests

test('Dieser Test funktioniert.', () => {
    assert(1 + 2, 3);
});

test('Dieser Test schlägt fehl.', () => {
    assert(2 * 2, 5);
});

test('Test mit Parameter', (a, b, expected) => {
    assert(a + b, expected);
}, [
    [1, 2, 3],
    [4, 5, 9],
    [2, 2, 5],
]);