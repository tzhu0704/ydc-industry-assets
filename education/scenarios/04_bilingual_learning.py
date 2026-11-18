import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from run import search_lesson

if __name__ == '__main__':
    search_lesson('04_bilingual_learning',
        'For a bilingual high-school student, explain why the seasons change; give an English-Chinese glossary (axial tilt, orbit, hemisphere) and one comprehension check. Use both English and Chinese evidence, and flag any disagreement rather than forcing them to match.',
        [dict(query='site:science.nasa.gov earth seasons axial tilt',language='EN',count=3,extraction=dict(extraction_mode='highlights')),
         dict(query='site:hk.space.museum 四季 地軸 傾斜',language='ZH-HANT',count=3,extraction=dict(extraction_mode='highlights'))],
        ['nasa.gov','hk.space.museum'])
