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

function GPT4(textValue, temperature=0.0, cache_seconds = 3600) {
    //just an alias to GPT_4
    return GPT(textValue, model_name='gpt-4', temperature=temperature, cache_seconds=cache_seconds)
}

function GPT_4(textValue, temperature=0.0, cache_seconds = 3600) {
    return GPT(textValue, model_name='gpt-4', temperature=temperature, cache_seconds=cache_seconds)
}

function download_paper(doi, selenium_on_fail, scihub_on_fail, parser, subfolder, do_not_reparse, selenium_min_wait, selenium_max_wait, cache_seconds) {
  // Handling default values
  selenium_on_fail = (selenium_on_fail === undefined) ? true : selenium_on_fail;
  scihub_on_fail = (scihub_on_fail === undefined) ? false : scihub_on_fail;
  parser = (parser === undefined) ? "py_mu_pdf" : parser;
  subfolder = (subfolder === undefined) ? true : subfolder;
  do_not_reparse = (do_not_reparse === undefined) ? true : do_not_reparse;
  selenium_min_wait = (selenium_min_wait === undefined) ? 15 : selenium_min_wait;
  selenium_max_wait = (selenium_max_wait === undefined) ? 60 : selenium_max_wait;
  cache_seconds = (cache_seconds === undefined) ? 3600 : cache_seconds;

  var cache = CacheService.getScriptCache();

  // Create a unique cache key based on the parameters
  var cache_key = Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, doi + "-" + selenium_on_fail + "-" + scihub_on_fail + "-" + parser + "-" + subfolder + "-" + do_not_reparse + "-" + selenium_min_wait + "-" + selenium_max_wait);
  var cache_key_string = cache_key.reduce(function(str, chr) {
    chr = (chr < 0 ? chr + 256 : chr).toString(16);
    return str + (chr.length == 1 ? '0' : '') + chr;
  }, '');

  // Check if the response is already in the cache
  if (cache_seconds > 0) {
    var cached_response = cache.get(cache_key_string);
    if (cached_response != null) {
      var cached_data = JSON.parse(cached_response);
      if (!cached_data.error) {
        return cached_data;
      }
    }
  }

  // FastAPI endpoint URL with doi as a query parameter
  var fast_api_url = 'http://agingkills.eu:8000/download_paper/';

  // Payload for the POST request (excluding 'doi')
  var payload = {
    "doi": doi,
    "selenium_on_fail": selenium_on_fail,
    "scihub_on_fail": scihub_on_fail,
    "parser": parser,
    "subfolder": subfolder,
    "do_not_reparse": do_not_reparse,
    "selenium_min_wait": selenium_min_wait,
    "selenium_max_wait": selenium_max_wait
  };

  // Options for the POST request
  var options = {
    'method' : 'post',
    'contentType': 'application/json',
    'payload' : JSON.stringify(payload)
  };

  // Make the request with error handling
  try {
    var response = UrlFetchApp.fetch(fast_api_url, options);
    var response_text = response.getContentText();

    // Cache the response only if it's successful
    if (cache_seconds > 0 && response.getResponseCode() == 200) {
      cache.put(cache_key_string, response_text, cache_seconds);
    }
    result = JSON.parse(response_text)
    console.info(result)

    // Parse and return the response
    return result.pdf;
  } catch (e) {
    // Handle errors
    Logger.log("Error in download_paper: " + e.toString());
    return {"error": true, "message": e.toString()};
  }
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

  return responseText
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