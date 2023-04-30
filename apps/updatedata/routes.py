"""
This script will scrap the iNeuron website and store the data
"""
import os
from flask import render_template, current_app, request, redirect, url_for
from apps.updatedata import blueprint
from apps.updatedata.utils import get_category_data, dump_data, get_details_parallely
from apps.updatedata.utils import insert_data_into_mongodb

from apps import mongoDB


@blueprint.route('/update-data', methods=['GET', 'POST'])
def update_data():
    """
    Updating Flask Application
    """
    if request.method == 'POST':
        try:
            # Getting Category and Subcategory Details
            category_data = get_category_data()
            current_app.logger.info(f'{len(category_data)}: Categories Detected')

            # Getting All Courses
            course_data, bundle_count, error_course, bundle_count_for_categories = get_details_parallely('COURSES', 30)
            current_app.logger.info(f'{len(course_data)}: Courses Detected')
            current_app.logger.info(f'{len(bundle_count)}: Bundles Detected')
            current_app.logger.info(f'{len(error_course)}: Failed Courses')
            current_app.logger.info(f'{len(bundle_count_for_categories)}: Category Bundles Detected')

            if 'local' in request.form:
                # Save the data in local
                dump_data(category_data, bundle_count, course_data, bundle_count_for_categories)
                current_app.logger.info('Data Successfully Saved in local')
            elif 'db' in request.form:
                # Inserting Categories to MongoDB
                for data in category_data:
                    insert_data_into_mongodb('CATEGORY', data, db_obj=mongoDB)
                current_app.logger.info('Category Data Successfully Saved in MongoDB')

                # Inserting Courses to MongoDB
                for data in course_data:
                    insert_data_into_mongodb('COURSE', data, db_obj=mongoDB)
                current_app.logger.info('Course Data Successfully Saved in MongoDB')

                # Inserting Bundle Count to MongoDB
                for key, value in bundle_count.items():
                    collection = os.environ.get('MONGO_DB_COURSE_BUNDLE_COUNT')
                    insert_data_into_mongodb('BUNDLE_COUNT', (key, value), db_obj=mongoDB, collection=collection)
                current_app.logger.info('Bundle Data Successfully Saved in MongoDB')

                # Inserting Bundle Count for Categories to MongoDB
                for key, value in bundle_count_for_categories.items():
                    collection = os.environ.get('MONGO_DB_COURSE_BUNDLE_CATEGORY_COUNT')
                    insert_data_into_mongodb('CAT_BUNDLE_COUNT', (key, value), db_obj=mongoDB, collection=collection)
                current_app.logger.info('Bundle Count Data Successfully Saved in MongoDB')

            # Generate PDF Files
            pdf_files = get_details_parallely('PDF')
            current_app.logger.info(f'{len(pdf_files)}: PDF File Generated')

            # Return
            return redirect(url_for('home_blueprint.index'), 200)
        except Exception as error:  # pylint: disable=broad-except
            current_app.logger.error(error)
            return render_template('home/page-404.html')
    else:
        return render_template('home/login.html')
