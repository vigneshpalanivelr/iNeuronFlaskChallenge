"""
This is Home page blueprint where it will route to all the desier pages
"""
from flask import render_template, current_app, send_file

from apps.home import blueprint
from apps.home.utils import read_json, get_course_data_for_category, get_course_details


@blueprint.route('/', methods=['GET'])
def index():
    """
    Index of the Ineuron Page
    """
    try:
        category_data = read_json('apps/database/category_data.json')
        bundle_count = read_json('apps/database/bundle_count.json')
        return render_template('home/index.html', categorydata=category_data,
                               bundlecount=bundle_count, zip=zip)
    except Exception as error:  # pylint: disable=broad-exception-caught
        current_app.logger.error(error)
        return render_template('home/page-404.html')


@blueprint.route('/category-courses/<string:categoryId>', methods=['GET'])
def category_courses(categoryId):
    """
    Once you selected the course category from index page, it will route to list of courses in the category
    """
    try:
        key = 'course-category-id'
        course_data_for_category, bundle_count = get_course_data_for_category(key, categoryId)
        if len(course_data_for_category) == 0:
            return render_template('home/courses_not_found.html')
        return render_template('home/category_courses.html',
                               coursesdata=course_data_for_category,
                               bundlecount=bundle_count, zip=zip)
    except Exception as error:  # pylint: disable=broad-exception-caught
        current_app.logger.error(error)
        return render_template('home/page-404.html')


@blueprint.route('/course/<string:courseName>', methods=['GET'])
def category_details(courseName):
    """
    Once Category is selected from home and course is selected from category-courses
    this page will load all the details about the course
    """
    try:
        course_data = get_course_details(courseName)
        return render_template('home/course.html', coursedata=course_data)
    except Exception as error:  # pylint: disable=broad-exception-caught
        current_app.logger.error(error)
        return render_template('home/page-404.html')


@blueprint.route('/download/<string:courseName>', methods=['GET'])
def download_file(courseName):
    """
    This will provide you an option to download the course PDF
    """
    try:
        path = f"pdfs/{courseName}.pdf"
        return send_file(path, as_attachment=True)
    except Exception as error:  # pylint: disable=broad-exception-caught
        current_app.logger.error(error)
        return render_template('home/page-404.html')
