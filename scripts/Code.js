function onOpen(){
    console.log("biotables extension opened");
}

function GPT(textValue, model_name='gpt-3.5-turbo', temperature=0.0, resplit = true, parse_escaped_quotes = true, host='http://agingkills.eu:8000', api = "/gpt", limit=1, cache_seconds = 3600) {
  // Generate a hash key for caching
  var cacheKey = Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, textValue + "-" + model_name);
  var cacheKeyString = cacheKey.reduce(function(str, chr){
    chr = (chr < 0 ? chr + 256 : chr).toString(16);
    return str + (chr.length == 1 ? '0' : '') + chr;
  }, '');

  if (cache_seconds > 0) {
    var cache = CacheService.getScriptCache();
    var cachedResponse = cache.get(cacheKeyString);
    if (cachedResponse != null) {
      return cachedResponse;
    }
  }

  // Prepare the data for the API call
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

  // Make the API call using the provided host and API endpoint
  var response = UrlFetchApp.fetch(host + api, options);
  var responseText = response.getContentText();

  // Replace \n with new lines if resplit is true
  if (resplit) {
    responseText = responseText.replace(/\\n/g, "\n");
  }

  // Replace escaped quotes with normal quotes if parse_escaped_quotes is true
  if (parse_escaped_quotes) {
    responseText = responseText.replace(/\\"/g, '"');
  }

  // Cache the new response if caching is enabled
  if (cache_seconds > 0) {
    cache.put(cacheKeyString, responseText, cache_seconds);
  }

  return responseText;
}


function GPT_3_5(textValue, temperature=0.0, cache_seconds = 3600) {
    return GPT(textValue, model_name='gpt-3.5-turbo', temperature=temperature, cache_seconds=cache_seconds)
}

function GPT_4(textValue, temperature=0.0, cache_seconds = 3600) {
    return GPT(textValue, model_name='gpt-4', temperature=temperature, cache_seconds=cache_seconds)
}

function SEMANTIC_SEARCH(textValue, collection_name='bge_base_en_v1.5_aging_5', host='http://agingkills.eu:8000', api = "/papers", limit=1, with_vectors=false, with_payload=true, resplit = true, cache_seconds = 3600) {
    var cacheKey = Utilities.computeDigest(Utilities.DigestAlgorithm.MD5,  textValue + "-" + collection_name + "-" + limit);
    var cacheKeyString = cacheKey.reduce(function(str, chr){
      chr = (chr < 0 ? chr + 256 : chr).toString(16);
      return str + (chr.length == 1 ? '0' : '') + chr;
    }, '');

  // Check if caching is enabled and if the response is already in the cache
  if (cache_seconds > 0) {
    var cachedResponse = cache.get(cacheKey);
    if (cachedResponse != null) {
      return cachedResponse;
    }
  }

  // If not cached or cache is disabled, proceed with the API call
  var data = {
    'text': textValue,
    'collection_name': collection_name,
    'with_vectors': with_vectors,
    'with_payload': with_payload,
    'limit': limit
  };

  var options = {
    'method' : 'post',
    'contentType': 'application/json',
    'payload' : JSON.stringify(data)
  };

  var url = host + api;
  var response = UrlFetchApp.fetch(url, options);
  var responseText = response.getContentText();

  // Replace \n with new lines if resplit is true
  if(resplit) {
    responseText = responseText.replace(/\\n/g, "\n");
  }

  // Cache the new response if cache is enabled
  if (cache_seconds > 0) {
    cache.put(cacheKey, responseText, cache_seconds);
  }

  return responseText;
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