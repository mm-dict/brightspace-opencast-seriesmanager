from cement import Controller, ex
import requests
import json
from tinydb import Query
from urllib.parse import urlparse, urlunparse
import collections

class Series(Controller):
    class Meta:
        label = 'series'
        stacked_type = 'nested'
        stacked_on = 'base'

    @ex(
        help='list OpenCast series matching given title',
        arguments=[
            (['-t','--title'],
            {'help':'OpenCast series title','dest':'series_title'}
            )
        ]
    )
    def list(self):
        paged_results = True
        got_series = True
        series_found = 0
        series_limit = 1000
        series_offset = 0
        result = []
        if self.app.pargs.series_title is not None:
            series_title = self.app.pargs.series_title
            url = 'https://'+ self.app.config.get('opencast','host') + '/api/series/?filter=title:' + series_title + 'limit=' + str(series_limit) + '&offset=' + str(series_offset)
            self.app.log.info('Listing OpenCast series matching title: ' + series_title)
        else:
            url = 'https://'+ self.app.config.get('opencast','host') + '/api/series/?limit=' + str(series_limit) + '&offset=' + str(series_offset)
            self.app.log.info('Listing all OpenCast series')

        while got_series:
            r = requests.get(url, auth=(self.app.config.get('opencast','username'),self.app.config.get('opencast','password'))).json()

            series_found += len(r)
            series_offset += series_limit

            series = {}
            for oc_serie in r:
                data = { 'serie' : oc_serie }
                self.app.log.debug('Saving OpenCast serie: ' + str(oc_serie) + ' to DB')
                Serie = Query()
                self.app.oc_db.upsert(oc_serie, Serie.identifier == oc_serie['identifier'])
                # self.app.render(data, 'series.jinja2')

            u = urlparse(url)
            parsed = u.query.split('&')

            arg_offset = 1
            if self.app.pargs.series_title is not None:
                arg_offset = 2

            parsed[arg_offset] = 'offset=' + str(series_offset)

            url = urlunparse([u.scheme, u.netloc, u.path, u.params, "&".join(parsed), u.fragment])

            print(url)
            if len(r) == 0:
                got_series = False
        self.app.log.info('Number of OpenCast series found: ' + str(series_found))

    @ex(
        help='find OpenCast series with duplicate titles',
    )
    def find_duplicates(self):
        got_series = True
        series_found = 0
        series_limit = 1000
        series_offset = 0
        result = []

        url = 'https://'+ self.app.config.get('opencast','host') + '/api/series/?limit=' + str(series_limit) + '&offset=' + str(series_offset)
        self.app.log.debug('Listing all OpenCast series')

        while got_series:
            r = requests.get(url, auth=(self.app.config.get('opencast','username'),self.app.config.get('opencast','password'))).json()

            series_found += len(r)
            series_offset += series_limit

            for oc_serie in r:
                result.append(oc_serie['title'])
                self.app.log.debug('Adding OpenCast serie: ' + oc_serie['title'] + ' (' + oc_serie['identifier'] + ')')

            u = urlparse(url)
            parsed = u.query.split('&')

            arg_offset = 1

            parsed[arg_offset] = 'offset=' + str(series_offset)

            url = urlunparse([u.scheme, u.netloc, u.path, u.params, "&".join(parsed), u.fragment])

            # print(url)
            if len(r) == 0:
                got_series = False

        seen = set()
        uniq = []
        duplicate_arr = []
        for x in result:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
            else:
                duplicate_arr.append(x)

        duplicates = len(result) - len(uniq)

        self.app.log.info('Number of OpenCast series found: ' + str(len(result)))
        self.app.log.info('Number of duplicate OpenCast series found: ' + str(duplicates))
        print(duplicate_arr)

    @ex(
        help='create OpenCast serie with given title',
        arguments=[
            (['series_title'],
            {'help':'OpenCast series title'})
        ]
    )
    def create(self):
        series_title = self.app.pargs.series_title
        self.app.log.info('Creating OpenCast series with title: ' + series_title)

        url = 'https://'+ self.app.config.get('opencast','host') + '/api/series/?filter=title:' + series_title
        r = requests.get(url, auth=(self.app.config.get('opencast','username'),self.app.config.get('opencast','password'))).json()
        print(r)

        url = 'https://' + self.app.config.get('opencast','host') + '/api/series'
        metadata = f"""
        [
          {{
            "label": "Opencast Series DublinCore",
            "flavor": "dublincore/series",
            "fields": [
              {{
                "id": "title",
                "value": "{series_title}"
              }},
              {{
                "id": "subjects",
                "value": ["{series_title}"]
              }},
              {{
                "id": "description",
                "value": "{series_title}"
              }}
            ]
          }}
        ]
        """

        acl = '''
        [
          {
            "allow": true,
            "action": "write",
            "role": "ROLE_ADMIN"
          },
          {
            "allow": true,
            "action": "read",
            "role": "ROLE_USER"
          }
        ]'''

        payload = { 'metadata': metadata, 'acl': acl }

        print(len(r))
        if len(r) == 0:
            r = requests.post(url, auth=(self.app.config.get('opencast','username'),self.app.config.get('opencast','password')), data=payload)
            json_result = json.loads(r.text)
            self.app.log.info('OpenCast series ' + series_title + ' created with id: ' + json_result['identifier'])

        else:
            rs = json.dumps(r[0])
            json_result = json.loads(rs)
            self.app.log.info('OpenCast series ' + series_title + ' already exists with id: ' + json_result['identifier'])

    @ex(
        help='import OpenCast series from memory',
        arguments=[
            (['filename'],
            {'help':'Ufora courses JSON file'})
        ]
    )
    def import_from_memory(self):
        got_series = True
        series_found = 0
        series_limit = 1000
        series_offset = 0
        result = []

        url = 'https://'+ self.app.config.get('opencast','host') + '/api/series/?limit=' + str(series_limit) + '&offset=' + str(series_offset)
        self.app.log.debug('Listing all OpenCast series')

        while got_series:
            r = requests.get(url, auth=(self.app.config.get('opencast','username'),self.app.config.get('opencast','password'))).json()

            series_found += len(r)
            series_offset += series_limit

            for oc_serie in r:
                result.append(oc_serie['title'])
                self.app.log.debug('Adding OpenCast serie: ' + oc_serie['title'] + ' (' + oc_serie['identifier'] + ')')

            u = urlparse(url)
            parsed = u.query.split('&')

            arg_offset = 1

            parsed[arg_offset] = 'offset=' + str(series_offset)

            url = urlunparse([u.scheme, u.netloc, u.path, u.params, "&".join(parsed), u.fragment])

            # print(url)
            if len(r) == 0:
                got_series = False

        ufora_jsonfile = self.app.pargs.filename
        self.app.log.info('Reading Ufora courses JSON file: ' + ufora_jsonfile)

        with open(ufora_jsonfile, 'r') as infile:
            data = infile.read()
        ufora_courses = json.loads(data)

        created = []
        for ufora_course_group in ufora_courses:
            for ufora_course in ufora_course_group:
                course_code = (ufora_course['Code']).strip()
                series_title = self.app.config.get('opencast','ufora_series_prefix') + ':' + course_code
                series_shorttitle = course_code
                series_description = (ufora_course['Name']).replace('"','')

                if series_title not in result:
                    self.app.log.debug('Creating OpenCast serie with title: ' + series_title + ', and description: ' + series_description)
                    ufora_identifier = ufora_course['Identifier']

                    url = 'https://' + self.app.config.get('opencast','host') + '/api/series'
                    metadata = f"""
                    [
                      {{
                        "label": "Opencast Series DublinCore",
                        "flavor": "dublincore/series",
                        "fields": [
                          {{
                            "id": "title",
                            "value": "{series_title}"
                          }},
                          {{
                            "id": "subjects",
                            "value": ["{ufora_identifier}"]
                          }},
                          {{
                            "id": "description",
                            "value": "{series_description}"
                          }}
                        ]
                      }}
                    ]
                    """

                    acl = f"""
                    [
                      {{
                        "allow": true,
                        "action": "read",
                        "role": "ROLE_ADMIN"
                      }},
                      {{
                        "allow": true,
                        "action": "write",
                        "role": "ROLE_ADMIN"
                      }},
                      {{
                        "allow": true,
                        "action": "read",
                        "role": "ROLE_USER"
                      }},
                      {{
                        "allow": true,
                        "action": "read",
                        "role": "{ufora_identifier}_Instructor"
                      }},
                      {{
                        "allow": true,
                        "action": "write",
                        "role": "{ufora_identifier}_Instructor"
                      }},
                      {{
                        "allow": true,
                        "action": "read",
                        "role": "{ufora_identifier}_Learner"
                      }},
                      {{
                        "allow": true,
                        "action": "read",
                        "role": "ROLE_{series_shorttitle}"
                      }}
                    ]
                    """

                    payload = { 'metadata': metadata, 'acl': acl }
                    r = requests.post(url, auth=(self.app.config.get('opencast','username'),self.app.config.get('opencast','password')), data=payload)
                    json_result = json.loads(r.text)
                    self.app.log.info('OpenCast serie created created with id: ' + json_result['identifier'])
                    created.append(json_result['identifier'])
                else:
                    self.app.log.debug('Skip creating, found in OpenCast series DB with title: ' + series_title)

        self.app.log.info('Number of OpenCast series created: ' + str(len(created)))
        #
        # seen = set()
        # uniq = []
        # duplicate_arr = []
        # for x in result:
        #     if x not in seen:
        #         uniq.append(x)
        #         seen.add(x)
        #     else:
        #         duplicate_arr.append(x)
        #
        # duplicates = len(result) - len(uniq)
        #
        # self.app.log.info('Number of OpenCast series found: ' + str(len(result)))
        # self.app.log.info('Number of duplicate OpenCast series found: ' + str(duplicates))
        # self.app.log.info('Number of duplicate OpenCast series found: ' + str(len(duplicate_arr)))
        # print(duplicate_arr)

    @ex(
        help='rebuild ACL in OpenCast serie(s)',
    )
    def rebuild_acl(self):
        got_series = True
        series_found = 0
        series_limit = 1000
        # series_limit = 10
        series_offset = 0
        result = {}

        url = 'https://'+ self.app.config.get('opencast','host') + '/api/series/?limit=' + str(series_limit) + '&offset=' + str(series_offset)
        self.app.log.debug('Listing all OpenCast series')

        while got_series:
            r = requests.get(url, auth=(self.app.config.get('opencast','username'),self.app.config.get('opencast','password'))).json()
            series_found += len(r)
            series_offset += series_limit

            for oc_serie in r:
                acl_url = 'https://'+ self.app.config.get('opencast','host') + '/api/series/' + oc_serie['identifier'] + '/acl'
                r_acl = requests.get(acl_url, auth=(self.app.config.get('opencast','username'),self.app.config.get('opencast','password'))).json()
                result[oc_serie['identifier']] = r_acl
                # print(oc_serie)
                # self.app.log.debug('Adding OpenCast serie: ' + oc_serie['title'] + ' (' + oc_serie['identifier'] + ')')

            u = urlparse(url)
            parsed = u.query.split('&')

            arg_offset = 1

            parsed[arg_offset] = 'offset=' + str(series_offset)

            url = urlunparse([u.scheme, u.netloc, u.path, u.params, "&".join(parsed), u.fragment])

            # print(url)
            if len(r) == 0:
                got_series = False

        acl_user = { "allow": True, "role": "ROLE_USER", "action": "read"  }

        for oc_serie_identifier in result:
            found_role_user = False
            for acl in result[oc_serie_identifier]:
                print(acl['role'])
                if acl['role'] == 'ROLE_USER':
                    found_role_user = True
            if found_role_user:
                self.app.log.debug('Found ROLE_USER, skip ACL rebuild')
            else:
                self.app.log.debug('ROLE_USER not found, rebuild ACL')
                result[oc_serie_identifier].append(acl_user)
                payload = { "acl": json.dumps(result[oc_serie_identifier]) }
                acl_update_url = 'https://'+ self.app.config.get('opencast','host') + '/api/series/' + oc_serie_identifier + '/acl'
                r_update_acl = requests.put(acl_update_url, auth=(self.app.config.get('opencast','username'),self.app.config.get('opencast','password')),data=payload)
                # r_update_acl = requests.put(acl_update_url, auth=(self.app.config.get('opencast','username'),self.app.config.get('opencast','password')),
                # files=(
                #         ('acl', (None, result[oc_serie_identifier])),
                #     )
                # )
                if r_update_acl.status_code == 200:
                    print(r_update_acl.text)
                    self.app.log.info('ACL updated for series with identifier: ' + oc_serie_identifier)
                elif r_update_acl.status_code == 404:
                    self.app.log.warn('Update failed, series not found with identifier: ' + oc_serie_identifier)
                else:
                    self.app.log.error('Unexpected status code with serie : ' + oc_serie_identifier)

    @ex(
        help='import Ufora courses from file and create OpenCast series',
        arguments=[
            (['filename'],
            {'help':'Ufora courses JSON file'})
        ]
    )
    def uforaimport(self):
        ufora_jsonfile = self.app.pargs.filename
        self.app.log.info('Reading Ufora courses JSON file: ' + ufora_jsonfile)

        with open(ufora_jsonfile, 'r') as infile:
            data = infile.read()
        ufora_courses = json.loads(data)

        Serie = Query()

        for ufora_course_group in ufora_courses:
            for ufora_course in ufora_course_group:
                series_title = self.app.config.get('opencast','ufora_series_prefix') + ':' + ufora_course['Code']
                series_shorttitle = ufora_course['Code']
                series_description = ufora_course['Name']
                q_result = self.app.oc_db.search(Serie.title.matches('^' + series_title + '$'))
                if len(q_result) == 0:
                    self.app.log.info('Creating OpenCast serie with title: ' + series_title + ', and description: ' + series_description)

                    ufora_identifier = ufora_course['Identifier']

                    url = 'https://' + self.app.config.get('opencast','host') + '/api/series'
                    metadata = f"""
                    [
                      {{
                        "label": "Opencast Series DublinCore",
                        "flavor": "dublincore/series",
                        "fields": [
                          {{
                            "id": "title",
                            "value": "{series_title}"
                          }},
                          {{
                            "id": "subjects",
                            "value": ["{ufora_identifier}"]
                          }},
                          {{
                            "id": "description",
                            "value": "{series_description}"
                          }}
                        ]
                      }}
                    ]
                    """

                    acl = f"""
                    [
                      {{
                        "allow": true,
                        "action": "read",
                        "role": "ROLE_ADMIN"
                      }},
                      {{
                        "allow": true,
                        "action": "write",
                        "role": "ROLE_ADMIN"
                      }},
                      {{
                        "allow": true,
                        "action": "read",
                        "role": "{ufora_identifier}_Instructor"
                      }},
                      {{
                        "allow": true,
                        "action": "write",
                        "role": "{ufora_identifier}_Instructor"
                      }},
                      {{
                        "allow": true,
                        "action": "read",
                        "role": "{ufora_identifier}_Learner"
                      }},
                      {{
                        "allow": true,
                        "action": "write",
                        "role": "ROLE_{series_shorttitle}"
                      }}
                    ]
                    """

                    payload = { 'metadata': metadata, 'acl': acl }

                    r = requests.post(url, auth=(self.app.config.get('opencast','username'),self.app.config.get('opencast','password')), data=payload)
                    json_result = json.loads(r.text)
                    self.app.log.info('OpenCast serie created created with id: ' + json_result['identifier'])

                else:
                    self.app.log.info('Skip creating, found in OpenCast series DB with title: ' + self.app.config.get('opencast','ufora_series_prefix') + ':' + ufora_course['Code'])
