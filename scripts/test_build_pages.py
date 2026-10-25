"""Course navigation survives a rebuild and preserves existing lecture URLs."""
import json
from pathlib import Path
import tempfile
import unittest
import build_pages as build


class CoursePagesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'teaching').mkdir()
        (self.root / 'teaching/index.html').write_text((build.ROOT / build.TEMPLATE).read_text())
        (self.root / 'index.html').write_text('<!-- home-courses:start --><!-- home-courses:end -->')
        (self.root / 'materials/Mechanics').mkdir(parents=True)
        (self.root / 'materials/Mechanics/open.md').write_text('# 开放章节\n\n正文包含测试内容。\n\n## 第一节\n')
        self.data = {'courses': [
            {'id': 'mechanics', 'title': '理论力学', 'description': '课程介绍', 'visitCounter': True, 'materials': [
                {'number': 0, 'title': '开放章节', 'file': 'materials/Mechanics/open.md'},
                {'number': 1, 'title': '未开放', 'file': 'materials/Mechanics/closed.md', 'available': False}]},
            {'id': 'computation', 'title': '计算物理', 'description': '正在整理', 'materials': []}]}
        self.save()

    def save(self):
        (self.root / 'materials.json').write_text(json.dumps(self.data, ensure_ascii=False))

    def test_courses_have_distinct_routes_and_note_returns_to_its_course(self):
        self.assertEqual(build.build(self.root), 1)
        course = (self.root / 'teaching/courses/mechanics/index.html').read_text()
        self.assertIn('data-course="mechanics"', course)
        self.assertIn('data-root="../../../"', course)
        self.assertIn('<h1 id="library-title">理论力学</h1>', course)
        self.assertIn('teaching-visit-count', course)
        self.assertIn('理论力学页面访问次数', course)
        note = (self.root / 'teaching/notes/Mechanics/open.html').read_text()
        self.assertIn('href="../../../teaching/courses/mechanics/"', note)
        self.assertIn('data-note="materials/Mechanics/open.md"', note)
        self.assertNotIn('teaching-visit-count', note)
        self.assertFalse((self.root / 'teaching/notes/Mechanics/closed.html').exists())
        empty = (self.root / 'teaching/courses/computation/index.html').read_text()
        self.assertIn('data-course="computation"', empty)
        self.assertNotIn('teaching-visit-count', empty)
        self.assertIn('<h1 id="library-title">计算物理</h1>', empty)
        sitemap = (self.root / 'sitemap.xml').read_text()
        self.assertIn('teaching/courses/computation/', sitemap)
        self.assertNotIn('closed.html', sitemap)

    def test_rebuild_is_repeatable_and_new_courses_reach_both_entry_pages(self):
        build.build(self.root)
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        build.build(self.root)
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.data['courses'].append({'id': 'future', 'title': '新课程', 'materials': []})
        self.save()
        build.build(self.root)
        for name in ('index.html', 'teaching/index.html'):
            self.assertIn('teaching/courses/future/', (self.root / name).read_text())
        self.assertTrue((self.root / 'teaching/courses/future/index.html').is_file())
        for required in ('index.html', 'teaching/index.html', 'teaching/courses'):
            self.assertIn(required, build.GENERATED)

    def test_invalid_course_path_cannot_escape_generated_directory(self):
        self.data['courses'][0]['id'] = '../outside'
        self.save()
        with self.assertRaises(ValueError):
            build.build(self.root)


if __name__ == '__main__':
    unittest.main()
