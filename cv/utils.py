import re

def clean_cv_text(text):
    if not text:
        return text
    
    # remove LaTeX math
    text = re.sub(r'\$\\cdot\$', ' • ', text)
    text = re.sub(r'\$[^$]*\$', '', text)
    
    # remove backslash & escape characters
    text = re.sub(r'\\\\', ' ', text)
    text = re.sub(r'\\&', '&', text)
    text = re.sub(r'\\n', '\n', text)
    text = re.sub(r'\\(?![a-zA-Z])', '', text)
    text = re.sub(r'\\(?=[a-zA-Z])', '', text)
    
    # remove HTML/markdown artifacts
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    
    # fix URLs that got broken by cdot(.) replacement
    text = re.sub(r'https: //', 'https://', text)
    text = re.sub(r'http: //', 'http://', text)
    
    # spacing
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text) 
    text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE) 

    # fix formatting issues
    text = re.sub(r'\n- ([a-z])', lambda m: f'-{m.group(1)}', text)
    
    # fix bullet points
    text = re.sub(r'\s*•\s*', '\n• ', text) 
    text = re.sub(r'^\s*-\s+', '- ', text, flags=re.MULTILINE)  
    text = re.sub(r'^\s*#\s*', '# ', text, flags=re.MULTILINE)
    
    # remove punctuation
    text = re.sub(r'\.{3,}', '...', text)
    text = re.sub(r'-{2,}', '--', text)
    
    # clean up email and link format
    text = re.sub(r'\s+@\s+', '@', text)
    text = re.sub(r'\s+\.\s+com', '.com', text)
    
    # remove extra whitespace & separators
    text = re.sub(r'\s*:\s*', ': ', text)
    text = re.sub(r'\s*,\s*', ', ', text)
    text = re.sub(r'\s*;\s*', '; ', text)
    
    # final cleanup
    text = text.strip()
    
    return text