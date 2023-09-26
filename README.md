Note: this code is deployed at `https://se-phones-demo.lilikovych.name`.

* Import `diploma_phones.documents.json` and `diploma_phones.prefix_tree.json` into your MongoDB (by defaault it's on `127.0.0.1:27017`)
* Install dependencies `pip3 install -r requirements.txt`
* Use Uvicorn to start server: `python3 -m uvicorn main:app --port 3000 --host 127.0.0.1`
* Test: `curl 
'http://127.0.0.1:3000/search?q=46a453945433ce452b30565cba88adb6&q=f6e2952cfb280ebc34fcc52bdfdc4b3e&q=845e33d9953f736be227314bfdefb817&q=a3d296261dbda886e8685e4bad338bf4&q=786cf641763e30aedb36c356b641b1b4&q=e5fdd95429dd281c20f2769f77bba7d1' 
-X 'GET' -H 'X-Secret: secret API token'`
