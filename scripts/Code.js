function onOpen(){
    console.log("biotables extension opened");
}

function GPT(textValue, model_name='gpt-3.5-turbo', temperature=0.0, resplit = true, parse_escaped_quotes = true, host='http://agingkills.eu:8000', api = "/papers", limit=1, cache = true) {
  var data = {
    'model_name': model_name,
    'temperature': temperature,
    'text': textValue,
    'cache': cache
  };
  
  var options = {
    'method' : 'post',
    'contentType': 'application/json',
    'payload' : JSON.stringify(data)
  };
  
  var response = UrlFetchApp.fetch('http://agingkills.eu:8000/gpt', options);
  var responseText = response.getContentText();
  
  // Replace \n with new lines if resplit is true
  if(resplit) {
    responseText = responseText.replace(/\\n/g, "\n");
  }
  
  // Replace escaped quotes with normal quotes if parse_escaped_quotes is true
  if(parse_escaped_quotes) {
    responseText = responseText.replace(/\\"/g, '"');
  }
  
  return responseText;
}

function GPT_3_5(textValue, temperature=0.0) {
    return GPT(textValue, model_name='gpt-3.5-turbo', temperature=temperature)
}

function GPT_4(textValue, temperature=0.0) {
    return GPT(textValue, model_name='gpt-4', temperature=temperature)
}

function SEMANTIC_SEARCH(textValue, collection_name='bge_base_en_v1.5_aging_5', host='http://agingkills.eu:8000'. api = "/papers", limit=1, with_vectors=false, with_payload=true, resplit = true)
{
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

function FLATTEN_JSON(jsonString) {
  // Check if the string starts with "{ and ends with }", and remove these characters if it does
  if (jsonString.startsWith('"{') && jsonString.endsWith('}"')) {
    jsonString = jsonString.substring(1, jsonString.length - 1);
  }

  // Initialize an array to hold the values
  var values = [];

  // Parse the JSON string into an object
  try {
    var jsonObject = JSON.parse(jsonString);
  } catch (e) {
    return [['Error parsing JSON: ' + e.message]];
  }

  // Function to recursively flatten the JSON object
  function flattenObject(obj) {
    Object.keys(obj).forEach(key => {
      if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
        // For nested objects, call the function recursively
        flattenObject(obj[key]);
      } else {
        // For primitive values or arrays, add the value to the values array
        values.push(JSON.stringify(obj[key]));
      }
    });
  }

  // Start the flattening process
  flattenObject(jsonObject);

  // Return the values as a single row
  return [values];
}