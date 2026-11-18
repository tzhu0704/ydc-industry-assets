import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from run import save
from you_api import custom_search, CUSTOM_URL
from education_utils import allowed_url

if __name__ == '__main__':
    request=dict(engine='google_images',q='water cycle diagram evaporation condensation precipitation USGS')
    response=custom_search(**request)
    candidates=[]
    for hit in response.get('images_results',[]):
        page=hit.get('link',''); image=hit.get('original','')
        if allowed_url(page,['usgs.gov','noaa.gov','nasa.gov']) and image.startswith('https://'):
            candidates.append(dict(title=hit.get('title',''),source_page=page,image_url=image,
                licence_status='not_verified',diagram_accuracy='not_visually_verified',role='teacher_review_candidate'))
    save('05_learning_diagrams',[dict(endpoint=CUSTOM_URL,method='GET',request=request,response=response)],[],
        dict(candidates=candidates,next_action='Review source page, diagram labels and usage terms before showing to learners; no image is treated as a solved problem.'),
        dict(returned=len(response.get('images_results',[])),allowed_source_candidates=len(candidates),
             boundary='URL filtering only; no OCR, visual correctness or licence verification'))
