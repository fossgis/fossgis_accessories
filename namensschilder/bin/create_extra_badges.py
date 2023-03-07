"""
Hiermit können einzelne Namensschilder generiert werden
"""
import pathlib
from typing import Dict, List
from convert2023 import BadgeInfo, writeBadgeCsv

path = pathlib.Path('extra_badges.csv')

extra_badges: List[BadgeInfo] = [
    BadgeInfo(name='Josephine Auerbach', company='Humboldt-Universität zu Berlin',
              notes='Eröffnungsgast'),
    BadgeInfo(name='Prof. Dr. Christoph Schneider', company='Humboldt-Universität zu Berlin',
              notes='Eröffnungsgast'),
    BadgeInfo(name='Wolfgang Crom', company='Staatsbibliothek zu Berlin',
              notes='Eröffnungsgast'),
    BadgeInfo(name='Dr. Ralf Kleindiek', company='Senatsverwaltung für Inneres, Digitalisierung und Sport',
              notes='Eröffnungsgast'),
]

path = path.resolve()
extra_badges: Dict[str, BadgeInfo] = {b.name: b for b in extra_badges}
writeBadgeCsv(extra_badges, path)

