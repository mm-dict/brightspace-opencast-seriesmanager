from cement import Controller, ex
import requests
import json
import os.path
from urllib.parse import urlparse, urlunparse

class Courses(Controller):
    class Meta:
        label = 'courses'
        stacked_type = 'nested'
        stacked_on = 'base'

    @ex(
        help='list Ufora courses matching given course code',
        arguments=[
            (['-c','--course-code'],
            {'help':'Ufora course code','dest':'course_code'}
            ),
            (['--orgunit-code'],
            {'help':'Ufora orgunit code','dest':'orgunit_code'}
            ),
            (['-o','--output-file'],
            {'help':'Write result to given output file','dest':'output_file'}
            ),
        ]
    )
    def list(self):
        if self.app.pargs.output_file is not None:
            if os.path.exists(self.app.pargs.output_file):
                self.app.log.error('Output file already exists: ' + self.app.pargs.output_file)
                raise IOError('Output file already exists: ' + self.app.pargs.output_file)
            else:
                self.app.log.debug('Output file does not exist: ' + self.app.pargs.output_file + ', continue...')

        paged_results = True
        result = []
        if self.app.pargs.course_code is not None:
            course_code = self.app.pargs.course_code
            url = 'https://' + self.app.config.get('bs','host') + '/d2l/api/lp/1.31/orgstructure/?orgUnitType=3&orgUnitCode=' + course_code

            self.app.log.info('Listing Ufora courses matching code: ' + course_code)
        else:
            if self.app.pargs.orgunit_code is not None:
                url = 'https://' + self.app.config.get('bs','host') + '/d2l/api/lp/1.31/orgstructure/' + self.app.pargs.orgunit_code + '/children/paged/?orgUnitType=3'
                self.app.log.info('Listing children of ufora orgunit code ' + self.app.pargs.orgunit_code )
            else:
                url = 'https://' + self.app.config.get('bs','host') + '/d2l/api/lp/1.31/orgstructure/?orgUnitType=3'
                self.app.log.info('Listing all Ufora courses')


        while paged_results:
            self.app.log.info('using url: ' + url)
            self.app.log.debug(requests.get(url, auth=self.app.d2l_uc))
            r = requests.get(url, auth=self.app.d2l_uc).json()

            u = urlparse(url)
            parsed = u.query.split('&')
            self.app.log.debug(parsed)

            arg_offset = 1
            if self.app.pargs.course_code is not None:
                arg_offset = 2

            if len(parsed) > arg_offset :
                parsed[arg_offset] = 'bookmark=' + r['PagingInfo']['Bookmark']
            else:
                self.app.log.debug(arg_offset)
                parsed.insert(int(arg_offset), 'bookmark=' + r['PagingInfo']['Bookmark'])
            url = urlunparse([u.scheme, u.netloc, u.path, u.params, "&".join(parsed), u.fragment])
            result.append(r['Items'])

            if r['PagingInfo']['HasMoreItems'] == False:
                paged_results = False

            self.app.log.debug('Requested page: ' + r['PagingInfo']['Bookmark'])

        nr_courses = 0
        for page in result:
            nr_courses += len(page)
        self.app.log.info('Number of Ufora courses found: ' + str(nr_courses))

        if self.app.pargs.output_file is not None:
            self.app.log.info('Writing results to: ' + self.app.pargs.output_file)
            with open(self.app.pargs.output_file, 'w') as outfile:
                json.dump(result, outfile, indent=4)
        else:
            print(result)
