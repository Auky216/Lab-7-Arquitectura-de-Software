import requests
import time
import subprocess
import os
import signal

# Iniciar servidor
server_process = subprocess.Popen(['python', 'main.py'])
time.sleep(10)  # Esperar startup

try:
    # Test 1: Search Performance
    login_response = requests.post('http://localhost:3000/api/v1/auth/login', 
                                 json={'email': 'student@utec.edu.pe', 'password': 'password123'})
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Probar búsquedas
    violations = 0
    for query in ['machine learning', 'AI', 'deep learning']:
        start = time.time()
        response = requests.get('http://localhost:3000/api/v1/search', 
                              params={'q': query}, headers=headers)
        duration_ms = (time.time() - start) * 1000
        
        if duration_ms > 3000:
            violations += 1
            print(f"VIOLATION: {query} took {duration_ms:.2f}ms")
        else:
            print(f"PASS: {query} took {duration_ms:.2f}ms")
    
    print(f"Fitness Function 1: {'PASS' if violations == 0 else 'FAIL'}")
    
    # Test 2: Data Integrity
    response = requests.get('http://localhost:3000/api/v1/search', 
                          params={'limit': 100}, headers=headers)
    papers = response.json()['data']
    
    issues = 0
    for paper in papers:
        if not paper.get('title') or len(paper['title']) < 5:
            issues += 1
        if not paper.get('authors') or len(paper['authors']) == 0:
            issues += 1
    
    integrity = ((len(papers) - issues) / len(papers)) * 100
    print(f"Data Integrity: {integrity:.1f}%")
    print(f"Fitness Function 2: {'PASS' if integrity >= 99.5 else 'FAIL'}")

finally:
    # Matar servidor
    server_process.terminate()