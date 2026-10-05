#!/usr/bin/env python3
"""Regression checks for instruction routing failures that silently drop policy."""
from pathlib import Path
import tempfile
import unittest
import check_instruction_docs as checker


class InstructionDocsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'rules').mkdir()
        for name in ('AGENTS.md', 'CLAUDE.md'):
            (self.root / name).write_text(f'# Entry\n**Doc link:** https://example.org/{name}\nRead INDEX_RULES.md.\n')
        detail, routes = [], []
        for kind, numbers in checker.EXPECTED.items():
            for number in sorted(numbers):
                detail.append(f'## {kind.title()} Rule {number}\n\nRequired action.\n')
                routes.append(f'[{kind} {number}](rules/contract.md#{kind}-rule-{number})')
        (self.root / 'rules/contract.md').write_text('\n'.join(detail))
        (self.root / 'INDEX_RULES.md').write_text('\n'.join(routes))
        (self.root / 'CATALOG.md').write_text('# Catalog\n')

    def errors(self):
        return checker.check(self.root)[0]

    def test_complete_portable_contract(self):
        self.assertEqual(self.errors(), [])

    def test_long_single_line_is_not_hidden_by_line_count(self):
        for name in ('AGENTS.md', 'CLAUDE.md'):
            (self.root / name).write_text('x' * 6145)
        self.assertTrue(any('bytes exceeds' in e for e in self.errors()))

    def test_entrypoint_drift_is_detected(self):
        (self.root / 'CLAUDE.md').write_text('Contradictory instructions.\n')
        self.assertIn('AGENTS.md and CLAUDE.md shared content differs', self.errors())

    def test_missing_and_duplicate_rules_are_detected(self):
        p = self.root / 'rules/contract.md'
        p.write_text(p.read_text().replace('## Trigger Rule 61', '## Trigger Rule 60'))
        errors = self.errors()
        self.assertIn('Duplicate trigger rule 60', errors)
        self.assertTrue(any('missing=[61]' in e for e in errors))

    def test_unrouted_rule_is_detected(self):
        p = self.root / 'INDEX_RULES.md'
        p.write_text('\n'.join(line for line in p.read_text().splitlines() if '#trigger-rule-43)' not in line))
        self.assertTrue(any('does not route' in e and '43' in e for e in self.errors()))

    def test_missing_file_and_fragment_are_detected(self):
        p = self.root / 'CATALOG.md'
        p.write_text('# Catalog\n[missing](not-here.md)\n[wrong](rules/contract.md#not-here)\n')
        errors = self.errors()
        self.assertTrue(any('missing link' in e for e in errors))
        self.assertTrue(any('missing anchor' in e for e in errors))

    def test_swapped_numbered_routes_are_detected(self):
        p = self.root / 'INDEX_RULES.md'
        text = p.read_text().replace('[trigger 46]', '[46]').replace('[trigger 51]', '[51]')
        text = text.replace('#trigger-rule-46)', '#trigger-rule-TEMP)').replace('#trigger-rule-51)', '#trigger-rule-46)').replace('#trigger-rule-TEMP)', '#trigger-rule-51)')
        p.write_text(text)
        errors = self.errors()
        self.assertIn('Index label 46 points to trigger rule 51', errors)
        self.assertIn('Index label 51 points to trigger rule 46', errors)

    def test_missing_index_reports_a_check_failure(self):
        (self.root / 'INDEX_RULES.md').unlink()
        self.assertIn('Missing startup file: INDEX_RULES.md', self.errors())

    def test_example_links_and_remote_links_are_not_local_files(self):
        (self.root / 'CATALOG.md').write_text('# Catalog\n```md\n[example](not-here.md)\n```\n[web](https://example.org/x)\n')
        self.assertEqual(self.errors(), [])


if __name__ == '__main__':
    unittest.main()
