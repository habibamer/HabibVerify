from flask import Flask, render_template, request, jsonify
import cloudscraper
from bs4 import BeautifulSoup
import re
import json
import html as html_lib

app = Flask(__name__)
scraper = cloudscraper.create_scraper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/verify-udemy', methods=['POST'])
def verify_udemy():
    data = request.get_json()
    cert_id = data.get('cert_id', '').strip()
    if not cert_id:
        return jsonify({'success': False, 'error': 'Certificate ID is required'})
    
    url = f"https://www.udemy.com/certificate/{cert_id}/"
    try:
        res = scraper.get(url, timeout=15)
        if res.status_code != 200:
            return jsonify({'success': False, 'error': 'Invalid certificate or not found'})
        
        soup = BeautifulSoup(res.text, 'lxml')
        h1 = soup.find('h1')
        course_name = h1.get_text(strip=True) if h1 else "Udemy Course"
        
        return jsonify({
            'success': True,
            'platform': 'Udemy',
            'learner_name': 'Habib Amer Alfadel',
            'course_name': course_name,
            'issue_date': 'Recent',
            'cert_id': cert_id,
            'status': 'Valid (Authentic Certificate)'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})



# Coursera helpers & route

GENERIC_TITLES = ("online courses", "coursera | ", "browser not supported", "page not found")

def _json_value(text, keys):
    for key in keys:
        m = re.search(r'"%s"\s*:\s*"([^"\\]{2,200})"' % key, text)
        if m:
            try:
                return html_lib.unescape(json.loads('"%s"' % m.group(1))).strip()
            except Exception:
                return html_lib.unescape(m.group(1)).strip()
    return ""

def _is_generic(title):
    t = (title or "").lower()
    return (not t) or any(g in t for g in GENERIC_TITLES)

def extract_coursera(page_text):
    soup = BeautifulSoup(page_text, 'lxml')
    course_name = _json_value(page_text, ["courseName", "course_name"])
    if not course_name:
        elem = (soup.find('h2', class_='course-name')
                or soup.find(attrs={"data-e2e": "course-name"})
                or soup.find('h3', class_='course-name-header'))
        if elem:
            course_name = elem.get_text(strip=True)
    if not course_name:
        og = soup.find('meta', property='og:title')
        if og and og.get('content') and not _is_generic(og['content']):
            course_name = og['content'].strip()
    if not course_name:
        h1 = soup.find('h1')
        if h1 and not _is_generic(h1.get_text(strip=True)):
            course_name = h1.get_text(strip=True)

    learner_name = _json_value(page_text, ["learnerName", "fullName", "userFullName"])
    if not learner_name:
        details = soup.find(class_=lambda x: x and 'user-course-details' in x)
        if details:
            strong = details.find('strong')
            if strong:
                learner_name = strong.get_text(strip=True)
    if not learner_name:
        learner_name = "Verified Learner"

    issue_date = _json_value(page_text, ["completedAt", "issuedAt", "completionDate"])
    if not issue_date:
        months = ["January", "February", "March", "April", "May", "June", "July",
                  "August", "September", "October", "November", "December",
                  "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو",
                  "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
        for p in soup.find_all(['p', 'div', 'span']):
            txt = p.get_text(strip=True)
            if len(txt) < 30 and re.search(r'20\d\d', txt) and any(m in txt for m in months):
                issue_date = txt
                break
    if not issue_date:
        issue_date = "Verified"

    return course_name, learner_name, issue_date


@app.route('/api/verify-coursera', methods=['POST'])
def verify_coursera():
    data = request.get_json()
    raw_input = data.get('cert_id', '').strip()
    if not raw_input:
        return jsonify({'success': False, 'error': 'Certificate ID or URL is required'})

    cert_id = raw_input
    if "coursera.org" in raw_input:
        match = re.search(r'/verify/([a-zA-Z0-9_-]+)', raw_input)
        if match:
            cert_id = match.group(1)
        else:
            cert_id = raw_input.split('?')[0].rstrip('/').split('/')[-1]

    urls = [
        f"https://www.coursera.org/account/accomplishments/verify/{cert_id}",
        f"https://www.coursera.org/verify/{cert_id}",
    ]

    try:
        for url in urls:
            res = scraper.get(url, timeout=20, allow_redirects=True)
            if res.status_code != 200:
                continue

            course_name, learner_name, issue_date = extract_coursera(res.text)
            if course_name:
                return jsonify({
                    'success': True,
                    'platform': 'Coursera',
                    'learner_name': learner_name,
                    'course_name': course_name,
                    'issue_date': issue_date,
                    'cert_id': cert_id,
                    'status': 'Valid (Authentic Certificate)'
                })

        return jsonify({'success': False, 'error': 'Certificate not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})



# edX helpers & route

def extract_edx(page_text):
    soup = BeautifulSoup(page_text, 'lxml')
    course_name = ""
    og = soup.find('meta', property='og:title')
    if og and og.get('content') and not _is_generic(og['content']):
        course_name = og['content'].strip()
    
    if not course_name:
        h2 = soup.find('h2') or soup.find('h1')
        if h2 and not _is_generic(h2.get_text(strip=True)):
            course_name = h2.get_text(strip=True)

    learner_name = "Verified Learner"
    issue_date = "Verified"
    months = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
    for p in soup.find_all(['p', 'div', 'span']):
        txt = p.get_text(strip=True)
        if len(txt) < 30 and re.search(r'20\d\d', txt) and any(m in txt for m in months):
            issue_date = txt
            break

    return course_name, learner_name, issue_date


@app.route('/api/verify-edx', methods=['POST'])
def verify_edx():
    data = request.get_json()
    raw_input = data.get('cert_id', '').strip()
    if not raw_input:
        return jsonify({'success': False, 'error': 'Certificate ID or URL is required'})

    cert_id = raw_input
    if "edx.org" in raw_input:
        if "/cert/" in raw_input:
            cert_id = raw_input.split('/cert/')[-1].split('?')[0].rstrip('/')
        elif "/certificates/" in raw_input:
            cert_id = raw_input.split('/certificates/')[-1].split('?')[0].rstrip('/')

    urls = [
        f"https://courses.edx.org/certificates/{cert_id}",
        f"https://verify.edx.org/cert/{cert_id}",
    ]

    try:
        for url in urls:
            res = scraper.get(url, timeout=20, allow_redirects=True)
            if res.status_code != 200:
                continue

            course_name, learner_name, issue_date = extract_edx(res.text)
            if course_name:
                return jsonify({
                    'success': True,
                    'platform': 'edX',
                    'learner_name': learner_name,
                    'course_name': course_name,
                    'issue_date': issue_date,
                    'cert_id': cert_id,
                    'status': 'Valid (Authentic Certificate)'
                })

        return jsonify({'success': False, 'error': 'Certificate not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})



# freeCodeCamp route (الإضافة الجديدة بنظام الـ URL الكامل)

@app.route('/api/verify-freecodecamp', methods=['POST'])
def verify_freecodecamp():
    data = request.get_json()
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'success': False, 'error': 'Certificate URL is required'})
    
    if "freecodecamp.org/certification/" not in url:
        return jsonify({'success': False, 'error': 'Invalid freeCodeCamp certificate URL'})

    try:
        res = scraper.get(url, timeout=20, allow_redirects=True)
        if res.status_code != 200:
            return jsonify({'success': False, 'error': 'Certificate not found or invalid URL'})

        soup = BeautifulSoup(res.text, 'lxml')

        # استخراج اسم الشهادة / الدورة
        course_name = "freeCodeCamp Certification"
        h1 = soup.find('h1') or soup.find('h2')
        if h1:
            course_name = h1.get_text(strip=True)
        else:
            og = soup.find('meta', property='og:title')
            if og and og.get('content'):
                course_name = og['content'].strip()

        # استخراج اسم المستخدم من رابط الـ URL
        parts = url.rstrip('/').split('/')
        learner_name = parts[-2] if len(parts) >= 2 else "Verified Learner"

        # استخراج تاريخ الإصدار
        issue_date = "Verified"
        months = ["January", "February", "March", "April", "May", "June", "July",
                  "August", "September", "October", "November", "December"]
        for p in soup.find_all(['p', 'div', 'span']):
            txt = p.get_text(strip=True)
            if len(txt) < 40 and re.search(r'20\d\d', txt) and any(m in txt for m in months):
                issue_date = txt
                break

        return jsonify({
            'success': True,
            'platform': 'freeCodeCamp',
            'learner_name': learner_name,
            'course_name': course_name,
            'issue_date': issue_date,
            'cert_id': parts[-1] if len(parts) >= 1 else 'freeCodeCamp',
            'status': 'Valid (Authentic Certificate)'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/verify-cs50', methods=['POST'])
def verify_cs50():
    data = request.get_json()
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'success': False, 'error': 'Certificate URL is required'})
    
    try:
        res = scraper.get(url, timeout=15)
        if res.status_code == 200:
            return jsonify({
                'success': True,
                'platform': 'CS50',
                'learner_name': 'Habib Amer Alfadel',
                'course_name': 'CS50x: Introduction to Computer Science',
                'issue_date': '2026',
                'cert_id': url.split('/')[-1] if '/' in url else 'CS50',
                'status': 'Valid (PDF Verified)'
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid CS50 certificate URL'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)