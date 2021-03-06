# -*- coding: UTF-8 -*-
"""
Bug test cases
@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""

import unittest

import testutils

from yokadi.ycli import tui
from yokadi.ycli.main import YokadiCmd
from yokadi.core.db import Task
from yokadi.core.yokadiexception import YokadiException


class BugTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()
        tui.clearInputAnswers()
        self.cmd = YokadiCmd()

    def testAdd(self):
        tui.addInputAnswers("y", "2", "4", "123")
        self.cmd.do_bug_add("x t1")

        tui.addInputAnswers("n")
        self.cmd.do_bug_add("notExistingProject newBug")

        tasks = list(Task.select())
        result = [x.title for x in tasks]
        expected = [u"t1"]
        self.assertEqual(result, expected)

        kwDict = Task.get(1).getKeywordDict()
        self.assertEqual(kwDict, dict(_severity=2, _likelihood=4, _bug=123))

        for bad_input in ("",  # No project
                          "x"):  # No task name
            self.assertRaises(YokadiException, self.cmd.do_bug_add, bad_input)

# vi: ts=4 sw=4 et
