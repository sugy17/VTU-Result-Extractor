# VTU Result Extractor
Live at https://scrapper-web.rxav.pw/

Swagger-url: https://scrapper-web.rxav.pw/info

Backend for VTU Result Analysis project.

Takes in url and list of USNS through API and sweeps the scrapped data into semstat-database for analysis.

## API Routes:

New Routes will Be added as necessary, however, these are some of the permanent API Routes Available.

Their Internal Workings are Subject to Change and the Output to Each May Also change from Version to Version, but they remain of the same functionality.

- /input/
  - GET /usn
  - POST /list
- /
  - GET /queue
  - DELETE /queue/{request_id}
- /
  - GET /history
  - GET /history/{request_id}
  - DELETE /history/{request_id}
- /data/
  - GET /data/url
  - GET /data/exam
  - GET /data/exam/{exam_id}/file
  - GET /data/exam/{exam_id}/file/{file_name}
  - GET /data/exam/{exam_id}/usn
  - GET /data/exam/{exam_id}/usn/{usn}

Refer to the swagger-url for more information.

## docker-compose
Pass port number through scrapper_port,defaults to port 8000.

Eg: scrapper_port=9001 docker-compose up