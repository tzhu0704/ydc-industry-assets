import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from run import search_lesson

if __name__ == '__main__':
    search_lesson('02_concept_correction',
        'A high-school learner says heavier objects always fall faster. Explain the difference between ideal free fall without air resistance and falling through air. Give a formative question without inventing an experiment result.',
        [dict(query='site:openstax.org free fall mass air resistance acceleration', count=4, extraction=dict(extraction_mode='highlights'))],['openstax.org'])
