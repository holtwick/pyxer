# -*- coding: UTF-8 -*-

import unittest
import pyxer.routing

class PyxerRoutingTestCase(unittest.TestCase):

    def cmp(self, a, b):
        self.assertEqual(a.strip(), b.strip())

    def testRouting(self):
        pyxer.routing.testing()

def buildTestSuite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
