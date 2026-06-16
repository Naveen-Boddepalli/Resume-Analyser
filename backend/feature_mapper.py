def estimate_coding_score(parsed_data: dict) -> float:
    score = 50.0
    skills = parsed_data.get('skills_list', [])
    coding_skills = {'python', 'java', 'c++', 'javascript', 'go', 'ruby'}
    matched = len(set(skills).intersection(coding_skills))
    score += matched * 10
    
    if parsed_data.get('projects_count', 0) > 2:
        score += 10
    return min(score, 100.0)

def estimate_communication_score(parsed_data: dict) -> float:
    score = 60.0
    if parsed_data.get('internships_count', 0) > 0:
        score += 20
    return min(score, 100.0)

def estimate_leadership_score(parsed_data: dict) -> float:
    score = 50.0
    if parsed_data.get('projects_count', 0) > 3:
        score += 20
    return min(score, 100.0)
