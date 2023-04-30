"""
This is the worker script for Home page bluwprint
"""
import json


def read_json(file_name):
    """
    Dump the JSON data in to file
    """
    with open(file_name, encoding="utf-8") as data:
        return json.load(data)


def get_course_data_for_category(key, value):
    """
    Read the course_data JSON file and return the course data if key is present
    """
    cat_course_data, bundle_count = [], {}
    course_data = read_json('apps/database/course_data.json')
    sno = 0
    for i in course_data:
        if key in i and value == i[key]:
            sno += 1
            bundle_name = i['course-bundlename']
            bundle_name = bundle_name if bundle_name else 'Without Bundle'
            bundle_count[bundle_name] = bundle_count[bundle_name]+1 if bundle_name in bundle_count else 1
            temp_data = [sno, i['course-name'], i['course-mode'],
                         i['course-bundlename'], i['course-price-inr']]
            cat_course_data.append(temp_data)
    return cat_course_data, bundle_count


def get_course_details(course_name):
    """
    Read the course_data JSON file and load the course data
    """
    course_data = read_json('apps/database/course_data.json')
    course_name = course_name.replace('-', ' ')
    for i in course_data:
        if course_name == i['course-name']:
            return i


if __name__ == '__main__':
    get_course_data_for_category('course-category-id', '62cd959d53f5fe14766b9ae5')
    get_course_details('Full-Stack-Data-Science-BootCamp-2.0')
