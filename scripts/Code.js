/*
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Hello World')
    .addItem('Say Hello', 'showHelloWorld')
    .addToUi();
}
*/


function GPT(textValue, model_name='gpt-3.5-turbo', temperature=0.0, resplit = true,  host='http://agingkills.eu:8000'. api = "/papers", limit=1) {
  var data = {
    'model_name': model_name,
    'temperature': temperature,
    'text': textValue
  };
  
  var options = {
    'method' : 'post',
    'contentType': 'application/json',
    'payload' : JSON.stringify(data)
  };
  
  var response = UrlFetchApp.fetch('http://agingkills.eu:8000/gpt', options);
    if(resplit == true) {
      return response.getContentText().replace(/\\n/g, "\n")
    } else return response;
}

function GPT_3_5(textValue, temperature=0.0) {
    return GPT(textValue, model_name='gpt-3.5-turbo', temperature=temperature)
}

function GPT_4(textValue, temperature=0.0) {
    return GPT(textValue, model_name='gpt-4', temperature=temperature)
}

function SEMANTIC_SEARCH(textValue, collection_name='bge_base_en_v1.5_aging_5',
    host='http://agingkills.eu:8000'. api = "/papers", limit=1, with_vectors=false, with_payload=true, resplit = true) {
      var data = {
        'text': textValue,
        'collection_name': 'bge_base_en_v1.5_aging_5',
        'with_vectors': with_vectors,
        'with_payload': with_payload,
        'limit': limit
      };

      var options = {
        'method' : 'post',
        'contentType': 'application/json',
        'payload' : JSON.stringify(data)
      };

      var url = host + api
      var response = UrlFetchApp.fetch(url, options);
      if(resplit == true) {
        return response.getContentText().replace(/\\n/g, "\n")
      } else return response;
}