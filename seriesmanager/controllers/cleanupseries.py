from cement import Controller, ex
import requests
from requests.auth import HTTPDigestAuth
import json
from tinydb import Query
from urllib.parse import urlparse, urlunparse

class CleanupSeries(Controller):
    class Meta:
        label = 'cleanup'
        stacked_type = 'nested'
        stacked_on = 'base'

    @ex(
        help='Retrieve all opencast series and insert then into the db',
    )
    def update_db(self):
        paged_results = True
        got_series = True
        series_found = 0
        series_limit = 1000
        series_offset = 0
        result = []

        url = 'https://'+ self.app.config.get('opencast','host') + '/admin-ng/series/series.json?limit=' + str(series_limit) + '&offset=' + str(series_offset)
        self.app.log.info('Listing all OpenCast series')

        #Clean current database
        self.app.oc_db.truncate()
        self.app.log.info('Database is empty, contains ' + str(len(self.app.oc_db)) + 'items')

        while got_series:
            headers = {'X-Requested-Auth': 'Digest'}
            r = requests.get(url,
                headers=headers,
                auth=HTTPDigestAuth(
                    self.app.config.get('opencast','digest_username'),
                    self.app.config.get('opencast','digest_password'))).json()

            series_found = r["total"]
            series_offset += series_limit
            self.app.oc_db.insert_multiple(r['results'])

            u = urlparse(url)
            parsed = u.query.split('&')

            parsed[1] = 'offset=' + str(series_offset)

            url = urlunparse([u.scheme, u.netloc, u.path, u.params, "&".join(parsed), u.fragment])

            if r['count'] == 0:
                got_series = False
        self.app.log.info('Number of OpenCast series found: ' + str(series_found))

    @ex(
        help='Cleanup empty opencast series matching given academic year',
        arguments=[
            (['-y', '--year'],
            {'help':'Academic year', 'dest':'academic_year'})
        ]
    )
    def cleanup_series(self):
        academic_year = self.app.pargs.academic_year
        self.app.log.info('Looping all series to find series without associated items')
        #Query the DB to find all series matching the academic year provided
        series = self.app.oc_db.search(Query().title.matches('(.*)_'+ academic_year))
        withoutEvents = 0
        withEvents = 0
        for serie in series:
            print(serie)
            #Check if serie has items in opencast
            url = 'https://'+ self.app.config.get('opencast','host') + '/admin-ng/series/'+serie["id"]+'/hasEvents.json'
            self.app.log.debug('Using url: ' + url)
            headers = {'X-Requested-Auth': 'Digest'}
            r = requests.get(url,
                headers=headers,
                auth=HTTPDigestAuth(
                    self.app.config.get('opencast','digest_username'),
                    self.app.config.get('opencast','digest_password'))).json()
            self.app.log.debug(r)

            if(r['hasEvents'] is False):
                withoutEvents += 1
                self.app.log.info('Deleting serie with title: ' + serie['title'])
                url = 'https://'+ self.app.config.get('opencast','host') + '/admin-ng/series/'+serie["id"]
                self.app.log.debug('Using url: ' + url)
                headers = {'X-Requested-Auth': 'Digest'}
                r = requests.delete(url,
                    headers=headers,
                    auth=HTTPDigestAuth(
                        self.app.config.get('opencast','digest_username'),
                        self.app.config.get('opencast','digest_password')))
                self.app.log.debug(r)
                if r.status_code == 200:
                    self.app.log.info('Success to delete serie with id ' + serie['id'])
                else:
                    self.app.log.error('Unable to delete serie with id ' + serie['id'])
            else:
                withEvents += 1

        self.app.log.info("Deleted " + str(withoutEvents) + " Series without associated events")
        self.app.log.info("Kept " + str(withEvents) + " Series with events associated")

