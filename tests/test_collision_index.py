"""Équivalence des collisions, y compris contacts et ajout incrémental."""
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugin'))
from shapely.geometry import Point,box,LineString,Polygon
from shapely.ops import unary_union
from Kicad_Via.geometry import CollisionIndex,leader_obstacles


class CollisionTests(unittest.TestCase):
    def test_matches_union_boundaries_and_incremental_additions(self):
        rng=random.Random(407)
        parts=[box(0,0,1,1),box(1,0,2,1),Polygon()]
        parts += [Point(rng.uniform(-5,5),rng.uniform(-5,5)).buffer(.3) for _ in range(30)]
        index=CollisionIndex(parts)
        queries=[Point(1,1),Point(2,1),LineString([(2,0),(2,1)]),Polygon()]
        queries += [Point(rng.uniform(-6,6),rng.uniform(-6,6)).buffer(.2) for _ in range(150)]
        for step in range(3):
            union=unary_union(parts)
            for q in queries:self.assertEqual(index.intersects(q),union.intersects(q))
            added=box(3+step,0,4+step,1);parts.append(added);index.add(added)
        self.assertFalse(CollisionIndex([]).intersects(Point(0,0)))

    def test_center_exception_matches_union_with_overlapping_obstacles(self):
        solid=box(-1,.25,1,.4);fixed=solid.buffer(.2)
        apertures={'own':Point(0,0).buffer(.6),'neighbor':Point(.7,0).buffer(.4)}
        index=CollisionIndex([fixed.difference(apertures['own']),solid,apertures['neighbor']])
        expected=leader_obstacles(fixed,apertures,'own',solid)
        for x in range(-20,21):
            q=LineString([(0,0),(x/10,-2)]).buffer(.08)
            self.assertEqual(index.intersects(q),expected.intersects(q))
