EXTRACT_JD = """Read this job description and extract what the employer requires.

Job description:
{jd}

Reply with JSON only:
{{"title": "job title",
  "must_have": ["skills/technologies explicitly required"],
  "nice_to_have": ["skills marked preferred, bonus or nice to have"],
  "responsibilities": ["up to 6 short phrases"]}}"""

EXTRACT_RESUME = """Read this resume and extract facts. Do not infer skills that are not written in it.

Resume:
{resume}

Reply with JSON only:
{{"name": "candidate name or empty",
  "years_experience": number of years of professional experience including internships (a number, may be fractional),
  "skills": ["every skill/tool/technology the resume explicitly mentions"]}}"""

ANALYZE = """You are a hiring manager screening a candidate for: {title}.

Requirement coverage (computed from the resume text):
{coverage}

Resume:
{resume}

Write a short, honest assessment. Reply with JSON only:
{{"strengths": ["2-4 points, each tied to specific resume evidence"],
  "gaps": ["the most important missing or weak requirements"],
  "verdict": "one of: strong fit, good fit, stretch, poor fit",
  "summary": "two sentences"}}"""

SUGGEST = """Improve this resume for the job below WITHOUT inventing anything.

Rules:
- Only rephrase the candidate's existing bullets.
- Never add tools, numbers, employers or results that are not in the original bullet.
- Use the job's wording for things the candidate genuinely did.
- For gaps, do not write bullets; list them under "learn" with a concrete way to close each gap.

Job title: {title}
Job keywords the candidate already has: {matched}
Job requirements the candidate lacks: {missing}

Candidate's bullets:
{bullets}

Reply with JSON only:
{{"rewrites": [{{"original": "exact original bullet", "improved": "rephrased bullet"}}],
  "learn": [{{"skill": "missing skill", "how": "one concrete step, e.g. a small project"}}]}}"""
