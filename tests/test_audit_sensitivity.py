import importlib

import numpy as np

study = importlib.import_module("scripts.73_audit_sensitivity")


def test_flags_follow_held_source_and_categories_do_not_overlap():
    # Commands at 1 and 4 hold source 0 (out of range) and source 3 (bound).
    # A spike flag on either cannot double-count its stronger category.
    source = np.array([0, 0, 2, 3, 3, 5])
    acted = np.array([False, True, False, False, True, True])
    in_range = np.array([False, True, True, True, True, True])
    bound = np.array([False, False, False, True, False, False])
    spike = np.ones(6, dtype=bool)
    assert study.source_counts(source, acted, in_range, bound, spike) == (1, 1, 1)
