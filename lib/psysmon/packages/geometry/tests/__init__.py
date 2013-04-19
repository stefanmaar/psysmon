def load_tests(loader, standard_tests, pattern):
    import os.path
    import psysmon
    this_dir = os.path.dirname(__file__)
    toplevel_dir = os.path.dirname(psysmon.__file__)
    if pattern is None:
        pattern = 'test*.py'
    package_tests = loader.discover(start_dir = this_dir, pattern = pattern, top_level_dir = toplevel_dir)
    standard_tests.addTests(package_tests)
    return standard_tests
