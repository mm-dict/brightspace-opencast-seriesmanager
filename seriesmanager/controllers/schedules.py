from cement import Controller, ex
import requests
import json

class Schedules(Controller):
    class Meta:
        label = 'schedules'
        stacked_type = 'nested'
        stacked_on = 'base'

    @ex(
        help='list OpenCast schedules matching given title',
        arguments=[
            (['-t','--title'],
            {'help':'OpenCast schedule title','dest':'schedule_title'}
            )
        ]
    )
    def list(self):
        paged_results = True
        result = []
        if self.app.pargs.schedule_title:
            schedule_title = self.app.pargs.schedule_title
            url = 'https://icto99.ugent.be/api/events/?filter=title:' + schedule_title
            self.app.log.info('Listing OpenCast schedules matching title: ' + schedule_title)
        else:
            url = 'https://opencasthostname.ugent.be/api/events/'
            self.app.log.info('Listing all OpenCast schedules')

        r = requests.get(url, auth=('username-todo','password-todo')).json()

        self.app.log.info('Number of OpenCast schedules found: ' + str(len(r)))

        print(r)

    @ex(
        help='create OpenCast schedule with given title',
        arguments=[
            (['schedule_title'],
            {'help':'OpenCast schedule title'})
        ]
    )
    def create(self):
        schedule_title = self.app.pargs.schedule_title
        self.app.log.info('Creating OpenCast schedule with title: ' + schedule_title)

        url = 'https://opencasthostname.ugent.be/api/events'
        metadata = f"""
        [
  {{
    "flavor": "dublincore/episode",
    "fields": [
      {{
        "id": "title",
        "value": "{schedule_title}"
      }},
      {{
        "id": "creator",
        "value": ["Thomas Berton","Kristof Keppens"]
      }},
      {{
        "id": "description",
        "value": "2019-09-07T12:00:00Z 2019-09-10T12:00:00Z FREQ=WEEKLY;BYDAY=MO,SU;BYHOUR=15;BYMINUTE=0"
      }},
      {{
        "id": "isPartOf"
        "value": "ebd48a4c-dde9-4f5f-a5ae-ebfa2035bcaf"
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
        ]
        '''

        processing = '''
        {
  "workflow": "schedule-and-upload",
  "configuration": {
    "flagForCutting": "false",
    "flagForReview": "false",
    "publishToEngage": "true",
    "publishToHarvesting": "true",
    "straightToPublishing": "true"
  }
}
        '''

        scheduling = '''
        {
  "agent_id": "GCMobile-ocrec01",
  "start": "2019-09-07T12:00:00Z",
  "end": "2019-09-10T12:00:00Z",
  "rrule":"FREQ=WEEKLY;BYDAY=MO,SU;BYHOUR=15;BYMINUTE=0",
  "inputs": ["default"],
  "duration": 3600000,
  }
        '''
        r = requests.post(url, auth=('username-todo','password-todo'),
        files=(
            ('metadata', (None, metadata)),
            ('acl', (None, acl)),
            ('processing', (None, processing)),
            ('scheduling', (None, scheduling)),
        ))
        print(r.text)
        print(r.status_code)
