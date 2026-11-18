import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from run import fulltext_lesson

if __name__ == '__main__':
    fulltext_lesson('03_fulltext_lesson',
        'Create a five-minute mini-lesson on photosynthesis: learning goal, scaffolded explanation, and two comprehension checks with answers. Clearly distinguish light-dependent reactions from the Calvin cycle. Use only the retrieved textbook.',
        dict(query='site:openstax.org books biology 2e overview photosynthesis', count=4, extraction=dict(extraction_mode='highlights')),['openstax.org'])
