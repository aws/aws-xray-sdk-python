from aws_xray_sdk.core.utils.search_pattern import wildcard_match


def test_match_exact_positive():
    pat = 'foo'
    bar = 'foo'
    assert wildcard_match(pat, bar)


def test_match_exact_negative():
    pat = 'foo'
    bar = 'cat'
    assert not wildcard_match(pat, bar)


def test_single_wildcard_positive():
    pat = 'fo?'
    bar = 'foo'
    assert wildcard_match(pat, bar)


def test_single_wildcard_negative():
    pat = 'f?o'
    bar = 'boo'
    assert not wildcard_match(pat, bar)


def test_multiple_wildcard_positive():
    pat = '?o?'
    bar = 'foo'
    assert wildcard_match(pat, bar)


def test_multiple_wildcard_negative():
    pat = 'f??'
    bar = 'boo'
    assert not wildcard_match(pat, bar)


def test_glob_positive_zero_or_more():
    pat = 'foo*'
    bar = 'foo'
    assert wildcard_match(pat, bar)


def test_glob_negative_zero_or_more():
    pat = 'foo*'
    bar = 'fo0'
    assert not wildcard_match(pat, bar)


def test_glob_negative():
    pat = 'fo*'
    bar = 'boo'
    assert not wildcard_match(pat, bar)


def test_glob_and_single_positive():
    pat = '*o?'
    bar = 'foo'
    assert wildcard_match(pat, bar)


def test_glob_and_single_negative():
    pat = 'f?*'
    bar = 'boo'
    assert not wildcard_match(pat, bar)


def test_pure_wildcard():
    pat = '*'
    bar = 'foo'
    assert wildcard_match(pat, bar)


def test_exact_match():
    pat = '6573459'
    bar = '6573459'
    assert wildcard_match(pat, bar)


def test_misc():
    animal1 = '?at'
    animal2 = '?o?se'
    animal3 = '*s'

    vehicle1 = 'J*'
    vehicle2 = '????'

    assert wildcard_match(animal1, 'bat')
    assert wildcard_match(animal1, 'cat')
    assert wildcard_match(animal2, 'horse')
    assert wildcard_match(animal2, 'mouse')
    assert wildcard_match(animal3, 'dogs')
    assert wildcard_match(animal3, 'horses')

    assert wildcard_match(vehicle1, 'Jeep')
    assert wildcard_match(vehicle2, 'ford')
    assert not wildcard_match(vehicle2, 'chevy')
    assert wildcard_match('*', 'cAr')

    assert wildcard_match('*/foo', '/bar/foo')


def test_case_insensitivity():
    assert wildcard_match('Foo', 'Foo', False)
    assert wildcard_match('Foo', 'Foo', True)

    assert not wildcard_match('Foo', 'FOO', False)
    assert wildcard_match('Foo', 'FOO', True)

    assert wildcard_match('Fo*', 'Foo0', False)
    assert wildcard_match('Fo*', 'Foo0', True)

    assert not wildcard_match('Fo*', 'FOo0', False)
    assert wildcard_match('Fo*', 'FOo0', True)

    assert wildcard_match('Fo?', 'Foo', False)
    assert wildcard_match('Fo?', 'Foo', True)

    assert not wildcard_match('Fo?', 'FOo', False)
    assert wildcard_match('Fo?', 'FoO', False)
    assert wildcard_match('Fo?', 'FOO', True)


def test_no_globs():
    assert not wildcard_match('abcd', 'abc')


def test_edge_case_globs():
    assert wildcard_match('', '')
    assert wildcard_match('a', 'a')
    assert wildcard_match('*a', 'a')
    assert wildcard_match('*a', 'ba')
    assert wildcard_match('a*', 'a')
    assert wildcard_match('a*', 'ab')
    assert wildcard_match('a*a', 'aa')
    assert wildcard_match('a*a', 'aba')
    assert wildcard_match('a*a', 'aaa')
    assert wildcard_match('a*a*', 'aa')
    assert wildcard_match('a*a*', 'aba')
    assert wildcard_match('a*a*', 'aaa')
    assert wildcard_match('a*a*', 'aaaaaaaaaaaaaaaaaaaaaaaaaa')
    assert wildcard_match('a*b*a*b*a*b*a*b*a*',
                          'akljd9gsdfbkjhaabajkhbbyiaahkjbjhbuykjakjhabkjhbabjhkaabbabbaaakljdfsjklababkjbsdabab')
    assert not wildcard_match('a*na*ha', 'anananahahanahana')


def test_multi_globs():
    assert wildcard_match('*a', 'a')
    assert wildcard_match('**a', 'a')
    assert wildcard_match('***a', 'a')
    assert wildcard_match('**a*', 'a')
    assert wildcard_match('**a**', 'a')

    assert wildcard_match('a**b', 'ab')
    assert wildcard_match('a**b', 'abb')

    assert wildcard_match('*?', 'a')
    assert wildcard_match('*?', 'aa')
    assert wildcard_match('*??', 'aa')
    assert not wildcard_match('*???', 'aa')
    assert wildcard_match('*?', 'aaa')

    assert wildcard_match('?', 'a')
    assert not wildcard_match('??', 'a')

    assert wildcard_match('?*', 'a')
    assert wildcard_match('*?', 'a')
    assert not wildcard_match('?*?', 'a')
    assert wildcard_match('?*?', 'aa')
    assert wildcard_match('*?*', 'a')

    assert not wildcard_match('*?*a', 'a')
    assert wildcard_match('*?*a*', 'ba')
