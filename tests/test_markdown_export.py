"""Les noms électriques restent littéraux dans le tableau Markdown exporté."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugin'))
from Kicad_Via import service


class MarkdownExportTests(unittest.TestCase):
    def test_reset_and_markup_are_protected_on_both_sides(self):
        names={
            '~{CMD_RESET}':r'\~\{CMD\_RESET\}',
            'A|B':r'A\|B',
            r'BUS\PATH':r'BUS\\PATH',
            '`RESET`':r'\`RESET\`',
            '<RESET>':r'\<RESET\>',
            '&amp;':r'\&amp\;',
            '*ENABLE*':r'\*ENABLE\*',
        }
        rows=[dict(repere='I1.2',net=name,imprime=True,x_mm=172.6,y_mm=17.6)
              for name in names]
        with tempfile.TemporaryDirectory() as directory:
            for side in ('Top','Bottom'):
                output,staged=service.stage_output(Path(directory)/(side+'.md'),side,rows,None)
                text=staged.read_text(encoding='utf-8')
                self.assertTrue(text.startswith('# '+side+'\n\n| Repère | Net |'))
                for protected in names.values():
                    self.assertIn('| I1.2 | '+protected+' | true | 172.6 | 17.6 |',text)
                # Le nom du net et les données sources ne sont jamais renommés.
                self.assertEqual([row['net'] for row in rows],list(names))
