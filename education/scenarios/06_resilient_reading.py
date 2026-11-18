import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from run import fulltext_lesson

if __name__ == '__main__':
    fulltext_lesson('06_resilient_reading',
        'Build a short learning card explaining how a scientific hypothesis differs from a theory, with one comprehension check. Keep the learning card tied to the actually usable evidence.',
        dict(query='site:openstax.org biology scientific method hypothesis theory',count=4,extraction=dict(extraction_mode='highlights')),
        ['openstax.org'],reliability=True)
