import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from run import search_lesson
from education_utils import math_check

if __name__ == '__main__':
    coefficients=[1,-5,6]; roots=[2,3]
    assert math_check(coefficients,roots)
    search_lesson('01_grounded_math',
        'Original typed exercise, not an OCR result: solve x^2 - 5x + 6 = 0 by factoring. Show a hint before the worked answer. Code separately verified roots [2,3] by substitution; explain the zero-product property using the sources. Do not say the exact exercise was found online.',
        [dict(query='site:openstax.org quadratic equations factoring zero product property', count=4, extraction=dict(extraction_mode='highlights'))],
        ['openstax.org'], extra=dict(deterministic_math_check=dict(coefficients=coefficients,roots=roots,residuals=[0,0]),input_modality='typed text; no OCR or image understanding performed'))
