"""
Hiermit können einzelne Namensschilder generiert werden
"""
import pathlib
from typing import Dict, List
from convert2024 import BadgeInfo, writeBadgeCsv

path = pathlib.Path('extra_badges.csv')

extra_badges: List[BadgeInfo] = [
    BadgeInfo(name='Anna Zagorski', company='Umweltbundesamt (UBA)',
              notes='Panelist:innen'),
    BadgeInfo(name='Miriam Seyffarth', company='Open Source Business Alliance (OSBA)',
              notes='Panelist:innen'),
    BadgeInfo(name='Pierre Golz', company='FB Digitalisierung Stadt Herne',
              notes='Panelist:innen'),
    BadgeInfo(name='Alexander Smolianitski', company='Zentrum Digitale Souveränität (ZenDIS)',
              notes='Panelist:innen'),
    BadgeInfo(name='Prof. Heike Flämig', company='TUHH',
              notes=''),
    BadgeInfo(name='Laura Kuhlmann', company='Mitarbeitende der TUHH',
              notes=''),
    BadgeInfo(name='Leonie Dittrich', company='Mitarbeitende der TUHH',
              notes=''),
    BadgeInfo(name='Daniela Wagner', company='Mitarbeitende der TUHH',
              notes=''),
    BadgeInfo(name='Jacqueline Maaß', company='Mitarbeitende der TUHH',
              notes=''),
    BadgeInfo(name='Christoph Meyer', company='Mitarbeitende der TUHH',
              notes=''),
    BadgeInfo(name='Ineke Jäger', company='Mitarbeitende der TUHH',
              notes=''),
    BadgeInfo(name='', company='Mitarbeitende der TUHH',
              notes=''),
    BadgeInfo(name='', company='Mitarbeitende der TUHH',
              notes=''),
    BadgeInfo(name='', company='Mitarbeitende der TUHH',
              notes=''),
    BadgeInfo(name='', company='',
              notes=''),

]


extra_badges: Dict[str, BadgeInfo] = {b.name: b for b in extra_badges}

if __name__ == '__main__':
    path = path.resolve()
    writeBadgeCsv(extra_badges, path)

