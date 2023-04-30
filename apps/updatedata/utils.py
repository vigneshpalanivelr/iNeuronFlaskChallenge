"""
This script is worker script for scrapping and storing the data.
"""
import os
import json
import time
import threading
from threading import Thread
from bs4 import BeautifulSoup as bs
import requests
from fpdf import FPDF

from flask_pymongo import PyMongo
from flask import current_app
mongoDB = PyMongo()


class ThreadWithReturnValue(Thread):
    """
    Child method of Thread with return value
    """
    # pylint: disable=too-many-arguments, unused-argument, dangerous-default-value
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return


def get_url(course_type='home', course=None):
    """
    Create full URL based on the course type and course name
    """
    base_url = 'https://www.ineuron.ai'
    if course_type == 'category':
        base_url = os.path.join(base_url, course_type, course.replace(' ', '-'))
    elif course_type == 'course':
        base_url = os.path.join(base_url, course_type, course.replace(' ', '-'))
    return base_url


def get_raw_data(course_type='home', course=None):
    """
    Get the full URL and Scrap the Website
    """
    retry = 3
    while True:
        try:
            response = requests.get(get_url(course_type, course), timeout=60)
            rawdata = bs(response.text, 'html.parser')
            return json.loads(rawdata.find_all('script', id='__NEXT_DATA__')[0].text)
        except requests.exceptions.ConnectionError:
            if retry >= 1:
                retry -= 1
                print(f'Could not reach the site, Trying Again! - {retry} - ', course_type, course)
                continue
            break


def get_category_data():
    """
    Get the scrapped data and create a Dict data to store in file or database
    """
    rawdata = get_raw_data()
    all_categories = rawdata['props']['pageProps']['initialState']['init']['categories']
    all_category_data = []
    for sno, each_category in enumerate(all_categories):
        each_category_data = {
            'category-number': sno + 1,
            'category-id': each_category,
            'category-title': all_categories[each_category]['title'],
            'category-url': get_url('category', all_categories[each_category]['title']),
            'course-subcategory': []
        }
        all_subcategory = all_categories[each_category]['subCategories']
        for sno, each_subcategory in enumerate(all_subcategory):
            subcategory_data = {
                'subcategory-no': sno + 1,
                'subcategory-id': all_subcategory[each_subcategory]['id'],
                'subcategory-title': all_subcategory[each_subcategory]['title'],
                'subcategory-url': get_url('category', all_subcategory[each_subcategory]['title']),
            }
            each_category_data['course-subcategory'].append(subcategory_data)
        all_category_data.append(each_category_data)
    return all_category_data


def get_all_courses_parallely():
    """
    Get the data for course parallely
    """
    rawdata = get_raw_data()
    all_courses = rawdata['props']['pageProps']['initialState']['init']['courses']
    all_course_data, threads, error_course_list = [], [], []
    bundle_count_dict = {}
    for sno, course in enumerate(all_courses.keys()):
        process = ThreadWithReturnValue(target=get_all_courses, args=(sno, course, all_courses))
        process.start()
        threads.append(process)

    for process in threads:
        course_data_dict, bundle_name, err_course = process.join()
        all_course_data.append(course_data_dict)
        if err_course:
            error_course_list.append(err_course)
        bundle_count_dict[bundle_name] = bundle_count_dict[bundle_name]+1 if bundle_name in bundle_count_dict else 1
    return all_course_data, bundle_count_dict, error_course_list


# pylint: disable=redefined-outer-name. too-many-locals
def get_all_courses(each_course, sno, all_courses):
    """
    Scrapping course data from all course data and create a dict
    """
    each_course_data = all_courses[each_course]

    # Course Bundle Name
    bundle_name = each_course_data['courseInOneNeuron']['bundleName'] if 'courseInOneNeuron' in each_course_data else None
    bundle_name = bundle_name if bundle_name else 'Without Bundle'

    # Course Learning Details
    for meta in each_course_data['courseMeta']:
        course_learning = meta.get('overview', {}).get('learn', [])
        course_requirements = meta.get('overview', {}).get('requirements', [])
        course_features = meta.get('overview', {}).get('features', [])
        course_language = meta.get('overview', {}).get('language', [])

    # Course Proce Details
    inr_price, usd_price, discount = 'NA', 'NA', 'NA'
    if 'pricing' in each_course_data:
        price = each_course_data['pricing']
        if price['isFree']:
            inr_price, usd_price, discount = 0, 0, 0
        elif 'discount' in price:
            discount = price['discount']
        else:
            inr_price, usd_price = price['IN'], price['US']

    # Course Instructor Details
    instructors_details = each_course_data['instructorsDetails']

    # Course Duration and Curriculum
    duration, curriculum = '', []
    course_rawdata = get_raw_data(course_type='course', course=each_course)
    if 'data' in course_rawdata['props']['pageProps']:
        course_data = course_rawdata['props']['pageProps']['data']
        duration = course_data['meta']['duration']
        # for each_curriculum in course_data['meta']['curriculum'].values():
        for each_curriculum in course_data.get('meta', {}).get('curriculum', {}).values():
            curriculum_details = {
                'curriculum-title': each_curriculum['title'],
                'curriculum-items': []
            }
            for item in each_curriculum['items']:
                curriculum_details['curriculum-items'].append(item['title'])
            curriculum.append(curriculum_details)

    # Each Course Details
    err_course = None
    try:
        course_details = {
            'course-number': sno + 1,
            'course-id': each_course_data['_id'],
            'course-name': each_course,
            'course-mode': each_course_data['mode'],
            'course-category-id': each_course_data['categoryId'],
            'course-description': each_course_data['description'],
            'course-bundlename': bundle_name,
            'course-learn': course_learning,
            'course-requirements': course_requirements,
            'course-features': course_features,
            'course-language': course_language,
            'course-price-inr': inr_price,
            'course-price-usd': usd_price,
            'course-price-dis': discount,
            'course-instructor-details': instructors_details,
            'course-duration': duration,
            'course-curriculum': curriculum
        }
    except Exception as error:  # pylint: disable=broad-exception-caught
        print('ERROR: ', str(error))
        err_course = each_course

    if course_details:
        return course_details, bundle_name, err_course


# pylint: disable=redefined-outer-name
def dump_data(category_data, bundle_count, course_data, bundle_count_for_categories):
    """
    Dumping the data into file
    """
    if category_data:
        file_name = [i for i, a in locals().items() if a == category_data][0]
        with open(f'apps/database/{file_name}.json', 'w', encoding='utf-8') as file_data:
            file_data.write(json.dumps(category_data, indent=4))
    if bundle_count:
        file_name = [i for i, a in locals().items() if a == bundle_count][0]
        with open(f'apps/database/{file_name}.json', 'w', encoding='utf-8') as file_data:
            file_data.write(json.dumps(bundle_count, indent=4))
    if course_data:
        file_name = [i for i, a in locals().items() if a == course_data][0]
        with open(f'apps/database/{file_name}.json', 'w', encoding='utf-8') as file_data:
            file_data.write(json.dumps(course_data, indent=4))
    if bundle_count_for_categories:
        file_name = [i for i, a in locals().items() if a == bundle_count_for_categories][0]
        with open(f'apps/database/{file_name}.json', 'w', encoding='utf-8') as file_data:
            file_data.write(json.dumps(bundle_count_for_categories, indent=4))


# pylint: disable=redefined-outer-name, too-many-locals, too-many-branches
def get_details_parallely(target, max_parallel_thred=None):
    """
    This function spawns Parallel Process to get the Scrapping done.
    """
    if target == 'PDF':
        target_func = generate_course_pdf
        with open('apps/database/course_data.json', encoding="utf-8") as data:
            all_courses = json.load(data)
        input_value = all_courses
    elif target == 'COURSES':
        rawdata = get_raw_data()
        all_courses = rawdata['props']['pageProps']['initialState']['init']['courses']
        input_value = all_courses.keys()
        target_func = get_all_courses

    all_course_data, threads, error_course = [], [], []
    bundle_count, bundle_count_for_categories = {}, {}
    for sno, course in enumerate(input_value):
        if max_parallel_thred:
            while len(threading.enumerate()) >= max_parallel_thred:
                current_app.logger.debug('Running Threads are: ' + str(len(threading.enumerate())))
                time.sleep(6)
        process = ThreadWithReturnValue(target=target_func, args=(course, sno, all_courses))
        process.start()
        threads.append(process)

    for process in threads:
        course_data, bundle_name, err_course = process.join()
        category_id = course_data['course-category-id'] if target != 'PDF' else None

        if course_data:
            all_course_data.append(course_data)
        if bundle_name:
            bundle_count[bundle_name] = bundle_count[bundle_name]+1 if bundle_name in bundle_count else 1
        if err_course:
            error_course.append(err_course)

        if bundle_count_for_categories and course_data['course-category-id'] in bundle_count_for_categories:
            if bundle_name in bundle_count_for_categories[category_id]:
                bundle_count_for_categories[category_id][bundle_name] = bundle_count_for_categories[category_id][bundle_name] + 1
            else:
                bundle_count_for_categories[category_id][bundle_name] = 1
        elif target != 'PDF':
            bundle_count_for_categories[category_id] = {}
            bundle_count_for_categories[category_id][bundle_name] = 1

    if target == 'PDF':
        return all_course_data
    return all_course_data, bundle_count, error_course, bundle_count_for_categories


# pylint: disable=consider-using-f-string)
def generate_course_pdf(data, _, __, save_pdf=True):
    """
    This function is to generate PDF for all the courses
    """
    class PDF(FPDF):
        """
        Classes and Functions for the PDF Document
        """
        def __init__(self):
            super().__init__()

        def header(self):
            self.set_font('Arial', '', 12)
            if not os.path.exists('apps/static/images/ineuron-logo.png'):
                url = r'https://ineuron.ai/images/ineuron-logo.png'
                os.makedirs('apps/static/images/', exist_ok=True)
                img = open('apps/static/images/ineuron-logo.png', 'wb')
                img.write(requests.get(url, timeout=60).content)
            self.image('apps/static/images/ineuron-logo.png', w=40, h=20, type='PNG', x=210/2-20)
            self.cell(w=0, border=True)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', '', 9)
            self.cell(w=0, border=True)
            self.cell(0, 8, f'Page {self.page_no()}', 0, 0, 'C')

    def format_text(txt):
        return str(txt).encode('latin-1', 'replace').decode('latin-1')

    # cell height
    cell_ht = 6
    pdf = PDF()
    pdf.add_page()
    pdf.ln(4)
    pdf.set_font('Arial', 'BU', 16)
    pdf.multi_cell(w=0, h=5, txt=format_text(data.get('course-name', '')), align='C')
    pdf.ln(4)
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(w=0, h=5, txt=format_text(data.get('course-description', '')))
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(w=210/3, h=cell_ht, txt=f"Mode: {format_text(data.get('course-mode'))}", ln=0)
    pdf.cell(w=210/3, h=cell_ht, txt=f"Language: {format_text(data.get('course-language',''))}", ln=0)
    pdf.cell(w=210/3, h=cell_ht, txt=f"Duration: {format_text(data.get('course-duration',''))}", ln=1)

    # y_pos = 65

    # pdf.set_y(y_pos)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(w=30, h=cell_ht, txt="What you'll learn:", ln=1)
    pdf.set_font('Arial', '', 9)
    for d in data.get('course-learn', []):
        pdf.cell(w=30, h=cell_ht, txt=f'{" "*4}{format_text(d)}', ln=1)
    pdf.ln(2)

    # pdf.set_xy(210/3, y_pos)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(w=30, h=cell_ht, txt="Course Features:", ln=1)
    pdf.set_font('Arial', '', 9)
    for feature in data.get('course-features', []):
        # pdf.set_x(210/3)
        pdf.cell(w=30, h=cell_ht, txt=f'{" "*4}{format_text(feature)}', ln=1)
    pdf.ln(2)

    # pdf.set_xy(210*2/3,y_pos)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(w=30, h=cell_ht, txt="Requirements:", ln=1)
    pdf.set_font('Arial', '', 9)
    for req in data.get('course-requirements', []):
        # pdf.set_x(210*2/3)
        pdf.cell(w=30, h=cell_ht, txt=f'{" "*4}{format_text(req)}', ln=1)
    pdf.ln(2)

    # pdf.set_x(210*2/3)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(w=30, h=cell_ht, txt="Pricing:", ln=1)
    pdf.set_font('Arial', '', 9)
    # pdf.set_x(210*2/3)
    pdf.cell(w=0, h=cell_ht, txt=f"{' '*4}{format_text(data.get('course-price-inr',''))} INR", ln=1)
    # pdf.set_x(210*2/3)
    pdf.cell(w=0, h=cell_ht, txt=f"{' '*4}{format_text(data.get('course-price-usd',''))} USD", ln=1)
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(w=30, h=cell_ht, txt="Course Curriculum:", ln=1)
    pdf.set_font('Arial', '', 9)
    for num, d in enumerate(data.get('course-curriculum', [])):
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(w=0, h=cell_ht, txt='{}{}. {}'.format(" "*4, num+1, format_text(d.get('curriculum-title', ''))), ln=1)
        for item in d['curriculum-items']:
            pdf.set_font('Arial', '', 9)
            pdf.cell(w=0, h=cell_ht, txt=f"{' '*12}{format_text(item)}", ln=1)
    pdf.ln(2)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(w=30, h=cell_ht, txt="Instructors:", ln=1)
    for num, d in enumerate(data.get('course-instructor-details', [])):
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(w=0, h=cell_ht, txt='{}. {}'.format(num+1, format_text(d.get('name', '').title())), ln=1)
        pdf.set_font('Arial', '', 9)
        pdf.multi_cell(w=0, h=5, txt=format_text(d.get('description', '')))
        pdf.set_font('Arial', '', 9)
        pdf.cell(w=30, h=cell_ht, txt=f"{' '*8}Email: ", ln=0)
        pdf.cell(w=100, h=cell_ht, txt=format_text(d.get('email', '')), ln=1)
        for key, value in d.get('social', {}).items():
            pdf.cell(w=30, h=cell_ht, txt=f"{' '*8}{format_text(key)}: ", ln=0)
            pdf.cell(w=100, h=cell_ht, txt=format_text(value), ln=1)
    # pdf.ln(4)
    if save_pdf:
        if not os.path.exists('apps/pdfs'):
            os.makedirs('apps/pdfs', exist_ok=True)
        pdf.output(f'apps/pdfs/{data.get("course-name","testpdf").replace(" ","-")}.pdf', 'F')
        return data.get('course-name', ''), None, None
    return pdf.output(f'{data.get("course-name","testpdf").replace(" ","-")}.pdf', 'S').encode('latin-1')


def insert_data_into_mongodb(data_type, data, db_obj=mongoDB, collection=None):
    """
    Inserting data into MangoDB.
    """
    mongodb = db_obj.db
    if data_type == 'CATEGORY':
        collection = collection if collection else os.environ.get('MONGO_DB_COURSE_CATEGORY')
        index = data['category-id']
        key = 'category-data'
    elif data_type == 'COURSE':
        collection = collection if collection else os.environ.get('MONGO_DB_COURSES')
        index = data['course-name'].replace(' ', '-')
        key = 'course-data'
    elif data_type in ['BUNDLE_COUNT', 'CAT_BUNDLE_COUNT']:
        key, value = data
        index, data = key, value

    if mongodb[collection].count_documents({'_id': index}):
        mongodb[collection].update_one({'_id': index}, {'$set': {key: data}})
        current_app.logger.debug(f'Updated: {index}')
    else:
        mongodb[collection].insert_one({'_id': index, key: data})
        current_app.logger.debug(f'Inserted: {index}')


if __name__ == '__main__':
    category_data = get_category_data()
    course_data, bundle_count, error_course, bundle_count_for_categories = get_details_parallely('COURSES', 30)
    dump_data(category_data, bundle_count, course_data, bundle_count_for_categories)
    pdf_files = get_details_parallely('PDF', 10)
